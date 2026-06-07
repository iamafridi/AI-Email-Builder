import { useState } from 'react';

const PRIORITY_COLORS = {
  HIGH: 'border-priority-high text-priority-high',
  MEDIUM: 'border-priority-medium text-priority-medium',
  LOW: 'border-priority-low text-priority-low',
};

const PRIORITY_BG = {
  HIGH: 'bg-priority-high/10',
  MEDIUM: 'bg-priority-medium/10',
  LOW: 'bg-priority-low/10',
};

function timeAgo(dateStr) {
  const now = new Date();
  const date = new Date(dateStr);
  const seconds = Math.floor((now - date) / 1000);
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
}

export default function NotificationCard({ notification, onDismiss }) {
  const [dismissing, setDismissing] = useState(false);
  const colorClass = PRIORITY_COLORS[notification.priority] || PRIORITY_COLORS.LOW;
  const badgeClass = PRIORITY_BG[notification.priority] || PRIORITY_BG.LOW;

  const handleDismiss = () => {
    setDismissing(true);
    setTimeout(() => onDismiss(notification.id), 300);
  };

  return (
    <div
       className={`bg-dark-surface border border-dark-border border-l-4 ${colorClass.split(' ')[0]} rounded p-4 mb-3 transition-all duration-300 hover:bg-dark-hover ${
        dismissing ? 'opacity-0 translate-y-2' : 'opacity-100 animate-slideDown'
      }`}
      style={{ borderLeftColor: 'inherit' }}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className={`inline-block px-2 py-0.5 text-[11px] font-mono font-bold uppercase rounded ${colorClass} ${badgeClass}`}>
              {notification.priority}
            </span>
            <span className="inline-block px-2 py-0.5 text-[11px] font-mono text-text-muted bg-dark-bg rounded border border-dark-border">
              {notification.category}
            </span>
          </div>
          <h3 className="text-base font-semibold text-text-primary truncate">{notification.subject}</h3>
          <p className="text-sm font-mono text-text-muted mt-1">From: {notification.sender}</p>
          {notification.reason && (
            <p className="text-sm text-text-muted italic mt-1 ml-2 border-l-2 border-dark-border pl-3">
              {notification.reason}
            </p>
          )}
          <p className="text-xs font-mono text-text-muted mt-2" title={notification.received_at}>
            {timeAgo(notification.received_at)}
          </p>
        </div>
        <button
          onClick={handleDismiss}
          className="ml-4 text-text-muted hover:text-priority-high transition-colors text-lg leading-none flex-shrink-0"
          title="Dismiss"
        >
          &times;
        </button>
      </div>
    </div>
  );
}
