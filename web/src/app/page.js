'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Settings, Newspaper, CheckCircle, AlertCircle,
  Sun, Moon, Clock, Copy, RefreshCw,
  Lightbulb, Globe, MapPin, BookmarkCheck, X
} from 'lucide-react';

/* ─── Custom Icons ────────────────────────────────────────────── */
const LinkedInIcon = ({ size = 24, color = "currentColor" }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width={size} height={size} fill={color}>
    <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
  </svg>
);

/* ─── Helpers ─────────────────────────────────────────────────── */
const sourceBadge = (src) => {
  const map = {
    raindrop: { cls: 'badge-raindrop', icon: <BookmarkCheck size={10} />, label: 'Raindrop' },
    news:     { cls: 'badge-news',     icon: <Newspaper size={10} />,     label: 'News'     },
    hybrid:   { cls: 'badge-hybrid',   icon: <RefreshCw size={10} />,     label: 'Hybrid'   },
  };
  return map[src?.toLowerCase()] || map.news;
};

const regionBadge = (region) => {
  const isAU = region?.toLowerCase().includes('aus');
  return isAU
    ? { cls: 'badge-au',     icon: <MapPin size={10} />, label: 'Australia' }
    : { cls: 'badge-global', icon: <Globe size={10} />,  label: 'Global'    };
};

/* ─── Skeleton Loader ─────────────────────────────────────────── */
const SkeletonCard = () => (
  <div className="glass-card" style={{ gap: 12, display: 'flex', flexDirection: 'column' }}>
    <div className="skeleton" style={{ height: 20, width: '55%' }} />
    <div className="skeleton" style={{ height: 14, width: '100%' }} />
    <div className="skeleton" style={{ height: 14, width: '90%' }} />
    <div className="skeleton" style={{ height: 14, width: '75%' }} />
    <div className="skeleton" style={{ height: 14, width: '80%' }} />
    <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
      <div className="skeleton" style={{ height: 36, flex: 1, borderRadius: 8 }} />
      <div className="skeleton" style={{ height: 36, flex: 1, borderRadius: 8 }} />
    </div>
  </div>
);

