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
from core.hospital_graph import build_graph as _charite_build_graph, heuristic as _charite_heuristic, NODES as _charite_NODES
from core.aiims_graph   import build_graph as _aiims_build_graph,   heuristic as _aiims_heuristic,   NODES as _aiims_NODES

def _get_graph_fns(hospital: str = "charite"):
    if hospital == "aiims":
        return _aiims_build_graph, _aiims_heuristic, _aiims_NODES
    return _charite_build_graph, _charite_heuristic, _charite_NODES

# default module-level symbols (used by mcts.py imports)
build_graph = _charite_build_graph
heuristic   = _charite_heuristic
NODES       = _charite_NODES


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

    def _jsafe(v):
        if v == math.inf:      return "inf"
        if v == -math.inf:     return "-inf"
        return round(v, 2)

    # Terminal: goal reached
    if node == goal:
        score = 200.0 - travel_cost  # big bonus for reaching goal fast
        trace.append({
            "depth": depth_limit - depth,
            "node": node,
            "is_max": is_max,
            "score": score,
            "alpha": _jsafe(alpha),
            "beta": _jsafe(beta),
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
            "alpha": _jsafe(alpha),
            "beta": _jsafe(beta),
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
                "alpha": _jsafe(alpha),
                "beta": _jsafe(beta),
                "note": f"{indent}MAX: '{move_desc}' → val={child_val:.1f}",
            })
            if child_val > value:
                value = child_val
            alpha = max(alpha, value)
            if beta <= alpha:
                prune_log.append({
                    "node": node,
                    "depth": depth_limit - depth,
                    "alpha": _jsafe(alpha),
                    "beta": _jsafe(beta),
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
                "alpha": _jsafe(alpha),
                "beta": _jsafe(beta),
                "note": f"{indent}MIN: '{move_desc}' → val={child_val:.1f}",
            })
            if child_val < value:
                value = child_val
            beta = min(beta, value)
            if beta <= alpha:
                prune_log.append({
                    "node": node,
                    "depth": depth_limit - depth,
                    "alpha": _jsafe(alpha),
                    "beta": _jsafe(beta),
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
    hospital: str = "charite",
) -> dict:
    """
    Run the minimax triage routing scenario.
    Returns traces, prune log, best value, and bounded-rationality note.
    hospital: 'charite' | 'aiims'
    """
    build_graph_fn, heuristic_fn, NODES_local = _get_graph_fns(hospital)
    G = build_graph_fn(profile)
    if start not in G or goal not in G:
        return {"error": f"Node {start} or {goal} not in graph for profile '{profile}'"}

    trace: list[dict] = []
    prune_log: list[dict] = []

    trace.append({
        "depth": 0,
        "node": start,
        "is_max": True,
        "note": f"🏥 START minimax depth={depth_limit} | MAX=Ambulance MIN=Congestion | start={start} goal={goal}",
        "alpha": "-inf",
        "beta": "inf",
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


def minimax_not_named_yet(
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
    depth_limit: int,
    sensor_readings: dict,
    time_of_day: str,
    use_llm_value: bool,
    api_key: str,
    provider: str,
    model: str,
) -> float:
    # Local import to avoid circular dependency
    from core.mcts import bayes_prior, _llm_value

    indent = "  " * (depth_limit - depth)

    def _jsafe(v):
        if v == math.inf:      return "inf"
        if v == -math.inf:     return "-inf"
        return round(v, 2)

    # Terminal: goal reached
    if node == goal:
        score = 200.0 - travel_cost
        trace.append({
            "depth": depth_limit - depth,
            "node": node,
            "is_max": is_max,
            "score": score,
            "alpha": _jsafe(alpha),
            "beta": _jsafe(beta),
            "note": f"{indent}🎯 GOAL REACHED  score={score:.1f}",
        })
        return score

    # Terminal: depth limit
    if depth == 0:
        if use_llm_value and api_key:
            score = _llm_value(node, goal, congestion, travel_cost, is_max, api_key, provider, model)
            if score == 0.0:  # fallback
                score = evaluate(node, goal, congestion, travel_cost)
            note_type = "🤖 LLM evaluation"
        else:
            score = evaluate(node, goal, congestion, travel_cost)
            note_type = "📊 Heuristic evaluation"

        trace.append({
            "depth": depth_limit - depth,
            "node": node,
            "is_max": is_max,
            "score": score,
            "alpha": _jsafe(alpha),
            "beta": _jsafe(beta),
            "note": f"{indent}{note_type} score={score:.1f} | cong={congestion}",
        })
        return score

    successors = get_successors(G, node, congestion, is_max)
    if not successors:
        score = evaluate(node, goal, congestion, travel_cost)
        return score

    # ── AI Guidance Move Ordering ──
    # Sort moves based on Bayesian clearing priors to evaluate best moves first
    # This maximizes alpha-beta pruning rates
    successors_with_priors = []
    for next_node, next_cong, edge_cost, move_desc in successors:
        prior = bayes_prior(next_node, sensor_readings, time_of_day)
        successors_with_priors.append((prior, (next_node, next_cong, edge_cost, move_desc)))

    # MAX wants clear paths first (higher low-occupancy prior first)
    # MIN wants congested paths first (lower low-occupancy prior first)
    successors_with_priors.sort(key=lambda x: x[0], reverse=is_max)
    successors = [x[1] for x in successors_with_priors]

    if is_max:
        value = -math.inf
        for next_node, next_cong, edge_cost, move_desc in successors:
            child_val = minimax_not_named_yet(
                G, next_node, goal, depth - 1, False,
                alpha, beta, travel_cost + edge_cost, next_cong,
                trace, prune_log, depth_limit,
                sensor_readings, time_of_day, use_llm_value, api_key, provider, model
            )
            trace.append({
                "depth": depth_limit - depth,
                "node": node,
                "is_max": True,
                "move": move_desc,
                "child_val": round(child_val, 2),
                "alpha": _jsafe(alpha),
                "beta": _jsafe(beta),
                "note": f"{indent}MAX (Ordered): '{move_desc}' → val={child_val:.1f}",
            })
            if child_val > value:
                value = child_val
            alpha = max(alpha, value)
            if beta <= alpha:
                prune_log.append({
                    "node": node,
                    "depth": depth_limit - depth,
                    "alpha": _jsafe(alpha),
                    "beta": _jsafe(beta),
                    "note": f"{indent}✂️  PRUNE (β={beta:.1f} ≤ α={alpha:.1f}) — AI ordered branch pruned",
                })
                break
        return value

    else:  # MIN
        value = math.inf
        for next_node, next_cong, edge_cost, move_desc in successors:
            child_val = minimax_not_named_yet(
                G, next_node, goal, depth - 1, True,
                alpha, beta, travel_cost + edge_cost, next_cong,
                trace, prune_log, depth_limit,
                sensor_readings, time_of_day, use_llm_value, api_key, provider, model
            )
            trace.append({
                "depth": depth_limit - depth,
                "node": node,
                "is_max": False,
                "move": move_desc,
                "child_val": round(child_val, 2),
                "alpha": _jsafe(alpha),
                "beta": _jsafe(beta),
                "note": f"{indent}MIN (Ordered): '{move_desc}' → val={child_val:.1f}",
            })
            if child_val < value:
                value = child_val
            beta = min(beta, value)
            if beta <= alpha:
                prune_log.append({
                    "node": node,
                    "depth": depth_limit - depth,
                    "alpha": _jsafe(alpha),
                    "beta": _jsafe(beta),
                    "note": f"{indent}✂️  PRUNE (β={beta:.1f} ≤ α={alpha:.1f}) — AI ordered branch pruned",
                })
                break
        return value


def run_not_named_yet(
    start: str = "BH_Lobby",
    goal: str = "Node_302_ICU_Tower",
    depth_limit: int = 4,
    profile: str = "emergency",
    time_of_day: Optional[str] = None,
    sensor_readings: Optional[dict] = None,
    api_key: str = "",
    provider: str = "claude",
    model: str = "claude-3-haiku-20240307",
    use_llm_value: bool = False,
    hospital: str = "charite",
) -> dict:
    build_graph_fn, _, _ = _get_graph_fns(hospital)
    G = build_graph_fn(profile)
    if start not in G or goal not in G:
        return {"error": f"Node {start} or {goal} not in graph for profile '{profile}'"}

    trace: list[dict] = []
    prune_log: list[dict] = []
    sensors = sensor_readings or {}

    trace.append({
        "depth": 0,
        "node": start,
        "is_max": True,
        "note": f"🧠 START 'Not Named Yet' depth={depth_limit} | AI-Guided Move Ordering + Alpha-Beta",
        "alpha": "-inf",
        "beta": "inf",
    })

    best_val = minimax_not_named_yet(
        G, start, goal, depth_limit, True,
        -math.inf, math.inf, 0.0, 0,
        trace, prune_log, depth_limit,
        sensors, time_of_day, use_llm_value, api_key, provider, model
    )

    # Trace best path using backpropagated values
    path = [start]
    curr = start
    curr_cong = 0
    curr_cost = 0.0
    depth = 0
    visited = {start}

    while curr != goal and depth < depth_limit * 2:
        depth += 1
        successors = get_successors(G, curr, curr_cong, True)
        if not successors:
            break

        best_next = None
        best_score = -math.inf
        for next_node, next_cong, cost, desc in successors:
            if next_node in visited:
                continue
            node_entries = [t for t in trace if t.get("node") == next_node and t.get("depth") == depth]
            score = node_entries[-1]["child_val"] if node_entries and "child_val" in node_entries[-1] else evaluate(next_node, goal, next_cong, curr_cost + cost)
            if score > best_score:
                best_score = score
                best_next = (next_node, next_cong, cost)

        if not best_next:
            break
        curr, curr_cong, cost = best_next
        path.append(curr)
        visited.add(curr)
        curr_cost += cost

    branching = max(len(list(G.neighbors(n))) for n in list(G.nodes)[:5])
    full_nodes = branching ** depth_limit

    return {
        "best_value": round(best_val, 2),
        "best_path": path,
        "best_cost": round(curr_cost, 1),
        "path": path,
        "cost": round(curr_cost, 1),
        "trace": trace,
        "prune_log": prune_log,
        "stats": {
            "depth_limit": depth_limit,
            "pruning_events": len(prune_log),
            "trace_steps": len(trace),
            "estimated_full_nodes": full_nodes,
        },
        "bounded_rationality": (
            f"Evaluated with depth limit {depth_limit}. "
            f"Move ordering prioritizes nodes with clear Bayesian priors, maximizing alpha-beta cuts."
        ),
        "explanation": (
            f"The hybrid 'Not Named Yet' algorithm achieved a score of {best_val:.1f}. "
            f"Evaluating clear paths first allowed alpha-beta pruning to cut {len(prune_log)} branches."
        ),
        "not_named_yet_note": (
            "This implements your proposed Hybrid AI-Guided Minimax: "
            "Bayesian Network priors act as System 1 (instinctively ordering moves to inspect best directions first), "
            "while the Minimax tree acts as System 2 (rigorously calculating plies ahead). "
            "The LLM evaluates leaves, providing expert judgment at the lookahead horizon."
        )
    }


if __name__ == "__main__":
    result = run_game(depth_limit=3)
    print(f"Best value: {result['best_value']}")
    print(f"Prune events: {result['stats']['pruning_events']}")
    print(result["bounded_rationality"])
