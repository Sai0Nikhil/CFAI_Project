"""
core/multi_agent.py
===================
Cooperative Multi-Agent Path Finding (MAPF) Solver.
Uses space-time Cooperative A* with space-time reservation tables to route 
multiple ambulances without vertex or edge collisions.
"""

import heapq
from typing import List, Dict, Any, Tuple, Set
import networkx as nx

# Urgency map to sort priority
PRIORITY_WEIGHTS = {
    "critical": 3,
    "urgent": 2,
    "standard": 1
}

def cooperative_astar(
    hospital: str = "charite",
    agents_config: List[Dict[str, Any]] = None,
    coordination_enabled: bool = True
) -> Dict[str, Any]:
    """
    Runs Cooperative A* on the selected hospital graph.
    agents_config: list of dicts:
       [{"id": "A1", "name": "Ambulance 1", "start": "ENTRANCE_MAIN", "goal": "Node_302_ICU_Tower", "priority": "critical"}, ...]
    """
    from core.hospital_graph import build_graph as _charite_bg
    from core.aiims_graph   import build_graph as _aiims_bg

    bgfn = _aiims_bg if hospital == "aiims" else _charite_bg
    G = bgfn("staff") # full graph

    if not agents_config:
        # Default scenario: Ambulance 1 and Ambulance 2 start at opposite ends and cross
        agents_config = [
            {"id": "A1", "name": "Ambulance 1", "start": "ENTRANCE_MAIN", "goal": "Node_302_ICU_Tower", "priority": "critical"},
            {"id": "A2", "name": "Ambulance 2", "start": "Node_302_ICU_Tower", "goal": "ENTRANCE_MAIN", "priority": "urgent"}
        ]

    # Validate starts and goals exist
    for ag in agents_config:
        if ag["start"] not in G or ag["goal"] not in G:
            return {
                "success": False,
                "error": f"Invalid start/goal for agent '{ag.get('name', ag.get('id'))}'",
                "timesteps": [],
                "collision_log": ["Error: Start or goal node not found in graph."]
            }

    # Sort agents by priority level (descending)
    sorted_agents = sorted(
        agents_config,
        key=lambda x: PRIORITY_WEIGHTS.get(x.get("priority", "standard").lower(), 1),
        reverse=True
    )

    # Global reservation tables
    # reserved_nodes: set of tuples (node, time_step)
    # reserved_edges: set of tuples (u, v, time_step) - meaning someone goes u -> v starting at time_step
    reserved_nodes: Set[Tuple[str, int]] = set()
    reserved_edges: Set[Tuple[str, str, int]] = set()

    collision_log = []
    agent_paths: Dict[str, List[str]] = {}
    agent_costs: Dict[str, float] = {}
    max_time_steps = 30 # Limit space-time search depth to prevent infinity loops

    # For independent search fallback
    if not coordination_enabled:
        collision_log.append("⚠️ Multi-agent coordination disabled. Running independent A* routing...")
        for ag in sorted_agents:
            try:
                path = nx.shortest_path(G, source=ag["start"], target=ag["goal"], weight="weight")
                cost = nx.shortest_path_length(G, source=ag["start"], target=ag["goal"], weight="weight")
                agent_paths[ag["id"]] = path
                agent_costs[ag["id"]] = cost
            except Exception:
                agent_paths[ag["id"]] = []
                agent_costs[ag["id"]] = 0.0

        # Detect collisions in independent pathing
        # Pad paths to same length
        max_len = max(len(p) for p in agent_paths.values()) if agent_paths else 0
        padded_paths = {}
        for aid, p in agent_paths.items():
            if p:
                padded_paths[aid] = p + [p[-1]] * (max_len - len(p))
            else:
                padded_paths[aid] = []

        # Check vertex collisions
        for t in range(max_len):
            occupied = {}
            for aid, path in padded_paths.items():
                if not path: continue
                n = path[t]
                if n in occupied:
                    collision_log.append(f"💥 Collision at step t={t} at node '{n}' between {occupied[n]} and {aid}!")
                else:
                    occupied[n] = aid

            # Check edge swaps
            if t < max_len - 1:
                for a1, p1 in padded_paths.items():
                    for a2, p2 in padded_paths.items():
                        if a1 >= a2 or not p1 or not p2: continue
                        u1, v1 = p1[t], p1[t+1]
                        u2, v2 = p2[t], p2[t+1]
                        if u1 == v2 and v1 == u2 and u1 != v1:
                          collision_log.append(f"💥 Swap Collision at step t={t} on corridor '{u1} ↔ {v1}' between {a1} and {a2}!")

    else:
        # Cooperative coordination active!
        collision_log.append("📡 Space-Time Cooperative A* coordinator active.")
        
        for idx, ag in enumerate(sorted_agents):
            name = ag["name"]
            aid = ag["id"]
            start = ag["start"]
            goal = ag["goal"]
            priority_label = ag.get("priority", "standard").upper()

            collision_log.append(f"🔍 Routing agent '{name}' (Priority: {priority_label})...")

            # Space-time A* search
            # heap queue element: (f_score, g_cost, current_node, time_step, path_list)
            # We want to minimize total travel time (g_cost represents total seconds)
            h_start = nx.shortest_path_length(G, source=start, target=goal, weight="weight")
            queue = [(h_start, 0.0, start, 0, [start])]
            visited = set()
            found = False

            while queue:
                f, g, u, t, path = heapq.heappop(queue)

                state_key = (u, t)
                if state_key in visited:
                    continue
                visited.add(state_key)

                if t > max_time_steps:
                    continue

                if u == goal:
                    # Found path!
                    agent_paths[aid] = path
                    agent_costs[aid] = g
                    found = True
                    collision_log.append(f"✅ Route planned for '{name}': { ' → '.join(path) } (Cost: {g:.0f}s, time steps: {t}).")

                    # Lock node for all future times to represent parked vehicle
                    for future_t in range(t, max_time_steps + 10):
                        reserved_nodes.add((goal, future_t))

                    # Reserve nodes & edges along the path
                    for step_t, node in enumerate(path):
                        reserved_nodes.add((node, step_t))
                        if step_t < len(path) - 1:
                            next_node = path[step_t + 1]
                            reserved_edges.add((node, next_node, step_t))
                    break

                # Neighbors transitions
                # 1. Travel to adjacent neighbors
                for neighbor in G.neighbors(u):
                    next_t = t + 1
                    
                    # Vertex collision check
                    if (neighbor, next_t) in reserved_nodes:
                        continue
                        
                    # Swap collision check
                    if (neighbor, u, t) in reserved_edges:
                        continue

                    # Edge cost
                    edge_w = G[u][neighbor]["weight"]
                    next_g = g + edge_w
                    h_val = nx.shortest_path_length(G, source=neighbor, target=goal, weight="weight")
                    next_f = next_g + h_val
                    
                    heapq.heappush(queue, (next_f, next_g, neighbor, next_t, path + [neighbor]))

                # 2. Wait in place transition (to let higher priority agents pass)
                next_t = t + 1
                if (u, next_t) not in reserved_nodes:
                    # Wait cost penalty (e.g. 10 seconds delay)
                    next_g = g + 10.0
                    h_val = nx.shortest_path_length(G, source=u, target=goal, weight="weight")
                    next_f = next_g + h_val
                    # Log wait action if we are yielding
                    heapq.heappush(queue, (next_f, next_g, u, next_t, path + [u]))

            if not found:
                collision_log.append(f"❌ Failed to find collision-free path for '{name}'. Falling back to independent route.")
                # Fallback to direct shortest path
                try:
                    direct_path = nx.shortest_path(G, source=start, target=goal, weight="weight")
                    direct_cost = nx.shortest_path_length(G, source=start, target=goal, weight="weight")
                    agent_paths[aid] = direct_path
                    agent_costs[aid] = direct_cost
                except Exception:
                    agent_paths[aid] = []
                    agent_costs[aid] = 0.0

    # Build space-time grid timetables for UI
    max_len = max(len(p) for p in agent_paths.values()) if agent_paths else 0
    padded_paths = {}
    for aid, p in agent_paths.items():
        if p:
            padded_paths[aid] = p + [p[-1]] * (max_len - len(p))
        else:
            padded_paths[aid] = ["—"] * max_len

    # Translate to time step list: [{"t": 0, "A1": "ENTRANCE_MAIN", "A2": "ICU"}, ...]
    timesteps = []
    for t in range(max_len):
        row = {"t": t}
        for ag in agents_config:
            aid = ag["id"]
            row[aid] = padded_paths[aid][t]
        timesteps.append(row)

    makespan = max_len
    sum_of_costs = sum(agent_costs.values())

    return {
        "success": True,
        "coordination_enabled": coordination_enabled,
        "timesteps": timesteps,
        "collision_log": collision_log,
        "agent_paths": agent_paths,
        "metrics": {
            "makespan": makespan,
            "sum_of_costs": round(sum_of_costs, 1),
            "agents_count": len(agents_config)
        }
    }

if __name__ == "__main__":
    # Test Cooperative A*
    res = cooperative_astar(
        hospital="charite",
        agents_config=[
            {"id": "A1", "name": "Ambulance 1", "start": "ENTRANCE_MAIN", "goal": "Node_302_ICU_Tower", "priority": "critical"},
            {"id": "A2", "name": "Ambulance 2", "start": "Node_302_ICU_Tower", "goal": "ENTRANCE_MAIN", "priority": "urgent"}
        ],
        coordination_enabled=True
    )
    for log in res["collision_log"]:
        print(log)
    print("Makespan steps:", res["metrics"]["makespan"])
