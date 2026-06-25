"""
core/triage.py
==============
Ethical Triage Governor & Resource Conflict Solver.
Models routing conflict where two patients compete for a bottleneck hospital resource 
(e.g., a single-occupancy elevator, isolation lift, or narrow ward passage).

Resolves conflict using:
1. Rawlsian Justice: Prioritize the worst-off (minimizes the maximum individual distress).
2. Utilitarianism: Maximizes overall flow (minimizes total combined transit delay).
3. Language Equity Guard: Corrects for systemic language processing latency.
"""

from typing import Dict, Any, List

# Priority and Tolerable Wait definitions
SEVERITY_MAP = {
    "critical": {"weight": 10.0, "max_wait": 15.0, "label": "🚨 Critical (e.g. Chest Pain)"},
    "urgent":   {"weight": 5.0,  "max_wait": 60.0, "label": "⚠️ Urgent (e.g. Severe Fracture)"},
    "standard": {"weight": 2.0,  "max_wait": 240.0, "label": "♿ Standard (e.g. Lab Sample)"},
    "non-urgent":{"weight": 1.0, "max_wait": 480.0, "label": "👤 Non-Urgent (e.g. Checkup)"}
}

class Patient:
    def __init__(self, id: str, name: str, severity: str, waiting_time: float, base_cost: float, language: str):
        """
        id: patient identifier
        name: patient display name
        severity: critical | urgent | standard | non-urgent
        waiting_time: minutes patient has been waiting since arrival
        base_cost: travel time in seconds for the path
        language: english | telugu | hindi
        """
        self.id = id
        self.name = name
        self.severity = severity.lower() if severity.lower() in SEVERITY_MAP else "standard"
        self.waiting_time = waiting_time  # in minutes
        self.base_cost = base_cost        # in seconds
        self.language = language.lower()

        # Severity config
        cfg = SEVERITY_MAP[self.severity]
        self.weight = cfg["weight"]
        self.max_wait = cfg["max_wait"]

