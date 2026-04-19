"""
Server-side Product Ops SDK namespace.

Mirrors the browser SDK's track/identify/alias methods but for backend
service calls (e.g. emit a "order.completed" event from a webhook handler).

Server-side calls flow through the same POST /v1/track endpoint with a
project_key. Unlike the browser SDK, server calls can carry rich properties
that the SDK does NOT hash by default — server callers are responsible for
PII handling per their own contract.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _new_anon_id() -> str:
    return f"v_srv_{uuid.uuid4().hex[:16]}"


class ProductOps:
    """Server-side product analytics SDK.

    Usage:
      client = Tennetctl(...)
      await client.product.track(
          project_key="pk_...",
          anonymous_id="v_visitor_abc",
          event_name="order.completed",
          properties={"order_id": "ord_123", "amount_cents": 4999},
      )
    """

    def __init__(self, transport: "Transport") -> None:
        self._t = transport

    async def track(
        self,
        *,
        project_key: str,
        anonymous_id: str | None = None,
        event_name: str,
        properties: dict[str, Any] | None = None,
        page_url: str | None = None,
        referrer: str | None = None,
        utm_source: str | None = None,
        utm_medium: str | None = None,
        utm_campaign: str | None = None,
        occurred_at: str | None = None,
    ) -> dict:
        """Emit a single custom event server-side."""
        body = {
            "project_key": project_key,
            "events": [
                {
                    "kind": "custom",
                    "anonymous_id": anonymous_id or _new_anon_id(),
                    "event_name": event_name,
                    "occurred_at": occurred_at or _now_iso(),
                    "properties": properties or {},
                    "page_url": page_url,
                    "referrer": referrer,
                    "utm_source": utm_source,
                    "utm_medium": utm_medium,
                    "utm_campaign": utm_campaign,
                }
            ],
        }
        return await self._t.request("POST", "/v1/track", json=body)

    async def track_batch(
        self,
        *,
        project_key: str,
        events: list[dict],
    ) -> dict:
        """Emit a pre-built batch (≤1000 events). Caller validates schema."""
        return await self._t.request(
            "POST", "/v1/track",
            json={"project_key": project_key, "events": events},
        )

    async def identify(
        self,
        *,
        project_key: str,
        anonymous_id: str,
        user_id: str,
        traits: dict[str, Any] | None = None,
    ) -> dict:
        """Resolve an anonymous visitor → IAM user. Idempotent."""
        return await self._t.request(
            "POST", "/v1/track",
            json={
                "project_key": project_key,
                "events": [{
                    "kind": "identify",
                    "anonymous_id": anonymous_id,
                    "occurred_at": _now_iso(),
                    "properties": {"user_id": user_id, "traits": traits or {}},
                }],
            },
        )

    async def list_events(
        self,
        *,
        workspace_id: str,
        cursor: str | None = None,
        limit: int = 100,
    ) -> dict:
        """Read path. Workspace-scoped."""
        params: dict[str, Any] = {"workspace_id": workspace_id, "limit": limit}
        if cursor:
            params["cursor"] = cursor
        return await self._t.request("GET", "/v1/product-events", params=params)

    async def get_visitor(self, visitor_id: str) -> dict:
        return await self._t.request("GET", f"/v1/product-visitors/{visitor_id}")
