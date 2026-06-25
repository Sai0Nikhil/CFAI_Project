"""tests/test_search.py — Unit tests for CO2 search algorithms"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.search import bfs, dfs, ucs, astar, run_search
from core.hospital_graph import build_graph

G_STAFF = build_graph("staff")
G_VISITOR = build_graph("visitor")

# ── BFS ──────────────────────────────────────────────────────────────────────

def test_bfs_finds_path():
    result = bfs(G_STAFF, "ENTRANCE_MAIN", "HW_Pharmacy")
    assert len(result["path"]) > 0, "BFS should find a path"
    assert result["path"][0] == "ENTRANCE_MAIN"
    assert result["path"][-1] == "HW_Pharmacy"

def test_bfs_no_path_disconnected():
    """Create a tiny disconnected graph."""
    import networkx as nx
    G = nx.Graph()
    G.add_node("A")
    G.add_node("B")
    result = bfs(G, "A", "B")
    assert result["path"] == []

def test_bfs_returns_trace():
    result = bfs(G_STAFF, "ENTRANCE_MAIN", "BH_Reception")
    assert len(result["trace"]) > 0

# ── DFS ──────────────────────────────────────────────────────────────────────

def test_dfs_finds_path():
    result = dfs(G_STAFF, "ENTRANCE_MAIN", "BH_F21_Admin")
    assert len(result["path"]) > 0

def test_dfs_path_valid_edges():
    result = dfs(G_STAFF, "ENTRANCE_MAIN", "Ward_F1_A")
    path = result["path"]
    for i in range(len(path) - 1):
        assert G_STAFF.has_edge(path[i], path[i+1]), f"Edge {path[i]}→{path[i+1]} missing"

# ── UCS ──────────────────────────────────────────────────────────────────────

def test_ucs_optimal_cost():
    r1 = ucs(G_STAFF, "ENTRANCE_MAIN", "BH_Reception")
    r2 = bfs(G_STAFF, "ENTRANCE_MAIN", "BH_Reception")
    assert r1["cost"] <= r2["cost"], "UCS cost should be <= BFS cost (UCS is optimal)"

def test_ucs_trace_has_g_values():
    result = ucs(G_STAFF, "BH_Lobby", "Ward_F1_A")
    expand_steps = [t for t in result["trace"] if t["action"] == "EXPAND"]
    assert all("g" in s for s in expand_steps), "UCS trace should include g values"

# ── A* ───────────────────────────────────────────────────────────────────────

def test_astar_finds_icu_staff():
    result = astar(G_STAFF, "ENTRANCE_MAIN", "Node_302_ICU_Tower")
    assert result["path"][-1] == "Node_302_ICU_Tower"

def test_astar_visitor_cannot_reach_icu():
    result = astar(G_VISITOR, "ENTRANCE_MAIN", "Node_302_ICU_Tower")
    assert result["path"] == [], "Visitor should not reach ICU"

def test_astar_trace_has_fgh():
    result = astar(G_STAFF, "ENTRANCE_MAIN", "Ward_Cardio_F7")
    expand_steps = [t for t in result["trace"] if t["action"] == "EXPAND"]
    for s in expand_steps:
        assert "f" in s and "g" in s and "h" in s

def test_astar_optimal_vs_ucs():
    """A* and UCS should find same optimal cost."""
    r_a = astar(G_STAFF, "BH_Lobby", "Ward_Neuro_F5")
    r_u = ucs(G_STAFF, "BH_Lobby", "Ward_Neuro_F5")
    assert abs(r_a["cost"] - r_u["cost"]) < 0.01, "A* and UCS must agree on optimal cost"

# ── run_search convenience ────────────────────────────────────────────────────

def test_run_search_returns_graph():
    result = run_search("astar", "staff", "ENTRANCE_MAIN", "HW_Pharmacy")
    assert "graph" in result

def test_run_search_emergency_full_access():
    result = run_search("astar", "emergency", "ENTRANCE_MAIN", "Node_302_ICU_Tower")
    assert len(result["path"]) > 0, "Emergency should always reach ICU"

def test_cooperative_astar():
    from core.multi_agent import cooperative_astar
    agents = [
        {"id": "A1", "name": "Ambulance 1", "start": "ENTRANCE_MAIN", "goal": "Node_302_ICU_Tower", "priority": "critical"},
        {"id": "A2", "name": "Ambulance 2", "start": "Node_302_ICU_Tower", "goal": "ENTRANCE_MAIN", "priority": "urgent"}
    ]
    res = cooperative_astar(hospital="charite", agents_config=agents, coordination_enabled=True)
    assert res["success"] is True
    assert len(res["timesteps"]) > 0
    assert res["metrics"]["makespan"] > 0
    assert not any("💥" in log for log in res["collision_log"])

