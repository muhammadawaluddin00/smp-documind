"""
Synthetic Data Generator for SMP DocuMind
==========================================

Generates a corpus of synthetic IT operations / AIOps documents and a
paired Q&A evaluation set, modeled on the kind of internal knowledge base
an enterprise tech company (e.g. SMP Technology) would maintain.

Outputs:
    data/synthetic/documents/*.md         -> 10 source documents
    data/synthetic/qa_pairs.json          -> 50 evaluation Q&A pairs
    data/synthetic/document_index.json    -> document metadata

Why this design:
    The job description emphasizes Generative AI for chatbots / virtual
    assistants and document understanding. To evaluate a Document Q&A
    system, we need (a) a realistic corpus and (b) ground-truth Q&A pairs
    so we can benchmark retrieval quality and answer faithfulness.

Run:
    python scripts/generate_synthetic_data.py
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any

random.seed(42)  # Reproducibility — important for benchmarks.

# ------------------------------------------------------------------
# Output paths (resolved relative to the repository root)
# ------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "data" / "synthetic" / "documents"
QA_PATH = ROOT / "data" / "synthetic" / "qa_pairs.json"
INDEX_PATH = ROOT / "data" / "synthetic" / "document_index.json"

DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------------
# Document definitions
# ------------------------------------------------------------------
@dataclass
class Document:
    doc_id: str
    title: str
    category: str
    content: str
    tags: List[str]
    last_updated: str


DOCUMENTS: List[Document] = [
    Document(
        doc_id="DOC-001",
        title="AIOps Incident Response Playbook",
        category="Operations",
        content="""# AIOps Incident Response Playbook

## 1. Scope
This playbook governs how the AIOps platform responds to production
incidents detected by the anomaly detection engine. It applies to all
Tier-1 and Tier-2 services integrated with the SMP monitoring stack.

## 2. Severity Classification
Severity is assigned automatically by the classifier and may be escalated
manually by the on-call engineer.

- **SEV-1**: Customer-facing outage; revenue impact > $10K/hour. Page the on-call lead within 2 minutes.
- **SEV-2**: Degraded service; partial functionality unavailable. Notify the channel within 5 minutes.
- **SEV-3**: Internal-only impact; no customer-visible degradation. Acknowledge within 30 minutes.
- **SEV-4**: Cosmetic or low-priority defect. Triage during business hours.

## 3. Escalation Path
First responder is the primary on-call engineer. If unacknowledged after
10 minutes, the alert escalates to the secondary on-call engineer. After
20 minutes, the incident commander is paged automatically.

## 4. Post-Incident Review
A blameless post-mortem is mandatory for every SEV-1 and SEV-2 incident.
The post-mortem must be published within 5 business days and include:
root cause, contributing factors, customer impact, and three concrete
follow-up actions with assigned owners.
""",
        tags=["aiops", "incident", "playbook", "on-call"],
        last_updated="2025-09-14",
    ),
    Document(
        doc_id="DOC-002",
        title="Machine Learning Model Deployment Standard",
        category="Engineering",
        content="""# Machine Learning Model Deployment Standard

## 1. Purpose
Standardizes how ML models move from a research notebook to a
production-served endpoint inside SMP infrastructure.

## 2. Required Artifacts
Every model promoted to staging must include:

1. A versioned model file (ONNX, TorchScript, or pickled scikit-learn).
2. A `model_card.md` describing intended use, training data, and known
   failure modes.
3. A `requirements.txt` pinned to exact versions.
4. An evaluation report containing metrics on the held-out test set.

## 3. Approval Gates
Models pass through three gates before serving production traffic:

- **Gate A (Code review)**: Two engineers approve the training pipeline.
- **Gate B (Offline metrics)**: Accuracy, F1, or task-specific metric must
  beat the current production baseline by at least 1% absolute.
- **Gate C (Shadow traffic)**: The candidate runs alongside production
  for 7 days, processing live traffic without serving responses to users.

## 4. Rollout Strategy
Default rollout is canary at 1% -> 10% -> 50% -> 100% with 24 hours of
observation between each step. Automatic rollback is triggered if the
golden-signal error rate exceeds 0.5% above the previous version.
""",
        tags=["mlops", "deployment", "engineering", "model-card"],
        last_updated="2025-10-02",
    ),
    Document(
        doc_id="DOC-003",
        title="Data Privacy and PII Handling Policy",
        category="Compliance",
        content="""# Data Privacy and PII Handling Policy

