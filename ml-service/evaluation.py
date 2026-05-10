"""
Evaluation Module for SMP DocuMind
===================================

Implements the metrics specified in the JD:
    "Evaluate model performance based on output quality (e.g., translation
    accuracy, answer relevance, or language naturalness)."

Three metrics are reported:

1. Answer Relevance
       Embedding cosine similarity between the predicted answer and the
       expected answer. Range [-1, 1]; we report scaled to [0, 1].

2. Retrieval Hit Rate @ K
       Fraction of questions where at least one retrieved chunk comes
       from the ground-truth source document.

3. Citation Faithfulness
       Of the citations produced, fraction that overlap with the ground
       truth source_doc_id.

These metrics map cleanly onto industry RAG evaluation frameworks
(e.g. RAGAS) but stay self-contained for this project.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Any

import numpy as np
from sentence_transformers import SentenceTransformer

from rag_pipeline import RAGPipeline, EMBEDDING_MODEL


ROOT = Path(__file__).resolve().parent.parent
QA_PATH = ROOT / "data" / "synthetic" / "qa_pairs.json"
OUT_PATH = ROOT / "data" / "benchmarks" / "results.json"
OUT_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class PerQuestionResult:
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
class AggregateResult:
    n: int
    mean_answer_relevance: float
    retrieval_hit_rate: float
    citation_faithfulness: float
    p50_latency_ms: float
    p95_latency_ms: float
    by_difficulty: Dict[str, Dict[str, float]] = field(default_factory=dict)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


def evaluate(pipeline: RAGPipeline,
             qa_pairs: List[Dict[str, Any]]) -> tuple[List[PerQuestionResult], AggregateResult]:
    """Run the pipeline against every Q&A pair and compute metrics."""
    embedder = SentenceTransformer(EMBEDDING_MODEL)
    per_q: List[PerQuestionResult] = []

    for pair in qa_pairs:
        expected_docs = [d.strip() for d in pair["source_doc_id"].split(",")]
        t0 = time.perf_counter()
        ans = pipeline.ask(pair["question"])
        latency_ms = (time.perf_counter() - t0) * 1000

        # Answer relevance via cosine similarity in embedding space.
        emb_pred, emb_exp = embedder.encode(
            [ans.text, pair["expected_answer"]],
            normalize_embeddings=True,
        )
        relevance = cosine(np.asarray(emb_pred), np.asarray(emb_exp))
        # Map [-1,1] -> [0,1] for easier interpretation in dashboards.
        relevance_scaled = max(0.0, (relevance + 1) / 2)

        retrieved_doc_ids = {r.chunk.doc_id for r in ans.retrieved_chunks}
        retrieval_hit = bool(retrieved_doc_ids & set(expected_docs))

        cited = set(ans.citations)
        citation_faithful = bool(cited & set(expected_docs)) if cited else False

        per_q.append(PerQuestionResult(
            qa_id=pair["qa_id"],
            question=pair["question"],
            expected_answer=pair["expected_answer"],
            predicted_answer=ans.text,
            expected_doc_ids=expected_docs,
            predicted_citations=sorted(cited),
            answer_relevance=relevance_scaled,
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
    for diff in {p.difficulty for p in per_q}:
        subset = [p for p in per_q if p.difficulty == diff]
        by_diff[diff] = {
            "n": len(subset),
            "mean_answer_relevance": float(np.mean([p.answer_relevance for p in subset])),
            "retrieval_hit_rate": float(np.mean([p.retrieval_hit for p in subset])),
            "citation_faithfulness": float(np.mean([p.citation_faithful for p in subset])),
        }

    agg = AggregateResult(
        n=len(per_q),
        mean_answer_relevance=float(np.mean(rel)),
        retrieval_hit_rate=float(np.mean(hits)),
        citation_faithfulness=float(np.mean(faith)),
        p50_latency_ms=float(np.percentile(lat, 50)),
        p95_latency_ms=float(np.percentile(lat, 95)),
        by_difficulty=by_diff,
    )

    return per_q, agg


def main() -> None:
    qa_pairs = json.loads(QA_PATH.read_text(encoding="utf-8"))
    pipeline = RAGPipeline()
    n_chunks = pipeline.ingest()
    print(f"Indexed {n_chunks} chunks. Running evaluation on {len(qa_pairs)} questions...")

    per_q, agg = evaluate(pipeline, qa_pairs)

    payload = {
        "summary": asdict(agg),
        "per_question": [asdict(p) for p in per_q],
        "config": {
            "embedding_model": EMBEDDING_MODEL,
            "top_k_final": 4,
        },
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print("\n=== AGGREGATE RESULTS ===")
    print(f"  Mean answer relevance:    {agg.mean_answer_relevance:.3f}")
    print(f"  Retrieval hit rate:       {agg.retrieval_hit_rate:.3f}")
    print(f"  Citation faithfulness:    {agg.citation_faithfulness:.3f}")
    print(f"  Latency p50:              {agg.p50_latency_ms:.0f} ms")
    print(f"  Latency p95:              {agg.p95_latency_ms:.0f} ms")
    print(f"\nFull results -> {OUT_PATH}")


if __name__ == "__main__":
    main()
