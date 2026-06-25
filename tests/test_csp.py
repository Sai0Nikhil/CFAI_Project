"""tests/test_csp.py — Unit tests for CO3 CSP"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from core.csp import validate_path_csp, find_valid_time_window, check_node_constraint, check_edge_constraint

def _staff_path():
    from core.search import run_search
    return run_search("astar", "staff", "ENTRANCE_MAIN", "Node_302_ICU_Tower")["path"]

def test_staff_path_valid():
    path = _staff_path()
    result = validate_path_csp(path, "staff")
    assert result["overall_valid"] is True

def test_visitor_path_invalid_for_icu():
    path = _staff_path()
    result = validate_path_csp(path, "visitor")
    assert result["overall_valid"] is False

def test_emergency_always_valid():
    path = _staff_path()
    result = validate_path_csp(path, "emergency")
    assert result["overall_valid"] is True

def test_icu_time_window_staff():
    result = find_valid_time_window("staff", "ICU_Floor3")
    # Staff has no time restriction — should be 24 hours
    assert result["domain_size"] == 24

def test_icu_time_window_visitor():
    result = find_valid_time_window("visitor", "ICU_Floor3")
    # Visitor cannot access ICU at any hour
    assert result["domain_size"] == 0

def test_node_constraint_visitor_lab():
    ok, reason = check_node_constraint("DIAG_Lab_Medicine", "visitor")
    assert ok is False
    assert "restricted" in reason.lower() or "❌" in reason

def test_node_constraint_staff_lab():
    ok, reason = check_node_constraint("DIAG_Lab_Medicine", "staff")
    assert ok is True

def test_edge_constraint_patient_stairs():
    ok, reason = check_edge_constraint("HW_Corridor_G", "HW_Stairs_A", "stairs", "patient")
    assert ok is False
    assert "wheelchair" in reason.lower() or "stairs" in reason.lower()

def test_validate_returns_trace():
    path = _staff_path()
    result = validate_path_csp(path, "staff")
    assert len(result["trace"]) > 0
