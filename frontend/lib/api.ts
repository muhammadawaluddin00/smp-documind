/**
 * Frontend API client
 * -------------------
 * Single place that talks to the backend. The Next.js dev server
 * proxies /api/* to the Node backend (see next.config.js), so callers
 * just hit relative URLs.
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

export interface AskResult {
  answer: string;
  citations: CitationRef[];
  retrieved: RetrievedChunk[];
  used_generator: string;
  latency_ms: number;
  wall_latency_ms: number;
  aborted_low_relevance: boolean;
  request_id: string;
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

export interface BenchmarkQuestion {
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
  difficulty: 'easy' | 'medium' | 'hard';
}

const BASE = process.env.NEXT_PUBLIC_API_BASE ?? '';

async function jsonOrThrow<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body.slice(0, 200)}`);
  }
  return res.json() as Promise<T>;
}

export async function ask(question: string, topK = 4): Promise<AskResult> {
  const res = await fetch(`${BASE}/api/ask`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, topK }),
  });
  return jsonOrThrow<AskResult>(res);
}

export async function listDocuments(): Promise<DocumentSummary[]> {
  return jsonOrThrow(await fetch(`${BASE}/api/documents`));
}

export async function getMetrics(): Promise<{
  summary: MetricsSummary;
  per_question: BenchmarkQuestion[];
}> {
  return jsonOrThrow(await fetch(`${BASE}/api/metrics`));
}

export const fetchBenchmarkResults = getMetrics;
