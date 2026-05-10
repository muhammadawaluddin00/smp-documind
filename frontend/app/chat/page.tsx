'use client';

import { useState, useRef, useEffect } from 'react';
import Sidebar from '@/components/Sidebar';
import { ask, AskResult } from '@/lib/api';
import { Send, Loader2, Bot, User, Copy, Check } from 'lucide-react';

interface ChatTurn {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  result?: AskResult;
  timestamp: number;
}

const SAMPLE_PROMPTS = [
  'What is the SEV-1 acknowledgement window?',
  'How does our chatbot decide when to escalate to a human?',
  'Why did we choose Qdrant over pgvector and FAISS?',
  'What four expectations does an on-call engineer have in the first hour?',
];

export default function ChatPage() {
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [turns]);

  const send = async (prompt?: string) => {
    const text = (prompt ?? input).trim();
    if (!text || loading) return;
    const userTurn: ChatTurn = {
      id: `u-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };
    setTurns((t) => [...t, userTurn]);
    setInput('');
    setLoading(true);
    try {
      const result = await ask(text);
      setTurns((t) => [
        ...t,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: result.answer,
          result,
          timestamp: Date.now(),
        },
      ]);
    } catch (e) {
      setTurns((t) => [
        ...t,
        {
          id: `a-${Date.now()}`,
          role: 'assistant',
          content: `Error: ${e instanceof Error ? e.message : 'request failed'}. Make sure the backend and ML service are running.`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const copy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  return (
    <div className="flex min-h-screen bg-grid">
      <Sidebar />
      <main className="flex-1 flex flex-col max-w-5xl mx-auto px-8 py-6">
        <header className="mb-6">
          <h1 className="font-display text-2xl font-bold text-ink-900">Ask DocuMind</h1>
          <p className="text-sm text-ink-700/80 mt-1">
            Grounded answers from the SMP knowledge base. Every claim is cited.
          </p>
        </header>

        <div className="flex-1 overflow-y-auto rounded-2xl border border-ink-100 bg-white p-6 shadow-soft mb-4 min-h-[60vh]">
          {turns.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center gap-4 py-16">
              <div className="size-14 rounded-2xl bg-gradient-to-br from-ink-900 to-signal-600 grid place-items-center text-white">
                <Bot size={24} />
              </div>
              <div>
                <div className="font-display text-lg font-bold text-ink-900">
                  Ask anything about SMP&rsquo;s docs.
                </div>
                <div className="text-sm text-ink-700/70 mt-1">
                  Try one of these to get started:
                </div>
              </div>
              <div className="flex flex-col gap-2 max-w-lg w-full">
                {SAMPLE_PROMPTS.map((p) => (
                  <button
                    key={p}
                    type="button"
                    onClick={() => send(p)}
                    className="text-left text-sm rounded-xl border border-ink-100 bg-ink-50 hover:bg-ink-100 hover:border-signal-500 px-4 py-3 transition text-ink-700"
                  >
                    {p}
                  </button>
                ))}
              </div>
            </div>
          )}

          {turns.map((t) => (
            <div key={t.id} className="mb-6 last:mb-0">
              {t.role === 'user' ? (
                <div className="flex gap-3 justify-end">
                  <div className="rounded-2xl rounded-tr-sm bg-ink-900 text-white px-4 py-2.5 max-w-2xl text-sm">
                    {t.content}
                  </div>
                  <div className="size-8 rounded-full bg-ink-100 grid place-items-center text-ink-700 shrink-0">
                    <User size={14} />
                  </div>
                </div>
              ) : (
                <div className="flex gap-3">
                  <div className="size-8 rounded-full bg-gradient-to-br from-ink-900 to-signal-600 grid place-items-center text-white shrink-0">
                    <Bot size={14} />
                  </div>
                  <div className="flex-1 max-w-2xl">
                    <div className="rounded-2xl rounded-tl-sm bg-ink-50 border border-ink-100 px-4 py-3 text-sm text-ink-900 leading-relaxed">
                      {t.content}
                    </div>
                    {t.result && (
                      <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-ink-700/70">
                        {t.result.citations.length > 0 && (
                          <div className="flex flex-wrap gap-1">
                            {t.result.citations.map((c) => (
                              <span key={c.doc_id} className="cite-chip">
                                {c.doc_id} · {c.title}
                              </span>
                            ))}
                          </div>
                        )}
                        <span className="text-ink-700/50">·</span>
                        <span className="font-mono">
                          {t.result.used_generator} · {t.result.wall_latency_ms} ms
                        </span>
                        <button
                          type="button"
                          onClick={() => copy(t.id, t.content)}
                          className="ml-auto flex items-center gap-1 text-ink-700/60 hover:text-ink-900 transition"
                        >
                          {copiedId === t.id ? (
                            <>
                              <Check size={11} /> Copied
                            </>
                          ) : (
                            <>
                              <Copy size={11} /> Copy
                            </>
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex gap-3">
              <div className="size-8 rounded-full bg-gradient-to-br from-ink-900 to-signal-600 grid place-items-center text-white shrink-0">
                <Bot size={14} />
              </div>
              <div className="rounded-2xl rounded-tl-sm bg-ink-50 border border-ink-100 px-4 py-3 text-sm text-ink-700 flex items-center gap-2">
                <Loader2 size={14} className="animate-spin" />
                Searching knowledge base…
              </div>
            </div>
          )}

          <div ref={endRef} />
        </div>

        <div className="flex gap-2 sticky bottom-0">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && send()}
            placeholder="Type your question…"
            disabled={loading}
            className="flex-1 rounded-xl border border-ink-100 bg-white px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-signal-500/30 focus:border-signal-500 shadow-soft disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => send()}
            disabled={loading || !input.trim()}
            className="rounded-xl bg-ink-900 hover:bg-ink-700 disabled:opacity-40 px-5 py-3 text-sm font-semibold text-white transition flex items-center gap-2 shadow-soft"
          >
            {loading ? <Loader2 size={14} className="animate-spin" /> : <Send size={14} />}
            Send
          </button>
        </div>
      </main>
    </div>
  );
}
