"""
RAG Pipeline for SMP DocuMind
==============================

Implements the full retrieval-augmented generation flow:

    user question
        |
        v
    [embed query]
        |
        v
    [FAISS top-k retrieval]      <-- semantic
        |
        v
    [BM25 top-k retrieval]       <-- lexical (in-process)
        |
        v
    [hybrid fusion + dedup]
        |
        v
    [LLM generator] (OpenAI if key set, otherwise extractive fallback)
        |
        v
    grounded answer + citations

Design notes
------------
* The fallback generator is *extractive* — it stitches together the most
  relevant retrieved sentences. It is deliberately conservative: it never
  invents content, which makes it a reasonable safety baseline and
  makes the demo runnable without API keys.

* The OpenAI path uses gpt-4o-mini by default and is wrapped so that any
  failure (no key, rate limit, network) falls back to extractive mode.

* Citations point to the source document IDs (DOC-001 etc.), which the
  frontend renders as clickable references.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

try:
    import faiss  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
    _SEMANTIC_RETRIEVAL_AVAILABLE = True
except ImportError:  # pragma: no cover
    faiss = None
    SentenceTransformer = None
    _SEMANTIC_RETRIEVAL_AVAILABLE = False

# OpenAI is optional. We catch ImportError so the service still starts.
try:
    from openai import OpenAI  # type: ignore
    _OPENAI_AVAILABLE = True
except ImportError:  # pragma: no cover
    _OPENAI_AVAILABLE = False


# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "data" / "synthetic" / "documents"
INDEX_PATH = ROOT / "data" / "synthetic" / "document_index.json"

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # MiniLM-L6-v2

CHUNK_SIZE_CHARS = 500     # ~100 tokens, keeps chunks coherent
CHUNK_OVERLAP_CHARS = 80   # overlap preserves context across boundaries

TOP_K_RETRIEVE = 8          # candidates from each retriever
TOP_K_FINAL = 4             # passed to the generator after fusion

# Similarity threshold below which we abort (mirrors DOC-005 policy).
RELEVANCE_THRESHOLD = 0.30  # cosine sim, slightly looser for synthetic data


# ------------------------------------------------------------------
# Data structures
# ------------------------------------------------------------------
@dataclass
class Chunk:
    """A retrievable piece of a document."""
    chunk_id: str
    doc_id: str
    title: str
    text: str
    category: str = ""
    embedding: Optional[np.ndarray] = field(default=None, repr=False)


@dataclass
class RetrievalResult:
    chunk: Chunk
    score: float
    source: str  # 'dense', 'bm25', or 'hybrid'


@dataclass
class Answer:
    text: str
    citations: List[str]                 # ['DOC-001', 'DOC-005']
    retrieved_chunks: List[RetrievalResult]
    used_generator: str                  # 'openai' or 'extractive_fallback'
    aborted_low_relevance: bool = False


# ------------------------------------------------------------------
# Chunking
# ------------------------------------------------------------------
def chunk_text(text: str,
               size: int = CHUNK_SIZE_CHARS,
               overlap: int = CHUNK_OVERLAP_CHARS) -> List[str]:
    """Split text into overlapping chunks of roughly `size` characters,
    breaking at sentence boundaries when possible."""
    text = text.strip()
    if len(text) <= size:
        return [text]

    # Split into sentences using simple punctuation rules. For real-world
    # use we'd swap in a proper sentence splitter (e.g., spaCy).
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    buf = ""
    for sent in sentences:
        if len(buf) + len(sent) + 1 <= size:
            buf = (buf + " " + sent).strip()
        else:
            if buf:
                chunks.append(buf)
            # Start the next chunk with the tail of the previous one for overlap.
            if overlap > 0 and chunks:
                tail = chunks[-1][-overlap:]
                buf = (tail + " " + sent).strip()
            else:
                buf = sent
    if buf:
        chunks.append(buf)
    return chunks


# ------------------------------------------------------------------
# Lightweight in-process BM25 (no external deps)
# ------------------------------------------------------------------
class BM25:
    """Minimal BM25 implementation. Good enough for thousands of chunks;
    swap in rank-bm25 or Elasticsearch for larger corpora."""

    def __init__(self, chunks: List[Chunk], k1: float = 1.5, b: float = 0.75):
        self.chunks = chunks
        self.k1 = k1
        self.b = b
        self._tokenized = [self._tokenize(c.text) for c in chunks]
        self._doc_lens = np.array([len(t) for t in self._tokenized])
        self._avg_len = self._doc_lens.mean() if len(self._doc_lens) else 0.0

        # Document frequency
        self._df: Dict[str, int] = {}
        for tokens in self._tokenized:
            for term in set(tokens):
                self._df[term] = self._df.get(term, 0) + 1
        self._n_docs = len(chunks)

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        return re.findall(r"[a-z0-9]+", text.lower())

    def _idf(self, term: str) -> float:
        df = self._df.get(term, 0)
        # Standard BM25 IDF with +1 smoothing to avoid negatives.
        return float(np.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0))

    def search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        q_terms = self._tokenize(query)
        scores = np.zeros(self._n_docs, dtype=np.float32)
        for term in q_terms:
            if term not in self._df:
                continue
            idf = self._idf(term)
            for i, tokens in enumerate(self._tokenized):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self._doc_lens[i] / max(self._avg_len, 1))
                scores[i] += idf * (tf * (self.k1 + 1)) / denom
        # Argpartition for top-k, then sort the slice for stable ordering.
        if top_k >= len(scores):
            order = np.argsort(-scores)
        else:
            top_idx = np.argpartition(-scores, top_k)[:top_k]
            order = top_idx[np.argsort(-scores[top_idx])]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]


# ------------------------------------------------------------------
# Main pipeline
# ------------------------------------------------------------------
class RAGPipeline:
    """Orchestrates ingestion, retrieval, and generation."""

    def __init__(self, embedding_model_name: str = EMBEDDING_MODEL):
        self._embedder = None
        self._index = None
        self._vectorizer: Optional[TfidfVectorizer] = None
        self._tfidf_matrix = None
        self._chunks: List[Chunk] = []
        self._bm25: Optional[BM25] = None
        self._openai_client: Optional["OpenAI"] = None
        self._retrieval_mode = "tfidf"

        if _SEMANTIC_RETRIEVAL_AVAILABLE and SentenceTransformer is not None:
            try:
                self._embedder = SentenceTransformer(embedding_model_name)
                self._retrieval_mode = "semantic"
            except Exception:
                self._embedder = None

        api_key = os.environ.get("OPENAI_API_KEY")
        if _OPENAI_AVAILABLE and api_key:
            self._openai_client = OpenAI(api_key=api_key)

    # -------------------- ingestion --------------------

    def ingest(self) -> int:
        """Load docs from disk, chunk, embed, index. Returns chunk count."""
        index_meta = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        chunks: List[Chunk] = []

        for entry in index_meta:
            doc_path = ROOT / entry["path"]
            text = doc_path.read_text(encoding="utf-8")
            for i, piece in enumerate(chunk_text(text)):
                chunks.append(
                    Chunk(
                        chunk_id=f"{entry['doc_id']}::chunk-{i:03d}",
                        doc_id=entry["doc_id"],
                        title=entry["title"],
                        category=entry["category"],
                        text=piece,
                    )
                )

        # Embed in a single batch — fast for our size.
        texts = [c.text for c in chunks]
        if self._embedder is not None and faiss is not None:
            embeddings = self._embedder.encode(
                texts, normalize_embeddings=True, show_progress_bar=False
            ).astype(np.float32)
            for c, e in zip(chunks, embeddings):
                c.embedding = e

            # FAISS inner-product on normalized vectors == cosine similarity.
            index = faiss.IndexFlatIP(embeddings.shape[1])
            index.add(embeddings)
            self._index = index
        else:
            self._vectorizer = TfidfVectorizer(
                lowercase=True,
                stop_words="english",
                ngram_range=(1, 2),
                max_features=4096,
            )
            self._tfidf_matrix = self._vectorizer.fit_transform(texts)

        self._chunks = chunks
        self._bm25 = BM25(chunks)
        return len(chunks)

    # -------------------- retrieval --------------------

    def _dense_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        if self._index is not None and self._embedder is not None:
            q_emb = self._embedder.encode(
                [query], normalize_embeddings=True
            ).astype(np.float32)
            scores, idx = self._index.search(q_emb, top_k)
            results = []
            for s, i in zip(scores[0], idx[0]):
                if i < 0:
                    continue
                results.append(RetrievalResult(self._chunks[i], float(s), "dense"))
            return results

        assert self._vectorizer is not None
        assert self._tfidf_matrix is not None
        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._tfidf_matrix).ravel()
        order = np.argsort(-scores)[:top_k]
        return [
            RetrievalResult(self._chunks[int(i)], float(scores[i]), "tfidf")
            for i in order
            if scores[i] > 0
        ]

    def _bm25_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        assert self._bm25 is not None
        return [
            RetrievalResult(self._chunks[i], score, "bm25")
            for i, score in self._bm25.search(query, top_k)
        ]

    @staticmethod
    def _normalize(scores: List[float]) -> List[float]:
        if not scores:
            return scores
        lo, hi = min(scores), max(scores)
        if hi - lo < 1e-9:
            return [1.0 for _ in scores]
        return [(s - lo) / (hi - lo) for s in scores]

    def retrieve(self, query: str,
                 top_k_each: int = TOP_K_RETRIEVE,
                 top_k_final: int = TOP_K_FINAL) -> List[RetrievalResult]:
        """Hybrid retrieval with reciprocal-rank-style fusion."""
        dense = self._dense_search(query, top_k_each)
        sparse = self._bm25_search(query, top_k_each)

        # Normalize scores per source to combine fairly.
        dense_norm = self._normalize([r.score for r in dense])
        sparse_norm = self._normalize([r.score for r in sparse])

        fused: Dict[str, RetrievalResult] = {}
        for r, s in zip(dense, dense_norm):
            fused[r.chunk.chunk_id] = RetrievalResult(r.chunk, 0.6 * s, "hybrid")
        for r, s in zip(sparse, sparse_norm):
            existing = fused.get(r.chunk.chunk_id)
            if existing:
                existing.score += 0.4 * s
            else:
                fused[r.chunk.chunk_id] = RetrievalResult(r.chunk, 0.4 * s, "hybrid")

        ranked = sorted(fused.values(), key=lambda r: r.score, reverse=True)
        return ranked[:top_k_final]

    # -------------------- generation --------------------

    def _format_context(self, results: List[RetrievalResult]) -> str:
        return "\n\n".join(
            f"[{r.chunk.doc_id}] {r.chunk.title}\n{r.chunk.text}" for r in results
        )

    def _generate_openai(self, question: str,
                         results: List[RetrievalResult]) -> str:
        assert self._openai_client is not None
        context = self._format_context(results)
        system = (
            "Kamu adalah DocuMind, asisten internal untuk SMP Technology. "
            "Jawab pertanyaan hanya berdasarkan KONTEKS yang diberikan. "
            "Jika konteks tidak mengandung jawaban, sampaikan dengan jelas. "
            "Cantumkan referensi dokumen sumber secara inline menggunakan ID-nya dalam tanda kurung siku, "
            "contoh [DOC-005]. Berikan jawaban yang ringkas dalam Bahasa Indonesia."
        )
        user = f"KONTEKS:\n{context}\n\nPERTANYAAN:\n{question}"
        resp = self._openai_client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return resp.choices[0].message.content or ""

    def _generate_extractive(self, question: str,
                             results: List[RetrievalResult]) -> str:
        """Fallback: pick the most relevant sentences from the top chunks
        and stitch them with citations. Conservative but never hallucinates."""
        if not results:
            return "Saya tidak dapat menemukan informasi yang relevan dalam basis pengetahuan."

        # Score each sentence by token overlap with the question.
        q_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
        candidates: List[Tuple[float, str, str]] = []  # (score, sent, doc_id)
        for r in results:
            for sent in re.split(r"(?<=[.!?])\s+", r.chunk.text):
                if not sent.strip():
                    continue
                s_terms = set(re.findall(r"[a-z0-9]+", sent.lower()))
                if not s_terms:
                    continue
                overlap = len(q_terms & s_terms) / max(len(q_terms), 1)
                # Combine sentence-level overlap with chunk-level retrieval score.
                candidates.append((overlap + 0.3 * r.score, sent.strip(), r.chunk.doc_id))

        candidates.sort(key=lambda x: -x[0])
        top = candidates[:3]
        if not top or top[0][0] < 0.05:
            return "Saya tidak dapat menemukan jawaban yang meyakinkan dalam basis pengetahuan."

        # De-duplicate sentences while preserving their citations.
        seen = set()
        parts: List[str] = []
        for _, sent, doc_id in top:
            if sent in seen:
                continue
            seen.add(sent)
            parts.append(f"{sent} [{doc_id}]")
        return " ".join(parts)

    # -------------------- public API --------------------

    def ask(self, question: str) -> Answer:
        """Full pipeline: retrieve, check threshold, generate, return."""
        results = self.retrieve(question)
        if not results or results[0].score < RELEVANCE_THRESHOLD:
            return Answer(
                text=("Saya tidak dapat menemukan kecocokan yang meyakinkan dalam basis pengetahuan "
                      "untuk pertanyaan ini. Coba ubah kata-kata pertanyaan atau hubungi "
                      "pakar yang berwenang."),
                citations=[],
                retrieved_chunks=results,
                used_generator="aborted",
                aborted_low_relevance=True,
            )

        if self._openai_client is not None:
            try:
                text = self._generate_openai(question, results)
                used = "openai"
            except Exception:  # noqa: BLE001 — bubble nothing up to the user
                text = self._generate_extractive(question, results)
                used = "extractive_fallback"
        else:
            text = self._generate_extractive(question, results)
            used = "extractive_fallback"

        # Pull citations out of the answer text and the retrieved chunks.
        cited_ids = sorted(set(re.findall(r"DOC-\d{3}", text)))
        if not cited_ids:
            # Default to the top retrieved doc IDs.
            cited_ids = sorted({r.chunk.doc_id for r in results[:2]})

        return Answer(
            text=text,
            citations=cited_ids,
            retrieved_chunks=results,
            used_generator=used,
        )
