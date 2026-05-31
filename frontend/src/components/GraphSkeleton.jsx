/**
 * GraphSkeleton.jsx
 * Animated loading skeleton themed around BFS node-visiting waves.
 * Shows pulsing nodes connected by edges, with a "frontier" sweep animation.
 */

const NODES = [
  { id: 0, cx: 80,  cy: 80,  r: 14, delay: 0    },
  { id: 1, cx: 200, cy: 50,  r: 10, delay: 0.15 },
  { id: 2, cx: 320, cy: 80,  r: 12, delay: 0.3  },
  { id: 3, cx: 440, cy: 55,  r: 10, delay: 0.45 },
  { id: 4, cx: 560, cy: 80,  r: 14, delay: 0.6  },
  { id: 5, cx: 130, cy: 170, r: 10, delay: 0.2  },
  { id: 6, cx: 260, cy: 150, r: 12, delay: 0.35 },
  { id: 7, cx: 390, cy: 170, r: 10, delay: 0.5  },
  { id: 8, cx: 500, cy: 155, r: 12, delay: 0.65 },
  { id: 9, cx: 80,  cy: 250, r: 10, delay: 0.25 },
  { id:10, cx: 210, cy: 260, r: 14, delay: 0.4  },
  { id:11, cx: 340, cy: 245, r: 10, delay: 0.55 },
  { id:12, cx: 470, cy: 255, r: 12, delay: 0.7  },
  { id:13, cx: 580, cy: 240, r: 10, delay: 0.8  },
]

const EDGES = [
  [0,1],[1,2],[2,3],[3,4],
  [0,5],[1,5],[1,6],[2,6],[2,7],[3,7],[3,8],[4,8],
  [5,9],[5,10],[6,10],[6,11],[7,11],[7,12],[8,12],[8,13],
  [9,10],[10,11],[11,12],[12,13],
]

export default function GraphSkeleton({ message = 'Running search…' }) {
  return (
    <div style={{
      background: '#fffdf9',
      border: '1px solid #e8d9c4',
      borderRadius: 12,
      padding: '20px 16px',
      overflow: 'hidden',
    }}>
      {/* SVG graph animation */}
      <svg
        viewBox="0 0 660 310"
        style={{ width: '100%', height: 220, display: 'block' }}
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Shimmer gradient sweeping left→right */}
          <linearGradient id="shimmer" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#e8d9c4" stopOpacity="1" />
            <stop offset="40%"  stopColor="#fef3c7" stopOpacity="1" />
            <stop offset="100%" stopColor="#e8d9c4" stopOpacity="1" />
            <animateTransform
              attributeName="gradientTransform"
              type="translate"
              from="-1 0" to="1 0"
              dur="1.6s"
              repeatCount="indefinite"
            />
          </linearGradient>

          {/* BFS wave ripple for visited nodes */}
          <radialGradient id="ripple">
            <stop offset="0%"   stopColor="#b45309" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#b45309" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Edges */}
        {EDGES.map(([a, b], i) => {
          const na = NODES[a], nb = NODES[b]
          return (
            <line
              key={i}
              x1={na.cx} y1={na.cy}
              x2={nb.cx} y2={nb.cy}
              stroke="url(#shimmer)"
              strokeWidth="2"
              strokeLinecap="round"
            />
          )
        })}

        {/* BFS frontier ripple rings */}
        {NODES.map(n => (
          <circle
            key={`ring-${n.id}`}
            cx={n.cx} cy={n.cy} r={n.r}
            fill="none"
            stroke="#b45309"
            strokeWidth="1.5"
            opacity="0"
          >
            <animate
              attributeName="r"
              from={n.r} to={n.r + 22}
              dur="1.8s"
              begin={`${n.delay}s`}
              repeatCount="indefinite"
            />
            <animate
              attributeName="opacity"
              from="0.6" to="0"
              dur="1.8s"
              begin={`${n.delay}s`}
              repeatCount="indefinite"
            />
          </circle>
        ))}

        {/* Node circles */}
        {NODES.map(n => (
          <g key={n.id}>
            {/* Node body with shimmer */}
            <circle
              cx={n.cx} cy={n.cy} r={n.r}
              fill="url(#shimmer)"
              stroke="#ddd0bb"
              strokeWidth="1.5"
            >
              <animate
                attributeName="fill-opacity"
                values="0.6;1;0.6"
                dur="1.6s"
                begin={`${n.delay}s`}
                repeatCount="indefinite"
              />
            </circle>
          </g>
        ))}

        {/* Animated "visited" dot sweeping across the path */}
        <circle r="6" fill="#b45309" opacity="0.9">
          <animateMotion
            dur="2.4s"
            repeatCount="indefinite"
            path="M80,80 L200,50 L320,80 L440,55 L560,80 L500,155 L390,170 L260,150 L130,170 L80,250 L210,260 L340,245 L470,255 L580,240"
            calcMode="linear"
          />
          <animate attributeName="opacity" values="1;0.8;1" dur="2.4s" repeatCount="indefinite" />
        </circle>
      </svg>

      {/* Skeleton text lines below graph */}
      <div style={{ marginTop: 14 }}>
        {/* Status message */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: 10,
          marginBottom: 14, justifyContent: 'center',
        }}>
          <span style={{ fontSize: '1.1rem' }}>🔍</span>
          <span style={{
            fontSize: '.84rem', fontWeight: 700, color: '#92400e',
            letterSpacing: '.3px',
          }}>
            {message}
          </span>
          <span style={{ display: 'flex', gap: 3 }}>
            {[0, 0.2, 0.4].map(d => (
              <span key={d} style={{
                width: 5, height: 5, borderRadius: '50%', background: '#b45309',
                display: 'inline-block', animation: `dotPulse 1s ${d}s ease-in-out infinite`,
              }} />
            ))}
          </span>
        </div>

        {/* Skeleton metric bars */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
          {[70, 50, 60].map((w, i) => (
            <div key={i} style={{
              background: '#f3e8d8', borderRadius: 8, padding: '10px 12px',
              border: '1px solid #e8d9c4',
            }}>
              <div style={{
                height: 22, width: `${w}%`, borderRadius: 4,
                background: 'url(#shimmer)',
                backgroundImage: 'linear-gradient(90deg,#e8d9c4 25%,#fef3c7 50%,#e8d9c4 75%)',
                backgroundSize: '200% 100%',
                animation: 'shimmerMove 1.6s linear infinite',
                marginBottom: 6,
              }} />
              <div style={{
                height: 10, width: '80%', borderRadius: 4,
                backgroundImage: 'linear-gradient(90deg,#e8d9c4 25%,#fef3c7 50%,#e8d9c4 75%)',
                backgroundSize: '200% 100%',
                animation: 'shimmerMove 1.6s linear infinite',
              }} />
            </div>
          ))}
        </div>
      </div>

      <style>{`
        @keyframes dotPulse {
          0%,100% { transform: scale(1); opacity:.4; }
          50%      { transform: scale(1.5); opacity:1; }
        }
        @keyframes shimmerMove {
          0%   { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  )
}