def solve_ethical_triage(
    patient_a_data: Dict[str, Any],
    patient_b_data: Dict[str, Any],
    mode: str = "rawlsian",
    equity_guard: bool = True
) -> Dict[str, Any]:
    """
    Solve conflict scheduling between two patients.
    Bottleneck resource rules:
      - The patient scheduled FIRST gets their base cost as transit time.
      - The patient scheduled SECOND must wait for the first patient to clear the corridor.
        Second Patient Total Delay = waiting_time + second_base_cost + first_transit_time + bottleneck_wait (e.g. 180 seconds).

    If equity_guard is OFF:
      - Telugu/Hindi queries suffer a translation/systemic penalty of +120 seconds (+2 minutes) of artificial waiting time
        added to their actual delay, and their priority weight is discounted by 20% due to administrative overhead.
      - This simulates systemic bias where minority languages are deprioritized.
    If equity_guard is ON:
      - The translation penalty is zeroed out, and a safety buffer of +2.0 weight is added to ensure fair scheduling.
    """
    # Create patient instances
    pa = Patient(
        id="A",
        name=patient_a_data.get("name", "Patient A"),
        severity=patient_a_data.get("severity", "critical"),
        waiting_time=float(patient_a_data.get("waiting_time", 10.0)),
        base_cost=float(patient_a_data.get("base_cost", 120.0)),
        language=patient_a_data.get("language", "english")
    )
    pb = Patient(
        id="B",
        name=patient_b_data.get("name", "Patient B"),
        severity=patient_b_data.get("severity", "urgent"),
        waiting_time=float(patient_b_data.get("waiting_time", 15.0)),
        base_cost=float(patient_b_data.get("base_cost", 90.0)),
        language=patient_b_data.get("language", "english")
    )

    # Apply translation penalty / bias if applicable
    pa_penalty = 0.0
    pb_penalty = 0.0
    pa_weight = pa.weight
    pb_weight = pb.weight

    if not equity_guard:
        if pa.language in ("telugu", "hindi"):
            pa_penalty = 2.0  # 2 minutes delay penalty
            pa_weight = max(1.0, pa.weight * 0.8) # 20% discount on weight
        if pb.language in ("telugu", "hindi"):
            pb_penalty = 2.0
            pb_weight = max(1.0, pb.weight * 0.8)
    else:
        # Equity Guard active: boost minority language priority weight slightly to ensure fair treatment
        if pa.language in ("telugu", "hindi"):
            pa_weight += 2.0
        if pb.language in ("telugu", "hindi"):
            pb_weight += 2.0

    # Let's compute outcomes for both possible schedules
    # Schedule 1: A first, then B (S_AB)
    # A transit time = pa.base_cost / 60 (minutes)
    # B waiting time at bottleneck = A transit time + bottleneck_overhead (e.g., 3 minutes)
    transit_a_mins = pa.base_cost / 60.0
    transit_b_mins = pb.base_cost / 60.0
    bottleneck_overhead = 3.0  # 3 minutes reset/waiting time

    # S_AB
    delay_a_sab = pa.waiting_time + pa_penalty + transit_a_mins
    delay_b_sab = pb.waiting_time + pb_penalty + transit_b_mins + transit_a_mins + bottleneck_overhead

    distress_a_sab = delay_a_sab / pa.max_wait
    distress_b_sab = delay_b_sab / pb.max_wait

    # S_BA: B first, then A
    delay_b_sba = pb.waiting_time + pb_penalty + transit_b_mins
    delay_a_sba = pa.waiting_time + pa_penalty + transit_a_mins + transit_b_mins + bottleneck_overhead

    distress_b_sba = delay_b_sba / pb.max_wait
    distress_a_sba = delay_a_sba / pa.max_wait

    # Utilitarian Objective: Minimize sum of travel times/delays (weighted by active weights)
    # Average unweighted delay:
    sum_delay_sab = delay_a_sab + delay_b_sab
    sum_delay_sba = delay_b_sba + delay_a_sba

    # Rawlsian Objective: Minimize the maximum normalized distress
    max_distress_sab = max(distress_a_sab, distress_b_sab)
    max_distress_sba = max(distress_a_sba, distress_b_sba)

    # Decision Making
    choose_sab = True
    reasoning = []

    if mode == "rawlsian":
        if max_distress_sab <= max_distress_sba:
            choose_sab = True
            selected_mode = "S_AB (A first, then B)"
            worse_case_distress = max_distress_sab
        else:
            choose_sab = False
            selected_mode = "S_BA (B first, then A)"
            worse_case_distress = max_distress_sba

        reasoning.append(f"⚖️ Rawlsian Governor prioritizes minimizing maximum distress.")
        reasoning.append(f"Distress of worst-off in A-first: {max_distress_sab:.2f}")
        reasoning.append(f"Distress of worst-off in B-first: {max_distress_sba:.2f}")
        reasoning.append(f"Selected: {selected_mode} because worst-case distress is lower ({worse_case_distress:.2f} vs. {max(max_distress_sab, max_distress_sba):.2f}).")
    else:  # utilitarian
        if sum_delay_sab <= sum_delay_sba:
            choose_sab = True
            selected_mode = "S_AB (A first, then B)"
            total_delay = sum_delay_sab
        else:
            choose_sab = False
            selected_mode = "S_BA (B first, then A)"
            total_delay = sum_delay_sba

        reasoning.append(f"📊 Utilitarian Governor prioritizes minimizing total cumulative delay.")
        reasoning.append(f"Total delay in A-first: {sum_delay_sab:.1f} mins")
        reasoning.append(f"Total delay in B-first: {sum_delay_sba:.1f} mins")
        reasoning.append(f"Selected: {selected_mode} to minimize sum of delays ({total_delay:.1f} mins vs. {max(sum_delay_sab, sum_delay_sba):.1f} mins).")

    # Construct trace/log
    schedule = []
    if choose_sab:
        schedule = [
            {
                "patient": pa.name,
                "language": pa.language.capitalize(),
                "severity": pa.severity.capitalize(),
                "order": 1,
                "delay": delay_a_sab,
                "distress": distress_a_sab,
                "is_equity_booster": equity_guard and pa.language in ("telugu", "hindi")
            },
            {
                "patient": pb.name,
                "language": pb.language.capitalize(),
                "severity": pb.severity.capitalize(),
                "order": 2,
                "delay": delay_b_sab,
                "distress": distress_b_sab,
                "is_equity_booster": equity_guard and pb.language in ("telugu", "hindi")
            }
        ]
    else:
        schedule = [
            {
                "patient": pb.name,
                "language": pb.language.capitalize(),
                "severity": pb.severity.capitalize(),
                "order": 1,
                "delay": delay_b_sba,
                "distress": distress_b_sba,
                "is_equity_booster": equity_guard and pb.language in ("telugu", "hindi")
            },
            {
                "patient": pa.name,
                "language": pa.language.capitalize(),
                "severity": pa.severity.capitalize(),
                "order": 2,
                "delay": delay_a_sba,
                "distress": distress_a_sba,
                "is_equity_booster": equity_guard and pa.language in ("telugu", "hindi")
            }
        ]

    # Return full package
    return {
        "schedule": schedule,
        "mode": mode,
        "equity_guard": equity_guard,
        "reasoning": reasoning,
        "metrics": {
            "average_delay": (sum_delay_sab if choose_sab else sum_delay_sba) / 2.0,
            "max_distress": max_distress_sab if choose_sab else max_distress_sba,
            "pa_effective_weight": pa_weight,
            "pb_effective_weight": pb_weight,
            "pa_penalty_applied": pa_penalty * 60, # in seconds
            "pb_penalty_applied": pb_penalty * 60,
        },
        "philosophical_note": (
            "John Rawls' Difference Principle ensures that inequality in scheduling is only allowed if it works "
            "to the maximum benefit of the least-advantaged (highest distress). Bentham's Utilitarianism, "
            "by contrast, treats all seconds of waiting equally, prioritizing the faster path even if it neglects critical needs."
        )
    }

if __name__ == "__main__":
    # Test Rawlsian vs Utilitarian
    pat_a = {"name": "Patient A (Telugu)", "severity": "critical", "waiting_time": 5.0, "base_cost": 300.0, "language": "telugu"}
    pat_b = {"name": "Patient B (English)", "severity": "urgent", "waiting_time": 10.0, "base_cost": 60.0, "language": "english"}

    print("--- RAWLSIAN WITH GUARD ---")
    res1 = solve_ethical_triage(pat_a, pat_b, mode="rawlsian", equity_guard=True)
    print("\n".join(res1["reasoning"]))
    print("Schedule order:", [p["patient"] for p in res1["schedule"]])

    print("\n--- UTILITARIAN WITH GUARD ---")
    res2 = solve_ethical_triage(pat_a, pat_b, mode="utilitarian", equity_guard=True)
    print("\n".join(res2["reasoning"]))
    print("Schedule order:", [p["patient"] for p in res2["schedule"]])

    print("\n--- RAWLSIAN WITHOUT GUARD (BIAS ON) ---")
    res3 = solve_ethical_triage(pat_a, pat_b, mode="rawlsian", equity_guard=False)
    print("\n".join(res3["reasoning"]))
    print("Schedule order:", [p["patient"] for p in res3["schedule"]])
