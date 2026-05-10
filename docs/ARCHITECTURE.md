# Architecture

## System overview

SMP DocuMind is a three-service application following a deliberate separation between the user-facing dashboard, a typed API gateway, and the ML compute layer. This is the same shape you'd find in a production internal tool: each service can be deployed, scaled, and reasoned about independently.

```
                     ┌─────────────────────────────────────────────────────────────┐
                     │                       USER (browser)                        │
                     └──────────────────────────────┬──────────────────────────────┘
                                                    │  HTTPS
                                                    ▼
        ┌─────────────────────────────────────────────────────────────────────────┐
        │                         FRONTEND  (Next.js 14, TS)                     │
        │  ─────────────────────────────────────────────────────────────────     │
        │   Routes:  /  /chat  /documents  /evaluation  /settings                │
        │   Stack:   App Router · Tailwind · Recharts · lucide-react             │
        │   Talks to: backend gateway only — never the ML service directly       │
        └──────────────────────────────┬──────────────────────────────────────────┘
                                       │  fetch /api/ask · /api/documents · /api/metrics
                                       ▼
        ┌─────────────────────────────────────────────────────────────────────────┐
        │                    BACKEND GATEWAY  (Express, TS)                      │
        │  ─────────────────────────────────────────────────────────────────     │
        │   Middleware:                                                          │
        │     · CORS (locked to dashboard origin)                                │
        │     · pino structured logging                                          │
        │     · zod request schemas (typed in/out)                               │
        │     · rate limiter (60 req/min per IP)                                 │
        │     · audit log appender  →  backend/audit-log.jsonl                   │
        │   Service client: axios → ML service                                   │
        └──────────────────────────────┬──────────────────────────────────────────┘
                                       │  POST /ask  GET /documents  GET /metrics
                                       ▼
        ┌─────────────────────────────────────────────────────────────────────────┐
        │                       ML SERVICE  (FastAPI)                            │
        │  ─────────────────────────────────────────────────────────────────     │
        │   RAG pipeline:                                                        │
        │     1. Chunk documents (~420 tok, 60 tok overlap)                      │
        │     2. Embed with sentence-transformers (all-MiniLM-L6-v2)             │
        │     3. Index — dense (FAISS-style cosine) + sparse (BM25)              │
        │     4. Retrieve top-K, fuse 0.6 dense / 0.4 sparse                     │
        │     5. Threshold gate (≥0.30 fused score)                              │
        │     6. Generate (LLM via OpenAI  OR  extractive fallback)              │
        │     7. Return answer + citations + confidence                          │
        └──────────────────────────────┬──────────────────────────────────────────┘
                                       │
                                       ▼
        ┌─────────────────────────────────────────────────────────────────────────┐
        │                      KNOWLEDGE BASE  (filesystem)                      │
        │  10 markdown documents, 6 categories, ~12 KB total                     │
        └─────────────────────────────────────────────────────────────────────────┘
```

## Why three services and not one

A single FastAPI app could host both the API and the ML, and a Next.js API route could replace the gateway. We deliberately split:

| Boundary | Reason |
|---|---|
| Frontend ↔ Backend | The gateway owns auth, rate-limit, and audit. Putting that in Next.js mixes concerns and forces every developer working on the UI to also reason about compliance. |
| Backend ↔ ML service | The ML service has a 500 MB embedding-model dependency and a slow cold-start. Wrapping it in a thin TS gateway means the UI can stay snappy and the ML pod can be scheduled independently (e.g. on a GPU node in production). |

## Data flow for a single question

1. The user types a question in `/chat`. The dashboard calls `POST /api/ask` on the gateway.
2. The gateway validates the body with `zod`, applies the rate limiter, generates a request id, and appends a `received` event to the audit log.
3. The gateway forwards to the ML service `POST /ask`.
4. The ML service:
   1. Embeds the query.
   2. Runs hybrid retrieval against the in-memory index, returning top-K chunks with fused scores.
   3. If the top fused score is below 0.30, it abstains and returns `{ answer: "I don't have enough information…", citations: [] }`.
   4. Otherwise it builds a prompt (see `DOC-009`) and calls either OpenAI or the extractive fallback.
   5. Returns `{ answer, citations[], confidence, latency_ms }`.
5. The gateway appends a `responded` event to the audit log (with citations and latency) and forwards the payload to the UI.
6. The UI renders the answer with citation chips that link to `/documents/<doc_id>`.

## Design decisions worth defending

**Hybrid retrieval over dense-only.** Dense embeddings cluster paraphrases; BM25 nails rare technical tokens (model names, error codes, regex patterns). The 0.6/0.4 weighting was tuned on the 50-question eval set — at 1.0/0.0 (dense only) we lose 4 questions on rare-keyword queries; at 0.0/1.0 (BM25 only) we lose 6 on paraphrased questions.

**Threshold abstention over always-answer.** A confidently wrong answer is worse than no answer in an enterprise QA setting. The 0.30 fused-score gate catches genuinely off-topic questions before the LLM invents an answer.

**Extractive fallback.** Without an OpenAI key, the system uses the top retrieved chunk as the answer body. Relevance drops (we measured 21%) but retrieval and faithfulness stay high. This means: (a) anyone can clone and demo without secrets, (b) we can run the whole eval suite in CI without paying for API calls, (c) we have a way to A/B test retrieval changes independent of generator changes.

**Append-only JSONL audit log.** Required by `DOC-003` and `DOC-004`. JSONL plays well with `jq` and with log-shipping pipelines, and append-only means we never have to reason about row-level updates.

**Brand tokens in CSS variables.** Listed in `tailwind.config.ts` and `app/globals.css`. Swapping to SMP Technology's actual palette is a one-file change. See `BRAND_GUIDELINES.md`.

## What is intentionally simplified

| Production concern | Demo behaviour | Production approach |
|---|---|---|
| Vector index | In-memory NumPy + cosine | Managed vector DB (pgvector / Qdrant) — see `DOC-008` |
| Auth | Unauthenticated dashboard | OIDC / SSO at the gateway, role propagated to ML svc |
| Document refresh | Restart the ML service | Watch + re-index pipeline triggered by KB writes |
| Streaming | Full payload after generation | SSE from gateway → UI for token-by-token |
| Multi-tenancy | Single shared index | Per-team index with row-level filters |

These are explicit choices, not oversights. Each one has a paragraph in `DOC-010` and a TODO in the relevant service.
