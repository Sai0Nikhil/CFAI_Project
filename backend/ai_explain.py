"""
backend/ai_explain.py
Claude / Gemini explanation engine for all 6 AI modules.
Called by /api/ai/explain in main.py
"""
from __future__ import annotations
import json
from typing import Any

# ── Prompt builders per module ────────────────────────────────────────────────

def build_prompt(module: str, ctx: dict) -> str:
    """Return a focused prompt for Claude/Gemini based on the module and context."""

    base = (
        "You are an AI assistant helping explain a hospital AI navigation system "
        "built for an academic project (IIT Madras CFAI course covering CO1–CO6). "
        "Be concise, clear, and insightful. Max 4 sentences unless asked for more. "
        "Use plain English. Mention the specific algorithm/technique used.\n\n"
    )

    if module == "search":
        algo   = ctx.get("algorithm", "A*").upper()
        path   = ctx.get("path", [])
        cost   = ctx.get("cost", 0)
        hops   = len(path)
        start  = ctx.get("start", "").replace("_", " ")
        goal   = ctx.get("goal", "").replace("_", " ")
        exp    = ctx.get("expansions", "?")
        prof   = ctx.get("profile", "staff")
        return base + (
            f"The {algo} algorithm found a hospital path for a '{prof}' profile.\n"
            f"Start: {start} → Goal: {goal}\n"
            f"Path ({hops} hops): {' → '.join(p.replace('_',' ') for p in path)}\n"
            f"Travel time: {cost:.0f}s | Nodes expanded: {exp}\n\n"
            f"Explain: (1) why {algo} chose this path, (2) what the {exp} node expansions mean, "
            f"(3) whether this is optimal and why, (4) one practical insight for the patient."
        )

    if module == "compare":
        results = ctx.get("results", {})
        start   = ctx.get("start", "").replace("_", " ")
        goal    = ctx.get("goal", "").replace("_", " ")
        summary = []
        for alg, r in results.items():
            if r.get("path"):
                summary.append(f"{alg.upper()}: {len(r['path'])} hops, {r['cost']:.0f}s, {r['stats'].get('expansions','?')} expansions")
            else:
                summary.append(f"{alg.upper()}: No path found")
        return base + (
            f"Four search algorithms were compared on the same query: {start} → {goal}.\n"
            f"Results:\n" + "\n".join(f"  • {s}" for s in summary) + "\n\n"
            f"Explain: (1) why A* typically wins, (2) why DFS might find a suboptimal path, "
            f"(3) the trade-off between BFS and UCS, (4) what 'expansions' tells us about efficiency."
        )

    if module == "csp":
        profile  = ctx.get("profile", "visitor")
        valid    = ctx.get("overall_valid", False)
        path     = ctx.get("path", [])
        fails    = ctx.get("violations", 0)
        trace    = ctx.get("trace", [])
        fail_reasons = [t["reason"] for t in trace if t.get("result") == "FAIL"][:3]
        return base + (
            f"The CSP (Constraint Satisfaction Problem) system validated a hospital path "
            f"for profile: '{profile}'.\n"
            f"Path: {' → '.join(p.replace('_',' ') for p in path)}\n"
            f"Result: {'✅ VALID — all constraints satisfied' if valid else f'❌ INVALID — {fails} violation(s)'}\n"
            + (f"Violations: {'; '.join(fail_reasons)}\n" if fail_reasons else "") +
            f"\nExplain: (1) what CSP constraints mean in a hospital context, "
            f"(2) why '{profile}' profile has these restrictions, "
            f"(3) what backtracking + AC-3 did to find this, "
            f"(4) a real-world implication of these access rules."
        )

    if module == "game":
        path    = ctx.get("best_path", [])
        cost    = ctx.get("best_cost", 0)
        depth   = ctx.get("depth", 3)
        pruned  = ctx.get("pruned_branches", 0)
        nodes   = ctx.get("nodes_evaluated", 0)
        ab      = ctx.get("alpha_beta", True)
        return base + (
            f"Minimax game AI ran triage routing as a two-player zero-sum game.\n"
            f"MAX (ambulance) vs MIN (congestion controller) — depth {depth}.\n"
            f"Best path: {' → '.join(p.replace('_',' ') for p in path)}\n"
            f"Cost: {cost:.0f}s | Nodes evaluated: {nodes} | "
            f"{'Alpha-beta pruned ' + str(pruned) + ' branches' if ab else 'No pruning'}\n\n"
            f"Explain: (1) what MAX and MIN represent in hospital triage, "
            f"(2) what the evaluation function balances, "
            f"(3) why alpha-beta pruning saved {pruned} nodes, "
            f"(4) how this differs from simple A* routing."
        )

    if module == "bayesian":
        tab      = ctx.get("tab", "bayes")
        sensor   = ctx.get("sensor", "busy")
        posterior = ctx.get("posterior", {})
        map_est  = ctx.get("map_estimate", "medium")
        explanation = ctx.get("explanation", "")

        if tab == "hmm":
            obs   = ctx.get("observations", [])
            final = ctx.get("final_belief", {})
            return base + (
                f"HMM (Hidden Markov Model) forward algorithm tracked corridor occupancy.\n"
                f"Observations: {' → '.join(obs)}\n"
                f"Final belief state: {json.dumps(final)}\n\n"
                f"Explain: (1) what hidden states and observations mean here, "
                f"(2) how the forward algorithm updates belief at each step, "
                f"(3) what this final distribution means for routing, "
                f"(4) why sensor fusion improves over simple threshold rules."
            )
        elif tab == "route":
            base_cost = ctx.get("total_base_cost", 0)
            adj_cost  = ctx.get("total_adjusted_cost", 0)
            return base + (
                f"Uncertainty-aware routing adjusted A* path costs using Bayesian sensor readings.\n"
                f"Base A* cost: {base_cost}s → Congestion-adjusted: {adj_cost:.0f}s "
                f"(+{adj_cost-base_cost:.1f}s overhead)\n\n"
                f"Explain: (1) how corridor occupancy probability adjusts edge weights, "
                f"(2) what congestion factors ×1.0/×1.4/×2.0 mean, "
                f"(3) why integrating Bayesian inference with A* is powerful, "
                f"(4) a real hospital scenario where this matters."
            )
        else:
            prob_str = ", ".join(f"{k}: {v:.0%}" for k,v in posterior.items())
            return base + (
                f"Bayesian Network computed corridor occupancy given sensor reading: '{sensor}'.\n"
                f"P(Occupancy | sensor='{sensor}'): {prob_str}\n"
                f"MAP estimate: {map_est}\n\n"
                f"Explain: (1) the Bayesian network structure (TimeOfDay→Occupancy←DayType→Sensor), "
                f"(2) what variable elimination computed here, "
                f"(3) what MAP estimate '{map_est}' means for routing, "
                f"(4) why this probabilistic approach beats hard-coded rules."
            )

    if module == "nlp":
        query    = ctx.get("query", "")
        lang     = ctx.get("language", "en")
        dest     = ctx.get("target_friendly", "Unknown")
        node     = ctx.get("target_node", "")
        urgency  = ctx.get("urgency_level", "NORMAL")
        keywords = ctx.get("matched_keywords", [])
        return base + (
            f"NLP pipeline processed a hospital navigation query.\n"
            f"Query: \"{query}\"\n"
            f"Detected language: {lang} | Destination: {dest} ({node})\n"
            f"Urgency: {urgency} | Matched keywords: {', '.join(keywords[:5])}\n\n"
            f"Explain: (1) how language detection works without an API, "
            f"(2) why this query maps to '{dest}', "
            f"(3) whether the urgency level '{urgency}' is appropriate for this symptom, "
            f"(4) what the routing hint should be for this case."
        )

    if module == "mcts":
        algo        = ctx.get("algorithm", "MCTS+Bayes")
        path        = ctx.get("path", [])
        cost        = ctx.get("cost", 0)
        sims        = ctx.get("num_simulations", 200)
        llm_calls   = ctx.get("llm_calls", 0)
        root_visits = ctx.get("root_visits", 0)
        low_visit   = ctx.get("low_visit_branches", 0)
        total_ch    = ctx.get("root_children", 0)
        use_llm     = ctx.get("use_llm_value", False)
        return base + (
            f"MCTS (AlphaZero-style) triage routing ran {sims} simulations.\n"
            f"Algorithm: {algo} | Path: {' → '.join(p.replace('_',' ') for p in path)}\n"
            f"Estimated cost: {cost:.0f}s | Root node visits: {root_visits}\n"
            f"Branches naturally deprioritised (≤2 visits): {low_visit}/{total_ch}\n"
            + (f"LLM value calls at leaf nodes: {llm_calls}\n" if use_llm else "") +
            f"\nExplain: (1) how Bayesian priors replace the AlphaZero policy network here, "
            f"(2) what UCB1 balances (exploitation vs exploration), "
            f"(3) why {low_visit} branches got few visits (emergent pruning), "
            f"(4) how this differs from the fixed-depth minimax approach and when each is better."
        )

    if module == "navigate":
        query  = ctx.get("query", "")
        dest   = ctx.get("destination", "")
        path   = ctx.get("path", [])
        cost   = ctx.get("cost", 0)
        urgency = ctx.get("urgency", "NORMAL")
        user_loc = ctx.get("user_location", "Main Entrance").replace("_", " ")
        return base + (
            f"A patient used the Smart Navigation system.\n"
            f"They said: \"{query}\"\n"
            f"AI identified: {dest} | Urgency: {urgency}\n"
            f"Route from {user_loc}: {' → '.join(p.replace('_',' ') for p in path)} ({cost:.0f}s)\n\n"
            f"Give the patient: (1) a plain-English confirmation of their destination, "
            f"(2) step-by-step directions in simple language (elevator/stairs/corridor), "
            f"(3) what to say when they arrive, "
            f"(4) any urgency advice if needed."
        )

    return base + f"Explain the following hospital AI result:\n{json.dumps(ctx, indent=2)}"


