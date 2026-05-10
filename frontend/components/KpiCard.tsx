interface KpiCardProps {
  label: string;
  value: string;
  delta?: string;
  status?: 'good' | 'warn' | 'bad';
  hint?: string;
}

const statusColors = {
  good: 'text-ok-500 bg-ok-500/10',
  warn: 'text-warn-500 bg-warn-500/10',
  bad:  'text-bad-500 bg-bad-500/10',
};

export default function KpiCard({
  label,
  value,
  delta,
  status = 'good',
  hint,
}: KpiCardProps) {
  return (
    <div className="rounded-2xl border border-ink-100 bg-white p-5 shadow-soft">
      <div className="flex items-start justify-between gap-2">
        <div className="text-xs uppercase tracking-wider font-semibold text-ink-700/70">
          {label}
        </div>
        {delta && (
          <span
            className={[
              'rounded-full px-2 py-0.5 text-[11px] font-mono font-medium',
              statusColors[status],
            ].join(' ')}
          >
            {delta}
          </span>
        )}
      </div>
      <div className="mt-2 font-display text-3xl font-bold text-ink-900 leading-none">
        {value}
      </div>
      {hint && (
        <div className="mt-2 text-xs text-ink-700/70">{hint}</div>
      )}
    </div>
  );
}
