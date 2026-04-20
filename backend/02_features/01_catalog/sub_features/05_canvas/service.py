"""Canvas service: assemble render payload."""

from datetime import datetime
from importlib import import_module
from typing import Any

import asyncpg

from . import repository
from .layout import compute_layout
from .port_index import build_port_index
from .schemas import (
    CanvasEdge,
    CanvasLayoutEntry,
    CanvasNode,
    CanvasNodePorts,
    CanvasPayload,
    CanvasPort,
    CanvasTrace,
    TraceNodeStatus,
)
from .trace_assembler import assemble_trace

_core = import_module("backend.01_core")


async def assemble_canvas(
    conn: asyncpg.Connection,
    flow_id: str,
    version_id: str,
    trace_id: str | None = None,
    registry: Any = None,
) -> CanvasPayload:
    """
    Assemble a complete canvas render payload.

    Single transaction. Loads the flow version DAG, resolves ports from the
    live registry, computes layout, and optionally loads + assembles trace.

    Args:
        conn: Database connection
        flow_id: Flow ID (used for validation)
        version_id: Flow version ID
        trace_id: Optional flow run ID for trace overlay
        registry: Node registry (if None, will be loaded)

    Returns:
        CanvasPayload ready to serialize

    Raises:
        ValueError: If version doesn't exist or belongs to different flow
    """
    # Load flow version DAG
    version_data = await repository.load_version_dag(conn, flow_id, version_id)
    if not version_data:
        raise ValueError(f"Flow version {version_id} not found for flow {flow_id}")

    nodes_raw = version_data.get("nodes", [])
    edges_raw = version_data.get("edges", [])

    # Convert raw nodes and edges to typed dicts
    nodes: list[CanvasNode] = []
    for node_raw in nodes_raw:
        nodes.append(
            CanvasNode(
                id=node_raw["id"],
                instance_label=node_raw["instance_label"],
                node_key=node_raw["node_key"],
                kind=node_raw.get("kind", "control"),
                config_json=node_raw.get("config_json", {}),
                position={
                    "x": node_raw.get("position_x"),
                    "y": node_raw.get("position_y"),
                } if node_raw.get("position_x") is not None else {},
            )
        )

    edges: list[CanvasEdge] = []
    for edge_raw in edges_raw:
        edges.append(
            CanvasEdge(
                id=edge_raw["id"],
                from_node_id=edge_raw["from_node_id"],
                from_port=edge_raw["from_port_key"],
                to_node_id=edge_raw["to_node_id"],
                to_port=edge_raw["to_port_key"],
                kind=edge_raw.get("edge_kind", "next"),
            )
        )

    # Resolve ports from live registry
    node_keys = [n.node_key for n in nodes]

    if registry is None:
        # Load registry from catalog
        try:
            catalog_module = import_module("backend.01_catalog")
            registry = catalog_module.registry
        except Exception:
            registry = None

    ports_by_key: dict[str, CanvasNodePorts] = {}
    if registry:
        port_index = build_port_index(node_keys, registry)
        for key, port_data in port_index.items():
            ports_by_key[key] = CanvasNodePorts(
                inputs=[CanvasPort(key=p["key"], type=p["type"]) for p in port_data["inputs"]],
                outputs=[CanvasPort(key=p["key"], type=p["type"]) for p in port_data["outputs"]],
                unresolved=port_data["unresolved"],
            )

    # Compute layout
    layout_data = compute_layout(
        [{"id": n.id, "instance_label": n.instance_label, **n.position} for n in nodes],
        [{"from_node_id": e.from_node_id, "to_node_id": e.to_node_id} for e in edges],
    )

    layout: dict[str, CanvasLayoutEntry] = {
        node_id: CanvasLayoutEntry(**pos_data)
        for node_id, pos_data in layout_data.items()
    }

    # Optionally load and assemble trace
    trace: CanvasTrace | None = None
    if trace_id:
        try:
            run_nodes = await repository.load_run_node_status(conn, trace_id)
            run_edges = await repository.load_run_edge_traversal(conn, trace_id)

            trace_data = assemble_trace(
                run_nodes,
                run_edges,
                [n.model_dump() for n in nodes],
                [e.model_dump() for e in edges],
            )

            trace = CanvasTrace(
                node_status={
                    node_id: TraceNodeStatus(**status_data)
                    for node_id, status_data in trace_data["node_status"].items()
                },
                edge_traversed=trace_data["edge_traversed"],
                started_at=trace_data["started_at"],
                finished_at=trace_data["finished_at"],
                total_duration_ms=trace_data["total_duration_ms"],
            )
        except Exception:
            # If trace assembly fails, continue with trace=null
            trace = None

    return CanvasPayload(
        nodes=nodes,
        edges=edges,
        ports=ports_by_key,
        layout=layout,
        trace=trace,
    )
