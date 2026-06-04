# 🏥 Charité Hospital AI Navigator

> **2500032630 · CFAI Project** — Full-stack AI system built on the Charité Campus Mitte hospital model, covering all 6 course outcomes (CO1–CO6).

[![GitHub](https://img.shields.io/badge/GitHub-Sai0Nikhil%2FCFAI__Project-181717?logo=github)](https://github.com/Sai0Nikhil/CFAI_Project)
![React](https://img.shields.io/badge/Frontend-React_+_Vite-61dafb?logo=react)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 📸 What it does

A real-world hospital navigation system that demonstrates 6 AI techniques on a 41-node, 52-edge graph of Charité hospital (Berlin):

| Module | CO | Technique |
|--------|-----|-----------|
| 🗺️ Navigate | CO1 + CO2 | PEAS Agent · BFS · DFS · UCS · A* · Interactive Graph |
| 🔍 Search | CO2 | Algorithm comparison · Step traces · Complexity analysis |
| 🧩 CSP | CO3 | Backtracking · AC-3 · MRV heuristic · Access control |
| ♟️ Game AI | CO4 | Minimax · Alpha-Beta pruning · Triage routing |
| 🎲 Bayesian | CO5 | Bayesian Networks · Variable Elimination · HMM |
| 🌐 NLP | CO6 | Telugu · Hindi · English · Urgency detection · Ethics |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** and npm

### 1 — Clone the repo
```bash
git clone https://github.com/Sai0Nikhil/CFAI_Project.git
cd CFAI_Project
```

### 2 — Install Python dependencies
```bash
pip install fastapi uvicorn pydantic networkx numpy
```

### 3 — Install Node dependencies
```bash
cd frontend
npm install
cd ..
```

### 4 — Run both servers

**Windows — double-click `start.bat`**

**Or manually in two terminals:**

```bash
# Terminal 1 — FastAPI backend (port 8000)
python -m uvicorn backend.main:app --reload --port 8000

# Terminal 2 — Vite React frontend (port 5173)
cd frontend
npm run dev
```

### 5 — Open the app
```
http://localhost:5173
```

API docs available at: `http://localhost:8000/docs`

---

## 📁 Project Structure

```
CFAI_Project/
│
├── core/                     # Python AI modules (no changes needed)
│   ├── hospital_graph.py     # 41 nodes, 52 edges — Charité topology
│   ├── search.py             # BFS, DFS, UCS, A* implementations
│   ├── csp.py                # Backtracking, AC-3, MRV, profiles
│   ├── game.py               # Minimax + Alpha-Beta pruning
│   ├── bayes.py              # Bayesian net + HMM forward algorithm
│   ├── nlp.py                # Multilingual NLP (TE/HI/EN)
│   └── llm_provider.py       # Optional Claude/Gemini LLM integration
│
├── backend/
│   └── main.py               # FastAPI — exposes core/ as REST API
│
├── frontend/
│   ├── src/
│   │   ├── pages/            # 7 React pages (Home, Navigate, Search…)
│   │   ├── components/
│   │   │   ├── Navbar.jsx    # Navigation bar
│   │   │   └── GraphMap.jsx  # Interactive vis-network graph
│   │   ├── styles/
│   │   │   └── global.css    # Warm cream design system
│   │   ├── api.js            # Axios API client
│   │   └── App.jsx           # React Router setup
│   └── package.json
│
├── tests/                    # Pytest unit tests
├── start.bat                 # Windows one-click launcher
├── SETUP.md                  # Detailed setup notes
└── README.md                 # This file
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server health check |
| GET | `/api/graph?profile=staff` | Hospital graph nodes + edges |
| GET | `/api/nodes` | All node IDs and labels |
| POST | `/api/search` | Run BFS / DFS / UCS / A* |
| POST | `/api/compare` | Compare all 4 algorithms |
| POST | `/api/nlp` | Multilingual NLP parse |
| POST | `/api/csp/validate` | Validate path against CSP constraints |
| GET | `/api/csp/time-window` | Valid access hours per profile |
| POST | `/api/game` | Minimax / Alpha-Beta triage routing |
| POST | `/api/bayes/infer` | Bayesian variable elimination |
| POST | `/api/bayes/hmm` | HMM forward algorithm |
| POST | `/api/bayes/route` | Uncertainty-aware A* routing |

Full interactive API docs: **http://localhost:8000/docs**

---

## 🧠 CO Coverage

### CO1 — Agent Model & Knowledge Representation
- PEAS model (Performance, Environment, Actuators, Sensors)
- Hospital graph as Python dataclasses + NetworkX
- Big-O complexity annotations on every algorithm

### CO2 — Graph Search
- BFS, DFS, UCS, A* on 41-node weighted graph
- f(n) = g(n) + h(n) trace at every step
- Admissible heuristic: `h(n) = |floor_goal − floor_n| × 12s`
- Side-by-side comparison of all 4 algorithms

### CO3 — Constraint Satisfaction
- 4 access profiles: Staff, Emergency, Visitor, Patient
- Backtracking with forward checking
- AC-3 arc consistency
- MRV (Most Restricted Variable) heuristic
- Time-window access finder

### CO4 — Game AI
- Two-player zero-sum: MAX (ambulance) vs MIN (congestion)
- Minimax with configurable search depth
- Alpha-beta pruning with pruned-branch count
- Evaluation function: `f = −travel_cost + urgency_bonus − congestion`

### CO5 — Probabilistic Reasoning
- Bayesian network: TimeOfDay → Occupancy ← DayType → SensorReads
- Variable elimination for P(Occupancy | evidence)
- HMM forward algorithm: P(state_t | obs_1:t)
- Sensor-adjusted path cost (congestion factors × 1.0 / 1.4 / 2.0)

### CO6 — NLP & Ethics
- Language detection: Telugu script, Hindi script, English keywords
- Roman transliteration support (ICU le jao, mujhe pharmacy jana hai)
- Urgency detection: CRITICAL / HIGH / NORMAL
- Urgency-aware routing: CRITICAL → A*, HIGH → UCS, NORMAL → BFS
- Ethics panel: language equity, bias audit, accessibility analysis

---

## 🗺️ Hospital Graph

**41 nodes · 52 edges** based on Charité Campus Mitte, Berlin:

- **Historic Wing** — Labs, Radiology, Pharmacy, Admin (stair-heavy)
- **Bettenhaus Tower** — 21-floor patient tower, ICU Floor 3, Wards (Cardio F7, Maternity F10, Neuro F5)
- **Central** — Main entrance, BH Lobby, Elevators A/B, connecting corridors

Node types: `entrance · lobby · elevator · corridor · ward · icu · lab · pharmacy · office · stairs`

---

## 🎙️ Voice Input

The Navigate page includes a Web Speech API microphone widget:
- Supports **Telugu** (te-IN), **Hindi** (hi-IN), **English** (en-US)
- Works in **Chrome** and Edge (Web Speech API required)
- Transcript auto-fills the NLP query box

---

## ⚙️ Optional: LLM-Enhanced NLP

The NLP module can optionally use Claude or Gemini for better intent parsing:

1. Go to the **Navigate** page → Zone 5
2. Toggle the provider (Claude / Gemini)
3. Paste your API key
4. Toggle **On**

Without an API key, rule-based NLP works fully offline for all 3 languages.

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 🛠️ Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18 + Vite + React Router |
| Graph viz | vis-network (interactive, zoomable) |
| Backend | FastAPI + Uvicorn |
| AI core | Python · NetworkX · NumPy |
| Styling | Plain CSS (cream/warm theme, zero frameworks) |

---

## 👤 Author

**Sai Nikhil** · 2500032630 · CFAI Project  
Roll: `25f2005507`  
GitHub: [@Sai0Nikhil](https://github.com/Sai0Nikhil)

---

## 📄 License

MIT — free to use for academic purposes.
