/**
 * HospitalMapView.jsx
 * Real satellite map — Leaflet + Esri World Imagery (free, no API key)
 * Shows real aerial imagery of Charité Campus Mitte & AIIMS Mangalagiri
 * with building polygon overlays and clickable markers.
 */
import { useEffect, useRef, useState } from 'react'

// ── Real GPS coordinates ──────────────────────────────────────────────────────

const HOSPITALS = {
  charite: {
    name: 'Charité Campus Mitte',
    center: [52.5253, 13.3775],
    zoom: 17,
    polygons: [
      {
        id: 'bettenhaus',
        label: 'Bettenhaus · Luisenstr. 64',
        color: '#3b82f6',
        coords: [
          [52.5257, 13.3765],
          [52.5261, 13.3765],
          [52.5261, 13.3775],
          [52.5257, 13.3775],
        ],
        info: [
          'Luisenstraße 64 — 21 floors · 615 beds',
          'Wards 101i/102i/103i — ICU (confirmed)',
          'Ward OBG/Delivery · Surgery · Neurosurgery · Urology',
          'Patient Admissions · Dialysis · Cafeteria',
        ],
      },
      {
        id: 'rnb',
        label: 'Rudolf-Nissen-Haus · Philippstr. 10',
        color: '#ef4444',
        coords: [
          [52.5261, 13.3776],
          [52.5264, 13.3776],
          [52.5264, 13.3785],
          [52.5261, 13.3785],
        ],
        info: [
          'Philippstraße 10 — Emergency Centre',
          'Ward 100 — Admissions Ward (confirmed)',
          'Central Emergency Dept 24h (confirmed)',
          '15 OTs incl. 2 Hybrid ORs · 70 ICU beds',
        ],
      },
      {
        id: 'diagnostics',
        label: 'Diagnostics · Luisenstr. 7',
        color: '#8b5cf6',
        coords: [
          [52.5247, 13.3762],
          [52.5250, 13.3762],
          [52.5250, 13.3770],
          [52.5247, 13.3770],
        ],
        info: [
          'Luisenstraße 7 — All Imaging',
          'X-Ray · CT · MRI · Mammography · Ultrasound (confirmed)',
          'Nuclear Medicine · Emergency Lab (confirmed)',
          'Nephrology OPD · International Patients',
        ],
      },
      {
        id: 'mvz',
        label: 'MVZ Outpatient · Luisenstr. 13',
        color: '#10b981',
        coords: [
          [52.5250, 13.3762],
          [52.5254, 13.3762],
          [52.5254, 13.3772],
          [52.5250, 13.3772],
        ],
        info: [
          'Luisenstraße 13/13a — MVZ Clinics',
          'Cardiology · Neurology · Dermatology · Psychiatry (confirmed)',
          'Rheumatology · Gynecology · Endocrinology (confirmed)',
          'Gastroenterology · ENT · Pneumonology',
        ],
      },
      {
        id: 'neuro_psych',
        label: 'Neurology & Psychiatry · Bonhoefferweg 3',
        color: '#f59e0b',
        coords: [
          [52.5243, 13.3780],
          [52.5247, 13.3780],
          [52.5247, 13.3790],
          [52.5243, 13.3790],
        ],
        info: [
          'Bonhoefferweg 3 — Neurology & Psychiatry',
          'Ward M116 — Neurology (confirmed)',
          'Ward M116s — Stroke Unit (confirmed)',
          'Psychiatry / Anxiety / Neurological OPD',
        ],
      },
      {
        id: 'research',
        label: 'Sauerbruchweg / Rahel-Hirsch',
        color: '#f97316',
        coords: [
          [52.5248, 13.3790],
          [52.5253, 13.3790],
          [52.5253, 13.3800],
          [52.5248, 13.3800],
        ],
        info: [
          'Sauerbruchweg 3/5 + Rahel-Hirsch-Weg 5',
          'Endoscopy (Internal · Surgery) (confirmed)',
          'Oncology/Haematology OPD · Wards 202/203',
          'Cardiology Functional Diagnostics',
        ],
      },
    ],
    markers: [
      { pos: [52.5254, 13.3762], label: '🚪 Main Entrance', sub: 'Luisenstraße 9 (pedestrian)' },
      { pos: [52.5263, 13.3779], label: '🚨 Emergency 24h', sub: 'Philippstraße 10 · Ward 100' },
      { pos: [52.5259, 13.3770], label: '🌉 Glass Bridge', sub: 'Bettenhaus ↔ Campus at F1' },
      { pos: [52.5248, 13.3766], label: '🩻 Radiology', sub: 'CT · MRI · X-Ray · PET · Luisenstr. 7' },
      { pos: [52.5245, 13.3784], label: '🧠 Neurology', sub: 'Ward M116 · Bonhoefferweg 3' },
    ],
  },

  aiims: {
    name: 'AIIMS Mangalagiri',
    center: [16.4445, 80.5848],
    zoom: 17,
    // Building polygons — AIIMS Mangalagiri campus, Guntur District AP
    polygons: [
      {
        id: 'ipd',
        label: 'IPD Block (Main Hospital)',
        color: '#3b82f6',
        coords: [
          [16.4450, 80.5840],
          [16.4455, 80.5840],
          [16.4455, 80.5852],
          [16.4450, 80.5852],
        ],
        info: [
          '8 floors · 960 beds (500 functional)',
          'G — Casualty · Dialysis (30 beds) · Blood Bank',
          'F1 — Radiology · CT/MRI · PET Scan',
          'F3 — Paediatrics (60 beds) · PICU · NICU ✓',
          'F5 — Cardiology · Cath Lab · CICU',
          'F6 — Oncology · LINAC Suite',
        ],
      },
      {
        id: 'opd',
        label: 'OPD Block',
        color: '#10b981',
        coords: [
          [16.4442, 80.5835],
          [16.4447, 80.5835],
          [16.4447, 80.5843],
          [16.4442, 80.5843],
        ],
        info: [
          '2 floors · 3000–3500 patients/day',
          'G — Registration · ABHA Kiosk · Jan Aushadhi',
          'F1 — ENT · Ophthalmology · Ortho · Psychiatry',
          'F2 — Gen Medicine OPD · OBG · Neurology',
        ],
      },
      {
        id: 'ot',
        label: 'OT Complex',
        color: '#ef4444',
        coords: [
          [16.4450, 80.5854],
          [16.4454, 80.5854],
          [16.4454, 80.5862],
          [16.4450, 80.5862],
        ],
        info: [
          '3 floors · 8 Modular + 2 Trauma OTs',
          'G — Emergency OT · Pre-Op · Recovery',
          'F1 — Modular OTs 1–8',
          'F2–3 — Trauma OTs + Hybrid OTs',
        ],
      },
      {
        id: 'academic',
        label: 'Academic Block',
        color: '#8b5cf6',
        coords: [
          [16.4440, 80.5840],
          [16.4444, 80.5840],
          [16.4444, 80.5850],
          [16.4440, 80.5850],
        ],
        info: [
          'Medical College · 125 MBBS seats',
          'G — Anatomy Hall · Simulation Lab',
          'F1 — Library · Lecture Halls A & B',
          'F2 — Research Lab · VRDL · Molecular Biology',
        ],
      },
    ],
    markers: [
      { pos: [16.4448, 80.5830], label: '🚪 Main Gate', sub: 'NH-16 / Mangalagiri–Amaravati Rd' },
      { pos: [16.4452, 80.5856], label: '🚨 Emergency Gate', sub: '24×7 Casualty · 60 beds' },
      { pos: [16.4444, 80.5845], label: '💊 Jan Aushadhi', sub: 'PM Generic Pharmacy' },
    ],
  },
}

