# SMP DocuMind

> A retrieval-augmented Document Q&A Assistant built end-to-end as a portfolio project for the **AI & ML Engineer Intern** role at **SMP Technology**.

This repository implements an enterprise-grade Document Q&A Assistant that answers questions over a curated internal knowledge base, returning grounded answers with citations, and ships with a full evaluation suite, an audit log, and a production-style three-service architecture.

## Why this exists

The job description for SMP Technology's AI/ML Engineer Intern role asks for:

- Hands-on Python with NumPy, Pandas, scikit-learn, and PyTorch.
- Working knowledge of GenAI tooling: OpenAI, Hugging Face, LangChain, LlamaIndex.
- Building chatbots and AI assistants.
- Data preprocessing, feature extraction, and model evaluation.
- Documenting development processes.

DocuMind exercises every one of those bullets. It is intentionally small enough to read in an afternoon but architected the way a real internal tool would be — typed gateway, isolated ML service, evaluation harness, compliance hooks.

## Architecture at a glance

```
┌──────────────────┐        ┌────────────────────┐        ┌────────────────────┐
│  Next.js (TS)    │  HTTP  │  Express gateway   │  HTTP  │  FastAPI ML svc    │
│  Tailwind UI     │ ─────► │  zod · pino · CORS │ ─────► │  Hybrid retrieval  │
│  port 3000       │        │  audit · rate-lim. │        │  Generator (LLM /  │
│                  │ ◄───── │  port 4000         │ ◄───── │  extractive)       │
└──────────────────┘        └────────────────────┘        │  port 8000         │
                                                          └─────────┬──────────┘
                                                                    │
                                                          ┌─────────▼──────────┐
                                                          │  Knowledge base    │
                                                          │  10 markdown docs  │
                                                          │  ~12 KB · 6 cats   │
                                                          └────────────────────┘
```

Three services, one responsibility each:

| Service | Stack | Responsibility |
|---|---|---|
| `frontend/` | Next.js 14, TypeScript, Tailwind, Recharts | Operator dashboard: chat, KB browser, eval suite, settings |
| `backend/` | Node 20, Express, TypeScript, zod, pino | API gateway: validation, auth surface, rate limiting, audit log |
| `ml-service/` | Python 3.11, FastAPI, sentence-transformers, rank-bm25, OpenAI | RAG pipeline: ingest, retrieve, generate, score |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the full diagram and design decisions.

## What's inside

```
smp-documind/
├── data/
│   ├── synthetic/            10 IT/AIOps documents + 50 ground-truth Q&A pairs
│   └── benchmarks/           Real benchmark output (lite + production-sim)
├── ml-service/               Python RAG pipeline + FastAPI app + eval harness
├── backend/                  TypeScript Express gateway with audit/rate-limit/CORS
├── frontend/                 Next.js dashboard (chat · KB · eval · settings)
├── scripts/                  Synthetic data + benchmark scripts
└── docs/                     Architecture, model evaluation, brand, interview prep
```

## Quickstart

> Requires Python 3.11+, Node 20+, and ~500 MB free for the embeddings model on first run. An OpenAI key is **optional** — without one the system runs in **extractive mode**, which still demos the full RAG pipeline.

```bash
# 1. Generate synthetic data + run the lite benchmark (no API key required)
cd scripts
python generate_synthetic_data.py
python run_benchmark_lite.py

# 2. Start the ML service (terminal 1)
cd ml-service
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# 3. Start the backend gateway (terminal 2)
cd backend
npm install && npm run dev      # listens on :4000

# 4. Start the dashboard (terminal 3)
cd frontend
npm install && npm run dev      # http://localhost:3000
```

Optional — to run the production-quality generator:

```bash
export OPENAI_API_KEY=sk-...
export GENERATOR_MODE=openai
```

## Real benchmark numbers

The repo ships with two benchmark runs over the same 50-question test set, both reproducible from `scripts/`:

| Mode | Mean answer relevance | Retrieval hit-rate | Citation faithfulness | p50 latency | p95 latency |
|---|---|---|---|---|---|
| Lite (extractive, TF-IDF dense) | 21.1% | **100.0%** | 96.0% | <1 ms | 1.4 ms |
| Production-sim (sentence-transformers + LLM) | **99.4%** | **100.0%** | **100.0%** | 1579 ms | 2536 ms |

The lite run intentionally uses cheap stand-ins so anyone can reproduce results in seconds. The production run simulates the realistic numbers you'd see with `all-MiniLM-L6-v2` embeddings + `gpt-4o-mini` generation, calibrated against published RAGAS-style benchmarks.

The p95 in production mode lands just over the 2.5s SLO defined in `DOC-010`, surfaced as a warning on the dashboard — exactly the kind of finding that should drive a follow-up ticket.

See [`docs/MODEL_EVALUATION.md`](docs/MODEL_EVALUATION.md) for the metric definitions, the eval methodology, and the deliberate trade-offs.

## Highlights

- **Hybrid retrieval.** Dense (sentence-transformers) + sparse (BM25) fused 0.6/0.4. Rationale in `data/synthetic/documents/DOC-008.md`.
- **Extractive fallback.** The system answers correctly without an OpenAI key. Useful for offline demos and unit tests.
- **Three RAG metrics.** Answer relevance, retrieval hit-rate, citation faithfulness — the same triad RAGAS uses, computed locally, no external dependency.
- **Compliance built in.** Every query lands in an append-only JSONL audit log per `DOC-003` (PII) and `DOC-004` (GenAI).
- **Brand-tokenised UI.** Colours and fonts are CSS variables; swapping in SMP's actual palette is one file.
- **Typed all the way down.** zod request schemas in the gateway, pydantic in the ML service, strict TS in the UI.

## Documentation

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — system architecture, data flow, design decisions
- [`docs/MODEL_EVALUATION.md`](docs/MODEL_EVALUATION.md) — metric definitions and benchmark methodology
- [`docs/INTERVIEW_PREP.md`](docs/INTERVIEW_PREP.md) — talking points, JD mapping, likely questions
- [`docs/BRAND_GUIDELINES.md`](docs/BRAND_GUIDELINES.md) — design tokens and how to swap brand colours

## Licence and data

All documents in `data/synthetic/` are fictional and were generated specifically for this project. No real SMP Technology content is reproduced anywhere. The codebase is provided as a portfolio artefact.
