import { useEffect, useRef, useState } from 'react'
import { Network } from 'vis-network'
import { DataSet } from 'vis-data'
import { getGraph } from '../api'

// Node type → color mapping (matches pyvis version)
const TYPE_COLOR = {
  entrance:    '#22c55e',
  corridor:    '#94a3b8',
  elevator:    '#3b82f6',
  stairs:      '#f59e0b',
  lobby:       '#a78bfa',
  ward:        '#22c55e',
  icu:         '#ef4444',
  lab:         '#8b5cf6',
  pharmacy:    '#06b6d4',
  office:      '#64748b',
  radiology:   '#8b5cf6',
  default:     '#94a3b8',
}

function nodeColor(type = '') {
  return TYPE_COLOR[type.toLowerCase()] || TYPE_COLOR.default
}

export default function GraphMap({ profile = 'staff', path = [], start = '', goal = '' }) {
  const containerRef = useRef(null)
  const networkRef   = useRef(null)
  const [graphData, setGraphData]   = useState(null)
  const [loading, setLoading]       = useState(true)
  const [selected, setSelected]     = useState(null)   // hovered node info
  const [nodeCount, setNodeCount]   = useState(0)
  const [edgeCount, setEdgeCount]   = useState(0)

  // Fetch graph whenever profile changes
  useEffect(() => {
    setLoading(true)
    getGraph(profile)
      .then(r => { setGraphData(r.data); setNodeCount(r.data.node_count); setEdgeCount(r.data.edge_count) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [profile])

  // Build / update vis-network
  useEffect(() => {
    if (!graphData || !containerRef.current) return

    const pathSet   = new Set(path)
    const pathEdges = new Set(path.slice(0,-1).map((n,i) => `${n}||${path[i+1]}`))

    // ── Nodes ──
    const visNodes = new DataSet(
      graphData.nodes.map(n => {
        const onPath  = pathSet.has(n.id)
        const isStart = n.id === start
        const isGoal  = n.id === goal

        const color = isStart ? '#f59e0b'
                    : isGoal  ? '#ef4444'
                    : onPath  ? '#22c55e'
                    : nodeColor(n.type)

        return {
          id:    n.id,
          label: n.label.replace(/_/g,' ').replace(/\s+/g,' '),
          color: {
            background: color,
            border:     isStart||isGoal ? '#111827' : color,
            highlight:  { background: '#fef3c7', border: '#b45309' },
            hover:      { background: '#fef3c7', border: '#b45309' },
          },
          size:      isStart||isGoal ? 24 : onPath ? 16 : 9,
          font:      { size: onPath||isStart||isGoal ? 11 : 9,
                       color: '#111827', face: 'Inter, system-ui, sans-serif',
                       bold: onPath||isStart||isGoal },
          borderWidth: isStart||isGoal ? 3 : onPath ? 2 : 1,
          shadow:    onPath,
          title:     `<div style="font-family:Inter,sans-serif;padding:6px 10px;font-size:12px;color:#111827">
                        <b>${n.label.replace(/_/g,' ')}</b><br/>
                        Floor ${n.floor} · ${n.type || 'node'}<br/>
                        Wing: ${n.wing || '—'}
                      </div>`,
          // store raw data for click panel
          _raw: n,
        }
      })
    )

    // ── Edges ──
    const visEdges = new DataSet(
      graphData.edges.map((e, i) => {
        const key1  = `${e.source}||${e.target}`
        const key2  = `${e.target}||${e.source}`
        const onPath = pathEdges.has(key1) || pathEdges.has(key2)
        return {
          id:     i,
          from:   e.source,
          to:     e.target,
          color:  { color: onPath ? '#f59e0b' : '#d1c4b0', highlight:'#b45309', hover:'#b45309' },
          width:  onPath ? 4 : 1,
          arrows: onPath ? { to: { enabled:true, scaleFactor:.6 } } : {},
          title:  `${e.via || 'passage'} · ${e.weight}s`,
          smooth: { type:'continuous' },
          shadow: onPath,
        }
      })
    )

    // ── Options ──
    const options = {
      physics: { enabled: false },
      interaction: {
        hover: true,
        tooltipDelay: 100,
        navigationButtons: true,
        keyboard: { enabled: true },
        zoomView: true,
      },
      nodes: { shape:'dot', borderWidth:1 },
      edges: { smooth:{ type:'continuous' } },
      layout: { improvedLayout: true },
    }

    // Destroy previous
    if (networkRef.current) {
      networkRef.current.destroy()
      networkRef.current = null
    }

    const network = new Network(containerRef.current, { nodes: visNodes, edges: visEdges }, options)
    networkRef.current = network

    // Click → show node info
    network.on('click', params => {
      if (params.nodes.length > 0) {
        const id  = params.nodes[0]
        const raw = graphData.nodes.find(n => n.id === id)
        setSelected(raw || null)
      } else {
        setSelected(null)
      }
    })

    // Fit to view after stabilisation
    network.once('stabilized', () => network.fit({ animation: { duration:400, easingFunction:'easeInOutQuad' } }))

    return () => {
      if (networkRef.current) { networkRef.current.destroy(); networkRef.current = null }
    }
  }, [graphData, path, start, goal])

  // Zoom controls
  const zoomIn  = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale()||1)*1.3 })
  const zoomOut = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale()||1)*0.75 })
  const fitAll  = () => networkRef.current?.fit({ animation:{ duration:300 } })

  return (
    <div style={{position:'relative'}}>
      {/* Toolbar */}
      <div style={{display:'flex', alignItems:'center', gap:6, marginBottom:6, flexWrap:'wrap'}}>
        <button onClick={zoomIn}  className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'.72rem'}}>＋ Zoom In</button>
        <button onClick={zoomOut} className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'.72rem'}}>－ Zoom Out</button>
        <button onClick={fitAll}  className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'.72rem'}}>⊡ Fit All</button>
        <div style={{marginLeft:'auto', fontSize:'.72rem', color:'#6b7280'}}>
          {nodeCount} nodes · {edgeCount} edges · profile: <strong>{profile}</strong>
        </div>
      </div>

      {/* Graph container */}
      <div style={{position:'relative', border:'1px solid #e8d9c4', borderRadius:10, overflow:'hidden', background:'#fffdf9'}}>
        {loading && (
          <div style={{position:'absolute',inset:0,display:'flex',alignItems:'center',
            justifyContent:'center',background:'rgba(255,253,249,.8)',zIndex:10}}>
            <div><div className="spinner"/><p style={{marginTop:10,fontSize:'.8rem',color:'#6b7280',textAlign:'center'}}>Loading graph…</p></div>
          </div>
        )}
        <div ref={containerRef} style={{height:380, width:'100%'}} />
      </div>

      {/* Legend */}
      <div style={{display:'flex', gap:12, flexWrap:'wrap', marginTop:8, fontSize:'.7rem', color:'#6b7280'}}>
        {[['#f59e0b','Start'],['#ef4444','Goal'],['#22c55e','Path'],['#3b82f6','Elevator'],['#8b5cf6','Lab/ICU'],['#94a3b8','Corridor']].map(([c,l])=>(
          <span key={l} style={{display:'flex',alignItems:'center',gap:4}}>
            <span style={{width:10,height:10,borderRadius:'50%',background:c,display:'inline-block'}}/>
            {l}
          </span>
        ))}
      </div>

      {/* Node info panel */}
      {selected && (
        <div style={{marginTop:10, background:'#fef3c7', border:'1px solid #fcd34d',
          borderRadius:8, padding:'10px 14px', fontSize:'.82rem', lineHeight:1.7}}>
          <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start'}}>
            <div>
              <strong>{selected.label?.replace(/_/g,' ')}</strong>
              <div style={{fontSize:'.72rem',color:'#92400e',fontFamily:'monospace'}}>{selected.id}</div>
            </div>
            <button onClick={()=>setSelected(null)}
              style={{background:'none',border:'none',cursor:'pointer',fontSize:'.8rem',color:'#92400e'}}>✕</button>
          </div>
          <div style={{marginTop:6, display:'flex', gap:12, flexWrap:'wrap'}}>
            <span>Floor: <strong>{selected.floor}</strong></span>
            <span>Type: <strong>{selected.type}</strong></span>
            <span>Wing: <strong>{selected.wing||'—'}</strong></span>
          </div>
        </div>
      )}
    </div>
  )
}
