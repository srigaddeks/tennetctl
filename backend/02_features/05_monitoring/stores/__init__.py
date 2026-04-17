"""Store factories — reads TENNETCTL_MONITORING_STORE_KIND via config."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_cfg: Any = import_module("backend.01_core.config")
_logs: Any = import_module("backend.02_features.05_monitoring.stores.postgres_logs_store")
_metrics: Any = import_module("backend.02_features.05_monitoring.stores.postgres_metrics_store")
_spans: Any = import_module("backend.02_features.05_monitoring.stores.postgres_spans_store")
_resources: Any = import_module("backend.02_features.05_monitoring.stores.postgres_resources_store")


def _kind() -> str:
    return _cfg.load_config().monitoring_store_kind


def _guard(kind: str) -> None:
    if kind != "postgres":
        raise NotImplementedError(
            f"Monitoring store kind {kind!r} not available in v0.1.5 — "
            "only 'postgres' is supported. ClickHouse swap scheduled for v0.2."
        )


def get_logs_store(pool: Any) -> Any:
    k = _kind()
    _guard(k)
    return _logs.PostgresLogsStore(pool)


def get_metrics_store(pool: Any) -> Any:
    k = _kind()
    _guard(k)
    return _metrics.PostgresMetricsStore(pool)


def get_spans_store(pool: Any) -> Any:
    k = _kind()
    _guard(k)
    return _spans.PostgresSpansStore(pool)


def get_resources_store(pool: Any) -> Any:
    k = _kind()
    _guard(k)
    return _resources.PostgresResourcesStore(pool)
