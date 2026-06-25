"""
core/mcts.py
============
CO4 (Extended) — MCTS + Neural-Guided Search for Hospital Triage Routing
AlphaZero-style hybrid: Bayesian priors guide tree expansion,
LLM evaluates leaf states as a learned value function.

Architecture
------------
  Policy (prior)   : core/bayes.py → P(occupancy=low | sensor, time)
                     High clearance probability = higher prior for that edge
  Value (rollout)  : LLM (Claude / Gemini) evaluates state at depth limit
                     Falls back to heuristic eval if no API key provided
  Search           : MCTS with UCB1, adversarial (MAX vs MIN turns)

Agents
------
  MAX = Ambulance Team         → maximise score (fast, clear path to ICU)
  MIN = Congestion Controller  → minimise score (block corridors, slow MAX)

UCB1 formula (from MAX perspective throughout):
  UCB(child) = Q(child) + C * prior * sqrt(ln(parent.N) / child.N)
  For MIN nodes: select child with lowest UCB (negate Q)

State
-----
  (node_id: str, congestion: int, travel_cost: float, is_max: bool)

Complexity
----------
  MCTS total       : O(num_simulations * sim_depth * branching)
  Bayes prior      : O(1) per edge  (table multiply)
  LLM value call   : O(API latency) — only at leaf nodes
  vs pure minimax  : O(b^d) exhaustive → MCTS focuses on promising branches
"""

from __future__ import annotations

import math
import random
from typing import Optional
from dataclasses import dataclass, field

from core.hospital_graph import build_graph as _charite_build_graph, heuristic as _charite_heuristic, NODES as _charite_NODES
from core.aiims_graph   import build_graph as _aiims_build_graph,   heuristic as _aiims_heuristic,   NODES as _aiims_NODES

def _get_graph_fns(hospital: str = "charite"):
    if hospital == "aiims":
        return _aiims_build_graph, _aiims_heuristic, _aiims_NODES
    return _charite_build_graph, _charite_heuristic, _charite_NODES

build_graph = _charite_build_graph
heuristic   = _charite_heuristic
NODES       = _charite_NODES
from core.bayes import infer_occupancy
from core.game import evaluate, get_successors   # reuse existing eval + successor logic


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

UCB_C          = 1.41   # exploration constant (√2 as in AlphaZero paper)
ROLLOUT_DEPTH  = 4      # steps for random rollout before using eval
DEFAULT_SIMS   = 200    # default MCTS iterations


# ─────────────────────────────────────────────────────────────────────────────
# MCTS Node
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class MCTSNode:
    """
    A single node in the MCTS search tree.

    state      : (node_id, congestion, travel_cost, is_max)
    parent     : parent MCTSNode or None (root)
    prior      : P(corridor_clear) from Bayes — guides exploration
    action_desc: human-readable description of how we arrived here
    """
    state: tuple                       # (node_id, congestion, travel_cost, is_max)
    parent: Optional["MCTSNode"] = field(default=None, repr=False)
    prior: float = 1.0
    action_desc: str = "root"

    visits: int = 0
    value_sum: float = 0.0
    children: list = field(default_factory=list)

    @property
    def node_id(self)    -> str:   return self.state[0]
    @property
    def congestion(self) -> int:   return self.state[1]
    @property
    def travel_cost(self)-> float: return self.state[2]
    @property
    def is_max(self)     -> bool:  return self.state[3]

    @property
    def Q(self) -> float:
        """Mean value from MAX's perspective."""
        return self.value_sum / self.visits if self.visits > 0 else 0.0

    def ucb_score(self) -> float:
        """
        UCB1 score for this node from its parent's perspective.
        MAX parent: wants high UCB  → select argmax
        MIN parent: wants low  UCB  → select argmin  (negate Q)
        """
        if self.visits == 0:
            return math.inf
        parent_visits = self.parent.visits if self.parent else 1
        exploit = self.Q if self.parent and self.parent.is_max else -self.Q
        explore = UCB_C * self.prior * math.sqrt(math.log(parent_visits) / self.visits)
        return exploit + explore

    def is_fully_expanded(self, G) -> bool:
        """True if every legal successor already has a child node."""
        return len(self.children) >= len(list(G.neighbors(self.node_id))) + (
            3 if not self.is_max else 0   # MIN also has congestion actions
        )

    def best_child(self) -> "MCTSNode":
        """Return the child with the highest UCB score."""
        return max(self.children, key=lambda c: c.ucb_score())


