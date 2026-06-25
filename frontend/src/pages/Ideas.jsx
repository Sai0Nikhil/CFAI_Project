import { useState, useEffect } from 'react'
import {
  runNotNamedYet,
  runEthicalTriage,
  runMultilingualExplain,
  runActiveBelief,
  runMultiAgentSearch,
  getNodes
} from '../api'
import AIInsight from '../components/AIInsight'
import { useAI } from '../context/AIContext'

const PROFILES = [
  { v: 'emergency', l: '🚨 Emergency' },
  { v: 'staff', l: '🩺 Staff' },
  { v: 'visitor', l: '👤 Visitor' },
  { v: 'patient', l: '♿ Patient' }
]

const LANGUAGES = [
  { v: 'en', l: 'English 🌐' },
  { v: 'te', l: 'Telugu (తెలుగు) 🇮🇳' },
  { v: 'hi', l: 'Hindi (हिंदी) 🇮🇳' }
]

const TIME_OF_DAYS = [
  { v: 'morning', l: '🌅 Morning' },
  { v: 'afternoon', l: '☀️ Afternoon' },
  { v: 'evening', l: '🌆 Evening' },
  { v: 'night', l: '🌃 Night' }
]

const SEVERITIES = [
  { v: 'critical', l: '🚨 Critical' },
  { v: 'urgent', l: '⚠️ Urgent' },
  { v: 'standard', l: '♿ Standard' },
  { v: 'non-urgent', l: '👤 Non-Urgent' }
]

