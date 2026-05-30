"""
core/bayes.py
=============
CO5 — Probabilistic Reasoning: Bayesian Network + HMM
      for Hospital Corridor Occupancy Estimation

BAYESIAN NETWORK
----------------
Variables:
  TimeOfDay   : {morning, afternoon, evening, night}
  DayType     : {weekday, weekend}
  Occupancy   : {low, medium, high}  ← the hidden state we want
  SensorReads : {clear, busy, jammed}  ← noisy sensor observation

Structure:
  TimeOfDay ──┐
              ├──► Occupancy ──► SensorReads
  DayType   ──┘

Inference: P(Occupancy | SensorReads, TimeOfDay, DayType)
           via Variable Elimination (CO5 requirement)

HMM
---
Hidden states : {low, medium, high}  — corridor occupancy
Observations  : {clear, busy, jammed}
Transition    : occupancy changes over time steps
Emission      : sensor reading given true occupancy

Forward algorithm computes P(state_t | obs_1:t).

Complexity:
  Variable Elimination : O(n * d^w)  n=vars, d=domain, w=treewidth
  HMM forward pass     : O(T * S^2)  T=time steps, S=states
"""

from __future__ import annotations
import numpy as np
from typing import Optional

# ────────────────────────────────────────────────────────────────────────────
# Discrete domain maps
# ────────────────────────────────────────────────────────────────────────────

TIME_OF_DAY = ["morning", "afternoon", "evening", "night"]   # 0..3
DAY_TYPE    = ["weekday", "weekend"]                          # 0..1
OCCUPANCY   = ["low", "medium", "high"]                      # 0..2
SENSOR      = ["clear", "busy", "jammed"]                    # 0..2

# ────────────────────────────────────────────────────────────────────────────
# CPTs (Conditional Probability Tables)
# ────────────────────────────────────────────────────────────────────────────

# P(Occupancy | TimeOfDay, DayType)
# Shape: [time(4), day(2), occupancy(3)]
CPT_OCCUPANCY = np.array([
    # morning
    [[0.5, 0.35, 0.15], [0.6, 0.30, 0.10]],  # weekday, weekend
    # afternoon
    [[0.2, 0.40, 0.40], [0.4, 0.40, 0.20]],
    # evening
    [[0.3, 0.45, 0.25], [0.5, 0.35, 0.15]],
    # night
    [[0.8, 0.15, 0.05], [0.85, 0.12, 0.03]],
])  # each row sums to 1

# P(SensorReads | Occupancy)
# Shape: [occupancy(3), sensor(3)]
CPT_SENSOR = np.array([
    # low occupancy
    [0.80, 0.15, 0.05],
    # medium occupancy
    [0.20, 0.60, 0.20],
    # high occupancy
    [0.05, 0.25, 0.70],
])

# Prior over TimeOfDay (uniform for demo)
PRIOR_TIME = np.array([0.25, 0.25, 0.25, 0.25])

# Prior over DayType
PRIOR_DAY = np.array([5/7, 2/7])  # weekday more likely


# ────────────────────────────────────────────────────────────────────────────
# Variable Elimination inference
# ────────────────────────────────────────────────────────────────────────────

