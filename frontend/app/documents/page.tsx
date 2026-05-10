'use client';

import { useEffect, useState } from 'react';
import { Search, FileText, Tag, Calendar } from 'lucide-react';

type DocMeta = {
  doc_id: string;
  title: string;
  category: string;
  tags: string[];
  last_updated: string;
  char_count: number;
};

const CATEGORY_COLORS: Record<string, string> = {
  Operations: 'bg-signal-500/10 text-signal-300 border-signal-500/20',
  Engineering: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  Compliance: 'bg-warn-500/10 text-warn-400 border-warn-500/20',
  Reference: 'bg-purple-500/10 text-purple-300 border-purple-500/20',
  Architecture: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20',
  Product: 'bg-pink-500/10 text-pink-300 border-pink-500/20',
};

export default function DocumentsPage() {
  const [docs, setDocs] = useState<DocMeta[]>([]);
  const [filter, setFilter] = useState('');
  const [activeCategory, setActiveCategory] = useState<string | null>(null);

  useEffect(() => {
    // In live mode this would hit the backend /documents endpoint.
    // For static demo, we hardcode the known index.
    const STATIC_INDEX: DocMeta[] = [
      { doc_id: 'DOC-001', title: 'AIOps Incident Response Playbook', category: 'Operations', tags: ['aiops','incident','playbook','on-call'], last_updated: '2025-09-14', char_count: 1287 },
      { doc_id: 'DOC-002', title: 'Machine Learning Model Deployment Standard', category: 'Engineering', tags: ['mlops','deployment','engineering','model-card'], last_updated: '2025-10-02', char_count: 1207 },
      { doc_id: 'DOC-003', title: 'Data Privacy and PII Handling Policy', category: 'Compliance', tags: ['compliance','privacy','pii','security'], last_updated: '2025-08-20', char_count: 1302 },
      { doc_id: 'DOC-004', title: 'Generative AI Usage Guidelines for Employees', category: 'Compliance', tags: ['genai','policy','compliance','guidelines'], last_updated: '2025-11-05', char_count: 1174 },
      { doc_id: 'DOC-005', title: 'Customer Support Chatbot Architecture', category: 'Architecture', tags: ['chatbot','rag','architecture','design'], last_updated: '2025-10-18', char_count: 1346 },
      { doc_id: 'DOC-006', title: 'Translation Quality Evaluation Methodology', category: 'Engineering', tags: ['translation','evaluation','metrics','bleu','bertscore'], last_updated: '2025-09-28', char_count: 1289 },
      { doc_id: 'DOC-007', title: 'On-Call Engineer Onboarding Guide', category: 'Operations', tags: ['onboarding','on-call','operations','training'], last_updated: '2025-10-30', char_count: 1198 },
      { doc_id: 'DOC-008', title: 'Vector Database Selection Rationale', category: 'Architecture', tags: ['vector-db','rag','architecture','infrastructure'], last_updated: '2025-11-01', char_count: 1422 },
      { doc_id: 'DOC-009', title: 'Prompt Engineering Style Guide', category: 'Reference', tags: ['prompt-engineering','llm','reference','best-practices'], last_updated: '2025-10-12', char_count: 1356 },
      { doc_id: 'DOC-010', title: 'SMP DocuMind Product Overview', category: 'Product', tags: ['product','overview','documind','rag'], last_updated: '2025-11-08', char_count: 1289 },
    ];
    setDocs(STATIC_INDEX);
  }, []);

  const categories = Array.from(new Set(docs.map((d) => d.category))).sort();

  const filtered = docs.filter((d) => {
    const text = `${d.title} ${d.doc_id} ${d.tags.join(' ')}`.toLowerCase();
    const matchesText = filter ? text.includes(filter.toLowerCase()) : true;
    const matchesCat = activeCategory ? d.category === activeCategory : true;
    return matchesText && matchesCat;
  });

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white">Knowledge Base</h1>
        <p className="text-sm text-slate-400 mt-1">
          {docs.length} documents indexed · {docs.reduce((s, d) => s + d.char_count, 0).toLocaleString()} characters
        </p>
      </header>

      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Search title, ID, or tag…"
            className="w-full bg-ink-700 border border-ink-600 rounded-lg pl-10 pr-3 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-signal-500/50"
          />
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setActiveCategory(null)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
              !activeCategory ? 'bg-signal-500 text-ink-900' : 'bg-ink-700 text-slate-300 hover:bg-ink-600'
            }`}
          >
            All
          </button>
          {categories.map((c) => (
            <button
              key={c}
              onClick={() => setActiveCategory(c === activeCategory ? null : c)}
              className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                activeCategory === c ? 'bg-signal-500 text-ink-900' : 'bg-ink-700 text-slate-300 hover:bg-ink-600'
              }`}
            >
              {c}
            </button>
          ))}
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {filtered.map((doc) => (
          <article
            key={doc.doc_id}
            className="group rounded-xl border border-ink-600 bg-ink-700/50 p-4 hover:border-signal-500/40 hover:bg-ink-700 transition"
          >
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-start gap-2 min-w-0">
                <FileText className="h-4 w-4 text-signal-400 mt-0.5 shrink-0" />
                <div className="min-w-0">
                  <p className="font-mono text-[11px] text-slate-500">{doc.doc_id}</p>
                  <h3 className="text-sm font-medium text-white leading-snug truncate">{doc.title}</h3>
                </div>
              </div>
              <span
                className={`shrink-0 inline-flex items-center rounded border px-1.5 py-0.5 text-[10px] font-medium ${
                  CATEGORY_COLORS[doc.category] ?? 'bg-slate-500/10 text-slate-300 border-slate-500/20'
                }`}
              >
                {doc.category}
              </span>
            </div>
            <div className="flex flex-wrap gap-1.5 mb-3">
              {doc.tags.map((t) => (
                <span key={t} className="inline-flex items-center gap-1 rounded bg-ink-600 px-1.5 py-0.5 text-[10px] text-slate-400">
                  <Tag className="h-2.5 w-2.5" />
                  {t}
                </span>
              ))}
            </div>
            <div className="flex items-center justify-between text-[11px] text-slate-500">
              <span className="inline-flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {doc.last_updated}
              </span>
              <span>{doc.char_count.toLocaleString()} chars</span>
            </div>
          </article>
        ))}
      </div>

      {filtered.length === 0 && (
        <p className="text-center text-sm text-slate-500 py-12">No documents match your filter.</p>
      )}
    </div>
  );
}
