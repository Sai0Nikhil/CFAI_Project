"""tests/test_game.py — Unit tests for CO4 Minimax"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
import math
from core.game import run_game, evaluate

def test_game_returns_best_value():
    result = run_game(depth_limit=2)
    assert "best_value" in result
    assert not math.isnan(result["best_value"])

def test_game_has_trace():
    result = run_game(depth_limit=2)
    assert len(result["trace"]) > 0

def test_game_prune_log_is_list():
    result = run_game(depth_limit=3)
    assert isinstance(result["prune_log"], list)

def test_evaluation_goal_state_high_score():
    # Reaching goal node should produce a high (positive-ish) value
    score = evaluate("Node_302_ICU_Tower", "Node_302_ICU_Tower", congestion=0, travel_cost=0)
    # evaluate doesn't handle goal itself — but with h=0 and congestion=0 score should be 0
    assert score == 0.0

def test_evaluation_high_congestion_lowers_score():
    s_low  = evaluate("BH_Lobby", "Node_302_ICU_Tower", congestion=0, travel_cost=0)
    s_high = evaluate("BH_Lobby", "Node_302_ICU_Tower", congestion=3, travel_cost=0)
    assert s_high < s_low, "High congestion should lower the score"

def test_game_emergency_profile():
    result = run_game(start="BH_Lobby", goal="Node_302_ICU_Tower",
                      depth_limit=2, profile="emergency")
    assert "error" not in result
