const PRIORITY_FILTERS = ['ALL', 'HIGH', 'MEDIUM', 'LOW'];
const CATEGORY_FILTERS = [
  'PAYMENT_ISSUE',
  'CLIENT_COMPLAINT',
  'SERVER_DOWN',
  'URGENT_REQUEST',
  'SUBSCRIPTION',
  'SPAM',
  'NEWSLETTER',
  'OTHER',
];

export default function FilterBar({ activeFilter, activeCategory, onFilterChange, onCategoryChange }) {
  return (
    <div className="mb-6 space-y-3">
      <div className="flex gap-2 flex-wrap">
        {PRIORITY_FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => onFilterChange(f)}
            className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded border transition-colors ${
              activeFilter === f
                ? 'border-accent text-accent bg-dark-surface'
                : 'border-dark-border text-text-muted hover:border-text-muted'
            }`}
          >
            {f}
          </button>
        ))}
      </div>
      <div className="flex gap-2 flex-wrap">
        {CATEGORY_FILTERS.map((c) => (
          <button
            key={c}
            onClick={() => onCategoryChange(activeCategory === c ? null : c)}
            className={`px-2.5 py-1 text-[11px] font-mono uppercase tracking-wider rounded border transition-colors ${
              activeCategory === c
                ? 'border-accent text-accent bg-dark-surface'
                : 'border-dark-border text-text-muted hover:border-text-muted'
            }`}
          >
            {c}
          </button>
        ))}
      </div>
    </div>
  );
}
