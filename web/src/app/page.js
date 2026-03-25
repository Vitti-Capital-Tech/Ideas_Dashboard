'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Settings, Droplet, Newspaper, Sparkles, CheckCircle, AlertCircle, Loader2, Sun, Moon, Clock, Copy, Linkedin } from 'lucide-react';

const PostCard = ({ title, content, isIdea }) => {
  const [copied, setCopied] = useState(false);
  
  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handlePost = () => {
    // Topmate uses the hidden text parameter to pre-fill the post box directly!
    const linkedInUrl = `https://www.linkedin.com/feed/?shareActive=true&text=${encodeURIComponent(content)}`;
    window.open(linkedInUrl, '_blank');
  };

  return (
    <motion.div 
      whileHover={{ y: -4 }}
      className="glass-card mt-4 transition-all" 
      style={{ 
        background: 'var(--surface)', 
        borderLeft: isIdea ? '4px solid var(--primary)' : '4px solid var(--secondary)',
        boxShadow: '0 4px 6px rgba(0,0,0,0.05)'
      }}
    >
      {title && (
        <h3 className="text-gradient" style={{ borderBottom: '1px solid var(--surface-border)', paddingBottom: '16px', fontSize: '1.25rem' }}>
          {title}
        </h3>
      )}
      <div className={title ? "mt-6" : ""} style={{ color: 'var(--foreground)', opacity: 0.9 }}>
        <pre style={{ whiteSpace: 'pre-wrap', fontType: 'inherit', fontFamily: 'inherit', fontSize: '0.95rem', lineHeight: '1.6' }}>
          {content}
        </pre>
      </div>
      <div className="flex gap-4 mt-6 pt-4" style={{ borderTop: '1px solid var(--surface-border)' }}>
        <button onClick={handleCopy} className="btn-secondary" style={{ flex: 1, justifyContent: 'center' }}>
          {copied ? <CheckCircle size={16} color="var(--success)" /> : <Copy size={16} />}
          {copied ? 'Copied!' : 'Copy Text'}
        </button>
        <button onClick={handlePost} className="btn-primary" style={{ flex: 1, justifyContent: 'center' }}>
          <Linkedin size={16} />
          Post to LinkedIn
        </button>
      </div>
    </motion.div>
  );
};


