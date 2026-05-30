"""tests/test_bayes.py — Unit tests for CO5 Bayesian/HMM"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import numpy as np
from core.bayes import infer_occupancy, hmm_forward, adjust_path_cost

def test_posterior_sums_to_one():
    result = infer_occupancy("busy")
    total = sum(result["posterior"].values())
    assert abs(total - 1.0) < 1e-6

def test_jammed_sensor_implies_high_occupancy():
    result = infer_occupancy("jammed", "afternoon", "weekday")
    assert result["map_estimate"] == "high"

def test_clear_sensor_implies_low_occupancy():
    result = infer_occupancy("clear", "night", "weekday")
    assert result["map_estimate"] == "low"

def test_inference_returns_trace():
    result = infer_occupancy("busy", "morning")
    assert len(result["trace"]) >= 3

def test_hmm_belief_sums_to_one():
    result = hmm_forward(["clear", "busy", "jammed"])
    for belief in result["final_belief"].values():
        pass  # just accessing
    total = sum(result["final_belief"].values())
    assert abs(total - 1.0) < 1e-6

def test_hmm_returns_trace():
    result = hmm_forward(["clear", "busy"])
    assert len(result["trace"]) == 2

def test_hmm_jammed_sequence_high():
    result = hmm_forward(["jammed", "jammed", "jammed"])
    assert result["final_state"] == "high"

def test_adjust_path_cost():
    from core.search import run_search
    path = run_search("astar", "staff", "ENTRANCE_MAIN", "BH_Reception")["path"]
    sensors = {n: "busy" for n in path}
    result = adjust_path_cost(path, sensors)
    assert result["total_adjusted_cost"] >= result["total_base_cost"]
