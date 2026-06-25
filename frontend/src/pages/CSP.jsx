import { useState, useEffect } from 'react'
import { validateCSP, timeWindow, runSearch, getNodes } from '../api'
import AIInsight from '../components/AIInsight'
import { useAI } from '../context/AIContext'

const PROFILES = [{v:'staff',l:'🩺 Staff'},{v:'emergency',l:'🚨 Emergency'},{v:'visitor',l:'👤 Visitor'},{v:'patient',l:'♿ Patient'}]

export default function CSP() {
  const { hospital, hospitalInfo } = useAI()
  const [nodes, setNodes]   = useState([])
  const [prof, setProf]     = useState('visitor')
  const [start, setStart]   = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [goal, setGoal]     = useState(hospitalInfo?.defaultGoal  || 'Node_302_ICU_Tower')
  const [hour, setHour]     = useState(10)
  const [result, setResult] = useState(null)
  const [tw, setTw]         = useState(null)
  const [loading, setLoading] = useState(false)
  const [aiTrigger, setAiTrigger] = useState(0)

  useEffect(()=>{ getNodes(hospital).then(r=>setNodes(r.data)) },[hospital])
  useEffect(()=>{ setStart(hospitalInfo?.defaultStart||'ENTRANCE_MAIN'); setGoal(hospitalInfo?.defaultGoal||'Node_302_ICU_Tower') },[hospital])

  const doValidate = async () => {
    setLoading(true); setResult(null)
    try {
      // First find path, then validate it
      const sr = await runSearch({algorithm:'astar', profile:prof, start, goal, hospital})
      const path = sr.data.path
      if (!path?.length) { setResult({path_found:false}); setLoading(false); return }
      const r = await validateCSP({path, profile:prof, hour, hospital})
      setResult({...r.data, path, cost:sr.data.cost})
      setAiTrigger(t => t + 1)
    } catch(e) { alert('CSP error: '+e.message) }
    setLoading(false)
  }

  const doTimeWindow = async () => {
    try {
      const r = await timeWindow(prof, goal)
      setTw(r.data)
    } catch(e) { alert('Time window error: '+e.message) }
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          🧩 CSP <span className="badge badge-co3">CO3</span>
        </div>
        <div className="page-sub">Backtracking · Forward Checking · AC-3 Arc Consistency · MRV Heuristic</div>
      </div>

      {/* Config */}
      <div className="card">
        <div className="form-row form-4">
          <div className="form-group">
            <label className="form-label">Access Profile</label>
            <select className="form-control" value={prof} onChange={e=>setProf(e.target.value)}>
              {PROFILES.map(p=><option key={p.v} value={p.v}>{p.l}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Start Node</label>
            <select className="form-control" value={start} onChange={e=>setStart(e.target.value)}>
              {nodes.map(n=><option key={n.id} value={n.id}>{n.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Goal Node</label>
            <select className="form-control" value={goal} onChange={e=>setGoal(e.target.value)}>
              {nodes.map(n=><option key={n.id} value={n.id}>{n.label}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Hour of Day ({hour}:00)</label>
            <input type="range" min={0} max={23} value={hour}
              onChange={e=>setHour(Number(e.target.value))}
              style={{width:'100%',accentColor:'#b45309',marginTop:8}} />
          </div>
        </div>
        <div style={{display:'flex', gap:10, marginTop:12}}>
          <button className="btn btn-primary btn-full" onClick={doValidate} disabled={loading}>
            {loading?'⏳ Validating…':'▶ Validate Path CSP'}
          </button>
          <button className="btn btn-secondary" onClick={doTimeWindow}>
            🕐 Find Time Window
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <>
          {result.path_found === false ? (
            <div className="alert alert-error">❌ No path found for <strong>{prof}</strong> profile — CSP blocks all routes to this node.</div>
          ) : (
            <>
              <div className={`alert ${result.overall_valid?'alert-success':'alert-error'}`}>
                {result.overall_valid
                  ? '✅ All CSP constraints satisfied — path is valid.'
                  : `❌ ${result.violations} constraint violation(s) found.`}
              </div>
              <div className="alert alert-info">
                📍 Path: {result.path?.join(' → ')} · {result.cost?.toFixed(0)}s
              </div>

              <div className="section-label">📋 Constraint Trace</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead>
                    <tr><th>Step</th><th>Type</th><th>Node/Edge</th><th>Result</th><th>Reason</th></tr>
                  </thead>
                  <tbody>
                    {result.trace?.map((t,i)=>(
                      <tr key={i}>
                        <td>{i+1}</td>
                        <td>{t.type}</td>
                        <td><code>{t.node||`${t.u}↔${t.v}`}</code></td>
                        <td>
                          <span style={{color:t.result==='PASS'?'#15803d':'#dc2626',fontWeight:700}}>
                            {t.result==='PASS'?'✅ PASS':'❌ FAIL'}
                          </span>
                        </td>
                        <td style={{fontSize:'.75rem'}}>{t.reason}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <AIInsight
                module="csp"
                trigger={aiTrigger}
                context={{ profile:prof, overall_valid:result.overall_valid,
                  path:result.path, violations:result.violations, trace:result.trace }}
              />
              <div className="section-label">🧩 CSP Formulation & Constraints (CO3)</div>
              <div className="card card-sm" style={{fontSize:'.84rem',lineHeight:1.7}}>
                <div className="two-col" style={{ gap: '16px' }}>
                  <div>
                    <strong style={{color:'#b45309', fontSize:'.9rem'}}>Variables ($X$)</strong>
                    <p style={{fontSize:'.8rem', color:'#374151', marginTop:4}}>
                      Each location/passage step along the proposed path: <br/>
                      <code>{'$X = \\{X_1, X_2, \\dots, X_n\\}$'}</code>
                    </p>

                    <strong style={{color:'#b45309', fontSize:'.9rem', display:'block', marginTop:12}}>Domains ($D$)</strong>
                    <p style={{fontSize:'.8rem', color:'#374151', marginTop:4}}>
                       Traversal viability assignment for each step: <br/>
                      <code>{'$Domain(X_i) = \\{\\text{Allowed}, \\text{Blocked}\\}$'}</code>
                    </p>

                    <strong style={{color:'#b45309', fontSize:'.9rem', display:'block', marginTop:12}}>Constraint Algorithms</strong>
                    <p style={{fontSize:'.8rem', color:'#374151', marginTop:4}}>
                      Checks path consistency dynamically using **Forward Checking** (pre-evaluation of hops), **AC-3** (enforcing edge-wise arc consistency), and the **MRV heuristic** (Variable ordering based on Time Window size).
                    </p>
                  </div>

                  <div>
                    <strong style={{color:'#b45309', fontSize:'.9rem'}}>Active Constraints ($C$)</strong>
                    <ul style={{fontSize:'.8rem', color:'#374151', paddingLeft:14, marginTop:4, listStyleType:'disc'}}>
                      <li style={{marginBottom:4}}><strong>Profile Lock:</strong> Locations cannot have selected profile in their restricted list (e.g. Visitor blocked from Labs/Wards).</li>
                      <li style={{marginBottom:4}}><strong>Wheelchair Barrier (Patient):</strong> Cannot traverse staircases (edges with <code>via = "stairs"</code> are pruned).</li>
                      <li style={{marginBottom:4}}><strong>Temporal ICU Window:</strong> ICU nodes locked outside of **06:00 – 22:00** for Visitors & Patients.</li>
                      <li style={{marginBottom:4}}><strong>Emergency Override:</strong> Emergency profile overrides all access checks (<code>{'$Domain = \\{\\text{Allowed}\\}$'}</code>).</li>
                    </ul>
                  </div>
                </div>
              </div>
            </>
          )}
        </>
      )}

      {/* Time window */}
      {tw && (
        <>
          <div className="section-label">🕐 Valid Access Time Windows for {prof}</div>
          <div className="card card-sm">
            {tw.valid_hours?.length ? (
              <>
                <div className="alert alert-success" style={{marginBottom:10}}>
                  ✅ {prof} can access {goal.replace(/_/g,' ')} during: <strong>{tw.valid_hours?.join(', ')}</strong>
                </div>
                <div style={{display:'flex',flexWrap:'wrap',gap:6}}>
                  {Array(24).fill(0).map((_,h)=>(
                    <span key={h} style={{
                      padding:'4px 10px', borderRadius:6, fontSize:'.72rem', fontWeight:700,
                      background: tw.valid_hours?.includes(h) ? '#f0fdf4' : '#fef2f2',
                      color: tw.valid_hours?.includes(h) ? '#15803d' : '#dc2626',
                      border: `1px solid ${tw.valid_hours?.includes(h)?'#bbf7d0':'#fecaca'}`,
                    }}>{h}:00</span>
                  ))}
                </div>
              </>
            ) : (
              <div className="alert alert-error">❌ {prof} has no access to this node at any time.</div>
            )}
          </div>
        </>
      )}
    </div>
  )
}