/* ─── Idea Card ───────────────────────────────────────────────── */
const IdeaCard = ({ index, idea, delay = 0 }) => {
  const [copied, setCopied] = useState(false);
  const [openPage, setOpenPage] = useState(null);
  const [showFormatWhy, setShowFormatWhy] = useState(false);

  // idea can be an object {title, context, angle, source_type, region} or a plain string
  const isObj   = idea && typeof idea === 'object';
  const title   = isObj ? idea.title   : '';
  const context = isObj ? idea.context : '';
  const angle   = isObj ? idea.angle   : '';
  const src     = isObj ? idea.source_type : 'news';
  const region  = isObj ? idea.region  : '';
  const seriesTitle = isObj ? idea.series_title : '';
  const seriesThesis = isObj ? idea.series_thesis : '';
  const pages = isObj ? (idea.content?.pages || []) : [];
  const format = isObj ? idea.content?.format : '';
  const sourcesUsed = isObj ? (idea.grounding?.sources_used || []) : [];
  const playbook = isObj ? (idea.linkedin_playbook || null) : null;
  const body    = isObj ? null : String(idea);

  const draftMarkdown = isObj
    ? pages.map((p) => (p && p.markdown ? String(p.markdown).trim() : '')).filter(Boolean).join('\n\n---\n\n')
    : '';

  const hasDraft = Boolean(draftMarkdown);

  const [pagerInitialized, setPagerInitialized] = useState(false);
  useEffect(() => {
    if (pagerInitialized) return;
    if (pages?.length === 1 && String(pages[0]?.markdown || '').trim()) {
      setOpenPage(0);
      setPagerInitialized(true);
    }
  }, [pages, pagerInitialized]);

  const copyText = hasDraft ? draftMarkdown : (isObj ? `${title}\n\n${context}\n\n${angle}` : body);

  const handleCopy = () => {
    navigator.clipboard.writeText(copyText || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const sb = sourceBadge(src);
  const rb = regionBadge(region);

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="glass-card"
      style={{ borderLeft: '3px solid var(--accent)', position: 'relative', paddingTop: playbook?.why_this_works ? 40 : undefined }}
    >
      {playbook?.why_this_works && (
        <button
          type="button"
          onClick={() => setShowFormatWhy((v) => !v)}
          className="btn-ghost idea-bulb-btn"
          title="Why this format works?"
          aria-label="Why this format works?"
          style={{
            position: 'absolute',
            top: 12,
            right: 12,
            zIndex: 12,
            padding: 8,
            borderRadius: 10,
            background: 'rgba(124, 92, 252, 0.12)',
            border: '1px solid rgba(124, 92, 252, 0.25)',
          }}
        >
          <Lightbulb size={18} color="var(--gold)" />
        </button>
      )}
      {showFormatWhy && playbook?.why_this_works && (
        <div
          className="format-why-popover"
          role="dialog"
          aria-modal="true"
          style={{
            position: 'absolute',
            top: 48,
            right: 12,
            zIndex: 20,
            maxWidth: 320,
            width: 300,
            padding: 16,
            background: 'var(--bg-popover, #12162a)',
            border: '1px solid rgba(124, 92, 252, 0.3)',
            borderRadius: 14,
            boxShadow: '0 16px 48px rgba(0,0,0,0.6)',
            backdropFilter: 'blur(0px)',
          }}
        >
          <div className="flex items-center justify-between mb-2">
            <span className="section-label" style={{ marginBottom: 0 }}>Why this format works</span>
            <button type="button" className="btn-ghost" style={{ padding: 4 }} onClick={() => setShowFormatWhy(false)} aria-label="Close">
              <X size={16} />
            </button>
          </div>
          <p style={{ fontSize: '0.86rem', lineHeight: 1.55, color: 'var(--foreground)', opacity: 0.9 }}>{playbook.why_this_works}</p>
        </div>
      )}
      {index !== undefined && (
        <div style={{
          position: 'absolute', top: -14, left: -14, width: 28, height: 28,
          borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent), #fb7185)', 
          color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.85rem', fontWeight: 600, boxShadow: '0 4px 12px rgba(244, 114, 182, 0.4)',
          border: '3px solid var(--background)', zIndex: 10
        }}>
          {index}
        </div>
      )}
      {isObj ? (
        <>
          {(seriesTitle || seriesThesis) && (
            <div style={{
              background: 'linear-gradient(135deg, rgba(124, 92, 252, 0.12), rgba(59, 153, 252, 0.10))',
              border: '1px solid rgba(124, 92, 252, 0.18)',
              borderRadius: 12,
              padding: '12px 14px',
              marginBottom: 14
            }}>
              <div className="section-label" style={{ marginBottom: 6 }}>Series</div>
              {seriesTitle && <h4 style={{ marginBottom: 6, color: 'var(--foreground)' }}>{seriesTitle}</h4>}
              {seriesThesis && <p style={{ color: 'var(--foreground)', opacity: 0.78, fontSize: '0.9rem', lineHeight: 1.55 }}>{seriesThesis}</p>}
            </div>
          )}

          {/* Badges */}
          <div className="flex gap-2 mb-3 flex-wrap">
            <span className={`badge ${sb.cls}`}>{sb.icon} {sb.label}</span>
            {region && <span className={`badge ${rb.cls}`}>{rb.icon} {rb.label}</span>}
            {format && <span className="badge badge-count" style={{ borderRadius: 999, padding: '3px 10px' }}>{format}</span>}
            {playbook?.format_name && (
              <span className="badge badge-hybrid" style={{ borderRadius: 999, padding: '3px 10px', textTransform: 'none' }}>
                <LinkedInIcon size={12} /> {playbook.format_name}
              </span>
            )}
          </div>

          {playbook && (
            <div className="linkedin-playbook" style={{ marginBottom: 18 }}>
              {playbook.opening_hook && (
                <div style={{ marginBottom: 12 }}>
                  <div className="section-label">Opening hook</div>
                  <p style={{ fontSize: '0.95rem', lineHeight: 1.6, color: 'var(--foreground)' }}>{playbook.opening_hook}</p>
                </div>
              )}
              {playbook.why_section && (
                <div style={{ marginBottom: 12 }}>
                  <div className="section-label">Why it matters</div>
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.65, opacity: 0.88 }}>{playbook.why_section}</p>
                </div>
              )}
              {playbook.unique_take && (
                <div style={{ marginBottom: 12 }}>
                  <div className="section-label">Unique take</div>
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.65, opacity: 0.88 }}>{playbook.unique_take}</p>
                </div>
              )}
              {playbook.call_to_action && (
                <div style={{ marginBottom: 12 }}>
                  <div className="section-label">Call to action</div>
                  <p style={{ fontSize: '0.9rem', lineHeight: 1.65, fontWeight: 500 }}>{playbook.call_to_action}</p>
                </div>
              )}
              {playbook.poll_options?.length > 0 && (
                <div style={{ marginBottom: 12 }}>
                  <div className="section-label">Poll options</div>
                  <ol style={{ paddingLeft: 18, fontSize: '0.88rem', lineHeight: 1.6, opacity: 0.9 }}>
                    {playbook.poll_options.map((o, i) => <li key={i}>{o}</li>)}
                  </ol>
                </div>
              )}
            </div>
          )}

          {/* Title / research: hide when draft exists (avoids repeating the same story as Pager) */}
          {!hasDraft && (
            <>
              <div className="section-label">Title</div>
              <h3 style={{ color: 'var(--foreground)', marginBottom: 16, lineHeight: 1.4 }}>{title}</h3>
            </>
          )}
          {context && !hasDraft && (
            <div style={{ marginBottom: 14 }}>
              <div className="section-label">Context</div>
              <p style={{ color: 'var(--foreground)', opacity: 0.8, fontSize: '0.92rem', lineHeight: 1.65 }}>{context}</p>
            </div>
          )}
          {angle && !hasDraft && (
            <div style={{
              background: 'rgba(124, 92, 252, 0.07)',
              border: '1px solid rgba(124, 92, 252, 0.15)',
              borderRadius: 10,
              padding: '12px 14px',
              marginBottom: 16
            }}>
              <div className="section-label" style={{ marginBottom: 4 }}>Why it matters</div>
              <p style={{ color: 'var(--foreground)', opacity: 0.75, fontSize: '0.89rem', lineHeight: 1.6 }}>{angle}</p>
            </div>
          )}
          {hasDraft && title && (
            <div style={{ marginBottom: 12 }}>
              <div className="section-label">Headline</div>
              <h3 style={{ color: 'var(--foreground)', marginBottom: 0, lineHeight: 1.35, fontSize: '1.05rem' }}>{title}</h3>
            </div>
          )}

          {/* Sources used */}
          {sourcesUsed?.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div className="section-label">Grounding</div>
              <div className="flex gap-2 flex-wrap" style={{ opacity: 0.9 }}>
                {sourcesUsed.slice(0, 6).map((s, idx) => (
                  <a
                    key={idx}
                    href={s.url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="badge"
                    style={{
                      background: 'var(--surface-inset)',
                      border: '1px solid var(--surface-border)',
                      color: 'var(--foreground)',
                      textTransform: 'none',
                      letterSpacing: 0,
                      fontWeight: 500
                    }}
                    title={s.title}
                  >
                    {(s.source_type || 'src').toUpperCase()}: {(s.title || 'Source').slice(0, 38)}
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Pages */}
          {pages?.length > 0 && (
            <div style={{ marginBottom: 10 }}>
              <div className="section-label">Pager</div>
              <div className="flex-col gap-2">
                {pages.map((p, idx) => {
                  const isOpen = openPage === idx;
                  return (
                    <div key={idx} className="pager-card">
                      <button
                        className="pager-head"
                        onClick={() => setOpenPage(isOpen ? null : idx)}
                      >
                        <span style={{ fontWeight: 600, color: 'var(--foreground)' }}>{p.page_title || `Page ${idx + 1}`}</span>
                        <span style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>{isOpen ? 'Hide' : 'Show'}</span>
                      </button>
                      {isOpen && (
                        <div className="pager-body">
                          <pre style={{ margin: 0, opacity: 0.9 }}>{p.markdown || ''}</pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </>
      ) : (
        <pre style={{ color: 'var(--foreground)', opacity: 0.88, marginBottom: 16 }}>{body}</pre>
      )}

      <div className="divider" />
      <button
        onClick={handleCopy}
        className="btn-secondary"
        style={{ justifyContent: 'center', width: '100%' }}
        disabled={isObj && !hasDraft && !context && !angle && !title}
      >
        {copied ? <CheckCircle size={15} color="var(--success)" /> : <Copy size={15} />}
        {copied ? 'Copied!' : hasDraft ? 'Copy draft' : 'Copy'}
      </button>
    </motion.div>
  );
};

/* ─── Empty State ─────────────────────────────────────────────── */
const EmptyState = ({ icon, msg, onRetry, onRun }) => (
  <div className="empty-state flex-col items-center gap-4">
    <div className="empty-icon">{icon}</div>
    <div className="text-center">
      <p className="text-muted" style={{ fontSize: '1rem', marginBottom: 12 }}>{msg}</p>
      <div className="flex gap-3 justify-center">
        {onRetry && <button onClick={onRetry} className="btn-secondary">Reload</button>}
        {onRun && <button onClick={onRun} className="btn-primary">Run Pipeline</button>}
      </div>
    </div>
  </div>
);

/* ─── Stats Bar ───────────────────────────────────────────────── */
const StatsBar = ({ ideas }) => {
  const items = [
    { label: 'Content Ideas',   count: ideas?.length   || 0, color: 'var(--accent)'    },
  ];
  return (
    <div className="flex gap-4 flex-wrap">
      {items.map(({ label, count, color }) => (
        <div key={label} className="flex items-center gap-2" style={{ opacity: count ? 1 : 0.4 }}>
          <span style={{ width: 8, height: 8, borderRadius: '50%', background: color, display: 'inline-block', boxShadow: `0 0 6px ${color}` }} />
          <span style={{ fontSize: '0.82rem', color: 'var(--muted)' }}>{count} {label}</span>
        </div>
      ))}
    </div>
  );
};

/* ─── Main Page ───────────────────────────────────────────────── */
export default function Home() {
  const [results, setResults]             = useState({ ideas: null });
  const [previousIdeas, setPreviousIdeas] = useState(null);
  const [previousDate, setPreviousDate]   = useState(null);
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate]   = useState(null);
  const [todayStr, setTodayStr]           = useState(null);
  const [loading, setLoading]             = useState(true);
  const [error, setError]                 = useState(null);
  const [theme, setTheme]                 = useState('dark');

  /* ── Data Fetching ──── */
  const fetchCache = async (date = null) => {
    setLoading(true);
    try {
      const url = date ? `/api/cache?date=${date}` : '/api/cache';
      const res  = await fetch(url);
      const data = await res.json();

      // Handle both old (data) and new (posts / ideas) key schemas
      const ideasRaw = data.ideas?.ideas || data.ideas?.data  || null;
      const prevRaw  = data.previousIdeas?.ideas || data.previousIdeas?.data || null;

      setResults({ ideas: ideasRaw });
      setPreviousIdeas(prevRaw);
      setPreviousDate(data.previousDate || null);
      if (data.availableDates) setAvailableDates(data.availableDates);
      if (data.selectedDate)   setSelectedDate(data.selectedDate);
      if (data.todayStr)       setTodayStr(data.todayStr);
    } catch (err) {
      console.error('Failed to load cache:', err);
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

      {/* ── Tab Bar + Stats ── */}
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.1 }}
        className="flex items-center justify-between mb-6 flex-wrap gap-4"
      >
        <div className="tab-bar">
          <button className="tab-btn active" disabled>
            <Lightbulb size={15} />
            Ideas
            {results.ideas?.length > 0 && (
              <span className="badge badge-count" style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                {results.ideas.length}
              </span>
            )}
          </button>
        </div>
        <StatsBar ideas={results.ideas} />
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
          background: 'var(--accent-glow)',
          filter: 'blur(100px)', opacity: 0.18, pointerEvents: 'none', zIndex: 0,
          transition: 'background 0.5s ease'
        }} />

        <AnimatePresence mode="wait">
          <motion.div key="ideas"
            initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }}
            style={{ position: 'relative', zIndex: 1 }}
          >
            <div style={{ marginBottom: 24 }}>
              <h2 style={{ marginBottom: 4 }}>Ideas</h2>
              <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                5 connected finance ideas/day, grounded in bookmarks + trending news
              </p>
            </div>

            {loading ? (
              <div className="flex-col gap-4">
                {[0,1,2].map(i => <SkeletonCard key={i} />)}
              </div>
            ) : results.ideas?.length > 0 ? (
              <div className="flex-col gap-8 mt-2">
                {results.ideas.map((idea, i) => (
                  <IdeaCard key={i} index={i + 1} idea={idea} delay={i * 0.06} />
                ))}
              </div>
            ) : (
              <>
                {/* Today pending banner */}
                <div style={{
                  background: 'linear-gradient(135deg, rgba(124,92,252,0.10), rgba(59,153,252,0.08))',
                  border: '1px dashed rgba(124,92,252,0.35)',
                  borderRadius: 14,
                  padding: '20px 24px',
                  marginBottom: previousIdeas?.length > 0 ? 32 : 0,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 14,
                }}>
                  <Lightbulb size={28} color="var(--gold, #f59e0b)" style={{ flexShrink: 0 }} />
                  <div>
                    <p style={{ fontWeight: 600, color: 'var(--foreground)', marginBottom: 4 }}>
                      {selectedDate === todayStr || !selectedDate
                        ? `Today's ideas haven't been generated yet (${todayStr}).`
                        : `No ideas found for ${selectedDate}.`}
                    </p>
                    {previousIdeas?.length > 0 && (
                      <p style={{ fontSize: '0.85rem', color: 'var(--muted)' }}>
                        In the meantime, here are the last ideas from <strong>{previousDate}</strong>.
                      </p>
                    )}
                  </div>
                  <button onClick={() => fetchCache(selectedDate)} className="btn-secondary" style={{ marginLeft: 'auto', flexShrink: 0 }}>
                    <RefreshCw size={14} /> Reload
                  </button>
                </div>

                {/* Previous ideas as fallback */}
                {previousIdeas?.length > 0 && (
                  <div className="flex-col gap-8">
                    {previousIdeas.map((idea, i) => (
                      <IdeaCard key={i} index={i + 1} idea={idea} delay={i * 0.06} />
                    ))}
                  </div>
                )}
              </>
            )}
          </motion.div>
        </AnimatePresence>
      </motion.div>

      {/* ── Footer ── */}
      <p className="text-muted" style={{ textAlign: 'center', marginTop: 36, fontSize: '0.85rem', opacity: 0.7 }}>
        Made with 💙 by{' '}
        <a 
          href="https://minianonlink.vercel.app/tusharbhardwaj" 
          target="_blank" 
          rel="noopener noreferrer" 
          style={{ color: 'var(--primary)', textDecoration: 'none', fontWeight: 500, transition: 'color 0.2s' }}
          onMouseOver={(e) => e.target.style.color = 'var(--secondary)'}
          onMouseOut={(e) => e.target.style.color = 'var(--primary)'}
        >
          Tushar Bhardwaj
        </a>
      </p>
    </div>
  );
}
