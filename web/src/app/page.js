'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import {
  Settings, Newspaper, Sparkles, CheckCircle, AlertCircle,
  Loader2, Sun, Moon, Clock, Copy, RefreshCw,
  TrendingUp, Lightbulb, Globe, MapPin, BookmarkCheck
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

/* ─── Post Card (CEO & LinkedIn posts) ───────────────────────── */
const PostCard = ({ index, topic, content, delay = 0 }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleLinkedIn = () => {
    if (!content) return;
    
    // LinkedIn's URL parser has a severe bug where it double-decodes and truncates text at '?' and '&' characters.
    // We replace them with visually identical Fullwidth Unicode characters to bypass the truncation entirely.
    const safeContent = content
      .replace(/\?/g, '\uFF1F')
      .replace(/&/g, '\uFF06')
      .replace(/#/g, '\uFF03');

    const url = `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(safeContent + '\u200B')}`;
    window.open(url, '_blank', 'noopener,noreferrer');
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 18 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
      className="glass-card"
      style={{ borderLeft: '3px solid var(--primary)', position: 'relative' }}
    >
      {index !== undefined && (
        <div style={{
          position: 'absolute', top: -14, left: -14, width: 28, height: 28,
          borderRadius: '50%', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', 
          color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: '0.85rem', fontWeight: 600, boxShadow: '0 4px 12px rgba(124, 92, 252, 0.4)',
          border: '3px solid var(--background)', zIndex: 10
        }}>
          {index}
        </div>
      )}
      {topic && (
        <>
          <div className="flex items-center gap-2 mb-2">
            <TrendingUp size={14} color="var(--primary)" />
            <span className="text-label">Topic</span>
          </div>
          <h3 style={{ color: 'var(--foreground)', marginBottom: 16 }}>{topic}</h3>
          <div className="divider" />
        </>
      )}
      <pre style={{ color: 'var(--foreground)', opacity: 0.88 }}>{content}</pre>
      <div className="divider" />
      <div className="flex gap-3">
        <button onClick={handleCopy} className="btn-secondary w-full" style={{ justifyContent: 'center' }}>
          {copied ? <CheckCircle size={15} color="var(--success)" /> : <Copy size={15} />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
        <button onClick={handleLinkedIn} className="btn-primary w-full" style={{ justifyContent: 'center' }}>
          <LinkedInIcon size={15} />
          Post to LinkedIn
        </button>
      </div>
    </motion.div>
  );
};

/* ─── Idea Card ───────────────────────────────────────────────── */
const IdeaCard = ({ index, idea, delay = 0 }) => {
  const [copied, setCopied] = useState(false);

  // idea can be an object {title, context, angle, source_type, region} or a plain string
  const isObj   = idea && typeof idea === 'object';
  const title   = isObj ? idea.title   : '';
  const context = isObj ? idea.context : '';
  const angle   = isObj ? idea.angle   : '';
  const src     = isObj ? idea.source_type : 'news';
  const region  = isObj ? idea.region  : '';
  const body    = isObj ? null : String(idea);

  const copyText = isObj
    ? `${title}\n\nContext: ${context}\n\nAngle: ${angle}`
    : body;

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
      style={{ borderLeft: '3px solid var(--accent)', position: 'relative' }}
    >
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
          {/* Badges */}
          <div className="flex gap-2 mb-3 flex-wrap">
            <span className={`badge ${sb.cls}`}>{sb.icon} {sb.label}</span>
            {region && <span className={`badge ${rb.cls}`}>{rb.icon} {rb.label}</span>}
          </div>

          {/* Hook / Title */}
          <div className="section-label">Hook</div>
          <h3 style={{ color: 'var(--foreground)', marginBottom: 16, lineHeight: 1.4 }}>{title}</h3>

          {/* Context */}
          {context && (
            <div style={{ marginBottom: 14 }}>
              <div className="section-label">Context</div>
              <p style={{ color: 'var(--foreground)', opacity: 0.8, fontSize: '0.92rem', lineHeight: 1.65 }}>{context}</p>
            </div>
          )}

          {/* Angle */}
          {angle && (
            <div style={{
              background: 'rgba(124, 92, 252, 0.07)',
              border: '1px solid rgba(124, 92, 252, 0.15)',
              borderRadius: 10,
              padding: '12px 14px',
              marginBottom: 16
            }}>
              <div className="section-label" style={{ marginBottom: 4 }}>Why It Matters</div>
              <p style={{ color: 'var(--foreground)', opacity: 0.75, fontSize: '0.89rem', lineHeight: 1.6 }}>{angle}</p>
            </div>
          )}
        </>
      ) : (
        <pre style={{ color: 'var(--foreground)', opacity: 0.88, marginBottom: 16 }}>{body}</pre>
      )}

      <div className="divider" />
      <button onClick={handleCopy} className="btn-secondary" style={{ justifyContent: 'center', width: '100%' }}>
        {copied ? <CheckCircle size={15} color="var(--success)" /> : <Copy size={15} />}
        {copied ? 'Copied!' : 'Copy Idea'}
      </button>
    </motion.div>
  );
};

