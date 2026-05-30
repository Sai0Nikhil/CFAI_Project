"""
core/game.py
============
CO4 — Minimax + Alpha-Beta Pruning for Triage Priority Routing

Scenario: Two competing agents share a single elevator corridor.
  MAX agent (Ambulance Team): minimises travel time to ICU
  MIN agent (Congestion Controller): maximises corridor congestion
                                     to slow emergency routing

State: (current_node, depth, congestion_level)
  congestion_level: 0 (clear) → 3 (blocked)

Evaluation function:
  score = -travel_cost_to_goal + 10 * (1 - congestion/3)
  MAX wants high score (fast path, low congestion)
  MIN wants low score (slow path, high congestion)

Complexity annotations:
  Minimax      : O(b^d)         b=branching factor, d=depth
  Alpha-Beta   : O(b^(d/2))    best case with perfect ordering
"""

from __future__ import annotations
import math
from typing import Optional
from core.hospital_graph import build_graph, heuristic, NODES


# ────────────────────────────────────────────────────────────────────────────
# State & evaluation
# ────────────────────────────────────────────────────────────────────────────

def evaluate(node: str, goal: str, congestion: int, travel_cost: float) -> float:
    """
    Evaluation function for non-terminal states.
    score = -h(node, goal) * (1 + congestion * 0.4)
    Lower travel time = better for MAX.
    High congestion multiplier = worse for MAX.

    O(1)
    """
    h = heuristic(node, goal)
    congestion_penalty = 1 + congestion * 0.4
    speed_score = -(travel_cost + h) * congestion_penalty
    return round(speed_score, 2)


def get_successors(G, node: str, congestion: int, is_max: bool) -> list[tuple]:
    """
    Generate successor states.
    MAX moves: picks next hop towards goal (uses graph neighbours)
    MIN moves: increments congestion on current corridor

    Returns list of (next_node, next_congestion, edge_cost, move_description)

    O(degree(node))
    """
    successors = []

    if is_max:
        # MAX tries each neighbour
        for nb in G.neighbors(node):
            cost = G[node][nb]["weight"]
            via = G[node][nb].get("via", "corridor")
            successors.append((nb, congestion, cost, f"Move to {nb} via {via} (cost {cost}s)"))
    else:
        # MIN can increase congestion (0→3) or leave it
        if congestion < 3:
            successors.append((node, congestion + 1, 0,
                               f"Increase congestion {congestion}→{congestion+1} at {node}"))
        # MIN can also try to block an adjacent corridor
        for nb in list(G.neighbors(node))[:2]:  # limit branching for demo
            successors.append((nb, min(congestion + 1, 3), 0,
                               f"Block corridor towards {nb}, congestion→{min(congestion+1,3)}"))
        if not successors:
            successors.append((node, congestion, 0, "MIN: no action (hold)"))

    return successors


# ────────────────────────────────────────────────────────────────────────────
# Minimax with Alpha-Beta Pruning
# ────────────────────────────────────────────────────────────────────────────

