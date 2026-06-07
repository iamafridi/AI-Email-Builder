const STATS = [
  { key: 'total', label: 'Total Flagged', color: 'text-text-primary', border: 'border-dark-border' },
  { key: 'high', label: 'HIGH', color: 'text-priority-high', border: 'border-priority-high' },
  { key: 'medium', label: 'MEDIUM', color: 'text-priority-medium', border: 'border-priority-medium' },
  { key: 'low', label: 'LOW', color: 'text-priority-low', border: 'border-priority-low' },
];

export default function StatsBar({ stats }) {
  return (
    <div className="grid grid-cols-4 gap-4 mb-6">
      {STATS.map((s) => (
        <div
          key={s.key}
          className={`bg-dark-surface border ${s.border} rounded p-4 flex flex-col items-center`}
        >
          <span className={`text-3xl font-bold font-mono ${s.color}`}>
            {stats?.[s.key] ?? 0}
          </span>
          <span className="text-text-muted text-xs font-mono uppercase tracking-wider mt-1">
            {s.label}
          </span>
        </div>
      ))}
    </div>
  );
}
