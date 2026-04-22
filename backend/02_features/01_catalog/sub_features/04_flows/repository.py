"""Repository: raw SQL operations for flows."""

from importlib import import_module
from typing import Any

from .schemas import FlowStatus, NodeInstanceOut

_id = import_module("backend.01_core.id")


async def list_flows(
    conn: Any,
    org_id: str,
    status: FlowStatus | None = None,
    q: str | None = None,
    workspace_id: str | None = None,
) -> list[dict[str, Any]]:
    """List flows matching criteria."""
    query = 'SELECT * FROM "01_catalog".v_flows WHERE org_id = $1 AND deleted_at IS NULL'
    params: list[Any] = [org_id]
    param_idx = 2

    if workspace_id:
        query += f" AND workspace_id = ${param_idx}"
        params.append(workspace_id)
        param_idx += 1

    if status:
        query += f" AND status = ${param_idx}"
        params.append(status)
        param_idx += 1

    if q:
        query += f" AND (name ILIKE ${param_idx} OR slug ILIKE ${param_idx})"
        params.append(f"%{q}%")
        param_idx += 1

    query += " ORDER BY updated_at DESC"
    return await conn.fetch(query, *params)


async def get_flow(conn: Any, flow_id: str) -> dict[str, Any] | None:
    """Get a single flow by ID."""
    return await conn.fetchrow(
        'SELECT * FROM "01_catalog".v_flows WHERE id = $1 AND deleted_at IS NULL',
        flow_id
    )


