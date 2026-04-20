"""
Trace assembler: joins run events with flow version DAG to produce canvas trace overlay.

Pure computation: no I/O. Takes already-loaded rows and produces per-node status
+ per-edge traversal + timing information.
"""

from datetime import datetime
from typing import Any, Literal, TypedDict


class NodeTraceStatus(TypedDict):
    """Status of a node in a flow run trace."""
    status: Literal["pending", "running", "success", "failure", "skipped", "timed_out"]
    started_at: datetime | None
    finished_at: datetime | None


class EdgeTraversal(TypedDict):
    """Whether an edge was traversed in the flow run."""
    traversed: bool


class CanvasTrace(TypedDict):
    """Complete trace information for a flow run overlay on canvas."""
    node_status: dict[str, NodeTraceStatus]
    edge_traversed: dict[str, bool]
    started_at: datetime | None
    finished_at: datetime | None
    total_duration_ms: int | None


def assemble_trace(
    run_node_rows: list[dict[str, Any]],
    run_edge_rows: list[dict[str, Any]],
    version_nodes: list[dict[str, Any]],
    version_edges: list[dict[str, Any]],
) -> CanvasTrace:
    """
    Assemble trace information from run events.

    Args:
        run_node_rows: Rows from v_catalog_flow_run_node_status
                      Each row: {node_instance_id, event_kind, occurred_at}
        run_edge_rows: Rows from v_catalog_flow_run_edge_traversal
                      Each row: {from_node_id, to_node_id, traversed, from_node_event_time}
        version_nodes: Nodes from the flow version DAG
                      Each node: {id, instance_label, node_key, ...}
        version_edges: Edges from the flow version DAG
                      Each edge: {id, from_node_id, to_node_id, ...}

    Returns:
        CanvasTrace with node_status, edge_traversal, and timing info
    """
    # Build node status map
    node_status: dict[str, NodeTraceStatus] = {}
    event_times: dict[str, datetime] = {}

    # Map run events by node instance ID
    node_event_map: dict[str, dict[str, Any]] = {}
    for row in run_node_rows:
        node_id = row["node_instance_id"]
        node_event_map[node_id] = row

    # Initialize all nodes as pending
    for node in version_nodes:
        node_id = node["id"]
        node_status[node_id] = {
            "status": "pending",
            "started_at": None,
            "finished_at": None,
        }

    # Update statuses from events
    for node_id, event in node_event_map.items():
        event_kind = event.get("event_kind", "")
        occurred_at = event.get("occurred_at")

        # Map event_kind to status
        if event_kind == "started":
            node_status[node_id]["started_at"] = occurred_at
            if node_status[node_id]["status"] == "pending":
                node_status[node_id]["status"] = "running"
        elif event_kind == "success":
            node_status[node_id]["status"] = "success"
            node_status[node_id]["finished_at"] = occurred_at
            event_times[node_id] = occurred_at
        elif event_kind == "failure":
            node_status[node_id]["status"] = "failure"
            node_status[node_id]["finished_at"] = occurred_at
            event_times[node_id] = occurred_at
        elif event_kind == "timeout":
            node_status[node_id]["status"] = "timed_out"
            node_status[node_id]["finished_at"] = occurred_at
            event_times[node_id] = occurred_at

    # Propagate skipped status to downstream nodes after failed nodes
    failed_nodes = {nid for nid, status in node_status.items() if status["status"] == "failure"}
    if failed_nodes:
        # Build adjacency for downstream walk
        adj: dict[str, list[str]] = {n["id"]: [] for n in version_nodes}
        for edge in version_edges:
            from_id = edge["from_node_id"]
            to_id = edge["to_node_id"]
            adj[from_id].append(to_id)

        # Mark downstream of failures as skipped if they have no event
        visited = set()
        to_visit = list(failed_nodes)
        while to_visit:
            node_id = to_visit.pop(0)
            if node_id in visited:
                continue
            visited.add(node_id)

            for downstream_id in adj.get(node_id, []):
                # Only mark skipped if no event exists
                if downstream_id not in node_event_map and downstream_id not in failed_nodes:
                    node_status[downstream_id]["status"] = "skipped"
                to_visit.append(downstream_id)

    # Build edge traversal map
    edge_traversal: dict[str, bool] = {}
    for edge in version_edges:
        edge_id = edge["id"]
        from_id = edge["from_node_id"]
        to_id = edge["to_node_id"]

        # Edge is traversed if:
        # 1. From node succeeded AND to node has any event
        # 2. OR from node failed (and to_node is failure handler)
        from_status = node_status[from_id]["status"]
        to_has_event = to_id in node_event_map

        traversed = (from_status in ("success", "failure")) and to_has_event
        edge_traversal[edge_id] = traversed

    # Compute timing
    all_times = list(event_times.values()) + [
        started for node_stat in node_status.values()
        if (started := node_stat["started_at"])
    ]

    started_at = min(all_times) if all_times else None
    finished_at = max(event_times.values()) if event_times else None
    total_duration_ms = None

    if started_at and finished_at:
        delta = finished_at - started_at
        total_duration_ms = int(delta.total_seconds() * 1000)

    return {
        "node_status": node_status,
        "edge_traversed": edge_traversal,
        "started_at": started_at,
        "finished_at": finished_at,
        "total_duration_ms": total_duration_ms,
    }
