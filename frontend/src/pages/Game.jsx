import { useState, useEffect } from 'react'
import { runGame, runMCTS, getNodes } from '../api'
import AIInsight from '../components/AIInsight'
import { useAI } from '../context/AIContext'

const PROFILES = [{v:'emergency',l:'🚨 Emergency'},{v:'staff',l:'🩺 Staff'},{v:'visitor',l:'👤 Visitor'},{v:'patient',l:'♿ Patient'}]
const TIME_OF_DAYS = [{v:'morning',l:'🌅 Morning'}, {v:'afternoon',l:'☀️ Afternoon'}, {v:'evening',l:'🌆 Evening'}, {v:'night',l:'🌃 Night'}]

export default function Game() {
  const globalAI = useAI()
  const { hospital, hospitalInfo } = globalAI
  const [nodes, setNodes]   = useState([])
  const [start, setStart]   = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [goal, setGoal]     = useState(hospitalInfo?.defaultGoal  || 'Node_302_ICU_Tower')
  const [prof, setProf]     = useState('emergency')
  
  // Game Mode: minimax, mcts, or not_named_yet
  const [mode, setMode]     = useState('minimax')
  
  // Minimax parameters
  const [depth, setDepth]   = useState(3)
  const [ab, setAb]         = useState(true)

  // MCTS parameters
  const [numSims, setNumSims]       = useState(200)
  const [depthLimit, setDepthLimit] = useState(6)
  const [timeOfDay, setTimeOfDay]   = useState('morning')
  const [useLlm, setUseLlm]         = useState(false)

  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [aiTrigger, setAiTrigger] = useState(0)

  useEffect(()=>{ getNodes(hospital).then(r=>setNodes(r.data)) },[hospital])
  useEffect(()=>{ 
    setStart(hospitalInfo?.defaultStart||'ENTRANCE_MAIN')
    setGoal(hospitalInfo?.defaultGoal||'Node_302_ICU_Tower') 
    setResult(null)
  },[hospital, hospitalInfo])

  const doRun = async () => {
    setLoading(true); setResult(null)
    try {
      if (mode === 'minimax') {
        const r = await runGame({start, goal, profile:prof, depth, use_alpha_beta:ab, hospital})
        setResult(r.data)
      } else {
        const r = await runMCTS({
          start, 
          goal, 
          profile: prof, 
          num_simulations: numSims,
          depth_limit: depthLimit,
          time_of_day: timeOfDay,
          use_llm_value: useLlm,
          api_key: globalAI.apiKey,
          provider: globalAI.provider,
          model: globalAI.model,
          hospital
        })
        setResult(r.data)
      }
      setAiTrigger(t => t + 1)
    } catch(e) { alert('Game AI execution failed: '+e.message) }
    setLoading(false)
  }

  const isMcts = mode === 'mcts'

  return (
    <div>
      <div className="page-header">
        <div className="page-title">
          ♟️ Game AI <span className="badge badge-co4">CO4</span>
        </div>
        <div className="page-sub">Triage Priority Routing modeled as a Two-Player Zero-Sum Game</div>
      </div>

      {/* Mode Switcher */}
      <div style={{ display:'flex', gap:6, marginBottom:16, flexWrap: 'wrap' }}>
        {[
          ['minimax','♟️ Minimax + Alpha-Beta'], 
          ['mcts','🤖 AlphaZero MCTS']
        ].map(([v,l]) => (
          <button key={v} onClick={() => { setMode(v); setResult(null) }}
            style={{
              padding:'7px 18px', borderRadius:8, border:'1px solid',
              fontWeight:600, fontSize:'.82rem', cursor:'pointer', fontFamily:'inherit',
              background: mode===v ? '#b45309' : '#fff8f0',
              color:      mode===v ? '#fff'   : '#5c4a30',
              borderColor: mode===v ? '#b45309' : '#e8d9c4',
              transition: 'all 0.15s',
            }}>
            {l}
          </button>
        ))}
      </div>

      {/* Concept Alert */}
      <div className="alert alert-info" style={{marginBottom:16}}>
        <div>
          <strong>Game Framing:</strong> Adversarial triage search. &nbsp;
          <strong>MAX (Ambulance)</strong> aims to find the fastest path. &nbsp;
          <strong>MIN (Congestion Controller)</strong> simulates obstacles/congestion.
          {isMcts ? (
            <span style={{fontSize:'.8rem', display:'block', marginTop:4}}>
              💡 <strong>AlphaZero MCTS Mode:</strong> Bayesian Network occupancy probabilities act as search policies (priors). 
              An optional LLM acts as the value function evaluating terminal leaves.
            </span>
          ) : (
            <span style={{fontSize:'.8rem', display:'block', marginTop:4}}>
              💡 <strong>Minimax Mode:</strong> Alternates moves between MAX (triage node hop) and MIN (congestion increase), using Alpha-Beta pruning to discard suboptimal subtrees.
            </span>
          )}
        </div>
      </div>

      {/* Config Card */}
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

          {!isMcts ? (
            <div className="form-group">
              <label className="form-label">Search Depth ({depth} plies)</label>
              <input type="range" min={1} max={5} value={depth}
                onChange={e=>setDepth(Number(e.target.value))}
                style={{width:'100%',accentColor:'#b45309',marginTop:8}} />
            </div>
          ) : (
            <div className="form-group">
              <label className="form-label">Simulations ({numSims})</label>
              <input type="range" min={20} max={600} step={20} value={numSims}
                onChange={e=>setNumSims(Number(e.target.value))}
                style={{width:'100%',accentColor:'#b45309',marginTop:8}} />
            </div>
          )}
        </div>

        {/* Mode-specific advanced config row */}
        {isMcts ? (
          <div className="form-row form-3" style={{ marginTop: 14, borderTop: '1px solid #e8d9c4', paddingTop: 12 }}>
            <div className="form-group">
              <label className="form-label">Depth Limit ({depthLimit} steps)</label>
              <input type="range" min={2} max={12} value={depthLimit}
                onChange={e=>setDepthLimit(Number(e.target.value))}
                style={{width:'100%',accentColor:'#b45309',marginTop:8}} />
            </div>
            <div className="form-group">
              <label className="form-label">Bayes Prior TimeOfDay</label>
              <select className="form-control" value={timeOfDay} onChange={e=>setTimeOfDay(e.target.value)}>
                {TIME_OF_DAYS.map(t=><option key={t.v} value={t.v}>{t.l}</option>)}
              </select>
            </div>
            <div className="form-group" style={{ justifyContent: 'center' }}>
              <label className="toggle-row" style={{ marginTop: 14 }}>
                <label className="toggle">
                  <input type="checkbox" checked={useLlm} onChange={e=>setUseLlm(e.target.checked)} />
                  <span className="toggle-slider" />
                </label>
                <span className="toggle-label" style={{ fontSize: '.8rem' }}>🤖 LLM Value Guidance</span>
              </label>
            </div>
          </div>
        ) : null}

        {/* Warning about LLM keys if checked */}
        <div style={{display:'flex', alignItems:'center', gap:16, marginTop:12}}>
          {!isMcts && (
            <label className="toggle-row">
              <label className="toggle">
                <input type="checkbox" checked={ab} onChange={e=>setAb(e.target.checked)} />
                <span className="toggle-slider" />
              </label>
              <span className="toggle-label">Alpha-Beta Pruning</span>
            </label>
          )}
          <button className="btn btn-primary btn-full" onClick={doRun} disabled={loading}>
            {loading ? '⏳ Searching Tree…' : isMcts ? '▶ Run MCTS Game AI' : '▶ Run Minimax Game AI'}
          </button>
        </div>
      </div>

      {/* Result UI */}
      {loading && (
        <div style={{ marginTop: 24, textAlign: 'center', color: '#6b7280' }}>
          <div className="spinner" />
          <p style={{ marginTop: 10, fontSize: '.85rem' }}>Evaluating candidate branches...</p>
        </div>
      )}

      {!loading && result && (
        <>
          {/* Stats metrics */}
          <div className="metrics-row metrics-3" style={{margin:'16px 0'}}>
            {[
              {val:result.path?.length??'—', lbl:'Hops Found'},
              {val:`${result.cost?.toFixed(0)??'—'}s`, lbl:'Travel Cost (MAX Score)'},
              {val: isMcts ? (result.root_visits || result.stats?.num_simulations) : (result.nodes_evaluated || result.stats?.trace_steps), 
               lbl: isMcts ? 'Simulations Executed' : 'Nodes/Steps Evaluated'},
            ].map(({val,lbl})=>(
              <div className="metric-card" key={lbl}>
                <div className="metric-val">{val}</div>
                <div className="metric-lbl">{lbl}</div>
              </div>
            ))}
          </div>

          {/* Path Winner alert */}
          {result.path?.length > 0 && (
            <div className="alert alert-success">
              🎉 <strong>MAX Wins</strong> — Routing path: {result.path.join(' → ')}
            </div>
          )}

          {/* Pruning notification */}
          {!isMcts && result.prune_log !== undefined && (
            <div className="alert alert-info">
              ✂️ Alpha-beta pruned <strong>{result.prune_log.length}</strong> suboptimal subtrees
            </div>
          )}

          {/* AlphaZero Concept */}
          {isMcts && result.alphazero_note && (
            <div className="alert alert-info" style={{ display: 'block', lineHeight: 1.6 }}>
              🤖 <strong>AlphaZero Hybrid Architecture:</strong>
              <p style={{ fontSize: '.8rem', marginTop: 4 }}>{result.alphazero_note}</p>
            </div>
          )}

          {/* Tree summary note */}
          {result.explanation && (
            <div className="card card-sm" style={{ fontSize: '.84rem', lineHeight: 1.65, background: '#fffdf9' }}>
              <strong>Execution Insight:</strong> {result.explanation}
            </div>
          )}

          {/* MCTS UI - Root Children Branch Explorer */}
          {isMcts && result.children_summary?.length > 0 && (
            <>
              <div className="section-label">🌳 Root Branch Explorer (UCB Selection)</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Candidate Node</th>
                      <th>Action</th>
                      <th>Visits (N)</th>
                      <th>Mean Value (Q)</th>
                      <th>Prior Clearing Prob (P)</th>
                      <th>UCB1 Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.children_summary.map((c, i) => (
                      <tr key={i}>
                        <td><code>{c.node}</code></td>
                        <td>{c.action}</td>
                        <td style={{ fontWeight: 800 }}>{c.visits}</td>
                        <td style={{ color: c.Q >= 0 ? '#15803d' : '#dc2626' }}>{c.Q?.toFixed(2)}</td>
                        <td>{(c.prior * 100).toFixed(1)}%</td>
                        <td>{c.ucb === 999 ? '∞ (Unexplored)' : c.ucb}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* MCTS UI - Tree Convergence trace */}
          {isMcts && result.iteration_log?.length > 0 && (
            <>
              <div className="section-label">📈 Tree Convergence Steps</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead>
                    <tr>
                      <th>Sim #</th>
                      <th>Root Visits</th>
                      <th>Best Target candidate</th>
                      <th>Visits</th>
                      <th>Mean Q Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.iteration_log.map((it, i) => (
                      <tr key={i}>
                        <td>{it.iteration}</td>
                        <td>{it.root_visits}</td>
                        <td><code>{it.best_node}</code></td>
                        <td>{it.best_visits}</td>
                        <td>{it.best_Q}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* Minimax / Not Named Yet Trace Table */}
          {!isMcts && result.trace?.length > 0 && (
            <>
              <div className="section-label">🌳 Minimax Step Log (First 30 steps)</div>
              <div className="table-wrap">
                <table className="trace-table">
                  <thead>
                    <tr><th>Depth</th><th>Node</th><th>Player</th><th>Score</th><th>Action Details</th></tr>
                  </thead>
                  <tbody>
                    {result.trace.slice(0,30).map((t,i)=>(
                      <tr key={i}>
                        <td>{t.depth}</td>
                        <td><code>{t.node}</code></td>
                        <td style={{color:t.is_max?'#15803d':'#dc2626',fontWeight:700}}>
                          {t.is_max?'MAX ▲':'MIN ▼'}
                        </td>
                        <td>{t.score !== undefined && t.score !== null ? t.score.toFixed(2) : (t.child_val !== undefined ? t.child_val.toFixed(2) : '—')}</td>
                        <td style={{fontSize:'.72rem'}}>{t.note || t.move || 'Start evaluation'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          {/* AI explainability widget */}
          <AIInsight
            module={isMcts ? "mcts" : "game"}
            trigger={aiTrigger}
            context={isMcts ? {
              path: result.path,
              cost: result.cost,
              num_simulations: numSims,
              depth_limit: depthLimit,
              time_of_day: timeOfDay,
              llm_used: useLlm && globalAI.isReady
            } : {
              best_path: result.best_path,
              best_cost: result.best_cost,
              depth,
              pruned_branches: result.pruned_branches,
              nodes_evaluated: result.nodes_evaluated,
              alpha_beta: ab
            }}
          />

          {/* Traditional Academic panel */}
          <div className="section-label">♟️ Explainability Notes (CO4)</div>
          <div className="card card-sm" style={{fontSize:'.84rem',lineHeight:1.7}}>
            <p><strong>Minimax Game Theory:</strong> MAX tries to select the node sequence that minimizes total travel cost. MIN simulates congestion to maximize travel cost. When they alternate, they simulate adversarial routing conditions.</p>
            <p><strong>Heuristic Evaluation Function:</strong> <code>{'$f = -\\text{travel\\_cost} + \\text{urgency\\_bonus} - \\text{congestion\\_penalty}$'}</code>. Represents the utility score of reaching that state.</p>
            {isMcts ? (
              <p style={{ marginTop: 6 }}><strong>Monte Carlo Tree Search (MCTS):</strong> Expands search path selectively using Upper Confidence Bound (UCB1) formula. Guides searches using prior probabilities computed via Bayesian Variable Elimination, rather than brute-force expanding all game tree branches.</p>
            ) : (
              <p style={{ marginTop: 6 }}><strong>Alpha-Beta Pruning:</strong> Maintains two bounds: $\alpha$ (the best MAX score guaranteed) and $\beta$ (the best MIN score guaranteed). Discards sub-trees as soon as a branch is proven to yield a worse outcome than a previously checked alternative.</p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
