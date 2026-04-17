"""Spans store Protocol."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SpansStore(Protocol):
    async def insert_batch(self, conn: Any, records: list[Any]) -> int: ...
    async def query_by_trace(self, conn: Any, trace_id: str) -> list[dict[str, Any]]: ...
    async def query(self, conn: Any, q: Any) -> list[dict[str, Any]]: ...