## 1. Definitions
**Personally Identifiable Information (PII)** includes any data that can
identify a natural person directly or indirectly. Examples: full name,
national ID, email, phone, IP address, biometric data.

## 2. Storage Requirements
PII at rest must be encrypted using AES-256. Encryption keys are managed
by the central KMS and rotated every 90 days. Plaintext PII must never
be written to logs, monitoring traces, or analytics events.

## 3. Access Control
Access to PII tables follows least-privilege. All access requires a
documented business justification and is logged in the audit pipeline.
Read access is granted for a maximum of 30 days; renewals require fresh
manager approval.

## 4. Use in Machine Learning
ML training datasets containing PII must be either (a) de-identified
through tokenization or hashing, or (b) processed inside the secure
enclave with no model artifact carrying memorized PII out. Membership
inference and extraction attacks must be tested before release.

## 5. Breach Notification
Suspected PII breaches must be reported to the Data Protection Officer
within 1 hour of detection. Regulatory notification follows the timelines
mandated by the applicable jurisdiction (GDPR: 72 hours; UU PDP
Indonesia: 3x24 hours).
""",
        tags=["compliance", "privacy", "pii", "security"],
        last_updated="2025-08-20",
    ),
    Document(
        doc_id="DOC-004",
        title="Generative AI Usage Guidelines for Employees",
        category="Compliance",
        content="""# Generative AI Usage Guidelines for Employees

## 1. Approved Tools
Only Generative AI tools listed in the central AI registry may be used
for company work. Currently approved: SMP-internal LLM gateway, OpenAI
(via enterprise account), and the on-prem Llama-3 inference cluster.

## 2. Prohibited Inputs
Employees must never paste the following into any Generative AI tool:

- Customer PII or credentials
- Proprietary source code from restricted repositories
- Unreleased financial figures
- Information classified as Confidential or Restricted

## 3. Output Validation
Generated content must be reviewed by a human subject-matter expert
before being committed to production code, customer communication, or
official documentation. Hallucinations and confident errors are
expected; treat every generation as a draft.

## 4. Attribution
When Generative AI substantially contributed to a deliverable, the
contribution must be disclosed in the document footer or commit message.

## 5. Training Data
Submitting company data to vendors that retain prompts for training is
prohibited unless an explicit zero-data-retention agreement is in place
and approved by the Legal team.
""",
        tags=["genai", "policy", "compliance", "guidelines"],
        last_updated="2025-11-05",
    ),
    Document(
        doc_id="DOC-005",
        title="Customer Support Chatbot Architecture",
        category="Architecture",
        content="""# Customer Support Chatbot Architecture

## 1. Overview
The Customer Support Chatbot resolves Tier-1 inquiries using a
retrieval-augmented generation (RAG) pipeline backed by the company
knowledge base. It currently handles 65% of incoming tickets without
human escalation.

## 2. Components
- **Frontend**: React widget embedded in the support portal.
- **API Gateway**: TypeScript service handling auth, rate limiting, and
  conversation state.
- **Retriever**: Hybrid BM25 + dense (sentence-transformers/all-MiniLM-L6-v2)
  retrieval over the knowledge base, reranked with a cross-encoder.
- **Generator**: LLM (Llama-3-8B-instruct, fine-tuned on ticket data) with
  few-shot prompting and citation enforcement.
- **Guardrails**: Output classifier for unsafe content, plus a relevance
  filter that aborts the response if retrieval similarity is below 0.45.

## 3. Latency Budget
End-to-end p95 latency must stay under 2.5 seconds. Budget allocation:
retrieval 300 ms, generation 1800 ms, network and overhead 400 ms.

## 4. Escalation
The bot escalates to a human agent if (a) the user explicitly requests
it, (b) the safety classifier fires, (c) the same user has asked three
unresolved questions in a row, or (d) the topic is on the
no-bot-allowed list (billing disputes, account closure, legal threats).

## 5. Evaluation
Quality is measured weekly on a frozen 500-question evaluation set.
Targets: answer relevance >= 0.85, citation faithfulness >= 0.90,
deflection rate >= 0.60.
""",
        tags=["chatbot", "rag", "architecture", "llm"],
        last_updated="2025-10-18",
    ),
    Document(
        doc_id="DOC-006",
        title="Translation Quality Evaluation Standard",
        category="Engineering",
        content="""# Translation Quality Evaluation Standard

