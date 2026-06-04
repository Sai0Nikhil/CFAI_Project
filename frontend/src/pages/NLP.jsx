import { useState } from 'react'
import { parseNLP } from '../api'
import AIInsight from '../components/AIInsight'
import { useAI } from '../context/AIContext'

const DEMOS = [
  {lang:'en', label:'🌐 English', queries:['Take me to the ICU','Where is the pharmacy?','Emergency! I am bleeding']},
  {lang:'te', label:'🇮🇳 Telugu', queries:['ICU కి తీసుకెళ్ళండి','నాకు గుండె నొప్పి వస్తోంది','ఫార్మసీ ఎక్కడ ఉంది?']},
  {lang:'hi', label:'🇮🇳 Hindi',  queries:['आईसीयू ले जाओ','मुझे ICU जाना है','दवाखाना कहाँ है?']},
]

const URG_CLS = {CRITICAL:'urg-critical', HIGH:'urg-high', NORMAL:'urg-normal'}
const URG_EMO = {CRITICAL:'🚨', HIGH:'⚠️', NORMAL:'✅'}

export default function NLP() {
  const { isReady, apiKey, provider, model } = useAI()
  const [query, setQuery]   = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [aiTrigger, setAiTrigger] = useState(0)

  const doparse = async (q = query) => {
    if (!q.trim()) return
    setLoading(true); setResult(null)
    try {
      const r = await parseNLP({
        query: q,
        use_llm: isReady,
        api_key: apiKey,
        provider,
        model,
      })
      setResult(r.data)
      setAiTrigger(t => t + 1)
    } catch(e) { alert(e.message) }
    setLoading(false)
  }

  return (
    <div>
      <div className="page-header">
        <div className="page-title">🌐 NLP <span className="badge badge-co6">CO6</span></div>
        <div className="page-sub">Telugu · Hindi · English · Roman transliteration · Urgency / Distress Detection</div>
      </div>

      {/* Demo phrases */}
      <div className="two-col" style={{marginBottom:20}}>
        {DEMOS.map(({lang,label,queries})=>(
          <div className="card card-sm" key={lang}>
            <div style={{fontWeight:700,fontSize:'.8rem',marginBottom:8}}>{label}</div>
            {queries.map(q=>(
              <div key={q} style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
                <span style={{flex:1,fontSize:'.82rem',fontStyle:'italic',color:'#374151'}}>{q}</span>
                <button className="btn btn-secondary" style={{padding:'3px 10px',fontSize:'.7rem'}}
                  onClick={()=>{ setQuery(q); doparse(q) }}>Try →</button>
              </div>
            ))}
          </div>
        ))}
        <div className="card card-sm">
          <div style={{fontWeight:700,fontSize:'.8rem',marginBottom:8}}>🔤 Roman Transliteration</div>
          {['ICU le jao', 'mujhe pharmacy jana hai', 'help cardiac arrest'].map(q=>(
            <div key={q} style={{display:'flex',alignItems:'center',gap:8,marginBottom:6}}>
              <span style={{flex:1,fontSize:'.82rem',fontStyle:'italic',color:'#374151'}}>{q}</span>
              <button className="btn btn-secondary" style={{padding:'3px 10px',fontSize:'.7rem'}}
                onClick={()=>{ setQuery(q); doparse(q) }}>Try →</button>
            </div>
          ))}
        </div>
      </div>

      {/* Input */}
      <div className="section-label">💬 Query Input</div>
      <div style={{display:'flex',gap:8,marginBottom:16}}>
        <input className="form-control" placeholder='Type in Telugu, Hindi, English, or Roman transliteration…'
          value={query} onChange={e=>setQuery(e.target.value)}
          onKeyDown={e=>e.key==='Enter'&&doparse()} />
        <button className="btn btn-primary btn-lg" onClick={()=>doparse()} disabled={loading}>
          {loading?'⏳ Parsing…':'➤ Parse'}
        </button>
      </div>

      {/* Pipeline stages explainer */}
      <div className="section-label">🔬 NLP Pipeline · CO6</div>
      <div className="pipe" style={{marginBottom:16}}>
        {[
          {lbl:'① Language Detect', val: result ? {te:'🇮🇳 Telugu',hi:'🇮🇳 Hindi',en:'🌐 English'}[result.language]||result.language : '—', sub:'Keyword + script'},
          {lbl:'② Intent Extract',  val: result ? (result.target_friendly||'Unknown').slice(0,16) : '—', sub:'Lexicon lookup'},
          {lbl:'③ Urgency Score',   val: result ? `${URG_EMO[result.urgency?.level]||''} ${result.urgency?.level||'—'}` : '—', sub:'Emotion patterns'},
          {lbl:'④ Route Target',   val: result?.target_node?.replace(/_/g,' ').slice(0,14)||'—', sub:'Node mapping'},
        ].map(s=>(
          <div key={s.lbl} className={`pipe-stage ${result?'active':''}`}>
            <div className="pipe-lbl">{s.lbl}</div>
            <div className="pipe-val" style={{fontSize:'.76rem'}}>{s.val}</div>
            <div className="pipe-sub">{s.sub}</div>
          </div>
        ))}
      </div>

      {/* Result */}
      {result && (
        <>
          <div className="result-card">
            <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:12}}>
              <div>
                <div style={{fontSize:'.62rem',fontWeight:700,letterSpacing:'.6px',textTransform:'uppercase',color:'#6b7280',marginBottom:2}}>Destination</div>
                <div className="result-dest">{result.target_friendly||'❓ Unknown destination'}</div>
                <div className="result-node">{result.target_node||'No node matched'}</div>
              </div>
              <div style={{textAlign:'right'}}>
                <div style={{fontSize:'.62rem',fontWeight:700,letterSpacing:'.6px',textTransform:'uppercase',color:'#6b7280',marginBottom:2}}>Detected Language</div>
                <span style={{fontWeight:700,fontSize:'.9rem'}}>
                  {({'te':'🇮🇳 Telugu','hi':'🇮🇳 Hindi','en':'🌐 English'})[result.language]||result.language}
                </span>
              </div>
            </div>
            <div style={{display:'flex',alignItems:'center',gap:10,flexWrap:'wrap'}}>
              <span className={`urg ${URG_CLS[result.urgency?.level]||'urg-normal'}`}>
                {URG_EMO[result.urgency?.level]} {result.urgency?.level}
              </span>
              <span style={{fontSize:'.82rem',color:'#374151'}}>{result.urgency?.routing_hint}</span>
            </div>
          </div>

          <AIInsight module="nlp" trigger={aiTrigger}
            context={{ query, language:result.language,
              target_friendly:result.target_friendly,
              target_node:result.target_node,
              urgency_level:result.urgency?.level,
              matched_keywords:result.urgency?.matched_keywords||[] }} />

          <div className="section-label">📋 Full Pipeline Trace</div>
          <div className="table-wrap">
            <table className="trace-table">
              <thead><tr><th>Stage</th><th>Output</th><th>Method</th><th>Note</th></tr></thead>
              <tbody>
                {result.pipeline_steps?.map((s,i)=>(
                  <tr key={i}>
                    <td><strong>{s.stage}</strong></td>
                    <td><code>{s.output}</code></td>
                    <td style={{fontSize:'.72rem'}}>{s.method}</td>
                    <td style={{fontSize:'.72rem'}}>{s.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="section-label">⚖️ Ethics & Bias Analysis · CO6</div>
          <div className="card card-sm" style={{fontSize:'.84rem',lineHeight:1.7}}>
            <p><strong>Language equity:</strong> Telugu, Hindi, and English receive equal processing priority.</p>
            <p><strong>Urgency bias check:</strong> CRITICAL routing not dependent on language used — same path for all 3.</p>
            <p><strong>Rule-based fallback:</strong> No LLM required — offline parsing prevents data leakage.</p>
            <p><strong>Accessibility:</strong> Wheelchair/mobility profiles considered in routing constraints (CO3 CSP).</p>
            <p style={{marginTop:8,color:'#92400e'}}>⚠️ This system is a demonstration prototype. Real deployment requires clinical validation and bias auditing by healthcare professionals.</p>
          </div>
        </>
      )}

      {!result && !loading && (
        <div className="empty-state">
          <div className="icon">🌐</div>
          <p>Type or select a demo query above to see the NLP pipeline in action.<br/>
          Supports Telugu · Hindi · English · Roman transliteration</p>
        </div>
      )}
    </div>
  )
}
