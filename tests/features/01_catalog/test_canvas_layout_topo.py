"""Test canvas layout computation."""

from backend.02_features.01_catalog.sub_features.05_canvas.layout import (
    compute_layout,
    topological_levels,
)


def test_topological_levels_simple_chain():
    """Test: A→B→C yields levels 0, 1, 2."""
    nodes = [{"id": "A"}, {"id": "B"}, {"id": "C"}]
    edges = [
        {"from_node_id": "A", "to_node_id": "B"},
        {"from_node_id": "B", "to_node_id": "C"},
    ]

    levels = topological_levels(nodes, edges)
    assert levels["A"] == 0
    assert levels["B"] == 1
    assert levels["C"] == 2


def test_topological_levels_diamond():
    """Test: Diamond A→B,C; B,C→D yields A=0, B=C=1, D=2."""
    nodes = [{"id": "A"}, {"id": "B"}, {"id": "C"}, {"id": "D"}]
    edges = [
        {"from_node_id": "A", "to_node_id": "B"},
        {"from_node_id": "A", "to_node_id": "C"},
        {"from_node_id": "B", "to_node_id": "D"},
        {"from_node_id": "C", "to_node_id": "D"},
    ]

    levels = topological_levels(nodes, edges)
    assert levels["A"] == 0
    assert levels["B"] == 1
    assert levels["C"] == 1
    assert levels["D"] == 2


def test_layout_x_by_level():
    """Test: Level 0 → x=0, Level 1 → x=240, Level 2 → x=480."""
    nodes = [
        {"id": "A", "instance_label": "a", "position_x": None, "position_y": None},
        {"id": "B", "instance_label": "b", "position_x": None, "position_y": None},
        {"id": "C", "instance_label": "c", "position_x": None, "position_y": None},
    ]
    edges = [
        {"from_node_id": "A", "to_node_id": "B"},
        {"from_node_id": "B", "to_node_id": "C"},
    ]

    layout = compute_layout(nodes, edges)
    assert layout["A"]["x"] == 0
    assert layout["B"]["x"] == 240
    assert layout["C"]["x"] == 480


def test_layout_y_by_lane():
    """Test: Lane 0 → y=0, Lane 1 → y=120, Lane 2 → y=240."""
    nodes = [
        {"id": "A", "instance_label": "a", "position_x": None, "position_y": None},
        {"id": "B", "instance_label": "b", "position_x": None, "position_y": None},
        {"id": "C", "instance_label": "c", "position_x": None, "position_y": None},
    ]
    # All at same level (A→B, A→C)
    edges = [
        {"from_node_id": "A", "to_node_id": "B"},
        {"from_node_id": "A", "to_node_id": "C"},
    ]

    layout = compute_layout(nodes, edges)
    # A at level 0
    assert layout["A"]["y"] == 0
    # B, C at level 1 (sorted by instance_label)
    assert layout["B"]["y"] == 0  # "b" < "c"
    assert layout["C"]["y"] == 120


def test_layout_operator_position_wins():
    """Test: Operator-set position_x/position_y overrides automatic placement."""
    nodes = [
        {"id": "A", "instance_label": "a", "position_x": 50, "position_y": 50},
        {"id": "B", "instance_label": "b", "position_x": None, "position_y": None},
    ]
    edges = [{"from_node_id": "A", "to_node_id": "B"}]

    layout = compute_layout(nodes, edges)
    # A's operator position
    assert layout["A"]["x"] == 50
    assert layout["A"]["y"] == 50
    # B's automatic position
    assert layout["B"]["x"] == 240
    assert layout["B"]["y"] == 0


def test_layout_determinism():
    """Test: Running compute_layout twice yields byte-identical results."""
    nodes = [
        {"id": "A", "instance_label": "auth", "position_x": None, "position_y": None},
        {"id": "B", "instance_label": "handler", "position_x": None, "position_y": None},
        {"id": "C", "instance_label": "audit", "position_x": None, "position_y": None},
    ]
    edges = [
        {"from_node_id": "A", "to_node_id": "B"},
        {"from_node_id": "B", "to_node_id": "C"},
    ]

    layout1 = compute_layout(nodes, edges)
    layout2 = compute_layout(nodes, edges)

    # Exact same positions
    for node_id in ["A", "B", "C"]:
        assert layout1[node_id] == layout2[node_id]