// ── Component ─────────────────────────────────────────────────────────────────

export default function HospitalMapView({ hospital }) {
  const mapRef     = useRef(null)
  const leafletRef = useRef(null)
  const mapObjRef  = useRef(null)
  const layersRef  = useRef([])
  const [expanded, setExpanded] = useState(false)

  // When expanded state changes, tell Leaflet to recalculate size
  useEffect(() => {
    const map = mapObjRef.current
    if (!map) return
    setTimeout(() => map.invalidateSize(), 50)
  }, [expanded])

  // Load Leaflet CSS once
  useEffect(() => {
    if (!document.getElementById('leaflet-css')) {
      const link = document.createElement('link')
      link.id   = 'leaflet-css'
      link.rel  = 'stylesheet'
      link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css'
      document.head.appendChild(link)
    }
  }, [])

  // Init map once
  useEffect(() => {
    let cancelled = false

    async function init() {
      const L = (await import('leaflet')).default
      if (cancelled || !mapRef.current || mapObjRef.current) return
      leafletRef.current = L

      // Fix default icon paths broken by Vite
      delete L.Icon.Default.prototype._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      const data = HOSPITALS[hospital] || HOSPITALS.charite
      const map  = L.map(mapRef.current, { zoomControl: true, attributionControl: true })
      mapObjRef.current = map

      // Esri World Imagery (free satellite, no API key)
      L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        {
          attribution: 'Tiles © Esri — Esri, DigitalGlobe, GeoEye, Earthstar Geographics',
          maxZoom: 20,
        }
      ).addTo(map)

      // Labels overlay (street names on top of satellite)
      L.tileLayer(
        'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
        { maxZoom: 20, opacity: 0.7 }
      ).addTo(map)

      map.setView(data.center, data.zoom)
      addLayers(L, map, data)
    }

    init()
    return () => { cancelled = true }
  }, [])  // eslint-disable-line

  // Update layers when hospital changes
  useEffect(() => {
    const L = leafletRef.current
    const map = mapObjRef.current
    if (!L || !map) return

    // Remove old layers
    layersRef.current.forEach(l => map.removeLayer(l))
    layersRef.current = []

    const data = HOSPITALS[hospital] || HOSPITALS.charite
    map.flyTo(data.center, data.zoom, { duration: 1.5 })
    addLayers(L, map, data)
  }, [hospital])

  function addLayers(L, map, data) {
    const newLayers = []

    // Building polygons
    data.polygons.forEach(p => {
      const poly = L.polygon(p.coords, {
        color:       p.color,
        fillColor:   p.color,
        fillOpacity: 0.25,
        weight:      2.5,
        opacity:     0.9,
      }).addTo(map)

      // Popup content
      const popupHtml = `
        <div style="font-family:system-ui,sans-serif;min-width:200px">
          <div style="font-weight:800;font-size:.9rem;color:${p.color};margin-bottom:6px;border-bottom:1px solid #e5e7eb;padding-bottom:6px">
            ${p.label}
          </div>
          ${p.info.map((line, i) => `
            <div style="font-size:.78rem;color:${i===0?'#374151':'#6b7280'};font-weight:${i===0?'700':'400'};margin-bottom:3px">
              ${i === 0 ? '📊 ' : '· '}${line}
            </div>
          `).join('')}
        </div>
      `
      poly.bindPopup(popupHtml, { maxWidth: 260 })
      poly.on('mouseover', function() { this.setStyle({ fillOpacity: 0.45, weight: 3.5 }) })
      poly.on('mouseout',  function() { this.setStyle({ fillOpacity: 0.25, weight: 2.5 }) })

      newLayers.push(poly)

      // Label in center of polygon
      const bounds = poly.getBounds()
      const center = bounds.getCenter()
      const label = L.marker(center, {
        icon: L.divIcon({
          className: '',
          html: `<div style="
            background:${p.color}cc;color:#fff;
            font-size:.62rem;font-weight:800;
            padding:2px 7px;border-radius:99px;
            white-space:nowrap;
            box-shadow:0 2px 6px rgba(0,0,0,.4);
            border:1px solid ${p.color};
            pointer-events:none;
          ">${p.label.split(' ')[0]}</div>`,
          iconAnchor: [0, 0],
        }),
        interactive: false,
      }).addTo(map)
      newLayers.push(label)
    })

    // Custom markers
    data.markers.forEach(m => {
      const icon = L.divIcon({
        className: '',
        html: `<div style="
          background:#0f172a;color:#f1f5f9;
          font-size:.68rem;font-weight:700;
          padding:4px 9px;border-radius:8px;
          border:1.5px solid #334155;
          box-shadow:0 3px 10px rgba(0,0,0,.5);
          white-space:nowrap;
        ">${m.label}</div>`,
        iconAnchor: [0, 0],
      })
      const marker = L.marker(m.pos, { icon })
        .addTo(map)
        .bindPopup(`<b>${m.label}</b><br><span style="color:#6b7280;font-size:.78rem">${m.sub}</span>`)
      newLayers.push(marker)
    })

    layersRef.current = newLayers
  }

  // IMPORTANT: mapRef div must NEVER move in the DOM — only wrapper changes.
  // Moving mapRef between renders kills Leaflet's container reference.
  return (
    <>
      {/* Dark backdrop when expanded */}
      {expanded && (
        <div
          onClick={() => setExpanded(false)}
          style={{
            position: 'fixed', inset: 0, zIndex: 2000,
            background: 'rgba(0,0,0,.65)',
            backdropFilter: 'blur(6px)',
          }}
        />
      )}

      {/* Wrapper — switches between inline and fixed without moving mapRef */}
      <div style={expanded ? {
        position: 'fixed',
        top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        zIndex: 2001,
        width: 'min(92vw, 1100px)',
        borderRadius: 20,
        overflow: 'hidden',
        boxShadow: '0 32px 80px rgba(0,0,0,.55)',
        border: '1px solid #334155',
      } : {
        borderRadius: 16,
        overflow: 'hidden',
        border: '1px solid #e5e7eb',
        boxShadow: '0 8px 32px rgba(0,0,0,.15)',
        position: 'relative',
      }}>

        {/* Header badge */}
        <div style={{
          position: 'absolute', top: 10, left: 10, zIndex: 1000,
          background: '#0f172aee', color: '#f1f5f9',
          fontSize: '.65rem', fontWeight: 800,
          padding: '4px 10px', borderRadius: 99,
          border: '1px solid #334155',
          letterSpacing: '.4px', textTransform: 'uppercase',
          pointerEvents: 'none',
        }}>
          {hospital === 'aiims' ? '🇮🇳' : '🇩🇪'} Satellite View · Click buildings for info
        </div>

        {/* Expand / Collapse button */}
        <button
          onClick={() => setExpanded(v => !v)}
          style={{
            position: 'absolute', top: 10, right: 10, zIndex: 1000,
            background: '#0f172aee', color: '#f1f5f9',
            border: '1px solid #475569', borderRadius: 8,
            padding: '5px 11px', cursor: 'pointer',
            fontSize: '.72rem', fontWeight: 700,
            display: 'flex', alignItems: 'center', gap: 5,
            backdropFilter: 'blur(4px)',
          }}
        >
          {expanded ? '✕ Close' : '⤢ Expand'}
        </button>

        {/* THE map container — stays in DOM at same position always */}
        <div
          ref={mapRef}
          style={{
            width: '100%',
            height: expanded ? 'min(75vh, 680px)' : 320,
            transition: 'height .3s ease',
          }}
        />
      </div>
    </>
  )
}
