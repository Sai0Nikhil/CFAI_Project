"""
core/search.py
==============
CO2 — Search Algorithms on the Charité Hospital Graph
Algorithms: BFS · DFS · UCS · A*

Each function returns:
  path       : list[str]  — node sequence from start to goal ([] if no path)
  cost       : float      — total edge weight along path
  trace      : list[dict] — step-by-step log for the UI trace panel
  stats      : dict       — node expansions, peak frontier size, peak memory concept

Complexity annotations are given per algorithm.
"""

from __future__ import annotations
import heapq
from collections import deque
from typing import Optional
import networkx as nx
from core.hospital_graph import build_graph as _charite_build_graph, heuristic as _charite_heuristic
from core.aiims_graph   import build_graph as _aiims_build_graph,   heuristic as _aiims_heuristic

# Module-level alias used by astar() directly — both heuristics are identical formulas
heuristic = _charite_heuristic

def _get_graph_fns(hospital: str):
    if hospital == "aiims":
        return _aiims_build_graph, _aiims_heuristic
    return _charite_build_graph, _charite_heuristic


# ────────────────────────────────────────────────────────────────────────────
# Shared helpers
# ────────────────────────────────────────────────────────────────────────────

def _reconstruct(came_from: dict, goal: str) -> list[str]:
    """Trace back from goal to start. O(path_length)."""
    path, node = [], goal
    while node is not None:
        path.append(node)
        node = came_from[node]
    return path[::-1]


def _path_cost(G: nx.Graph, path: list[str]) -> float:
    """Sum edge weights along a path. O(path_length)."""
    return sum(G[path[i]][path[i + 1]]["weight"] for i in range(len(path) - 1))


# ────────────────────────────────────────────────────────────────────────────
# BFS — Breadth-First Search
# Time: O(V + E)   Space: O(V)   Optimal: YES (unweighted)
# ────────────────────────────────────────────────────────────────────────────

