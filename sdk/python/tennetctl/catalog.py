from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class Catalog:
    """Read-only catalog inspection.

    v0.2.3 scope: the only shipped endpoint today is `/v1/catalog/nodes`.
    Additional endpoints (features, sub-features, flows) land as the catalog
    HTTP surface expands; the SDK will grow to match.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def list_nodes(self, **filters: Any) -> list[dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        data = await self._t.request(
            "GET", "/v1/catalog/nodes", params=params or None
        )
        return data if isinstance(data, list) else list(data or [])

    # ---- API-stable aliases for future endpoints (call-through safe) -------
    # Each of these hits an endpoint path reserved by ADR-026. If the backend
    # hasn't shipped them yet the call raises NotFoundError; SDK consumers
    # get a clear signal rather than a silent drift.

    async def list_features(self, **filters: Any) -> list[dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        data = await self._t.request(
            "GET", "/v1/catalog/features", params=params or None
        )
        return data if isinstance(data, list) else list(data or [])

    async def list_sub_features(self, *, feature: str | None = None) -> list[dict]:
        params = {"feature": feature} if feature else None
        data = await self._t.request(
            "GET", "/v1/catalog/sub-features", params=params
        )
        return data if isinstance(data, list) else list(data or [])

    async def get_flow(self, key: str) -> dict:
        return await self._t.request("GET", f"/v1/catalog/flows/{key}")
