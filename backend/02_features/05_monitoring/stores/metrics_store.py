"""Metrics store Protocol."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MetricsStore(Protocol):
    async def register(self, conn: Any, metric_def: Any) -> int: ...
    async def increment(
        self, conn: Any, metric_id: int, labels: dict[str, Any], value: float,
        *, resource_id: int, org_id: str, recorded_at: datetime | None = None,
    ) -> bool: ...
    async def set_gauge(
        self, conn: Any, metric_id: int, labels: dict[str, Any], value: float,
        *, resource_id: int, org_id: str, recorded_at: datetime | None = None,
    ) -> bool: ...
    async def observe_histogram(
        self, conn: Any, metric_id: int, labels: dict[str, Any], value: float,
        *, resource_id: int, org_id: str, recorded_at: datetime | None = None,
    ) -> bool: ...
    async def query_timeseries(
        self, conn: Any, metric_id: int, label_filter: dict[str, Any] | None,
        bucket: str, from_ts: datetime, to_ts: datetime,
    ) -> list[dict[str, Any]]: ...
    async def query_latest(
        self, conn: Any, metric_id: int, label_filter: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None: ...
