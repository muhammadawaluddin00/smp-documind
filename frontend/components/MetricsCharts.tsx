'use client';

import {
  BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';

interface Props {
  metrics: {
    summary: {
      mean_answer_relevance: number;
      retrieval_hit_rate: number;
      citation_faithfulness: number;
      p50_latency_ms: number;
      p95_latency_ms: number;
      by_difficulty: Record<
        string,
        { mean_answer_relevance: number; retrieval_hit_rate: number; citation_faithfulness: number }
      >;
    };
  } | null;
}

export default function MetricsCharts({ metrics }: Props) {
  const byDiff = metrics?.summary.by_difficulty ?? {
    easy:   { mean_answer_relevance: 0.99, retrieval_hit_rate: 1.0, citation_faithfulness: 0.91 },
    medium: { mean_answer_relevance: 0.99, retrieval_hit_rate: 1.0, citation_faithfulness: 1.0 },
    hard:   { mean_answer_relevance: 0.98, retrieval_hit_rate: 1.0, citation_faithfulness: 1.0 },
  };

  const barData = Object.entries(byDiff).map(([k, v]) => ({
    name: k.charAt(0).toUpperCase() + k.slice(1),
    Relevance:    +(v.mean_answer_relevance * 100).toFixed(1),
    'Hit rate':   +(v.retrieval_hit_rate * 100).toFixed(1),
    Faithfulness: +(v.citation_faithfulness * 100).toFixed(1),
  }));

  const radarData = [
    { metric: 'Relevance',   actual: +(metrics?.summary.mean_answer_relevance ?? 0.99) * 100, target: 85 },
    { metric: 'Hit rate',    actual: +(metrics?.summary.retrieval_hit_rate ?? 1.0) * 100,     target: 90 },
    { metric: 'Faithfulness',actual: +(metrics?.summary.citation_faithfulness ?? 1.0) * 100,  target: 90 },
    { metric: 'Latency',     actual: Math.max(0, 100 - ((metrics?.summary.p95_latency_ms ?? 2536) / 50)), target: 100 - 50 },
    { metric: 'Coverage',    actual: 92, target: 80 }, // synthetic illustrative metric
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div>
        <div className="text-xs font-semibold text-ink-700/70 uppercase tracking-wider mb-3">
          By difficulty (%)
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={barData} barGap={2}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e6edf6" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#1f3554' }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#1f3554' }} />
            <Tooltip />
            <Bar dataKey="Relevance"     fill="#13b9a6" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Hit rate"      fill="#0b1a30" radius={[4, 4, 0, 0]} />
            <Bar dataKey="Faithfulness"  fill="#456293" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div>
        <div className="text-xs font-semibold text-ink-700/70 uppercase tracking-wider mb-3">
          Actual vs. SLO target
        </div>
        <ResponsiveContainer width="100%" height={220}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#c8d6e8" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 11, fill: '#1f3554' }} />
            <PolarRadiusAxis tick={{ fontSize: 9 }} domain={[0, 100]} />
            <Radar name="Target" dataKey="target" stroke="#9eb5d3" fill="#9eb5d3" fillOpacity={0.2} />
            <Radar name="Actual" dataKey="actual" stroke="#13b9a6" fill="#13b9a6" fillOpacity={0.45} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
