"""
core/csp.py
===========
CO3 — Constraint Satisfaction Problem for Hospital Access Control
Models WHICH ROUTE SEGMENTS are permissible for a given profile,
plus SCHEDULING constraints (time-window access).

Variables   : Each edge/node in the path that needs a "permitted" assignment.
Domain      : {True, False}  — can the profile traverse it?
Constraints :
  1. Node restriction  — profile not in node.restricted
  2. Edge restriction  — profile not in edge.restricted
  3. Wheelchair        — patient cannot use non-wheelchair edges
  4. Time window       — ICU access only 06:00–22:00 (staff/emergency only)

Returns: trace log of every assignment attempt + final constraint report.

Complexity annotations:
  AC-3 arc consistency : O(E * D^2) where D=2 (binary domain)
  Backtracking         : O(D^n) worst case, pruned heavily by propagation
"""

from __future__ import annotations
from typing import Any
from core.hospital_graph import NODES, EDGES, build_graph


# ────────────────────────────────────────────────────────────────────────────
# Profile definitions
# ────────────────────────────────────────────────────────────────────────────

PROFILES = {
    "visitor": {
        "label": "Visitor",
        "emoji": "👤",
        "wheelchair": False,
        "time_restrictions": True,
        "description": "General visitor: no ICU, no labs, no restricted wards.",
    },
    "patient": {
        "label": "Patient (Wheelchair)",
        "emoji": "♿",
        "wheelchair": True,
        "time_restrictions": True,
        "description": "Wheelchair patient: no stairs, no restricted zones.",
    },
    "staff": {
        "label": "Staff / Doctor",
        "emoji": "🩺",
        "wheelchair": False,
        "time_restrictions": False,
        "description": "Full access to all zones including ICU and labs.",
    },
    "emergency": {
        "label": "Emergency Responder",
        "emoji": "🚨",
        "wheelchair": False,
        "time_restrictions": False,
        "description": "Priority override — bypasses all access locks.",
    },
}

ICU_NODES = {"ICU_Floor3", "ICU_Floor3_B", "Node_302_ICU_Tower", "BH_F3_Corridor"}
ICU_ACCESS_HOURS = (6, 22)  # 06:00 – 22:00


# ────────────────────────────────────────────────────────────────────────────
# Constraint checkers (each returns (allowed: bool, reason: str))
# ────────────────────────────────────────────────────────────────────────────

def check_node_constraint(node_id: str, profile: str, hour: int = 10) -> tuple[bool, str]:
    """
    Constraint 1: Node access restriction.
    Constraint 4: Time-window for ICU.
    O(1)
    """
    if profile == "emergency":
        return True, "✅ Emergency override — all nodes permitted"

    attrs = NODES.get(node_id, {})
    restricted = attrs.get("restricted", set())

    if profile in restricted:
        return False, f"❌ Node '{node_id}' restricted for profile '{profile}'"

    if node_id in ICU_NODES and profile in ("visitor", "patient"):
        return False, f"❌ ICU zone locked for '{profile}'"

    if node_id in ICU_NODES and PROFILES[profile]["time_restrictions"]:
        if not (ICU_ACCESS_HOURS[0] <= hour < ICU_ACCESS_HOURS[1]):
            return False, f"❌ ICU access outside permitted hours (06:00–22:00), current hour={hour}"

    return True, f"✅ Node '{node_id}' permitted for '{profile}'"


def check_edge_constraint(u: str, v: str, via: str, profile: str) -> tuple[bool, str]:
    """
    Constraint 2: Edge access restriction.
    Constraint 3: Wheelchair (no stairs).
    O(1)
    """
    if profile == "emergency":
        return True, "✅ Emergency override — all edges permitted"

    # Find the edge
    edge_restricted: set = set()
    for eu, ev, eattrs in EDGES:
        if (eu == u and ev == v) or (eu == v and ev == u):
            edge_restricted = eattrs.get("restricted", set())
            break

    if profile in edge_restricted:
        return False, f"❌ Edge {u}→{v} restricted for '{profile}'"

    if PROFILES[profile]["wheelchair"] and via == "stairs":
        return False, f"❌ Edge {u}→{v} uses stairs — wheelchair constraint violated"

    return True, f"✅ Edge {u}→{v} ({via}) permitted for '{profile}'"


# ────────────────────────────────────────────────────────────────────────────
# AC-3 Arc Consistency
# ────────────────────────────────────────────────────────────────────────────

