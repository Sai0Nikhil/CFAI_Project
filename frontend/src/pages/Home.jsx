import { Link } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { getHealth } from '../api'

const MODULES = [
  { co:'CO1', cls:'co1', emoji:'🤖', title:'Agent Model & Knowledge',
    desc:'PEAS model, environment types, Python data structures, trace logging & Big-O complexity analysis.',
    chips:['PEAS','Graphs/Trees','Big-O','Dataclasses'], link:'/navigate' },
  { co:'CO2', cls:'co2', emoji:'🔍', title:'Graph Search Algorithms',
    desc:'BFS · DFS · UCS · A* with f/g/h step traces, admissible heuristic design, and profiling.',
    chips:['BFS','DFS','UCS','A*','Admissibility'], link:'/search' },
  { co:'CO3', cls:'co3', emoji:'🧩', title:'Constraint Satisfaction',
    desc:'Backtracking, forward checking, AC-3 arc consistency, MRV & LCV heuristics for access control.',
    chips:['Backtracking','AC-3','MRV','4 Profiles'], link:'/csp' },
  { co:'CO4', cls:'co4', emoji:'♟️', title:'Game AI — Minimax',
    desc:'Triage routing as two-player zero-sum game. MAX minimises travel; MIN raises congestion. Alpha-beta.',
    chips:['Minimax','Alpha-Beta','Eval Fn','Bounded Rationality'], link:'/game' },
  { co:'CO5', cls:'co5', emoji:'🎲', title:'Bayesian Networks & HMM',
    desc:'Corridor occupancy via variable elimination. HMM forward algorithm for patient movement tracking.',
    chips:['Bayes Net','Variable Elim.','HMM','Sensor Fusion'], link:'/bayesian' },
  { co:'CO6', cls:'co6', emoji:'🌐', title:'Multilingual NLP & Ethics',
    desc:'Telugu · Hindi · English intent parsing, urgency detection, explainability traces & AI bias analysis.',
    chips:['తెలుగు','हिंदी','English','Urgency 🚨','Ethics'], link:'/nlp' },
]

export default function Home() {
  const [health, setHealth] = useState(null)

  useEffect(() => {
    getHealth().then(r => setHealth(r.data)).catch(() => {})
  }, [])

  return (
    <div>
      {/* Hero */}
      <div className="hero">
        <div className="hero-badge">🔴 LIVE · AI Research Preview · CO1–CO6</div>
        <div className="hero-title">Charité Hospital AI Navigator</div>
        <div className="hero-sub">
          A full-stack AI system combining Graph Search, CSP, Game Theory,
          Bayesian Inference & Multilingual NLP — built on the real Charité Campus Mitte model.
        </div>
        <div style={{marginTop:18, display:'flex', gap:10, flexWrap:'wrap'}}>
          <Link to="/navigate" className="btn btn-primary btn-lg">🗺️ Launch Navigator</Link>
          <Link to="/search"   className="btn btn-secondary btn-lg">🔍 Algorithm Lab</Link>
        </div>
      </div>

      {/* Stats */}
      <div className="metrics-row metrics-4" style={{marginBottom:24}}>
        {[
          {val: health?.nodes ?? '41', lbl:'Hospital Nodes',       color:'#b45309'},
          {val:'52',                    lbl:'Graph Edges',           color:'#0891b2'},
          {val:'3',                     lbl:'Languages (EN/HI/TE)', color:'#7c3aed'},
          {val:'6',                     lbl:'AI Modules · CO1–CO6', color:'#15803d'},
        ].map(({val, lbl, color}) => (
          <div className="metric-card" key={lbl}>
            <div className="metric-val" style={{color}}>{val}</div>
            <div className="metric-lbl">{lbl}</div>
          </div>
        ))}
      </div>

      {/* Modules */}
      <div className="section-label">🎓 Course Outcome Coverage</div>
      <div className="module-grid">
        {MODULES.map(({co, cls, emoji, title, desc, chips, link}) => (
          <div className="module-card" key={co}>
            <div className="module-icon">{emoji}</div>
            <div style={{marginBottom:6}}>
              <span className={`badge badge-${cls}`}>{co}</span>
            </div>
            <div className="module-title">{title}</div>
            <div className="module-desc">{desc}</div>
            <div className="module-chips">
              {chips.map(c => <span key={c} className="chip">{c}</span>)}
            </div>
            <Link to={link} className="module-link">Open {co} →</Link>
          </div>
        ))}
      </div>

      {/* Hospital topology */}
      <div className="section-label">🏗️ Hospital Graph — Charité Campus Mitte</div>
      <div className="two-col">
        <div className="card card-sm">
          <div style={{fontSize:'.72rem', fontWeight:800, color:'#1d4ed8',
            letterSpacing:'.5px', textTransform:'uppercase', marginBottom:10}}>
            🏛️ Historic Wing (Stairs-Heavy)
          </div>
          <table style={{width:'100%', fontSize:'.8rem', borderCollapse:'collapse'}}>
            <tbody>
              {[
                ['#7c3aed','Lab_101 / Lab_102','Lab','🔒 Visitor'],
                ['#b45309','HW_Stairs_A / B','Stairs','🚫 Wheelchair'],
                ['#6b7280','HW_Admin','Office',''],
                ['#6b7280','HW_Pharmacy','Pharmacy',''],
                ['#7c3aed','HW_Radiology','Lab','🔒 Visitor'],
                ['#94a3b8','HW_Corridor G/1/2','Corridor',''],
              ].map(([col,name,type,tag]) => (
                <tr key={name}>
                  <td><span style={{color:col}}>●</span> {name}</td>
                  <td style={{color:'#9ca3af', fontSize:'.72rem'}}>{type}</td>
                  <td style={{color:'#dc2626', fontSize:'.68rem'}}>{tag}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card card-sm">
          <div style={{fontSize:'.72rem', fontWeight:800, color:'#0891b2',
            letterSpacing:'.5px', textTransform:'uppercase', marginBottom:10}}>
            🏢 Bettenhaus Tower (21 Floors)
          </div>
          <table style={{width:'100%', fontSize:'.8rem', borderCollapse:'collapse'}}>
            <tbody>
              {[
                ['#dc2626','ICU_Floor3 / Node_302','ICU','🔒 Visitors'],
                ['#1d4ed8','Elevator_A / Elevator_B','Elevator',''],
                ['#15803d','Ward_Cardio_F7','Floor 7',''],
                ['#15803d','Ward_Maternity_F10','Floor 10',''],
                ['#15803d','Ward_Neuro_F5','Floor 5',''],
                ['#0891b2','ENTRANCE_MAIN','Entry Point',''],
              ].map(([col,name,type,tag]) => (
                <tr key={name}>
                  <td><span style={{color:col}}>●</span> {name}</td>
                  <td style={{color:'#9ca3af', fontSize:'.72rem'}}>{type}</td>
                  <td style={{color:'#dc2626', fontSize:'.68rem'}}>{tag}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Footer */}
      <div style={{textAlign:'center', padding:'20px 0 4px', color:'#9ca3af',
        fontSize:'.75rem', borderTop:'1px solid #e8d9c4', marginTop:16}}>
        IIT Madras · CFAI Project · Charité Campus Mitte · BFS · DFS · UCS · A* · CSP · Minimax · Bayesian · HMM · NLP · CO1–CO6
      </div>
    </div>
  )
}