def infer_occupancy(
    sensor_obs: str,
    time_of_day: Optional[str] = None,
    day_type: Optional[str] = None,
) -> dict:
    """
    Compute P(Occupancy | sensor_obs, time_of_day, day_type)
    via Variable Elimination (marginalise over unknown variables).

    If time_of_day or day_type is None, marginalise over that variable.

    Complexity: O(n * d^w) ≈ O(4 * 2 * 3) per elimination step

    Returns posterior distribution + step-by-step belief update log.
    """
    s_idx = SENSOR.index(sensor_obs)
    trace = []
    step = 0

    # Step 1: Factor over TimeOfDay
    if time_of_day is not None:
        t_idx = TIME_OF_DAY.index(time_of_day)
        f_time = np.zeros((1, 3))  # [1, occupancy]
        for d in range(2):
            f_time[0] += CPT_OCCUPANCY[t_idx, d] * PRIOR_DAY[d]
        step += 1
        trace.append({
            "step": step,
            "operation": "Factor(TimeOfDay=fixed)",
            "prior": f"P(TimeOfDay={time_of_day})=1.0",
            "result": {o: round(float(f_time[0, i]), 3) for i, o in enumerate(OCCUPANCY)},
            "note": f"Fixed time={time_of_day}; marginalised over DayType",
        })
    else:
        # Marginalise over all times and days
        f_time = np.zeros(3)  # [occupancy]
        for t in range(4):
            for d in range(2):
                f_time += CPT_OCCUPANCY[t, d] * PRIOR_TIME[t] * PRIOR_DAY[d]
        step += 1
        trace.append({
            "step": step,
            "operation": "Marginalise(TimeOfDay, DayType)",
            "result": {o: round(float(f_time[i]), 3) for i, o in enumerate(OCCUPANCY)},
            "note": "Summed out TimeOfDay and DayType → prior over Occupancy",
        })
        f_time = f_time.reshape(1, 3)

    # Flatten to [occupancy]
    prior_occ = f_time.flatten()

    step += 1
    trace.append({
        "step": step,
        "operation": "Prior P(Occupancy)",
        "result": {o: round(float(prior_occ[i]), 3) for i, o in enumerate(OCCUPANCY)},
        "note": "Prior occupancy distribution before observing sensor",
    })

    # Step 2: Likelihood factor P(sensor | occupancy)
    likelihood = CPT_SENSOR[:, s_idx]  # [occupancy]
    step += 1
    trace.append({
        "step": step,
        "operation": f"Likelihood P(sensor={sensor_obs} | Occupancy)",
        "result": {o: round(float(likelihood[i]), 3) for i, o in enumerate(OCCUPANCY)},
        "note": f"How likely is '{sensor_obs}' given each occupancy level",
    })

    # Step 3: Bayes update  P(occ | sensor) ∝ P(sensor | occ) * P(occ)
    unnorm = likelihood * prior_occ
    posterior = unnorm / unnorm.sum()
    step += 1
    trace.append({
        "step": step,
        "operation": "Posterior = Likelihood × Prior (normalised)",
        "result": {o: round(float(posterior[i]), 3) for i, o in enumerate(OCCUPANCY)},
        "note": "Bayes rule applied — this is the updated belief",
    })

    best_state = OCCUPANCY[int(np.argmax(posterior))]
    return {
        "sensor_obs": sensor_obs,
        "time_of_day": time_of_day,
        "day_type": day_type,
        "posterior": {o: round(float(posterior[i]), 4) for i, o in enumerate(OCCUPANCY)},
        "map_estimate": best_state,
        "trace": trace,
        "explanation": (
            f"Given sensor reads '{sensor_obs}', most likely occupancy is "
            f"'{best_state}' (P={round(float(posterior[OCCUPANCY.index(best_state)]),3)}). "
            f"This estimate uses {step} variable elimination steps."
        ),
    }


# ────────────────────────────────────────────────────────────────────────────
# HMM — Forward Algorithm for patient movement tracking
# ────────────────────────────────────────────────────────────────────────────

# HMM parameters
HMM_STATES = OCCUPANCY  # {low, medium, high}
HMM_OBS    = SENSOR     # {clear, busy, jammed}

# Transition matrix A[i,j] = P(state_t=j | state_{t-1}=i)
HMM_A = np.array([
    [0.70, 0.25, 0.05],  # low → ...
    [0.20, 0.60, 0.20],  # medium → ...
    [0.05, 0.35, 0.60],  # high → ...
])

# Emission matrix B[i,j] = P(obs=j | state=i)  (same as CPT_SENSOR)
HMM_B = CPT_SENSOR.copy()

# Initial state distribution
HMM_PI = np.array([0.50, 0.35, 0.15])