async def create_flow(
    conn: Any,
    org_id: str,
    workspace_id: str,
    slug: str,
    name: str,
    description: str | None,
    user_id: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Create a new flow with initial draft version.

    Writes identity to 10_fct_flows, strings to 20_dtl_flows, then inserts
    an initial v1 draft row into 11_fct_flow_versions.

    Returns:
        (flow_dict, version_dict)
    """
    flow_id = _id.uuid7()

    await conn.execute(
        """
        INSERT INTO "01_catalog"."10_fct_flows"
        (id, org_id, workspace_id, status_id, is_active, is_test,
         created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, 1, true, false, $4, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        flow_id, org_id, workspace_id, user_id,
    )

    await conn.execute(
        """
        INSERT INTO "01_catalog"."20_dtl_flows"
        (flow_id, org_id, slug, name, description, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        flow_id, org_id, slug, name, description,
    )

    version_id = _id.uuid7()
    await conn.execute(
        """
        INSERT INTO "01_catalog"."11_fct_flow_versions"
        (id, flow_id, org_id, version_number, status_id,
         is_active, is_test, created_by, updated_by, created_at, updated_at)
        VALUES ($1, $2, $3, 1, 1, true, false, $4, $4, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        version_id, flow_id, org_id, user_id,
    )

    await conn.execute(
        """
        UPDATE "01_catalog"."10_fct_flows"
        SET current_version_id = $1, updated_by = $3, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
        """,
        version_id, flow_id, user_id,
    )

    flow = await conn.fetchrow(
        'SELECT * FROM "01_catalog".v_flows WHERE id = $1',
        flow_id
    )
    version = await conn.fetchrow(
        'SELECT * FROM "01_catalog".v_flow_versions WHERE id = $1',
        version_id
    )
    return (flow, version)


async def update_flow_strings(
    conn: Any,
    flow_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
) -> None:
    """Patch slug/name/description on 20_dtl_flows.

    Only updates fields explicitly provided. Slug changes are not supported here
    (would need uniqueness re-check) — reserved for a future dedicated endpoint.
    """
    set_parts: list[str] = []
    params: list[Any] = []
    idx = 1

    if name is not None:
        set_parts.append(f"name = ${idx}")
        params.append(name)
        idx += 1

    if description is not None:
        set_parts.append(f"description = ${idx}")
        params.append(description)
        idx += 1

    if not set_parts:
        return

    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    params.append(flow_id)

    query = (
        f'UPDATE "01_catalog"."20_dtl_flows" SET {", ".join(set_parts)} '
        f'WHERE flow_id = ${idx}'
    )
    await conn.execute(query, *params)


async def update_flow_status(
    conn: Any,
    flow_id: str,
    status_id: int,
    user_id: str,
) -> None:
    """Update status_id on 10_fct_flows."""
    await conn.execute(
        """
        UPDATE "01_catalog"."10_fct_flows"
        SET status_id = $2, updated_by = $3, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        flow_id, status_id, user_id,
    )


async def get_version(conn: Any, version_id: str) -> dict[str, Any] | None:
    """
    Get a flow version with full DAG (nodes + edges + resolved ports).

    Returns dict with version info + nodes[] + edges[].
    """
    version = await conn.fetchrow(
        'SELECT * FROM "01_catalog".v_flow_versions WHERE id = $1',
        version_id
    )

    if not version:
        return None

    nodes_raw = await conn.fetch(
        """
        SELECT
            id, instance_label, node_key, config_json,
            position_x, position_y
        FROM "01_catalog"."21_dtl_flow_nodes"
        WHERE flow_version_id = $1
        ORDER BY sort_order, created_at
        """,
        version_id
    )

    edges_raw = await conn.fetch(
        """
        SELECT
            dtl.id, dtl.from_node_id, dtl.from_port_key,
            dtl.to_node_id, dtl.to_port_key,
            dim.code AS edge_kind
        FROM "01_catalog"."22_dtl_flow_edges" dtl
        LEFT JOIN "01_catalog"."05_dim_flow_edge_kind" dim
            ON dtl.edge_kind_id = dim.id
        WHERE dtl.flow_version_id = $1
        ORDER BY dtl.sort_order, dtl.created_at
        """,
        version_id
    )

    nodes = [
        NodeInstanceOut(
            id=n["id"],
            instance_label=n["instance_label"],
            node_key=n["node_key"],
            config=n["config_json"] or {},
            position={"x": n["position_x"], "y": n["position_y"]} if n["position_x"] is not None else None,
            inputs=[],
            outputs=[],
        )
        for n in nodes_raw
    ]

    edges = [
        {
            "id": e["id"],
            "from_node_id": e["from_node_id"],
            "from_port_key": e["from_port_key"],
            "to_node_id": e["to_node_id"],
            "to_port_key": e["to_port_key"],
            "kind": e["edge_kind"],
        }
        for e in edges_raw
    ]

    return {
        **dict(version),
        "nodes": nodes,
        "edges": edges,
    }


async def replace_version_dag(
    conn: Any,
    version_id: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> None:
    """
    Replace all nodes and edges in a (draft) version.

    Atomically clears and re-inserts. Used by PATCH endpoint.
    """
    await conn.execute(
        'DELETE FROM "01_catalog"."22_dtl_flow_edges" WHERE flow_version_id = $1',
        version_id
    )
    await conn.execute(
        'DELETE FROM "01_catalog"."21_dtl_flow_nodes" WHERE flow_version_id = $1',
        version_id
    )

    label_to_id: dict[str, str] = {}
    for i, node in enumerate(nodes):
        node_id = _id.uuid7()
        label_to_id[node["instance_label"]] = node_id

        await conn.execute(
            """
            INSERT INTO "01_catalog"."21_dtl_flow_nodes"
            (id, flow_version_id, node_key, instance_label, config_json,
             position_x, position_y, sort_order, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
            """,
            node_id,
            version_id,
            node["node_key"],
            node["instance_label"],
            node.get("config_json", {}),
            (node.get("position") or {}).get("x"),
            (node.get("position") or {}).get("y"),
            i,
        )

    edge_kind_id_map = {
        "next": 1,
        "success": 2,
        "failure": 3,
        "true_branch": 4,
        "false_branch": 5,
    }

    for i, edge in enumerate(edges):
        from_node_id = edge.get("from_node_id") or label_to_id.get(edge.get("from_instance_label", ""))
        to_node_id   = edge.get("to_node_id")   or label_to_id.get(edge.get("to_instance_label", ""))

        if not from_node_id or not to_node_id:
            continue

        edge_kind_id = edge_kind_id_map.get(edge["kind"], 1)

        await conn.execute(
            """
            INSERT INTO "01_catalog"."22_dtl_flow_edges"
            (id, flow_version_id, from_node_id, from_port_key, to_node_id, to_port_key,
             edge_kind_id, sort_order, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, CURRENT_TIMESTAMP)
            """,
            _id.uuid7(),
            version_id,
            from_node_id,
            edge["from_port"],
            to_node_id,
            edge["to_port"],
            edge_kind_id,
            i,
        )


async def mark_archived(conn: Any, flow_id: str, user_id: str) -> None:
    """Mark a flow as archived (status=3)."""
    await update_flow_status(conn, flow_id, 3, user_id)


async def soft_delete(conn: Any, flow_id: str, user_id: str) -> None:
    """Soft-delete a flow (updates both fct and dtl deleted_at)."""
    await conn.execute(
        """
        UPDATE "01_catalog"."10_fct_flows"
        SET deleted_at = CURRENT_TIMESTAMP, updated_by = $2, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
        """,
        flow_id, user_id,
    )
    await conn.execute(
        """
        UPDATE "01_catalog"."20_dtl_flows"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE flow_id = $1
        """,
        flow_id,
    )
