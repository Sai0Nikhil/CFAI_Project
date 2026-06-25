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

export default function GraphMap({ profile = 'staff', path = [], start = '', goal = '', autoZoomPath = true, pathOnly = false, hospital = 'charite' }) {
  const containerRef = useRef(null)
  const networkRef   = useRef(null)
  const [graphData, setGraphData]   = useState(null)
  const [loading, setLoading]       = useState(true)
  const [selected, setSelected]     = useState(null)   // hovered node info
  const [nodeCount, setNodeCount]   = useState(0)
  const [edgeCount, setEdgeCount]   = useState(0)

  // Fetch graph whenever profile OR hospital changes
  useEffect(() => {
    setLoading(true)
    getGraph(profile, hospital)
      .then(r => { setGraphData(r.data); setNodeCount(r.data.node_count); setEdgeCount(r.data.edge_count) })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [profile, hospital])

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

        // Hide completely if there is an active path and this node is not part of it
        const hideNode = (pathOnly || path.length > 0) && !onPath && !isStart && !isGoal

        const color = isStart ? '#f59e0b'
                    : isGoal  ? '#ef4444'
                    : onPath  ? '#22c55e'
                    : nodeColor(n.type)

        return {
          id:    n.id,
          label: n.label.replace(/_/g,' ').replace(/\s+/g,' '),
          hidden: hideNode,
          color: {
            background: color,
            border: isStart ? '#92400e'
                  : isGoal  ? '#7f1d1d'
                  : onPath  ? '#166534'
                  : '#c4a882',
            highlight: { background: '#fef3c7', border: '#b45309' },
            hover:     { background: '#fef3c7', border: '#b45309' },
          },
          size:        isStart||isGoal ? 28 : onPath ? 20 : 8,
          font: {
            size:  isStart||isGoal ? 13 : onPath ? 11 : 8,
            color: isStart||isGoal ? '#111827' : onPath ? '#111827' : '#6b7280',
            face:  'Inter, system-ui, sans-serif',
            bold:  onPath || isStart || isGoal,
            background: onPath ? 'rgba(255,255,255,0.85)' : undefined,
          },
          borderWidth:      isStart||isGoal ? 4 : onPath ? 3 : 1,
          borderWidthSelected: 4,
          shadow: onPath || isStart || isGoal
            ? { enabled:true, color:'rgba(0,0,0,.25)', size:10, x:2, y:2 }
            : false,
          title: `<div style="font-family:Inter,sans-serif;padding:8px 12px;font-size:12px;color:#111827;min-width:140px">
                    <b style="font-size:13px">${n.label.replace(/_/g,' ')}</b><br/>
                    <span style="color:#6b7280">Floor ${n.floor} · ${n.type || 'node'}</span><br/>
                    ${onPath ? '<span style="color:#15803d;font-weight:700">✅ On path</span>' : ''}
                    ${isStart ? '<span style="color:#b45309;font-weight:700">🟡 Start</span>' : ''}
                    ${isGoal  ? '<span style="color:#dc2626;font-weight:700">🔴 Goal</span>' : ''}
                  </div>`,
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

        const hideEdge = (pathOnly || path.length > 0) && !onPath

        return {
          id:     i,
          from:   e.source,
          to:     e.target,
          hidden: hideEdge,
          color:  {
            color:     onPath ? '#f59e0b' : '#ddd0bb',
            highlight: '#b45309',
            hover:     '#b45309',
          },
          width:  onPath ? 6 : 1,
          arrows: onPath ? { to: { enabled:true, scaleFactor:.8, type:'arrow' } } : {},
          title:  `<div style="font-family:Inter,sans-serif;padding:4px 8px;font-size:11px">
                    ${e.via || 'passage'} · <b>${e.weight}s</b>
                    ${onPath ? ' · <span style="color:#15803d">✅ path</span>' : ''}
                  </div>`,
          smooth: { type:'curvedCW', roundness: onPath ? 0 : 0.1 },
          shadow: onPath
            ? { enabled:true, color:'rgba(245,158,11,.4)', size:8, x:0, y:0 }
            : false,
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
      nodes: { shape: 'dot', borderWidth: 1 },
      edges: { smooth: { type: 'continuous' } },
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

    // After stabilisation: zoom to path if one exists, else fit all
    network.once('stabilized', () => {
      if (autoZoomPath && path.length > 1) {
        // Zoom to just the path nodes with padding
        network.fit({
          nodes: path,
          animation: { duration: 700, easingFunction: 'easeInOutQuad' },
        })
      } else {
        network.fit({ animation: { duration: 400, easingFunction: 'easeInOutQuad' } })
      }
    })

    return () => {
      if (networkRef.current) { networkRef.current.destroy(); networkRef.current = null }
    }
  }, [graphData, path, start, goal, pathOnly])

  // Zoom controls
  const zoomIn    = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale()||1)*1.3 })
  const zoomOut   = () => networkRef.current?.moveTo({ scale: (networkRef.current.getScale()||1)*0.75 })
  const fitAll    = () => networkRef.current?.fit({ animation:{ duration:300 } })
  const fitPath   = () => {
    if (path.length > 1)
      networkRef.current?.fit({ nodes: path, animation:{ duration:500, easingFunction:'easeInOutQuad' } })
  }

  return (
    <div style={{position:'relative'}}>

      {/* ── Path breadcrumb strip ─────────────────────────────────────── */}
      {path.length > 0 && (
        <div style={{
          display:'flex', alignItems:'center', flexWrap:'wrap', gap:4,
          background:'linear-gradient(135deg,#f0fdf4,#dcfce7)',
          border:'2px solid #22c55e', borderRadius:10,
          padding:'10px 14px', marginBottom:10,
          fontSize:'.78rem', fontWeight:600,
        }}>
          <span style={{color:'#15803d', fontWeight:800, marginRight:4}}>🗺️ Route:</span>
          {path.map((node, i) => (
            <span key={node} style={{display:'flex', alignItems:'center', gap:4}}>
              <span style={{
                background: i===0 ? '#f59e0b' : i===path.length-1 ? '#ef4444' : '#22c55e',
                color:'#fff', borderRadius:6, padding:'2px 8px',
                fontSize:'.72rem', fontWeight:700, whiteSpace:'nowrap',
                boxShadow:'0 1px 3px rgba(0,0,0,.15)',
              }}>
                {i===0 ? '🟡 ' : i===path.length-1 ? '🔴 ' : ''}{node.replace(/_/g,' ')}
              </span>
              {i < path.length-1 && <span style={{color:'#15803d', fontWeight:900}}>→</span>}
            </span>
          ))}
          <span style={{marginLeft:'auto', color:'#15803d', fontSize:'.7rem'}}>
            {path.length} stops
          </span>
        </div>
      )}

      {/* Toolbar */}
      <div style={{display:'flex', alignItems:'center', gap:6, marginBottom:6, flexWrap:'wrap'}}>
        <button onClick={zoomIn}  className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'.72rem'}}>＋ Zoom In</button>
        <button onClick={zoomOut} className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'.72rem'}}>－ Zoom Out</button>
        <button onClick={fitAll}  className="btn btn-secondary" style={{padding:'4px 10px',fontSize:'.72rem'}}>⊡ Fit All</button>
        {path.length > 1 && (
          <button onClick={fitPath}
            style={{padding:'4px 12px', fontSize:'.72rem', fontWeight:700,
              background:'#fef3c7', border:'1px solid #fcd34d', borderRadius:6,
              cursor:'pointer', color:'#92400e', fontFamily:'inherit'}}>
            🟡 Zoom to Path
          </button>
        )}
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
        <div ref={containerRef} style={{height:420, width:'100%'}} />
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
