/**
 * ML Service Client
 * -----------------
 * Thin HTTP client around the FastAPI ML service. Centralised so that
 * timeouts, retries, and base-URL config live in one place.
 */

import axios, { AxiosInstance } from 'axios';
import {
  AskResponse,
  DocumentSummary,
  MetricsResponse,
} from '../types';

const ML_SERVICE_URL =
  process.env.ML_SERVICE_URL ?? 'http://localhost:8000';
const ML_SERVICE_TIMEOUT_MS = Number(
  process.env.ML_SERVICE_TIMEOUT_MS ?? 15_000,
);

class MlServiceClient {
  private readonly http: AxiosInstance;

  constructor(baseURL: string = ML_SERVICE_URL) {
    this.http = axios.create({
      baseURL,
      timeout: ML_SERVICE_TIMEOUT_MS,
      headers: { 'Content-Type': 'application/json' },
    });
  }

  async ask(question: string, topK = 4): Promise<AskResponse> {
    const { data } = await this.http.post<AskResponse>('/ask', {
      question,
      top_k: topK,
    });
    return data;
  }

  async listDocuments(): Promise<DocumentSummary[]> {
    const { data } = await this.http.get<DocumentSummary[]>('/documents');
    return data;
  }

  async getMetrics(): Promise<MetricsResponse> {
    const { data } = await this.http.get<MetricsResponse>('/metrics');
    return data;
  }

  async health(): Promise<{ status: string; chunks_indexed: number; generator_mode: string }> {
    const { data } = await this.http.get('/health');
    return data;
  }
}

export const mlService = new MlServiceClient();
