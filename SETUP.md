# Charité AI Navigator — React + FastAPI Setup

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

## Architecture
```
C:\CFAI_Project\
├── core/              ← Python AI modules (unchanged)
│   ├── hospital_graph.py
│   ├── search.py
│   ├── csp.py
│   ├── game.py
│   ├── bayes.py
│   └── nlp.py
├── backend/
│   └── main.py        ← FastAPI wrapping core/
├── frontend/
│   ├── src/
│   │   ├── pages/     ← 7 React pages
│   │   ├── components/← Navbar
│   │   ├── styles/    ← global.css (cream theme)
│   │   ├── api.js     ← axios client
│   │   └── App.jsx    ← React Router
│   └── package.json
└── start.bat          ← One-click launcher
```

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/graph | Hospital graph nodes + edges |
| GET | /api/nodes | All node IDs and labels |
| POST | /api/search | BFS/DFS/UCS/A* search |
| POST | /api/compare | Run all 4 algorithms |
| POST | /api/nlp | Multilingual NLP parse |
| POST | /api/csp/validate | CSP path validation |
| GET | /api/csp/time-window | Valid access hours |
| POST | /api/game | Minimax / Alpha-Beta |
| POST | /api/bayes/infer | Bayesian inference |
| POST | /api/bayes/hmm | HMM forward pass |
| POST | /api/bayes/route | Uncertainty-aware routing |
