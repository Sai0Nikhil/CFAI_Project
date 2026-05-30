import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Home from './pages/Home'
import Navigate from './pages/Navigate'
import Search from './pages/Search'
import CSP from './pages/CSP'
import Game from './pages/Game'
import Bayesian from './pages/Bayesian'
import NLP from './pages/NLP'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <Navbar />
        <main className="page-content">
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/navigate" element={<Navigate />} />
            <Route path="/search" element={<Search />} />
            <Route path="/csp" element={<CSP />} />
            <Route path="/game" element={<Game />} />
            <Route path="/bayesian" element={<Bayesian />} />
            <Route path="/nlp" element={<NLP />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  )
}
