"""Postgres implementation of SpansStore."""

from __future__ import annotations

from typing import Any


class PostgresSpansStore:
    def __init__(self, pool: Any) -> None:
        self._pool = pool

    async def insert_batch(self, conn: Any, records: list[Any]) -> int:
        if not records:
            return 0
        rows = [
            (
                r.trace_id,
                r.span_id,
                r.parent_span_id,
                r.org_id,
                r.workspace_id,
                r.resource_id,
                r.name,
                r.kind_id,
                r.status_id,
                r.status_message,
                r.recorded_at,
                r.start_time_unix_nano,
                r.end_time_unix_nano,
                r.attributes or {},
                r.events or [],
                r.links or [],
            )
            for r in records
        ]
        await conn.executemany(
            """
            INSERT INTO "05_monitoring"."62_evt_monitoring_spans"
                (trace_id, span_id, parent_span_id, org_id, workspace_id, resource_id,
                 name, kind_id, status_id, status_message, recorded_at,
                 start_time_unix_nano, end_time_unix_nano, attributes, events, links)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14::jsonb, $15::jsonb, $16::jsonb)
            """,
            rows,
        )
        return len(rows)

    async def query_by_trace(self, conn: Any, trace_id: str) -> list[dict[str, Any]]:
        rows = await conn.fetch(
            """
            SELECT trace_id, span_id, parent_span_id, org_id, workspace_id,
                   resource_id, name, kind_id, status_id, status_message,
                   recorded_at, start_time_unix_nano, end_time_unix_nano,
                   duration_ns, attributes, events, links
            FROM "05_monitoring"."62_evt_monitoring_spans"
            WHERE trace_id = $1
            ORDER BY start_time_unix_nano ASC
            """,
            trace_id,
        )
        return [dict(r) for r in rows]

    async def query(self, conn: Any, q: Any) -> list[dict[str, Any]]:
        conditions = ["s.org_id = $1"]
        params: list[Any] = [q.org_id]
        if q.from_ts is not None:
            params.append(q.from_ts)
            conditions.append(f"s.recorded_at >= ${len(params)}")
        if q.to_ts is not None:
            params.append(q.to_ts)
            conditions.append(f"s.recorded_at < ${len(params)}")
        if q.status_id is not None:
            params.append(q.status_id)
            conditions.append(f"s.status_id = ${len(params)}")
        if q.name_contains is not None:
            params.append(f"%{q.name_contains}%")
            conditions.append(f"s.name ILIKE ${len(params)}")
        if q.service_name is not None:
            params.append(q.service_name)
            conditions.append(f"r.service_name = ${len(params)}")
        params.append(max(1, min(q.limit, 1000)))
        where = " AND ".join(conditions)
        sql = f"""
            SELECT s.trace_id, s.span_id, s.parent_span_id, s.org_id, s.name,
                   s.kind_id, s.status_id, s.status_message, s.recorded_at,
                   s.start_time_unix_nano, s.end_time_unix_nano, s.duration_ns,
                   s.attributes
            FROM "05_monitoring"."62_evt_monitoring_spans" s
            JOIN "05_monitoring"."11_fct_monitoring_resources" r
              ON r.id = s.resource_id
            WHERE {where}
            ORDER BY s.recorded_at DESC
            LIMIT ${len(params)}
        """
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]
