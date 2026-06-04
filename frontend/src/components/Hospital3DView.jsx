/**
 * Hospital3DView.jsx  —  Google Maps-style 3D campus
 * Isometric projection, shadows, ground textures, roads, trees
 */
import { useEffect, useRef, useCallback } from 'react'

// ─── World units: 1 unit ≈ 5 metres ─────────────────────────────────────────

const CHARITE = {
  ground: { x: -30, z: -20, w: 240, d: 160 },
  roads: [
    { x: 70, z: -20, w: 8, d: 160 },   // vertical road between buildings
    { x: -30, z: 60, w: 240, d: 8 },   // horizontal road
  ],
  trees: [
    {x:-15,z:10},{x:-15,z:30},{x:-15,z:50},
    {x:210,z:15},{x:210,z:35},{x:210,z:55},
    {x:30,z:140},{x:90,z:140},{x:150,z:140},
  ],
  buildings: [
    {
      id:'bettenhaus', label:'Bettenhaus Tower',
      sub:'21 floors · 615 beds · 14 departments',
      x:0, z:0, w:60, d:40, h:200,
      face:'#e8edf5', side:'#c5cdd8', roof:'#d4dae4',
      accent:'#1d4ed8',
      info:['G — Lobby · Reception','F1 — ENT · Ortho · Bridge Level',
            'F5 — Neurology · Stroke Unit','F7 — Cardiology · Cath Lab',
            'F15 — Oncology','F21 — Admin'],
    },
    {
      id:'rnb', label:'Rudolf-Nissen-Haus',
      sub:'5 floors · 15 OTs · 70 ICU beds',
      x:80, z:8, w:50, d:35, h:55,
      face:'#fde8e8', side:'#f0c8c8', roof:'#f5d5d5',
      accent:'#dc2626',
      info:['G — Central Emergency (Philippstr.)','F1 — ICU 70 beds · Neuro-ICU',
            'F2–3 — 15 Modular OTs incl. 2 Hybrid ORs'],
    },
    {
      id:'historic', label:'Historic Wing',
      sub:'Built 1897–1917 · Outpatient',
      x:-88, z:5, w:75, d:45, h:28,
      face:'#fef3e2', side:'#f0d9aa', roof:'#f5e2bb',
      accent:'#d97706',
      info:['G — OPD · Pharmacy · Blood Bank',
            'F1 — Radiology (Luisenstr. 10) · Physio · Labs',
            'F2 — Rahel Hirsch Center · Microbiology'],
    },
    {
      id:'bridge', label:'Glass Bridge',
      sub:'Crosses Luisenstraße at F1 level',
      x:-15, z:18, w:12, d:6, h:8,
      face:'#bfdbfe88', side:'#93c5fd66', roof:'#60a5fa99',
      accent:'#38bdf8', glass:true,
      info:['Connects Bettenhaus ↔ Historic Wing'],
    },
  ],
}

const AIIMS = {
  ground: { x: -130, z: -100, w: 340, d: 240 },
  roads: [
    { x: -130, z: 20, w: 340, d: 8 },
    { x: -10,  z:-100, w: 8, d: 240 },
    { x: 85,   z:-100, w: 8, d: 240 },
  ],
  trees: [
    {x:-110,z:-80},{x:-110,z:-50},{x:-110,z:-20},{x:-110,z:10},
    {x:200,z:-80},{x:200,z:-50},{x:200,z:-20},{x:200,z:10},
    {x:-40,z:125},{x:20,z:125},{x:80,z:125},{x:140,z:125},
    {x:-100,z:125},{x:-60,z:-90},{x:60,z:-90},{x:120,z:-90},
  ],
  buildings: [
    {
      id:'ipd', label:'IPD Block',
      sub:'8 floors · 960 beds · Main Hospital',
      x:0, z:0, w:75, d:55, h:160,
      face:'#e8edf5', side:'#c5cdd8', roof:'#d4dae4',
      accent:'#1d4ed8',
      info:['G — Casualty · Dialysis (30 beds) · Blood Bank',
            'F1 — Radiology · CT/MRI · PET Scan · Labs',
            'F2 — Gen Medicine · MICU (20 beds)',
            'F3 — Paediatrics (60 beds) · PICU · NICU ✓',
            'F5 — Cardiology · Cath Lab','F6 — Oncology · LINAC',
            'F7 — Nephrology · Urology'],
    },
    {
      id:'opd', label:'OPD Block',
      sub:'2 floors · 3000–3500 patients/day',
      x:-115, z:15, w:70, d:50, h:26,
      face:'#e8f5ee', side:'#c2dfc9', roof:'#d4edda',
      accent:'#059669',
      info:['G — Registration · ABHA Kiosk · Jan Aushadhi',
            'F1 — ENT · Ophthalmology · Ortho · Psych',
            'F2 — Gen Medicine OPD (official) · OBG · Neurology'],
    },
    {
      id:'ot', label:'OT Complex',
      sub:'8 Modular + 2 Trauma OTs',
      x:95, z:8, w:60, d:45, h:48,
      face:'#fde8e8', side:'#f0c8c8', roof:'#f5d5d5',
      accent:'#dc2626',
      info:['G — Emergency · Pre-Op · Recovery Room',
            'F1 — Modular OTs 1–8',
            'F2–3 — Trauma OTs + Hybrid OTs (imaging)'],
    },
    {
      id:'academic', label:'Academic Block',
      sub:'Medical College · 125 MBBS seats',
      x:-110, z:-85, w:65, d:45, h:34,
      face:'#f0ebff', side:'#d8caf5', roof:'#e4daff',
      accent:'#7c3aed',
      info:['G — Anatomy Hall · Simulation Lab',
            'F1 — Library · Lecture Halls A & B',
            'F2 — Research Lab · VRDL · Molecular Biology'],
    },
  ],
}

