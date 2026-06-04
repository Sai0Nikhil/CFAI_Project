import { useState, useEffect } from 'react'
import { runSearch, compareAll, getNodes } from '../api'
import GraphMap from '../components/GraphMap'
import GraphSkeleton from '../components/GraphSkeleton'
import ExportPDFButton from '../components/ExportPDF'
import AIInsight from '../components/AIInsight'
import { useAI } from '../context/AIContext'

const ALGOS   = [{v:'astar',l:'⭐ A*'},{v:'ucs',l:'💰 UCS'},{v:'bfs',l:'🌊 BFS'},{v:'dfs',l:'🔦 DFS'}]
const PROFILES = [{v:'staff',l:'🩺 Staff'},{v:'emergency',l:'🚨 Emergency'},{v:'visitor',l:'👤 Visitor'},{v:'patient',l:'♿ Patient'}]
const CMPLX   = {bfs:'O(V+E)',dfs:'O(V+E)',ucs:'O((V+E)logV)',astar:'O((V+E)logV)'}
const OPTIMAL = {bfs:'Hops only',dfs:'❌ No',ucs:'✅ Cost',astar:'✅ Cost + h(n)'}

export default function Search() {
  const { hospital, hospitalInfo } = useAI()
  const [nodes, setNodes]   = useState([])
  const [algo, setAlgo]     = useState('astar')
  const [prof, setProf]     = useState('staff')
  const [start, setStart]   = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [goal, setGoal]     = useState(hospitalInfo?.defaultGoal  || 'Node_302_ICU_Tower')
  const [result, setResult] = useState(null)
  const [cmp, setCmp]       = useState(null)
  const [loading, setLoading] = useState(false)
  const [cmpLoading, setCmpLoading] = useState(false)
  const [showAll, setShowAll] = useState(false)
  const [aiTrigger, setAiTrigger] = useState(0)
  const [cmpAiTrigger, setCmpAiTrigger] = useState(0)

  useEffect(() => { getNodes(hospital).then(r => setNodes(r.data)) }, [hospital])
  // Reset defaults when hospital changes
  useEffect(() => {
    setStart(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
    setGoal(hospitalInfo?.defaultGoal   || 'Node_302_ICU_Tower')
  }, [hospital])

  const doSearch = async () => {
    setLoading(true); setResult(null)
    try {
      const r = await runSearch({algorithm:algo, profile:prof, start, goal, hospital})
      setResult(r.data)
      setAiTrigger(t => t + 1)
    } catch(e) { alert('Search failed: '+e.message) }
    setLoading(false)
  }

  const doCompare = async () => {
    setCmpLoading(true); setCmp(null)
    try {
      const r = await compareAll({profile:prof, start, goal, hospital})
      setCmp(r.data)
      setCmpAiTrigger(t => t + 1)
    } catch(e) { alert('Compare failed: '+e.message) }
    setCmpLoading(false)
  }

  const trace = result?.trace || []
  const displayed = showAll ? trace : trace.slice(0,25)

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          🔍 Search
          <span className="badge badge-co2">CO2</span>
        </div>
        <div className="page-sub">BFS · DFS · UCS · A* on the {hospitalInfo?.name || 'hospital'} graph {hospitalInfo?.flag}</div>
      </div>

      {/* Controls */}
      <div className="card">
        <div className="form-row form-4">
          <div className="form-group">
            <label className="form-label">Algorithm</label>
            <select className="form-control" value={algo} onChange={e=>setAlgo(e.target.value)}>
              {ALGOS.map(a=><option key={a.v} value={a.v}>{a.l}</option>)}
            </select>
          </div>
          <div className="form-group">
            <label className="form-label">Profile</label>
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
        </div>
        <div style={{marginTop:14, display:'flex', gap:10}}>
          <button className="btn btn-primary btn-full btn-lg" onClick={doSearch} disabled={loading}>
            {loading ? '⏳ Running…' : '▶ Run Search'}
          </button>
          <ExportPDFButton result={result} algo={algo} prof={prof} start={start} goal={goal} />
        </div>
      </div>

      {/* Skeleton while loading */}
      {loading && (
        <div style={{marginTop:16}}>
          <GraphSkeleton message={`Running ${algo.toUpperCase()} on ${prof} profile…`} />
        </div>
      )}

      {/* Result */}
      {!loading && result && (
        <>
          {result.path?.length ? (
            <>
              <div className="metrics-row metrics-4">
                {[
                  {val:result.path.length, lbl:'Hops'},
                  {val:`${result.cost?.toFixed(0)}s`, lbl:'Travel Time'},
                  {val:result.stats?.expansions??'—', lbl:'Nodes Expanded'},
                  {val:result.stats?.peak_frontier??'—', lbl:'Peak Frontier'},
                ].map(({val,lbl})=>(
                  <div className="metric-card" key={lbl}>
                    <div className="metric-val">{val}</div>
                    <div className="metric-lbl">{lbl}</div>
                  </div>
                ))}
              </div>
              <div className="alert alert-success">
                ✅ <strong>Path:</strong> {result.path.join(' → ')}
              </div>
              <div style={{fontSize:'.75rem',color:'#6b7280',marginTop:4}}>
                {algo.toUpperCase()} · Time {CMPLX[algo]} · Space O(V) · {OPTIMAL[algo]}
              </div>
            </>
          ) : (
            <div className="alert alert-error">
              ❌ No path from <code>{start}</code> → <code>{goal}</code> for profile <strong>{prof}</strong>. Try Staff or Emergency.
            </div>
          )}

          {/* Interactive graph */}
          {result.path?.length > 0 && (
            <>
              <div className="section-label">🗺️ Interactive Hospital Graph</div>
              <GraphMap profile={prof} path={result.path} start={start} goal={goal} hospital={hospital} />
            </>
          )}

          {/* Trace table */}
          {result.path?.length > 0 && (
            <>
              <div className="section-label">📋 Step-by-Step Trace Log</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Step</th><th>Action</th><th>Node</th>
                      {algo==='astar'&&<><th>F</th><th>G</th><th>H</th></>}
                      <th>Note</th>
                    </tr>
                  </thead>
                  <tbody>
                    {displayed.map((t,i)=>(
                      <tr key={i}>
                        <td>{t.step}</td>
                        <td>{t.action}</td>
                        <td>{t.node}</td>
                        {algo==='astar'&&<><td>{t.f?.toFixed(1)}</td><td>{t.g?.toFixed(1)}</td><td>{t.h?.toFixed(1)}</td></>}
                        <td>{t.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {trace.length > 25 && (
                <button className="btn btn-secondary" style={{marginTop:8}}
                  onClick={()=>setShowAll(!showAll)}>
                  {showAll ? 'Show less' : `Show all ${trace.length} steps`}
                </button>
              )}

              {/* Explainability */}
              <AIInsight
                module="search"
                trigger={aiTrigger}
                context={{ algorithm:algo, profile:prof, start, goal,
                  path:result.path, cost:result.cost,
                  expansions:result.stats?.expansions }}
              />

              <details style={{marginTop:14}}>
                <summary>🔍 Why this path? (CO2 Explainability)</summary>
                <div className="card card-sm" style={{marginTop:8, fontSize:'.85rem', lineHeight:1.7}}>
                  <p><strong>Algorithm:</strong> {algo.toUpperCase()} on <strong>{prof}</strong> profile</p>
                  <p><strong>Path:</strong> {result.path.join(' → ')}</p>
                  <p><strong>Cost:</strong> {result.cost?.toFixed(0)}s &nbsp;|&nbsp; <strong>Expansions:</strong> {result.stats?.expansions}</p>
                  <p style={{marginTop:8}}>
                    Every node is <strong>accessible</strong> for the <code>{prof}</code> profile.
                    The heuristic <code>h(n) = |floor_goal − floor_n| × 12s</code> never overestimates — it is <strong>admissible</strong>.
                  </p>
                </div>
              </details>
            </>
          )}
        </>
      )}

      {/* Comparison */}
      <div className="section-label">📊 Algorithm Comparison — All 4 on the Same Query</div>
      <div style={{fontSize:'.82rem', color:'#374151', marginBottom:12}}>
        Run BFS · DFS · UCS · A* simultaneously on the chosen start → goal and profile.
      </div>
      <button className="btn btn-secondary btn-full" onClick={doCompare} disabled={cmpLoading}>
        {cmpLoading ? '⏳ Running all 4…' : '⚡ Compare All 4 Algorithms Now'}
      </button>

      {cmp && (
        <div style={{marginTop:16}}>
          <div className="table-wrap">
            <table className="trace-table">
              <thead>
                <tr>
                  <th>Algorithm</th><th>Found?</th><th>Hops</th>
                  <th>Cost (s)</th><th>Expansions</th><th>Optimal?</th><th>Complexity</th>
                </tr>
              </thead>
              <tbody>
                {['bfs','dfs','ucs','astar'].map(a=>{
                  const r=cmp[a]; const has=r.path?.length>0
                  const labels={bfs:'🌊 BFS',dfs:'🔦 DFS',ucs:'💰 UCS',astar:'⭐ A*'}
                  return (
                    <tr key={a}>
                      <td><strong>{labels[a]}</strong></td>
                      <td>{has?'✅':'❌'}</td>
                      <td>{has?r.path.length:'—'}</td>
                      <td>{has?`${r.cost?.toFixed(0)}s`:'—'}</td>
                      <td>{has?r.stats?.expansions:'—'}</td>
                      <td>{OPTIMAL[a]}</td>
                      <td><code>{CMPLX[a]}</code></td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
          <AIInsight
            module="compare"
            trigger={cmpAiTrigger}
            context={{ results: cmp, start, goal, profile: prof }}
          />
          {cmp.astar?.path?.length>0 && (
            <div className="alert alert-success" style={{marginTop:12}}>
              ⭐ <strong>A*</strong> finds the optimal-cost path ({cmp.astar.cost?.toFixed(0)}s)
              with only <strong>{cmp.astar.stats?.expansions} expansions</strong> —
              guided by admissible heuristic h(n) = |floor_goal − floor_n| × 12s
            </div>
          )}
        </div>
      )}
    </div>
  )
}
