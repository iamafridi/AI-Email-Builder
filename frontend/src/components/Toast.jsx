import { useState, useEffect } from 'react';

const TOAST_TYPES = {
  success: { border: 'border-green-500', icon: '✓' },
  error: { border: 'border-red-500', icon: '✗' },
  info: { border: 'border-blue-500', icon: 'i' },
};

export default function Toast({ message, type = 'info', onRemove }) {
  const [exiting, setExiting] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setExiting(true);
      setTimeout(onRemove, 300);
    }, 3500);
    return () => clearTimeout(timer);
  }, [onRemove]);

  const t = TOAST_TYPES[type] || TOAST_TYPES.info;

  return (
    <div
      className={`flex items-center gap-3 px-4 py-3 rounded border-l-4 bg-dark-surface border-border shadow-lg text-sm font-mono transition-all duration-300 ${
        exiting ? 'opacity-0 translate-x-4' : 'opacity-100 animate-slideInRight'
      } ${t.border}`}
    >
      <span className={`flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold ${
        type === 'success' ? 'bg-green-500/20 text-green-400' :
        type === 'error' ? 'bg-red-500/20 text-red-400' :
        'bg-blue-500/20 text-blue-400'
      }`}>
        {t.icon}
      </span>
      <span className="flex-1 text-text-primary">{message}</span>
      <button
        onClick={() => { setExiting(true); setTimeout(onRemove, 300); }}
        className="text-text-muted hover:text-text-primary transition-colors leading-none text-lg"
      >
        &times;
      </button>
    </div>
  );
}
