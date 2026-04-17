"""Postgres implementation of LogsStore — batch insert + cursor pagination."""

from __future__ import annotations

from typing import Any


class PostgresLogsStore:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def insert_batch(self, conn: Any, records: list[Any]) -> int:
        if not records:
            return 0
        rows = [
            (
                r.id,
                r.org_id,
                r.workspace_id,
                r.resource_id,
                r.recorded_at,
                r.observed_at,
                r.severity_id,
                r.severity_text,
                r.body,
                r.trace_id,
                r.span_id,
                r.trace_flags,
                r.scope_name,
                r.scope_version,
                r.attributes or {},
                r.dropped_attributes_count,
            )
            for r in records
        ]
        await conn.executemany(
            """
            INSERT INTO "05_monitoring"."60_evt_monitoring_logs"
                (id, org_id, workspace_id, resource_id, recorded_at, observed_at,
                 severity_id, severity_text, body, trace_id, span_id, trace_flags,
                 scope_name, scope_version, attributes, dropped_attributes_count)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)
            """,
            rows,
        )
        return len(rows)

    async def query(self, conn: Any, q: Any) -> list[dict[str, Any]]:
        conditions = ["org_id = $1"]
        params: list[Any] = [q.org_id]
        if q.from_ts is not None:
            params.append(q.from_ts)
            conditions.append(f"recorded_at >= ${len(params)}")
        if q.to_ts is not None:
            params.append(q.to_ts)
            conditions.append(f"recorded_at < ${len(params)}")
        if q.severity_min is not None:
            params.append(q.severity_min)
            conditions.append(f"severity_id >= ${len(params)}")
        if q.trace_id is not None:
            params.append(q.trace_id)
            conditions.append(f"trace_id = ${len(params)}")
        if q.body_contains is not None:
            params.append(f"%{q.body_contains}%")
            conditions.append(f"body ILIKE ${len(params)}")
        if q.cursor_recorded_at is not None and q.cursor_id is not None:
            params.append(q.cursor_recorded_at)
            params.append(q.cursor_id)
            conditions.append(
                f"(recorded_at, id) < (${len(params) - 1}, ${len(params)})"
            )
        params.append(max(1, min(q.limit, 1000)))
        where = " AND ".join(conditions)
        sql = f"""
            SELECT id, org_id, workspace_id, resource_id, recorded_at, observed_at,
                   severity_id, severity_text, body, trace_id, span_id, trace_flags,
                   scope_name, scope_version, attributes, dropped_attributes_count
            FROM "05_monitoring"."60_evt_monitoring_logs"
            WHERE {where}
            ORDER BY recorded_at DESC, id DESC
            LIMIT ${len(params)}
        """
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]
