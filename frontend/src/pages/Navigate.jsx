import { useState, useEffect, useRef } from 'react'
import { Link } from 'react-router-dom'
import { getGraph, runSearch, parseNLP, validateCSP } from '../api'
import GraphMap from '../components/GraphMap'
import GraphSkeleton from '../components/GraphSkeleton'
import ExportPDFButton from '../components/ExportPDF'
import AIInsight from '../components/AIInsight'
import { useAI } from '../context/AIContext'

const DEMOS = [
  { l:'🌐 ICU',        q:'Take me to the ICU please'          },
  { l:'🌐 Pharmacy',   q:'Where is the pharmacy?'             },
  { l:'🌐 Ear pain',   q:'I have ear pain'                    },
  { l:'🌐 Knee pain',  q:'My knee is hurting badly'           },
  { l:'🇮🇳 ICU కి',   q:'ICU కి తీసుకెళ్ళండి'              },
  { l:'🇮🇳 చెవి నొప్పి', q:'నాకు చెవి నొప్పి వస్తోంది'    },
  { l:'🇮🇳 గుండె',    q:'నాకు గుండె నొప్పి వస్తోంది సహాయం' },
  { l:'🇮🇳 ICU ले',   q:'आईसीयू ले जाओ जल्दी'               },
  { l:'🇮🇳 कान दर्द', q:'मेरे कान में दर्द है'               },
  { l:'🚨 Emergency',  q:'Emergency! bleeding help now'       },
]
const URG_CLS = { CRITICAL:'urg-critical', HIGH:'urg-high', NORMAL:'urg-normal' }
const URG_EMO = { CRITICAL:'🚨', HIGH:'⚠️', NORMAL:'✅' }
const LANG_LABEL = { te:'🇮🇳 Telugu', hi:'🇮🇳 Hindi', en:'🌐 English' }

// NLP flow states
const FLOW = { IDLE:'idle', PARSED:'parsed', LOCATING:'locating', ROUTING:'routing', DONE:'done' }

