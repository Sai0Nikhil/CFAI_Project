import { useState, useEffect, useRef } from 'react'
import { getNodes, runSearch, parseNLP, validateCSP } from '../api'
import GraphMap from '../components/GraphMap'
import GraphSkeleton from '../components/GraphSkeleton'
import ExportPDFButton from '../components/ExportPDF'

const ALGOS    = [{v:'astar',l:'⭐ A*'},{v:'ucs',l:'💰 UCS'},{v:'bfs',l:'🌊 BFS'},{v:'dfs',l:'🔦 DFS'}]
const PROFILES = [{v:'staff',l:'🩺 Staff'},{v:'emergency',l:'🚨 Emergency'},{v:'visitor',l:'👤 Visitor'},{v:'patient',l:'♿ Patient'}]
const DEMOS    = [
  {l:'🌐 ICU',      q:'Take me to the ICU please'},
  {l:'🌐 Pharmacy', q:'Where is the pharmacy?'},
  {l:'🇮🇳 ICU కి',  q:'ICU కి తీసుకెళ్ళండి'},
  {l:'🇮🇳 గుండె',  q:'నాకు గుండె నొప్పి వస్తోంది సహాయం'},
  {l:'🇮🇳 ICU ले',  q:'आईसीयू ले जाओ जल्दी'},
  {l:'🚨 Emergency', q:'Emergency! bleeding help now'},
]

const urgStyle = {CRITICAL:'urg-critical',HIGH:'urg-high',NORMAL:'urg-normal'}