// ─── Isometric projection ─────────────────────────────────────────────────────

function iso(x, y, z, angle, tilt, scale, cx, cy) {
  const ca = Math.cos(angle), sa = Math.sin(angle)
  const rx = x * ca + z * sa
  const rz = -x * sa + z * ca
  const ct = Math.cos(tilt), st = Math.sin(tilt)
  const sx = cx + rx * scale
  const sy = cy - (y * ct - rz * st) * scale
  return [sx, sy]
}

// ─── Draw helpers ─────────────────────────────────────────────────────────────

function poly(ctx, pts, fill, stroke, lw = 0.5) {
  if (!pts.length) return
  ctx.beginPath()
  ctx.moveTo(pts[0][0], pts[0][1])
  for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0], pts[i][1])
  ctx.closePath()
  if (fill)  { ctx.fillStyle = fill;    ctx.fill()   }
  if (stroke){ ctx.strokeStyle = stroke; ctx.lineWidth = lw; ctx.stroke() }
}

function drawTree(ctx, x, z, angle, tilt, scale, cx, cy) {
  const base = iso(x, 0, z, angle, tilt, scale, cx, cy)
  const top  = iso(x, 12, z, angle, tilt, scale, cx, cy)
  // trunk
  ctx.strokeStyle = '#78350f'
  ctx.lineWidth = 1.5
  ctx.beginPath(); ctx.moveTo(base[0], base[1]); ctx.lineTo(top[0], top[1]); ctx.stroke()
  // canopy
  ctx.beginPath()
  ctx.arc(top[0], top[1], 5, 0, Math.PI * 2)
  ctx.fillStyle = '#16a34a'
  ctx.fill()
  ctx.strokeStyle = '#15803d'
  ctx.lineWidth = 0.5
  ctx.stroke()
}

