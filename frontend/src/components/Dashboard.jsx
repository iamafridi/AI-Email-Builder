import { useState, useEffect, useCallback } from 'react';
import StatsBar from './StatsBar';
import FilterBar from './FilterBar';
import NotificationCard from './NotificationCard';
import Toast from './Toast';

const API_BASE = window.location.origin + '/api';

export default function Dashboard() {
  const [notifications, setNotifications] = useState([]);
  const [stats, setStats] = useState({ total: 0, high: 0, medium: 0, low: 0 });
  const [activeFilter, setActiveFilter] = useState('ALL');
  const [activeCategory, setActiveCategory] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [config, setConfig] = useState({ mode: 'mock', available_modes: ['mock', 'csv', 'imap'], imap_connected: false });
  const [imapForm, setImapForm] = useState({ host: 'imap.gmail.com', port: 993, user: '', password: '' });
  const [csvFile, setCsvFile] = useState(null);
  const [csvUploading, setCsvUploading] = useState(false);
  const [pollMode, setPollMode] = useState('auto');
  const [loadingAll, setLoadingAll] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'info') => {
    const id = Date.now() + Math.random();
    setToasts((prev) => [...prev, { id, message, type }]);
  };

  const removeToast = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const fetchNotifications = useCallback(async () => {
    try {
      const [notifRes, statsRes] = await Promise.all([
        fetch(`${API_BASE}/notifications`),
        fetch(`${API_BASE}/stats`),
      ]);
      if (notifRes.ok) setNotifications(await notifRes.json());
      if (statsRes.ok) setStats(await statsRes.json());
    } catch {
      // silent fail
    } finally {
      setLoading(false);
    }
  }, []);

  const fetchConfig = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/config`);
      if (res.ok) setConfig(await res.json());
    } catch {
      // silent fail
    }
  }, []);

  const fetchPollMode = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/poll-mode`);
      if (res.ok) {
        const data = await res.json();
        setPollMode(data.mode);
      }
    } catch {
      // silent fail
    }
  }, []);

  useEffect(() => {
    fetchNotifications();
    fetchConfig();
    fetchPollMode();
    const interval = setInterval(fetchNotifications, 10000);
    return () => clearInterval(interval);
  }, [fetchNotifications, fetchConfig, fetchPollMode]);

  const handleDismiss = async (id) => {
    try {
      await fetch(`${API_BASE}/notifications/${id}`, { method: 'DELETE' });
      fetchNotifications();
    } catch {
      // silent fail
    }
  };

  const handleModeSwitch = async (mode) => {
    try {
      const res = await fetch(`${API_BASE}/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
      });
      if (res.ok) {
        const data = await res.json();
        setConfig((c) => ({ ...c, mode: data.mode }));
        addToast(`Switched to ${mode} mode`, 'success');
      }
    } catch {
      addToast('Failed to switch mode', 'error');
    }
  };

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) setCsvFile(file);
  };

  const handleUploadSubmit = async () => {
    if (!csvFile) return;
    setCsvUploading(true);
    const formData = new FormData();
    formData.append('file', csvFile);
    try {
      const res = await fetch(`${API_BASE}/upload-csv`, { method: 'POST', body: formData });
      if (res.ok) {
        setConfig((c) => ({ ...c, mode: 'csv' }));
        addToast(`Loaded ${csvFile.name}`, 'success');
        await handleLoadAll();
      } else {
        addToast('CSV upload failed', 'error');
      }
    } catch {
      addToast('CSV upload failed', 'error');
    } finally {
      setCsvUploading(false);
    }
  };

  const handleLoadAll = async () => {
    setLoadingAll(true);
    try {
      await fetch(`${API_BASE}/load-all`, { method: 'POST' });
      await fetchNotifications();
      addToast('All remaining emails loaded', 'success');
    } catch {
      addToast('Failed to load emails', 'error');
    } finally {
      setLoadingAll(false);
    }
  };

  const handlePollModeToggle = async () => {
    const next = pollMode === 'auto' ? 'manual' : 'auto';
    try {
      const res = await fetch(`${API_BASE}/poll-mode`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: next }),
      });
      if (res.ok) {
        setPollMode(next);
        addToast(`Polling: ${next}`, 'success');
      }
    } catch {
      addToast('Failed to switch poll mode', 'error');
    }
  };

  const handleImapConnect = async () => {
    try {
      const res = await fetch(`${API_BASE}/connect-imap`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(imapForm),
      });
      if (res.ok) {
        setConfig((c) => ({ ...c, mode: 'imap', imap_connected: true }));
        addToast('IMAP connected', 'success');
      }
    } catch {
      addToast('IMAP connection failed', 'error');
    }
  };

  const filtered = notifications.filter((n) => {
    if (activeFilter !== 'ALL' && n.priority !== activeFilter) return false;
    if (activeCategory && n.category !== activeCategory) return false;
    return true;
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <header className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold font-mono tracking-tight">
            AI Email Agent{' '}
            <span className="text-accent text-sm font-normal tracking-wider uppercase">
              Dashboard
            </span>
          </h1>
          <p className="text-text-muted text-sm mt-1">
            Monitoring incoming emails — flagging important ones in real time
          </p>
        </div>
        <button
          onClick={() => setShowSettings(!showSettings)}
          className="text-text-muted hover:text-text-main transition-colors text-sm font-mono"
        >
          {showSettings ? '[ − ]' : '[ ⚙ ]'} Settings
        </button>
      </header>

      <StatsBar stats={stats} />
      <FilterBar
        activeFilter={activeFilter}
        activeCategory={activeCategory}
        onFilterChange={setActiveFilter}
        onCategoryChange={setActiveCategory}
      />

      {showSettings && (
        <div className="border border-border rounded p-4 mb-6 bg-bg-card text-sm font-mono">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-accent">▶</span>
            <span className="text-text-main font-bold">Email Source</span>
            <span className="text-text-muted ml-auto">
              Current: <span className="text-accent">{config.mode.toUpperCase()}</span>
            </span>
          </div>

          <div className="flex gap-2 mb-3">
            {config.available_modes.map((m) => (
              <button
                key={m}
                onClick={() => handleModeSwitch(m)}
                className={`px-3 py-1 rounded border text-xs uppercase tracking-wider transition-colors ${
                  config.mode === m
                    ? 'bg-accent text-bg-dark border-accent'
                    : 'bg-bg-dark text-text-muted border-border hover:text-text-main hover:border-text-muted'
                }`}
              >
                {m}
              </button>
            ))}
          </div>

          {config.mode === 'csv' && (
            <div className="bg-bg-dark rounded p-3 mb-2">
              <label className="block mb-1 text-text-muted text-xs uppercase tracking-wider">
                Upload CSV File
              </label>
              <div className="flex gap-2 items-center">
                <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileSelect}
                  className="block text-xs text-text-muted file:mr-3 file:py-1 file:px-3 file:rounded file:border file:border-border file:bg-bg-dark file:text-text-main file:text-xs file:font-mono hover:file:border-accent flex-1"
                />
                <button
                  onClick={handleUploadSubmit}
                  disabled={!csvFile || csvUploading}
                  className={`px-3 py-1.5 text-xs font-mono uppercase tracking-wider rounded border transition-colors ${
                    !csvFile || csvUploading
                      ? 'border-border text-text-muted cursor-not-allowed opacity-50'
                      : 'border-accent text-accent hover:bg-accent hover:text-bg-dark'
                  }`}
                >
                  {csvUploading ? 'Uploading…' : 'Upload'}
                </button>
              </div>
            </div>
          )}

          {config.mode === 'imap' && (
            <div className="bg-bg-dark rounded p-3 mb-2">
              <label className="block mb-2 text-text-muted text-xs uppercase tracking-wider">
                Gmail IMAP Configuration
              </label>
              <div className="grid grid-cols-2 gap-2 mb-2">
                <input
                  placeholder="Host"
                  value={imapForm.host}
                  onChange={(e) => setImapForm((f) => ({ ...f, host: e.target.value }))}
                  className="bg-bg-card border border-border rounded px-2 py-1 text-text-main text-xs font-mono col-span-2"
                />
                <input
                  placeholder="Port"
                  type="number"
                  value={imapForm.port}
                  onChange={(e) => setImapForm((f) => ({ ...f, port: parseInt(e.target.value) }))}
                  className="bg-bg-card border border-border rounded px-2 py-1 text-text-main text-xs font-mono"
                />
                <input
                  placeholder="User (email)"
                  value={imapForm.user}
                  onChange={(e) => setImapForm((f) => ({ ...f, user: e.target.value }))}
                  className="bg-bg-card border border-border rounded px-2 py-1 text-text-main text-xs font-mono"
                />
                <input
                  placeholder="Password (App Password)"
                  type="password"
                  value={imapForm.password}
                  onChange={(e) => setImapForm((f) => ({ ...f, password: e.target.value }))}
                  className="bg-bg-card border border-border rounded px-2 py-1 text-text-main text-xs font-mono col-span-2"
                />
              </div>
              <button
                onClick={handleImapConnect}
                className="px-4 py-1 rounded border border-accent text-accent text-xs uppercase tracking-wider hover:bg-accent hover:text-bg-dark transition-colors"
              >
                Connect
              </button>
            </div>
          )}

          <div className="border-t border-border mt-4 pt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-text-muted text-xs uppercase tracking-wider">Polling</span>
                <button
                  onClick={handlePollModeToggle}
                  className={`px-3 py-1 text-xs font-mono uppercase tracking-wider rounded border transition-colors ${
                    pollMode === 'auto'
                      ? 'border-accent text-accent bg-dark-surface'
                      : 'border-border text-text-muted hover:border-text-muted'
                  }`}
                >
                  {pollMode === 'auto' ? 'Auto' : 'Manual'}
                </button>
              </div>
              <button
                onClick={handleLoadAll}
                disabled={loadingAll}
                className={`px-3 py-1 text-xs font-mono uppercase tracking-wider rounded border transition-colors ${
                  loadingAll
                    ? 'border-border text-text-muted cursor-not-allowed opacity-50'
                    : 'border-accent text-accent hover:bg-accent hover:text-bg-dark'
                }`}
              >
                {loadingAll ? 'Loading…' : 'Load All Now'}
              </button>
            </div>
          </div>
        </div>
      )}

      {loading ? (
        <div>
          {[1, 2, 3].map((i) => (
            <div key={i} className="bg-dark-surface border border-dark-border border-l-4 border-dark-border rounded p-4 mb-3 animate-pulse-shimmer">
              <div className="flex items-center gap-2 mb-3">
                <div className="h-4 w-14 rounded bg-dark-border" />
                <div className="h-4 w-24 rounded bg-dark-border" />
              </div>
              <div className="h-5 w-3/4 rounded bg-dark-border mb-2" />
              <div className="h-3 w-1/3 rounded bg-dark-border mb-2" />
              <div className="h-3 w-1/2 rounded bg-dark-border" />
            </div>
          ))}
        </div>
      ) : filtered.length === 0 ? (
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

      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
        {toasts.map((t) => (
          <div key={t.id} className="pointer-events-auto">
            <Toast message={t.message} type={t.type} onRemove={() => removeToast(t.id)} />
          </div>
        ))}
      </div>
    </div>
  );
}
