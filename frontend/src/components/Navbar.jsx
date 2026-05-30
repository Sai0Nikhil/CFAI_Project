import { NavLink } from 'react-router-dom'

const LINKS = [
  { to: '/',         label: 'Home',     emoji: '🏥', co: ''        },
  { to: '/navigate', label: 'Navigate', emoji: '🗺️', co: 'CO1·CO2' },
  { to: '/search',   label: 'Search',   emoji: '🔍', co: 'CO2'     },
  { to: '/csp',      label: 'CSP',      emoji: '🧩', co: 'CO3'     },
  { to: '/game',     label: 'Game AI',  emoji: '♟️', co: 'CO4'     },
  { to: '/bayesian', label: 'Bayesian', emoji: '🎲', co: 'CO5'     },
  { to: '/nlp',      label: 'NLP',      emoji: '🌐', co: 'CO6'     },
]

export default function Navbar() {
  return (
    <nav className="navbar">
      <span className="navbar-brand">🏥 Charité AI</span>
      <div className="nav-links">
        {LINKS.map(({ to, label, emoji, co }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) => 'nav-link' + (isActive ? ' active' : '')}
          >
            <span>{emoji}</span>
            <span>{label}</span>
            {co && <span className="nav-co">{co}</span>}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