# ─────────────────────────────────────────────────────────────────────────────
# Bayes Prior
# ─────────────────────────────────────────────────────────────────────────────

def bayes_prior(
    node_id: str,
    sensor_readings: dict[str, str],
    time_of_day: Optional[str] = None,
) -> float:
    """
    Compute prior probability that a corridor node is navigable (low occupancy).

    Uses the existing infer_occupancy() Bayesian inference engine.
    Returns a value in [0.05, 0.95] to avoid zero/one priors.

    Higher prior  → MCTS explores this branch more
    Lower prior   → MCTS deprioritises congested corridors
    """
    sensor = sensor_readings.get(node_id, "clear")
    result = infer_occupancy(sensor, time_of_day=time_of_day)
    p_low  = result["posterior"].get("low", 0.33)
    # Clip to avoid degenerate priors
    return max(0.05, min(0.95, p_low))


# ─────────────────────────────────────────────────────────────────────────────
# LLM Value Function
# ─────────────────────────────────────────────────────────────────────────────

def _llm_value(
    node_id: str,
    goal: str,
    congestion: int,
    travel_cost: float,
    is_max: bool,
    api_key: str,
    provider: str = "claude",
    model: str = "claude-3-haiku-20240307",
) -> float:
    """
    Ask an LLM to estimate the game state value from MAX's perspective.

    Returns a float in [-100, 100].
    On any error returns 0.0 (neutral) — pure heuristic takes over.

    This mirrors the 'value head' in AlphaZero:
      - AlphaZero:  neural net outputs a scalar in [-1, 1]
      - Our system: LLM outputs a paragraph, we parse a scalar from it
    """
    if not api_key:
        return 0.0

    node_label  = NODES.get(node_id,  {}).get("label", node_id)
    goal_label  = NODES.get(goal,     {}).get("label", goal)
    floor_curr  = NODES.get(node_id,  {}).get("floor", 0)
    floor_goal  = NODES.get(goal,     {}).get("floor", 0)
    floors_away = abs(floor_curr - floor_goal)
    agent       = "Ambulance (MAX)" if is_max else "Congestion Controller (MIN)"

    prompt = f"""You are evaluating a hospital triage routing game state.

Game: An ambulance team (MAX) tries to reach the ICU as fast as possible.
      A congestion controller (MIN) tries to block corridors to slow them.

Current state:
  - Current location : {node_label} (Floor {floor_curr})
  - Goal             : {goal_label} (Floor {floor_goal})
  - Floors remaining : {floors_away}
  - Travel cost so far: {travel_cost:.0f} seconds
  - Corridor congestion: {congestion}/3  (0=clear, 3=fully blocked)
  - Active agent     : {agent}

Score this position from MAX (ambulance) perspective.
Reply with ONLY a single integer between -100 and 100.
  100 = ambulance is definitely reaching ICU quickly
 -100 = corridor is completely blocked, no hope
   0  = neutral, uncertain

Single integer only:"""

    try:
        if provider == "gemini":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            m = genai.GenerativeModel(model)
            r = m.generate_content(prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=10, temperature=0.0))
            raw = r.text.strip()
        else:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key)
            msg = client.messages.create(
                model=model, max_tokens=10,
                messages=[{"role": "user", "content": prompt}])
            raw = msg.content[0].text.strip()

        # Extract first integer from the response
        import re
        nums = re.findall(r"-?\d+", raw)
        if nums:
            val = int(nums[0])
            return max(-100.0, min(100.0, float(val)))
    except Exception:
        pass

    return 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MCTS Core
# ─────────────────────────────────────────────────────────────────────────────

