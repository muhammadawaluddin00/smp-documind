'use client';

import { useState } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { ask, AskResult } from '@/lib/api';

const SAMPLE_QUESTIONS = [
  'What is the SEV-1 acknowledgement window?',
  'Which embedding model do we use for retrieval?',
  'What are the rollout steps for a new ML model?',
];

export default function QuickAsk() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AskResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const submit = async (q?: string) => {
    const text = (q ?? question).trim();
    if (!text) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await ask(text);
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Request failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-3">
      <div className="flex gap-2">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
          placeholder="Ask a question…"
          className="flex-1 rounded-lg bg-white/10 border border-white/15 px-3 py-2 text-sm placeholder:text-white/40 focus:outline-none focus:border-signal-400"
          disabled={loading}
        />
        <button
          type="button"
          onClick={() => submit()}
          disabled={loading || !question.trim()}
          className="rounded-lg bg-signal-500 hover:bg-signal-400 disabled:opacity-40 px-3 py-2 text-sm font-semibold text-ink-900 transition flex items-center gap-1.5"
        >
          {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
          {loading ? 'Asking' : 'Ask'}
        </button>
      </div>

      {!result && !error && !loading && (
        <div className="flex flex-wrap gap-1.5">
          {SAMPLE_QUESTIONS.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => {
                setQuestion(q);
                submit(q);
              }}
              className="text-[11px] rounded-full bg-white/5 hover:bg-white/10 border border-white/10 px-2.5 py-1 text-white/70 transition"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="text-xs text-warn-500 bg-warn-500/10 rounded-lg p-2">
          {error}. Make sure the backend and ML service are running.
        </div>
      )}

      {result && (
        <div className="rounded-lg bg-white/5 border border-white/10 p-3">
          <div className="text-xs text-white/60 mb-2">
            {result.used_generator} · {result.wall_latency_ms} ms
          </div>
          <div className="text-sm text-white/95 leading-relaxed">
            {result.answer}
          </div>
          {result.citations.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {result.citations.map((c) => (
                <span
                  key={c.doc_id}
                  className="text-[10px] font-mono rounded-full bg-signal-500/20 border border-signal-500/30 text-signal-400 px-2 py-0.5"
                >
                  {c.doc_id}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
