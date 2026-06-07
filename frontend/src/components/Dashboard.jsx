import { useState, useEffect, useCallback } from 'react';
import StatsBar from './StatsBar';
import FilterBar from './FilterBar';
import NotificationCard from './NotificationCard';

const API_BASE = window.location.origin + '/api';

export default function Dashboard() {
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({ total: 0, high: 0, medium: 0, low: 0 });
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [activeCategory, setActiveCategory] = useState(null);

  const fetchNotifications = useCallback(async () => {
    try {
      const [notifRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/notifications`),
        fetch(`${API_BASE}/stats`),
      ]);
      if (notifRes.ok) setNotifications(await notifRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch {
      // silent fail — backend may not be ready
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, [fetchNotifications]);

  const handleDismiss = async (id) => {
    try {
      await fetch(`${API_BASE}/notifications/${id}`, { method: 'DELETE' });
      fetchNotifications();
    } catch {
      // silent fail
    }
  };

  const filtered = notifications.filter((n) => {
    if (activeFilter !== 'ALL' && n.priority !== activeFilter) return false;
    if (activeCategory && n.category !== activeCategory) return false;
    return true;
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-2xl font-bold font-mono tracking-tight">
          AI Email Agent{' '}
          <span className="text-accent text-sm font-normal tracking-wider uppercase">
            Dashboard
          </span>
        </h1>
        <p className="text-text-muted text-sm mt-1">
          Monitoring incoming emails — flagging important ones in real time
        </p>
      </header>

      <StatsBar stats={stats} />
      <FilterBar
        activeFilter={activeFilter}
        activeCategory={activeCategory}
        onFilterChange={setActiveFilter}
        onCategoryChange={setActiveCategory}
      />

      {filtered.length === 0 ? (
        <div className="text-center py-20">
          <div className="text-4xl mb-4 text-text-muted">[ ]</div>
          <p className="text-text-muted font-mono text-sm">
            No important emails detected. Monitoring inbox...
          </p>
        </div>
      ) : (
        <div>
          {filtered.map((n) => (
            <NotificationCard key={n.id} notification={n} onDismiss={handleDismiss} />
          ))}
        </div>
      )}
    </div>
  );
}
