from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import CollectionRun

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(
    namespace="sandbox.collection_runs.repository",
    logger_name="backend.sandbox.collection_runs.repository.instrumentation",
)
class CollectionRunRepository:

    async def create_run(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        connector_instance_id: str,
        trigger_type: str,
        triggered_by: str | None,
    ) -> CollectionRun:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."35_fct_collection_runs"
                (id, tenant_key, org_id, connector_instance_id,
                 status, trigger_type,
                 started_at, completed_at,
                 assets_discovered, assets_updated, assets_deleted, logs_ingested,
                 error_message, triggered_by,
                 created_at, updated_at)
            VALUES
                (gen_random_uuid(), $1, $2, $3,
                 'queued', $4,
                 NULL, NULL,
                 0, 0, 0, 0,
                 NULL, $5,
                 NOW() AT TIME ZONE 'UTC', NOW() AT TIME ZONE 'UTC')
            RETURNING
                id::text, tenant_key, org_id::text, connector_instance_id::text,
                status, trigger_type,
                started_at, completed_at,
                assets_discovered, assets_updated, assets_deleted, logs_ingested,
                error_message, triggered_by::text,
                created_at, updated_at
            """,
            tenant_key,
            org_id,
            connector_instance_id,
            trigger_type,
            triggered_by,
        )
        return _row_to_run(row)

    async def update_run_status(
        self,
        connection: asyncpg.Connection,
        run_id: str,
        status: str,
        *,
        error_message: str | None = None,
        assets_discovered: int = 0,
        assets_updated: int = 0,
        assets_deleted: int = 0,
        logs_ingested: int = 0,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."35_fct_collection_runs"
            SET status = $1,
                error_message = $2,
                assets_discovered = $3,
                assets_updated = $4,
                assets_deleted = $5,
                logs_ingested = $6,
                updated_at = NOW() AT TIME ZONE 'UTC'
            WHERE id = $7
            """,
            status,
            error_message,
            assets_discovered,
            assets_updated,
            assets_deleted,
            logs_ingested,
            run_id,
        )

    async def set_run_started(
        self,
        connection: asyncpg.Connection,
        run_id: str,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."35_fct_collection_runs"
            SET status = 'running',
                started_at = NOW() AT TIME ZONE 'UTC',
                updated_at = NOW() AT TIME ZONE 'UTC'
            WHERE id = $1
            """,
            run_id,
        )

    async def set_run_completed(
        self,
        connection: asyncpg.Connection,
        run_id: str,
        *,
        status: str = "completed",
        assets_discovered: int = 0,
        assets_updated: int = 0,
        assets_deleted: int = 0,
        logs_ingested: int = 0,
        error_message: str | None = None,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."35_fct_collection_runs"
            SET status = $1,
                completed_at = NOW() AT TIME ZONE 'UTC',
                assets_discovered = $2,
                assets_updated = $3,
                assets_deleted = $4,
                logs_ingested = $5,
                error_message = $6,
                updated_at = NOW() AT TIME ZONE 'UTC'
            WHERE id = $7
            """,
            status,
            assets_discovered,
            assets_updated,
            assets_deleted,
            logs_ingested,
            error_message,
            run_id,
        )

    async def get_run(
        self,
        connection: asyncpg.Connection,
        run_id: str,
        org_id: str,
    ) -> CollectionRun | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                id::text, tenant_key, org_id::text, connector_instance_id::text,
                status, trigger_type,
                started_at, completed_at,
                assets_discovered, assets_updated, assets_deleted, logs_ingested,
                error_message, triggered_by::text,
                created_at, updated_at
            FROM {SCHEMA}."67_vw_collection_run_detail"
            WHERE id = $1 AND org_id = $2
            """,
            run_id,
            org_id,
        )
        return _row_to_run(row) if row else None

    async def list_runs(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        connector_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[CollectionRun], int]:
        """Returns (records, total_count) using a window function."""
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if connector_id is not None:
            filters.append(f"connector_instance_id = ${idx}")
            values.append(connector_id)
            idx += 1
        if status is not None:
            filters.append(f"status = ${idx}")
            values.append(status)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT
                id::text, tenant_key, org_id::text, connector_instance_id::text,
                status, trigger_type,
                started_at, completed_at,
                assets_discovered, assets_updated, assets_deleted, logs_ingested,
                error_message, triggered_by::text,
                created_at, updated_at,
                COUNT(*) OVER() AS _total
            FROM {SCHEMA}."67_vw_collection_run_detail"
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_run(r) for r in rows], total

    async def cancel_run(
        self,
        connection: asyncpg.Connection,
        run_id: str,
        org_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."35_fct_collection_runs"
            SET status = 'cancelled',
                updated_at = NOW() AT TIME ZONE 'UTC'
            WHERE id = $1
              AND org_id = $2
              AND status IN ('queued', 'running')
            """,
            run_id,
            org_id,
        )
        return result != "UPDATE 0"


def _row_to_run(r) -> CollectionRun:
    return CollectionRun(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        connector_instance_id=r["connector_instance_id"],
        status=r["status"],
        trigger_type=r["trigger_type"],
        started_at=r["started_at"],
        completed_at=r["completed_at"],
        assets_discovered=r["assets_discovered"],
        assets_updated=r["assets_updated"],
        assets_deleted=r["assets_deleted"],
        logs_ingested=r["logs_ingested"],
        error_message=r["error_message"],
        triggered_by=r["triggered_by"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )
