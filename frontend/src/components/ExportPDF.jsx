/**
 * ExportPDF.jsx
 * Generates a clean printable HTML page for a search result and triggers window.print()
 */

function buildHTML({ result, algo, prof, start, goal, nlp }) {
  const path  = result?.path  || []
  const cost  = result?.cost  || 0
  const stats = result?.stats || {}

  const CMPLX  = { bfs:'O(V+E)', dfs:'O(V+E)', ucs:'O((V+E)logV)', astar:'O((V+E)logV)' }
  const OPTIM  = { bfs:'Hops only (not cost-optimal)', dfs:'❌ Not optimal', ucs:'✅ Cost-optimal', astar:'✅ Cost-optimal + guided' }
  const ALGO_L = { bfs:'🌊 BFS', dfs:'🔦 DFS', ucs:'💰 UCS', astar:'⭐ A*' }

  const now = new Date().toLocaleString('en-IN', { dateStyle:'medium', timeStyle:'short' })

  const pathHTML = path.map((n,i) => `
    <span class="path-node">${n.replace(/_/g,' ')}</span>
    ${i < path.length-1 ? '<span class="arrow">→</span>' : ''}
  `).join('')

  const nlpSection = nlp ? `
    <div class="section">
      <div class="section-title">🌐 NLP Query Analysis · CO6</div>
      <table class="info-table">
        <tr><td>Query</td><td><strong>${nlp.raw_text || '—'}</strong></td></tr>
        <tr><td>Language</td><td>${{te:'🇮🇳 Telugu', hi:'🇮🇳 Hindi', en:'🌐 English'}[nlp.language] || nlp.language}</td></tr>
        <tr><td>Intent / Destination</td><td>${nlp.target_friendly || '—'}</td></tr>
        <tr><td>Urgency</td><td><span class="badge urg-${(nlp.urgency?.level||'normal').toLowerCase()}">${nlp.urgency?.level || '—'}</span></td></tr>
        <tr><td>Routing hint</td><td>${nlp.urgency?.routing_hint || '—'}</td></tr>
        <tr><td>Method</td><td>${nlp.llm_used ? 'Claude/Gemini LLM' : 'Rule-based (offline)'}</td></tr>
      </table>
    </div>
  ` : ''

  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Charité AI — Path Report</title>
  <style>
    * { margin:0; padding:0; box-sizing:border-box; }
    body {
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #fff;
      color: #111827;
      padding: 36px 48px;
      font-size: 13px;
      line-height: 1.6;
    }

    /* Header */
    .header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      padding-bottom: 16px;
      border-bottom: 3px solid #b45309;
      margin-bottom: 24px;
    }
    .header-left h1 { font-size: 1.4rem; font-weight: 900; color: #111827; letter-spacing: -.3px; }
    .header-left p  { font-size: .8rem; color: #6b7280; margin-top: 2px; }
    .header-right   { text-align: right; font-size: .75rem; color: #6b7280; }
    .header-right strong { color: #b45309; display: block; font-size: .9rem; }

    /* Badges */
    .co-badge {
      display: inline-block;
      padding: 2px 8px; border-radius: 20px;
      font-size: .65rem; font-weight: 700;
      margin: 0 3px;
    }
    .co1 { background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; }
    .co2 { background:#ecfeff; color:#0891b2; border:1px solid #a5f3fc; }
    .co3 { background:#f5f3ff; color:#7c3aed; border:1px solid #ddd6fe; }
    .co6 { background:#fdf2f8; color:#be185d; border:1px solid #fbcfe8; }

    .urg-critical { background:#fef2f2; color:#dc2626; border:1px solid #fecaca; padding:2px 8px; border-radius:20px; font-weight:700; }
    .urg-high     { background:#fffbeb; color:#d97706; border:1px solid #fde68a; padding:2px 8px; border-radius:20px; font-weight:700; }
    .urg-normal   { background:#f0fdf4; color:#16a34a; border:1px solid #bbf7d0; padding:2px 8px; border-radius:20px; font-weight:700; }

    /* Sections */
    .section { margin-bottom: 22px; }
    .section-title {
      font-size: .72rem; font-weight: 800; letter-spacing: 1px;
      text-transform: uppercase; color: #9ca3af;
      border-bottom: 1px solid #f3e8d8;
      padding-bottom: 5px; margin-bottom: 12px;
    }

    /* Metrics row */
    .metrics { display: flex; gap: 12px; margin-bottom: 16px; }
    .metric  {
      flex: 1; background: #faf7f2; border: 1px solid #e8d9c4;
      border-radius: 8px; padding: 12px 14px; text-align: center;
    }
    .metric-val { font-size: 1.5rem; font-weight: 800; color: #b45309; letter-spacing: -1px; }
    .metric-lbl { font-size: .62rem; font-weight: 700; color: #6b7280;
                  text-transform: uppercase; letter-spacing: .5px; margin-top: 3px; }

    /* Path */
    .path-box {
      background: linear-gradient(135deg,#fef3c7,#f0fdf4);
      border: 1px solid #fcd34d; border-radius: 10px;
      padding: 14px 18px; margin-bottom: 16px;
      line-height: 2;
    }
    .path-node {
      display: inline-block;
      background: #fff; border: 1px solid #e8d9c4;
      border-radius: 4px; padding: 2px 8px;
      font-size: .78rem; font-weight: 600; color: #111827;
      margin: 2px;
    }
    .arrow { color: #9ca3af; margin: 0 2px; font-size: .9rem; }

    /* Info table */
    .info-table { width: 100%; border-collapse: collapse; }
    .info-table td {
      padding: 6px 10px; border-bottom: 1px solid #f3e8d8;
      font-size: .82rem; vertical-align: top;
    }
    .info-table td:first-child {
      font-weight: 700; color: #6b7280; width: 160px;
      text-transform: uppercase; font-size: .7rem; letter-spacing: .4px;
    }

    /* Algorithm card */
    .algo-card {
      display: flex; gap: 16px; flex-wrap: wrap;
      background: #faf7f2; border: 1px solid #e8d9c4;
      border-radius: 8px; padding: 12px 16px;
    }
    .algo-item { flex: 1; min-width: 120px; }
    .algo-item-lbl { font-size: .65rem; font-weight:800; text-transform:uppercase;
                     letter-spacing:.5px; color:#9ca3af; margin-bottom:3px; }
    .algo-item-val { font-size: .88rem; font-weight: 700; color: #111827; }

    /* Footer */
    .footer {
      margin-top: 32px; padding-top: 14px;
      border-top: 1px solid #e8d9c4;
      display: flex; justify-content: space-between;
      font-size: .72rem; color: #9ca3af;
    }

    /* Result status */
    .status-ok  { background:#f0fdf4; border:1px solid #bbf7d0; color:#15803d;
                  border-radius:6px; padding:8px 12px; margin-bottom:14px; font-weight:600; }
    .status-err { background:#fef2f2; border:1px solid #fecaca; color:#991b1b;
                  border-radius:6px; padding:8px 12px; margin-bottom:14px; font-weight:600; }

    @media print {
      body { padding: 20px 30px; }
      @page { margin: 1cm; size: A4; }
    }
  </style>
</head>
<body>

  <div class="header">
    <div class="header-left">
      <h1>🏥 Charité Hospital AI Navigator</h1>
      <p>Campus Mitte · Berlin &nbsp;·&nbsp; 2500032630 CFAI Project</p>
      <div style="margin-top:8px">
        <span class="co-badge co1">CO1</span>
        <span class="co-badge co2">CO2</span>
        <span class="co-badge co3">CO3</span>
        ${nlp ? '<span class="co-badge co6">CO6</span>' : ''}
      </div>
    </div>
    <div class="header-right">
      <strong>Path Report</strong>
      Generated: ${now}<br/>
      Profile: <strong>${prof}</strong>
    </div>
  </div>

  <!-- Status -->
  ${path.length > 0
    ? `<div class="status-ok">✅ Path found — ${path.length} hops · ${cost.toFixed(0)}s travel time</div>`
    : `<div class="status-err">❌ No path found for profile "${prof}" — CSP constraints block access.</div>`
  }

  <!-- Metrics -->
  ${path.length > 0 ? `
  <div class="metrics">
    <div class="metric">
      <div class="metric-val">${path.length}</div>
      <div class="metric-lbl">Hops</div>
    </div>
    <div class="metric">
      <div class="metric-val">${cost.toFixed(0)}s</div>
      <div class="metric-lbl">Travel Time</div>
    </div>
    <div class="metric">
      <div class="metric-val">${stats.expansions ?? '—'}</div>
      <div class="metric-lbl">Nodes Expanded</div>
    </div>
    <div class="metric">
      <div class="metric-val">${stats.peak_frontier ?? '—'}</div>
      <div class="metric-lbl">Peak Frontier</div>
    </div>
  </div>` : ''}

  <!-- Path -->
  ${path.length > 0 ? `
  <div class="section">
    <div class="section-title">🗺️ Computed Path · CO2</div>
    <div class="path-box">${pathHTML}</div>
  </div>` : ''}

  <!-- Algorithm -->
  <div class="section">
    <div class="section-title">🧠 Algorithm Details · CO2</div>
    <div class="algo-card">
      <div class="algo-item">
        <div class="algo-item-lbl">Algorithm</div>
        <div class="algo-item-val">${ALGO_L[algo] || algo.toUpperCase()}</div>
      </div>
      <div class="algo-item">
        <div class="algo-item-lbl">Time Complexity</div>
        <div class="algo-item-val">${CMPLX[algo] || '—'}</div>
      </div>
      <div class="algo-item">
        <div class="algo-item-lbl">Space Complexity</div>
        <div class="algo-item-val">O(V)</div>
      </div>
      <div class="algo-item">
        <div class="algo-item-lbl">Optimal?</div>
        <div class="algo-item-val">${OPTIM[algo] || '—'}</div>
      </div>
      ${algo === 'astar' ? `
      <div class="algo-item">
        <div class="algo-item-lbl">Heuristic h(n)</div>
        <div class="algo-item-val">|floor_goal − floor_n| × 12s</div>
      </div>` : ''}
    </div>
  </div>

  <!-- Route details -->
  <div class="section">
    <div class="section-title">📋 Route Details · CO1 (PEAS Agent)</div>
    <table class="info-table">
      <tr><td>Start Node</td><td><strong>${start.replace(/_/g,' ')}</strong></td></tr>
      <tr><td>Goal Node</td><td><strong>${goal.replace(/_/g,' ')}</strong></td></tr>
      <tr><td>Access Profile</td><td><strong>${prof}</strong></td></tr>
      <tr><td>Total Hops</td><td>${path.length}</td></tr>
      <tr><td>Total Cost</td><td>${cost.toFixed(1)} seconds estimated travel</td></tr>
      <tr><td>Nodes Expanded</td><td>${stats.expansions ?? '—'}</td></tr>
      <tr><td>Full Path</td><td style="font-family:monospace;font-size:.75rem">${path.join(' → ')}</td></tr>
    </table>
  </div>

  <!-- NLP section (if available) -->
  ${nlpSection}

  <div class="footer">
    <span>2500032630 · CFAI Project · Charité Campus Mitte · CO1–CO6</span>
    <span>github.com/Sai0Nikhil/CFAI_Project</span>
  </div>

</body>
</html>`
}

export function exportToPDF({ result, algo, prof, start, goal, nlp = null }) {
  const html = buildHTML({ result, algo, prof, start, goal, nlp })
  const win  = window.open('', '_blank', 'width=900,height=700')
  win.document.write(html)
  win.document.close()
  win.onload = () => {
    setTimeout(() => {
      win.print()
    }, 400)
  }
}

// Button component — drop this anywhere
export default function ExportPDFButton({ result, algo, prof, start, goal, nlp }) {
  const hasResult = result?.path?.length > 0 || result?.path?.length === 0

  return (
    <button
      className="btn btn-secondary"
      disabled={!hasResult}
      title={!hasResult ? 'Run a search first' : 'Export path report as PDF'}
      onClick={() => exportToPDF({ result, algo, prof, start, goal, nlp })}
      style={{ display:'flex', alignItems:'center', gap:6 }}
    >
      📄 Export PDF
    </button>
  )
}