class MCTS:
    """
    Monte Carlo Tree Search with:
      - Bayes-guided expansion (policy prior)
      - LLM or heuristic leaf evaluation (value function)
      - Adversarial MAX/MIN alternation
    """

    def __init__(
        self,
        G,
        goal: str,
        sensor_readings: dict[str, str] = None,
        time_of_day: Optional[str] = None,
        num_simulations: int = DEFAULT_SIMS,
        depth_limit: int = 6,
        api_key: str = "",
        provider: str = "claude",
        model: str = "claude-3-haiku-20240307",
        use_llm_value: bool = False,
    ):
        self.G               = G
        self.goal            = goal
        self.sensor_readings = sensor_readings or {}
        self.time_of_day     = time_of_day
        self.num_simulations = num_simulations
        self.depth_limit     = depth_limit
        self.api_key         = api_key
        self.provider        = provider
        self.model           = model
        self.use_llm_value   = use_llm_value and bool(api_key)

        # Telemetry
        self.llm_calls     = 0
        self.prune_events  = 0   # UCB naturally prunes; count low-visit branches
        self.total_rollouts= 0

    # ── Selection ────────────────────────────────────────────────────────────

    def _select(self, node: MCTSNode) -> MCTSNode:
        """
        Traverse tree from root using UCB1 until we reach a leaf
        (unexpanded node or terminal).

        O(depth) per call.
        """
        while node.children:
            if not node.is_fully_expanded(self.G):
                return node   # expand this node next
            node = node.best_child()
        return node

    # ── Expansion ────────────────────────────────────────────────────────────

    def _expand(self, node: MCTSNode) -> MCTSNode:
        """
        Add one new child to `node` using Bayes prior to weight edges.

        For MAX turn: expand a neighbor not yet in children
        For MIN turn: expand a congestion-increase action

        O(degree(node)) for prior computation.
        """
        existing = {c.state for c in node.children}
        successors = get_successors(self.G, node.node_id, node.congestion, node.is_max)

        for next_node, next_cong, edge_cost, desc in successors:
            new_state = (next_node, next_cong, node.travel_cost + edge_cost, not node.is_max)
            if new_state in existing:
                continue

            # Bayes prior: P(next corridor is clear)
            prior = bayes_prior(next_node, self.sensor_readings, self.time_of_day)

            child = MCTSNode(
                state      = new_state,
                parent     = node,
                prior      = prior,
                action_desc= desc,
            )
            node.children.append(child)
            return child

        # All successors already expanded — return a random existing child
        return random.choice(node.children) if node.children else node

    # ── Simulation (Rollout) ──────────────────────────────────────────────────

    def _simulate(self, node: MCTSNode) -> float:
        """
        Estimate the value of `node` from MAX's perspective.

        Strategy:
          1. If LLM value enabled AND at depth limit → call LLM (AlphaZero value head)
          2. Otherwise → random rollout for ROLLOUT_DEPTH steps + heuristic eval
          3. Goal reached → large positive reward
          4. MAX's heuristic eval = -(cost + h(node,goal)) * (1 + congestion*0.4)

        O(ROLLOUT_DEPTH * branching) for rollout
        O(API latency) for LLM call
        """
        self.total_rollouts += 1

        # Terminal: goal reached
        if node.node_id == self.goal:
            return 200.0 - node.travel_cost

        # Use LLM as value function (AlphaZero value head)
        if self.use_llm_value:
            self.llm_calls += 1
            llm_val = _llm_value(
                node.node_id, self.goal, node.congestion, node.travel_cost,
                node.is_max, self.api_key, self.provider, self.model,
            )
            if llm_val != 0.0:
                return llm_val

        # Heuristic rollout (fast fallback)
        curr_node   = node.node_id
        congestion  = node.congestion
        travel_cost = node.travel_cost
        is_max      = node.is_max

        for _ in range(ROLLOUT_DEPTH):
            if curr_node == self.goal:
                return 200.0 - travel_cost

            succs = get_successors(self.G, curr_node, congestion, is_max)
            if not succs:
                break

            # Bias random rollout with Bayes prior (light policy)
            weights = [
                bayes_prior(s[0], self.sensor_readings, self.time_of_day)
                for s in succs
            ]
            total_w = sum(weights)
            probs   = [w / total_w for w in weights] if total_w > 0 else None
            chosen  = random.choices(succs, weights=probs, k=1)[0]

            curr_node, congestion, edge_cost, _ = chosen
            travel_cost += edge_cost
            is_max = not is_max

        return evaluate(curr_node, self.goal, congestion, travel_cost)

    # ── Backpropagation ───────────────────────────────────────────────────────

    def _backprop(self, node: MCTSNode, value: float) -> None:
        """
        Propagate value up to root.
        Value is always stored from MAX's perspective.

        O(depth) per call.
        """
        while node is not None:
            node.visits    += 1
            node.value_sum += value
            node = node.parent

    # ── Main Loop ────────────────────────────────────────────────────────────

    def run(self, start: str) -> dict:
        """
        Run MCTS from `start` toward `self.goal`.

        Returns a result dict compatible with the existing game module format.
        """
        root = MCTSNode(
            state      = (start, 0, 0.0, True),
            prior      = 1.0,
            action_desc= f"START: {start}",
        )

        iteration_log = []

        for i in range(self.num_simulations):
            # 1. Selection
            leaf = self._select(root)

            # 2. Expansion (if not terminal)
            if leaf.node_id != self.goal and leaf.visits > 0:
                leaf = self._expand(leaf)

            # 3. Simulation
            value = self._simulate(leaf)

            # 4. Backpropagation
            self._backprop(leaf, value)

            # Log every 20 iterations for the UI trace
            if i % 20 == 0 or i == self.num_simulations - 1:
                best_child = max(root.children, key=lambda c: c.visits) if root.children else None
                iteration_log.append({
                    "iteration"  : i + 1,
                    "root_visits": root.visits,
                    "best_node"  : best_child.node_id if best_child else start,
                    "best_Q"     : round(best_child.Q, 2) if best_child else 0.0,
                    "best_visits": best_child.visits if best_child else 0,
                    "llm_calls"  : self.llm_calls,
                    "note"       : (
                        f"Iter {i+1}: root.N={root.visits} | "
                        f"best={best_child.node_id if best_child else '?'} "
                        f"Q={f'{best_child.Q:.1f}' if best_child else '?'} "
                        f"N={best_child.visits if best_child else 0}"
                    ),
                })

        # ── Extract best path by greedy most-visited child ────────────────────
        path        = [start]
        curr        = root
        visited_ids = {start}
        path_cost   = 0.0
        depth       = 0

        while curr.children and depth < self.depth_limit * 2:
            depth += 1
            # AlphaZero policy: pick most-visited child (robust, less noisy than max Q)
            best = max(curr.children, key=lambda c: c.visits)
            if best.node_id in visited_ids:
                break
            path.append(best.node_id)
            visited_ids.add(best.node_id)
            path_cost = best.travel_cost
            curr = best
            if best.node_id == self.goal:
                break

        # ── Build children summary for UI ─────────────────────────────────────
        children_summary = []
        for c in sorted(root.children, key=lambda x: -x.visits)[:10]:
            children_summary.append({
                "node"      : c.node_id,
                "action"    : c.action_desc,
                "visits"    : c.visits,
                "Q"         : round(c.Q, 2),
                "prior"     : round(c.prior, 3),
                "ucb"       : round(c.ucb_score(), 2) if c.visits > 0 else 999,
            })

        # Count low-visit branches (proxy for implicit pruning)
        all_children = root.children
        low_visit    = sum(1 for c in all_children if c.visits <= 2)

        return {
            "algorithm"     : "MCTS+Bayes+LLM" if self.use_llm_value else "MCTS+Bayes",
            "start"         : start,
            "goal"          : self.goal,
            "path"          : path,
            "cost"          : round(path_cost, 1),
            "root_visits"   : root.visits,
            "iteration_log" : iteration_log,
            "children_summary": children_summary,
            "stats": {
                "num_simulations" : self.num_simulations,
                "depth_limit"     : self.depth_limit,
                "llm_calls"       : self.llm_calls,
                "total_rollouts"  : self.total_rollouts,
                "root_children"   : len(root.children),
                "low_visit_branches": low_visit,
                "use_llm_value"   : self.use_llm_value,
                "time_of_day"     : self.time_of_day,
            },
            "explanation": (
                f"MCTS ran {self.num_simulations} simulations guided by Bayesian corridor priors. "
                f"Best path has {len(path)} hops, estimated cost {path_cost:.0f}s. "
                f"Root node visited {root.visits} times; "
                f"{low_visit} of {len(all_children)} branches had ≤2 visits "
                f"(naturally deprioritised — equivalent to alpha-beta pruning). "
                + (f"LLM value function called {self.llm_calls} times at leaf nodes. "
                   if self.use_llm_value else
                   "Heuristic eval used at leaf nodes (no LLM key provided). ")
                + f"Policy prior from Bayes: P(occupancy=low) per corridor edge."
            ),
            "alphazero_note": (
                "This mirrors AlphaZero's architecture: "
                "Bayes occupancy posterior acts as the *policy network* (which edges to explore), "
                "while the LLM acts as the *value network* (how good is this position). "
                "MCTS provides the search backbone, replacing exhaustive minimax."
            ),
        }


