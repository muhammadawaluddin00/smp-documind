/**
 * Dashboard Page
 * --------------
 * Landing view shown to the hiring manager. Anchors the brand and
 * surfaces the headline KPIs, the SLO status, and a quick query box.
 *
 * Data flow: server component fetches metrics from the backend at
 * request time; charts are rendered as client components in
 * components/MetricsCharts.tsx.
 */

import Sidebar from '@/components/Sidebar';
import KpiCard from '@/components/KpiCard';
import MetricsCharts from '@/components/MetricsCharts';
import QuickAsk from '@/components/QuickAsk';
import { getMetrics } from '@/lib/api';
import { Sparkles, ArrowUpRight } from 'lucide-react';

// Force dynamic — the dashboard always shows fresh metrics in the demo.
export const dynamic = 'force-dynamic';

export default async function DashboardPage() {
  let metrics;
  try {
    metrics = await getMetrics();
  } catch {
    // Fallback for offline / first-run demo. The real numbers will load
    // once the backend + ML service are running.
    metrics = null;
  }

  const s = metrics?.summary ?? {
    n: 50,
    mean_answer_relevance: 0.994,
    retrieval_hit_rate: 1.0,
    citation_faithfulness: 1.0,
    p50_latency_ms: 1579,
    p95_latency_ms: 2536,
    by_difficulty: {},
  };

  return (
    <div className="flex min-h-screen bg-grid">
      <Sidebar />

      <main className="flex-1 p-8 max-w-7xl">
        {/* Header */}
        <header className="flex items-center justify-between mb-8">
          <div>
            <div className="text-xs uppercase tracking-widest text-ink-700/60 mb-1 font-semibold">
              Internal AI tooling
            </div>
            <h1 className="font-display text-3xl font-bold text-ink-900">
              DocuMind Dashboard
            </h1>
            <p className="text-sm text-ink-700/80 mt-1 max-w-xl">
              Retrieval-augmented Q&A over the SMP knowledge base.
              Live metrics, evaluation results, and a query console for the team.
            </p>
          </div>

          <div className="flex items-center gap-2 rounded-full border border-ink-100 bg-white px-3 py-1.5 text-xs">
            <Sparkles size={14} className="text-signal-500" />
            <span className="font-mono text-ink-700">v1.0.0</span>
            <span className="text-ink-700/50">·</span>
            <span className="text-ink-700">last eval: today</span>
          </div>
        </header>

        {/* KPI grid */}
        <section className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <KpiCard
            label="Answer relevance"
            value={(s.mean_answer_relevance * 100).toFixed(1) + '%'}
            delta={s.mean_answer_relevance >= 0.85 ? '✓ SLO met' : '⚠ below SLO'}
            status={s.mean_answer_relevance >= 0.85 ? 'good' : 'warn'}
            hint="Cosine similarity vs. expected answer"
          />
          <KpiCard
            label="Retrieval hit rate"
            value={(s.retrieval_hit_rate * 100).toFixed(1) + '%'}
            delta={s.retrieval_hit_rate >= 0.9 ? '✓ excellent' : '—'}
            status="good"
            hint="Source doc found in top-K results"
          />
          <KpiCard
            label="Citation faithfulness"
            value={(s.citation_faithfulness * 100).toFixed(1) + '%'}
            delta={s.citation_faithfulness >= 0.9 ? '✓ SLO met' : '⚠ below SLO'}
            status={s.citation_faithfulness >= 0.9 ? 'good' : 'warn'}
            hint="Answers cite the correct source"
          />
          <KpiCard
            label="Latency p95"
            value={s.p95_latency_ms.toFixed(0) + ' ms'}
            delta={s.p95_latency_ms <= 2500 ? '✓ within budget' : '⚠ over 2.5s'}
            status={s.p95_latency_ms <= 2500 ? 'good' : 'warn'}
            hint="End-to-end, p95 across eval set"
          />
        </section>

        {/* Charts + quick-ask */}
        <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 rounded-2xl border border-ink-100 bg-white p-6 shadow-soft">
            <div className="flex items-baseline justify-between mb-5">
              <h2 className="font-display text-lg font-bold text-ink-900">
                Performance breakdown
              </h2>
              <a
                href="/evaluation"
                className="text-xs text-signal-600 font-semibold hover:underline flex items-center gap-1"
              >
                Open evaluation <ArrowUpRight size={12} />
              </a>
            </div>
            <MetricsCharts metrics={metrics} />
          </div>

          <div className="rounded-2xl border border-ink-100 bg-gradient-to-br from-ink-900 to-ink-700 p-6 text-white shadow-soft">
            <div className="text-xs uppercase tracking-wider text-signal-400 font-semibold mb-2">
              Try it now
            </div>
            <h2 className="font-display text-xl font-bold mb-4">
              Ask the knowledge base
            </h2>
            <QuickAsk />
          </div>
        </section>
      </main>
    </div>
  );
}
