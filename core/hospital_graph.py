"""
core/hospital_graph.py
======================
Charité Campus Mitte — Hospital Navigation Graph
Two zones:
  1. Historic Wing  — stair-heavy, no elevators, restricted lab access
  2. Bettenhaus Tower — 21 floors, elevator-linked, ICU floors locked

Node metadata keys:
  zone        : 'historic' | 'bettenhaus' | 'connector'
  floor       : int (0 = ground)
  type        : 'room' | 'stairs' | 'elevator' | 'corridor' | 'icu' | 'lab' | 'ward' | 'entrance'
  restricted  : set of profiles that CANNOT enter  e.g. {'visitor'}
  wheelchair  : bool  — True means reachable without stairs

Edge metadata keys:
  weight      : travel cost (seconds)
  via         : 'stairs' | 'elevator' | 'corridor' | 'door'
  restricted  : set of profiles blocked on this edge
"""

from __future__ import annotations
import networkx as nx
from typing import Dict, Any

# ---------------------------------------------------------------------------
# Node catalogue
# ---------------------------------------------------------------------------
NODES: Dict[str, Dict[str, Any]] = {

    # ── ENTRANCES / CONNECTORS ───────────────────────────────────────────
    "ENTRANCE_MAIN":   {"zone":"connector","floor":0,"type":"entrance","restricted":set(),"wheelchair":True},
    "ENTRANCE_NORTH":  {"zone":"connector","floor":0,"type":"entrance","restricted":set(),"wheelchair":True},
    "LOBBY_BRIDGE":    {"zone":"connector","floor":0,"type":"corridor","restricted":set(),"wheelchair":True},

    # ── HISTORIC WING ────────────────────────────────────────────────────
    "HW_Lobby":        {"zone":"historic","floor":0,"type":"corridor","restricted":set(),"wheelchair":True},
    "HW_Corridor_G":   {"zone":"historic","floor":0,"type":"corridor","restricted":set(),"wheelchair":True},
    "HW_Corridor_1":   {"zone":"historic","floor":1,"type":"corridor","restricted":set(),"wheelchair":False},
    "HW_Corridor_2":   {"zone":"historic","floor":2,"type":"corridor","restricted":set(),"wheelchair":False},
    "HW_Stairs_A":     {"zone":"historic","floor":0,"type":"stairs",  "restricted":{"patient"},"wheelchair":False},
    "HW_Stairs_B":     {"zone":"historic","floor":1,"type":"stairs",  "restricted":{"patient"},"wheelchair":False},
    "Lab_101":         {"zone":"historic","floor":1,"type":"lab",     "restricted":{"visitor"},"wheelchair":False},
    "Lab_102":         {"zone":"historic","floor":1,"type":"lab",     "restricted":{"visitor"},"wheelchair":False},
    "Lab_201":         {"zone":"historic","floor":2,"type":"lab",     "restricted":{"visitor"},"wheelchair":False},
    "HW_Admin":        {"zone":"historic","floor":0,"type":"room",    "restricted":set(),"wheelchair":True},
    "HW_Pharmacy":     {"zone":"historic","floor":0,"type":"room",    "restricted":set(),"wheelchair":True},
    "HW_Radiology":    {"zone":"historic","floor":1,"type":"room",    "restricted":{"visitor"},"wheelchair":False},
    "HW_Storage":      {"zone":"historic","floor":2,"type":"room",    "restricted":{"visitor","patient"},"wheelchair":False},

    # ── BETTENHAUS TOWER ─────────────────────────────────────────────────
    "BH_Lobby":        {"zone":"bettenhaus","floor":0,"type":"corridor","restricted":set(),"wheelchair":True},
    "BH_Reception":    {"zone":"bettenhaus","floor":0,"type":"room",   "restricted":set(),"wheelchair":True},
    "Elevator_A":      {"zone":"bettenhaus","floor":0,"type":"elevator","restricted":set(),"wheelchair":True},
    "Elevator_B":      {"zone":"bettenhaus","floor":0,"type":"elevator","restricted":set(),"wheelchair":True},
    "BH_Stairs_C":     {"zone":"bettenhaus","floor":0,"type":"stairs", "restricted":{"patient"},"wheelchair":False},

    # Floor 1
    "BH_F1_Corridor":  {"zone":"bettenhaus","floor":1,"type":"corridor","restricted":set(),"wheelchair":True},
    "Ward_F1_A":       {"zone":"bettenhaus","floor":1,"type":"ward",   "restricted":set(),"wheelchair":True},
    "Ward_F1_B":       {"zone":"bettenhaus","floor":1,"type":"ward",   "restricted":{"visitor"},"wheelchair":True},

    # Floor 2
    "BH_F2_Corridor":  {"zone":"bettenhaus","floor":2,"type":"corridor","restricted":set(),"wheelchair":True},
    "Ward_F2_A":       {"zone":"bettenhaus","floor":2,"type":"ward",   "restricted":set(),"wheelchair":True},
    "Operating_F2":    {"zone":"bettenhaus","floor":2,"type":"room",   "restricted":{"visitor","patient"},"wheelchair":True},

    # Floor 3 — ICU (locked to visitors)
    "BH_F3_Corridor":  {"zone":"bettenhaus","floor":3,"type":"corridor","restricted":{"visitor"},"wheelchair":True},
    "ICU_Floor3":      {"zone":"bettenhaus","floor":3,"type":"icu",    "restricted":{"visitor","patient"},"wheelchair":True},
    "ICU_Floor3_B":    {"zone":"bettenhaus","floor":3,"type":"icu",    "restricted":{"visitor","patient"},"wheelchair":True},
    "Node_302_ICU_Tower":{"zone":"bettenhaus","floor":3,"type":"icu",  "restricted":{"visitor","patient"},"wheelchair":True},

    # Floor 5 — Neuro ward
    "BH_F5_Corridor":  {"zone":"bettenhaus","floor":5,"type":"corridor","restricted":set(),"wheelchair":True},
    "Ward_Neuro_F5":   {"zone":"bettenhaus","floor":5,"type":"ward",   "restricted":set(),"wheelchair":True},

    # Floor 7 — Cardiology
    "BH_F7_Corridor":  {"zone":"bettenhaus","floor":7,"type":"corridor","restricted":set(),"wheelchair":True},
    "Ward_Cardio_F7":  {"zone":"bettenhaus","floor":7,"type":"ward",   "restricted":set(),"wheelchair":True},
    "Lab_Cardio_F7":   {"zone":"bettenhaus","floor":7,"type":"lab",    "restricted":{"visitor"},"wheelchair":True},

    # Floor 10 — Maternity
    "BH_F10_Corridor": {"zone":"bettenhaus","floor":10,"type":"corridor","restricted":set(),"wheelchair":True},
    "Ward_Maternity_F10":{"zone":"bettenhaus","floor":10,"type":"ward","restricted":set(),"wheelchair":True},

    # Floor 15 — Oncology
    "BH_F15_Corridor": {"zone":"bettenhaus","floor":15,"type":"corridor","restricted":set(),"wheelchair":True},
    "Ward_Oncology_F15":{"zone":"bettenhaus","floor":15,"type":"ward", "restricted":{"visitor"},"wheelchair":True},

    # Floor 21 — Roof / Admin
    "BH_F21_Admin":    {"zone":"bettenhaus","floor":21,"type":"room",  "restricted":{"visitor","patient"},"wheelchair":True},
}