# ── LLM caller ───────────────────────────────────────────────────────────────

async def call_claude(prompt: str, api_key: str, model: str) -> str:
    """Call Anthropic Claude API."""
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model=model,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except ImportError:
        raise RuntimeError("anthropic package not installed. Run: pip install anthropic")
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}")


async def call_gemini(prompt: str, api_key: str, model: str) -> str:
    """Call Google Gemini API."""
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        m = genai.GenerativeModel(model)
        r = m.generate_content(prompt)
        return r.text.strip()
    except ImportError:
        raise RuntimeError("google-generativeai package not installed. Run: pip install google-generativeai")
    except Exception as e:
        raise RuntimeError(f"Gemini API error: {e}")


async def explain(module: str, ctx: dict, provider: str, api_key: str, model: str) -> dict:
    """Main entry — build prompt, call LLM, return structured response."""
    prompt = build_prompt(module, ctx)
    if provider == "gemini":
        text = await call_gemini(prompt, api_key, model)
    else:
        text = await call_claude(prompt, api_key, model)

    # Split into sentences for structured display
    sentences = [s.strip() for s in text.replace("\n", " ").split(". ") if s.strip()]
    return {
        "explanation": text,
        "sentences": sentences,
        "module": module,
        "provider": provider,
        "model": model,
    }
