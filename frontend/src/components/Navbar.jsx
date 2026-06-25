import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useAI, HOSPITALS } from '../context/AIContext'

const LINKS = [
  { to: '/',         label: 'Home',     emoji: '🏥' },
  { to: '/navigate', label: 'Navigate', emoji: '🎙️' },
  { to: '/lab',      label: 'AI Lab',   emoji: '🧠' },
  { to: '/search',   label: 'Search',   emoji: '🔍' },
  { to: '/csp',      label: 'CSP',      emoji: '🧩' },
  { to: '/game',     label: 'Game AI',  emoji: '♟️' },
  { to: '/bayesian', label: 'Bayesian', emoji: '🎲' },
  { to: '/ideas',    label: "Ideas Lab", emoji: '💡' },
  { to: '/nlp',      label: 'NLP',      emoji: '🌐' },
]

export default function Navbar() {
  const {
    enabled, setEnabled, provider, setProvider,
    apiKey, setApiKey, model, setModel, MODELS, isReady,
    hospital, setHospital, hospitalInfo,
  } = useAI()
  const [showConfig,   setShowConfig]   = useState(false)
  const [showHospital, setShowHospital] = useState(false)

  return (
    <>
      <nav className="navbar">
        {/* Hospital selector pill */}
        <button
          onClick={() => { setShowHospital(v => !v); setShowConfig(false) }}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '5px 12px', borderRadius: 8,
            border: '1.5px solid',
            cursor: 'pointer', fontFamily: 'inherit',
            fontSize: '.78rem', fontWeight: 800,
            background: hospital === 'aiims' ? '#fff0f0' : '#f0f8ff',
            color: '#111827',
            borderColor: hospital === 'aiims' ? '#f87171' : '#60a5fa',
            transition: 'all .15s',
          }}
          title="Switch Hospital"
        >
          <span style={{ fontSize: '1rem' }}>{hospitalInfo.flag}</span>
          <span style={{ maxWidth: 120, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {hospitalInfo.short}
          </span>
          <span style={{ fontSize: '.65rem', opacity: .6 }}>▼</span>
        </button>

        <div className="nav-links">
          {LINKS.map(({ to, label, emoji }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
            >
              <span>{emoji}</span>
              <span>{label}</span>
            </NavLink>
          ))}
        </div>

        {/* AI toggle button */}
        <button
          onClick={() => { setShowConfig(v => !v); setShowHospital(false) }}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '5px 12px', borderRadius: 8, border: '1px solid',
            cursor: 'pointer', fontFamily: 'inherit',
            fontSize: '.78rem', fontWeight: 700,
            background: isReady ? '#fef3c7' : enabled ? '#fff8f0' : '#f9fafb',
            color:      isReady ? '#92400e' : '#374151',
            borderColor: isReady ? '#fcd34d' : '#e8d9c4',
            transition: 'all .15s',
          }}
          title="Configure AI (Claude/Gemini)"
        >
          🤖
          <span>{isReady ? 'AI ON' : 'AI OFF'}</span>
          {isReady && (
            <span style={{
              width: 7, height: 7, borderRadius: '50%',
              background: '#22c55e',
              animation: 'blink 1.8s ease-in-out infinite',
            }} />
          )}
        </button>
      </nav>

      {/* ── Hospital Selector Popup ──────────────────────────────────────── */}
      {showHospital && (
        <>
          <div onClick={() => setShowHospital(false)} style={{
            position:'fixed', inset:0, zIndex:199, background:'rgba(0,0,0,.15)',
          }} />
          <div style={{
            position:'fixed', top:62, left:16, zIndex:200,
            background:'#fffdf9', border:'1px solid #e8d9c4',
            borderRadius:14, padding:'18px 20px', width:320,
            boxShadow:'0 8px 32px rgba(92,74,48,.18)',
          }}>
            <div style={{ fontWeight:800, fontSize:'.92rem', color:'#111827', marginBottom:12 }}>
              🏥 Select Hospital
            </div>
            <div style={{ fontSize:'.73rem', color:'#6b7280', marginBottom:14, lineHeight:1.5 }}>
              All AI modules (Search, CSP, Game, Bayesian, NLP) will use the selected hospital's graph.
            </div>
            {HOSPITALS.map(h => (
              <button key={h.id} onClick={() => { setHospital(h.id); setShowHospital(false) }}
                style={{
                  display:'flex', alignItems:'center', gap:10,
                  width:'100%', padding:'12px 14px', marginBottom:8,
                  borderRadius:10, border:'1.5px solid',
                  cursor:'pointer', fontFamily:'inherit', textAlign:'left',
                  background: hospital === h.id ? (h.id === 'aiims' ? '#fff0f0' : '#f0f8ff') : '#fff',
                  borderColor: hospital === h.id ? (h.id === 'aiims' ? '#f87171' : '#60a5fa') : '#e5e7eb',
                  boxShadow: hospital === h.id ? '0 2px 8px rgba(0,0,0,.08)' : 'none',
                  transition: 'all .15s',
                }}
              >
                <span style={{ fontSize:'1.6rem' }}>{h.flag}</span>
                <div>
                  <div style={{ fontWeight:800, fontSize:'.85rem', color:'#111827' }}>{h.name}</div>
                  <div style={{ fontSize:'.7rem', color:'#6b7280', marginTop:1 }}>{h.city || ''}</div>
                </div>
                {hospital === h.id && (
                  <span style={{ marginLeft:'auto', fontSize:'.9rem', color:'#22c55e' }}>✓</span>
                )}
              </button>
            ))}
          </div>
        </>
      )}

      {/* ── AI Config Popup ─────────────────────────────────────────────── */}
      {showConfig && (
        <>
          <div onClick={() => setShowConfig(false)} style={{
            position:'fixed', inset:0, zIndex:199, background:'rgba(0,0,0,.15)',
          }} />
          <div style={{
            position:'fixed', top:62, right:16, zIndex:200,
            background:'#fffdf9', border:'1px solid #e8d9c4',
            borderRadius:14, padding:'20px 22px', width:360,
            boxShadow:'0 8px 32px rgba(92,74,48,.18)',
          }}>
            <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:14 }}>
              <div style={{ fontWeight:800, fontSize:'.95rem', color:'#111827' }}>
                🤖 AI Configuration
              </div>
              <button onClick={() => setShowConfig(false)}
                style={{ background:'none', border:'none', cursor:'pointer', fontSize:'1rem', color:'#6b7280' }}>✕</button>
            </div>

            <div style={{ fontSize:'.75rem', color:'#6b7280', marginBottom:14, lineHeight:1.5 }}>
              When ON, Claude or Gemini will explain every result across all pages.
            </div>

            {/* Provider tabs */}
            <div style={{ display:'flex', gap:6, marginBottom:12 }}>
              {[['claude','⚡ Claude'],['gemini','✨ Gemini']].map(([v,l]) => (
                <button key={v} onClick={() => { setProvider(v); setModel(MODELS[v][0].v) }}
                  style={{
                    flex:1, padding:'7px 0', borderRadius:8, border:'1px solid',
                    cursor:'pointer', fontFamily:'inherit', fontWeight:700, fontSize:'.8rem',
                    background: provider===v ? '#b45309' : '#fff8f0',
                    color:      provider===v ? '#fff'   : '#5c4a30',
                    borderColor: provider===v ? '#b45309' : '#e8d9c4',
                  }}>{l}</button>
              ))}
            </div>

            {/* API Key */}
            <div style={{ marginBottom:10 }}>
              <label style={{ fontSize:'.72rem', fontWeight:700, color:'#374151', display:'block', marginBottom:4 }}>
                {provider === 'claude' ? 'Anthropic API Key' : 'Google AI API Key'}
              </label>
              <input
                type="password"
                className="form-control"
                placeholder={provider === 'claude' ? 'sk-ant-api03-…' : 'AIzaSy…'}
                value={apiKey}
                onChange={e => setApiKey(e.target.value)}
              />
            </div>

            {/* Model */}
            <div style={{ marginBottom:14 }}>
              <label style={{ fontSize:'.72rem', fontWeight:700, color:'#374151', display:'block', marginBottom:4 }}>Model</label>
              <select className="form-control" value={model} onChange={e => setModel(e.target.value)}>
                {(MODELS[provider] || []).map(m => (
                  <option key={m.v} value={m.v}>{m.l}</option>
                ))}
              </select>
            </div>

            {/* Toggle */}
            <div style={{
              display:'flex', alignItems:'center', justifyContent:'space-between',
              background: isReady ? '#f0fdf4' : '#fff8f0',
              border: `1px solid ${isReady ? '#bbf7d0' : '#e8d9c4'}`,
              borderRadius:10, padding:'10px 14px',
            }}>
              <div>
                <div style={{ fontWeight:700, fontSize:'.85rem', color:'#111827' }}>
                  {isReady ? '✅ AI Active' : enabled && !apiKey ? '⚠️ Need API key' : '🤖 Enable AI'}
                </div>
                <div style={{ fontSize:'.72rem', color:'#6b7280', marginTop:2 }}>
                  {isReady
                    ? `${provider === 'claude' ? 'Claude' : 'Gemini'} will explain all results`
                    : 'All pages use rule-based algorithms only'}
                </div>
              </div>
              <label className="toggle" style={{ flexShrink:0 }}>
                <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} />
                <span className="toggle-slider" />
              </label>
            </div>

            {isReady && (
              <div style={{ marginTop:10, fontSize:'.72rem', color:'#15803d', textAlign:'center' }}>
                🟢 Active on: Navigate · Search · CSP · Game · Bayesian · NLP
              </div>
            )}
          </div>
        </>
      )}

      <style>{`@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}`}</style>
    </>
  )
}
