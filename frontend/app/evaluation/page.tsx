'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid,
} from 'recharts';
import { CheckCircle2, XCircle, Clock, Filter } from 'lucide-react';
import { fetchBenchmarkResults } from '../../lib/api';

type PerQuestion = {
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
};

type Difficulty = 'all' | 'easy' | 'medium' | 'hard';
type FilterMode = 'all' | 'failed' | 'unfaithful';

export default function EvaluationPage() {
  const [rows, setRows] = useState<PerQuestion[]>([]);
  const [diff, setDiff] = useState<Difficulty>('all');
  const [mode, setMode] = useState<FilterMode>('all');

  useEffect(() => {
    fetchBenchmarkResults().then((d) => {
      if (d?.per_question) setRows(d.per_question);
    });
  }, []);

  const filtered = useMemo(() => {
    return rows.filter((r) => {
      if (diff !== 'all' && r.difficulty !== diff) return false;
      if (mode === 'failed' && r.retrieval_hit) return false;
      if (mode === 'unfaithful' && r.citation_faithful) return false;
      return true;
    });
  }, [rows, diff, mode]);

  const histogram = useMemo(() => {
    const buckets = [
      { label: '<1s', max: 1000, count: 0 },
      { label: '1-1.5s', max: 1500, count: 0 },
      { label: '1.5-2s', max: 2000, count: 0 },
      { label: '2-2.5s', max: 2500, count: 0 },
      { label: '2.5s+', max: Infinity, count: 0 },
    ];
    rows.forEach((r) => {
      for (const b of buckets) {
        if (r.latency_ms < b.max) {
          b.count += 1;
          break;
        }
      }
    });
    return buckets;
  }, [rows]);

  const aggregate = useMemo(() => {
    if (rows.length === 0) return null;
    const n = rows.length;
    const meanRel = rows.reduce((s, r) => s + r.answer_relevance, 0) / n;
    const hits = rows.filter((r) => r.retrieval_hit).length;
    const faithful = rows.filter((r) => r.citation_faithful).length;
    return {
      n,
      meanRel,
      hitRate: hits / n,
      faithRate: faithful / n,
    };
  }, [rows]);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Evaluation Suite</h1>
        <p className="text-sm text-slate-400 mt-1">
          Per-question results from the latest benchmark run · 50 Q&A pairs across 10 documents
        </p>
      </header>

      {aggregate && (
        <div className="grid gap-3 grid-cols-2 lg:grid-cols-4">
          <SummaryStat label="Total questions" value={aggregate.n.toString()} />
          <SummaryStat
            label="Mean answer relevance"
            value={(aggregate.meanRel * 100).toFixed(1) + '%'}
            tone={aggregate.meanRel >= 0.85 ? 'ok' : 'warn'}
          />
          <SummaryStat
            label="Retrieval hit rate"
            value={(aggregate.hitRate * 100).toFixed(1) + '%'}
            tone={aggregate.hitRate >= 0.9 ? 'ok' : 'warn'}
          />
          <SummaryStat
            label="Citation faithfulness"
            value={(aggregate.faithRate * 100).toFixed(1) + '%'}
            tone={aggregate.faithRate >= 0.9 ? 'ok' : 'warn'}
          />
        </div>
      )}

      <section className="rounded-xl border border-ink-600 bg-ink-700/50 p-5">
        <h2 className="text-sm font-medium text-white mb-4 flex items-center gap-2">
          <Clock className="h-4 w-4 text-signal-400" /> Latency distribution
        </h2>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={histogram}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="label" stroke="#94a3b8" fontSize={11} />
              <YAxis stroke="#94a3b8" fontSize={11} />
              <Tooltip
                contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8, fontSize: 12 }}
              />
              <Bar dataKey="count" fill="#22d3ee" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-[11px] text-slate-500 mt-2">
          SLO target: p95 &lt; 2.5s (DOC-010). Bars show count of questions in each latency bucket.
        </p>
      </section>

      <section className="rounded-xl border border-ink-600 bg-ink-700/50">
        <header className="p-4 border-b border-ink-600 flex flex-wrap items-center gap-3">
          <h2 className="text-sm font-medium text-white flex items-center gap-2">
            <Filter className="h-4 w-4 text-signal-400" /> Per-question results
          </h2>
          <div className="flex gap-1 ml-auto">
            {(['all', 'easy', 'medium', 'hard'] as Difficulty[]).map((d) => (
              <button
                key={d}
                onClick={() => setDiff(d)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium ${
                  diff === d ? 'bg-signal-500 text-ink-900' : 'bg-ink-600 text-slate-300 hover:bg-ink-500'
                }`}
              >
                {d}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            {(['all', 'failed', 'unfaithful'] as FilterMode[]).map((m) => (
              <button
                key={m}
                onClick={() => setMode(m)}
                className={`px-2.5 py-1 rounded text-[11px] font-medium ${
                  mode === m ? 'bg-signal-500 text-ink-900' : 'bg-ink-600 text-slate-300 hover:bg-ink-500'
                }`}
              >
                {m === 'all' ? 'All' : m === 'failed' ? 'Retrieval miss' : 'Unfaithful'}
              </button>
            ))}
          </div>
        </header>

        <div className="overflow-auto max-h-[560px]">
          <table className="w-full text-xs">
            <thead className="sticky top-0 bg-ink-800 text-slate-400 text-left">
              <tr>
                <th className="px-3 py-2 font-medium">ID</th>
                <th className="px-3 py-2 font-medium">Question</th>
                <th className="px-3 py-2 font-medium">Diff</th>
                <th className="px-3 py-2 font-medium text-right">Rel.</th>
                <th className="px-3 py-2 font-medium text-center">Hit</th>
                <th className="px-3 py-2 font-medium text-center">Faith</th>
                <th className="px-3 py-2 font-medium text-right">Latency</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((r) => (
                <tr key={r.qa_id} className="border-t border-ink-600 hover:bg-ink-600/40">
                  <td className="px-3 py-2 font-mono text-slate-500">{r.qa_id}</td>
                  <td className="px-3 py-2 text-slate-200 max-w-md truncate" title={r.question}>{r.question}</td>
                  <td className="px-3 py-2">
                    <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] ${
                      r.difficulty === 'hard' ? 'bg-warn-500/20 text-warn-400' :
                      r.difficulty === 'medium' ? 'bg-signal-500/20 text-signal-300' :
                      'bg-ok-500/20 text-ok-400'
                    }`}>
                      {r.difficulty}
                    </span>
                  </td>
                  <td className="px-3 py-2 text-right font-mono">{(r.answer_relevance * 100).toFixed(0)}%</td>
                  <td className="px-3 py-2 text-center">
                    {r.retrieval_hit ? <CheckCircle2 className="h-3.5 w-3.5 text-ok-400 inline" /> : <XCircle className="h-3.5 w-3.5 text-bad-400 inline" />}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {r.citation_faithful ? <CheckCircle2 className="h-3.5 w-3.5 text-ok-400 inline" /> : <XCircle className="h-3.5 w-3.5 text-bad-400 inline" />}
                  </td>
                  <td className="px-3 py-2 text-right font-mono text-slate-400">{r.latency_ms.toFixed(0)}ms</td>
                </tr>
              ))}
            </tbody>
          </table>
          {filtered.length === 0 && rows.length > 0 && (
            <p className="text-center text-sm text-slate-500 py-8">No questions match the current filters.</p>
          )}
          {rows.length === 0 && (
            <p className="text-center text-sm text-slate-500 py-8">Loading benchmark results…</p>
          )}
        </div>
      </section>
    </div>
  );
}

function SummaryStat({ label, value, tone }: { label: string; value: string; tone?: 'ok' | 'warn' }) {
  const color =
    tone === 'ok' ? 'text-ok-400' : tone === 'warn' ? 'text-warn-400' : 'text-white';
  return (
    <div className="rounded-xl border border-ink-600 bg-ink-700/50 p-4">
      <p className="text-[11px] uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`text-2xl font-semibold mt-1 ${color}`}>{value}</p>
    </div>
  );
}