# ---------------------------------------------------------------------------
# Edge catalogue  (undirected; each tuple = (u, v, attrs))
# ---------------------------------------------------------------------------
EDGES = [
    # ENTRANCES → LOBBIES
    ("ENTRANCE_MAIN",  "HW_Lobby",       {"weight":5,  "via":"door",     "restricted":set()}),
    ("ENTRANCE_MAIN",  "BH_Lobby",       {"weight":8,  "via":"door",     "restricted":set()}),
    ("ENTRANCE_NORTH", "BH_Lobby",       {"weight":6,  "via":"door",     "restricted":set()}),
    ("LOBBY_BRIDGE",   "HW_Lobby",       {"weight":10, "via":"corridor", "restricted":set()}),
    ("LOBBY_BRIDGE",   "BH_Lobby",       {"weight":10, "via":"corridor", "restricted":set()}),

    # HISTORIC WING — ground
    ("HW_Lobby",       "HW_Corridor_G",  {"weight":5,  "via":"corridor", "restricted":set()}),
    ("HW_Corridor_G",  "HW_Admin",       {"weight":3,  "via":"corridor", "restricted":set()}),
    ("HW_Corridor_G",  "HW_Pharmacy",    {"weight":4,  "via":"corridor", "restricted":set()}),
    ("HW_Corridor_G",  "HW_Stairs_A",    {"weight":2,  "via":"corridor", "restricted":{"patient"}}),

    # HISTORIC WING — stairs to floor 1
    ("HW_Stairs_A",    "HW_Corridor_1",  {"weight":15, "via":"stairs",   "restricted":{"patient"}}),
    ("HW_Corridor_1",  "Lab_101",        {"weight":3,  "via":"corridor", "restricted":{"visitor"}}),
    ("HW_Corridor_1",  "Lab_102",        {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),
    ("HW_Corridor_1",  "HW_Radiology",   {"weight":5,  "via":"corridor", "restricted":{"visitor"}}),
    ("HW_Corridor_1",  "HW_Stairs_B",    {"weight":2,  "via":"corridor", "restricted":{"patient"}}),

    # HISTORIC WING — stairs to floor 2
    ("HW_Stairs_B",    "HW_Corridor_2",  {"weight":15, "via":"stairs",   "restricted":{"patient"}}),
    ("HW_Corridor_2",  "Lab_201",        {"weight":3,  "via":"corridor", "restricted":{"visitor"}}),
    ("HW_Corridor_2",  "HW_Storage",     {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),

    # BETTENHAUS TOWER — ground
    ("BH_Lobby",       "BH_Reception",   {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_Lobby",       "Elevator_A",     {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_Lobby",       "Elevator_B",     {"weight":4,  "via":"corridor", "restricted":set()}),
    ("BH_Lobby",       "BH_Stairs_C",    {"weight":2,  "via":"corridor", "restricted":{"patient"}}),

    # ELEVATORS — to each floor (weight = floor * 12 sec per floor)
    ("Elevator_A",     "BH_F1_Corridor", {"weight":12, "via":"elevator", "restricted":set()}),
    ("Elevator_A",     "BH_F2_Corridor", {"weight":24, "via":"elevator", "restricted":set()}),
    ("Elevator_A",     "BH_F3_Corridor", {"weight":36, "via":"elevator", "restricted":{"visitor"}}),
    ("Elevator_A",     "BH_F5_Corridor", {"weight":60, "via":"elevator", "restricted":set()}),
    ("Elevator_A",     "BH_F7_Corridor", {"weight":84, "via":"elevator", "restricted":set()}),
    ("Elevator_A",     "BH_F10_Corridor",{"weight":120,"via":"elevator", "restricted":set()}),
    ("Elevator_A",     "BH_F15_Corridor",{"weight":180,"via":"elevator", "restricted":set()}),
    ("Elevator_A",     "BH_F21_Admin",   {"weight":252,"via":"elevator", "restricted":{"visitor","patient"}}),

    ("Elevator_B",     "BH_F1_Corridor", {"weight":12, "via":"elevator", "restricted":set()}),
    ("Elevator_B",     "BH_F2_Corridor", {"weight":24, "via":"elevator", "restricted":set()}),
    ("Elevator_B",     "BH_F3_Corridor", {"weight":36, "via":"elevator", "restricted":{"visitor"}}),
    ("Elevator_B",     "BH_F5_Corridor", {"weight":60, "via":"elevator", "restricted":set()}),
    ("Elevator_B",     "BH_F7_Corridor", {"weight":84, "via":"elevator", "restricted":set()}),
    ("Elevator_B",     "BH_F10_Corridor",{"weight":120,"via":"elevator", "restricted":set()}),
    ("Elevator_B",     "BH_F15_Corridor",{"weight":180,"via":"elevator", "restricted":set()}),

    # STAIRS — bettenhaus (patient-restricted)
    ("BH_Stairs_C",    "BH_F1_Corridor", {"weight":20, "via":"stairs",   "restricted":{"patient"}}),
    ("BH_Stairs_C",    "BH_F2_Corridor", {"weight":40, "via":"stairs",   "restricted":{"patient"}}),
    ("BH_Stairs_C",    "BH_F3_Corridor", {"weight":60, "via":"stairs",   "restricted":{"patient","visitor"}}),

    # FLOOR 1
    ("BH_F1_Corridor", "Ward_F1_A",      {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F1_Corridor", "Ward_F1_B",      {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),

    # FLOOR 2
    ("BH_F2_Corridor", "Ward_F2_A",      {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F2_Corridor", "Operating_F2",   {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),

    # FLOOR 3 — ICU
    ("BH_F3_Corridor", "ICU_Floor3",     {"weight":4,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("BH_F3_Corridor", "ICU_Floor3_B",   {"weight":5,  "via":"corridor", "restricted":{"visitor","patient"}}),
    ("ICU_Floor3",     "Node_302_ICU_Tower",{"weight":2,"via":"corridor","restricted":{"visitor","patient"}}),
    ("ICU_Floor3_B",   "Node_302_ICU_Tower",{"weight":3,"via":"corridor","restricted":{"visitor","patient"}}),

    # FLOOR 5
    ("BH_F5_Corridor", "Ward_Neuro_F5",  {"weight":3,  "via":"corridor", "restricted":set()}),

    # FLOOR 7
    ("BH_F7_Corridor", "Ward_Cardio_F7", {"weight":3,  "via":"corridor", "restricted":set()}),
    ("BH_F7_Corridor", "Lab_Cardio_F7",  {"weight":4,  "via":"corridor", "restricted":{"visitor"}}),

    # FLOOR 10
    ("BH_F10_Corridor","Ward_Maternity_F10",{"weight":3,"via":"corridor","restricted":set()}),

    # FLOOR 15
    ("BH_F15_Corridor","Ward_Oncology_F15",{"weight":3,"via":"corridor","restricted":{"visitor"}}),

    # FLOOR 21
    # (Elevator_A -> BH_F21_Admin already listed)
]

# ---------------------------------------------------------------------------
# Graph factory
# ---------------------------------------------------------------------------

def build_graph(profile: str = "staff") -> nx.Graph:
    """
    Build a filtered NetworkX graph for the given access profile.

    Profiles: 'visitor' | 'patient' | 'staff' | 'emergency'

    'emergency' overrides ALL restrictions.
    'staff' has full access (no restrictions apply).
    'visitor' and 'patient' have nodes/edges pruned accordingly.

    Complexity: O(V + E)
    """
    G = nx.Graph()

    for node_id, attrs in NODES.items():
        restricted = attrs.get("restricted", set())
        if profile not in ("staff", "emergency") and profile in restricted:
            continue  # prune this node for the profile
        G.add_node(node_id, **attrs)

    for u, v, attrs in EDGES:
        if u not in G.nodes or v not in G.nodes:
            continue  # one endpoint pruned
        edge_restricted = attrs.get("restricted", set())
        if profile not in ("staff", "emergency") and profile in edge_restricted:
            continue  # prune this edge
        # For patient profile: also block stair edges
        if profile == "patient" and attrs.get("via") == "stairs":
            continue
        G.add_edge(u, v, **attrs)

    return G


def heuristic(u: str, v: str) -> float:
    """
    Admissible heuristic for A*: floor-difference * 12 (elevator seconds per floor).
    Never overestimates because real elevator cost >= 12 * |floor_diff|.

    Complexity: O(1)
    """
    floor_u = NODES.get(u, {}).get("floor", 0)
    floor_v = NODES.get(v, {}).get("floor", 0)
    return abs(floor_u - floor_v) * 12


def node_label(node_id: str) -> str:
    """Short display label for UI."""
    return node_id.replace("_", " ")


def get_node_color(node_id: str) -> str:
    """Returns a colour string for pyvis based on node type."""
    t = NODES.get(node_id, {}).get("type", "corridor")
    return {
        "icu":      "#e74c3c",
        "lab":      "#8e44ad",
        "elevator": "#2980b9",
        "stairs":   "#f39c12",
        "ward":     "#27ae60",
        "entrance": "#1abc9c",
        "room":     "#95a5a6",
        "corridor": "#bdc3c7",
    }.get(t, "#bdc3c7")


if __name__ == "__main__":
    G = build_graph("staff")
    print(f"Staff graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    G2 = build_graph("visitor")
    print(f"Visitor graph: {G2.number_of_nodes()} nodes, {G2.number_of_edges()} edges")