/* ─── Empty State ─────────────────────────────────────────────── */
const EmptyState = ({ icon, msg }) => (
  <div className="empty-state flex-col items-center gap-4">
    <div className="empty-icon">{icon}</div>
    <p className="text-muted" style={{ fontSize: '1rem' }}>{msg}</p>
  </div>
);

/* ─── Stats Bar ───────────────────────────────────────────────── */
const StatsBar = ({ ceo, posts, ideas }) => {
  const items = [
    { label: 'CEO Posts',       count: ceo?.length    || 0, color: 'var(--primary)'   },
    { label: 'LinkedIn Drafts', count: posts?.length   || 0, color: 'var(--secondary)' },
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
  const [activeTab, setActiveTab]         = useState('ceo');
  const [results, setResults]             = useState({ ceo: null, posts: null, ideas: null });
  const [availableDates, setAvailableDates] = useState([]);
  const [selectedDate, setSelectedDate]   = useState(null);
  const [loading, setLoading]             = useState(true);
  const [triggering, setTriggering]       = useState(null); // 'ceo' | 'raindrop' | null
  const [triggerProgress, setTriggerProgress] = useState(0);
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
      const ceoRaw   = data.ceo?.posts   || data.ceo?.data   || null;
      const postsRaw = data.posts?.posts || data.posts?.data  || null;
      const ideasRaw = data.ideas?.ideas || data.ideas?.data  || null;

      setResults({ ceo: ceoRaw, posts: postsRaw, ideas: ideasRaw });
      if (data.availableDates) setAvailableDates(data.availableDates);
      if (data.selectedDate)   setSelectedDate(data.selectedDate);
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

  /* ── Trigger Workflow ──── */
  const triggerWorkflow = async (pipeline) => {
    setTriggering(pipeline);
    setTriggerProgress(0);
    setError(null);

    try {
      const res  = await fetch('/api/trigger', { method: 'POST' });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to trigger workflow');

      // Animate progress bar for 60 seconds
      let prog = 0;
      const iv = setInterval(() => {
        prog += 1;
        setTriggerProgress(prog);
        if (prog >= 100) {
          clearInterval(iv);
          setTriggering(null);
          fetchCache();
        }
      }, 600);
    } catch (err) {
      setError(err.message);
      setTriggering(null);
    }
  };

  const tabs = [
    { key: 'ceo',   label: 'CEO Posts',     icon: <TrendingUp size={15} />,  count: results.ceo?.length   },
    { key: 'posts', label: 'LinkedIn',       icon: <LinkedInIcon size={15} />,    count: results.posts?.length },
    { key: 'ideas', label: 'Ideas',          icon: <Lightbulb size={15} />,   count: results.ideas?.length },
  ];

  return (
    <div className="flex-col" style={{ minHeight: '100vh', paddingTop: 36, paddingBottom: 60, gap: 0 }}>

      {/* ── Trigger Overlay ── */}
      <AnimatePresence>
        {triggering && (
          <motion.div
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
            style={{
              position: 'fixed', inset: 0, zIndex: 100,
              background: 'rgba(4, 8, 20, 0.8)', backdropFilter: 'blur(12px)',
              display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24
            }}
          >
            <motion.div
              initial={{ scale: 0.88, y: 24 }} animate={{ scale: 1, y: 0 }}
              className="glass-card"
              style={{ maxWidth: 420, width: '100%', textAlign: 'center', padding: 40,
                       border: '1px solid rgba(124,92,252,0.35)' }}
            >
              <Loader2 className="spinner" size={44} color="var(--primary)" style={{ margin: '0 auto 20px' }} />
              <h2 className="text-gradient" style={{ marginBottom: 6 }}>
                Running {triggering === 'ceo' ? 'CEO' : 'Raindrop'} Pipeline
              </h2>
              <p className="text-muted" style={{ fontSize: '0.85rem', marginBottom: 24 }}>
                Fetching real-time data and generating content...
              </p>
              <div className="progress-bar-track">
                <motion.div
                  className="progress-bar-fill"
                  initial={{ width: '0%' }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 60, ease: 'linear' }}
                />
              </div>
              <p style={{ marginTop: 14, fontSize: '0.75rem', color: 'var(--muted)', opacity: 0.6 }}>
                This usually takes 30–60 seconds
              </p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

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
                    {d === availableDates[0] ? `Today (${d})` : d}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Force Run Pipeline */}
          <button
            className="btn-ghost"
            onClick={() => triggerWorkflow(activeTab === 'ceo' ? 'ceo' : 'raindrop')}
            disabled={!!triggering || loading}
            title={`Force run ${activeTab === 'ceo' ? 'CEO' : 'Raindrop'} pipeline`}
          >
            {triggering ? <Loader2 size={16} className="spinner" /> : <Sparkles size={16} />}
          </button>

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
          {tabs.map(t => (
            <button
              key={t.key}
              className={`tab-btn ${activeTab === t.key ? 'active' : ''}`}
              onClick={() => setActiveTab(t.key)}
            >
              {t.icon}
              {t.label}
              {t.count > 0 && (
                <span className="badge badge-count" style={{ padding: '1px 6px', fontSize: '0.65rem' }}>
                  {t.count}
                </span>
              )}
            </button>
          ))}
        </div>
        <StatsBar ceo={results.ceo} posts={results.posts} ideas={results.ideas} />
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
          background: activeTab === 'ideas' ? 'var(--accent-glow)' : 'var(--primary-glow)',
          filter: 'blur(100px)', opacity: 0.18, pointerEvents: 'none', zIndex: 0,
          transition: 'background 0.5s ease'
        }} />

        <AnimatePresence mode="wait">
          {/* CEO Tab */}
          {activeTab === 'ceo' && (
            <motion.div key="ceo"
              initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }}
              style={{ position: 'relative', zIndex: 1 }}
            >
              <div style={{ marginBottom: 24 }}>
                <h2 style={{ marginBottom: 4 }}>CEO LinkedIn Posts</h2>
                <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                  Institutional financial news posts for Shubham Goyal
                </p>
              </div>

              {loading ? (
                <div className="flex-col gap-4">
                  {[0,1,2].map(i => <SkeletonCard key={i} />)}
                </div>
              ) : results.ceo?.length > 0 ? (
                <div className="flex-col gap-8 mt-2">
                  {results.ceo.map((item, i) => (
                    <PostCard
                      key={i}
                      index={i + 1}
                      topic={item.topic || item.headline}
                      content={item.post}
                      delay={i * 0.06}
                    />
                  ))}
                </div>
              ) : (
                <EmptyState icon={<TrendingUp size={48} />} msg="No CEO posts logged for this date. Run the pipeline to generate." />
              )}
            </motion.div>
          )}

          {/* Posts Tab */}
          {activeTab === 'posts' && (
            <motion.div key="posts"
              initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }}
              style={{ position: 'relative', zIndex: 1 }}
            >
              <div style={{ marginBottom: 24 }}>
                <h2 style={{ marginBottom: 4 }}>LinkedIn Drafts</h2>
                <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                  Posts generated from Raindrop bookmarks and AU news
                </p>
              </div>

              {loading ? (
                <div className="flex-col gap-4">
                  {[0,1,2].map(i => <SkeletonCard key={i} />)}
                </div>
              ) : results.posts?.length > 0 ? (
                <div className="flex-col gap-8 mt-2">
                  {results.posts.map((post, i) => (
                    <PostCard key={i} index={i + 1} content={post} delay={i * 0.06} />
                  ))}
                </div>
              ) : (
                <EmptyState icon={<LinkedInIcon size={48} />} msg="No LinkedIn posts logged for this date. Run the Raindrop pipeline." />
              )}
            </motion.div>
          )}

          {/* Ideas Tab */}
          {activeTab === 'ideas' && (
            <motion.div key="ideas"
              initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: 12 }}
              style={{ position: 'relative', zIndex: 1 }}
            >
              <div style={{ marginBottom: 24 }}>
                <h2 style={{ marginBottom: 4 }}>Content Ideas</h2>
                <p className="text-muted" style={{ fontSize: '0.85rem' }}>
                  Grounded, data-backed ideas filtered for quality
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
                <EmptyState icon={<Lightbulb size={48} />} msg="No ideas logged for this date. Run the Raindrop pipeline." />
              )}
            </motion.div>
          )}
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
