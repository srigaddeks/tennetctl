"""Repository for monitoring.metrics — thin wrapper over stores + view reads."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_stores: Any = import_module("backend.02_features.05_monitoring.stores")


async def list_metrics(conn: Any, *, org_id: str) -> list[dict[str, Any]]:
    rows = await conn.fetch(
        """
        SELECT id, org_id, key, kind_id, kind_code, label_keys, histogram_buckets,
               max_cardinality, description, unit, created_at, updated_at
        FROM "05_monitoring"."v_monitoring_metrics"
        WHERE org_id = $1
        ORDER BY key
        """,
        org_id,
    )
    return [dict(r) for r in rows]


async def get_metric_by_key(conn: Any, *, org_id: str, key: str) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, kind_id, kind_code, label_keys, histogram_buckets,
               max_cardinality, description, unit, created_at, updated_at
        FROM "05_monitoring"."v_monitoring_metrics"
        WHERE org_id = $1 AND key = $2
        """,
        org_id,
        key,
    )
    return dict(row) if row else None


async def get_metric_by_id(conn: Any, *, metric_id: int) -> dict[str, Any] | None:
    row = await conn.fetchrow(
        """
        SELECT id, org_id, key, kind_id, kind_code, label_keys, histogram_buckets,
               max_cardinality, description, unit, created_at, updated_at
        FROM "05_monitoring"."v_monitoring_metrics"
        WHERE id = $1
        """,
        metric_id,
    )
    return dict(row) if row else None


def metrics_store(pool: Any) -> Any:
    return _stores.get_metrics_store(pool)


def resources_store(pool: Any) -> Any:
    return _stores.get_resources_store(pool)
