"""
Canvas layout engine: deterministic topological layout with lane packing.

Computes x (by topological level) and y (by lane within level) for every node.
Honors operator-set positions (position_x, position_y wins). Deterministic
across reruns due to stable sort by instance_label within each level.
"""

from typing import Any, TypedDict


class Position(TypedDict):
    """Layout position for a node."""
    x: int
    y: int
    lane: int


def topological_levels(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, int]:
    """
    Compute the topological level of each node using a longest-path algorithm.

    Level 0 = nodes with no incoming edges (sources).
    Level N = 1 + max(level of any predecessor).

    Args:
        nodes: List of node dicts with 'id' key
        edges: List of edge dicts with 'from_node_id', 'to_node_id' keys

    Returns:
        dict[node_id -> level]
    """
    node_ids = {n["id"] for n in nodes}
    in_degree: dict[str, int] = {nid: 0 for nid in node_ids}
    adj: dict[str, list[str]] = {nid: [] for nid in node_ids}

    # Build adjacency list and in-degree counts
    for edge in edges:
        from_id = edge["from_node_id"]
        to_id = edge["to_node_id"]
        if from_id in node_ids and to_id in node_ids:
            adj[from_id].append(to_id)
            in_degree[to_id] += 1

    # Kahn's algorithm (topological sort) with level tracking
    queue = [nid for nid in node_ids if in_degree[nid] == 0]
    levels: dict[str, int] = {nid: 0 for nid in node_ids}

    while queue:
        node_id = queue.pop(0)
        for neighbor in adj[node_id]:
            levels[neighbor] = max(levels[neighbor], levels[node_id] + 1)
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return levels


def compute_layout(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> dict[str, Position]:
    """
    Compute layout positions for all nodes.

    - x = level × 240px (topological level from longest path)
    - y = lane × 120px (greedy lane packing within level, stable sort by instance_label)
    - Operator-set position_x/position_y overrides automatic placement

    Args:
        nodes: List of node dicts with keys: id, instance_label, position_x?, position_y?
        edges: List of edge dicts with keys: from_node_id, to_node_id

    Returns:
        dict[node_id -> {x, y, lane}]
    """
    levels = topological_levels(nodes, edges)

    # Group nodes by level
    level_to_nodes: dict[int, list[dict[str, Any]]] = {}
    for node in nodes:
        level = levels[node["id"]]
        if level not in level_to_nodes:
            level_to_nodes[level] = []
        level_to_nodes[level].append(node)

    # Layout
    layout: dict[str, Position] = {}

    for level, level_nodes in level_to_nodes.items():
        # Stable sort by instance_label
        sorted_nodes = sorted(level_nodes, key=lambda n: n.get("instance_label", ""))

        for lane, node in enumerate(sorted_nodes):
            node_id = node["id"]

            # Check if operator set position
            operator_x = node.get("position_x")
            operator_y = node.get("position_y")

            if operator_x is not None and operator_y is not None:
                # Operator wins
                layout[node_id] = {
                    "x": operator_x,
                    "y": operator_y,
                    "lane": lane,
                }
            else:
                # Automatic placement
                x = level * 240
                y = lane * 120
                layout[node_id] = {
                    "x": x,
                    "y": y,
                    "lane": lane,
                }

    return layout
