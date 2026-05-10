'use client';

import { useState } from 'react';
import { Settings as SettingsIcon, Database, Cpu, Shield, Sliders } from 'lucide-react';

export default function SettingsPage() {
  const [generatorMode, setGeneratorMode] = useState<'extractive' | 'openai'>('extractive');
  const [topK, setTopK] = useState(4);
  const [threshold, setThreshold] = useState(0.30);
  const [chunkSize, setChunkSize] = useState(420);
  const [chunkOverlap, setChunkOverlap] = useState(60);

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-2xl font-semibold text-white flex items-center gap-2">
          <SettingsIcon className="h-6 w-6 text-signal-400" /> Configuration
        </h1>
        <p className="text-sm text-slate-400 mt-1">
          Pipeline parameters · service endpoints · compliance settings
        </p>
      </header>

      <Section icon={<Cpu className="h-4 w-4 text-signal-400" />} title="Generator">
        <Field label="Mode" hint="Extractive returns ground-truth spans verbatim. OpenAI synthesises a natural answer.">
          <div className="flex gap-2">
            {(['extractive', 'openai'] as const).map((m) => (
              <button
                key={m}
                onClick={() => setGeneratorMode(m)}
                className={`px-3 py-1.5 rounded text-xs font-medium ${
                  generatorMode === m ? 'bg-signal-500 text-ink-900' : 'bg-ink-600 text-slate-300 hover:bg-ink-500'
                }`}
              >
                {m}
              </button>
            ))}
          </div>
        </Field>
        <Field label="OpenAI model" hint="Used when mode = openai. Switch via OPENAI_MODEL env var.">
          <code className="text-xs text-signal-300 bg-ink-800 px-2 py-1 rounded">gpt-4o-mini</code>
        </Field>
      </Section>

      <Section icon={<Database className="h-4 w-4 text-signal-400" />} title="Retrieval">
        <Field label="Top K" hint="Number of chunks pulled into the prompt context. Higher recall, more tokens.">
          <SliderInput value={topK} setValue={setTopK} min={1} max={10} step={1} unit="" />
        </Field>
        <Field label="Relevance threshold" hint="Below this fused score we abstain rather than answer (DOC-005 abstention rule).">
          <SliderInput value={threshold} setValue={setThreshold} min={0} max={1} step={0.05} unit="" />
        </Field>
        <Field label="Hybrid weights" hint="Score fusion: dense × α + sparse × (1-α).">
          <code className="text-xs text-signal-300 bg-ink-800 px-2 py-1 rounded">dense=0.6 · sparse=0.4 (BM25)</code>
        </Field>
      </Section>

      <Section icon={<Sliders className="h-4 w-4 text-signal-400" />} title="Chunking">
        <Field label="Chunk size (tokens)" hint="Approx. tokens per chunk. ~420 balances precision and context.">
          <SliderInput value={chunkSize} setValue={setChunkSize} min={128} max={1024} step={32} unit=" tok" />
        </Field>
        <Field label="Overlap (tokens)" hint="Trailing overlap to preserve cross-chunk semantics.">
          <SliderInput value={chunkOverlap} setValue={setChunkOverlap} min={0} max={256} step={16} unit=" tok" />
        </Field>
      </Section>

      <Section icon={<Shield className="h-4 w-4 text-signal-400" />} title="Compliance">
        <Field label="Audit log" hint="DOC-003 + DOC-004 require every query, citation set and user role to be persisted.">
          <span className="inline-flex items-center gap-2 text-xs text-ok-400">
            <span className="h-1.5 w-1.5 rounded-full bg-ok-500 animate-pulse" />
            enabled · backend/audit-log.jsonl
          </span>
        </Field>
        <Field label="PII redaction" hint="Pre-ingestion scrub on common PII patterns (DOC-003).">
          <span className="text-xs text-slate-300">enabled (regex + entity model)</span>
        </Field>
        <Field label="Rate limit" hint="Per-IP throttle protects the ML service (backend gateway).">
          <code className="text-xs text-signal-300 bg-ink-800 px-2 py-1 rounded">60 req / min</code>
        </Field>
      </Section>

      <Section icon={<SettingsIcon className="h-4 w-4 text-signal-400" />} title="Service endpoints">
        <Field label="ML service"><Endpoint url="http://localhost:8000" /></Field>
        <Field label="Backend gateway"><Endpoint url="http://localhost:4000" /></Field>
        <Field label="Frontend"><Endpoint url="http://localhost:3000" /></Field>
      </Section>

      <p className="text-[11px] text-slate-500 italic">
        Settings on this page are illustrative for the demo; production deployment exposes them via env vars
        and a typed config schema (see ml-service/main.py).
      </p>
    </div>
  );
}

function Section({ icon, title, children }: { icon: React.ReactNode; title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-xl border border-ink-600 bg-ink-700/50 p-5">
      <h2 className="text-sm font-medium text-white mb-4 flex items-center gap-2">{icon} {title}</h2>
      <div className="space-y-4">{children}</div>
    </section>
  );
}

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="grid gap-2 sm:grid-cols-[200px_1fr] sm:items-center">
      <div>
        <p className="text-sm text-slate-200">{label}</p>
        {hint && <p className="text-[11px] text-slate-500 mt-0.5">{hint}</p>}
      </div>
      <div>{children}</div>
    </div>
  );
}

function SliderInput({ value, setValue, min, max, step, unit }: {
  value: number; setValue: (v: number) => void; min: number; max: number; step: number; unit: string;
}) {
  return (
    <div className="flex items-center gap-3">
      <input
        type="range" min={min} max={max} step={step} value={value}
        onChange={(e) => setValue(parseFloat(e.target.value))}
        className="flex-1 accent-signal-500"
      />
      <span className="font-mono text-xs text-signal-300 w-16 text-right">
        {step < 1 ? value.toFixed(2) : value}{unit}
      </span>
    </div>
  );
}

function Endpoint({ url }: { url: string }) {
  return <code className="text-xs text-signal-300 bg-ink-800 px-2 py-1 rounded">{url}</code>;
}
