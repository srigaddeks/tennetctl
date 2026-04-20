"""DAG validation tests."""

import pytest
from backend.02_features.01_catalog.sub_features.04_flows.dag import (
    DagValidation,
    Edge,
    NodeInstance,
    validate_dag,
)


def test_valid_dag():
    """Test a valid linear DAG passes."""
    nodes = [
        NodeInstance("n1", "auth", "iam.auth_required", {}),
        NodeInstance("n2", "handler", "core.run_handler", {}),
        NodeInstance("n3", "audit", "audit.emit", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n2", "in", "success"),
        Edge("e2", "n2", "out", "n3", "in", "next"),
    ]

    validation = validate_dag(nodes, edges)
    assert validation.ok


def test_cycle_detection():
    """Test detection of cycles (3-node cycle)."""
    nodes = [
        NodeInstance("n1", "a", "node.a", {}),
        NodeInstance("n2", "b", "node.b", {}),
        NodeInstance("n3", "c", "node.c", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n2", "in", "next"),
        Edge("e2", "n2", "out", "n3", "in", "next"),
        Edge("e3", "n3", "out", "n1", "in", "next"),  # Back edge creates cycle
    ]

    validation = validate_dag(nodes, edges)
    assert not validation.ok
    assert any(e.code == "DAG_CYCLE" for e in validation.errors)


def test_self_loop_detection():
    """Test detection of self-loop."""
    nodes = [
        NodeInstance("n1", "self", "node.self", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n1", "in", "next"),
    ]

    validation = validate_dag(nodes, edges)
    assert not validation.ok
    assert any(e.code == "DAG_CYCLE" for e in validation.errors)


def test_missing_branch_pair():
    """Test detection of incomplete branch pairs."""
    nodes = [
        NodeInstance("n1", "condition", "control.if", {}),
        NodeInstance("n2", "yes", "audit.emit", {}),
    ]

    # Only true_branch, missing false_branch
    edges = [
        Edge("e1", "n1", "result", "n2", "in", "true_branch"),
    ]

    validation = validate_dag(nodes, edges)
    assert not validation.ok
    assert any(e.code == "MISSING_BRANCH_PAIR" for e in validation.errors)


def test_branch_pair_complete():
    """Test that complete branch pairs pass."""
    nodes = [
        NodeInstance("n1", "condition", "control.if", {}),
        NodeInstance("n2", "yes", "audit.emit", {}),
        NodeInstance("n3", "no", "audit.emit", {}),
    ]

    edges = [
        Edge("e1", "n1", "result", "n2", "in", "true_branch"),
        Edge("e2", "n1", "result", "n3", "in", "false_branch"),
    ]

    validation = validate_dag(nodes, edges)
    assert validation.ok


def test_invalid_edge_reference():
    """Test detection of edges referencing non-existent nodes."""
    nodes = [
        NodeInstance("n1", "a", "node.a", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n999", "in", "next"),  # n999 doesn't exist
    ]

    validation = validate_dag(nodes, edges)
    assert not validation.ok
    assert any(e.code == "INVALID_EDGE" for e in validation.errors)


def test_empty_dag():
    """Test that empty DAG is valid."""
    validation = validate_dag([], [])
    assert validation.ok


def test_disconnected_components():
    """Test that disconnected components are allowed (no reachability check yet)."""
    nodes = [
        NodeInstance("n1", "a", "node.a", {}),
        NodeInstance("n2", "b", "node.b", {}),
        NodeInstance("n3", "c", "node.c", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n2", "in", "next"),
        # n3 is isolated
    ]

    validation = validate_dag(nodes, edges)
    # Should be valid — reachability check is future scope
    assert validation.ok


def test_diamond_pattern():
    """Test that diamond patterns (valid DAG) pass."""
    nodes = [
        NodeInstance("n1", "start", "node.start", {}),
        NodeInstance("n2", "left", "node.left", {}),
        NodeInstance("n3", "right", "node.right", {}),
        NodeInstance("n4", "merge", "node.merge", {}),
    ]

    edges = [
        Edge("e1", "n1", "out", "n2", "in", "next"),
        Edge("e2", "n1", "out", "n3", "in", "next"),
        Edge("e3", "n2", "out", "n4", "in", "next"),
        Edge("e4", "n3", "out", "n4", "in", "next"),
    ]

    validation = validate_dag(nodes, edges)
    assert validation.ok


def test_complex_edge_kinds():
    """Test mix of all edge kinds without cycles."""
    nodes = [
        NodeInstance("n1", "api_call", "http.request", {}),
        NodeInstance("n2", "success_handler", "audit.emit", {}),
        NodeInstance("n3", "error_handler", "audit.emit", {}),
        NodeInstance("n4", "condition", "control.if", {}),
        NodeInstance("n5", "next", "http.request", {}),
    ]

    edges = [
        Edge("e1", "n1", "result", "n2", "in", "success"),
        Edge("e2", "n1", "error", "n3", "in", "failure"),
        Edge("e3", "n2", "out", "n4", "in", "next"),
        Edge("e4", "n4", "result", "n5", "in", "true_branch"),
    ]

    validation = validate_dag(nodes, edges)
    # This is actually incomplete — no false_branch for n4
    assert not validation.ok
    assert any(e.code == "MISSING_BRANCH_PAIR" for e in validation.errors)
