'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import Link from 'next/link';
import {
  Newspaper, CheckCircle, AlertCircle,
  Sun, Moon, Clock, Copy, RefreshCw,
  Lightbulb, Calendar, Sunset, X
} from 'lucide-react';
import { copyToClipboard } from '@/utils/clipboard';

/* ─── Type Badges & Icons ──────────────────────────────────────── */
const typeMap = {
  morning: {
    label: 'Morning Commentary',
    color: '#f59e0b', // gold/orange
    icon: <Sun size={14} color="#f59e0b" />,
    badgeCls: 'badge-count'
  },
  daily: {
    label: 'Daily Commentary',
    color: '#fb7185', // rose
    icon: <Sunset size={14} color="#fb7185" />,
    badgeCls: 'badge-hybrid'
  },
  monthly: {
    label: 'Monthly Summary',
    color: '#3b99fc', // blue
    icon: <Calendar size={14} color="#3b99fc" />,
    badgeCls: 'badge-news'
  }
};

const getContentTypeDetails = (type) => {
  return typeMap[type?.toLowerCase()] || {
    label: type || 'Commentary',
    color: 'var(--primary)',
    icon: <Newspaper size={14} />,
    badgeCls: 'badge-global'
  };
};

/* ─── Skeleton Loader ─────────────────────────────────────────── */
const SkeletonCard = () => (
  <div className="glass-card" style={{ gap: 12, display: 'flex', flexDirection: 'column' }}>
    <div className="skeleton" style={{ height: 20, width: '40%' }} />
    <div className="skeleton" style={{ height: 14, width: '100%' }} />
    <div className="skeleton" style={{ height: 14, width: '95%' }} />
    <div className="skeleton" style={{ height: 14, width: '90%' }} />
    <div className="skeleton" style={{ height: 14, width: '60%' }} />
    <div className="skeleton" style={{ height: 36, width: '100%', borderRadius: 8, marginTop: 8 }} />
  </div>
);