def ac3(path: list[str], profile: str, hour: int = 10) -> tuple[bool, list[dict]]:
    """
    AC-3 applied to the path's edge arcs.
    For each consecutive pair (u, v) in path: check both directions.

    Domain per node: {True}  (we only consider nodes already in the proposed path)
    AC-3 removes a node's domain to {} if any constraint fails.

    Complexity: O(E * D^2) = O(E * 4) = O(E) for binary domain

    Returns: (consistent: bool, arc_log: list[dict])
    """
    import networkx as nx
    G = build_graph("staff")  # full graph for edge attrs

    arc_log = []
    domains = {n: {"allowed"} for n in path}

    # Build arc worklist
    worklist = []
    for i in range(len(path) - 1):
        worklist.append((path[i], path[i+1]))
        worklist.append((path[i+1], path[i]))

    step = 0
    while worklist:
        u, v = worklist.pop(0)
        step += 1

        # Node check for u
        ok_u, reason_u = check_node_constraint(u, profile, hour)
        if not ok_u:
            domains[u] = set()
            arc_log.append({"step": step, "arc": f"{u}→{v}", "result": "PRUNE",
                            "reason": reason_u})
            return False, arc_log

        # Edge check
        via = G[u][v]["via"] if G.has_edge(u, v) else "unknown"
        ok_e, reason_e = check_edge_constraint(u, v, via, profile)
        if not ok_e:
            domains[u] = set()
            arc_log.append({"step": step, "arc": f"{u}→{v}", "result": "PRUNE",
                            "reason": reason_e})
            return False, arc_log

        arc_log.append({"step": step, "arc": f"{u}→{v}", "result": "OK",
                        "reason": reason_e})

    return True, arc_log


# ────────────────────────────────────────────────────────────────────────────
# Backtracking path validator with constraint propagation (forward checking)
# ────────────────────────────────────────────────────────────────────────────

def validate_path_csp(path: list[str], profile: str, hour: int = 10) -> dict:
    """
    Run full CSP validation on a proposed path:
      1. Forward checking: check each node before committing
      2. AC-3: arc consistency across the full path

    Returns a detailed report for the UI.

    Complexity: O(V + E) for a path of length V
    """
    trace = []
    step = 0

    # Forward checking pass
    fc_ok = True
    for i, node in enumerate(path):
        step += 1
        ok, reason = check_node_constraint(node, profile, hour)
        trace.append({
            "step": step,
            "phase": "Forward Check",
            "node": node,
            "result": "PASS" if ok else "FAIL",
            "reason": reason,
        })
        if not ok:
            fc_ok = False
            trace.append({
                "step": step,
                "phase": "Backtrack",
                "node": node,
                "result": "BACKTRACK",
                "reason": f"Constraint failed at position {i} — cannot proceed",
            })
            break

    # Edge checks
    if fc_ok:
        import networkx as nx
        G = build_graph("staff")
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            step += 1
            via = G[u][v]["via"] if G.has_edge(u, v) else "unknown"
            ok, reason = check_edge_constraint(u, v, via, profile)
            trace.append({
                "step": step,
                "phase": "Edge Check",
                "node": f"{u}→{v}",
                "result": "PASS" if ok else "FAIL",
                "reason": reason,
            })
            if not ok:
                fc_ok = False
                trace.append({
                    "step": step,
                    "phase": "Backtrack",
                    "node": f"{u}→{v}",
                    "result": "BACKTRACK",
                    "reason": "Edge constraint failed — prune this branch",
                })
                break

    # AC-3 pass (only if forward check passed)
    ac3_consistent, arc_log = (True, []) if not fc_ok else ac3(path, profile, hour)

    overall = fc_ok and ac3_consistent
    return {
        "profile": profile,
        "hour": hour,
        "path": path,
        "forward_check_ok": fc_ok,
        "ac3_consistent": ac3_consistent,
        "overall_valid": overall,
        "trace": trace,
        "arc_log": arc_log,
        "explanation": (
            f"✅ Path is VALID for profile '{PROFILES[profile]['label']}' at hour {hour:02d}:00"
            if overall
            else f"❌ Path REJECTED for profile '{PROFILES[profile]['label']}' — see constraint trace above"
        ),
    }


# ────────────────────────────────────────────────────────────────────────────
# Scheduling demo: find a time window where a profile CAN access ICU
# ────────────────────────────────────────────────────────────────────────────

def find_valid_time_window(profile: str, icu_node: str = "ICU_Floor3") -> dict:
    """
    MRV heuristic demo: which hours are valid for ICU access?
    Returns the smallest domain (most constrained) variable first.

    O(24) — checks each hour
    """
    valid_hours = []
    for h in range(24):
        ok, _ = check_node_constraint(icu_node, profile, h)
        if ok:
            valid_hours.append(h)
    return {
        "profile": profile,
        "node": icu_node,
        "valid_hours": valid_hours,
        "domain_size": len(valid_hours),
        "mrv_note": (
            f"Profile '{profile}' has domain size {len(valid_hours)}/24 for ICU access "
            f"(MRV selects this variable first if size is smallest)"
        ),
    }


if __name__ == "__main__":
    from core.search import run_search
    result = run_search("astar", "staff", "ENTRANCE_MAIN", "Node_302_ICU_Tower")
    path = result["path"]
    print("=== CSP Validation — Staff ===")
    r = validate_path_csp(path, "staff")
    print(r["explanation"])
    print("\n=== CSP Validation — Visitor ===")
    r2 = validate_path_csp(path, "visitor")
    print(r2["explanation"])
    for t in r2["trace"][:5]:
        print(t)
