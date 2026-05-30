"""
backend/main.py — FastAPI Backend for Charité AI Navigator
Wraps all core Python modules and exposes REST endpoints.
Run: uvicorn backend.main:app --reload --port 8000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from core.hospital_graph import NODES, build_graph, node_label, get_node_color
from core.search import run_search
from core.csp import validate_path_csp, find_valid_time_window, PROFILES
from core.nlp import parse_query_enhanced
from core.game import run_game
from core.bayes import infer_occupancy, hmm_forward, adjust_path_cost, TIME_OF_DAY, SENSOR, OCCUPANCY, HMM_STATES

app = FastAPI(title="Charité AI Navigator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    algorithm: str = "astar"
    profile: str = "staff"
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"

class NLPRequest(BaseModel):
    query: str
    use_llm: bool = False

class CSPRequest(BaseModel):
    path: List[str]
    profile: str
    hour: int = 10

class GameRequest(BaseModel):
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    profile: str = "emergency"
    depth: int = 3
    use_alpha_beta: bool = True

class BayesRequest(BaseModel):
    sensor: str = "busy"
    time_of_day: Optional[str] = None
    day_type: Optional[str] = None

class HMMRequest(BaseModel):
    observations: List[str]

class RouteRequest(BaseModel):
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    sensor_readings: Optional[Dict[str, str]] = None

class CompareRequest(BaseModel):
    profile: str = "staff"
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"


# ── Graph ─────────────────────────────────────────────────────────────────────

@app.get("/api/graph")
def get_graph(profile: str = "staff"):
    """Return nodes and edges for the given profile."""
    G = build_graph(profile)
    nodes = []
    for n, data in NODES.items():
        nodes.append({
            "id": n,
            "label": node_label(n),
            "color": get_node_color(n),
            "floor": data.get("floor", 0),
            "type": data.get("type", ""),
            "wing": data.get("wing", ""),
        })
    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": d.get("weight", 10),
            "via": d.get("via", ""),
        })
    return {"nodes": nodes, "edges": edges, "profile": profile,
            "node_count": len(nodes), "edge_count": len(edges)}


@app.get("/api/nodes")
def get_nodes():
    """Return all node IDs and labels."""
    return [{"id": k, "label": node_label(k)} for k in NODES.keys()]


@app.get("/api/profiles")
def get_profiles():
    return [{"id": k, "label": v["label"], "emoji": v["emoji"]}
            for k, v in PROFILES.items()]


# ── Search ────────────────────────────────────────────────────────────────────

@app.post("/api/search")
def search(req: SearchRequest):
    """Run BFS / DFS / UCS / A* and return path + trace."""
    try:
        result = run_search(req.algorithm, req.profile, req.start, req.goal)
        # graph is not JSON serialisable — strip it
        result.pop("graph", None)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/compare")
def compare_algorithms(req: CompareRequest):
    """Run all 4 algorithms on the same query."""
    results = {}
    for alg in ["bfs", "dfs", "ucs", "astar"]:
        r = run_search(alg, req.profile, req.start, req.goal)
        r.pop("graph", None)
        results[alg] = r
    return results


# ── NLP ───────────────────────────────────────────────────────────────────────

@app.post("/api/nlp")
def nlp_parse(req: NLPRequest):
    """Parse a multilingual query and return intent + urgency + route target."""
    try:
        result = parse_query_enhanced(req.query, use_llm=req.use_llm)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── CSP ───────────────────────────────────────────────────────────────────────

@app.post("/api/csp/validate")
def csp_validate(req: CSPRequest):
    """Validate a path against CSP constraints for a given profile."""
    try:
        return validate_path_csp(req.path, req.profile, req.hour)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/csp/time-window")
def csp_time_window(profile: str = "visitor", node: str = "ICU_Floor3"):
    """Find valid access time windows for a profile."""
    try:
        return find_valid_time_window(profile, node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Game AI ───────────────────────────────────────────────────────────────────

@app.post("/api/game")
def game_minimax(req: GameRequest):
    """Run Minimax / Alpha-Beta triage routing."""
    try:
        result = run_game(
            start=req.start,
            goal=req.goal,
            profile=req.profile,
            depth=req.depth,
            use_alpha_beta=req.use_alpha_beta,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Bayesian ──────────────────────────────────────────────────────────────────

@app.post("/api/bayes/infer")
def bayes_infer(req: BayesRequest):
    """Run Bayesian variable elimination for corridor occupancy."""
    try:
        result = infer_occupancy(req.sensor, req.time_of_day, req.day_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/bayes/hmm")
def bayes_hmm(req: HMMRequest):
    """Run HMM forward algorithm over an observation sequence."""
    try:
        result = hmm_forward(req.observations)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/bayes/route")
def bayes_route(req: RouteRequest):
    """Run A* then adjust costs by sensor readings."""
    try:
        sr = run_search("astar", "staff", req.start, req.goal)
        path = sr["path"]
        if not path:
            raise HTTPException(status_code=404, detail="No path found")
        demo = ["clear", "busy", "jammed", "busy", "clear"]
        sensors = req.sensor_readings or {
            n: demo[i % len(demo)] for i, n in enumerate(path)
        }
        result = adjust_path_cost(path, sensors)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/bayes/options")
def bayes_options():
    return {"time_of_day": TIME_OF_DAY, "sensors": SENSOR, "occupancy": OCCUPANCY, "hmm_states": HMM_STATES}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {"status": "ok", "nodes": len(NODES), "version": "1.0.0"}
