"""Canvas routes: read-only endpoints for rendering flows and traces."""

from datetime import datetime
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, Query
from importlib import import_module

from . import service
from .schemas import CanvasPayload, FlowRunSummary

_core = import_module("backend.01_core")
_response = import_module("backend.01_core.response")

router = APIRouter(prefix="/v1/flows", tags=["canvas"])


@router.get("/{flow_id}/versions/{version_id}/canvas")
async def get_canvas(
    flow_id: str,
    version_id: str,
    trace_id: str | None = Query(None),
    pool: asyncpg.Pool = Depends(_core.database.get_pool),
) -> dict:
    """
    Get the complete canvas render payload for a flow version.

    Single round-trip endpoint serving nodes, edges, ports, layout, and
    optional trace overlay.

    Query params:
    - trace_id: Optional flow run ID for trace overlay

    Returns 404 if version doesn't belong to the given flow.
    Returns 200 with trace=null if trace_id omitted.
    """
    try:
        async with pool.acquire() as conn:
            # Set transaction to read-only
            await conn.execute("SET TRANSACTION READ ONLY")

            payload = await service.assemble_canvas(
                conn,
                flow_id,
                version_id,
                trace_id=trace_id,
            )

            response = _response.success_response(payload.model_dump())

            # Cache control: immutable versions can be cached
            # If trace_id is present, don't cache (state evolves while running)
            if not trace_id:
                response.headers["Cache-Control"] = "private, max-age=2"

            return response

    except ValueError as e:
        if "not found" in str(e):
            return _response.error_response(
                "FLOW_VERSION_NOT_FOUND",
                str(e),
                status_code=404,
            )
        raise


@router.get("/{flow_id}/versions/{version_id}/runs")
async def list_runs(
    flow_id: str,
    version_id: str,
    from_time: datetime | None = Query(None),
    to_time: datetime | None = Query(None),
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=500),
    pool: asyncpg.Pool = Depends(_core.database.get_pool),
) -> dict:
    """
    List recent flow runs for a version.

    Used by the canvas trace picker dropdown. Supports filtering by time range
    and status. Returns the most recent runs first.

    Query params:
    - from_time: Filter runs after this timestamp
    - to_time: Filter runs before this timestamp
    - status: Filter by status (pending, running, success, failure)
    - limit: Max number of runs to return (default 50, max 500)

    Returns list of FlowRunSummary objects.
    """
    try:
        async with pool.acquire() as conn:
            # Set transaction to read-only
            await conn.execute("SET TRANSACTION READ ONLY")

            from . import repository

            runs = await repository.list_runs(
                conn,
                version_id,
                from_time=from_time,
                to_time=to_time,
                status=status,
                limit=limit,
            )

            summaries = [
                FlowRunSummary(
                    id=run["id"],
                    version_id=run["version_id"],
                    started_at=run["started_at"],
                    finished_at=run.get("finished_at"),
                    status=run.get("status", "pending"),
                    total_duration_ms=int(run.get("total_duration_ms") or 0)
                    if run.get("total_duration_ms") else None,
                )
                for run in runs
            ]

            return _response.success_response([s.model_dump() for s in summaries])

    except Exception as e:
        return _response.error_response(
            "INTERNAL_ERROR",
            str(e),
            status_code=500,
        )
