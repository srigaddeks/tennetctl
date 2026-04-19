from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class AuditEvents:
    """Query path for audit events. Emission is backend-only via the
    audit.events.emit node — the SDK does not expose an emit() method."""

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list(self, **filters: Any) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return await self._t.request("GET", "/v1/audit-events", params=params or None)

    async def get(self, event_id: str) -> dict:
        return await self._t.request("GET", f"/v1/audit-events/{event_id}")

    async def stats(self, **filters: Any) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return await self._t.request("GET", "/v1/audit-events/stats", params=params or None)

    async def tail(self, **filters: Any) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return await self._t.request("GET", "/v1/audit-events/tail", params=params or None)

    async def funnel(self, body: dict) -> dict:
        return await self._t.request("POST", "/v1/audit-events/funnel", json=body)

    async def retention(self, **filters: Any) -> dict:
        params = {k: v for k, v in filters.items() if v is not None}
        return await self._t.request("GET", "/v1/audit-events/retention", params=params or None)

    async def outbox_cursor(self) -> dict:
        return await self._t.request("GET", "/v1/audit-events/outbox-cursor")

    async def event_keys(self) -> list[dict]:
        data = await self._t.request("GET", "/v1/audit-event-keys")
        return data if isinstance(data, list) else list(data or [])


class Audit:
    def __init__(self, transport: Transport) -> None:
        self.events = AuditEvents(transport)
