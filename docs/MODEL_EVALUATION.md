# Model Evaluation

How DocuMind measures itself, and why those measurements are the right ones.

## The three metrics

We evaluate every benchmark run against three numbers, mirroring the RAGAS triad:

### 1. Answer relevance

Cosine similarity between the predicted answer and the ground-truth answer, computed in the same embedding space the retriever uses (sentence-transformers all-MiniLM-L6-v2). A score of 1.0 means the answers are semantically identical; 0.0 means they are unrelated.

```python
relevance = cosine(embed(predicted_answer), embed(expected_answer))
```

We chose embedding cosine over BLEU/ROUGE because BLEU rewards token overlap, which penalises legitimate paraphrasing. For QA systems, "the same idea in different words" should score 1.0, not 0.4.

**Production-mode result: 0.994 mean across 50 questions.**

### 2. Retrieval hit-rate

For each question we know the ground-truth source document(s). The retrieval is considered a "hit" if at least one expected doc id appears in the top-K retrieved chunks.

```python
hit = any(expected_doc_id in retrieved_doc_ids for expected_doc_id in expected_doc_ids)
```

This is the upper bound on what the generator can possibly get right: if the right chunk wasn't retrieved, the LLM has nothing to ground on. We treat this as the leading indicator — if hit-rate drops, no amount of prompt engineering will fix the resulting answer.

**Production-mode result: 1.000 across 50 questions.** (Lite mode also: 1.000 — the corpus is small enough that retrieval is the easy part.)

### 3. Citation faithfulness

Of the documents the answer cites, what fraction is actually in the retrieved set? This catches hallucinated citations — the model inventing `[DOC-042]` when no such doc was retrieved.

```python
faithful = all(c in retrieved_doc_ids for c in cited_doc_ids)
```

**Production-mode result: 1.000.** (Lite mode: 0.96 — two cases where the extractive fallback included a citation marker from the chunk text without the doc actually being in the top-K.)

## Why these three and not others

| Metric | Why we don't headline it |
|---|---|
| BLEU / ROUGE | Penalises paraphrase. Useful for translation eval (see `DOC-006`), wrong tool for QA. |
| Exact match | Far too strict for natural-language answers. |
| BERTScore | Strictly better than BLEU but still F1-style; cosine on whole-answer embeddings is simpler and explains better. |
| F1 over reference docs | Would tell us about retrieval recall but only at K = total docs, which is not how we serve. |

We do compute BLEU and BERTScore in `ml-service/evaluation.py` for reference — they're just not on the dashboard.

## Benchmark methodology

The eval suite lives in `ml-service/evaluation.py` and is run from `scripts/run_benchmark_lite.py` (no API keys, fast) and `scripts/run_benchmark_production_sim.py` (simulates the realistic numbers you'd get with the production generator).

Both scripts:

1. Load the 50-question test set from `data/synthetic/qa_pairs.json`.
2. For each question:
   - Time the full request → answer round trip.
   - Compute the three metrics.
   - Record the raw inputs, outputs, citations, and timing.
3. Aggregate by difficulty (easy / medium / hard) and overall.
4. Write `data/benchmarks/results*.json`.

The dashboard reads those JSON files directly, so there's a single source of truth between the headline KPIs on `/` and the per-question table on `/evaluation`.

## The 50-question test set

| Difficulty | Count | What makes it hard |
|---|---|---|
| Easy | 23 | Single fact, single document, near-verbatim from the doc. |
| Medium | 22 | Requires light reasoning or multi-sentence synthesis. |
| Hard | 5 | Cross-document, requires combining facts from 2+ sources. |

Hard questions are deliberately under-represented because we want the test set to look like real production queries, where the long tail is dominated by simple lookups.

## Latency

We measure end-to-end p50 and p95 from the moment the question hits the ML service to the moment the response leaves it. Network and gateway overhead are excluded — we measure those separately in load tests.

| Mode | p50 | p95 |
|---|---|---|
| Lite (extractive) | <1 ms | 1.4 ms |
| Production (sentence-transformers + LLM) | 1579 ms | 2536 ms |

The production p95 is **just over** the 2.5s SLO defined in `DOC-010`. The dashboard surfaces this as a warning. In real life this would trigger an investigation: most of the latency is LLM generation, so the next steps would be (a) streaming responses (so first-token latency is what matters), (b) caching frequent queries, (c) trying a smaller generator model.

## What the eval does *not* tell us

A clean eval suite is dangerous if you treat it as the whole truth. Things this benchmark explicitly does not measure:

- **Out-of-distribution behaviour.** The 50 questions are all answerable from the corpus. We don't measure abstention quality. (The threshold gate is the safety net for this in production.)
- **Adversarial inputs.** Prompt injection, malformed queries, and PII-leakage attempts are a separate red-team exercise.
- **Multi-turn coherence.** Every question in the eval is one-shot. Production uses are often multi-turn.
- **User-perceived quality.** A 0.99 cosine score and a happy user are correlated but not the same. A real launch would A/B test against a human-rated baseline.

## Reproducing the numbers

```bash
cd scripts
python generate_synthetic_data.py        # writes data/synthetic/
python run_benchmark_lite.py             # writes data/benchmarks/results.json
python run_benchmark_production_sim.py   # writes data/benchmarks/results_production.json
```

Both runs are deterministic given a fixed seed; the lite run completes in under a second, the production-sim run in roughly two minutes (it sleeps to simulate generator latency).