function drawBuilding(ctx, b, angle, tilt, scale, cx, cy, isHov) {
  const {x, z, w, d, h, face, side, roof, glass} = b

  // 8 corners
  const c = (bx, by, bz) => iso(bx, by, bz, angle, tilt, scale, cx, cy)

  const B = [
    c(x,   0, z),   c(x+w, 0, z),   c(x+w, 0, z+d), c(x,   0, z+d),
    c(x,   h, z),   c(x+w, h, z),   c(x+w, h, z+d), c(x,   h, z+d),
  ]

  // Determine visible faces from angle
  const a = ((angle % (Math.PI*2)) + Math.PI*2) % (Math.PI*2)
  const showF = a < Math.PI          // front face (low z)
  const showR = a > Math.PI*0.5 && a < Math.PI*1.5  // right face (high x)
  const showB = a >= Math.PI         // back face (high z)
  const showL = a <= Math.PI*0.5 || a >= Math.PI*1.5 // left face (low x)

  const alpha = isHov ? 'ff' : 'f0'
  const highlight = isHov ? 'ffffffaa' : null

  // Shadow on ground
  if (!glass) {
    const sh = 0.3
    const sx = iso(x+w*0.5 + 8, 0, z+d*0.5 + 8, angle, tilt, scale, cx, cy)
    ctx.save()
    ctx.globalAlpha = 0.18
    poly(ctx, [
      iso(x+4,   0, z+4,   angle, tilt, scale, cx, cy),
      iso(x+w+4, 0, z+4,   angle, tilt, scale, cx, cy),
      iso(x+w+4, 0, z+d+4, angle, tilt, scale, cx, cy),
      iso(x+4,   0, z+d+4, angle, tilt, scale, cx, cy),
    ], '#000000', null)
    ctx.restore()
  }

  // Front face (z)
  if (showF) {
    poly(ctx, [B[0],B[1],B[5],B[4]], face + alpha, '#00000022', 0.5)
    if (!glass) drawWindows(ctx, b, 'front', angle, tilt, scale, cx, cy, isHov)
  }
  // Back face
  if (showB) {
    poly(ctx, [B[3],B[2],B[6],B[7]], face + alpha, '#00000022', 0.5)
  }
  // Right face (x+w)
  if (showR) {
    poly(ctx, [B[1],B[2],B[6],B[5]], side + alpha, '#00000022', 0.5)
    if (!glass) drawWindows(ctx, b, 'right', angle, tilt, scale, cx, cy, isHov)
  }
  // Left face
  if (showL) {
    poly(ctx, [B[0],B[3],B[7],B[4]], side + alpha, '#00000022', 0.5)
  }

  // Roof
  const roofAlpha = isHov ? 'ff' : 'f8'
  poly(ctx, [B[4],B[5],B[6],B[7]], roof + roofAlpha, '#00000033', 0.8)

  // Accent stripe on rooftop edge
  if (!glass && b.accent) {
    const edgeH = Math.max(h * 0.04, 3)
    if (showF)
      poly(ctx,
        [c(x,h,z), c(x+w,h,z), c(x+w,h+edgeH,z), c(x,h+edgeH,z)],
        b.accent + '88', null)
  }

  // Hover glow outline
  if (isHov) {
    ctx.save()
    ctx.shadowColor = b.accent || '#ffffff'
    ctx.shadowBlur  = 12
    poly(ctx, [B[0],B[1],B[5],B[4]], null, '#ffffffbb', 1.5)
    ctx.restore()
  }
}

function drawWindows(ctx, b, face, angle, tilt, scale, cx, cy, isHov) {
  const {x, z, w, d, h} = b
  if (h < 15) return
  const c = (bx, by, bz) => iso(bx, by, bz, angle, tilt, scale, cx, cy)

  const rows = Math.min(Math.floor(h / 22), 9)
  if (face === 'front') {
    const cols = Math.min(Math.floor(w / 14), 6)
    for (let r = 1; r <= rows; r++) {
      for (let col = 0; col < cols; col++) {
        const wx  = x + w * (col + 0.25) / cols
        const wx2 = x + w * (col + 0.75) / cols
        const wy  = h * r / (rows + 1) - 3
        const wy2 = h * r / (rows + 1) + 3
        const pts = [c(wx,wy,z), c(wx2,wy,z), c(wx2,wy2,z), c(wx,wy2,z)]
        poly(ctx, pts, isHov ? '#fef3c7cc' : '#dbeafecc', null)
      }
    }
  } else {
    const cols = Math.min(Math.floor(d / 14), 4)
    for (let r = 1; r <= rows; r++) {
      for (let col = 0; col < cols; col++) {
        const wz  = z + d * (col + 0.25) / cols
        const wz2 = z + d * (col + 0.75) / cols
        const wy  = h * r / (rows + 1) - 3
        const wy2 = h * r / (rows + 1) + 3
        const pts = [c(x+w,wy,wz), c(x+w,wy,wz2), c(x+w,wy2,wz2), c(x+w,wy2,wz)]
        poly(ctx, pts, '#dbeafe88', null)
      }
    }
  }
}

