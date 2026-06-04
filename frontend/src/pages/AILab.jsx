import { Link } from 'react-router-dom'

const MODULES = [
  {
    emoji: '🔍',
    title: 'Graph Search Algorithms',
    sub: 'BFS · DFS · UCS · A*',
    desc: 'Run any of the 4 search algorithms on the 41-node Charité hospital graph. See every node expansion, f/g/h scores at each step, and compare all 4 side-by-side with cost and efficiency metrics.',
    features: ['Step-by-step trace log', 'f(n)=g(n)+h(n) breakdown per node', 'Interactive vis-network graph', 'All 4 algorithms compared side by side', 'Export path as PDF report'],
    link: '/search',
    grad: 'linear-gradient(135deg,#0c4a6e,#0891b2)',
    accent: '#0891b2',
    light: '#ecfeff',
    border: '#a5f3fc',
  },
  {
    emoji: '🧩',
    title: 'Constraint Satisfaction',
    sub: 'Backtracking · AC-3 · MRV',
    desc: 'Validate hospital paths against real access constraints. 4 profiles (Staff, Emergency, Visitor, Patient) with different permissions. Find valid time windows for restricted zones.',
    features: ['4 access profiles with different permissions', 'AC-3 arc consistency enforcement', 'MRV heuristic for variable ordering', 'Full constraint violation trace', 'Time-window access finder per profile'],
    link: '/csp',
    grad: 'linear-gradient(135deg,#2e1065,#7c3aed)',
    accent: '#7c3aed',
    light: '#f5f3ff',
    border: '#ddd6fe',
  },
  {
    emoji: '♟️',
    title: 'Game AI — Minimax',
    sub: 'Alpha-Beta Pruning · Triage Routing',
    desc: 'Triage routing modelled as a two-player zero-sum game. MAX (ambulance) minimises travel time while MIN (congestion controller) raises corridor loads. Alpha-beta pruning cuts redundant branches.',
    features: ['Two-player adversarial search', 'Configurable search depth (1–5)', 'Alpha-beta pruning with branch count', 'Evaluation function: cost + urgency + congestion', 'Full minimax tree trace'],
    link: '/game',
    grad: 'linear-gradient(135deg,#431407,#b45309)',
    accent: '#b45309',
    light: '#fffbeb',
    border: '#fde68a',
  },
  {
    emoji: '🎲',
    title: 'Bayesian Networks & HMM',
    sub: 'Variable Elimination · Forward Algorithm',
    desc: 'Compute corridor occupancy probability given sensor readings and time of day. Track patient movement with the HMM forward algorithm. Adjust A* path costs by real-time congestion estimates.',
    features: ['Bayesian network: TimeOfDay → Occupancy ← DayType', 'Variable elimination for P(Occupancy | evidence)', 'HMM forward: P(state_t | obs_1:t)', 'Sensor-adjusted path cost (×1.0/1.4/2.0)', 'Full belief evolution trace per time step'],
    link: '/bayesian',
    grad: 'linear-gradient(135deg,#052e16,#15803d)',
    accent: '#15803d',
    light: '#f0fdf4',
    border: '#bbf7d0',
  },
  {
    emoji: '🌐',
    title: 'Multilingual NLP Pipeline',
    sub: 'Telugu · Hindi · English · Ethics',
    desc: 'Parse hospital navigation queries in three languages including Roman transliteration. Detect urgency level, extract destination intent, and see full explainability traces for every decision.',
    features: ['Language detection: Telugu / Hindi / English', 'Roman transliteration (ICU le jao)', 'Urgency: CRITICAL / HIGH / NORMAL', 'Full pipeline trace per stage', 'Ethics panel: bias audit + accessibility analysis'],
    link: '/nlp',
    grad: 'linear-gradient(135deg,#500724,#be185d)',
    accent: '#be185d',
    light: '#fdf2f8',
    border: '#fbcfe8',
  },
]

export default function AILab() {
  return (
    <div>
      {/* Header */}
      <div style={{ marginBottom: 32 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
          <Link to="/" style={{ fontSize: '.8rem', color: '#6b7280', textDecoration: 'none',
            display: 'flex', alignItems: 'center', gap: 4 }}>
            ← Home
          </Link>
        </div>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, color: '#111827',
          letterSpacing: '-.5px', marginBottom: 8 }}>
          🧠 AI Algorithm Lab
        </h1>
        <p style={{ fontSize: '.95rem', color: '#374151', maxWidth: 560, lineHeight: 1.65 }}>
          Explore every AI technique powering the Charité Navigator. Full explainability,
          step traces, and real hospital data on every module.
        </p>
      </div>

      {/* Module cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
        {MODULES.map(({ emoji, title, sub, desc, features, link, grad, accent, light, border }) => (
          <Link key={link} to={link} style={{ textDecoration: 'none' }}>
            <div style={{
              display: 'grid',
              gridTemplateColumns: '280px 1fr',
              background: '#fffdf9',
              border: '1px solid #e8d9c4',
              borderRadius: 16,
              overflow: 'hidden',
              transition: 'transform .18s, box-shadow .18s',
              cursor: 'pointer',
              boxShadow: '0 1px 4px rgba(92,74,48,.08)',
            }}
              onMouseEnter={e => { e.currentTarget.style.transform='translateY(-3px)'; e.currentTarget.style.boxShadow='0 12px 32px rgba(0,0,0,.12)' }}
              onMouseLeave={e => { e.currentTarget.style.transform=''; e.currentTarget.style.boxShadow='0 1px 4px rgba(92,74,48,.08)' }}
            >
              {/* Left accent panel */}
              <div style={{ background: grad, padding: '28px 24px', display: 'flex',
                flexDirection: 'column', justifyContent: 'space-between' }}>
                <div>
                  <div style={{ fontSize: '2.4rem', marginBottom: 14 }}>{emoji}</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 800, color: '#fff',
                    lineHeight: 1.2, marginBottom: 6 }}>{title}</div>
                  <div style={{ fontSize: '.75rem', color: 'rgba(255,255,255,.75)',
                    fontWeight: 600, letterSpacing: '.3px' }}>{sub}</div>
                </div>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: 6,
                  background: 'rgba(255,255,255,.15)', border: '1px solid rgba(255,255,255,.3)',
                  borderRadius: 8, padding: '8px 14px', fontSize: '.78rem',
                  fontWeight: 700, color: '#fff', marginTop: 24, width: 'fit-content',
                }}>
                  Open Module →
                </div>
              </div>

              {/* Right content */}
              <div style={{ padding: '24px 28px' }}>
                <p style={{ fontSize: '.84rem', color: '#374151', lineHeight: 1.65,
                  marginBottom: 18 }}>{desc}</p>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 7 }}>
                  {features.map(f => (
                    <div key={f} style={{ display: 'flex', alignItems: 'flex-start', gap: 8,
                      fontSize: '.8rem', color: '#111827' }}>
                      <span style={{
                        width: 18, height: 18, borderRadius: 4, flexShrink: 0,
                        background: light, border: `1px solid ${border}`,
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '.55rem', fontWeight: 800, color: accent, marginTop: 1,
                      }}>✓</span>
                      {f}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Footer note */}
      <div style={{ textAlign: 'center', marginTop: 36, padding: '16px',
        color: '#9ca3af', fontSize: '.75rem' }}>
        All modules run on the same 41-node Charité Campus Mitte graph &nbsp;·&nbsp;
        Python FastAPI backend &nbsp;·&nbsp; Zero external APIs required for core functionality
      </div>
    </div>
  )
}
