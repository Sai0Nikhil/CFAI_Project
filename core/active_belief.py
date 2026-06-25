"""
core/active_belief.py
=====================
Active Belief Routing (POMDP-lite) Solver.
Calculates Shannon Entropy on HMM belief states over time (decaying sensor observations).
Decides whether to perform Exploration (detour to observation node to resolve uncertainty)
or Exploitation (taking the direct path and risking congestion).
"""

import math
from typing import Dict, Any, List
import networkx as nx
from core.bayes import HMM_A, HMM_PI, HMM_STATES

# Steady state calculation or transition step diffusion
def diffuse_belief(initial_belief: List[float], steps: int) -> List[float]:
    """
    Apply transition matrix HMM_A repeatedly to diffuse belief over time steps.
    """
    belief = list(initial_belief)
    for _ in range(steps):
        next_b = [0.0, 0.0, 0.0]
        for j in range(3):
            next_b[j] = sum(belief[i] * HMM_A[i][j] for i in range(3))
        belief = next_b
    return belief

def calculate_shannon_entropy(belief: List[float]) -> float:
    """
    Compute Shannon Entropy of state distribution: H(X) = -sum(p * log2(p)).
    Maximum entropy for 3 states is log2(3) = 1.58.
    """
    entropy = 0.0
    for p in belief:
        if p > 0.0:
            entropy -= p * math.log2(p)
    return entropy