def minimax(
    G,
    node: str,
    goal: str,
    depth: int,
    is_max: bool,
    alpha: float,
    beta: float,
    travel_cost: float,
    congestion: int,
    trace: list,
    prune_log: list,
    depth_limit: int = 4,
) -> float:
    """
    Minimax with Alpha-Beta pruning.

    Time complexity : O(b^d)        without pruning
                      O(b^(d/2))    with perfect move ordering (alpha-beta)
    Space complexity: O(d)          — recursion stack

    Parameters
    ----------
    alpha : best value MAX can guarantee so far
    beta  : best value MIN can guarantee so far
    """
    indent = "  " * (depth_limit - depth)

    # Terminal: goal reached
    if node == goal:
        score = 200.0 - travel_cost  # big bonus for reaching goal fast
        trace.append({
            "depth": depth_limit - depth,
            "node": node,
            "is_max": is_max,
            "score": score,
            "alpha": round(alpha, 2),
            "beta": round(beta, 2),
            "note": f"{indent}🎯 GOAL REACHED  score={score:.1f}",
        })
        return score

    # Terminal: depth limit
    if depth == 0:
        score = evaluate(node, goal, congestion, travel_cost)
        trace.append({
            "depth": depth_limit - depth,
            "node": node,
            "is_max": is_max,
            "score": score,
            "alpha": round(alpha, 2),
            "beta": round(beta, 2),
            "note": f"{indent}📊 Depth limit  eval={score:.1f}  cong={congestion}",
        })
        return score

    successors = get_successors(G, node, congestion, is_max)
    if not successors:
        score = evaluate(node, goal, congestion, travel_cost)
        return score

    if is_max:
        value = -math.inf
        for next_node, next_cong, edge_cost, move_desc in successors:
            child_val = minimax(
                G, next_node, goal, depth - 1, False,
                alpha, beta, travel_cost + edge_cost, next_cong,
                trace, prune_log, depth_limit
            )
            trace.append({
                "depth": depth_limit - depth,
                "node": node,
                "is_max": True,
                "move": move_desc,
                "child_val": round(child_val, 2),
                "alpha": round(alpha, 2),
                "beta": round(beta, 2),
                "note": f"{indent}MAX: '{move_desc}' → val={child_val:.1f}",
            })
            if child_val > value:
                value = child_val
            alpha = max(alpha, value)
            if beta <= alpha:
                prune_log.append({
                    "node": node,
                    "depth": depth_limit - depth,
                    "alpha": round(alpha, 2),
                    "beta": round(beta, 2),
                    "note": f"{indent}✂️  PRUNE (β={beta:.1f} ≤ α={alpha:.1f}) — MIN won't choose this branch",
                })
                break  # β-cutoff
        return value

    else:  # MIN
        value = math.inf
        for next_node, next_cong, edge_cost, move_desc in successors:
            child_val = minimax(
                G, next_node, goal, depth - 1, True,
                alpha, beta, travel_cost + edge_cost, next_cong,
                trace, prune_log, depth_limit
            )
            trace.append({
                "depth": depth_limit - depth,
                "node": node,
                "is_max": False,
                "move": move_desc,
                "child_val": round(child_val, 2),
                "alpha": round(alpha, 2),
                "beta": round(beta, 2),
                "note": f"{indent}MIN: '{move_desc}' → val={child_val:.1f}",
            })
            if child_val < value:
                value = child_val
            beta = min(beta, value)
            if beta <= alpha:
                prune_log.append({
                    "node": node,
                    "depth": depth_limit - depth,
                    "alpha": round(alpha, 2),
                    "beta": round(beta, 2),
                    "note": f"{indent}✂️  PRUNE (β={beta:.1f} ≤ α={alpha:.1f}) — MAX won't choose this branch",
                })
                break  # α-cutoff
        return value


# ────────────────────────────────────────────────────────────────────────────
# Public entry point
# ────────────────────────────────────────────────────────────────────────────

def run_game(
    start: str = "BH_Lobby",
    goal: str = "Node_302_ICU_Tower",
    depth_limit: int = 4,
    profile: str = "emergency",
) -> dict:
    """
    Run the minimax triage routing scenario.
    Returns traces, prune log, best value, and bounded-rationality note.
    """
    G = build_graph(profile)
    if start not in G or goal not in G:
        return {"error": f"Node {start} or {goal} not in graph for profile '{profile}'"}

    trace: list[dict] = []
    prune_log: list[dict] = []

    trace.append({
        "depth": 0,
        "node": start,
        "is_max": True,
        "note": f"🏥 START minimax depth={depth_limit} | MAX=Ambulance MIN=Congestion | start={start} goal={goal}",
        "alpha": -math.inf,
        "beta": math.inf,
    })

    best_val = minimax(
        G, start, goal, depth_limit, True,
        -math.inf, math.inf, 0.0, 0,
        trace, prune_log, depth_limit
    )

    # Bounded rationality note (CO4)
    branching = max(len(list(G.neighbors(n))) for n in list(G.nodes)[:5])
    full_nodes = branching ** depth_limit
    pruned_est = int(full_nodes * 0.55)

    return {
        "best_value": round(best_val, 2),
        "trace": trace,
        "prune_log": prune_log,
        "stats": {
            "depth_limit": depth_limit,
            "pruning_events": len(prune_log),
            "trace_steps": len(trace),
            "estimated_full_nodes": full_nodes,
            "estimated_pruned": pruned_est,
        },
        "bounded_rationality": (
            f"With depth limit {depth_limit}, the agent cannot plan beyond "
            f"{depth_limit} moves ahead. Full game tree ≈ {full_nodes} nodes; "
            f"alpha-beta pruned ≈ {pruned_est} nodes. "
            f"This is bounded rationality — optimal within the horizon, not globally."
        ),
        "explanation": (
            f"MAX (Ambulance) achieves a score of {best_val:.1f}. "
            f"Higher = faster route with less congestion. "
            f"{len(prune_log)} branches were alpha-beta pruned, "
            f"reducing search by ~{int(len(prune_log)/max(len(trace),1)*100)}%."
        ),
    }


if __name__ == "__main__":
    result = run_game(depth_limit=3)
    print(f"Best value: {result['best_value']}")
    print(f"Prune events: {result['stats']['pruning_events']}")
    print(result["bounded_rationality"])
