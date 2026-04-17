"""Logs store Protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from importlib import import_module

_types: Any = import_module("backend.02_features.05_monitoring.stores.types")
LogRecord = _types.LogRecord
LogQuery = _types.LogQuery


@runtime_checkable
class LogsStore(Protocol):
    async def insert_batch(self, conn: Any, records: list[Any]) -> int: ...
    async def query(self, conn: Any, q: Any) -> list[dict[str, Any]]: ...