## 1. Scope
Defines how we evaluate machine-translated output across the SMP
multilingual product surfaces (Bahasa Indonesia, English, Mandarin,
Japanese).

## 2. Automatic Metrics
We report three complementary metrics on every release candidate:

- **BLEU-4**: Surface-level n-gram overlap. Useful for regression
  detection, less useful for absolute quality.
- **chrF++**: Character-level F-score. More robust than BLEU for
  morphologically rich languages.
- **BERTScore (F1)**: Embedding-level semantic similarity, computed with
  a multilingual XLM-R backbone.

## 3. Human Evaluation
Two professional linguists per language pair score 200 sampled segments
on a 1-5 Likert scale across Adequacy and Fluency. Inter-annotator
agreement (Cohen's kappa) must be >= 0.6, otherwise the evaluation is
discarded and re-run with a calibration session.

## 4. Release Gate
A model may ship only if BLEU-4 has not regressed by more than 0.5
points and average human Adequacy is >= 4.0/5.

## 5. Domain Adaptation
For technical-support translation, we use in-domain fine-tuning data
mined from past tickets. The base model is NLLB-200 distilled to 600M
parameters; LoRA adapters carry the domain weights.
""",
        tags=["translation", "evaluation", "bleu", "bertscore"],
        last_updated="2025-09-30",
    ),
    Document(
        doc_id="DOC-007",
        title="On-Call Engineer Onboarding Guide",
        category="Operations",
        content="""# On-Call Engineer Onboarding Guide

## 1. Eligibility
An engineer becomes on-call eligible after (a) 90 days of tenure on the
team, (b) two shadow shifts with a senior engineer, and (c) passing the
runbook quiz with a score of at least 80%.

## 2. Schedule
Primary rotations are 7 days, Monday 09:00 to the following Monday
09:00 Jakarta time. Secondary rotations are 14 days. Engineers may swap
shifts up to 48 hours before the start time without manager approval.

## 3. Tooling
On-call engineers must have these installed and tested before their
first shift: PagerDuty mobile app, the SMP CLI (smpctl), VPN client,
and the runbook viewer.

## 4. First-Hour Response
For any page during a shift, the engineer is expected to:

1. Acknowledge the page within 5 minutes.
2. Open the relevant runbook within 10 minutes.
3. Post a status update in the incident channel within 15 minutes.
4. Decide on mitigate-vs-investigate by minute 20.

## 5. Compensation
On-call hours are compensated at 0.25x base hourly rate while not
actively engaged, and 1.5x while actively engaged on an incident.
""",
        tags=["on-call", "onboarding", "operations"],
        last_updated="2025-07-11",
    ),
    Document(
        doc_id="DOC-008",
        title="Vector Database Selection Rationale",
        category="Architecture",
        content="""# Vector Database Selection Rationale

## 1. Background
SMP needed to choose a vector database to back the RAG retrieval layer
of the Customer Support Chatbot and DocuMind. We evaluated three
candidates over four weeks.

## 2. Candidates Evaluated
- **FAISS (in-process)**: Library, no managed service. Lowest latency
  but no replication; loses data on pod restart unless persisted.
- **pgvector (Postgres extension)**: Reuses the existing Postgres
  fleet. Strong consistency, simple operationally, weaker recall at
  scale beyond ~10M vectors.
- **Qdrant (self-hosted)**: Purpose-built, supports filters, payload
  indexing, and hybrid search natively. Adds an operational surface.

## 3. Decision
We chose **Qdrant** for the production deployment because (a) the
filter pushdown is critical for tenant-scoped retrieval, (b) hybrid
search is supported out of the box, and (c) it scales horizontally
without rebuilding the index.

We retain **FAISS** for offline evaluation, prototyping, and unit
tests where reproducibility outweighs operational concerns.

## 4. Embedding Model
We standardize on `sentence-transformers/all-MiniLM-L6-v2` for English
and `intfloat/multilingual-e5-base` for cross-lingual retrieval.
Embedding dimensionality: 384 (MiniLM), 768 (E5).
""",
        tags=["vector-db", "rag", "architecture", "qdrant", "faiss"],
        last_updated="2025-10-25",
    ),
    Document(
        doc_id="DOC-009",
        title="Prompt Engineering Best Practices",
        category="Engineering",
        content="""# Prompt Engineering Best Practices

## 1. Structure
Every production prompt should contain four sections in this order:
role, task, context, output format. Anything more is a smell; consider
splitting into multiple LLM calls.

## 2. Role
Set the role explicitly. "You are a customer support agent for a
telecom company in Indonesia" outperforms unscoped prompts on factual
accuracy by roughly 12% on our internal benchmark.

## 3. Few-Shot Examples
Two to four examples are usually optimal. Above five, returns
diminish, and the prompt becomes harder to maintain. Examples should
cover both the success path and at least one edge case.

## 4. Output Format
Always specify the format machine-readably. For structured outputs,
prefer JSON schema in the prompt and validate the response. Reject
and retry once if validation fails; on second failure, return a
fallback.

## 5. Anti-Patterns
- Asking the model to "think step by step" in user-facing responses
  bloats latency and exposes reasoning that confuses end users.
- Stuffing the entire knowledge base into the prompt instead of using
  retrieval. This is brittle and expensive.
- Using temperature > 0 for deterministic tasks (classification,
  extraction). Set it to 0.

## 6. Versioning
Prompts are code. Every prompt change goes through code review,
ships with a changelog entry, and is regression-tested on the eval
set.
""",
        tags=["prompt-engineering", "llm", "best-practices"],
        last_updated="2025-11-12",
    ),
    Document(
        doc_id="DOC-010",
        title="DocuMind System Overview",
        category="Architecture",
        content="""# DocuMind System Overview

## 1. Mission
DocuMind is an internal Document Q&A assistant that lets employees
ask natural-language questions over the company's policy, engineering,
and operations knowledge bases. It returns grounded answers with
citations to the source documents.

## 2. High-Level Architecture
DocuMind is composed of four services:

- **Ingestion service** (Python): chunking, embedding, indexing.
- **ML service** (FastAPI, Python): retrieval, reranking, generation.
- **Backend** (Node.js, TypeScript): auth, conversation state,
  rate limiting, audit logging.
- **Frontend** (Next.js, TypeScript): chat UI, evaluation dashboard,
  document explorer.

## 3. Data Flow
A user question hits the frontend, which calls the backend. The
backend authenticates the user, applies tenant filters, and forwards
the query to the ML service. The ML service retrieves the top-k
chunks, reranks them, prompts the LLM with the chunks and question,
and returns the grounded answer plus citations. The backend logs the
exchange and streams the answer back to the frontend.

## 4. Service Level Objectives
- p95 query latency: < 2.5 seconds end-to-end.
- Answer relevance: >= 0.85 on the evaluation set.
- Citation faithfulness: >= 0.90.
- Availability: 99.5% monthly.

## 5. Out of Scope
DocuMind does not (yet): generate new documents, modify the knowledge
base, take actions on the user's behalf, or operate without a
retrieval grounding step. These are explicit non-goals for the v1
release.
""",
        tags=["documind", "architecture", "overview", "rag"],
        last_updated="2025-11-20",
    ),
]


# ------------------------------------------------------------------
# Q&A pairs (ground truth for evaluation)
# ------------------------------------------------------------------
# Each item: question, expected_answer, source_doc_id, difficulty.
# 'difficulty' is rough: easy = single fact, medium = single doc multi-hop,
# hard = synthesis across multiple documents.
QA_PAIRS: List[Dict[str, Any]] = [
    {"question": "What is the maximum acknowledgement time for a SEV-1 alert?",
     "expected_answer": "On-call lead must be paged within 2 minutes for a SEV-1 incident.",
     "source_doc_id": "DOC-001", "difficulty": "easy"},
    {"question": "When is a blameless post-mortem mandatory?",
     "expected_answer": "For every SEV-1 and SEV-2 incident; it must be published within 5 business days.",
     "source_doc_id": "DOC-001", "difficulty": "easy"},
    {"question": "How long until an unacknowledged page escalates to the secondary on-call engineer?",
     "expected_answer": "After 10 minutes without acknowledgement.",
     "source_doc_id": "DOC-001", "difficulty": "easy"},
    {"question": "When is an incident commander automatically paged?",
     "expected_answer": "Twenty minutes after the original page if it remains unacknowledged.",
     "source_doc_id": "DOC-001", "difficulty": "medium"},
    {"question": "What three artifacts must accompany a model promoted to staging?",
     "expected_answer": "A versioned model file, a model card, a pinned requirements.txt, and an evaluation report.",
     "source_doc_id": "DOC-002", "difficulty": "medium"},
    {"question": "What does Gate B require for a model promotion?",
     "expected_answer": "The candidate must beat the current production baseline by at least 1% absolute on the offline metric.",
     "source_doc_id": "DOC-002", "difficulty": "easy"},
    {"question": "How long is the shadow-traffic period before serving production traffic?",
     "expected_answer": "Seven days.",
     "source_doc_id": "DOC-002", "difficulty": "easy"},
    {"question": "What is the canary rollout schedule?",
     "expected_answer": "1%, then 10%, 50%, 100%, with 24 hours of observation between each step.",
     "source_doc_id": "DOC-002", "difficulty": "medium"},
    {"question": "What error-rate increase triggers automatic rollback?",
     "expected_answer": "Golden-signal error rate exceeding 0.5% above the previous version.",
     "source_doc_id": "DOC-002", "difficulty": "easy"},
    {"question": "What encryption is required for PII at rest?",
     "expected_answer": "AES-256, with keys managed by the central KMS and rotated every 90 days.",
     "source_doc_id": "DOC-003", "difficulty": "easy"},
    {"question": "What are the two acceptable ways to use PII for ML training?",
     "expected_answer": "De-identification through tokenization or hashing, or processing inside the secure enclave with no PII memorized in artifacts.",
     "source_doc_id": "DOC-003", "difficulty": "medium"},
    {"question": "What is the maximum duration of read access to a PII table before renewal?",
     "expected_answer": "Thirty days; renewals require fresh manager approval.",
     "source_doc_id": "DOC-003", "difficulty": "easy"},
    {"question": "Within how many hours must a suspected PII breach be reported to the DPO?",
     "expected_answer": "Within 1 hour of detection.",
     "source_doc_id": "DOC-003", "difficulty": "easy"},
    {"question": "What are the GDPR and UU PDP notification timelines for a PII breach?",
     "expected_answer": "GDPR is 72 hours; UU PDP Indonesia is 3x24 hours.",
     "source_doc_id": "DOC-003", "difficulty": "medium"},
    {"question": "Which Generative AI tools are currently approved for employee use?",
     "expected_answer": "The SMP-internal LLM gateway, OpenAI through the enterprise account, and the on-prem Llama-3 inference cluster.",
     "source_doc_id": "DOC-004", "difficulty": "easy"},
    {"question": "What kinds of inputs are prohibited in Generative AI tools?",
     "expected_answer": "Customer PII or credentials, proprietary source code from restricted repositories, unreleased financial figures, and Confidential or Restricted information.",
     "source_doc_id": "DOC-004", "difficulty": "medium"},
    {"question": "When must Generative AI contributions be disclosed?",
     "expected_answer": "When Generative AI substantially contributed to a deliverable, in the document footer or commit message.",
     "source_doc_id": "DOC-004", "difficulty": "easy"},
    {"question": "Under what condition can company data be sent to a vendor that retains prompts?",
     "expected_answer": "Only with an explicit zero-data-retention agreement approved by Legal.",
     "source_doc_id": "DOC-004", "difficulty": "medium"},
    {"question": "What percentage of Tier-1 inquiries does the Customer Support Chatbot resolve without human escalation?",
     "expected_answer": "Sixty-five percent.",
     "source_doc_id": "DOC-005", "difficulty": "easy"},
    {"question": "Which embedding model does the Customer Support Chatbot use for retrieval?",
     "expected_answer": "sentence-transformers/all-MiniLM-L6-v2, combined with BM25 in a hybrid retriever and reranked by a cross-encoder.",
     "source_doc_id": "DOC-005", "difficulty": "medium"},
    {"question": "What is the end-to-end p95 latency budget for the Customer Support Chatbot?",
     "expected_answer": "Under 2.5 seconds end-to-end.",
     "source_doc_id": "DOC-005", "difficulty": "easy"},
    {"question": "How is the latency budget allocated across components?",
     "expected_answer": "300 ms for retrieval, 1800 ms for generation, and 400 ms for network and overhead.",
     "source_doc_id": "DOC-005", "difficulty": "medium"},
    {"question": "Under what conditions does the chatbot escalate to a human agent?",
     "expected_answer": "When the user requests it, when the safety classifier fires, after three unresolved questions in a row, or when the topic is on the no-bot-allowed list.",
     "source_doc_id": "DOC-005", "difficulty": "medium"},
    {"question": "What is the relevance-filter similarity threshold below which the bot aborts the response?",
     "expected_answer": "0.45.",
     "source_doc_id": "DOC-005", "difficulty": "easy"},
    {"question": "Which three automatic metrics do we report for translation quality?",
     "expected_answer": "BLEU-4, chrF++, and BERTScore F1 computed with a multilingual XLM-R backbone.",
     "source_doc_id": "DOC-006", "difficulty": "medium"},
    {"question": "What is the minimum inter-annotator agreement (kappa) required for human evaluation?",
     "expected_answer": "Cohen's kappa of at least 0.6.",
     "source_doc_id": "DOC-006", "difficulty": "easy"},
    {"question": "What translation release-gate criteria must be met?",
     "expected_answer": "BLEU-4 must not regress by more than 0.5 points, and average human Adequacy must be at least 4.0 out of 5.",
     "source_doc_id": "DOC-006", "difficulty": "medium"},
    {"question": "Which base model and adaptation technique are used for technical-support translation?",
     "expected_answer": "NLLB-200 distilled to 600M parameters, with LoRA adapters carrying the domain weights.",
     "source_doc_id": "DOC-006", "difficulty": "medium"},
    {"question": "What are the three eligibility criteria for becoming on-call eligible?",
     "expected_answer": "Ninety days of team tenure, two shadow shifts with a senior engineer, and a runbook quiz score of at least 80%.",
     "source_doc_id": "DOC-007", "difficulty": "medium"},
    {"question": "How long is a primary on-call rotation?",
     "expected_answer": "Seven days, from Monday 09:00 to the following Monday 09:00 Jakarta time.",
     "source_doc_id": "DOC-007", "difficulty": "easy"},
    {"question": "What is the on-call compensation structure?",
     "expected_answer": "0.25x base hourly rate while not actively engaged, and 1.5x base hourly rate while actively engaged on an incident.",
     "source_doc_id": "DOC-007", "difficulty": "easy"},
    {"question": "What four expectations does an engineer have during the first hour of a page?",
     "expected_answer": "Acknowledge within 5 minutes, open the runbook within 10, post a status update within 15, and decide mitigate-vs-investigate by minute 20.",
     "source_doc_id": "DOC-007", "difficulty": "hard"},
    {"question": "Why was Qdrant chosen over pgvector and FAISS for production?",
     "expected_answer": "Filter pushdown for tenant-scoped retrieval, native hybrid search, and horizontal scaling without index rebuilds.",
     "source_doc_id": "DOC-008", "difficulty": "medium"},
    {"question": "Where is FAISS still used after the migration to Qdrant?",
     "expected_answer": "Offline evaluation, prototyping, and unit tests where reproducibility matters more than operational concerns.",
     "source_doc_id": "DOC-008", "difficulty": "medium"},
    {"question": "Which embedding models are standard for English and for multilingual retrieval?",
     "expected_answer": "all-MiniLM-L6-v2 for English (384 dimensions) and multilingual-e5-base for cross-lingual retrieval (768 dimensions).",
     "source_doc_id": "DOC-008", "difficulty": "medium"},
    {"question": "What four sections should every production prompt contain?",
     "expected_answer": "Role, task, context, and output format, in that order.",
     "source_doc_id": "DOC-009", "difficulty": "easy"},
    {"question": "What is the recommended number of few-shot examples in a prompt?",
     "expected_answer": "Two to four. Above five, returns diminish.",
     "source_doc_id": "DOC-009", "difficulty": "easy"},
    {"question": "What temperature should be used for deterministic tasks like classification?",
     "expected_answer": "Zero.",
     "source_doc_id": "DOC-009", "difficulty": "easy"},
    {"question": "List two prompt-engineering anti-patterns called out in the guidelines.",
     "expected_answer": "Asking the model to think step by step in user-facing responses, and stuffing the entire knowledge base into the prompt instead of using retrieval.",
     "source_doc_id": "DOC-009", "difficulty": "medium"},
    {"question": "How are prompt changes managed in production?",
     "expected_answer": "Prompts are treated as code: every change goes through code review, ships with a changelog entry, and is regression-tested on the evaluation set.",
     "source_doc_id": "DOC-009", "difficulty": "medium"},
    {"question": "What four services compose the DocuMind system?",
     "expected_answer": "Ingestion service, ML service, backend, and frontend.",
     "source_doc_id": "DOC-010", "difficulty": "easy"},
    {"question": "What is the answer-relevance SLO for DocuMind?",
     "expected_answer": "At least 0.85 on the evaluation set.",
     "source_doc_id": "DOC-010", "difficulty": "easy"},
    {"question": "What is the citation-faithfulness target for DocuMind?",
     "expected_answer": "At least 0.90.",
     "source_doc_id": "DOC-010", "difficulty": "easy"},
    {"question": "What is explicitly out of scope for DocuMind v1?",
     "expected_answer": "Generating new documents, modifying the knowledge base, taking actions on the user's behalf, and operating without a retrieval grounding step.",
     "source_doc_id": "DOC-010", "difficulty": "medium"},
    # Cross-document, harder questions:
    {"question": "Which embedding model is shared between the Customer Support Chatbot and the standard documented in the Vector Database Selection Rationale?",
     "expected_answer": "sentence-transformers/all-MiniLM-L6-v2, used for English retrieval in both.",
     "source_doc_id": "DOC-005,DOC-008", "difficulty": "hard"},
    {"question": "How do the SLOs of DocuMind compare to those of the Customer Support Chatbot?",
     "expected_answer": "Both target answer relevance at least 0.85 and citation/faithfulness at least 0.90; DocuMind additionally targets 99.5% monthly availability and the Chatbot targets a deflection rate of at least 0.60.",
     "source_doc_id": "DOC-005,DOC-010", "difficulty": "hard"},
    {"question": "If an engineer wants to ship a translation model that uses a Generative AI service, which two policies and which evaluation standard apply?",
     "expected_answer": "The ML Deployment Standard governs promotion gates and rollout, the Generative AI Usage Guidelines govern approved tools and disclosed use, and the Translation Quality Evaluation Standard governs metrics and human evaluation.",
     "source_doc_id": "DOC-002,DOC-004,DOC-006", "difficulty": "hard"},
    {"question": "What protections combine to prevent PII leakage from a production LLM?",
     "expected_answer": "Encryption and access controls from the Privacy Policy, the prohibition on pasting PII into AI tools from the GenAI Guidelines, and de-identification or secure-enclave training plus extraction-attack testing for ML use of PII.",
     "source_doc_id": "DOC-003,DOC-004", "difficulty": "hard"},
    {"question": "What is the minimum tenure plus quiz score combined needed to reach on-call eligibility?",
     "expected_answer": "Ninety days of tenure plus a runbook quiz score of at least 80% (and two shadow shifts).",
     "source_doc_id": "DOC-007", "difficulty": "medium"},
    {"question": "Why is temperature zero recommended for extraction tasks, and what other anti-pattern does the prompt guide flag for production prompts?",
     "expected_answer": "Temperature zero gives deterministic outputs needed for extraction and classification; another anti-pattern is stuffing the knowledge base into the prompt instead of using retrieval.",
     "source_doc_id": "DOC-009", "difficulty": "medium"},
]


# ------------------------------------------------------------------
# Write everything out
# ------------------------------------------------------------------
def write_documents() -> None:
    """Write each Document object to its own markdown file."""
    for doc in DOCUMENTS:
        path = DOCS_DIR / f"{doc.doc_id}.md"
        path.write_text(doc.content, encoding="utf-8")


def write_index() -> None:
    """Write a JSON manifest of the corpus for the ingestion service."""
    index = [
        {
            "doc_id": d.doc_id,
            "title": d.title,
            "category": d.category,
            "tags": d.tags,
            "last_updated": d.last_updated,
            "path": f"data/synthetic/documents/{d.doc_id}.md",
            "char_count": len(d.content),
        }
        for d in DOCUMENTS
    ]
    INDEX_PATH.write_text(json.dumps(index, indent=2), encoding="utf-8")


def write_qa_pairs() -> None:
    """Write the evaluation Q&A set with stable IDs."""
    enriched = [
        {
            "qa_id": f"QA-{i+1:03d}",
            **pair,
        }
        for i, pair in enumerate(QA_PAIRS)
    ]
    QA_PATH.write_text(json.dumps(enriched, indent=2), encoding="utf-8")


def main() -> None:
    write_documents()
    write_index()
    write_qa_pairs()
    print(f"[OK] {len(DOCUMENTS)} documents written to {DOCS_DIR}")
    print(f"[OK] {len(QA_PAIRS)} QA pairs written to {QA_PATH}")
    print(f"[OK] Index written to {INDEX_PATH}")


if __name__ == "__main__":
    main()
