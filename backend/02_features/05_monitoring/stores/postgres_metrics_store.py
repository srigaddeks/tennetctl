"""Postgres implementation of MetricsStore.

- register: ON CONFLICT idempotent on (org_id, key).
- increment: writes evt_monitoring_metric_points with counter delta.
- set_gauge: writes gauge point (value column).
- observe_histogram: bucketizes value against histogram_buckets from registry.
- query_timeseries: aggregates evt_monitoring_metric_points using date_trunc.
- query_latest: returns most recent observation for metric + labels.
- Cardinality check: rejects new label combinations past max_cardinality (returns False).
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any


class PostgresMetricsStore:
    # Process-local cardinality cache: {metric_id: (count, expires_epoch)}
    _CARD_TTL_S = 60.0

    def __init__(self, pool: Any) -> None:
        self._pool = pool
        self._card_cache: dict[int, tuple[int, float]] = {}

    async def register(self, conn: Any, metric_def: Any) -> int:
        row = await conn.fetchrow(
            """
            INSERT INTO "05_monitoring"."10_fct_monitoring_metrics"
                (org_id, key, kind_id, label_keys, histogram_buckets,
                 max_cardinality, description, unit)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (org_id, key) DO UPDATE
                SET kind_id           = EXCLUDED.kind_id,
                    label_keys        = EXCLUDED.label_keys,
                    histogram_buckets = EXCLUDED.histogram_buckets,
                    max_cardinality   = EXCLUDED.max_cardinality,
                    description       = EXCLUDED.description,
                    unit              = EXCLUDED.unit,
                    updated_at        = CURRENT_TIMESTAMP
            RETURNING id
            """,
            metric_def.org_id,
            metric_def.key,
            metric_def.kind_id,
            list(metric_def.label_keys),
            list(metric_def.histogram_buckets) if metric_def.histogram_buckets else None,
            metric_def.max_cardinality,
            metric_def.description,
            metric_def.unit,
        )
        return int(row["id"])

    async def _check_cardinality(
        self, conn: Any, metric_id: int, labels: dict[str, Any]
    ) -> bool:
        """Return True if OK to insert; False if over limit."""
        now = time.monotonic()
        cached = self._card_cache.get(metric_id)
        if cached and cached[1] > now:
            current = cached[0]
        else:
            current = int(await conn.fetchval(
                """
                SELECT COUNT(DISTINCT labels)
                FROM "05_monitoring"."61_evt_monitoring_metric_points"
                WHERE metric_id = $1
                """,
                metric_id,
            ) or 0)
            self._card_cache[metric_id] = (current, now + self._CARD_TTL_S)

        max_card = int(await conn.fetchval(
            'SELECT max_cardinality FROM "05_monitoring"."10_fct_monitoring_metrics" WHERE id = $1',
            metric_id,
        ) or 1000)

        # If this label combo already exists, we're safe — it counts as existing.
        exists = await conn.fetchval(
            """
            SELECT 1
            FROM "05_monitoring"."61_evt_monitoring_metric_points"
            WHERE metric_id = $1 AND labels = $2::jsonb
            LIMIT 1
            """,
            metric_id,
            labels or {},
        )
        if exists:
            return True
        if current >= max_card:
            return False
        # Bump cache optimistically.
        self._card_cache[metric_id] = (current + 1, now + self._CARD_TTL_S)
        return True

    async def increment(
        self, conn: Any, metric_id: int, labels: dict[str, Any], value: float,
        *, resource_id: int, org_id: str, recorded_at: datetime | None = None,
    ) -> bool:
        if not await self._check_cardinality(conn, metric_id, labels):
            return False
        ts = recorded_at or datetime.now(timezone.utc).replace(tzinfo=None)
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                (metric_id, resource_id, org_id, labels, value, recorded_at)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            """,
            metric_id, resource_id, org_id, labels or {}, float(value), ts,
        )
        return True

    async def set_gauge(
        self, conn: Any, metric_id: int, labels: dict[str, Any], value: float,
        *, resource_id: int, org_id: str, recorded_at: datetime | None = None,
    ) -> bool:
        if not await self._check_cardinality(conn, metric_id, labels):
            return False
        ts = recorded_at or datetime.now(timezone.utc).replace(tzinfo=None)
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                (metric_id, resource_id, org_id, labels, value, recorded_at)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6)
            """,
            metric_id, resource_id, org_id, labels or {}, float(value), ts,
        )
        return True

    async def observe_histogram(
        self, conn: Any, metric_id: int, labels: dict[str, Any], value: float,
        *, resource_id: int, org_id: str, recorded_at: datetime | None = None,
    ) -> bool:
        if not await self._check_cardinality(conn, metric_id, labels):
            return False
        buckets_row = await conn.fetchrow(
            'SELECT histogram_buckets FROM "05_monitoring"."10_fct_monitoring_metrics" WHERE id = $1',
            metric_id,
        )
        buckets: list[float] = list(buckets_row["histogram_buckets"]) if buckets_row and buckets_row["histogram_buckets"] else []
        counts = [0] * (len(buckets) + 1)
        placed = False
        for i, bound in enumerate(buckets):
            if value <= bound:
                counts[i] = 1
                placed = True
                break
        if not placed:
            counts[-1] = 1

        ts = recorded_at or datetime.now(timezone.utc).replace(tzinfo=None)
        await conn.execute(
            """
            INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                (metric_id, resource_id, org_id, labels, value,
                 histogram_counts, histogram_sum, histogram_count, recorded_at)
            VALUES ($1, $2, $3, $4::jsonb, $5, $6, $7, $8, $9)
            """,
            metric_id, resource_id, org_id, labels or {}, float(value),
            counts, float(value), 1, ts,
        )
        return True

    async def query_timeseries(
        self, conn: Any, metric_id: int, label_filter: dict[str, Any] | None,
        bucket: str, from_ts: datetime, to_ts: datetime,
    ) -> list[dict[str, Any]]:
        valid = {"minute", "hour", "day", "second"}
        if bucket not in valid:
            raise ValueError(f"bucket must be one of {valid}, got {bucket!r}")
        params: list[Any] = [metric_id, from_ts, to_ts]
        filter_clause = ""
        if label_filter:
            params.append(label_filter)
            filter_clause = f"AND labels @> ${len(params)}::jsonb"
        sql = f"""
            SELECT date_trunc('{bucket}', recorded_at) AS bucket,
                   SUM(COALESCE(value, 0))::DOUBLE PRECISION AS sum_value,
                   COUNT(*)::BIGINT AS count
            FROM "05_monitoring"."61_evt_monitoring_metric_points"
            WHERE metric_id = $1 AND recorded_at >= $2 AND recorded_at < $3
              {filter_clause}
            GROUP BY bucket
            ORDER BY bucket
        """
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]

    async def query_latest(
        self, conn: Any, metric_id: int, label_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        params: list[Any] = [metric_id]
        filter_clause = ""
        if label_filter:
            params.append(label_filter)
            filter_clause = f"AND labels @> ${len(params)}::jsonb"
        sql = f"""
            SELECT metric_id, labels, value, recorded_at
            FROM "05_monitoring"."61_evt_monitoring_metric_points"
            WHERE metric_id = $1 {filter_clause}
            ORDER BY recorded_at DESC
            LIMIT 1
        """
        row = await conn.fetchrow(sql, *params)
        return dict(row) if row else None