function drawLabel(ctx, b, angle, tilt, scale, cx, cy) {
  const c = (bx, by, bz) => iso(bx, by, bz, angle, tilt, scale, cx, cy)
  const top = c(b.x + b.w/2, b.h + 14, b.z + b.d/2)

  const lines = [b.label, b.sub]
  const lineH = 15, pad = 9
  const maxW = Math.max(...lines.map(l => l.length)) * 6 + pad*2
  const boxH = lines.length * lineH + pad * 1.5
  const bx = top[0] - maxW/2, by = top[1] - boxH - 6

  // Box
  ctx.beginPath()
  ctx.roundRect(bx, by, maxW, boxH, 6)
  ctx.fillStyle = '#0f172aee'
  ctx.fill()
  ctx.strokeStyle = (b.accent || '#334155') + '99'
  ctx.lineWidth = 1.2
  ctx.stroke()

  // Lines
  ctx.font = 'bold 10.5px system-ui, sans-serif'
  ctx.fillStyle = '#f1f5f9'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.fillText(b.label, top[0], by + pad * 0.8)

  ctx.font = '9px system-ui, sans-serif'
  ctx.fillStyle = b.accent || '#94a3b8'
  ctx.fillText(b.sub, top[0], by + pad * 0.8 + lineH)

  // Connector dot
  const dot = c(b.x + b.w/2, b.h, b.z + b.d/2)
  ctx.beginPath()
  ctx.arc(dot[0], dot[1], 3, 0, Math.PI*2)
  ctx.fillStyle = b.accent || '#94a3b8'
  ctx.fill()
  ctx.beginPath()
  ctx.moveTo(dot[0], dot[1])
  ctx.lineTo(top[0], by + boxH)
  ctx.strokeStyle = (b.accent || '#94a3b8') + '66'
  ctx.lineWidth = 1
  ctx.stroke()
}

// ─── Main component ───────────────────────────────────────────────────────────

