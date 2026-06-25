"""
backend/main.py — FastAPI Backend
Hospital AI Navigator — Charité Campus Mitte & AIIMS Mangalagiri
Run: uvicorn backend.main:app --reload --port 8000
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

import core.hospital_graph as _charite
import core.aiims_graph   as _aiims

def _mod(hospital: str):
    """Return the graph module for the given hospital key."""
    return _aiims if hospital == "aiims" else _charite

from backend.ai_explain import explain as ai_explain
from core.search import run_search
from core.csp import validate_path_csp, find_valid_time_window, PROFILES
from core.nlp import parse_query_enhanced
from core.game import run_game, run_not_named_yet
from core.mcts import run_mcts_game
from core.bayes import infer_occupancy, hmm_forward, adjust_path_cost, TIME_OF_DAY, SENSOR, OCCUPANCY, HMM_STATES
from core.triage import solve_ethical_triage
from core.explain import explain_path_multilingual
from core.active_belief import solve_active_belief_routing
from core.multi_agent import cooperative_astar

app = FastAPI(
    title="Hospital AI Navigator API — Charité & AIIMS Mangalagiri",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Pydantic models ─────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    algorithm: str = "astar"
    profile: str = "staff"
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    hospital: str = "charite"
    blocked_nodes: Optional[List[str]] = None
    blocked_edges: Optional[List[List[str]]] = None

class NLPRequest(BaseModel):
    query: str
    use_llm: bool = False
    api_key: str = ""
    provider: str = "claude"
    model: str = "claude-3-haiku-20240307"
    hospital: str = "charite"

class CSPRequest(BaseModel):
    path: List[str]
    profile: str
    hour: int = 10
    hospital: str = "charite"

class GameRequest(BaseModel):
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    profile: str = "emergency"
    depth: int = 3
    use_alpha_beta: bool = True
    hospital: str = "charite"

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
    hospital: str = "charite"

class AIExplainRequest(BaseModel):
    module: str
    context: Dict[str, Any] = {}
    provider: str = "claude"
    api_key: str = ""
    model: str = "claude-3-haiku-20240307"

class GameMCTSRequest(BaseModel):
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    profile: str = "emergency"
    num_simulations: int = 200
    depth_limit: int = 6
    time_of_day: Optional[str] = None
    sensor_readings: Optional[Dict[str, str]] = None
    api_key: str = ""
    provider: str = "claude"
    model: str = "claude-3-haiku-20240307"
    use_llm_value: bool = False
    hospital: str = "charite"

class CompareRequest(BaseModel):
    profile: str = "staff"
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    hospital: str = "charite"
    blocked_nodes: Optional[List[str]] = None
    blocked_edges: Optional[List[List[str]]] = None


class NotNamedYetRequest(BaseModel):
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    profile: str = "emergency"
    depth: int = 3
    time_of_day: Optional[str] = None
    sensor_readings: Optional[Dict[str, str]] = None
    api_key: str = ""
    provider: str = "claude"
    model: str = "claude-3-haiku-20240307"
    use_llm_value: bool = False
    hospital: str = "charite"

class EthicalTriageRequest(BaseModel):
    patient_a: Dict[str, Any]
    patient_b: Dict[str, Any]
    mode: str = "rawlsian"
    equity_guard: bool = True

class MultilingualExplainRequest(BaseModel):
    path: List[str]
    cost: float
    algorithm: str = "astar"
    profile: str = "staff"
    language: str = "en"
    hospital: str = "charite"
    use_llm: bool = False
    api_key: str = ""
    provider: str = "claude"
    model: str = "claude-3-haiku-20240307"

class ActiveBeliefRequest(BaseModel):
    start: str = "ENTRANCE_MAIN"
    goal: str = "Node_302_ICU_Tower"
    hospital: str = "charite"
    entropy_threshold: float = 0.8
    sensor_ages: Optional[Dict[str, float]] = None
    active_belief_enabled: bool = True

class MultiAgentRequest(BaseModel):
    hospital: str = "charite"
    agents: List[Dict[str, Any]]
    coordination_enabled: bool = True


# ── Hospitals list ───────────────────────────────────────────────────────────

@app.get("/api/hospitals")
def get_hospitals():
    """Return available hospital options."""
    return [
        {
            "id": "charite",
            "name": "Charité Campus Mitte",
            "city": "Berlin, Germany",
            "emoji": "🇩🇪",
            "default_start": "ENTRANCE_MAIN",
            "default_goal": "Node_302_ICU_Tower",
        },
        {
            "id": "aiims",
            "name": "AIIMS Mangalagiri",
            "city": "Andhra Pradesh, India",
            "emoji": "🇮🇳",
            "default_start": "MAIN_GATE",
            "default_goal": "NICU_F3",
        },
    ]


# ── Graph ────────────────────────────────────────────────────────────────────

@app.get("/api/graph")
def get_graph(profile: str = "staff", hospital: str = "charite"):
    m = _mod(hospital)
    G = m.build_graph(profile)
    nodes = []
    for n, data in m.NODES.items():
        nodes.append({
            "id": n,
            "label": m.node_label(n),
            "color": m.get_node_color(n),
            "floor": data.get("floor", 0),
            "type":  data.get("type", ""),
            "zone":  data.get("zone", ""),
        })
    edges = []
    for u, v, d in G.edges(data=True):
        edges.append({
            "source": u,
            "target": v,
            "weight": d.get("weight", 10),
            "via":    d.get("via", ""),
        })
    return {
        "nodes": nodes, "edges": edges,
        "profile": profile, "hospital": hospital,
        "node_count": len(nodes), "edge_count": len(edges),
    }


@app.get("/api/nodes")
def get_nodes(hospital: str = "charite"):
    m = _mod(hospital)
    return [{"id": k, "label": m.node_label(k)} for k in m.NODES.keys()]


@app.get("/api/profiles")
def get_profiles():
    return [{"id": k, "label": v["label"], "emoji": v["emoji"]}
            for k, v in PROFILES.items()]


# ── Search ───────────────────────────────────────────────────────────────────

@app.post("/api/search")
def search(req: SearchRequest):
    try:
        result = run_search(
            req.algorithm, req.profile, req.start, req.goal, req.hospital,
            blocked_nodes=req.blocked_nodes, blocked_edges=req.blocked_edges
        )
        result.pop("graph", None)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/compare")
def compare_algorithms(req: CompareRequest):
    results = {}
    for alg in ["bfs", "dfs", "ucs", "astar"]:
        r = run_search(
            alg, req.profile, req.start, req.goal, req.hospital,
            blocked_nodes=req.blocked_nodes, blocked_edges=req.blocked_edges
        )
        r.pop("graph", None)
        results[alg] = r
    return results


def resolve_node_id(node_id: Optional[str], hospital: str) -> Optional[str]:
    if not node_id:
        return node_id
    
    MAPPING = {
        "charite": {
            "HW_Radiology": "DIAG_Radiology",
            "HW_Pharmacy": "HW_Pharmacy",
            "HW_OPD": "MVZ_Lobby",
            "HW_Physiotherapy": "DIAG_PhysioTherapy",
            "HW_Dialysis": "BH_Dialysis",
            "HW_BloodBank": "HW_BloodBank",
            "HW_Admin": "ADMIN_HQ",
        },
        "aiims": {
            "HW_Radiology": "LAB_RADIOLOGY",
            "HW_Pharmacy": "AMIRT_PHARMACY",
            "HW_OPD": "OPD_LOBBY",
            "HW_Physiotherapy": "OPD_GENERAL_MEDICINE",
            "HW_Dialysis": "DIALYSIS_UNIT",
            "HW_BloodBank": "BLOOD_BANK",
            "HW_Admin": "OPD_REGISTRATION",
        }
    }
    
    h_map = MAPPING.get(hospital.lower(), MAPPING["charite"])
    return h_map.get(node_id, node_id)

# ── NLP ──────────────────────────────────────────────────────────────────────

@app.post("/api/nlp")
def nlp_parse(req: NLPRequest):
    try:
        if req.use_llm and req.api_key.strip():
            os.environ["LLM_PROVIDER"] = req.provider
            os.environ["LLM_MODEL"]    = req.model
            if req.provider == "gemini":
                os.environ["GEMINI_API_KEY"]    = req.api_key
            else:
                os.environ["ANTHROPIC_API_KEY"] = req.api_key
        result = parse_query_enhanced(req.query, use_llm=req.use_llm and bool(req.api_key.strip()))
        
        # Resolve target node to actual hospital-specific node ID
        if "target_node" in result and result["target_node"]:
            result["target_node"] = resolve_node_id(result["target_node"], req.hospital)
            
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── CSP ──────────────────────────────────────────────────────────────────────

@app.post("/api/csp/validate")
def csp_validate(req: CSPRequest):
    try:
        return validate_path_csp(req.path, req.profile, req.hour, req.hospital)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/csp/time-window")
def csp_time_window(profile: str = "visitor", node: str = "Node_302_ICU_Tower"):
    try:
        return find_valid_time_window(profile, node)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Game AI ──────────────────────────────────────────────────────────────────

@app.post("/api/game")
def game_minimax(req: GameRequest):
    try:
        result = run_game(
            start=req.start, goal=req.goal,
            profile=req.profile, depth_limit=req.depth,
            hospital=req.hospital,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/game/mcts")
def game_mcts(req: GameMCTSRequest):
    try:
        result = run_mcts_game(
            start=req.start, goal=req.goal,
            profile=req.profile,
            num_simulations=req.num_simulations,
            depth_limit=req.depth_limit,
            time_of_day=req.time_of_day,
            sensor_readings=req.sensor_readings,
            api_key=req.api_key,
            provider=req.provider,
            model=req.model,
            use_llm_value=req.use_llm_value,
            hospital=req.hospital,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/game/not-named-yet")
def game_not_named_yet(req: NotNamedYetRequest):
    try:
        result = run_not_named_yet(
            start=req.start, goal=req.goal,
            profile=req.profile, depth_limit=req.depth,
            time_of_day=req.time_of_day,
            sensor_readings=req.sensor_readings,
            api_key=req.api_key,
            provider=req.provider,
            model=req.model,
            use_llm_value=req.use_llm_value,
            hospital=req.hospital
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Bayesian ─────────────────────────────────────────────────────────────────

@app.post("/api/bayes/infer")
def bayes_infer(req: BayesRequest):
    try:
        return infer_occupancy(req.sensor, req.time_of_day, req.day_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/bayes/hmm")
def bayes_hmm(req: HMMRequest):
    try:
        return hmm_forward(req.observations)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/bayes/route")
def bayes_route(req: RouteRequest):
    try:
        sr = run_search("astar", "staff", req.start, req.goal, req.hospital)
        path = sr["path"]
        if not path:
            raise HTTPException(status_code=404, detail="No path found")
        demo = ["clear", "busy", "jammed", "busy", "clear"]
        sensors = req.sensor_readings or {
            n: demo[i % len(demo)] for i, n in enumerate(path)
        }
        return adjust_path_cost(path, sensors, req.hospital)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/bayes/options")
def bayes_options():
    return {"time_of_day": TIME_OF_DAY, "sensors": SENSOR,
            "occupancy": OCCUPANCY, "hmm_states": HMM_STATES}


# ── Ideas Lab / Novel Features ────────────────────────────────────────────────

@app.post("/api/csp/ethical-triage")
def ethical_triage(req: EthicalTriageRequest):
    try:
        return solve_ethical_triage(
            req.patient_a, req.patient_b, req.mode, req.equity_guard
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/explain/multilingual")
async def explain_multilingual(req: MultilingualExplainRequest):
    try:
        return await explain_path_multilingual(
            path=req.path,
            cost=req.cost,
            algo=req.algorithm,
            profile=req.profile,
            lang=req.language,
            hospital=req.hospital,
            use_llm=req.use_llm,
            api_key=req.api_key,
            provider=req.provider,
            model=req.model
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/bayes/active-belief")
def active_belief_routing(req: ActiveBeliefRequest):
    try:
        return solve_active_belief_routing(
            start=req.start,
            goal=req.goal,
            hospital=req.hospital,
            entropy_threshold=req.entropy_threshold,
            sensor_ages=req.sensor_ages,
            active_belief_enabled=req.active_belief_enabled
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/search/multi-agent")
def multi_agent_search(req: MultiAgentRequest):
    try:
        return cooperative_astar(
            hospital=req.hospital,
            agents_config=req.agents,
            coordination_enabled=req.coordination_enabled
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── AI Explain ───────────────────────────────────────────────────────────────

@app.post("/api/ai/explain")
async def ai_explain_endpoint(req: AIExplainRequest):
    if not req.api_key.strip():
        raise HTTPException(status_code=400, detail="API key required")
    try:
        return await ai_explain(req.module, req.context, req.provider, req.api_key, req.model)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "hospitals": {
            "charite": {"nodes": len(_charite.NODES)},
            "aiims":   {"nodes": len(_aiims.NODES)},
        },
        "version": "2.0.0",
    }
