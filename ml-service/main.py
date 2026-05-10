"""
FastAPI Service for SMP DocuMind
=================================

Exposes the RAG pipeline over HTTP for the TypeScript backend to call.

Endpoints
---------
GET  /health                     -> liveness probe
POST /ask                        -> answer a question
GET  /documents                  -> list ingested documents
GET  /metrics                    -> latest evaluation results (cached)

Run locally:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import json
from dotenv import load_dotenv
load_dotenv()
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from rag_pipeline import RAGPipeline


ROOT = Path(__file__).resolve().parent.parent
INDEX_PATH = ROOT / "data" / "synthetic" / "document_index.json"
METRICS_PATH = ROOT / "data" / "benchmarks" / "results.json"


# ------------------------------------------------------------------
# Pydantic schemas
# ------------------------------------------------------------------
class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(4, ge=1, le=10)


class CitationRef(BaseModel):
    doc_id: str
    title: str


class RetrievedChunk(BaseModel):
    doc_id: str
    title: str
    text: str
    score: float


class AskResponse(BaseModel):
    answer: str
    citations: List[CitationRef]
    retrieved: List[RetrievedChunk]
    used_generator: str
    latency_ms: float
    aborted_low_relevance: bool


class DocumentSummary(BaseModel):
    doc_id: str
    title: str
    category: str
    tags: List[str]
    last_updated: str
    char_count: int


class HealthResponse(BaseModel):
    status: str
    chunks_indexed: int
    generator_mode: str


# ------------------------------------------------------------------
# Lifespan: warm up the pipeline once at startup
# ------------------------------------------------------------------
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    pipeline = RAGPipeline()
    n = pipeline.ingest()
    _state["pipeline"] = pipeline
    _state["chunks"] = n
    yield
    _state.clear()


app = FastAPI(
    title="SMP DocuMind ML Service",
    version="1.0.0",
    description="Retrieval-augmented Q&A over the SMP knowledge base.",
    lifespan=lifespan,
)

# Allow the local Next.js dev server and the Node backend to call us.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4000"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------
# Routes
# ------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    pipeline: Optional[RAGPipeline] = _state.get("pipeline")
    if pipeline is None:
        raise HTTPException(503, "pipeline not initialised")
    mode = "openai" if pipeline._openai_client is not None else "extractive_fallback"
    return HealthResponse(
        status="ok",
        chunks_indexed=_state.get("chunks", 0),
        generator_mode=mode,
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    pipeline: Optional[RAGPipeline] = _state.get("pipeline")
    if pipeline is None:
        raise HTTPException(503, "pipeline not initialised")

    t0 = time.perf_counter()
    ans = pipeline.ask(req.question)
    latency_ms = (time.perf_counter() - t0) * 1000

    titles_by_id = {d["doc_id"]: d["title"]
                    for d in json.loads(INDEX_PATH.read_text(encoding="utf-8"))}

    citations = [
        CitationRef(doc_id=cid, title=titles_by_id.get(cid, cid))
        for cid in ans.citations
    ]
    retrieved = [
        RetrievedChunk(
            doc_id=r.chunk.doc_id,
            title=r.chunk.title,
            text=r.chunk.text,
            score=r.score,
        )
        for r in ans.retrieved_chunks
    ]
    return AskResponse(
        answer=ans.text,
        citations=citations,
        retrieved=retrieved,
        used_generator=ans.used_generator,
        latency_ms=latency_ms,
        aborted_low_relevance=ans.aborted_low_relevance,
    )


@app.get("/documents", response_model=List[DocumentSummary])
def list_documents() -> List[DocumentSummary]:
    if not INDEX_PATH.exists():
        return []
    raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    return [DocumentSummary(**r) for r in raw]


@app.get("/metrics")
def get_metrics():
    if not METRICS_PATH.exists():
        raise HTTPException(404, "no benchmark results yet — run python evaluation.py")
    return json.loads(METRICS_PATH.read_text(encoding="utf-8"))
