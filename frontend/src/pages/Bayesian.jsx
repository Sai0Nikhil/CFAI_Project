import { useState, useEffect } from 'react'
import { bayesInfer, bayesHMM, bayesRoute, bayesOptions, getNodes } from '../api'

export default function Bayesian() {
  const [opts, setOpts]     = useState({time_of_day:[], sensors:[], occupancy:[], hmm_states:[]})
  const [nodes, setNodes]   = useState([])
  const [tab, setTab]       = useState('bayes')

  // Bayes
  const [sensor, setSensor] = useState('busy')
  const [fixTime, setFixTime] = useState(true)
  const [tod, setTod]       = useState('morning')
  const [fixDay, setFixDay] = useState(false)
  const [day, setDay]       = useState('weekday')
  const [bayesRes, setBayesRes] = useState(null)
  const [bayesLoading, setBayesLoading] = useState(false)

  // HMM
  const [nObs, setNObs]     = useState(4)
  const [obs, setObs]       = useState(['clear','busy','busy','jammed'])
  const [hmmRes, setHmmRes] = useState(null)
  const [hmmLoading, setHmmLoading] = useState(false)

  // Route
  const [rStart, setRStart] = useState('ENTRANCE_MAIN')
  const [rGoal, setRGoal]   = useState('Node_302_ICU_Tower')
  const [routeRes, setRouteRes] = useState(null)
  const [routeLoading, setRouteLoading] = useState(false)

  useEffect(()=>{
    bayesOptions().then(r=>{ setOpts(r.data); setTod(r.data.time_of_day?.[0]||'morning') })
    getNodes().then(r=>setNodes(r.data))
  },[])

  const doInfer = async () => {
    setBayesLoading(true); setBayesRes(null)
    try {
      const r = await bayesInfer({sensor, time_of_day:fixTime?tod:null, day_type:fixDay?day:null})
      setBayesRes(r.data)
    } catch(e) { alert(e.message) }
    setBayesLoading(false)
  }

  const doHMM = async () => {
    setHmmLoading(true); setHmmRes(null)
    try {
      const r = await bayesHMM({observations: obs.slice(0,nObs)})
      setHmmRes(r.data)
    } catch(e) { alert(e.message) }
    setHmmLoading(false)
  }

  const doRoute = async () => {
    setRouteLoading(true); setRouteRes(null)
    try {
      const r = await bayesRoute({start:rStart, goal:rGoal})
      setRouteRes(r.data)
    } catch(e) { alert(e.message) }
    setRouteLoading(false)
  }

  const SENSOR_LABEL = {clear:'🟢 Clear', busy:'🟡 Busy', jammed:'🔴 Jammed'}
  const OCC_COLOR    = {low:'#15803d', medium:'#d97706', high:'#dc2626'}

  return (
    <div>
      <div className="page-header">
        <div className="page-title">🎲 Bayesian <span className="badge badge-co5">CO5</span></div>
        <div className="page-sub">Bayesian Network · Variable Elimination · HMM Forward Algorithm · Uncertainty-Aware Routing</div>
      </div>

      <div style={{display:'flex', gap:6, marginBottom:20}}>
        {[['bayes','🔮 Bayesian Inference'],['hmm','📡 HMM Tracking'],['route','🗺️ Uncertainty Routing']].map(([v,l])=>(
          <button key={v} className={`btn ${tab===v?'btn-primary':'btn-secondary'}`} onClick={()=>setTab(v)}>{l}</button>
        ))}
      </div>

      {tab==='bayes' && (
        <>
          <div className="alert alert-info" style={{marginBottom:14}}>
            <div><strong>Network:</strong> TimeOfDay → Occupancy ← DayType &nbsp;→&nbsp; SensorReads<br/>
            <span style={{fontSize:'.8rem'}}>Variable elimination computes P(Occupancy | sensor, evidence)</span></div>
          </div>
          <div className="card">
            <div className="form-row form-3">
              <div className="form-group">
                <label className="form-label">🔵 Sensor Reading</label>
                <select className="form-control" value={sensor} onChange={e=>setSensor(e.target.value)}>
                  {opts.sensors.map(s=><option key={s} value={s}>{SENSOR_LABEL[s]||s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">
                  <input type="checkbox" checked={fixTime} onChange={e=>setFixTime(e.target.checked)} style={{marginRight:6}} />
                  Fix TimeOfDay
                </label>
                {fixTime && (
                  <select className="form-control" value={tod} onChange={e=>setTod(e.target.value)}>
                    {opts.time_of_day.map(t=><option key={t} value={t}>{t}</option>)}
                  </select>
                )}
              </div>
              <div className="form-group">
                <label className="form-label">
                  <input type="checkbox" checked={fixDay} onChange={e=>setFixDay(e.target.checked)} style={{marginRight:6}} />
                  Fix DayType
                </label>
                {fixDay && (
                  <select className="form-control" value={day} onChange={e=>setDay(e.target.value)}>
                    {['weekday','weekend'].map(d=><option key={d} value={d}>{d}</option>)}
                  </select>
                )}
              </div>
            </div>
            <button className="btn btn-primary btn-full" style={{marginTop:12}} onClick={doInfer} disabled={bayesLoading}>
              {bayesLoading?'⏳ Computing…':'▶ Run Bayesian Inference'}
            </button>
          </div>

          {bayesRes && (
            <>
              <div className="alert alert-success">{bayesRes.explanation}</div>
              <div className="section-label">📊 P(Occupancy | evidence)</div>
              <div className="card card-sm">
                {opts.occupancy.map(o=>{
                  const v = bayesRes.posterior?.[o]||0
                  return (
                    <div key={o} style={{marginBottom:12}}>
                      <div style={{display:'flex',justifyContent:'space-between',marginBottom:4}}>
                        <span style={{fontWeight:700,color:OCC_COLOR[o]}}>{o}</span>
                        <span style={{fontWeight:800}}>{(v*100).toFixed(1)}%</span>
                      </div>
                      <div style={{background:'#f3e8d8',borderRadius:4,height:18,overflow:'hidden'}}>
                        <div style={{width:`${v*100}%`,background:OCC_COLOR[o],height:'100%',
                          borderRadius:4,transition:'width .4s'}} />
                      </div>
                    </div>
                  )
                })}
                <div style={{marginTop:8,fontSize:'.8rem'}}>
                  <strong>MAP estimate:</strong> <code>{bayesRes.map_estimate}</code> &nbsp;·&nbsp;
                  <strong>Complexity:</strong> O(n·d^w)
                </div>
              </div>
            </>
          )}
        </>
      )}

      {tab==='hmm' && (
        <>
          <div className="alert alert-info" style={{marginBottom:14}}>
            <div><strong>Hidden states:</strong> low · medium · high &nbsp;|&nbsp;
            <strong>Forward Algorithm:</strong> P(state_t | obs_1:t)</div>
          </div>
          <div className="card">
            <div className="form-group" style={{marginBottom:12}}>
              <label className="form-label">Number of time steps ({nObs})</label>
              <input type="range" min={2} max={8} value={nObs}
                onChange={e=>{ setNObs(Number(e.target.value)); setObs(a=>{const n=[...a];while(n.length<Number(e.target.value))n.push('clear');return n}) }}
                style={{width:'100%',accentColor:'#b45309'}} />
            </div>
            <div className="form-row" style={{gridTemplateColumns:`repeat(${nObs},1fr)`}}>
              {Array(nObs).fill(0).map((_,i)=>(
                <div className="form-group" key={i}>
                  <label className="form-label">t={i}</label>
                  <select className="form-control" value={obs[i]||'clear'}
                    onChange={e=>setObs(a=>{const n=[...a];n[i]=e.target.value;return n})}>
                    {opts.sensors.map(s=><option key={s} value={s}>{SENSOR_LABEL[s]||s}</option>)}
                  </select>
                </div>
              ))}
            </div>
            <button className="btn btn-primary btn-full" style={{marginTop:12}} onClick={doHMM} disabled={hmmLoading}>
              {hmmLoading?'⏳ Computing…':'▶ Run HMM Forward Pass'}
            </button>
          </div>

          {hmmRes && (
            <>
              <div className="alert alert-success">{hmmRes.explanation}</div>
              <div className="section-label">📡 Belief Evolution Over Time</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead><tr><th>Time</th><th>Obs</th>{(opts.hmm_states||['low','medium','high']).map(s=><th key={s}>{s}</th>)}</tr></thead>
                  <tbody>
                    {hmmRes.trace?.map((t,i)=>(
                      <tr key={i}>
                        <td>t={t.t}</td>
                        <td>{SENSOR_LABEL[t.observation]||t.observation}</td>
                        {Object.values(t.belief||{}).map((p,j)=>(
                          <td key={j} style={{fontWeight:700,color:OCC_COLOR[Object.keys(t.belief)[j]]}}>
                            {(p*100).toFixed(1)}%
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}

      {tab==='route' && (
        <>
          <div className="alert alert-info" style={{marginBottom:14}}>
            A* finds the path, then edge costs are <strong>adjusted by occupancy estimates</strong>.<br/>
            <span style={{fontSize:'.8rem'}}>Congestion factors: low×1.0 · medium×1.4 · high×2.0</span>
          </div>
          <div className="card">
            <div className="form-row form-2">
              <div className="form-group">
                <label className="form-label">Start</label>
                <select className="form-control" value={rStart} onChange={e=>setRStart(e.target.value)}>
                  {nodes.map(n=><option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Goal</label>
                <select className="form-control" value={rGoal} onChange={e=>setRGoal(e.target.value)}>
                  {nodes.map(n=><option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
            </div>
            <button className="btn btn-primary btn-full" style={{marginTop:12}} onClick={doRoute} disabled={routeLoading}>
              {routeLoading?'⏳ Routing…':'▶ Run Uncertainty-Aware Routing'}
            </button>
          </div>

          {routeRes && (
            <>
              <div className="alert alert-success">{routeRes.explanation}</div>
              <div className="metrics-row metrics-3" style={{marginBottom:16}}>
                {[
                  {val:`${routeRes.total_base_cost}s`, lbl:'Base Cost'},
                  {val:`${routeRes.total_adjusted_cost?.toFixed(0)}s`, lbl:'Adjusted Cost'},
                  {val:`+${(routeRes.total_adjusted_cost-routeRes.total_base_cost).toFixed(1)}s`, lbl:'Congestion Overhead'},
                ].map(({val,lbl})=>(
                  <div className="metric-card" key={lbl}>
                    <div className="metric-val">{val}</div>
                    <div className="metric-lbl">{lbl}</div>
                  </div>
                ))}
              </div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead><tr><th>Edge</th><th>Base</th><th>Sensor</th><th>Factor</th><th>Adjusted</th></tr></thead>
                  <tbody>
                    {routeRes.adjusted_edges?.map((e,i)=>(
                      <tr key={i}>
                        <td><code>{e.u} → {e.v}</code></td>
                        <td>{e.base_cost}s</td>
                        <td>{SENSOR_LABEL[e.sensor]||e.sensor}</td>
                        <td>×{e.factor}</td>
                        <td style={{fontWeight:700}}>{e.adjusted_cost?.toFixed(1)}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
