/**
 * AIInsight.jsx
 * Reusable Claude/Gemini explanation card.
 * Drop <AIInsight module="search" context={...} /> anywhere after a result.
 */
import { useState, useEffect, useRef } from 'react'
import { useAI } from '../context/AIContext'
import axios from 'axios'

export default function AIInsight({ module, context, trigger = 0 }) {
  const { isReady, provider, apiKey, model } = useAI()
  const [text, setText]       = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState('')
  const prevTrigger = useRef(-1)

  useEffect(() => {
    // Run whenever trigger changes (new result) AND AI is ready AND context exists
    if (!isReady) return
    if (trigger === 0) return
    if (trigger === prevTrigger.current) return
    prevTrigger.current = trigger

    const ctx = typeof context === 'function' ? context() : context
    if (!ctx || Object.keys(ctx).length === 0) return

    setLoading(true); setText(''); setError('')
    axios.post('/api/ai/explain', {
      module,
      context: ctx,
      provider,
      api_key: apiKey,
      model,
    })
      .then(r => setText(r.data.explanation))
      .catch(e => setError(e.response?.data?.detail || 'AI explanation failed'))
      .finally(() => setLoading(false))
  }, [trigger, isReady, provider, apiKey, model])

  if (!isReady) return null

  return (
    <div style={{
      background: loading ? '#fff8f0' : error ? '#fef2f2' : '#fffdf9',
      border: `1px solid ${loading ? '#e8d9c4' : error ? '#fecaca' : '#fcd34d'}`,
      borderRadius: 10,
      padding: '12px 16px',
      marginTop: 12,
      transition: 'all .2s',
    }}>
      {/* Header */}
      <div style={{ display:'flex', alignItems:'center', gap:8, marginBottom: loading || text || error ? 8 : 0 }}>
        <span style={{ fontSize:'1rem' }}>🤖</span>
        <span style={{
          fontSize: '.72rem', fontWeight: 800, letterSpacing: '.5px',
          textTransform: 'uppercase', color: '#92400e',
        }}>
          {provider === 'claude' ? 'Claude' : 'Gemini'} Insight
        </span>
        {loading && (
          <span style={{ fontSize:'.7rem', color:'#a8906e', marginLeft:4 }}>
            thinking
            <DotDot />
          </span>
        )}
      </div>

      {/* Content */}
      {loading && (
        <div style={{ display:'flex', gap:6, alignItems:'center' }}>
          <div style={{ flex:1, height:10, borderRadius:4,
            background:'linear-gradient(90deg,#f3e8d8 25%,#fef3c7 50%,#f3e8d8 75%)',
            backgroundSize:'200% 100%', animation:'shimmerMove 1.4s linear infinite' }} />
          <div style={{ width:'60%', height:10, borderRadius:4,
            background:'linear-gradient(90deg,#f3e8d8 25%,#fef3c7 50%,#f3e8d8 75%)',
            backgroundSize:'200% 100%', animation:'shimmerMove 1.4s linear infinite .2s' }} />
        </div>
      )}

      {error && (
        <div style={{ fontSize:'.8rem', color:'#dc2626' }}>⚠️ {error}</div>
      )}

      {text && !loading && (
        <div style={{
          fontSize: '.84rem', color: '#111827', lineHeight: 1.7,
          whiteSpace: 'pre-wrap',
        }}>
          {text}
        </div>
      )}

      <style>{`
        @keyframes shimmerMove { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
      `}</style>
    </div>
  )
}

function DotDot() {
  return (
    <span>
      {[0, 0.2, 0.4].map(d => (
        <span key={d} style={{
          display:'inline-block', width:4, height:4, borderRadius:'50%',
          background:'#b45309', marginLeft:3,
          animation:`dotPulse 1s ${d}s ease-in-out infinite`,
        }} />
      ))}
      <style>{`@keyframes dotPulse{0%,100%{transform:scale(1);opacity:.4}50%{transform:scale(1.5);opacity:1}}`}</style>
    </span>
  )
}
