from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ._transport import Transport


class Traces:
    """Distributed tracing — query path + raw OTLP emission.

    True auto-instrument (FastAPI + asyncpg + httpx wiring) is deferred to a
    later v0.2.2 phase; this v0 ships the HTTP surface so external callers
    can push spans and query traces now.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def emit_batch(self, resource_spans: list[dict]) -> dict:
        """Push a pre-built OTLP `resourceSpans` payload."""
        return await self._t.request(
            "POST",
            "/v1/monitoring/otlp/v1/traces",
            json={"resourceSpans": resource_spans},
        )

    async def query(self, body: dict) -> dict:
        return await self._t.request(
            "POST", "/v1/monitoring/traces/query", json=body
        )

    async def get(self, trace_id: str) -> dict:
        return await self._t.request(
            "GET", f"/v1/monitoring/traces/{trace_id}"
        )