def solve_active_belief_routing(
    start: str,
    goal: str,
    hospital: str = "charite",
    entropy_threshold: float = 0.8,
    sensor_ages: Dict[str, float] = None, # maps node_id to age in hours
    active_belief_enabled: bool = True
) -> Dict[str, Any]:
    """
    POMDP-lite routing solver.
    1. Find direct A* path.
    2. Compute Shannon Entropy H(X) for nodes along the path.
    3. If any node has H(X) >= entropy_threshold, look for the nearest "observation point" (e.g. adjacent sensor/camera node).
    4. Calculate:
       - Direct Expected Cost = Base Cost + Risk Penalty
         Where Risk Penalty = (Prob(medium)*40s + Prob(high)*150s) * (Age in hours / 2.0)
       - Detour Cost = Route via Observation Node (which resolves uncertainty to entropy=0)
       - If Detour Cost < Direct Expected Cost AND active_belief_enabled is True, trigger Detour.
    """
    from core.hospital_graph import build_graph as _charite_bg
    from core.aiims_graph   import build_graph as _aiims_bg
    
    bgfn = _aiims_bg if hospital == "aiims" else _charite_bg
    # Use full staff graph for routing
    G = bgfn("staff")

    if sensor_ages is None:
        sensor_ages = {}

    # 1. Compute direct A* path
    try:
        direct_path = nx.shortest_path(G, source=start, target=goal, weight="weight")
        direct_cost = nx.shortest_path_length(G, source=start, target=goal, weight="weight")
    except Exception:
        # Fallback if no path found
        return {
            "path": [],
            "cost": 0,
            "detour_triggered": False,
            "nodes_entropy": {},
            "decision_log": ["No path exists in the hospital graph between selected nodes."],
            "is_exploit": True
        }

    # 2. Analyze entropy for nodes in path
    nodes_entropy = {}
    path_entropy_nodes = []
    
    # Predefined baseline prior belief (uniform or HMM_PI)
    base_belief = list(HMM_PI) # [0.50, 0.35, 0.15]

    for node in direct_path:
        age = float(sensor_ages.get(node, 0.0))
        # Age translates to transition diffusion steps (e.g. 1 step per hour)
        steps = int(math.ceil(age))
        if steps > 0:
            diffused = diffuse_belief(base_belief, steps)
        else:
            # Fresh observation: low entropy (e.g. P(low)=0.9, P(med)=0.08, P(high)=0.02)
            diffused = [0.90, 0.08, 0.02]
            
        entropy = calculate_shannon_entropy(diffused)
        nodes_entropy[node] = {
            "age_hours": age,
            "entropy": round(entropy, 3),
            "belief": [round(p, 3) for p in diffused]
        }
        if entropy >= entropy_threshold:
            path_entropy_nodes.append((node, entropy, diffused))

    # 3. Check detours if active belief routing is enabled
    detour_triggered = False
    final_path = list(direct_path)
    final_cost = direct_cost
    decision_log = []
    is_exploit = True
    detour_node = None
    direct_expected_cost = direct_cost

    decision_log.append(f"📡 Direct A* Path found: {' → '.join(direct_path)} (Cost: {direct_cost:.0f}s).")

    if path_entropy_nodes:
        # Find the node with the highest uncertainty
        target_node, max_h, max_b = max(path_entropy_nodes, key=lambda x: x[1])
        decision_log.append(f"⚠️ High uncertainty node detected: {target_node} with Entropy = {max_h:.2f} (Threshold: {entropy_threshold:.2f}).")
        
        # Calculate Risk Penalty
        # Risk is higher when high/medium occupancy is more probable and age is higher
        prob_med = max_b[1]
        prob_high = max_b[2]
        congestion_penalty = (prob_med * 60.0 + prob_high * 180.0)
        direct_expected_cost = direct_cost + congestion_penalty
        
        decision_log.append(f"🔍 Direct Expected Cost = Base Cost ({direct_cost:.0f}s) + Congestion Risk ({congestion_penalty:.1f}s) = {direct_expected_cost:.1f}s.")

        # Find an observation/alternative node near target_node
        # We can find neighbors of target_node that aren't on the direct path
        neighbors = list(G.neighbors(target_node))
        candidates = [n for n in neighbors if n not in direct_path]
        if not candidates:
            candidates = neighbors
            
        if candidates:
            # Let's pick a candidate to act as our "observation sensor scan"
            detour_node = candidates[0]
            
            # Find detour route: start -> detour_node -> goal
            try:
                path_to_obs = nx.shortest_path(G, source=start, target=detour_node, weight="weight")
                cost_to_obs = nx.shortest_path_length(G, source=start, target=detour_node, weight="weight")
                path_from_obs = nx.shortest_path(G, source=detour_node, target=goal, weight="weight")
                cost_from_obs = nx.shortest_path_length(G, source=detour_node, target=goal, weight="weight")
                
                detour_candidate_path = path_to_obs[:-1] + path_from_obs
                detour_candidate_cost = cost_to_obs + cost_from_obs
                
                decision_log.append(f"👀 Detour path via observation node {detour_node}: {' → '.join(detour_candidate_path)} (Cost: {detour_candidate_cost:.0f}s).")
                
                if active_belief_enabled:
                    if detour_candidate_cost < direct_expected_cost:
                        detour_triggered = True
                        is_exploit = False
                        final_path = detour_candidate_path
                        final_cost = detour_candidate_cost
                        decision_log.append(f"⚡ [EXPLORATION SELECTED] Detour cost ({detour_candidate_cost:.0f}s) < Expected direct cost ({direct_expected_cost:.1f}s). Routing via detour.")
                    else:
                        decision_log.append(f"🛡️ [EXPLOITATION SELECTED] Detour cost ({detour_candidate_cost:.0f}s) is too high compared to risk. Sticking to direct path.")
                else:
                    decision_log.append(f"ℹ️ Active Belief Routing disabled. Proceeding with standard direct path (Exploit).")
            except Exception:
                decision_log.append(f"❌ Failed to calculate detour path via neighbor {detour_node}.")
        else:
            decision_log.append(f"❌ No valid observation nodes found near {target_node} to schedule detour.")
    else:
        decision_log.append(f"✅ All path nodes are under the entropy threshold. Direct routing is optimal.")

    return {
        "path": final_path,
        "cost": final_cost,
        "base_cost": direct_cost,
        "direct_expected_cost": round(direct_expected_cost, 1),
        "detour_triggered": detour_triggered,
        "detour_node": detour_node,
        "nodes_entropy": nodes_entropy,
        "decision_log": decision_log,
        "is_exploit": is_exploit,
        "explanation": (
            f"Active Belief Routing: {'Explored detour via ' + detour_node if detour_triggered else 'Exploited direct path'}. "
            f"Resulting route cost: {final_cost:.0f}s."
        )
    }

if __name__ == "__main__":
    # Test diffusion
    print("Diffusion steps:")
    for step in range(5):
        b = diffuse_belief(HMM_PI, step)
        e = calculate_shannon_entropy(b)
        print(f"Step {step}: Belief={b}, Entropy={e:.3f}")
        
    print("\nRouting test:")
    res = solve_active_belief_routing(
        "ENTRANCE_MAIN", 
        "Node_302_ICU_Tower", 
        entropy_threshold=0.8,
        sensor_ages={"ICU_Floor3": 4.0}, # make ICU_Floor3 observation old!
        active_belief_enabled=True
    )
    for log in res["decision_log"]:
        print(log)
