"""In-process metrics SDK — counter / gauge / histogram factories.

Usage:
    from backend.02_features.05_monitoring.sdk import metrics

    c = metrics.counter("auth.signin.attempts", labels=["outcome"])
    await c.increment(ctx, labels={"outcome": "success"})

Implementation:
- First call per (org_id, key) registers the metric via
  run_node("monitoring.metrics.register", ...) under an asyncio.Lock.
- Subsequent calls skip register and go straight to the ingest node.
- When config.monitoring_enabled is False, all handles are no-ops.
- Caches are process-local; _reset_sdk_cache() is exposed for tests.
"""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

_catalog: Any = import_module("backend.01_catalog")
_config: Any = import_module("backend.01_core.config")

logger = logging.getLogger("tennetctl.monitoring.sdk")

__all__ = ["counter", "gauge", "histogram", "_reset_sdk_cache"]

# Module-level caches.
_registered: dict[tuple[str, str], int] = {}
_locks: dict[tuple[str, str], asyncio.Lock] = {}


def _reset_sdk_cache() -> None:
    """Testing hook — drop process-level SDK caches."""
    _registered.clear()
    _locks.clear()


def _enabled() -> bool:
    try:
        return bool(_config.load_config().monitoring_enabled)
    except Exception:
        # Config unavailable — err on the safe side (no-op).
        return False


def _pool_from_ctx(ctx: Any) -> Any:
    pool = (ctx.extras or {}).get("pool") if ctx is not None else None
    if pool is None:
        raise RuntimeError(
            "monitoring SDK requires ctx.extras['pool'] — pass the FastAPI app pool "
            "when constructing NodeContext"
        )
    return pool


class _BaseHandle:
    kind: str = ""

    def __init__(
        self,
        key: str,
        *,
        label_keys: list[str],
        description: str,
        unit: str,
        max_cardinality: int,
        histogram_buckets: list[float] | None = None,
    ) -> None:
        self.key = key
        self.label_keys = list(label_keys)
        self.description = description
        self.unit = unit
        self.max_cardinality = int(max_cardinality)
        self.histogram_buckets = (
            list(histogram_buckets) if histogram_buckets else None
        )

    async def _ensure_registered(self, ctx: Any) -> int:
        if ctx is None or not ctx.org_id:
            raise RuntimeError(
                "monitoring SDK requires a NodeContext with org_id set"
            )
        org_key = (str(ctx.org_id), self.key)
        cached = _registered.get(org_key)
        if cached is not None:
            return cached
        lock = _locks.setdefault(org_key, asyncio.Lock())
        async with lock:
            cached = _registered.get(org_key)
            if cached is not None:
                return cached
            pool = _pool_from_ctx(ctx)
            result = await _catalog.run_node(
                pool,
                "monitoring.metrics.register",
                ctx,
                {
                    "org_id": ctx.org_id,
                    "key": self.key,
                    "kind": self.kind,
                    "label_keys": list(self.label_keys),
                    "description": self.description,
                    "unit": self.unit,
                    "histogram_buckets": self.histogram_buckets,
                    "max_cardinality": self.max_cardinality,
                },
            )
            metric_id = int(result["metric_id"])
            _registered[org_key] = metric_id
            return metric_id


class CounterHandle(_BaseHandle):
    kind = "counter"

    async def increment(
        self,
        ctx: Any,
        *,
        labels: dict[str, str] | None = None,
        value: float = 1.0,
    ) -> None:
        if not _enabled():
            logger.debug("monitoring disabled — counter.increment(%s) no-op", self.key)
            return
        await self._ensure_registered(ctx)
        pool = _pool_from_ctx(ctx)
        await _catalog.run_node(
            pool,
            "monitoring.metrics.increment",
            ctx,
            {
                "org_id": ctx.org_id,
                "metric_key": self.key,
                "labels": dict(labels or {}),
                "value": float(value),
            },
        )


class GaugeHandle(_BaseHandle):
    kind = "gauge"

    async def set(
        self,
        ctx: Any,
        *,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        if not _enabled():
            logger.debug("monitoring disabled — gauge.set(%s) no-op", self.key)
            return
        await self._ensure_registered(ctx)
        pool = _pool_from_ctx(ctx)
        await _catalog.run_node(
            pool,
            "monitoring.metrics.set_gauge",
            ctx,
            {
                "org_id": ctx.org_id,
                "metric_key": self.key,
                "labels": dict(labels or {}),
                "value": float(value),
            },
        )


class HistogramHandle(_BaseHandle):
    kind = "histogram"

    async def observe(
        self,
        ctx: Any,
        *,
        value: float,
        labels: dict[str, str] | None = None,
    ) -> None:
        if not _enabled():
            logger.debug(
                "monitoring disabled — histogram.observe(%s) no-op", self.key
            )
            return
        await self._ensure_registered(ctx)
        pool = _pool_from_ctx(ctx)
        await _catalog.run_node(
            pool,
            "monitoring.metrics.observe_histogram",
            ctx,
            {
                "org_id": ctx.org_id,
                "metric_key": self.key,
                "labels": dict(labels or {}),
                "value": float(value),
            },
        )


def counter(
    key: str,
    *,
    labels: list[str] | None = None,
    description: str = "",
    unit: str = "1",
    max_cardinality: int = 1000,
) -> CounterHandle:
    return CounterHandle(
        key,
        label_keys=labels or [],
        description=description,
        unit=unit,
        max_cardinality=max_cardinality,
    )


def gauge(
    key: str,
    *,
    labels: list[str] | None = None,
    description: str = "",
    unit: str = "1",
    max_cardinality: int = 1000,
) -> GaugeHandle:
    return GaugeHandle(
        key,
        label_keys=labels or [],
        description=description,
        unit=unit,
        max_cardinality=max_cardinality,
    )


def histogram(
    key: str,
    *,
    buckets: list[float],
    labels: list[str] | None = None,
    description: str = "",
    unit: str = "1",
    max_cardinality: int = 1000,
) -> HistogramHandle:
    if not buckets:
        raise ValueError("histogram() requires non-empty buckets")
    return HistogramHandle(
        key,
        label_keys=labels or [],
        description=description,
        unit=unit,
        max_cardinality=max_cardinality,
        histogram_buckets=list(buckets),
    )