export default function Home() {
  const [activeTab, setActiveTab] = useState('raindrop');
  const [loading, setLoading] = useState(false);
  const [raindropResults, setRaindropResults] = useState(null);
  const [ceoResults, setCeoResults] = useState(null);
  const [error, setError] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [lastRuns, setLastRuns] = useState({ raindrop: null, ceo: null });

  // On mount, fetch cache and set theme
  useEffect(() => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
      setTheme('light');
      document.body.classList.add('light-theme');
    }

    const fetchCache = async () => {
      try {
        const res = await fetch('/api/cache');
        const data = await res.json();
        if (data.raindrop?.data) {
          setRaindropResults(data.raindrop.data);
          setLastRuns(prev => ({ ...prev, raindrop: data.raindrop.timestamp }));
        }
        if (data.ceo?.data) {
          setCeoResults(data.ceo.data);
          setLastRuns(prev => ({ ...prev, ceo: data.ceo.timestamp }));
        }
      } catch (err) {
        console.error("Failed to load cache:", err);
      }
    };
    fetchCache();
  }, []);

  const toggleTheme = () => {
    const newTheme = theme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
    localStorage.setItem('theme', newTheme);
    if (newTheme === 'light') {
      document.body.classList.add('light-theme');
    } else {
      document.body.classList.remove('light-theme');
    }
  };

  const formatTimeAgo = (timestamp) => {
    if (!timestamp) return "Never run";
    const diffMins = Math.floor((Date.now() - timestamp) / 60000);
    if (diffMins < 60) return `${diffMins} mins ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours} hours ago`;
    return `${Math.floor(diffHours / 24)} days ago`;
  };

  const triggerWorkflow = async () => {
    setLoading(true); setError(null);
    try {
      const res = await fetch('/api/trigger', { method: "POST" });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Failed to trigger workflow');
      alert("GitHub Action Triggered Successfully! ✨\n\nGitHub is now spinning up a container to run the Python scripts.\nPlease allow 1-2 minutes for completion. Refetching the page will show the new logs once pushed by GitHub!");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-col min-h-screen py-8 gap-8">
      {/* Header */}
      <header className="flex justify-between items-center mb-8 animate-fade-in">
        <div>
          <h1 className="text-gradient hover:scale-105 transition-transform" style={{ cursor: 'pointer' }}>Content Generator</h1>
          <p style={{ color: 'var(--primary)', fontWeight: '500' }}>Vitti Capital AI Dashboard</p>
        </div>
        <div className="flex gap-4">
          <button className="btn-secondary" onClick={toggleTheme} aria-label="Toggle Theme">
            {theme === 'dark' ? <Sun size={18} /> : <Moon size={18} />}
          </button>
        </div>
      </header>

      {/* Error Toast */}
      <AnimatePresence>
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            className="flex items-center gap-2 p-4 mb-6"
            style={{ backgroundColor: 'rgba(239, 68, 68, 0.1)', color: 'var(--error)', border: '1px solid rgba(239, 68, 68, 0.3)', borderRadius: '12px' }}
          >
            <AlertCircle size={20} />
            <p>{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Tabs */}
      <div className="flex gap-4 mb-4 animate-fade-in" style={{ animationDelay: '0.1s' }}>
        <button 
          className={`btn-secondary ${activeTab === 'raindrop' ? 'btn-primary' : ''}`}
          onClick={() => setActiveTab('raindrop')}
          disabled={loading}
        >
          <Droplet size={18} />
          Raindrop Ideas
        </button>
        <button 
          className={`btn-secondary ${activeTab === 'ceo' ? 'btn-primary' : ''}`}
          onClick={() => setActiveTab('ceo')}
          disabled={loading}
        >
          <Newspaper size={18} />
          CEO Content
        </button>
      </div>

      {/* Main Content Area */}
      <div className="glass-card animate-fade-in" style={{ minHeight: '60vh', animationDelay: '0.2s', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: '-10%', right: '-5%', width: '300px', height: '300px', background: 'var(--primary-glow)', filter: 'blur(100px)', zIndex: 0, opacity: 0.5, pointerEvents: 'none' }} />
        
        <AnimatePresence mode="wait">
          {activeTab === 'raindrop' ? (
            <motion.div 
              key="raindrop"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="flex-col gap-6"
              style={{ position: 'relative', zIndex: 1 }}
            >
              <div className="flex justify-between items-start flex-wrap gap-4">
                <div>
                  <h2>Raindrop &rarr; LinkedIn Ideas</h2>
                  <p style={{ color: 'var(--foreground)', opacity: 0.7, marginBottom: '8px' }}>
                    Fetch the last 5 days of bookmarks and generate creative ideas and drafts using Perplexity.
                  </p>
                  <div className="flex items-center gap-2" style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>
                    <Clock size={14} />
                    <span>Last Run: {formatTimeAgo(lastRuns.raindrop)}</span>
                  </div>
                </div>
                <button className="btn-primary" onClick={triggerWorkflow} disabled={loading} style={{ transform: loading ? 'scale(0.98)' : 'scale(1)' }}>
                  {loading ? <Loader2 className="spinner" size={18} /> : <Sparkles size={18} />}
                  {loading ? 'Triggering...' : 'Trigger Workflow on GitHub'}
                </button>
              </div>
              
              {raindropResults ? (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-8 flex-col gap-6">
                  {raindropResults.ideas?.length > 0 && (
                    <div className="mt-4">
                      <h3 className="text-gradient mb-4 font-bold" style={{ fontSize: '1.4rem' }}>Extracted Concepts & Ideas</h3>
                      <div className="grid gap-6">
                        {raindropResults.ideas.map((idea, idx) => (
                          <PostCard key={`idea-${idx}`} content={idea} isIdea={true} />
                        ))}
                      </div>
                    </div>
                  )}

                  {raindropResults.posts?.length > 0 && (
                    <div className="mt-12">
                      <h3 className="text-gradient mb-4 font-bold" style={{ fontSize: '1.4rem' }}>LinkedIn Drafts</h3>
                      <div className="grid gap-6">
                        {raindropResults.posts.map((post, idx) => (
                          <PostCard key={`post-${idx}`} content={post} isIdea={false} />
                        ))}
                      </div>
                    </div>
                  )}
                </motion.div>
              ) : (
                <div className="mt-8 p-12" style={{ border: '2px dashed var(--surface-border)', borderRadius: '16px', textAlign: 'center', background: 'rgba(0,0,0,0.1)' }}>
                  <Sparkles size={32} style={{ margin: '0 auto 16px', color: 'var(--primary-glow)' }} />
                  <p style={{ color: 'var(--foreground)', opacity: 0.6, fontSize: '1.1rem' }}>Click generate to create fresh content from your bookmarks.</p>
                </div>
              )}
            </motion.div>
          ) : (
            <motion.div 
              key="ceo"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              transition={{ type: 'spring', stiffness: 300, damping: 30 }}
              className="flex-col gap-6"
              style={{ position: 'relative', zIndex: 1 }}
            >
              <div className="flex justify-between items-start flex-wrap gap-4">
                <div>
                  <h2>Financial News &rarr; CEO Posts</h2>
                  <p style={{ color: 'var(--foreground)', opacity: 0.7, marginBottom: '8px' }}>
                    Discover trending Australian financial news and draft institutional-grade posts.
                  </p>
                  <div className="flex items-center gap-2" style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>
                    <Clock size={14} />
                    <span>Last Run: {formatTimeAgo(lastRuns.ceo)}</span>
                  </div>
                </div>
                <button className="btn-primary" onClick={triggerWorkflow} disabled={loading} style={{ transform: loading ? 'scale(0.98)' : 'scale(1)' }}>
                  {loading ? <Loader2 className="spinner" size={18} /> : <Sparkles size={18} />}
                  {loading ? 'Triggering...' : 'Trigger Workflow on GitHub'}
                </button>
              </div>

               {ceoResults ? (
                <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-8 flex-col gap-6">
                  {ceoResults.posts?.map((item, idx) => (
                     <PostCard key={`ceo-${idx}`} title={item.topic} content={item.post} isIdea={false} />
                  ))}
                </motion.div>
              ) : (
                <div className="mt-8 p-12" style={{ border: '2px dashed var(--surface-border)', borderRadius: '16px', textAlign: 'center', background: 'rgba(0,0,0,0.1)' }}>
                  <Newspaper size={32} style={{ margin: '0 auto 16px', color: 'var(--primary-glow)' }} />
                  <p style={{ color: 'var(--foreground)', opacity: 0.6, fontSize: '1.1rem' }}>Click generate to analyze today's latest financial news.</p>
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
