import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getHealth } from '../api'
import { useAI, HOSPITALS } from '../context/AIContext'
import HospitalMapView from '../components/HospitalMapView'

export default function Home() {
  const [health, setHealth] = useState(null)
  const { hospital, setHospital, hospitalInfo } = useAI()

  useEffect(() => { getHealth().then(r => setHealth(r.data)).catch(() => {}) }, [])

  const isAIIMS   = hospital === 'aiims'
  const nodeCount = health?.hospitals?.[hospital]?.nodes ?? (isAIIMS ? 55 : 41)

  return (
    <div style={{ minHeight: '90vh', display: 'flex', flexDirection: 'column' }}>

      {/* ── Hero ── */}
      <div style={{ textAlign: 'center', padding: '52px 24px 32px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          background: '#fef3c7', border: '1px solid #fcd34d',
          borderRadius: 20, padding: '5px 16px',
          fontSize: '.75rem', fontWeight: 700, color: '#92400e',
          marginBottom: 24, letterSpacing: '.3px',
        }}>
          <span style={{ width:7, height:7, borderRadius:'50%', background:'#ef4444',
            boxShadow:'0 0 8px #ef4444', display:'inline-block',
            animation:'blink 1.8s ease-in-out infinite' }} />
          LIVE &nbsp;·&nbsp; AI Research Preview &nbsp;·&nbsp; CO1–CO6
        </div>

        <h1 style={{
          fontSize: 'clamp(2rem, 5vw, 3.2rem)',
          fontWeight: 900, color: '#111827',
          letterSpacing: '-1.5px', lineHeight: 1.1,
          marginBottom: 12,
        }}>
          Hospital<br />
          <span style={{
            background: isAIIMS
              ? 'linear-gradient(135deg, #dc2626, #f97316)'
              : 'linear-gradient(135deg, #b45309, #0891b2)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
          }}>AI Navigator</span>
        </h1>

        {/* Hospital switcher + 3D view side by side */}
        <div style={{
          display:'flex', gap:20, justifyContent:'center',
          alignItems:'flex-start', marginBottom:28, flexWrap:'wrap',
        }}>
          {/* Left: switcher + description */}
          <div style={{ display:'flex', flexDirection:'column', gap:12, maxWidth:340, textAlign:'left' }}>
            <div style={{
              display:'inline-flex', gap:0,
              background:'#f9fafb', border:'1px solid #e5e7eb',
              borderRadius:12, overflow:'hidden', alignSelf:'flex-start',
            }}>
              {HOSPITALS.map(h => (
                <button key={h.id} onClick={() => setHospital(h.id)}
                  style={{
                    padding:'9px 20px', cursor:'pointer',
                    fontFamily:'inherit', fontWeight:700, fontSize:'.8rem',
                    border:'none', transition:'all .15s',
                    background: hospital === h.id
                      ? (h.id === 'aiims' ? '#dc2626' : '#1d4ed8')
                      : 'transparent',
                    color: hospital === h.id ? '#fff' : '#6b7280',
                  }}>
                  {h.flag} {h.name}
                </button>
              ))}
            </div>

            <p style={{ fontSize:'.92rem', color:'#374151', lineHeight:1.7, margin:0 }}>
              {isAIIMS
                ? 'Built on the real AIIMS Mangalagiri hospital model — verified from official sources. Graph search, constraints, game theory, probabilistic reasoning & multilingual NLP — all live.'
                : 'Built on the real Charité Campus Mitte hospital model. Graph search, constraints, game theory, probabilistic reasoning & multilingual NLP — all live.'
              }
            </p>
          </div>

          {/* Right: real satellite map */}
          <div style={{ width: 340, flexShrink: 0 }}>
            <HospitalMapView hospital={hospital} />
          </div>
        </div>

        {/* Stats strip */}
        <div style={{
          display:'inline-flex', gap:0,
          background:'#fffdf9', border:'1px solid #e8d9c4',
          borderRadius:12, overflow:'hidden', marginBottom:48,
          boxShadow:'0 2px 8px rgba(92,74,48,.08)',
        }}>
          {[
            { val: nodeCount,                lbl: 'Nodes' },
            { val: isAIIMS ? 70 : 52,        lbl: 'Edges' },
            { val: 3,                         lbl: 'Languages' },
            { val: 6,                         lbl: 'AI Modules' },
          ].map(({ val, lbl }, i) => (
            <div key={lbl} style={{
              padding:'12px 24px', textAlign:'center',
              borderRight: i < 3 ? '1px solid #e8d9c4' : 'none',
            }}>
              <div style={{ fontSize:'1.4rem', fontWeight:900, color: isAIIMS ? '#dc2626' : '#b45309', lineHeight:1 }}>{val}</div>
              <div style={{ fontSize:'.65rem', fontWeight:700, color:'#9ca3af',
                textTransform:'uppercase', letterSpacing:'.5px', marginTop:3 }}>{lbl}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Two giant cards ── */}
      <div style={{
        display:'grid', gridTemplateColumns:'1fr 1fr',
        gap:20, flex:1, padding:'0 0 48px',
      }}>
        {/* Navigate card */}
        <Link to="/navigate" style={{ textDecoration:'none' }}>
          <div className="landing-card landing-card-left">
            <div className="landing-card-bg" style={{
              background: isAIIMS
                ? 'linear-gradient(135deg, #991b1b 0%, #dc2626 50%, #f97316 100%)'
                : 'linear-gradient(135deg, #92400e 0%, #b45309 50%, #d97706 100%)',
            }} />
            <div className="landing-card-body">
              <div className="landing-card-icon">🎙️</div>
              <div className="landing-card-tag">Smart Navigation</div>
              <h2 className="landing-card-title">Talk to the Hospital</h2>
              <p className="landing-card-desc">
                Speak or type in Telugu, Hindi, or English. The AI understands your intent,
                detects urgency, and routes you to the right ward — instantly.
              </p>
              <div className="landing-card-features">
                {[
                  '🎤 Voice input — Web Speech API',
                  '🌐 Multilingual NLP (TE · HI · EN)',
                  '🚨 Urgency-aware routing',
                  '🗺️ Live interactive hospital graph',
                  '⚠️ CSP access constraint alerts',
                ].map(f => <div key={f} className="landing-feature">{f}</div>)}
              </div>
              <div className="landing-card-cta">Start Navigating →</div>
            </div>
          </div>
        </Link>

        {/* AI Lab card */}
        <Link to="/lab" style={{ textDecoration:'none' }}>
          <div className="landing-card landing-card-right">
            <div className="landing-card-bg" style={{
              background:'linear-gradient(135deg, #0c4a6e 0%, #0891b2 50%, #06b6d4 100%)',
            }} />
            <div className="landing-card-body">
              <div className="landing-card-icon">🧠</div>
              <div className="landing-card-tag">AI Algorithm Lab</div>
              <h2 className="landing-card-title">Explore the AI</h2>
              <p className="landing-card-desc">
                Dive deep into every algorithm powering this system.
                Run searches, solve constraints, play adversarial games,
                and reason under uncertainty — all with full explainability.
              </p>
              <div className="landing-card-features">
                {[
                  '🔍 BFS · DFS · UCS · A* with step traces',
                  '🧩 CSP backtracking + AC-3 arc consistency',
                  '♟️ Minimax + Alpha-Beta pruning',
                  '🎲 Bayesian networks + HMM tracking',
                  '🌐 NLP pipeline + ethics analysis',
                ].map(f => <div key={f} className="landing-feature">{f}</div>)}
              </div>
              <div className="landing-card-cta">Open AI Lab →</div>
            </div>
          </div>
        </Link>
      </div>

      {/* ── Footer ── */}
      <div style={{
        textAlign:'center', padding:'16px 0 8px',
        color:'#9ca3af', fontSize:'.73rem',
        borderTop:'1px solid #e8d9c4',
      }}>
        25F2005507 · CFAI Project &nbsp;·&nbsp;
        {hospitalInfo.flag} {hospitalInfo.name} &nbsp;·&nbsp;
        <a href="https://github.com/Sai0Nikhil/CFAI_Project"
          style={{ color:'#b45309', textDecoration:'none' }}>
          GitHub ↗
        </a>
      </div>

      <style>{`
        @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.3} }
        .landing-card {
          position:relative; border-radius:20px; overflow:hidden;
          height:100%; min-height:480px;
          transition:transform .2s, box-shadow .2s;
          cursor:pointer; display:flex; flex-direction:column;
        }
        .landing-card:hover { transform:translateY(-6px); box-shadow:0 24px 56px rgba(0,0,0,.18); }
        .landing-card-bg { position:absolute; inset:0; z-index:0; }
        .landing-card-body {
          position:relative; z-index:1; padding:36px 32px 32px;
          display:flex; flex-direction:column; height:100%; color:#fff;
        }
        .landing-card-icon { font-size:2.8rem; margin-bottom:14px; filter:drop-shadow(0 2px 8px rgba(0,0,0,.25)); }
        .landing-card-tag {
          display:inline-block; background:rgba(255,255,255,.18);
          border:1px solid rgba(255,255,255,.3); border-radius:20px;
          padding:4px 14px; font-size:.72rem; font-weight:700;
          letter-spacing:.5px; text-transform:uppercase; margin-bottom:14px; width:fit-content;
        }
        .landing-card-title { font-size:1.9rem; font-weight:900; letter-spacing:-.5px; line-height:1.1; margin-bottom:14px; color:#fff; }
        .landing-card-desc { font-size:.88rem; line-height:1.65; opacity:.88; margin-bottom:24px; color:#fff; }
        .landing-card-features { display:flex; flex-direction:column; gap:8px; flex:1; margin-bottom:28px; }
        .landing-feature { font-size:.82rem; color:rgba(255,255,255,.9); display:flex; align-items:center; gap:8px; }
        .landing-feature::before { content:''; width:4px; height:4px; border-radius:50%; background:rgba(255,255,255,.6); flex-shrink:0; }
        .landing-card-cta {
          display:inline-flex; align-items:center; gap:6px;
          background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.35);
          border-radius:10px; padding:11px 22px; font-size:.9rem; font-weight:700;
          color:#fff; transition:background .15s; width:fit-content; backdrop-filter:blur(4px);
        }
        .landing-card:hover .landing-card-cta { background:rgba(255,255,255,.25); }
        @media (max-width:700px) { .landing-card { min-height:360px; } .landing-card-title { font-size:1.5rem; } }
      `}</style>
    </div>
  )
}
