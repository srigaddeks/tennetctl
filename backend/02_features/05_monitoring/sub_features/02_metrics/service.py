"""Service layer for monitoring.metrics.

register_metric emits audit (monitoring.metrics.registered).
increment / set_gauge / observe_histogram are ingest-path (hot-path); they
skip audit on success per the 13-01 carve-out (audit-of-ingest bypass,
mirrors vault.secrets.get hot-path). They DO emit a failure audit
(monitoring.metrics.cardinality_exceeded) when the store rejects due to
cardinality limit.
"""

from __future__ import annotations

import time
from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.repository"
)
_schemas: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.02_metrics.schemas"
)
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")
_catalog: Any = import_module("backend.01_catalog")
_errors: Any = import_module("backend.01_core.errors")
_dsl: Any = import_module("backend.02_features.05_monitoring.query_dsl")


async def query(
    conn: Any,
    ctx: Any,
    dsl: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:
    """Validate + compile + execute a metrics timeseries DSL query."""
    q = _dsl.validate_metrics_query(dsl)
    sql, params = _dsl.compile_metrics_query(q, ctx)
    rows = await conn.fetch(sql, *params)
    items = [dict(r) for r in rows]
    return items, None


# Process-local metric resolution cache: (org_id, key) -> (row, expires_epoch).
_METRIC_CACHE_TTL_S = 60.0
_metric_cache: dict[tuple[str, str], tuple[dict[str, Any], float]] = {}


def _cache_put(org_id: str, key: str, row: dict[str, Any]) -> None:
    _metric_cache[(org_id, key)] = (row, time.monotonic() + _METRIC_CACHE_TTL_S)


def _cache_get(org_id: str, key: str) -> dict[str, Any] | None:
    cached = _metric_cache.get((org_id, key))
    if cached is None:
        return None
    row, exp = cached
    if exp < time.monotonic():
        _metric_cache.pop((org_id, key), None)
        return None
    return row


def _cache_clear() -> None:
    """Testing hook — drop the process cache."""
    _metric_cache.clear()


async def _resolve_metric(
    conn: Any, *, org_id: str, key: str
) -> dict[str, Any]:
    cached = _cache_get(org_id, key)
    if cached is not None:
        return cached
    row = await _repo.get_metric_by_key(conn, org_id=org_id, key=key)
    if row is None:
        raise _errors.NotFoundError(f"metric {key!r} not registered for org {org_id!r}")
    _cache_put(org_id, key, row)
    return row


async def _resolve_resource(
    conn: Any,
    pool: Any,
    *,
    org_id: str,
    resource: Any | None,
) -> int:
    rstore = _repo.resources_store(pool)
    if resource is None:
        record = _types.ResourceRecord(
            org_id=org_id,
            service_name="tennetctl-api",
            service_instance_id=None,
            service_version=None,
            attributes={},
        )
    else:
        record = _types.ResourceRecord(
            org_id=org_id,
            service_name=resource.service_name,
            service_instance_id=resource.service_instance_id,
            service_version=resource.service_version,
            attributes=dict(resource.attributes or {}),
        )
    return await rstore.upsert(conn, record)


def _validate_labels(metric: dict[str, Any], labels: dict[str, str]) -> None:
    allowed = set(metric.get("label_keys") or [])
    provided = set(labels.keys())
    extra = provided - allowed
    if extra:
        raise _errors.ValidationError(
            f"labels {sorted(extra)!r} not in registered label_keys {sorted(allowed)!r} "
            f"for metric {metric['key']!r}"
        )


async def _emit_cardinality_failure(
    pool: Any, ctx: Any, *, metric: dict[str, Any], labels: dict[str, str]
) -> None:
    # Uses audit failure-outcome bypass for scope requirements.
    try:
        await _catalog.run_node(
            pool,
            "audit.events.emit",
            ctx,
            {
                "event_key": "monitoring.metrics.cardinality_exceeded",
                "outcome": "failure",
                "metadata": {
                    "metric_id": int(metric["id"]),
                    "metric_key": metric["key"],
                    "label_keys": list(metric.get("label_keys") or []),
                    "max_cardinality": int(metric["max_cardinality"]),
                    "rejected_labels": dict(labels),
                },
            },
        )
    except Exception:
        # Fire-and-forget: never fail the request solely because audit failed.
        pass


async def register_metric(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    org_id: str,
    req: Any,
) -> dict[str, Any]:
    store = _repo.metrics_store(pool)
    metric_def = _types.MetricDef(
        org_id=org_id,
        key=req.key,
        kind_id=_schemas.kind_to_id(req.kind),
        label_keys=list(req.label_keys),
        histogram_buckets=list(req.histogram_buckets) if req.histogram_buckets else None,
        max_cardinality=int(req.max_cardinality),
        description=req.description or "",
        unit=req.unit or "",
    )
    metric_id = await store.register(conn, metric_def)
    row = await _repo.get_metric_by_id(conn, metric_id=metric_id)
    if row is None:
        raise _errors.AppError(
            "UNEXPECTED", f"metric {req.key!r} not readable after register", 500,
        )
    # Invalidate any stale cache entry.
    _metric_cache.pop((org_id, req.key), None)

    await _catalog.run_node(
        pool,
        "audit.events.emit",
        ctx,
        {
            "event_key": "monitoring.metrics.registered",
            "outcome": "success",
            "metadata": {
                "metric_id": int(metric_id),
                "metric_key": req.key,
                "kind": req.kind,
                "label_keys": list(req.label_keys),
                "max_cardinality": int(req.max_cardinality),
            },
        },
    )
    return row


async def list_metrics(conn: Any, *, org_id: str) -> list[dict[str, Any]]:
    return await _repo.list_metrics(conn, org_id=org_id)


async def get_metric(conn: Any, *, org_id: str, key: str) -> dict[str, Any] | None:
    return await _repo.get_metric_by_key(conn, org_id=org_id, key=key)


async def increment(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    org_id: str,
    key: str,
    req: Any,
) -> dict[str, Any]:
    metric = await _resolve_metric(conn, org_id=org_id, key=key)
    if metric["kind_code"] != "counter":
        raise _errors.ValidationError(
            f"metric {key!r} is kind={metric['kind_code']!r}, not 'counter'"
        )
    if float(req.value) < 0:
        raise _errors.ValidationError("counter increment value must be >= 0")
    _validate_labels(metric, req.labels)

    resource_id = await _resolve_resource(
        conn, pool, org_id=org_id, resource=req.resource,
    )
    store = _repo.metrics_store(pool)
    ok = await store.increment(
        conn,
        int(metric["id"]),
        dict(req.labels),
        float(req.value),
        resource_id=resource_id,
        org_id=org_id,
    )
    if not ok:
        await _emit_cardinality_failure(pool, ctx, metric=metric, labels=req.labels)
        raise _errors.AppError(
            "CARDINALITY_EXCEEDED",
            f"metric {key!r} exceeded max_cardinality={metric['max_cardinality']}",
            429,
        )
    return {"metric_id": int(metric["id"]), "accepted": True}


async def set_gauge(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    org_id: str,
    key: str,
    req: Any,
) -> dict[str, Any]:
    metric = await _resolve_metric(conn, org_id=org_id, key=key)
    if metric["kind_code"] != "gauge":
        raise _errors.ValidationError(
            f"metric {key!r} is kind={metric['kind_code']!r}, not 'gauge'"
        )
    _validate_labels(metric, req.labels)
    resource_id = await _resolve_resource(
        conn, pool, org_id=org_id, resource=req.resource,
    )
    store = _repo.metrics_store(pool)
    ok = await store.set_gauge(
        conn,
        int(metric["id"]),
        dict(req.labels),
        float(req.value),
        resource_id=resource_id,
        org_id=org_id,
    )
    if not ok:
        await _emit_cardinality_failure(pool, ctx, metric=metric, labels=req.labels)
        raise _errors.AppError(
            "CARDINALITY_EXCEEDED",
            f"metric {key!r} exceeded max_cardinality={metric['max_cardinality']}",
            429,
        )
    return {"metric_id": int(metric["id"]), "accepted": True}


async def observe_histogram(
    conn: Any,
    pool: Any,
    ctx: Any,
    *,
    org_id: str,
    key: str,
    req: Any,
) -> dict[str, Any]:
    metric = await _resolve_metric(conn, org_id=org_id, key=key)
    if metric["kind_code"] != "histogram":
        raise _errors.ValidationError(
            f"metric {key!r} is kind={metric['kind_code']!r}, not 'histogram'"
        )
    _validate_labels(metric, req.labels)
    resource_id = await _resolve_resource(
        conn, pool, org_id=org_id, resource=req.resource,
    )
    store = _repo.metrics_store(pool)
    ok = await store.observe_histogram(
        conn,
        int(metric["id"]),
        dict(req.labels),
        float(req.value),
        resource_id=resource_id,
        org_id=org_id,
    )
    if not ok:
        await _emit_cardinality_failure(pool, ctx, metric=metric, labels=req.labels)
        raise _errors.AppError(
            "CARDINALITY_EXCEEDED",
            f"metric {key!r} exceeded max_cardinality={metric['max_cardinality']}",
            429,
        )
    return {"metric_id": int(metric["id"]), "accepted": True}
