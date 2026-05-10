"""
Lightweight Benchmark Runner
============================

Runs a TF-IDF + BM25 hybrid retrieval pipeline (no torch dependency)
against the synthetic Q&A set, computes realistic metrics, and writes
them to data/benchmarks/results.json so the dashboard has real data.

This mirrors the behaviour of rag_pipeline.py closely enough to
produce representative metrics. The production code uses
sentence-transformers; this benchmark uses TF-IDF as a stand-in for
the dense retriever. Numbers are slightly lower than the production
pipeline would yield, which is honest and conservative.

Why a separate script?
    The full ML stack (torch + sentence-transformers + faiss) is heavy
    to install. In CI we run THIS script as a sanity check. The full
    evaluation (ml-service/evaluation.py) runs nightly with the heavy
    deps loaded.

Run:
    python scripts/run_benchmark_lite.py
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List, Dict, Tuple, Set

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ------------------------------------------------------------------
# Paths
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "data" / "synthetic" / "documents"
INDEX_PATH = ROOT / "data" / "synthetic" / "document_index.json"
QA_PATH = ROOT / "data" / "synthetic" / "qa_pairs.json"
OUT_PATH = ROOT / "data" / "benchmarks" / "results.json"


# ------------------------------------------------------------------
# Chunking (mirrors rag_pipeline.chunk_text)
# ------------------------------------------------------------------
def chunk_text(text: str, size: int = 500, overlap: int = 80) -> List[str]:
    text = text.strip()
    if len(text) <= size:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    out, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) + 1 <= size:
            buf = (buf + " " + s).strip()
        else:
            if buf:
                out.append(buf)
            tail = out[-1][-overlap:] if out and overlap > 0 else ""
            buf = (tail + " " + s).strip() if tail else s
    if buf:
        out.append(buf)
    return out


# ------------------------------------------------------------------
# BM25 (same as rag_pipeline)
# ------------------------------------------------------------------
class BM25:
    def __init__(self, docs: List[str], k1: float = 1.5, b: float = 0.75):
        self.tokenized = [re.findall(r"[a-z0-9]+", d.lower()) for d in docs]
        self.doc_lens = np.array([len(t) for t in self.tokenized])
        self.avg = self.doc_lens.mean() if len(self.doc_lens) else 0.0
        self.k1, self.b = k1, b
        self.df: Dict[str, int] = {}
        for tokens in self.tokenized:
            for t in set(tokens):
                self.df[t] = self.df.get(t, 0) + 1
        self.n = len(docs)

    def search(self, query: str, top_k: int) -> List[Tuple[int, float]]:
        q_terms = re.findall(r"[a-z0-9]+", query.lower())
        scores = np.zeros(self.n, dtype=np.float32)
        for term in q_terms:
            if term not in self.df:
                continue
            idf = float(np.log((self.n - self.df[term] + 0.5) / (self.df[term] + 0.5) + 1))
            for i, tokens in enumerate(self.tokenized):
                tf = tokens.count(term)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (1 - self.b + self.b * self.doc_lens[i] / max(self.avg, 1))
                scores[i] += idf * (tf * (self.k1 + 1)) / denom
        order = np.argsort(-scores)[:top_k]
        return [(int(i), float(scores[i])) for i in order if scores[i] > 0]


# ------------------------------------------------------------------
# Pipeline
# ------------------------------------------------------------------
@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    title: str
    text: str


def load_chunks() -> List[Chunk]:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    chunks: List[Chunk] = []
    for entry in index:
        text = (ROOT / entry["path"]).read_text(encoding="utf-8")
        for i, piece in enumerate(chunk_text(text)):
            chunks.append(Chunk(
                chunk_id=f"{entry['doc_id']}::chunk-{i:03d}",
                doc_id=entry["doc_id"],
                title=entry["title"],
                text=piece,
            ))
    return chunks


def normalize(scores: np.ndarray) -> np.ndarray:
    if scores.size == 0:
        return scores
    lo, hi = scores.min(), scores.max()
    if hi - lo < 1e-9:
        return np.ones_like(scores)
    return (scores - lo) / (hi - lo)


def retrieve(question: str,
             chunks: List[Chunk],
             tfidf: TfidfVectorizer,
             tfidf_matrix,
             bm25: BM25,
             top_k_each: int = 8,
             top_k_final: int = 4) -> List[Tuple[Chunk, float]]:
    # Dense (TF-IDF as a stand-in for sentence-transformers)
    q_vec = tfidf.transform([question])
    sims = cosine_similarity(q_vec, tfidf_matrix).flatten()
    dense_idx = np.argsort(-sims)[:top_k_each]
    dense = [(int(i), float(sims[i])) for i in dense_idx]

    # Sparse
    sparse = bm25.search(question, top_k_each)

    # Normalize and fuse
    dense_norm = normalize(np.array([s for _, s in dense]))
    sparse_norm = normalize(np.array([s for _, s in sparse])) if sparse else np.array([])

    fused: Dict[int, float] = {}
    for (i, _), s in zip(dense, dense_norm):
        fused[i] = fused.get(i, 0.0) + 0.6 * float(s)
    for (i, _), s in zip(sparse, sparse_norm):
        fused[i] = fused.get(i, 0.0) + 0.4 * float(s)

    ranked = sorted(fused.items(), key=lambda x: -x[1])[:top_k_final]
    return [(chunks[i], score) for i, score in ranked]


def extractive_answer(question: str,
                      results: List[Tuple[Chunk, float]]) -> Tuple[str, List[str]]:
    """Pick the most overlapping sentences from retrieved chunks."""
    if not results:
        return "I could not find relevant information.", []
    q_terms = set(re.findall(r"[a-z0-9]+", question.lower()))
    candidates: List[Tuple[float, str, str]] = []
    for chunk, score in results:
        for sent in re.split(r"(?<=[.!?])\s+", chunk.text):
            s_terms = set(re.findall(r"[a-z0-9]+", sent.lower()))
            if not s_terms:
                continue
            overlap = len(q_terms & s_terms) / max(len(q_terms), 1)
            candidates.append((overlap + 0.3 * score, sent.strip(), chunk.doc_id))
    candidates.sort(key=lambda x: -x[0])
    top = candidates[:3]
    if not top or top[0][0] < 0.05:
        return "I could not find a confident answer.", []
    seen: Set[str] = set()
    parts: List[str] = []
    cited: List[str] = []
    for _, sent, doc_id in top:
        if sent in seen:
            continue
        seen.add(sent)
        parts.append(f"{sent} [{doc_id}]")
        if doc_id not in cited:
            cited.append(doc_id)
    return " ".join(parts), cited


# ------------------------------------------------------------------
# Metrics
# ------------------------------------------------------------------
def text_similarity(a: str, b: str, vec: TfidfVectorizer) -> float:
    """Cosine similarity in TF-IDF space, scaled to [0, 1]."""
    if not a.strip() or not b.strip():
        return 0.0
    m = vec.transform([a, b])
    return float(cosine_similarity(m[0], m[1])[0][0])


@dataclass
class PerQ:
    qa_id: str
    question: str
    expected_answer: str
    predicted_answer: str
    expected_doc_ids: List[str]
    predicted_citations: List[str]
    answer_relevance: float
    retrieval_hit: bool
    citation_faithful: bool
    latency_ms: float
    difficulty: str


@dataclass
class Agg:
    n: int
    mean_answer_relevance: float
    retrieval_hit_rate: float
    citation_faithfulness: float
    p50_latency_ms: float
    p95_latency_ms: float
    by_difficulty: Dict[str, Dict[str, float]] = field(default_factory=dict)


def main() -> None:
    print("Loading documents...")
    chunks = load_chunks()
    print(f"  -> {len(chunks)} chunks across {len(set(c.doc_id for c in chunks))} documents")

    print("Building indices (TF-IDF + BM25)...")
    tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=1, max_df=0.95, lowercase=True)
    tfidf_matrix = tfidf.fit_transform([c.text for c in chunks])
    bm25 = BM25([c.text for c in chunks])

    # Separate vectorizer for answer-similarity scoring (richer corpus).
    eval_vec = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
    qa_pairs = json.loads(QA_PATH.read_text(encoding="utf-8"))
    eval_vec.fit([c.text for c in chunks]
                 + [p["expected_answer"] for p in qa_pairs]
                 + [p["question"] for p in qa_pairs])

    print(f"Running benchmark on {len(qa_pairs)} questions...")
    per_q: List[PerQ] = []
    for pair in qa_pairs:
        expected_docs = [d.strip() for d in pair["source_doc_id"].split(",")]
        t0 = time.perf_counter()
        results = retrieve(pair["question"], chunks, tfidf, tfidf_matrix, bm25)
        answer_text, cited = extractive_answer(pair["question"], results)
        latency_ms = (time.perf_counter() - t0) * 1000

        retrieved_doc_ids = {c.doc_id for c, _ in results}
        retrieval_hit = bool(retrieved_doc_ids & set(expected_docs))
        citation_faithful = bool(set(cited) & set(expected_docs)) if cited else False
        relevance = text_similarity(answer_text, pair["expected_answer"], eval_vec)

        per_q.append(PerQ(
            qa_id=pair["qa_id"],
            question=pair["question"],
            expected_answer=pair["expected_answer"],
            predicted_answer=answer_text,
            expected_doc_ids=expected_docs,
            predicted_citations=cited,
            answer_relevance=float(relevance),
            retrieval_hit=retrieval_hit,
            citation_faithful=citation_faithful,
            latency_ms=latency_ms,
            difficulty=pair.get("difficulty", "unknown"),
        ))

    # Aggregate
    rel = [p.answer_relevance for p in per_q]
    lat = [p.latency_ms for p in per_q]
    hits = [p.retrieval_hit for p in per_q]
    faith = [p.citation_faithful for p in per_q]

    by_diff: Dict[str, Dict[str, float]] = {}
    for d in {p.difficulty for p in per_q}:
        subset = [p for p in per_q if p.difficulty == d]
        by_diff[d] = {
            "n": len(subset),
            "mean_answer_relevance": float(np.mean([p.answer_relevance for p in subset])),
            "retrieval_hit_rate": float(np.mean([p.retrieval_hit for p in subset])),
            "citation_faithfulness": float(np.mean([p.citation_faithful for p in subset])),
            "p50_latency_ms": float(np.percentile([p.latency_ms for p in subset], 50)),
        }

    agg = Agg(
        n=len(per_q),
        mean_answer_relevance=float(np.mean(rel)),
        retrieval_hit_rate=float(np.mean(hits)),
        citation_faithfulness=float(np.mean(faith)),
        p50_latency_ms=float(np.percentile(lat, 50)),
        p95_latency_ms=float(np.percentile(lat, 95)),
        by_difficulty=by_diff,
    )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUT_PATH.write_text(json.dumps({
        "summary": asdict(agg),
        "per_question": [asdict(p) for p in per_q],
        "config": {
            "retriever": "TF-IDF (dense) + BM25 (sparse) hybrid, weights 0.6/0.4",
            "generator": "extractive_fallback (production uses LLM)",
            "top_k_final": 4,
            "note": "Lightweight benchmark. Production pipeline uses sentence-transformers.",
        },
    }, indent=2), encoding="utf-8")

    print("\n=== AGGREGATE RESULTS ===")
    print(f"  N questions:              {agg.n}")
    print(f"  Mean answer relevance:    {agg.mean_answer_relevance:.3f}")
    print(f"  Retrieval hit rate:       {agg.retrieval_hit_rate:.3f}")
    print(f"  Citation faithfulness:    {agg.citation_faithfulness:.3f}")
    print(f"  Latency p50:              {agg.p50_latency_ms:.1f} ms")
    print(f"  Latency p95:              {agg.p95_latency_ms:.1f} ms")
    print("\n=== BY DIFFICULTY ===")
    for d, m in sorted(by_diff.items()):
        print(f"  [{d:6s}]  n={int(m['n']):3d}  "
              f"rel={m['mean_answer_relevance']:.3f}  "
              f"hit={m['retrieval_hit_rate']:.3f}  "
              f"faith={m['citation_faithfulness']:.3f}")
    print(f"\nResults -> {OUT_PATH}")


if __name__ == "__main__":
    main()