/* ─── X Content Card ──────────────────────────────────────────── */
const XCard = ({ entry, index, delay = 0 }) => {
  const [copied, setCopied] = useState(false);

  const typeDetails = getContentTypeDetails(entry.type);
  const formattedTime = entry.timestamp
    ? new Date(entry.timestamp).toLocaleTimeString('en-AU', { hour: '2-digit', minute: '2-digit', hour12: true })
    : '';

  const handleCopy = () => {
    copyToClipboard(entry.content || '').then((success) => {
      if (success) {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      }
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="glass-card"
      style={{ borderLeft: `3px solid ${typeDetails.color}`, position: 'relative' }}
    >
      {/* Index Number */}
      {index !== undefined && (
        <div style={{
          position: 'absolute', top: -14, left: -14, width: 28, height: 28,
          borderRadius: '50%', background: `linear-gradient(135deg, ${typeDetails.color}, var(--bg-secondary))`,
          color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.85rem', fontWeight: 600, boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
          border: '3px solid var(--background)', zIndex: 10
        }}>
          {index}
        </div>
      )}

      {/* Header Metadata */}
      <div className="flex justify-between items-center mb-4 flex-wrap gap-2">
        <div className="flex gap-2 items-center">
          <span className={`badge ${typeDetails.badgeCls}`} style={{ textTransform: 'none', letterSpacing: 0, padding: '4px 12px' }}>
            <span className="flex items-center gap-1.5 font-semibold">
              {typeDetails.icon} {typeDetails.label}
            </span>
          </span>
        </div>
        {formattedTime && (
          <div className="flex items-center gap-1.5 text-muted" style={{ fontSize: '0.8rem' }}>
            <Clock size={12} />
            <span>Generated at {formattedTime}</span>
          </div>
        )}
      </div>

      {/* Body Content */}
      <div style={{
        background: 'var(--surface-inset)',
        border: '1px solid var(--surface-border)',
        borderRadius: 10,
        padding: '16px',
        marginBottom: 16,
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <pre style={{
          margin: 0,
          whiteSpace: 'pre-wrap',
          wordWrap: 'break-word',
          fontSize: '0.9rem',
          lineHeight: 1.65,
          fontFamily: 'inherit',
          color: 'var(--foreground)',
          opacity: 0.95
        }}>
          {entry.content}
        </pre>
      </div>

      <div className="divider" />
      <button
        onClick={handleCopy}
        className="btn-secondary"
        style={{ justifyContent: 'center', width: '100%' }}
      >
        {copied ? <CheckCircle size={15} color="var(--success)" /> : <Copy size={15} />}
        {copied ? 'Copied!' : 'Copy to clipboard'}
      </button>
    </motion.div>
  );
};

/* ─── Main Page ───────────────────────────────────────────────── */
export default function XDashboard() {
  const [entries, setEntries] = useState(null);
  const [previousEntries, setPreviousEntries] = useState(null);
  const [previousDate, setPreviousDate] = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate] = useState(null);
  const [todayStr, setTodayStr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState('dark');

  /* ── Data Fetching ──── */
  const fetchCache = async (date = null) => {
    setLoading(true);
    try {
      const url = date ? `/api/x_cache?date=${date}` : '/api/x_cache';
      const res = await fetch(url);
      const data = await res.json();

      setEntries(data.entries || null);
      setPreviousEntries(data.previousEntries || null);
      setPreviousDate(data.previousDate || null);
      if (data.availableDates) setAvailableDates(data.availableDates);
      if (data.selectedDate) setSelectedDate(data.selectedDate);
      if (data.todayStr) setTodayStr(data.todayStr);
    } catch (err) {
      console.error('Failed to load X cache:', err);
      setError('Could not fetch generated content logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const saved = localStorage.getItem('theme');
    if (saved === 'light') {
      setTheme('light');
      document.body.classList.add('light-theme');
    }
    fetchCache();
  }, []);

  /* ── Theme ──── */
  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
    document.body.classList.toggle('light-theme', next === 'light');
  };

  return (
    <div className="flex-col" style={{ minHeight: '100vh', paddingTop: 36, paddingBottom: 60, gap: 0 }}>

      {/* ── Header ── */}
      <motion.header
        initial={{ opacity: 0, y: -12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}
        className="flex items-center justify-between mb-8"
      >
        <div className="flex items-center gap-4">
          {/* Custom SVG Logo */}
          <div style={{
            width: 52, height: 52, borderRadius: 16,
            background: 'linear-gradient(135deg, rgba(124, 92, 252, 0.1) 0%, rgba(59, 153, 252, 0.15) 100%)',
            border: '1px solid rgba(124, 92, 252, 0.3)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 8px 24px rgba(124, 92, 252, 0.25)',
            position: 'relative', overflow: 'hidden', flexShrink: 0
          }}>
            {/* Spinning gradient border effect */}
            <div style={{
              position: 'absolute', top: '-50%', left: '-50%', width: '200%', height: '200%',
              background: 'conic-gradient(transparent, rgba(124, 92, 252, 0.4), transparent 30%)',
              animation: 'spin 4s linear infinite'
            }} />

            {/* Inner background and logo */}
            <div style={{
              position: 'absolute', inset: 2, background: 'var(--surface)',
              borderRadius: 14, display: 'flex', alignItems: 'center', justifyContent: 'center'
            }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="url(#vittiGrad)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <defs>
                  <linearGradient id="vittiGrad" x1="0" y1="0" x2="1" y2="1">
                    <stop offset="0%" stopColor="#8b5cf6" />
                    <stop offset="100%" stopColor="#3b82f6" />
                  </linearGradient>
                </defs>
                <path d="M5 4l7 15 7-15" />
                <path d="M12 19v-5" />
              </svg>
            </div>
          </div>

          <div>
            <h1 className="text-gradient" style={{ lineHeight: 1.1, marginBottom: 4 }}>VITTI Engine</h1>
            <p style={{ color: 'var(--muted)', fontSize: '0.85rem', fontWeight: 500 }}>AI Content Dashboard · Vitti Capital</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Date Selector */}
          {availableDates.length > 0 && (
            <div className="date-pill">
              <Clock size={14} color="var(--primary)" />
              <select
                value={selectedDate || ''}
                onChange={(e) => { setSelectedDate(e.target.value); fetchCache(e.target.value); }}
              >
                {availableDates.map(d => (
                  <option key={d} value={d} style={{ background: 'var(--bg-secondary)' }}>
                    {d === todayStr ? `Today (${d})` : d}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Refresh */}
          <button
            className="btn-ghost"
            onClick={() => fetchCache(selectedDate)}
            disabled={loading}
            title="Refresh data"
          >
            <RefreshCw size={16} className={loading ? 'spinner' : ''} />
          </button>

          {/* Theme Toggle */}
          <button className="btn-ghost" onClick={toggleTheme} aria-label="Toggle theme">
            {theme === 'dark' ? <Sun size={17} /> : <Moon size={17} />}
          </button>
        </div>
      </motion.header>

      {/* ── Error Toast ── */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
            className="flex items-center gap-3 mb-6"
            style={{
              background: 'var(--error-bg)', color: 'var(--error)',
              border: '1px solid rgba(248,113,113,0.25)',
              borderRadius: 10, padding: '12px 16px'
            }}
          >
            <AlertCircle size={18} />
            <p style={{ fontSize: '0.875rem' }}>{error}</p>
            <button onClick={() => setError(null)} className="btn-ghost" style={{ marginLeft: 'auto', padding: '4px 8px' }}>✕</button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Navigation Tab Bar ── */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="flex items-center justify-between mb-6 flex-wrap gap-4"
      >
        <div className="tab-bar">
          <Link href="/" className="tab-btn" style={{ textDecoration: 'none' }}>
            <Lightbulb size={15} />
            Ideas
          </Link>
          <Link href="/x-dashboard" className="tab-btn active" style={{ textDecoration: 'none' }}>
            <Newspaper size={15} />
            X Content
            {entries?.length > 0 && (
              <span className="badge badge-count" style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                {entries.length}
              </span>
            )}
          </Link>
        </div>
      </motion.div>

      {/* ── Main Content ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.15 }}
        className="glass-card"
        style={{ minHeight: '60vh', overflow: 'hidden' }}
      >
        {/* Ambient glow */}
        <div style={{
          position: 'absolute', top: '-20%', right: '-10%',
          width: 350, height: 350,
          background: 'var(--secondary-glow)',
          filter: 'blur(100px)', opacity: 0.18, pointerEvents: 'none', zIndex: 0,
          transition: 'background 0.5s ease'
        }} />

        <AnimatePresence mode="wait">
          <motion.div key="x-content"
            initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }}
            style={{ position: 'relative', zIndex: 1 }}
          >
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ marginBottom: 4 }}>X Content & Commentary</h2>
              <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                Morning outlooks, daily closings, and monthly summaries generated for Sydney trading sessions.
              </p>
            </div>

            {loading ? (
              <div className="flex-col gap-4">
                {[0, 1, 2].map(i => <SkeletonCard key={i} />)}
              </div>
            ) : entries?.length > 0 ? (
              <div className="flex-col gap-8 mt-2">
                {entries.map((entry, i) => (
                  <XCard key={i} index={i + 1} entry={entry} delay={i * 0.06} />
                ))}
              </div>
            ) : (
              <>
                {/* Today pending banner */}
                <div style={{
                  background: 'linear-gradient(135deg, rgba(59,153,252,0.10), rgba(124,92,252,0.08))',
                  border: '1px dashed rgba(59,153,252,0.35)',
                  borderRadius: 14,
                  padding: '20px 24px',
                  marginBottom: previousEntries?.length > 0 ? 32 : 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                }}>
                  <Newspaper size={28} color="var(--primary)" style={{ flexShrink: 0 }} />
                  <div>
                    <p style={{ fontWeight: 600, color: 'var(--foreground)', marginBottom: 4 }}>
                      {selectedDate === todayStr || !selectedDate
                        ? `Today's commentaries have not been generated yet (${todayStr}).`
                        : `No content logs found for ${selectedDate}.`}
                    </p>
                    {previousEntries?.length > 0 && (
                      <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                        In the meantime, here are the commentaries from <strong>{previousDate}</strong>.
                      </p>
                    )}
                  </div>
                  <button onClick={() => fetchCache(selectedDate)} className="btn-secondary" style={{ marginLeft: 'auto', flexShrink: 0 }}>
                    <RefreshCw size={14} /> Reload
                  </button>
                </div>

                {/* Previous entries as fallback */}
                {previousEntries?.length > 0 && (
                  <div className="flex-col gap-8">
                    {previousEntries.map((entry, i) => (
                      <XCard key={i} index={i + 1} entry={entry} delay={i * 0.06} />
                    ))}
                  </div>
                )}
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </motion.div>
    </div>
  );
}