# ─────────────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_mcts_game(
    start: str = "ENTRANCE_MAIN",
    goal: str  = "Node_302_ICU_Tower",
    profile: str = "emergency",
    num_simulations: int = DEFAULT_SIMS,
    depth_limit: int = 6,
    time_of_day: Optional[str] = None,
    sensor_readings: Optional[dict] = None,
    api_key: str = "",
    provider: str = "claude",
    model: str = "claude-3-haiku-20240307",
    use_llm_value: bool = False,
    hospital: str = "charite",
) -> dict:
    """
    Unified entry point for the MCTS triage routing module.

    Parameters
    ----------
    start           : starting node ID
    goal            : goal node ID
    profile         : access profile for graph filtering
    num_simulations : MCTS iterations (more = better quality, slower)
    depth_limit     : max path depth in tree
    time_of_day     : 'morning'|'afternoon'|'evening'|'night' (for Bayes priors)
    sensor_readings : dict[node_id → 'clear'|'busy'|'jammed']
    api_key         : Claude / Gemini API key for LLM value function
    provider        : 'claude' | 'gemini'
    model           : LLM model string
    use_llm_value   : if True and api_key provided, call LLM at leaf nodes

    Returns a result dict with path, cost, traces, and AlphaZero-style annotations.
    """
    build_graph_fn, _, _ = _get_graph_fns(hospital)
    G = build_graph_fn(profile)

    if start not in G:
        return {"error": f"Start node '{start}' not in graph for profile '{profile}'"}
    if goal not in G:
        return {"error": f"Goal node '{goal}' not in graph for profile '{profile}'"}

    mcts = MCTS(
        G               = G,
        goal            = goal,
        sensor_readings = sensor_readings or {},
        time_of_day     = time_of_day,
        num_simulations = num_simulations,
        depth_limit     = depth_limit,
        api_key         = api_key,
        provider        = provider,
        model           = model,
        use_llm_value   = use_llm_value,
    )

    result = mcts.run(start)
    result["profile"] = profile
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Quick smoke test
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    result = run_mcts_game(
        start="ENTRANCE_MAIN",
        goal="Node_302_ICU_Tower",
        profile="emergency",
        num_simulations=100,
    )
    print(f"Algorithm  : {result['algorithm']}")
    print(f"Path       : {' → '.join(result['path'])}")
    print(f"Cost       : {result['cost']}s")
    print(f"Simulations: {result['stats']['num_simulations']}")
    print(f"LLM calls  : {result['stats']['llm_calls']}")
    print(f"\n{result['explanation']}")
    print(f"\n{result['alphazero_note']}")