export default function Hospital3DView({ hospital }) {
  const isAIIMS = hospital === 'aiims'
  const data = isAIIMS ? AIIMS : CHARITE
  const canvasRef = useRef(null)
  const stateRef  = useRef({
    angle: isAIIMS ? -0.4 : -0.5,
    tilt: 0.65,
    dragging: false,
    last: {x:0,y:0},
    hovered: null,
    mx: -1, my: -1,
  })
  const rafRef = useRef(null)

  const render = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    const W = canvas.width, H = canvas.height
    const s = stateRef.current
    const scale = isAIIMS ? 0.45 : 0.5
    const cx = W * 0.5, cy = H * 0.58

    ctx.clearRect(0, 0, W, H)

    // Sky gradient
    const sky = ctx.createLinearGradient(0, 0, 0, H)
    sky.addColorStop(0, '#0c1a2e')
    sky.addColorStop(1, '#1e3a5f')
    ctx.fillStyle = sky
    ctx.fillRect(0, 0, W, H)

    const isoP = (x,y,z) => iso(x,y,z, s.angle, s.tilt, scale, cx, cy)

    // Ground
    const {x:gx, z:gz, w:gw, d:gd} = data.ground
    poly(ctx,
      [isoP(gx,0,gz), isoP(gx+gw,0,gz), isoP(gx+gw,0,gz+gd), isoP(gx,0,gz+gd)],
      '#1a3320', '#0d2014', 0.5
    )

    // Roads
    for (const r of data.roads) {
      poly(ctx,
        [isoP(r.x,0,r.z), isoP(r.x+r.w,0,r.z), isoP(r.x+r.w,0,r.z+r.d), isoP(r.x,0,r.z+r.d)],
        '#374151', '#4b5563', 0.3
      )
    }

    // Grid lines on ground
    ctx.globalAlpha = 0.08
    ctx.strokeStyle = '#86efac'
    ctx.lineWidth = 0.4
    for (let gxi = gx; gxi <= gx+gw; gxi += 20) {
      ctx.beginPath()
      const a = isoP(gxi,0,gz), b = isoP(gxi,0,gz+gd)
      ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke()
    }
    for (let gzi = gz; gzi <= gz+gd; gzi += 20) {
      ctx.beginPath()
      const a = isoP(gx,0,gzi), b = isoP(gx+gw,0,gzi)
      ctx.moveTo(a[0],a[1]); ctx.lineTo(b[0],b[1]); ctx.stroke()
    }
    ctx.globalAlpha = 1

    // Trees
    for (const t of data.trees)
      drawTree(ctx, t.x, t.z, s.angle, s.tilt, scale, cx, cy)

    // Sort buildings back-to-front
    const cosA = Math.cos(s.angle), sinA = Math.sin(s.angle)
    const bldgs = [...data.buildings].sort((a,b) => {
      const da = (a.x+a.w/2)*(-sinA) + (a.z+a.d/2)*cosA
      const db = (b.x+b.w/2)*(-sinA) + (b.z+b.d/2)*cosA
      return da - db
    })

    // Draw buildings
    for (const b of bldgs)
      drawBuilding(ctx, b, s.angle, s.tilt, scale, cx, cy, s.hovered === b.id)

    // Draw hovered label on top
    if (s.hovered) {
      const bld = data.buildings.find(b => b.id === s.hovered)
      if (bld) drawLabel(ctx, bld, s.angle, s.tilt, scale, cx, cy)
    }

    // Compass
    const cx2 = W - 28, cy2 = H - 28
    ctx.save()
    ctx.translate(cx2, cy2)
    ctx.rotate(-s.angle)
    ctx.font = 'bold 8px system-ui'
    ctx.fillStyle = '#f87171'; ctx.textAlign='center'; ctx.textBaseline='middle'
    ctx.fillText('N', 0, -10)
    ctx.strokeStyle = '#f87171'; ctx.lineWidth=1.2
    ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(0,-8); ctx.stroke()
    ctx.strokeStyle = '#94a3b8'; ctx.lineWidth=1
    ctx.beginPath(); ctx.moveTo(0,0); ctx.lineTo(0,8); ctx.stroke()
    ctx.restore()
  }, [data, isAIIMS])

  useEffect(() => {
    const tick = () => { render(); rafRef.current = requestAnimationFrame(tick) }
    rafRef.current = requestAnimationFrame(tick)
    const auto = setInterval(() => {
      if (!stateRef.current.dragging)
        stateRef.current.angle += 0.003
    }, 16)
    return () => { cancelAnimationFrame(rafRef.current); clearInterval(auto) }
  }, [render])

  const getCanvas = () => canvasRef.current
  const onDown = e => {
    stateRef.current.dragging = true
    stateRef.current.last = {x: e.clientX, y: e.clientY}
  }
  const onMove = e => {
    const s = stateRef.current
    if (s.dragging) {
      s.angle += (e.clientX - s.last.x) * 0.007
      s.tilt   = Math.max(0.25, Math.min(1.1, s.tilt - (e.clientY - s.last.y) * 0.004))
      s.last   = {x: e.clientX, y: e.clientY}
      return
    }
    const canvas = getCanvas(); if (!canvas) return
    const rect  = canvas.getBoundingClientRect()
    const scale = isAIIMS ? 0.45 : 0.5
    const cx = canvas.width * 0.5, cy = canvas.height * 0.58
    const mx = (e.clientX - rect.left) * canvas.width  / rect.width
    const my = (e.clientY - rect.top)  * canvas.height / rect.height
    let found = null
    for (const b of data.buildings) {
      const tl = iso(b.x,     b.h, b.z,     s.angle, s.tilt, scale, cx, cy)
      const br = iso(b.x+b.w, 0,   b.z+b.d, s.angle, s.tilt, scale, cx, cy)
      const minX = Math.min(tl[0],br[0])-6, maxX = Math.max(tl[0],br[0])+6
      const minY = Math.min(tl[1],br[1])-6, maxY = Math.max(tl[1],br[1])+6
      if (mx>=minX&&mx<=maxX&&my>=minY&&my<=maxY){ found=b.id; break }
    }
    s.hovered = found
  }
  const onUp  = () => { stateRef.current.dragging = false }
  const onWheel = e => {
    stateRef.current.tilt = Math.max(0.25, Math.min(1.1, stateRef.current.tilt + e.deltaY * 0.001))
  }

  return (
    <div style={{
      borderRadius: 16, overflow: 'hidden', position: 'relative',
      border: '1px solid #1e3a5f',
      boxShadow: '0 8px 40px rgba(0,0,0,.5)',
    }}>
      <canvas
        ref={canvasRef} width={340} height={270}
        style={{ display:'block', width:'100%', cursor:'grab' }}
        onMouseDown={onDown} onMouseMove={onMove}
        onMouseUp={onUp}     onMouseLeave={onUp}
        onWheel={onWheel}
      />
      <div style={{
        position:'absolute', top:8, left:10,
        display:'flex', gap:6, alignItems:'center'
      }}>
        <span style={{fontSize:'.65rem',fontWeight:800,color:'#94a3b8',letterSpacing:'.5px',textTransform:'uppercase'}}>
          {isAIIMS ? '🇮🇳' : '🇩🇪'} 3D Campus
        </span>
        <span style={{fontSize:'.55rem',color:'#334155',background:'#0f172a99',padding:'2px 7px',borderRadius:99,border:'1px solid #1e3a5f'}}>
          drag · scroll
        </span>
      </div>
    </div>
  )
}