def hmm_forward(observations: list[str]) -> dict:
    """
    HMM Forward Algorithm.
    Computes P(state_t | obs_1, ..., obs_t) for each time step.

    Complexity: O(T * S^2)  T=len(observations), S=len(HMM_STATES)

    Returns alpha matrix + step-by-step belief update log.
    """
    T = len(observations)
    S = len(HMM_STATES)
    alpha = np.zeros((T, S))
    trace = []

    # Initialisation
    obs_idx = HMM_OBS.index(observations[0])
    alpha[0] = HMM_PI * HMM_B[:, obs_idx]
    alpha[0] /= alpha[0].sum()  # normalise for numerical stability
    trace.append({
        "t": 0,
        "observation": observations[0],
        "belief": {s: round(float(alpha[0, i]), 3) for i, s in enumerate(HMM_STATES)},
        "note": f"t=0 | obs='{observations[0]}' | init belief = π × B[obs]",
    })

    # Recursion
    for t in range(1, T):
        obs_idx = HMM_OBS.index(observations[t])
        # alpha[t, j] = B[j, obs] * sum_i(alpha[t-1, i] * A[i, j])
        for j in range(S):
            alpha[t, j] = HMM_B[j, obs_idx] * np.dot(alpha[t-1], HMM_A[:, j])
        alpha[t] /= alpha[t].sum()  # normalise
        best = HMM_STATES[int(np.argmax(alpha[t]))]
        trace.append({
            "t": t,
            "observation": observations[t],
            "belief": {s: round(float(alpha[t, i]), 3) for i, s in enumerate(HMM_STATES)},
            "map_state": best,
            "note": (
                f"t={t} | obs='{observations[t]}' | "
                f"belief update: α[t] = B[obs] × (A^T · α[t-1]) → normalise"
            ),
        })

    final_belief = {s: round(float(alpha[-1, i]), 3) for i, s in enumerate(HMM_STATES)}
    final_state  = HMM_STATES[int(np.argmax(alpha[-1]))]

    return {
        "observations": observations,
        "alpha": alpha.tolist(),
        "trace": trace,
        "final_belief": final_belief,
        "final_state": final_state,
        "explanation": (
            f"After {T} sensor readings {observations}, the HMM estimates "
            f"corridor occupancy is most likely '{final_state}' "
            f"(P={final_belief[final_state]}). "
            f"The forward algorithm complexity is O(T×S²) = O({T}×{S}²)."
        ),
    }


# ────────────────────────────────────────────────────────────────────────────
# Uncertainty-aware path cost adjustment
# ────────────────────────────────────────────────────────────────────────────

def adjust_path_cost(path: list[str], sensor_readings: dict[str, str]) -> dict:
    """
    Given sensor readings per node, adjust edge costs using occupancy posteriors.
    High occupancy → multiply edge weight by congestion factor.

    Congestion factors: low=1.0, medium=1.4, high=2.0

    O(path_length * inference_cost)
    """
    FACTOR = {"low": 1.0, "medium": 1.4, "high": 2.0}
    import importlib
    from core.hospital_graph import build_graph
    G = build_graph("staff")

    adjusted = []
    total_base = 0
    total_adjusted = 0

    for i in range(len(path) - 1):
        u, v = path[i], path[i+1]
        base_w = G[u][v]["weight"] if G.has_edge(u, v) else 0
        obs = sensor_readings.get(u, "clear")
        infer = infer_occupancy(obs)
        occ = infer["map_estimate"]
        factor = FACTOR[occ]
        adj_w = base_w * factor
        total_base += base_w
        total_adjusted += adj_w
        adjusted.append({
            "edge": f"{u}→{v}",
            "base_cost": base_w,
            "sensor": obs,
            "estimated_occupancy": occ,
            "factor": factor,
            "adjusted_cost": round(adj_w, 1),
        })

    return {
        "path": path,
        "adjusted_edges": adjusted,
        "total_base_cost": total_base,
        "total_adjusted_cost": round(total_adjusted, 1),
        "explanation": (
            f"Base path cost: {total_base}s → "
            f"Uncertainty-adjusted cost: {round(total_adjusted, 1)}s "
            f"(accounting for observed congestion levels)"
        ),
    }


if __name__ == "__main__":
    print("=== Bayesian Inference ===")
    r = infer_occupancy("busy", "afternoon", "weekday")
    print(r["explanation"])
    for t in r["trace"]:
        print(f"  Step {t['step']}: {t['operation']} → {t['result']}")

    print("\n=== HMM Forward ===")
    obs_seq = ["clear", "busy", "busy", "jammed"]
    r2 = hmm_forward(obs_seq)
    print(r2["explanation"])
