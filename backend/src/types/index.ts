/**
 * Shared TypeScript types for the SMP DocuMind backend.
 *
 * These mirror the Pydantic models exposed by ml-service/main.py.
 * Keeping them in sync is a code-review checklist item; for a larger
 * project we would generate these from the FastAPI OpenAPI schema.
 */

export interface CitationRef {
  doc_id: string;
  title: string;
}

export interface RetrievedChunk {
  doc_id: string;
  title: string;
  text: string;
  score: number;
}

export interface AskResponse {
  answer: string;
  citations: CitationRef[];
  retrieved: RetrievedChunk[];
  used_generator: string;
  latency_ms: number;
  aborted_low_relevance: boolean;
}

export interface DocumentSummary {
  doc_id: string;
  title: string;
  category: string;
  tags: string[];
  last_updated: string;
  char_count: number;
}

export interface MetricsSummary {
  n: number;
  mean_answer_relevance: number;
  retrieval_hit_rate: number;
  citation_faithfulness: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  by_difficulty: Record<
    string,
    {
      n: number;
      mean_answer_relevance: number;
      retrieval_hit_rate: number;
      citation_faithfulness: number;
      p50_latency_ms?: number;
    }
  >;
}

export interface MetricsResponse {
  summary: MetricsSummary;
  per_question: Array<{
    qa_id: string;
    question: string;
    expected_answer: string;
    predicted_answer: string;
    expected_doc_ids: string[];
    predicted_citations: string[];
    answer_relevance: number;
    retrieval_hit: boolean;
    citation_faithful: boolean;
    latency_ms: number;
    difficulty: string;
  }>;
  config: Record<string, unknown>;
}

/**
 * Audit log entry written for every request. Useful for debugging,
 * compliance (DOC-003 requires logging), and offline analysis.
 */
export interface AuditLogEntry {
  timestamp: string;
  request_id: string;
  user_id: string;
  question: string;
  answer_preview: string;
  citations: string[];
  latency_ms: number;
  used_generator: string;
}
