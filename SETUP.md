# Hospital AI Navigator — Charité Campus Mitte & AIIMS Mangalagiri

## One-command start (Windows)
```
double-click start.bat
```
Then open **http://localhost:5173**

---

## Manual setup

### Backend (Python FastAPI)
```bash
# Install backend deps (one time)
pip install fastapi uvicorn pydantic networkx numpy

# Start backend
python -m uvicorn backend.main:app --reload --port 8000
```
API runs at: http://localhost:8000  
Docs at: http://localhost:8000/docs

### Frontend (Vite React)
```bash
# Install node deps (one time)
cd frontend
npm install

# Start dev server
npm run dev
```
App runs at: http://localhost:5173

---

## Hospitals Supported
| Hospital | Key | Real data sources |
|---|---|---|
| 🇩🇪 Charité Campus Mitte, Berlin | `charite` | dieneue-charite.de, neurologie.charite.de, Bettenhaus Wikipedia |
| 🇮🇳 AIIMS Mangalagiri, Andhra Pradesh | `aiims` | aiimsmangalagiri.edu.in (official), KMV Projects |

Switch hospitals using the 🇩🇪/🇮🇳 toggle in the top-left of the navbar.

## Architecture
```
C:\CFAI_Project\
├── core/
│   ├── hospital_graph.py  ← Charité Campus Mitte graph (verified)
│   ├── aiims_graph.py     ← AIIMS Mangalagiri graph (verified) ← NEW
│   ├── search.py          ← BFS/DFS/UCS/A* (hospital param)
│   ├── csp.py             ← CSP validation (hospital param)
│   ├── game.py            ← Minimax/Alpha-Beta (hospital param)
│   ├── mcts.py            ← MCTS (hospital param)
│   ├── bayes.py           ← Bayesian (hospital param)
│   └── nlp.py
├── backend/
│   └── main.py            ← FastAPI v2.0 (dual-hospital)
├── frontend/
│   ├── src/
│   │   ├── pages/         ← 8 React pages (all hospital-aware)
│   │   ├── components/    ← Navbar with hospital switcher
│   │   ├── context/       ← AIContext with hospital state
│   │   ├── styles/        ← global.css (cream theme)
│   │   ├── api.js         ← axios client (hospital param)
│   │   └── App.jsx        ← React Router
│   └── package.json
└── start.bat              ← One-click launcher
```

## API Endpoints (v2.0 — all support `?hospital=charite|aiims`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/hospitals | List available hospitals |
| GET | /api/graph?hospital= | Hospital graph nodes + edges |
| GET | /api/nodes?hospital= | All node IDs and labels |
| POST | /api/search | BFS/DFS/UCS/A* (pass `hospital` in body) |
| POST | /api/compare | Run all 4 algorithms |
| POST | /api/nlp | Multilingual NLP parse |
| POST | /api/csp/validate | CSP path validation |
| GET | /api/csp/time-window | Valid access hours |
| POST | /api/game | Minimax / Alpha-Beta |
| POST | /api/game/mcts | MCTS + Bayesian prior |
| POST | /api/bayes/infer | Bayesian inference |
| POST | /api/bayes/hmm | HMM forward pass |
| POST | /api/bayes/route | Uncertainty-aware routing |
| GET | /api/health | Status + node counts for both hospitals |
