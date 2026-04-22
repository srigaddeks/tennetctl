"""Canvas repository: data access for flows, runs, and traces."""

from datetime import datetime
from importlib import import_module
from typing import Any

import asyncpg

_core = import_module("backend.01_core")
_flows_repo = import_module("backend.02_features.01_catalog.sub_features.04_flows.repository")


async def load_version_dag(
    conn: asyncpg.Connection,
    flow_id: str,
    version_id: str,
) -> dict[str, Any] | None:
    """
    Load a complete flow version DAG: nodes and edges.

    Returns None if version doesn't exist or belongs to a different flow.
    """
    # Delegate to flows repository
    version = await _flows_repo.get_version(conn, version_id)
    if not version or version.get("flow_id") != flow_id:
        return None
    return version


async def load_run_node_status(
    conn: asyncpg.Connection,
    flow_run_id: str,
) -> list[dict[str, Any]]:
    """
    Load the latest status per node instance in a flow run.

    Reads v_catalog_flow_run_node_status view.
    """
    query = """
    SELECT
        node_instance_id,
        event_kind,
        occurred_at
    FROM "01_catalog"."v_catalog_flow_run_node_status"
    WHERE flow_run_id = $1
    ORDER BY node_instance_id, occurred_at DESC
    """
    rows = await conn.fetch(query, flow_run_id)
    return [dict(row) for row in rows]


async def load_run_edge_traversal(
    conn: asyncpg.Connection,
    flow_run_id: str,
) -> list[dict[str, Any]]:
    """
    Load edge traversal status for a flow run.

    Reads v_catalog_flow_run_edge_traversal view.
    """
    query = """
    SELECT
        edge_id,
        from_node_id,
        to_node_id,
        traversed,
        from_node_event_time,
        to_node_event_time
    FROM "01_catalog"."v_catalog_flow_run_edge_traversal"
    WHERE flow_run_id = $1
    """
    rows = await conn.fetch(query, flow_run_id)
    return [dict(row) for row in rows]


async def list_runs(
    conn: asyncpg.Connection,
    version_id: str,
    from_time: datetime | None = None,
    to_time: datetime | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[dict[str, Any]]:
    """
    List recent flow runs for a version.

    Filters by time range and status if provided. Returns up to limit rows.
    """
    query = """
    SELECT
        id,
        flow_version_id AS version_id,
        started_at,
        finished_at,
        status,
        EXTRACT(EPOCH FROM (finished_at - started_at)) * 1000 AS total_duration_ms
    FROM "01_catalog".v_flow_runs
    WHERE flow_version_id = $1 AND deleted_at IS NULL
    """

    params: list[Any] = [version_id]
    param_num = 2

    if from_time:
        query += f" AND started_at >= ${param_num}"
        params.append(from_time)
        param_num += 1

    if to_time:
        query += f" AND finished_at <= ${param_num}"
        params.append(to_time)
        param_num += 1

    if status:
        query += f" AND status = ${param_num}"
        params.append(status)
        param_num += 1

    query += f" ORDER BY started_at DESC LIMIT ${param_num}"
    params.append(limit)

    rows = await conn.fetch(query, *params)
    return [dict(row) for row in rows]