export default function Navigate() {
  // Global AI context
  const globalAI = useAI()
  const { hospital, hospitalInfo } = globalAI

  // Graph data (all nodes with metadata)
  const [graphData, setGraphData] = useState(null)

  // NLP flow
  const [query, setQuery]     = useState('')
  const [nlp, setNlp]         = useState(null)
  const [flow, setFlow]       = useState(FLOW.IDLE)
  const [nlpLoading, setNlpLoading] = useState(false)

  // "Where are you?" picker
  const [selectedFloor, setSelectedFloor] = useState(0)
  const [userNode, setUserNode]           = useState('')

  // Search result
  const [sr, setSr]       = useState(null)
  const [csp, setCsp]     = useState(null)
  const [srLoading, setSrLoading] = useState(false)
  const [navAiTrigger, setNavAiTrigger] = useState(0)

  // Manual search state
  const [activeTab, setActiveTab] = useState('nlp')
  const [algo, setAlgo]   = useState('astar')
  const [prof, setProf]   = useState('staff')
  const [mStart, setMStart] = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [mGoal, setMGoal]   = useState(hospitalInfo?.defaultGoal  || 'Node_302_ICU_Tower')
  const [mSr, setMSr]       = useState(null)

  // LLM
  const [provider, setProvider]     = useState('claude')
  const [claudeKey, setClaudeKey]   = useState('')
  const [geminiKey, setGeminiKey]   = useState('')
  const [llmModel, setLlmModel]     = useState('claude-3-haiku-20240307')
  const [llmEnabled, setLlmEnabled] = useState(false)
  const [showLLM, setShowLLM]       = useState(false)

  // Load full graph data once (for floor/node picker)
  useEffect(() => {
    getGraph('staff', hospital).then(r => {
      setGraphData(r.data)
      setMStart(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
      setMGoal(hospitalInfo?.defaultGoal   || 'Node_302_ICU_Tower')
    }).catch(() => {})
  }, [hospital])

  // Derived: unique floors sorted
  const floors = graphData
    ? [...new Set(graphData.nodes.map(n => n.floor))].sort((a,b) => a-b)
    : []

  // Derived: nodes on selected floor (exclude corridors/stairs/elevators for picker)
  const nodesOnFloor = graphData
    ? graphData.nodes.filter(n =>
        n.floor === selectedFloor &&
        !['corridor','stairs','elevator'].includes(n.type)
      )
    : []

  // Auto-select first node when floor changes
  useEffect(() => {
    if (nodesOnFloor.length > 0) setUserNode(nodesOnFloor[0].id)
  }, [selectedFloor, graphData])

  // ── Step 1: Parse NLP ────────────────────────────────────────────────────
  const doNLP = async (q = query) => {
    if (!q.trim()) return
    setNlpLoading(true)
    setNlp(null); setSr(null); setCsp(null); setFlow(FLOW.IDLE)
    try {
      // Prefer global AI key, fall back to local provider key
      const localKey = provider === 'claude' ? claudeKey : geminiKey
      const useGlobal = globalAI.isReady
      const finalKey      = useGlobal ? globalAI.apiKey   : localKey
      const finalProvider = useGlobal ? globalAI.provider : provider
      const finalModel    = useGlobal ? globalAI.model    : llmModel
      const useLLM = (llmEnabled && !!localKey.trim()) || useGlobal

      const r = await parseNLP({
        query: q,
        use_llm: useLLM,
        api_key: finalKey,
        provider: finalProvider,
        model: finalModel,
        hospital,
      })
      setNlp(r.data)
      setFlow(r.data.ready_for_routing ? FLOW.LOCATING : FLOW.PARSED)
    } catch(e) { alert(e.message) }
    setNlpLoading(false)
  }

  // ── Step 2: Route from user location ────────────────────────────────────
  const doRoute = async () => {
    if (!userNode || !nlp?.target_node) return
    setSrLoading(true); setSr(null); setCsp(null); setFlow(FLOW.ROUTING)
    try {
      const urgLvl = nlp.urgency?.level
      const ap = urgLvl === 'CRITICAL' ? 'emergency' : 'staff'
      const r = await runSearch({
        algorithm: urgLvl === 'CRITICAL' ? 'astar' : urgLvl === 'HIGH' ? 'ucs' : 'astar',
        profile: ap,
        start: userNode,
        goal: nlp.target_node,
        hospital,
      })
      setSr(r.data)
      setFlow(FLOW.DONE)
      setNavAiTrigger(t => t + 1)
      if (r.data.path?.length) {
        const c = await validateCSP({ path: r.data.path, profile: ap, hospital })
        setCsp(c.data)
      }
    } catch(e) { alert(e.message) }
    setSrLoading(false)
  }

  // ── Manual search ────────────────────────────────────────────────────────
  const doManual = async () => {
    setSrLoading(true); setMSr(null)
    try {
      const r = await runSearch({ algorithm:algo, profile:prof, start:mStart, goal:mGoal, hospital })
      setMSr(r.data)
    } catch(e) { alert(e.message) }
    setSrLoading(false)
  }

  const reset = () => {
    setNlp(null); setSr(null); setCsp(null)
    setFlow(FLOW.IDLE); setQuery('')
  }

  const loading = nlpLoading || srLoading
  const activePath = activeTab === 'nlp' ? sr?.path : mSr?.path
  const activeStart = activeTab === 'nlp' ? userNode : mStart
  const activeGoal  = activeTab === 'nlp' ? nlp?.target_node : mGoal
  const activeProf  = activeTab === 'nlp'
    ? (nlp?.urgency?.level === 'CRITICAL' ? 'emergency' : 'staff')
    : prof
  const pathOnly = activeTab === 'nlp' && flow === FLOW.DONE && !!sr?.path?.length

  // All nodes list (for manual dropdowns)
  const allNodes = graphData?.nodes || []

  return (
    <div>
      <div style={{ marginBottom:16 }}>
        <Link to="/" style={{ fontSize:'.8rem', color:'#6b7280', textDecoration:'none' }}>← Home</Link>
      </div>

      <div style={{ marginBottom:20 }}>
        <h1 style={{ fontSize:'1.6rem', fontWeight:900, color:'#111827', letterSpacing:'-.5px', marginBottom:4 }}>
          🎙️ Smart Navigation
        </h1>
        <p style={{ fontSize:'.88rem', color:'#374151' }}>
          Speak or type your symptoms — the AI routes you to the right department
        </p>
      </div>

      {/* ── Tab switcher ── */}
      <div style={{ display:'flex', gap:6, marginBottom:16 }}>
        {[['nlp','🎙️ Voice & Text'], ['manual','⚙️ Manual Search']].map(([v,l]) => (
          <button key={v} onClick={() => setActiveTab(v)}
            style={{
              padding:'7px 18px', borderRadius:8, border:'1px solid',
              fontWeight:600, fontSize:'.82rem', cursor:'pointer', fontFamily:'inherit',
              background: activeTab===v ? '#b45309' : '#fff8f0',
              color:      activeTab===v ? '#fff'   : '#5c4a30',
              borderColor: activeTab===v ? '#b45309' : '#e8d9c4',
            }}>
            {l}
          </button>
        ))}
      </div>

      {/* ════════════════════════════════════════════════════════════
          NLP TAB
      ════════════════════════════════════════════════════════════ */}
      {activeTab === 'nlp' && (
        <>
          {/* ── STEP 1: Input ── */}
          <div style={{
            background:'#fffdf9', border:'1px solid #e8d9c4', borderRadius:16,
            padding:'20px 24px', marginBottom:16, boxShadow:'0 2px 12px rgba(92,74,48,.07)',
          }}>
            <div style={{ fontWeight:700, fontSize:'.82rem', color:'#374151', marginBottom:10 }}>
              Step 1 — Tell us what's wrong or where you need to go
            </div>

            <MicWidget onTranscript={q => { setQuery(q); doNLP(q) }} />

            <div style={{ display:'flex', gap:8, margin:'12px 0 10px' }}>
              <input
                style={{
                  flex:1, padding:'10px 14px', border:'1px solid #ddd0bb',
                  borderRadius:8, background:'#fff8f0', color:'#111827',
                  fontSize:'.9rem', fontFamily:'inherit', outline:'none',
                }}
                placeholder='"ear pain" · "I have chest pain" · "ICU కి" · "कान दर्द"…'
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && doNLP()}
              />
              <button className="btn btn-primary btn-lg"
                onClick={() => doNLP()} disabled={nlpLoading}>
                {nlpLoading ? '⏳' : '➤ Send'}
              </button>
              {(nlp || sr) && (
                <button className="btn btn-secondary" onClick={reset}>↺ Reset</button>
              )}
            </div>

            {/* Demo chips */}
            <div style={{ display:'flex', gap:5, flexWrap:'wrap' }}>
              {DEMOS.map(({ l, q }) => (
                <button key={l} className="btn btn-secondary"
                  style={{ fontSize:'.7rem', padding:'3px 10px' }}
                  onClick={() => { setQuery(q); doNLP(q) }}>
                  {l}
                </button>
              ))}
            </div>

            {/* LLM provider */}
            <div style={{ borderTop:'1px solid #e8d9c4', paddingTop:10, marginTop:12 }}>
              <button onClick={() => setShowLLM(v => !v)}
                style={{ background:'none', border:'none', cursor:'pointer',
                  fontSize:'.75rem', fontWeight:700, color:'#b45309', fontFamily:'inherit' }}>
                🤖 AI Provider {showLLM ? '▲' : '▼'}
                <span style={{ fontSize:'.65rem', fontWeight:400, color:'#9ca3af', marginLeft:6 }}>
                  {llmEnabled ? `(${provider} active)` : '(rule-based)'}
                </span>
              </button>
              {showLLM && (
                <div style={{ marginTop:10, background:'#fff8f0', border:'1px solid #e8d9c4',
                  borderRadius:10, padding:'12px 14px' }}>
                  <div style={{ display:'flex', gap:12, marginBottom:10 }}>
                    {[['claude','⚡ Claude'],['gemini','✨ Gemini']].map(([v,l]) => (
                      <label key={v} style={{ display:'flex', alignItems:'center', gap:5,
                        cursor:'pointer', fontSize:'.82rem', fontWeight:600 }}>
                        <input type="radio" name="provider" value={v}
                          checked={provider===v} onChange={()=>setProvider(v)}
                          style={{ accentColor:'#b45309' }} />
                        {l}
                      </label>
                    ))}
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 150px auto', gap:8, alignItems:'end' }}>
                    <input type="password" className="form-control"
                      placeholder={provider==='claude' ? 'sk-ant-api03-…' : 'AIzaSy…'}
                      value={provider==='claude' ? claudeKey : geminiKey}
                      onChange={e => provider==='claude' ? setClaudeKey(e.target.value) : setGeminiKey(e.target.value)} />
                    <select className="form-control" value={llmModel} onChange={e=>setLlmModel(e.target.value)}>
                      {provider==='claude'
                        ? [['claude-3-haiku-20240307','Haiku 3'],['claude-3-5-haiku-20241022','Haiku 3.5'],['claude-3-5-sonnet-20241022','Sonnet 3.5']]
                            .map(([v,l])=><option key={v} value={v}>{l}</option>)
                        : [['gemini-1.5-flash','Flash 1.5'],['gemini-1.5-pro','Pro 1.5']]
                            .map(([v,l])=><option key={v} value={v}>{l}</option>)
                      }
                    </select>
                    <div style={{ display:'flex', alignItems:'center', gap:6 }}>
                      <label className="toggle">
                        <input type="checkbox" checked={llmEnabled} onChange={e=>setLlmEnabled(e.target.checked)} />
                        <span className="toggle-slider" />
                      </label>
                      <span style={{ fontSize:'.78rem', fontWeight:600 }}>On</span>
                    </div>
                  </div>
                  <div style={{ marginTop:6, fontSize:'.7rem', color: llmEnabled && (provider==='claude'?claudeKey:geminiKey) ? '#15803d' : '#6b7280' }}>
                    {llmEnabled && (provider==='claude'?claudeKey:geminiKey) ? `✅ ${provider} NLP active` : llmEnabled ? '⚠️ Paste API key above' : 'Rule-based NLP active'}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* ── STEP 2: NLP Result + Where are you? ── */}
          {nlp && flow !== FLOW.IDLE && (
            <div style={{
              background:'linear-gradient(135deg,#fef3c7,#fffdf9)',
              border:'1px solid #fcd34d', borderRadius:14,
              padding:'20px 24px', marginBottom:16,
            }}>
              {/* Destination identified */}
              <div style={{ display:'flex', alignItems:'flex-start', justifyContent:'space-between', marginBottom:14 }}>
                <div>
                  <div style={{ fontSize:'.62rem', fontWeight:700, letterSpacing:'.6px',
                    textTransform:'uppercase', color:'#6b7280', marginBottom:3 }}>
                    🎯 Destination Identified
                  </div>
                  <div style={{ fontSize:'1.3rem', fontWeight:900, color:'#111827' }}>
                    {nlp.target_friendly || '❓ Unknown'}
                  </div>
                  <div style={{ fontSize:'.72rem', color:'#6b7280', fontFamily:'monospace' }}>
                    {nlp.target_node}
                  </div>
                </div>
                <div style={{ display:'flex', flexDirection:'column', alignItems:'flex-end', gap:6 }}>
                  <span style={{ fontSize:'.8rem', fontWeight:700 }}>
                    {LANG_LABEL[nlp.language] || nlp.language}
                  </span>
                  <span className={`urg ${URG_CLS[nlp.urgency?.level]||'urg-normal'}`}>
                    {URG_EMO[nlp.urgency?.level]} {nlp.urgency?.level}
                  </span>
                </div>
              </div>

              {/* NLP pipe */}
              <div className="pipe" style={{ marginBottom:16 }}>
                {[
                  { lbl:'① Language', val: LANG_LABEL[nlp.language]||nlp.language },
                  { lbl:'② Intent',   val: (nlp.target_friendly||'Unknown').slice(0,18) },
                  { lbl:'③ Urgency',  val: `${URG_EMO[nlp.urgency?.level]} ${nlp.urgency?.level}` },
                  { lbl:'④ Route',    val: flow===FLOW.DONE ? 'A* ✅' : 'Pending…' },
                ].map(s => (
                  <div className={`pipe-stage ${flow===FLOW.DONE||s.lbl!=='④ Route'?'active':''}`} key={s.lbl}>
                    <div className="pipe-lbl">{s.lbl}</div>
                    <div className="pipe-val" style={{fontSize:'.76rem'}}>{s.val}</div>
                  </div>
                ))}
              </div>

              {/* ── STEP 2: Where are you? ── */}
              {(flow === FLOW.LOCATING || flow === FLOW.ROUTING) && (
                <div style={{
                  background:'#fff', border:'2px solid #b45309', borderRadius:12,
                  padding:'18px 20px',
                }}>
                  <div style={{ fontWeight:800, fontSize:'1rem', color:'#111827', marginBottom:4 }}>
                    📍 Where are you right now?
                  </div>
                  <div style={{ fontSize:'.8rem', color:'#6b7280', marginBottom:14 }}>
                    Select your current floor and location so we can route you there
                  </div>

                  <div style={{ display:'grid', gridTemplateColumns:'140px 1fr', gap:12, marginBottom:14 }}>
                    <div className="form-group" style={{ margin:0 }}>
                      <label className="form-label">📐 Floor</label>
                      <select className="form-control"
                        value={selectedFloor}
                        onChange={e => setSelectedFloor(Number(e.target.value))}>
                        {floors.map(f => (
                          <option key={f} value={f}>Floor {f}{f===0?' (Ground)':''}</option>
                        ))}
                      </select>
                    </div>
                    <div className="form-group" style={{ margin:0 }}>
                      <label className="form-label">🏥 Your Location</label>
                      <select className="form-control"
                        value={userNode}
                        onChange={e => setUserNode(e.target.value)}>
                        {nodesOnFloor.length > 0
                          ? nodesOnFloor.map(n => (
                              <option key={n.id} value={n.id}>{n.label}</option>
                            ))
                          : <option value="">— No rooms on this floor —</option>
                        }
                      </select>
                    </div>
                  </div>

                  <button
                    className="btn btn-primary btn-full btn-lg"
                    onClick={doRoute}
                    disabled={!userNode || srLoading}>
                    {srLoading ? '⏳ Finding your route…' : '🗺️ Show My Route'}
                  </button>
                </div>
              )}

              {/* ── STEP 3: Route result ── */}
              {flow === FLOW.DONE && sr?.path?.length > 0 && (
                <div style={{
                  background:'#f0fdf4', border:'1px solid #bbf7d0',
                  borderRadius:10, padding:'14px 16px',
                }}>
                  <div style={{ fontWeight:800, color:'#15803d', marginBottom:8, fontSize:'.95rem' }}>
                    ✅ Route Found — {sr.path.length} hops · {sr.cost?.toFixed(0)}s
                  </div>
                  <div style={{ fontSize:'.8rem', color:'#374151', lineHeight:2, flexWrap:'wrap', display:'flex', alignItems:'center', gap:4 }}>
                    {sr.path.map((n,i) => (
                      <span key={n} style={{ display:'inline-flex', alignItems:'center', gap:4 }}>
                        <span style={{
                          background: i===0?'#fef3c7' : i===sr.path.length-1?'#fef2f2' : '#eff6ff',
                          border: `1px solid ${i===0?'#fcd34d':i===sr.path.length-1?'#fecaca':'#bfdbfe'}`,
                          borderRadius:6, padding:'2px 8px', fontSize:'.75rem', fontWeight:700,
                          color: i===0?'#92400e':i===sr.path.length-1?'#991b1b':'#1d4ed8',
                        }}>
                          {i===0?'📍 ':i===sr.path.length-1?'🎯 ':''}{n.replace(/_/g,' ')}
                        </span>
                        {i<sr.path.length-1 && <span style={{color:'#9ca3af'}}>→</span>}
                      </span>
                    ))}
                  </div>
                  {csp && (
                    <div style={{ marginTop:8, fontSize:'.75rem',
                      color: csp.overall_valid ? '#15803d' : '#dc2626' }}>
                      {csp.overall_valid ? '✅ All access constraints satisfied' : '⚠️ Some constraints flagged — check with staff'}
                    </div>
                  )}
                  <AIInsight module="navigate" trigger={navAiTrigger}
                    context={{ query, destination:nlp?.target_friendly,
                      path:sr?.path||[], cost:sr?.cost||0,
                      urgency:nlp?.urgency?.level,
                      user_location:userNode }} />
                </div>
              )}
            </div>
          )}

          {/* ── Loading skeleton ── */}
          {loading && <GraphSkeleton message={
            nlpLoading ? 'Parsing your query…' : 'Finding your route…'
          } />}

          {/* ── Graph ── */}
          {!loading && (
            <>
              <div style={{ display:'flex', justifyContent:'space-between',
                alignItems:'center', marginBottom:8, flexWrap:'wrap', gap:8 }}>
                <div className="section-label" style={{ margin:0, border:'none', padding:0 }}>
                  🗺️ Hospital Graph {pathOnly ? '— Route View' : '— Full Map'}
                </div>
                <div style={{ display:'flex', gap:8 }}>
                  {pathOnly && (
                    <span style={{ fontSize:'.72rem', color:'#6b7280',
                      background:'#fef3c7', border:'1px solid #fcd34d',
                      borderRadius:6, padding:'3px 10px' }}>
                      Showing path only · other nodes faded
                    </span>
                  )}
                  <ExportPDFButton result={sr} algo="astar" prof={activeProf}
                    start={userNode} goal={nlp?.target_node||''} nlp={nlp} />
                </div>
              </div>
              <GraphMap
                profile={activeProf}
                path={activePath||[]}
                start={activeStart}
                goal={activeGoal}
                pathOnly={pathOnly}
                autoZoomPath={true}
              />
            </>
          )}
        </>
      )}

      {/* ════════════════════════════════════════════════════════════
          MANUAL TAB
      ════════════════════════════════════════════════════════════ */}
      {activeTab === 'manual' && (
        <>
          <div className="card">
            <div className="form-row form-2" style={{ marginBottom:12 }}>
              <div className="form-group">
                <label className="form-label">Algorithm</label>
                <select className="form-control" value={algo} onChange={e=>setAlgo(e.target.value)}>
                  {[{v:'astar',l:'⭐ A*'},{v:'ucs',l:'💰 UCS'},{v:'bfs',l:'🌊 BFS'},{v:'dfs',l:'🔦 DFS'}]
                    .map(a=><option key={a.v} value={a.v}>{a.l}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Profile</label>
                <select className="form-control" value={prof} onChange={e=>setProf(e.target.value)}>
                  {[{v:'staff',l:'🩺 Staff'},{v:'emergency',l:'🚨 Emergency'},{v:'visitor',l:'👤 Visitor'},{v:'patient',l:'♿ Patient'}]
                    .map(p=><option key={p.v} value={p.v}>{p.l}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Start Node</label>
                <select className="form-control" value={mStart} onChange={e=>setMStart(e.target.value)}>
                  {allNodes.map(n=><option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Goal Node</label>
                <select className="form-control" value={mGoal} onChange={e=>setMGoal(e.target.value)}>
                  {allNodes.map(n=><option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
            </div>
            <button className="btn btn-primary btn-full" onClick={doManual} disabled={srLoading}>
              {srLoading ? '⏳ Searching…' : '▶ Run Search'}
            </button>
            {mSr?.path?.length > 0 && (
              <div className="alert alert-success" style={{marginTop:10}}>
                ✅ {mSr.path.length} hops · {mSr.cost?.toFixed(0)}s · Expansions: {mSr.stats?.expansions}
              </div>
            )}
            {mSr && !mSr.path?.length && (
              <div className="alert alert-error" style={{marginTop:10}}>❌ No path found for this profile</div>
            )}
          </div>

          {srLoading
            ? <GraphSkeleton message={`${algo.toUpperCase()} searching…`} />
            : <GraphMap profile={prof} path={mSr?.path||[]} start={mStart} goal={mGoal} />
          }
          {mSr?.path?.length > 0 && (
            <div className="metrics-row metrics-3" style={{marginTop:12}}>
              {[
                {val:mSr.path.length, lbl:'Hops'},
                {val:`${mSr.cost?.toFixed(0)}s`, lbl:'Travel Time'},
                {val:mSr.stats?.expansions??'—', lbl:'Nodes Expanded'},
              ].map(({val,lbl})=>(
                <div className="metric-card" key={lbl}>
                  <div className="metric-val" style={{fontSize:'1.3rem'}}>{val}</div>
                  <div className="metric-lbl">{lbl}</div>
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

/* ── Mic Widget ─────────────────────────────────────────────────────────── */
function MicWidget({ onTranscript }) {
  const [lang, setLang]     = useState('te-IN')
  const [going, setGoing]   = useState(false)
  const [transcript, setTranscript] = useState('')
  const [status, setStatus] = useState('Click the mic to speak')
  const [supported, setSupported] = useState(true)
  const recRef = useRef(null)

  useEffect(() => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window))
      setSupported(false)
  }, [])

  const toggle = () => {
    if (going) { recRef.current?.stop(); return }
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition
    const rec = new SR()
    rec.lang = lang; rec.interimResults = true; rec.continuous = false
    recRef.current = rec
    let final = ''

    rec.onstart  = () => { setGoing(true); final=''; setTranscript(''); setStatus('🔴 Listening…') }
    rec.onresult = e => {
      let tmp=''
      for(let i=e.resultIndex;i<e.results.length;i++)
        e.results[i].isFinal ? final+=e.results[i][0].transcript : tmp+=e.results[i][0].transcript
      setTranscript(final||tmp)
    }
    rec.onend = () => { setGoing(false); setStatus('✅ Done'); if(final) onTranscript(final) }
    rec.onerror = e => { setGoing(false); setStatus('⚠️ Error: '+e.error) }
    rec.start()
  }

  return (
    <div style={{ background:'#fff8f0', border:'1px solid #e8d9c4', borderRadius:12, padding:'12px 14px', marginBottom:4 }}>
      <div style={{ display:'flex', gap:6, marginBottom:10 }}>
        {[['en-US','🌐 EN'],['te-IN','🇮🇳 TE'],['hi-IN','🇮🇳 HI']].map(([l,lbl]) => (
          <button key={l} onClick={()=>setLang(l)} style={{
            flex:1, padding:'4px 0', borderRadius:7, cursor:'pointer',
            fontFamily:'inherit', fontWeight:700, fontSize:'.72rem', border:'1px solid',
            background: lang===l?'#fef3c7':'#fff8f0',
            color: lang===l?'#92400e':'#a8906e',
            borderColor: lang===l?'#fcd34d':'#e8d9c4',
          }}>{lbl}</button>
        ))}
      </div>
      <div style={{ display:'flex', alignItems:'center', gap:12 }}>
        <button onClick={toggle} disabled={!supported} style={{
          width:46, height:46, borderRadius:'50%', border:'none',
          cursor:supported?'pointer':'not-allowed', fontSize:'1.2rem', color:'#fff', flexShrink:0,
          background: going ? 'linear-gradient(135deg,#dc2626,#b91c1c)' : 'linear-gradient(135deg,#b45309,#92400e)',
          boxShadow:'0 2px 10px rgba(180,83,9,.35)',
          animation: going ? 'ring 1.1s ease-in-out infinite' : 'none',
        }}>{going?'⏹':'🎤'}</button>
        <div style={{ flex:1 }}>
          <div style={{ fontSize:'.7rem', color:'#7a5c38', marginBottom:5 }}>{status}</div>
          <div style={{ display:'flex', gap:2, height:20, alignItems:'flex-end' }}>
            {Array(10).fill(0).map((_,i) => (
              <div key={i} style={{
                flex:1, borderRadius:2,
                background: going?'#b45309':'#e8d9c4',
                height: going?`${Math.sin(i*.8)*8+12}px`:'4px',
                animation: going?`wave ${.4+i*.05}s ease-in-out infinite alternate`:'none',
              }}/>
            ))}
          </div>
        </div>
      </div>
      {transcript && (
        <div style={{ marginTop:8, padding:'6px 10px', borderRadius:8,
          background:'#fef3c7', border:'1px solid #fcd34d', fontSize:'.85rem', color:'#111827' }}>
          {transcript}
        </div>
      )}
      {!supported && <div className="alert alert-error" style={{marginTop:8}}>⚠️ Use Chrome/Edge for mic support</div>}
      <style>{`
        @keyframes ring{0%{box-shadow:0 0 0 0 rgba(220,38,38,.6);}70%{box-shadow:0 0 0 12px rgba(220,38,38,0);}100%{box-shadow:0 0 0 0 rgba(220,38,38,0);}}
        @keyframes wave{from{height:4px;}to{height:18px;}}
      `}</style>
    </div>
  )
}