def bfs(G: nx.Graph, start: str, goal: str) -> dict:
    """
    BFS explores the graph level-by-level.
    Guarantees the fewest-hops path (not fewest-cost).

    Time complexity : O(V + E)
    Space complexity: O(V)
    """
    if start not in G or goal not in G:
        return {"path": [], "cost": 0, "trace": [{"step":0,"action":"ERROR","node":start,"note":"Node not in graph"}], "stats": {}}

    frontier: deque[str] = deque([start])
    came_from: dict[str, Optional[str]] = {start: None}
    trace = []
    expansions = 0
    peak_frontier = 1

    while frontier:
        node = frontier.popleft()
        expansions += 1
        trace.append({
            "step": expansions,
            "action": "EXPAND",
            "node": node,
            "frontier_size": len(frontier),
            "note": f"BFS dequeue | frontier={len(frontier)}",
        })

        if node == goal:
            path = _reconstruct(came_from, goal)
            cost = _path_cost(G, path)
            trace.append({"step": expansions+1, "action": "GOAL FOUND", "node": goal,
                          "frontier_size": 0, "note": f"Path length {len(path)}, cost {cost:.1f}s"})
            return {"path": path, "cost": cost, "trace": trace,
                    "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}

        for neighbour in G.neighbors(node):
            if neighbour not in came_from:
                came_from[neighbour] = node
                frontier.append(neighbour)
                peak_frontier = max(peak_frontier, len(frontier))
                trace.append({
                    "step": expansions,
                    "action": "ADD",
                    "node": neighbour,
                    "frontier_size": len(frontier),
                    "note": f"  → add {neighbour} (via {node})",
                })

    trace.append({"step": expansions+1, "action": "FAILURE", "node": goal,
                  "frontier_size": 0, "note": "No path found"})
    return {"path": [], "cost": 0, "trace": trace,
            "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}


# ────────────────────────────────────────────────────────────────────────────
# DFS — Depth-First Search
# Time: O(V + E)   Space: O(V)   Optimal: NO
# ────────────────────────────────────────────────────────────────────────────

def dfs(G: nx.Graph, start: str, goal: str) -> dict:
    """
    DFS explores as deep as possible before backtracking.
    NOT guaranteed to find shortest path.

    Time complexity : O(V + E)
    Space complexity: O(V)  — call stack depth
    """
    if start not in G or goal not in G:
        return {"path": [], "cost": 0, "trace": [{"step":0,"action":"ERROR","node":start,"note":"Node not in graph"}], "stats": {}}

    stack = [(start, [start])]
    visited: set[str] = set()
    trace = []
    expansions = 0
    peak_frontier = 1

    while stack:
        node, path_so_far = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        expansions += 1
        trace.append({
            "step": expansions,
            "action": "EXPAND",
            "node": node,
            "frontier_size": len(stack),
            "note": f"DFS pop | depth={len(path_so_far)-1} | stack={len(stack)}",
        })

        if node == goal:
            cost = _path_cost(G, path_so_far)
            trace.append({"step": expansions+1, "action": "GOAL FOUND", "node": goal,
                          "frontier_size": 0, "note": f"Path length {len(path_so_far)}, cost {cost:.1f}s"})
            return {"path": path_so_far, "cost": cost, "trace": trace,
                    "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}

        for neighbour in G.neighbors(node):
            if neighbour not in visited:
                stack.append((neighbour, path_so_far + [neighbour]))
                peak_frontier = max(peak_frontier, len(stack))
                trace.append({
                    "step": expansions,
                    "action": "ADD",
                    "node": neighbour,
                    "frontier_size": len(stack),
                    "note": f"  → push {neighbour}",
                })

    trace.append({"step": expansions+1, "action": "FAILURE", "node": goal,
                  "frontier_size": 0, "note": "No path found"})
    return {"path": [], "cost": 0, "trace": trace,
            "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}


# ────────────────────────────────────────────────────────────────────────────
# UCS — Uniform Cost Search
# Time: O((V + E) log V)   Space: O(V)   Optimal: YES (weighted)
# ────────────────────────────────────────────────────────────────────────────

def ucs(G: nx.Graph, start: str, goal: str) -> dict:
    """
    UCS expands the lowest-cost frontier node first.
    Guarantees optimal cost (like Dijkstra but goal-directed).

    Time complexity : O((V + E) log V)   — priority queue operations
    Space complexity: O(V)
    """
    if start not in G or goal not in G:
        return {"path": [], "cost": 0, "trace": [{"step":0,"action":"ERROR","node":start,"note":"Node not in graph"}], "stats": {}}

    # heap entries: (cost, node, path)
    heap = [(0.0, start, [start])]
    visited: set[str] = set()
    trace = []
    expansions = 0
    peak_frontier = 1

    while heap:
        g, node, path_so_far = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        expansions += 1
        trace.append({
            "step": expansions,
            "action": "EXPAND",
            "node": node,
            "g": round(g, 1),
            "frontier_size": len(heap),
            "note": f"UCS pop | g={g:.1f}s | frontier={len(heap)}",
        })

        if node == goal:
            trace.append({"step": expansions+1, "action": "GOAL FOUND", "node": goal,
                          "g": round(g,1), "frontier_size": 0,
                          "note": f"Optimal cost {g:.1f}s | path len {len(path_so_far)}"})
            return {"path": path_so_far, "cost": g, "trace": trace,
                    "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}

        for neighbour in G.neighbors(node):
            if neighbour not in visited:
                edge_cost = G[node][neighbour]["weight"]
                new_g = g + edge_cost
                heapq.heappush(heap, (new_g, neighbour, path_so_far + [neighbour]))
                peak_frontier = max(peak_frontier, len(heap))
                trace.append({
                    "step": expansions,
                    "action": "ADD",
                    "node": neighbour,
                    "g": round(new_g, 1),
                    "frontier_size": len(heap),
                    "note": f"  → {neighbour} g={new_g:.1f}s",
                })

    trace.append({"step": expansions+1, "action": "FAILURE", "node": goal,
                  "frontier_size": 0, "note": "No path found"})
    return {"path": [], "cost": 0, "trace": trace,
            "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}


# ────────────────────────────────────────────────────────────────────────────
# A* — A-Star Search
# Time: O((V + E) log V)   Space: O(V)   Optimal: YES (admissible heuristic)
# ────────────────────────────────────────────────────────────────────────────

def astar(G: nx.Graph, start: str, goal: str) -> dict:
    """
    A* uses f(n) = g(n) + h(n) to guide search towards the goal.

    Heuristic h(n): floor-difference * 12 seconds (admissible, never overestimates).
    Tie-breaking: prefer nodes closer to goal (lower h).

    Time complexity : O((V + E) log V)
    Space complexity: O(V)
    """
    if start not in G or goal not in G:
        return {"path": [], "cost": 0, "trace": [{"step":0,"action":"ERROR","node":start,"note":"Node not in graph"}], "stats": {}}

    h_start = heuristic(start, goal)
    # heap: (f, h, g, node, path)  — h used as tie-breaker
    heap = [(h_start, h_start, 0.0, start, [start])]
    visited: set[str] = set()
    trace = []
    expansions = 0
    peak_frontier = 1

    while heap:
        f, h, g, node, path_so_far = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        expansions += 1
        trace.append({
            "step": expansions,
            "action": "EXPAND",
            "node": node,
            "f": round(f, 1),
            "g": round(g, 1),
            "h": round(h, 1),
            "frontier_size": len(heap),
            "note": f"A* pop | f={f:.1f} g={g:.1f} h={h:.1f} | frontier={len(heap)}",
        })

        if node == goal:
            trace.append({"step": expansions+1, "action": "GOAL FOUND", "node": goal,
                          "f": round(f,1), "g": round(g,1), "h": 0,
                          "frontier_size": 0,
                          "note": f"Optimal cost {g:.1f}s | path len {len(path_so_far)}"})
            return {"path": path_so_far, "cost": g, "trace": trace,
                    "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}

        for neighbour in G.neighbors(node):
            if neighbour not in visited:
                edge_cost = G[node][neighbour]["weight"]
                new_g = g + edge_cost
                new_h = heuristic(neighbour, goal)
                new_f = new_g + new_h
                heapq.heappush(heap, (new_f, new_h, new_g, neighbour, path_so_far + [neighbour]))
                peak_frontier = max(peak_frontier, len(heap))
                trace.append({
                    "step": expansions,
                    "action": "ADD",
                    "node": neighbour,
                    "f": round(new_f,1),
                    "g": round(new_g,1),
                    "h": round(new_h,1),
                    "frontier_size": len(heap),
                    "note": f"  → {neighbour} f={new_f:.1f} g={new_g:.1f} h={new_h:.1f}",
                })

    trace.append({"step": expansions+1, "action": "FAILURE", "node": goal,
                  "frontier_size": 0, "note": "No path found"})
    return {"path": [], "cost": 0, "trace": trace,
            "stats": {"expansions": expansions, "peak_frontier": peak_frontier}}


# ────────────────────────────────────────────────────────────────────────────
# Convenience runner
# ────────────────────────────────────────────────────────────────────────────

def run_search(algorithm: str, profile: str, start: str, goal: str, hospital: str = "charite") -> dict:
    """
    Unified entry point.

    algorithm: 'bfs' | 'dfs' | 'ucs' | 'astar'
    profile  : 'visitor' | 'patient' | 'staff' | 'emergency'
    hospital : 'charite' | 'aiims'
    """
    build_graph, heuristic = _get_graph_fns(hospital)
    G = build_graph(profile)
    fn = {"bfs": bfs, "dfs": dfs, "ucs": ucs, "astar": astar}[algorithm]
    result = fn(G, start, goal)
    result["graph"] = G
    result["algorithm"] = algorithm.upper()
    result["profile"] = profile
    result["start"] = start
    result["goal"] = goal
    return result


if __name__ == "__main__":
    result = run_search("astar", "staff", "ENTRANCE_MAIN", "Node_302_ICU_Tower")
    print(f"Path: {' → '.join(result['path'])}")
    print(f"Cost: {result['cost']:.1f}s | Expansions: {result['stats']['expansions']}")