export default function Ideas() {
  const globalAI = useAI()
  const { hospital, hospitalInfo } = globalAI

  const [activeTab, setActiveTab] = useState('not_named_yet')
  const [nodes, setNodes] = useState([])
  const [loading, setLoading] = useState(false)
  const [aiTrigger, setAiTrigger] = useState(0)

  // Fetch nodes
  useEffect(() => {
    getNodes(hospital).then(r => setNodes(r.data))
  }, [hospital])

  // --- STATE FOR TABS ---

  // 1. Not Named Yet State
  const [nnyStart, setNnyStart] = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [nnyGoal, setNnyGoal] = useState(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
  const [nnyProfile, setNnyProfile] = useState('emergency')
  const [nnyDepth, setNnyDepth] = useState(3)
  const [nnyTimeOfDay, setNnyTimeOfDay] = useState('morning')
  const [nnyUseLlm, setNnyUseLlm] = useState(false)
  const [nnyResult, setNnyResult] = useState(null)

  // 2. Ethical Triage State
  const [paName, setPaName] = useState('Patient A (Minority)')
  const [paSeverity, setPaSeverity] = useState('critical')
  const [paWait, setPaWait] = useState(12)
  const [paCost, setPaCost] = useState(300)
  const [paLang, setPaLang] = useState('telugu')

  const [pbName, setPbName] = useState('Patient B (English)')
  const [pbSeverity, setPbSeverity] = useState('urgent')
  const [pbWait, setPbWait] = useState(15)
  const [pbCost, setPbCost] = useState(90)
  const [pbLang, setPbLang] = useState('english')

  const [triageMode, setTriageMode] = useState('rawlsian')
  const [equityGuard, setEquityGuard] = useState(true)
  const [triageResult, setTriageResult] = useState(null)

  // 3. Multilingual Explainer State
  const [xaiStart, setXaiStart] = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [xaiGoal, setXaiGoal] = useState(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
  const [xaiProfile, setXaiProfile] = useState('patient')
  const [xaiLanguage, setXaiLanguage] = useState('te')
  const [xaiUseLlm, setXaiUseLlm] = useState(false)
  const [xaiResult, setXaiResult] = useState(null)

  // 4. Active Belief State
  const [abStart, setAbStart] = useState(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
  const [abGoal, setAbGoal] = useState(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
  const [abThreshold, setAbThreshold] = useState(0.8)
  const [abEnabled, setAbEnabled] = useState(true)
  const [sensorAgeICU, setSensorAgeICU] = useState(4.0) // age in hours
  const [sensorAgeCorridor, setSensorAgeCorridor] = useState(0.5)
  const [abResult, setAbResult] = useState(null)

  // 5. Multi-Agent State
  const [maStart1, setMaStart1] = useState('ENTRANCE_MAIN')
  const [maGoal1, setMaGoal1] = useState('Node_302_ICU_Tower')
  const [maPriority1, setMaPriority1] = useState('critical')

  const [maStart2, setMaStart2] = useState('Node_302_ICU_Tower')
  const [maGoal2, setMaGoal2] = useState('ENTRANCE_MAIN')
  const [maPriority2, setMaPriority2] = useState('urgent')

  const [maStart3, setMaStart3] = useState('HW_Pharmacy')
  const [maGoal3, setMaGoal3] = useState('Ward_Cardio_F7')
  const [maPriority3, setMaPriority3] = useState('standard')

  const [maCoordEnabled, setMaCoordEnabled] = useState(true)
  const [maResult, setMaResult] = useState(null)

  // Sync defaults
  useEffect(() => {
    setNnyStart(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
    setNnyGoal(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
    setXaiStart(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
    setXaiGoal(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
    setAbStart(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
    setAbGoal(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')

    // Set defaults for multi-agent starts & goals
    setMaStart1(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
    setMaGoal1(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
    setMaStart2(hospitalInfo?.defaultGoal || 'Node_302_ICU_Tower')
    setMaGoal2(hospitalInfo?.defaultStart || 'ENTRANCE_MAIN')
    setMaStart3(hospitalInfo?.defaultStart === 'MAIN_GATE' ? 'OPD_BLOCK' : 'HW_Pharmacy')
    setMaGoal3(hospitalInfo?.defaultStart === 'MAIN_GATE' ? 'NICU_F3' : 'Ward_Cardio_F7')

    setNnyResult(null)
    setTriageResult(null)
    setXaiResult(null)
    setAbResult(null)
    setMaResult(null)
  }, [hospital, hospitalInfo])

  // --- ACTIONS ---

  const handleRunNny = async () => {
    setLoading(true)
    setNnyResult(null)
    try {
      const res = await runNotNamedYet({
        start: nnyStart,
        goal: nnyGoal,
        profile: nnyProfile,
        depth: nnyDepth,
        time_of_day: nnyTimeOfDay,
        use_llm_value: nnyUseLlm,
        api_key: globalAI.apiKey,
        provider: globalAI.provider,
        model: globalAI.model,
        hospital
      })
      setNnyResult(res.data)
      setAiTrigger(t => t + 1)
    } catch (e) {
      alert('Search failed: ' + e.message)
    }
    setLoading(false)
  }

  const handleRunTriage = async () => {
    setLoading(true)
    setTriageResult(null)
    try {
      const res = await runEthicalTriage({
        patient_a: { name: paName, severity: paSeverity, waiting_time: paWait, base_cost: paCost, language: paLang },
        patient_b: { name: pbName, severity: pbSeverity, waiting_time: pbWait, base_cost: pbCost, language: pbLang },
        mode: triageMode,
        equity_guard: equityGuard
      })
      setTriageResult(res.data)
    } catch (e) {
      alert('Triage simulator failed: ' + e.message)
    }
    setLoading(false)
  }

  const handleRunXai = async () => {
    setLoading(true)
    setXaiResult(null)
    try {
      // Find a mock route cost using the selected start/goal
      const mockRouteCost = 140.0 // seconds default
      const res = await runMultilingualExplain({
        path: [xaiStart, 'Corridor_Link', xaiGoal],
        cost: mockRouteCost,
        algorithm: 'astar',
        profile: xaiProfile,
        language: xaiLanguage,
        hospital,
        use_llm: xaiUseLlm,
        api_key: globalAI.apiKey,
        provider: globalAI.provider,
        model: globalAI.model
      })
      setXaiResult(res.data)
    } catch (e) {
      alert('XAI generation failed: ' + e.message)
    }
    setLoading(false)
  }

  const handleRunActiveBelief = async () => {
    setLoading(true)
    setAbResult(null)
    try {
      // Build a dynamic map of sensor age
      const ages = {
        'ICU_Floor3': sensorAgeICU,
        'Node_302_ICU_Tower': sensorAgeICU,
        'HW_OPD': sensorAgeCorridor,
        'ENTRANCE_MAIN': 0.0
      }
      const res = await runActiveBelief({
        start: abStart,
        goal: abGoal,
        hospital,
        entropy_threshold: abThreshold,
        sensor_ages: ages,
        active_belief_enabled: abEnabled
      })
      setAbResult(res.data)
    } catch (e) {
      alert('POMDP pathfinder failed: ' + e.message)
    }
    setLoading(false)
  }

  const handleRunMultiAgent = async () => {
    setLoading(true)
    setMaResult(null)
    try {
      const res = await runMultiAgentSearch({
        hospital,
        agents: [
          { id: 'A1', name: 'Ambulance 1 🚑', start: maStart1, goal: maGoal1, priority: maPriority1 },
          { id: 'A2', name: 'Ambulance 2 🚒', start: maStart2, goal: maGoal2, priority: maPriority2 },
          { id: 'A3', name: 'Ambulance 3 🚓', start: maStart3, goal: maGoal3, priority: maPriority3 }
        ],
        coordination_enabled: maCoordEnabled
      })
      setMaResult(res.data)
    } catch (e) {
      alert('Multi-agent pathfinding failed: ' + e.message)
    }
    setLoading(false)
  }

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div className="page-title">
          💡 Ideas Lab <span className="badge badge-co5">Active R&D</span>
        </div>
        <div className="page-sub">
          Publication-grade AI algorithms under active deployment at Charité & AIIMS
        </div>
      </div>

      {/* Tab Selectors */}
      <div style={{ display: 'flex', gap: 6, marginBottom: 20, flexWrap: 'wrap' }}>
        {[
          ['not_named_yet', '🧠 "Not Named Yet"'],
          ['ethical_triage', '⚖️ Ethical Governor'],
          ['multilingual_xai', '🌐 Offline Explainer'],
          ['active_belief', '📡 Active Belief'],
          ['multi_agent', '🚒 Multi-Agent']
        ].map(([v, l]) => (
          <button
            key={v}
            onClick={() => {
              setActiveTab(v)
            }}
            style={{
              padding: '8px 18px',
              borderRadius: 8,
              border: '1px solid',
              fontWeight: 700,
              fontSize: '.8rem',
              cursor: 'pointer',
              fontFamily: 'inherit',
              background: activeTab === v ? '#b45309' : '#fff8f0',
              color: activeTab === v ? '#fff' : '#5c4a30',
              borderColor: activeTab === v ? '#b45309' : '#e8d9c4',
              transition: 'all 0.15s'
            }}
          >
            {l}
          </button>
        ))}
      </div>

      {/* CONCEPT INFO ALERT */}
      <div className="alert alert-info" style={{ marginBottom: 16 }}>
        {activeTab === 'not_named_yet' && (
          <div>
            <strong>"Not Named Yet" Mode:</strong> Uses Bayesian prior probability distributions from variable elimination to <strong>sort minimax successors</strong> (clearest paths evaluated first). Reduces tree branch expansion. Optional LLM evaluates terminal leaves.
          </div>
        )}
        {activeTab === 'ethical_triage' && (
          <div>
            <strong>Ethical Triage Governor:</strong> Resolves path scheduling conflicts when patients compete for bottleneck access points. Compares <strong>John Rawls' Maximin Difference Principle</strong> (helping the worst-off) against <strong>Bentham's Utilitarianism</strong> (maximizing cumulative average flow).
          </div>
        )}
        {activeTab === 'multilingual_xai' && (
          <div>
            <strong>Offline Multilingual Explainer:</strong> Local Explainable AI (XAI) engine generating direct text summaries in English, Telugu, and Hindi scripts without calling web APIs. Plugs local pathfinder and security constraints into symbolic grammar rules.
          </div>
        )}
        {activeTab === 'active_belief' && (
          <div>
            <strong>Active Belief Routing (POMDP-lite):</strong> Simulates corridor sensor age decay. Solves the <strong>Exploration vs. Exploitation trade-off</strong> using Shannon Entropy. If a path contains high-uncertainty nodes, the routing agent schedules an observation detour.
          </div>
        )}
        {activeTab === 'multi_agent' && (
          <div>
            <strong>🚒 Multi-Agent Coordinator (Cooperative MAPF):</strong> Simulates space-time Cooperative A* with space-time reservation tables to avoid vertex and swap collisions between multiple ambulances.
          </div>
        )}
      </div>

      {/* LOADING INDICATOR */}
      {loading && (
        <div style={{ margin: '24px 0', textAlign: 'center', color: '#6b7280' }}>
          <div className="spinner" />
          <p style={{ marginTop: 10, fontSize: '.85rem' }}>Processing model outputs...</p>
        </div>
      )}

      {/* --- TAB VIEW 1: NOT NAMED YET --- */}
      {activeTab === 'not_named_yet' && !loading && (
        <>
          <div className="card">
            <div className="form-row form-4">
              <div className="form-group">
                <label className="form-label">Start Node</label>
                <select
                  className="form-control"
                  value={nnyStart}
                  onChange={e => setNnyStart(e.target.value)}
                >
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>
                      {n.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Goal Node</label>
                <select
                  className="form-control"
                  value={nnyGoal}
                  onChange={e => setNnyGoal(e.target.value)}
                >
                  {nodes.map(n => (
                    <option key={n.id} value={n.id}>
                      {n.label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Profile</label>
                <select
                  className="form-control"
                  value={nnyProfile}
                  onChange={e => setNnyProfile(e.target.value)}
                >
                  {PROFILES.map(p => (
                    <option key={p.v} value={p.v}>
                      {p.l}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Search Depth ({nnyDepth} plies)</label>
                <input
                  type="range"
                  min={1}
                  max={5}
                  value={nnyDepth}
                  onChange={e => setNnyDepth(Number(e.target.value))}
                  style={{ width: '100%', accentColor: '#b45309', marginTop: 8 }}
                />
              </div>
            </div>

            <div className="form-row form-3" style={{ marginTop: 14, borderTop: '1px solid #e8d9c4', paddingTop: 12 }}>
              <div className="form-group">
                <label className="form-label">Prior TimeOfDay</label>
                <select
                  className="form-control"
                  value={nnyTimeOfDay}
                  onChange={e => setNnyTimeOfDay(e.target.value)}
                >
                  {TIME_OF_DAYS.map(t => (
                    <option key={t.v} value={t.v}>
                      {t.l}
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-group" style={{ justifyContent: 'center' }}>
                <label className="toggle-row" style={{ marginTop: 14 }}>
                  <label className="toggle">
                    <input
                      type="checkbox"
                      checked={nnyUseLlm}
                      onChange={e => setNnyUseLlm(e.target.checked)}
                    />
                    <span className="toggle-slider" />
                  </label>
                  <span className="toggle-label" style={{ fontSize: '.8rem' }}>
                    🤖 LLM Value Guidance
                  </span>
                </label>
              </div>
            </div>

            {nnyUseLlm && !globalAI.isReady && (
              <div className="alert alert-warning" style={{ fontSize: '.78rem', marginTop: 10 }}>
                ⚠️ LLM Value Guidance requires an active API key. Please configure a key in the header. Falling back to heuristic evaluations.
              </div>
            )}

            <button
              className="btn btn-primary btn-full"
              style={{ marginTop: 16 }}
              onClick={handleRunNny}
            >
              ▶ Run "Not Named Yet" Hybrid Search
            </button>
          </div>

          {/* Nny Results */}
          {nnyResult && (
            <div style={{ marginTop: 16 }}>
              <div className="metrics-row metrics-3">
                <div className="metric-card">
                  <div className="metric-val">{nnyResult.path?.length || '—'}</div>
                  <div className="metric-lbl">Hops Found</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{nnyResult.cost?.toFixed(0) || '—'}s</div>
                  <div className="metric-lbl">Travel Cost</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{nnyResult.nodes_evaluated || '—'}</div>
                  <div className="metric-lbl">Nodes Evaluated</div>
                </div>
              </div>

              {nnyResult.path && (
                <div className="alert alert-success" style={{ margin: '14px 0' }}>
                  🎉 <strong>Optimal Route:</strong> {nnyResult.path.join(' → ')}
                </div>
              )}

              {nnyResult.prune_log && (
                <div className="alert alert-info">
                  ✂️ Alpha-Beta cutoffs pruned <strong>{nnyResult.prune_log.length}</strong> suboptimal subtrees.
                </div>
              )}

              {nnyResult.explanation && (
                <div className="card card-sm" style={{ background: '#fffdf9', fontSize: '.84rem', lineHeight: 1.6 }}>
                  <strong>Execution Insight:</strong> {nnyResult.explanation}
                </div>
              )}

              {nnyResult.trace && (
                <>
                  <div className="section-label">🌳 Minimax Decision Tree Trace</div>
                  <div className="table-wrap">
                    <table className="trace-table">
                      <thead>
                        <tr>
                          <th>Depth</th>
                          <th>Node</th>
                          <th>Player</th>
                          <th>Score</th>
                          <th>Search Details</th>
                        </tr>
                      </thead>
                      <tbody>
                        {nnyResult.trace.slice(0, 20).map((t, i) => (
                          <tr key={i}>
                            <td>{t.depth}</td>
                            <td><code>{t.node}</code></td>
                            <td style={{ color: t.is_max ? '#15803d' : '#dc2626', fontWeight: 700 }}>
                              {t.is_max ? 'MAX ▲' : 'MIN ▼'}
                            </td>
                            <td>{t.score !== undefined ? t.score.toFixed(2) : '—'}</td>
                            <td style={{ fontSize: '.72rem' }}>{t.note || t.move}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              <AIInsight
                module="not_named_yet"
                trigger={aiTrigger}
                context={{
                  path: nnyResult.path,
                  cost: nnyResult.cost,
                  depth: nnyDepth,
                  time_of_day: nnyTimeOfDay,
                  prunes: nnyResult.prune_log?.length,
                  llm_used: nnyUseLlm && globalAI.isReady
                }}
              />
            </div>
          )}
        </>
      )}

      {/* --- TAB VIEW 2: ETHICAL TRIAGE GOVERNOR --- */}
      {activeTab === 'ethical_triage' && !loading && (
        <>
          <div className="card">
            <h4 style={{ marginBottom: 12, color: '#b45309' }}>⚖️ Ethical Dilemma Simulator</h4>
            <p style={{ fontSize: '.76rem', color: '#6b7280', marginBottom: 16 }}>
              Configure two patients arriving concurrently at the hospital lobby, competing for a single working elevator.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20 }}>
              {/* Patient A panel */}
              <div style={{ background: '#fffdf9', padding: 14, borderRadius: 10, border: '1px solid #e8d9c4' }}>
                <h5 style={{ marginBottom: 10, borderBottom: '1px solid #e8d9c4', paddingBottom: 4 }}>👤 Patient A</h5>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Name</label>
                  <input className="form-control" value={paName} onChange={e => setPaName(e.target.value)} />
                </div>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Severity</label>
                  <select className="form-control" value={paSeverity} onChange={e => setPaSeverity(e.target.value)}>
                    {SEVERITIES.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Wait Time ({paWait}m)</label>
                  <input type="range" min={0} max={60} value={paWait} onChange={e => setPaWait(Number(e.target.value))} style={{ width: '100%' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Language</label>
                  <select className="form-control" value={paLang} onChange={e => setPaLang(e.target.value)}>
                    {LANGUAGES.map(l => <option key={l.v} value={l.v}>{l.l}</option>)}
                  </select>
                </div>
              </div>

              {/* Patient B panel */}
              <div style={{ background: '#fffdf9', padding: 14, borderRadius: 10, border: '1px solid #e8d9c4' }}>
                <h5 style={{ marginBottom: 10, borderBottom: '1px solid #e8d9c4', paddingBottom: 4 }}>👤 Patient B</h5>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Name</label>
                  <input className="form-control" value={pbName} onChange={e => setPbName(e.target.value)} />
                </div>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Severity</label>
                  <select className="form-control" value={pbSeverity} onChange={e => setPbSeverity(e.target.value)}>
                    {SEVERITIES.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Wait Time ({pbWait}m)</label>
                  <input type="range" min={0} max={60} value={pbWait} onChange={e => setPbWait(Number(e.target.value))} style={{ width: '100%' }} />
                </div>
                <div className="form-group" style={{ marginBottom: 10 }}>
                  <label className="form-label" style={{ fontSize: '.7rem' }}>Language</label>
                  <select className="form-control" value={pbLang} onChange={e => setPbLang(e.target.value)}>
                    {LANGUAGES.map(l => <option key={l.v} value={l.v}>{l.l}</option>)}
                  </select>
                </div>
              </div>
            </div>

            {/* Governor Configuration Controls */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 16, borderTop: '1px solid #e8d9c4', paddingTop: 14, flexWrap: 'wrap', gap: 10 }}>
              <div style={{ display: 'flex', gap: 8 }}>
                <button
                  onClick={() => setTriageMode('rawlsian')}
                  style={{
                    padding: '6px 12px', borderRadius: 6, cursor: 'pointer', border: '1px solid', fontSize: '.75rem', fontWeight: 700,
                    background: triageMode === 'rawlsian' ? '#0f766e' : '#fff',
                    color: triageMode === 'rawlsian' ? '#fff' : '#0f766e',
                    borderColor: '#0f766e'
                  }}
                >
                  ⚖️ Rawlsian Justice
                </button>
                <button
                  onClick={() => setTriageMode('utilitarian')}
                  style={{
                    padding: '6px 12px', borderRadius: 6, cursor: 'pointer', border: '1px solid', fontSize: '.75rem', fontWeight: 700,
                    background: triageMode === 'utilitarian' ? '#1d4ed8' : '#fff',
                    color: triageMode === 'utilitarian' ? '#fff' : '#1d4ed8',
                    borderColor: '#1d4ed8'
                  }}
                >
                  📊 Utilitarianism
                </button>
              </div>

              <div>
                <label className="toggle-row">
                  <label className="toggle">
                    <input type="checkbox" checked={equityGuard} onChange={e => setEquityGuard(e.target.checked)} />
                    <span className="toggle-slider" />
                  </label>
                  <span className="toggle-label" style={{ fontSize: '.75rem', fontWeight: 600 }}>🛡️ Language Equity Guard</span>
                </label>
              </div>
            </div>

            <button className="btn btn-primary btn-full" style={{ marginTop: 14 }} onClick={handleRunTriage}>
              ⚖️ Resolve Triage Conflict & Schedule Queue
            </button>
          </div>

          {/* Triage Results */}
          {triageResult && (
            <div style={{ marginTop: 16 }}>
              <div className="section-label">📋 Scheduled Queue Order</div>

              <div style={{ display: 'flex', gap: 12, marginBottom: 14, flexDirection: 'column' }}>
                {triageResult.schedule.map((pat, index) => (
                  <div
                    key={index}
                    style={{
                      background: pat.order === 1 ? '#f0fdf4' : '#fff',
                      border: `1.5px solid ${pat.order === 1 ? '#86efac' : '#e5e7eb'}`,
                      borderRadius: 10, padding: '14px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                    }}
                  >
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                        <span style={{ background: pat.order === 1 ? '#22c55e' : '#6b7280', color: '#fff', borderRadius: '50%', width: 22, height: 22, display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '.75rem', fontWeight: 800 }}>
                          #{pat.order}
                        </span>
                        <strong style={{ fontSize: '.9rem' }}>{pat.patient}</strong>
                        {pat.is_equity_booster && (
                          <span style={{ fontSize: '.68rem', background: '#fef3c7', color: '#b45309', padding: '1px 6px', borderRadius: 4, fontWeight: 700 }}>
                            Equity Boosted
                          </span>
                        )}
                      </div>
                      <div style={{ fontSize: '.74rem', color: '#6b7280', marginTop: 4 }}>
                        Severity: {pat.severity} | Language: {pat.language}
                      </div>
                    </div>

                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 800, fontSize: '.9rem', color: '#111827' }}>
                        {pat.delay.toFixed(1)} mins
                      </div>
                      <div style={{ fontSize: '.68rem', color: '#6b7280' }}>
                        Expected delay
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              {/* Philosophical insight */}
              <div className="alert alert-info">
                <strong>Governor Philosophical Logic:</strong>
                <p style={{ fontSize: '.8rem', marginTop: 4, lineHeight: 1.5 }}>
                  {triageResult.philosophical_note}
                </p>
              </div>

              {/* Trace details */}
              <div className="card card-sm" style={{ background: '#fffdf9' }}>
                <strong>Triage Decision Log:</strong>
                <ul style={{ paddingLeft: 18, marginTop: 6, fontSize: '.78rem', lineHeight: 1.6 }}>
                  {triageResult.reasoning.map((r, i) => <li key={i}>{r}</li>)}
                </ul>
              </div>
            </div>
          )}
        </>
      )}

      {/* --- TAB VIEW 3: MULTILINGUAL EXPLAINER --- */}
      {activeTab === 'multilingual_xai' && !loading && (
        <>
          <div className="card">
            <h4 style={{ marginBottom: 12, color: '#b45309' }}>🌐 Offline Explainable AI (XAI) engine</h4>
            <p style={{ fontSize: '.76rem', color: '#6b7280', marginBottom: 16 }}>
              Generate path descriptions and safety validation summaries completely offline using symbolic templates.
            </p>

            <div className="form-row form-4">
              <div className="form-group">
                <label className="form-label">Start</label>
                <select className="form-control" value={xaiStart} onChange={e => setXaiStart(e.target.value)}>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Goal</label>
                <select className="form-control" value={xaiGoal} onChange={e => setXaiGoal(e.target.value)}>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Profile</label>
                <select className="form-control" value={xaiProfile} onChange={e => setXaiProfile(e.target.value)}>
                  {PROFILES.map(p => <option key={p.v} value={p.v}>{p.l}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Target Language</label>
                <select className="form-control" value={xaiLanguage} onChange={e => setXaiLanguage(e.target.value)}>
                  {LANGUAGES.map(l => <option key={l.v} value={l.v}>{l.l}</option>)}
                </select>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 14 }}>
              <label className="toggle-row">
                <label className="toggle">
                  <input type="checkbox" checked={xaiUseLlm} onChange={e => setXaiUseLlm(e.target.checked)} />
                  <span className="toggle-slider" />
                </label>
                <span className="toggle-label" style={{ fontSize: '.75rem', fontWeight: 600 }}>🤖 Enable LLM Refinement Translation</span>
              </label>

              <button className="btn btn-primary" onClick={handleRunXai}>
                Generate Local Explanation
              </button>
            </div>
          </div>

          {/* Xai Output */}
          {xaiResult && (
            <div style={{ marginTop: 16 }}>
              <div className="section-label">📜 Local Symbolic Summary (100% Offline)</div>
              <div className="card card-sm" style={{ background: '#f9fafb', fontSize: '.86rem', lineHeight: 1.6 }}>
                <code>{xaiResult.symbolic_explanation}</code>
              </div>

              {xaiUseLlm && xaiResult.llm_refined && (
                <>
                  <div className="section-label">🤖 Warm, Empathetic Voice output (LLM Refined)</div>
                  <div
                    style={{
                      background: 'linear-gradient(135deg, #fdfbf7 0%, #fffbeb 100%)',
                      border: '1.5px solid #fcd34d',
                      borderRadius: 12, padding: '16px 20px', boxShadow: '0 4px 12px rgba(252,211,77,0.1)'
                    }}
                  >
                    <p style={{ fontStyle: 'italic', fontSize: '.95rem', color: '#78350f', lineHeight: 1.7, margin: 0 }}>
                      "{xaiResult.llm_refined}"
                    </p>
                  </div>
                </>
              )}
            </div>
          )}
        </>
      )}

      {/* --- TAB VIEW 4: ACTIVE BELIEF ROUTING --- */}
      {activeTab === 'active_belief' && !loading && (
        <>
          <div className="card">
            <h4 style={{ marginBottom: 12, color: '#b45309' }}>📡 Active Belief Routing (POMDP-lite)</h4>
            <p style={{ fontSize: '.76rem', color: '#6b7280', marginBottom: 16 }}>
              Model dynamic corridor congestion states. Adjust the age of the sensor observations to see Shannon Entropy increase uncertainty, triggering detours.
            </p>

            <div className="form-row form-3">
              <div className="form-group">
                <label className="form-label">Start</label>
                <select className="form-control" value={abStart} onChange={e => setAbStart(e.target.value)}>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Goal</label>
                <select className="form-control" value={abGoal} onChange={e => setAbGoal(e.target.value)}>
                  {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label className="form-label">Uncertainty Threshold H(X) &ge; {abThreshold}</label>
                <input type="range" min={0.3} max={1.4} step={0.1} value={abThreshold} onChange={e => setAbThreshold(Number(e.target.value))} style={{ width: '100%' }} />
              </div>
            </div>

            {/* Sensor ages simulator sliders */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 20, marginTop: 14, borderTop: '1px solid #e8d9c4', paddingTop: 12 }}>
              <div className="form-group">
                <label className="form-label">ICU Corridor Observation Age ({sensorAgeICU} hrs ago)</label>
                <input type="range" min={0.0} max={6.0} step={0.5} value={sensorAgeICU} onChange={e => setSensorAgeICU(Number(e.target.value))} style={{ width: '100%', accentColor: '#b45309' }} />
                <span style={{ fontSize: '.68rem', color: '#6b7280', marginTop: 4 }}>
                  Larger age = higher state distribution decay & higher Shannon Entropy.
                </span>
              </div>
              <div className="form-group">
                <label className="form-label">OPD Corridor Observation Age ({sensorAgeCorridor} hrs ago)</label>
                <input type="range" min={0.0} max={6.0} step={0.5} value={sensorAgeCorridor} onChange={e => setSensorAgeCorridor(Number(e.target.value))} style={{ width: '100%', accentColor: '#b45309' }} />
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginTop: 16 }}>
              <label className="toggle-row">
                <label className="toggle">
                  <input type="checkbox" checked={abEnabled} onChange={e => setAbEnabled(e.target.checked)} />
                  <span className="toggle-slider" />
                </label>
                <span className="toggle-label" style={{ fontSize: '.75rem', fontWeight: 600 }}>Enable Active Exploration detours</span>
              </label>

              <button className="btn btn-primary" onClick={handleRunActiveBelief}>
                Run POMDP Pathfinder
              </button>
            </div>
          </div>

          {/* Pathfinder result map */}
          {abResult && (
            <div style={{ marginTop: 16 }}>
              <div className="metrics-row metrics-3">
                <div className="metric-card">
                  <div className="metric-val" style={{ color: abResult.detour_triggered ? '#d97706' : '#22c55e' }}>
                    {abResult.detour_triggered ? 'Detour 📡' : 'Direct 🛣️'}
                  </div>
                  <div className="metric-lbl">Routing Action</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{abResult.cost?.toFixed(0)}s</div>
                  <div className="metric-lbl">Route Cost</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{abResult.base_cost?.toFixed(0)}s</div>
                  <div className="metric-lbl">Base Cost</div>
                </div>
              </div>

              {/* Entropy Uncertainty Map Visualization */}
              <div className="section-label">📡 Shannon Entropy Uncertainty Map</div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 10, marginBottom: 14 }}>
                {Object.entries(abResult.nodes_entropy).map(([node, data]) => {
                  const h = data.entropy
                  const pct = Math.min(100, (h / 1.58) * 100)
                  const barColor = h < 0.5 ? '#22c55e' : h < 0.9 ? '#eab308' : '#ef4444'
                  return (
                    <div key={node} style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 10 }}>
                      <div style={{ fontWeight: 700, fontSize: '.78rem', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {node}
                      </div>
                      <div style={{ fontSize: '.66rem', color: '#6b7280', marginTop: 2 }}>
                        Observation: {data.age_hours} hrs ago
                      </div>
                      <div style={{ fontSize: '.68rem', fontWeight: 800, marginTop: 6, display: 'flex', justifyContent: 'space-between' }}>
                        <span>Entropy H(X)</span>
                        <span>{h}</span>
                      </div>
                      <div style={{ width: '100%', height: 6, background: '#f3f4f6', borderRadius: 3, marginTop: 4, overflow: 'hidden' }}>
                        <div style={{ width: `${pct}%`, height: '100%', background: barColor, transition: 'width 0.3s' }} />
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Path winner */}
              <div className="alert alert-success">
                <strong>Resulting Path:</strong> {abResult.path.join(' → ')}
              </div>

              {/* Decision trace logs */}
              <div className="card card-sm" style={{ background: '#fffdf9' }}>
                <strong>POMDP-Lite Decision Logs:</strong>
                <ul style={{ paddingLeft: 18, marginTop: 6, fontSize: '.78rem', lineHeight: 1.6, listStyleType: 'square' }}>
                  {abResult.decision_log.map((log, i) => <li key={i}>{log}</li>)}
                </ul>
              </div>
            </div>
          )}
        </>
      )}

      {/* --- TAB VIEW 5: MULTI-AGENT emergency coordinator --- */}
      {activeTab === 'multi_agent' && !loading && (
        <>
          <div className="card">
            <h4 style={{ marginBottom: 12, color: '#b45309' }}>🚒 Multi-Agent Coordinator (MAPF)</h4>
            <p style={{ fontSize: '.76rem', color: '#6b7280', marginBottom: 16 }}>
              Route three emergency units concurrently. If "Coordination" is enabled, they resolve path conflicts in space-time (making one agent wait or take a detour to prevent collisions!).
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16, marginBottom: 16 }}>
              {/* Agent 1 */}
              <div style={{ background: '#fffdf9', padding: 12, borderRadius: 8, border: '1px solid #e8d9c4' }}>
                <h5 style={{ marginBottom: 8, borderBottom: '1px solid #e8d9c4', paddingBottom: 4 }}>🚑 Ambulance 1</h5>
                <div className="form-group" style={{ marginBottom: 8 }}>
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Start</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maStart1} onChange={e => setMaStart1(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 8 }}>
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Goal</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maGoal1} onChange={e => setMaGoal1(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Priority</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maPriority1} onChange={e => setMaPriority1(e.target.value)}>
                    <option value="critical">🚨 Critical</option>
                    <option value="urgent">⚠️ Urgent</option>
                    <option value="standard">♿ Standard</option>
                  </select>
                </div>
              </div>

              {/* Agent 2 */}
              <div style={{ background: '#fffdf9', padding: 12, borderRadius: 8, border: '1px solid #e8d9c4' }}>
                <h5 style={{ marginBottom: 8, borderBottom: '1px solid #e8d9c4', paddingBottom: 4 }}>🚒 Ambulance 2</h5>
                <div className="form-group" style={{ marginBottom: 8 }}>
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Start</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maStart2} onChange={e => setMaStart2(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 8 }}>
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Goal</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maGoal2} onChange={e => setMaGoal2(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Priority</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maPriority2} onChange={e => setMaPriority2(e.target.value)}>
                    <option value="critical">🚨 Critical</option>
                    <option value="urgent">⚠️ Urgent</option>
                    <option value="standard">♿ Standard</option>
                  </select>
                </div>
              </div>

              {/* Agent 3 */}
              <div style={{ background: '#fffdf9', padding: 12, borderRadius: 8, border: '1px solid #e8d9c4' }}>
                <h5 style={{ marginBottom: 8, borderBottom: '1px solid #e8d9c4', paddingBottom: 4 }}>🚓 Patrol Unit 3</h5>
                <div className="form-group" style={{ marginBottom: 8 }}>
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Start</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maStart3} onChange={e => setMaStart3(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  </select>
                </div>
                <div className="form-group" style={{ marginBottom: 8 }}>
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Goal</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maGoal3} onChange={e => setMaGoal3(e.target.value)}>
                    {nodes.map(n => <option key={n.id} value={n.id}>{n.label}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label className="form-label" style={{ fontSize: '.68rem' }}>Priority</label>
                  <select className="form-control" style={{ fontSize: '.74rem' }} value={maPriority3} onChange={e => setMaPriority3(e.target.value)}>
                    <option value="critical">🚨 Critical</option>
                    <option value="urgent">⚠️ Urgent</option>
                    <option value="standard">♿ Standard</option>
                  </select>
                </div>
              </div>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <label className="toggle-row">
                <label className="toggle">
                  <input type="checkbox" checked={maCoordEnabled} onChange={e => setMaCoordEnabled(e.target.checked)} />
                  <span className="toggle-slider" />
                </label>
                <span className="toggle-label" style={{ fontSize: '.75rem', fontWeight: 600 }}>Enable Space-Time Coordination</span>
              </label>

              <button className="btn btn-primary" onClick={handleRunMultiAgent}>
                🚒 Coordinate Dispatch
              </button>
            </div>
          </div>

          {/* Multi-Agent results */}
          {maResult && (
            <div style={{ marginTop: 16 }}>
              {/* Metrics */}
              <div className="metrics-row metrics-3">
                <div className="metric-card">
                  <div className="metric-val" style={{ color: maResult.coordination_enabled ? '#22c55e' : '#ef4444' }}>
                    {maResult.coordination_enabled ? 'Coordinated' : 'Conflicts Raw'}
                  </div>
                  <div className="metric-lbl">Routing State</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{maResult.metrics.makespan} steps</div>
                  <div className="metric-lbl">Total Time (Makespan)</div>
                </div>
                <div className="metric-card">
                  <div className="metric-val">{maResult.metrics.sum_of_costs?.toFixed(0)}s</div>
                  <div className="metric-lbl">Sum of Path Costs</div>
                </div>
              </div>

              {/* Space-Time Timetable */}
              <div className="section-label">🗓️ Space-Time Dispatch Timetable</div>
              <div className="table-wrap">
                <table className="trace-table" style={{ textAlign: 'center' }}>
                  <thead>
                    <tr>
                      <th style={{ width: '80px' }}>Step (t)</th>
                      <th>Ambulance 1 Pos</th>
                      <th>Ambulance 2 Pos</th>
                      <th>Patrol Unit 3 Pos</th>
                    </tr>
                  </thead>
                  <tbody>
                    {maResult.timesteps.map((row, idx) => (
                      <tr key={idx}>
                        <td><strong>t = {row.t}</strong></td>
                        <td style={{ color: row.A1 === maGoal1 ? '#22c55e' : '#111827', fontWeight: row.A1 === maGoal1 ? 800 : 400 }}>
                          <code>{row.A1}</code> {row.A1 === maGoal1 && '🏁'}
                        </td>
                        <td style={{ color: row.A2 === maGoal2 ? '#22c55e' : '#111827', fontWeight: row.A2 === maGoal2 ? 800 : 400 }}>
                          <code>{row.A2}</code> {row.A2 === maGoal2 && '🏁'}
                        </td>
                        <td style={{ color: row.A3 === maGoal3 ? '#22c55e' : '#111827', fontWeight: row.A3 === maGoal3 ? 800 : 400 }}>
                          <code>{row.A3}</code> {row.A3 === maGoal3 && '🏁'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Collision / Delay Logs */}
              <div className="section-label">📜 Collision Resolution Logs</div>
              <div className="card card-sm" style={{ background: '#fffdf9' }}>
                <ul style={{ paddingLeft: 18, fontSize: '.78rem', lineHeight: 1.6 }}>
                  {maResult.collision_log.map((log, i) => (
                    <li key={i} style={{ color: log.includes('💥') ? '#ef4444' : log.includes('✅') ? '#15803d' : '#374151', marginBottom: 4 }}>
                      {log}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}
