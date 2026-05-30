import { useState, useEffect } from 'react'
import { runGame, getNodes } from '../api'

const PROFILES = [{v:'emergency',l:'🚨 Emergency'},{v:'staff',l:'🩺 Staff'},{v:'visitor',l:'👤 Visitor'},{v:'patient',l:'♿ Patient'}]

export default function Game() {
  const [nodes, setNodes]   = useState([])
  const [start, setStart]   = useState('ENTRANCE_MAIN')
  const [goal, setGoal]     = useState('Node_302_ICU_Tower')
  const [prof, setProf]     = useState('emergency')
  const [depth, setDepth]   = useState(3)
  const [ab, setAb]         = useState(true)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  useEffect(()=>{ getNodes().then(r=>setNodes(r.data)) },[])

  const doRun = async () => {
    setLoading(true); setResult(null)
    try {
      const r = await runGame({start, goal, profile:prof, depth, use_alpha_beta:ab})
      setResult(r.data)
    } catch(e) { alert('Game error: '+e.message) }
    setLoading(false)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          ♟️ Game AI <span className="badge badge-co4">CO4</span>
        </div>
        <div className="page-sub">Minimax + Alpha-Beta Pruning · Triage Priority Routing · Two-Player Zero-Sum Game</div>
      </div>

      {/* Concept */}
      <div className="alert alert-info" style={{marginBottom:16}}>
        <div>
          <strong>Game framing:</strong> Triage routing as adversarial search.<br/>
          <span style={{fontSize:'.8rem'}}>
            <strong>MAX (Ambulance)</strong> tries to minimise travel time to ICU. &nbsp;
            <strong>MIN (Congestion Controller)</strong> raises corridor loads to maximise time.
            Alpha-beta pruning removes provably suboptimal branches.
          </span>
        </div>
      </div>

      {/* Config */}
      <div className="card">
        <div className="form-row form-4">
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
            <label className="form-label">Profile</label>
            <select className="form-control" value={prof} onChange={e=>setProf(e.target.value)}>
              {PROFILES.map(p=><option key={p.v} value={p.v}>{p.l}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Search Depth ({depth})</label>
            <input type="range" min={1} max={5} value={depth}
              onChange={e=>setDepth(Number(e.target.value))}
              style={{width:'100%',accentColor:'#b45309',marginTop:8}} />
          </div>
        </div>
        <div style={{display:'flex', alignItems:'center', gap:16, marginTop:12}}>
          <label className="toggle-row">
            <label className="toggle">
              <input type="checkbox" checked={ab} onChange={e=>setAb(e.target.checked)} />
              <span className="toggle-slider" />
            </label>
            <span className="toggle-label">Alpha-Beta Pruning</span>
          </label>
          <button className="btn btn-primary btn-full" onClick={doRun} disabled={loading}>
            {loading?'⏳ Running Minimax…':'▶ Run Game AI'}
          </button>
        </div>
      </div>

      {/* Result */}
      {result && (
        <>
          <div className="metrics-row metrics-3" style={{marginBottom:16}}>
            {[
              {val:result.best_path?.length??'—', lbl:'Hops'},
              {val:`${result.best_cost?.toFixed(0)??'—'}s`, lbl:'Best Cost (MAX wins)'},
              {val:result.nodes_evaluated??'—', lbl:'Nodes Evaluated'},
            ].map(({val,lbl})=>(
              <div className="metric-card" key={lbl}>
                <div className="metric-val">{val}</div>
                <div className="metric-lbl">{lbl}</div>
              </div>
            ))}
          </div>

          {result.best_path?.length>0 && (
            <div className="alert alert-success">
              ✅ <strong>MAX wins</strong> — best triage path: {result.best_path.join(' → ')}
            </div>
          )}

          {result.pruned_branches !== undefined && (
            <div className="alert alert-info">
              ✂️ Alpha-beta pruned <strong>{result.pruned_branches}</strong> branches
              ({result.pruned_branches>0 ? 'saved computation' : 'no pruning at this depth'})
            </div>
          )}

          {result.minimax_trace?.length > 0 && (
            <>
              <div className="section-label">🌳 Minimax Trace</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead>
                    <tr><th>Depth</th><th>Node</th><th>Player</th><th>Score</th><th>Action</th></tr>
                  </thead>
                  <tbody>
                    {result.minimax_trace.slice(0,30).map((t,i)=>(
                      <tr key={i}>
                        <td>{t.depth}</td>
                        <td><code>{t.node}</code></td>
                        <td style={{color:t.is_max?'#15803d':'#dc2626',fontWeight:700}}>
                          {t.is_max?'MAX ▲':'MIN ▼'}
                        </td>
                        <td>{t.score?.toFixed(2)}</td>
                        <td style={{fontSize:'.72rem'}}>{t.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <div className="section-label">♟️ CO4 Explainability</div>
          <div className="card card-sm" style={{fontSize:'.84rem',lineHeight:1.7}}>
            <p><strong>Minimax:</strong> MAX maximises path quality; MIN simulates worst-case congestion.</p>
            <p><strong>Eval function:</strong> f = −travel_cost + urgency_bonus − congestion_penalty</p>
            <p><strong>Alpha-Beta:</strong> α = best MAX found, β = best MIN found. Prune when α ≥ β.</p>
            <p><strong>Depth {depth}:</strong> explores {depth} plies of alternating MAX/MIN moves.</p>
          </div>
        </>
      )}
    </div>
  )
}