export default function Navigate() {
  const [nodes, setNodes]   = useState([])
  const [algo, setAlgo]     = useState('astar')
  const [prof, setProf]     = useState('staff')
  const [start, setStart]   = useState('ENTRANCE_MAIN')
  const [goal, setGoal]     = useState('Node_302_ICU_Tower')
  const [sr, setSr]         = useState(null)
  const [csp, setCsp]       = useState(null)
  const [query, setQuery]   = useState('')
  const [nlp, setNlp]       = useState(null)
  const [nlpLoading, setNlpLoading] = useState(false)
  const [srLoading, setSrLoading]   = useState(false)

  useEffect(()=>{ getNodes().then(r=>setNodes(r.data)) },[])

  const doSearch = async () => {
    setSrLoading(true); setSr(null); setCsp(null)
    try {
      const r = await runSearch({algorithm:algo, profile:prof, start, goal})
      setSr(r.data)
      if (r.data.path?.length) {
        const c = await validateCSP({path:r.data.path, profile:prof})
        setCsp(c.data)
      }
    } catch(e) { alert('Search error: '+e.message) }
    setSrLoading(false)
  }

  const doNLP = async (q = query) => {
    if (!q.trim()) return
    setNlpLoading(true); setNlp(null)
    try {
      const r = await parseNLP({query:q, use_llm:false})
      setNlp(r.data)
      // Auto-run route if target found
      if (r.data.ready_for_routing && r.data.target_node) {
        const urgLvl = r.data.urgency?.level
        const ap = urgLvl==='CRITICAL' ? 'emergency' : 'staff'
        const sr2 = await runSearch({algorithm:'astar', profile:ap,
                                     start:'ENTRANCE_MAIN', goal:r.data.target_node})
        setSr(sr2.data)
      }
    } catch(e) { alert('NLP error: '+e.message) }
    setNlpLoading(false)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          🗺️ Navigate
          <span className="badge badge-co1">CO1</span>
          <span className="badge badge-co2">CO2</span>
        </div>
        <div className="page-sub">PEAS Agent · Graph Search · CSP Constraints · Multilingual NLP</div>
      </div>

      {/* PEAS explainer */}
      <details style={{marginBottom:16}}>
        <summary>CO1 — PEAS Agent Model & Environment Analysis</summary>
        <div className="four-col" style={{display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginTop:12}}>
          {[
            {l:'Performance 🏆', items:['Shortest path','Min travel time','CSP satisfied','Urgency routing']},
            {l:'Environment 🏥', items:['41-node graph','52 edges','Stochastic occupancy','Multi-floor']},
            {l:'Actuators ⚙️',   items:['Route display','NLP output','CSP alerts','Urgency badge']},
            {l:'Sensors 👁️',    items:['Voice input','Text query (3 langs)','Profile selector']},
          ].map(({l,items})=>(
            <div className="card card-sm" key={l} style={{margin:0}}>
              <div style={{fontSize:'.72rem',fontWeight:800,color:'#1d4ed8',
                letterSpacing:'.5px',textTransform:'uppercase',marginBottom:8}}>{l}</div>
              {items.map(i=><span key={i} className="chip">{i}</span>)}
            </div>
          ))}
        </div>
      </details>

      <div className="two-col">
        {/* LEFT — Search */}
        <div>
          <div className="section-label">🧠 AI Graph Search Engine</div>
          <div className="card card-sm">
            <div className="form-row form-2">
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
            <button className="btn btn-primary btn-full" style={{marginTop:12}}
              onClick={doSearch} disabled={srLoading}>
              {srLoading?'⏳ Running…':'▶ Run Search'}
            </button>
          </div>

          {/* Interactive graph map */}
          <div className="section-label" style={{display:'flex',alignItems:'center',justifyContent:'space-between'}}>
            <span>🗺️ Interactive Hospital Graph</span>
            <ExportPDFButton result={sr} algo={algo} prof={prof} start={start} goal={goal} nlp={nlp} />
          </div>

          {srLoading
            ? <GraphSkeleton message={`${algo.toUpperCase()} searching ${prof} profile…`} />
            : <GraphMap profile={prof} path={sr?.path || []} start={start} goal={goal} />
          }

          {/* Path metrics below map */}
          {sr?.path?.length > 0 && (
            <div className="metrics-row metrics-3" style={{marginTop:12}}>
              {[
                {val:sr.path.length,          lbl:'Hops'},
                {val:`${sr.cost?.toFixed(0)}s`, lbl:'Travel Time'},
                {val:sr.stats?.expansions??'—', lbl:'Nodes Expanded'},
              ].map(({val,lbl})=>(
                <div className="metric-card" key={lbl}>
                  <div className="metric-val" style={{fontSize:'1.3rem'}}>{val}</div>
                  <div className="metric-lbl">{lbl}</div>
                </div>
              ))}
            </div>
          )}
          {sr && !sr.path?.length && (
            <div className="alert alert-error" style={{marginTop:8}}>
              ❌ No path found — this profile cannot access that node.
            </div>
          )}

          {/* CSP */}
          <div className="section-label">⚠️ CSP Constraint Alerts · CO3</div>
          {csp ? (
            csp.overall_valid
              ? <div className="alert alert-success">✅ All CSP constraints satisfied — path is valid for <strong>{prof}</strong> profile.</div>
              : csp.trace?.filter(t=>t.result==='FAIL').slice(0,3).map((f,i)=>(
                  <div className="alert alert-error" key={i}>⚠️ {f.reason}</div>
                ))
          ) : (
            <>
              <div className="alert alert-info">ℹ️ Historic Wing — Stair-heavy: Lab_101 ↔ Stairs_A</div>
              <div className="alert alert-warning">⚠️ Visitor profile → ICU & Labs access-denied; edges pruned by CSP.</div>
            </>
          )}
        </div>

        {/* RIGHT — NLP */}
        <div>
          <div className="section-label">🎙️ Voice Input (Web Speech API) · CO6</div>
          <MicWidget onTranscript={q=>{ setQuery(q); doNLP(q) }} />

          <div className="section-label">💬 Query Input · CO6</div>
          <div style={{display:'flex', gap:8, marginBottom:10}}>
            <input className="form-control" placeholder='E.g. "ICU le jao" · "ICU కి తీసుకెళ్ళండి" · "आईसीयू ले जाओ"…'
              value={query} onChange={e=>setQuery(e.target.value)}
              onKeyDown={e=>e.key==='Enter'&&doNLP()} />
            <button className="btn btn-primary" onClick={()=>doNLP()} disabled={nlpLoading}>
              {nlpLoading?'…':'➤'}
            </button>
          </div>

          <div style={{display:'flex', gap:6, flexWrap:'wrap', marginBottom:12}}>
            {DEMOS.map(({l,q})=>(
              <button key={l} className="btn btn-secondary"
                style={{fontSize:'.72rem', padding:'4px 10px'}}
                onClick={()=>{ setQuery(q); doNLP(q) }}>{l}</button>
            ))}
          </div>

          {/* NLP Result */}
          <div className="section-label">🔬 NLP Pipeline · CO6</div>
          {nlp ? (
            <>
              <div className="pipe">
                {[
                  {lbl:'① Language', val:{te:'🇮🇳 Telugu',hi:'🇮🇳 Hindi',en:'🌐 English'}[nlp.language]||nlp.language, sub:'Detect'},
                  {lbl:'② Intent',   val:(nlp.target_friendly||'Unknown').slice(0,18), sub:'Extract'},
                  {lbl:'③ Urgency',  val:`${{'CRITICAL':'🚨','HIGH':'⚠️','NORMAL':'✅'}[nlp.urgency?.level]} ${nlp.urgency?.level}`, sub:'Scan'},
                  {lbl:'④ Route',    val:'A*', sub:nlp.ready_for_routing?'✅ Done':'—'},
                ].map(s=>(
                  <div className="pipe-stage active" key={s.lbl}>
                    <div className="pipe-lbl">{s.lbl}</div>
                    <div className="pipe-val" style={{fontSize:'.76rem'}}>{s.val}</div>
                    <div className="pipe-sub">{s.sub}</div>
                  </div>
                ))}
              </div>

              <div className="result-card">
                <div style={{display:'flex', justifyContent:'space-between', marginBottom:10}}>
                  <div>
                    <div style={{fontSize:'.62rem',fontWeight:700,letterSpacing:'.6px',
                      textTransform:'uppercase',color:'#6b7280',marginBottom:2}}>Destination</div>
                    <div className="result-dest">{nlp.target_friendly||'❓ Unknown'}</div>
                    <div className="result-node">{nlp.target_node||'—'}</div>
                  </div>
                  <div style={{textAlign:'right'}}>
                    <div style={{fontSize:'.62rem',fontWeight:700,letterSpacing:'.6px',
                      textTransform:'uppercase',color:'#6b7280',marginBottom:2}}>Language</div>
                    <span style={{fontWeight:700,color:'#1d4ed8'}}>
                      {{te:'🇮🇳 Telugu',hi:'🇮🇳 Hindi',en:'🌐 English'}[nlp.language]||nlp.language}
                    </span>
                  </div>
                </div>
                <div className={`urg ${urgStyle[nlp.urgency?.level]||'urg-normal'}`} style={{marginBottom:8}}>
                  {{'CRITICAL':'🚨','HIGH':'⚠️','NORMAL':'✅'}[nlp.urgency?.level]} {nlp.urgency?.level}
                  <span style={{fontWeight:400,fontSize:'.75rem',marginLeft:6}}>{nlp.urgency?.routing_hint}</span>
                </div>
                {sr?.path?.length > 0 && nlp.ready_for_routing && (
                  <div style={{background:'#f0fdf4',border:'1px solid #bbf7d0',borderRadius:8,
                    padding:'8px 12px',display:'flex',alignItems:'center',gap:10}}>
                    <span>🗺️</span>
                    <div>
                      <div style={{fontSize:'.82rem',fontWeight:700,color:'#15803d'}}>
                        {sr.path.length} hops · {sr.cost?.toFixed(0)}s
                      </div>
                      <div style={{fontSize:'.68rem',color:'#6b7280'}}>
                        {sr.path.slice(0,3).join(' → ')}{sr.path.length>3?' …':''}
                      </div>
                    </div>
                    <span style={{marginLeft:'auto',fontSize:'.68rem',color:'#15803d',fontWeight:700}}>✅ Routed</span>
                  </div>
                )}
              </div>

              <details style={{marginTop:10}}>
                <summary>Full pipeline trace — how was this determined?</summary>
                <div style={{marginTop:8}}>
                  {nlp.pipeline_steps?.map((s,i)=>(
                    <div key={i} style={{padding:'6px 0',borderBottom:'1px solid #f3e8d8',fontSize:'.82rem'}}>
                      <strong>{s.stage}</strong> → <code>{s.output}</code>
                      <div style={{fontSize:'.72rem',color:'#6b7280'}}>{s.note}</div>
                    </div>
                  ))}
                </div>
              </details>
            </>
          ) : (
            <div className="empty-state">
              <div className="icon">🎙️</div>
              <p>Speak or type a query to begin<br/>
              Telugu · Hindi · English · Roman transliteration all supported</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// ── Mic widget ──────────────────────────────────────────────────────────────
function MicWidget({ onTranscript }) {
  const [lang, setLang] = useState('te-IN')
  const [going, setGoing] = useState(false)
  const [transcript, setTranscript] = useState('')
  const [status, setStatus] = useState('Click mic to speak · Chrome recommended')
  const [supported, setSupported] = useState(true)
  const recRef = useRef(null)

  useEffect(()=>{
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window))
      setSupported(false)
  },[])

  const toggle = () => {
    if (going) { recRef.current?.stop(); return }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const rec = new SR()
    rec.lang = lang; rec.interimResults = true; rec.continuous = false
    recRef.current = rec

    rec.onstart = () => { setGoing(true); setTranscript(''); setStatus('🔴 Listening… speak now') }
    rec.onresult = (e) => {
      let final='', tmp=''
      for(let i=e.resultIndex;i<e.results.length;i++)
        e.results[i].isFinal ? final+=e.results[i][0].transcript : tmp+=e.results[i][0].transcript
      setTranscript(final||tmp)
    }
    rec.onend = () => {
      setGoing(false)
      setStatus('✅ Done')
      if (transcript) onTranscript(transcript)
    }
    rec.onerror = (e) => { setGoing(false); setStatus('⚠️ Error: '+e.error) }
    rec.start()
  }

  return (
    <div className="mic-panel" style={{marginBottom:12}}>
      <div className="lang-tabs">
        {[['en-US','🌐 English'],['te-IN','🇮🇳 Telugu'],['hi-IN','🇮🇳 Hindi']].map(([l,lbl])=>(
          <button key={l} className={`lang-tab${lang===l?' active':''}`} onClick={()=>setLang(l)}>{lbl}</button>
        ))}
      </div>
      <div style={{display:'flex', alignItems:'center', gap:12}}>
        <button onClick={toggle} disabled={!supported}
          style={{width:46,height:46,borderRadius:'50%',border:'none',cursor:'pointer',fontSize:'1.2rem',
            background:going?'linear-gradient(135deg,#dc2626,#b91c1c)':'linear-gradient(135deg,#b45309,#92400e)',
            color:'#fff', flexShrink:0, boxShadow:'0 2px 8px rgba(180,83,9,.3)',
            animation:going?'ring 1.1s ease-in-out infinite':'none'}}>
          {going ? '⏹' : '🎤'}
        </button>
        <div style={{flex:1}}>
          <div style={{fontSize:'.7rem',color:'#7a5c38',marginBottom:4}}>{status}</div>
          <div style={{display:'flex',gap:2,height:22,alignItems:'flex-end'}}>
            {Array(8).fill(0).map((_,i)=>(
              <div key={i} style={{flex:1,borderRadius:2,background:going?'#b45309':'#e8d9c4',
                height:going?`${Math.random()*18+4}px`:'5px',transition:'height .1s'}} />
            ))}
          </div>
        </div>
      </div>
      {transcript && (
        <div style={{marginTop:8,padding:'7px 10px',borderRadius:8,background:'#fef3c7',
          border:'1px solid #fcd34d',fontSize:'.82rem',color:'#111827'}}>
          {transcript}
        </div>
      )}
      {!supported && <div className="alert alert-error" style={{marginTop:8}}>⚠️ Web Speech API not available — use Chrome</div>}
      <style>{`@keyframes ring{0%{box-shadow:0 0 0 0 rgba(220,38,38,.65);}70%{box-shadow:0 0 0 12px rgba(220,38,38,0);}100%{box-shadow:0 0 0 0 rgba(220,38,38,0);}}`}</style>
    </div>
  )
}
