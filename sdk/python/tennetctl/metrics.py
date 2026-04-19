from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport


class Metrics:
    """Counter / gauge / histogram emission + registry + query.

    Emission is fail-open at the SDK level — if you want guaranteed delivery,
    handle errors at the call site. Current implementation is synchronous;
    async batch + drop-on-retry-exhaustion is a v0.2.2 follow-up noted in
    the SDK roadmap.
    """

    def __init__(self, transport: Transport) -> None:
        self._t = transport

    async def increment(
        self,
        key: str,
        *,
        value: float = 1.0,
        labels: dict[str, Any] | None = None,
    ) -> dict:
        body: dict[str, Any] = {"value": value}
        if labels is not None:
            body["labels"] = labels
        return await self._t.request(
            "POST", f"/v1/monitoring/metrics/{key}/increment", json=body
        )

    async def set(
        self,
        key: str,
        *,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> dict:
        body: dict[str, Any] = {"value": value}
        if labels is not None:
            body["labels"] = labels
        return await self._t.request(
            "POST", f"/v1/monitoring/metrics/{key}/set", json=body
        )

    async def observe(
        self,
        key: str,
        *,
        value: float,
        labels: dict[str, Any] | None = None,
    ) -> dict:
        body: dict[str, Any] = {"value": value}
        if labels is not None:
            body["labels"] = labels
        return await self._t.request(
            "POST", f"/v1/monitoring/metrics/{key}/observe", json=body
        )

    # ---- registry -----------------------------------------------------------

    async def register(
        self,
        *,
        key: str,
        kind: str,
        description: str | None = None,
        buckets: list[float] | None = None,
        cardinality_limit: int | None = None,
    ) -> dict:
        body: dict[str, Any] = {"key": key, "kind": kind}
        if description is not None:
            body["description"] = description
        if buckets is not None:
            body["buckets"] = buckets
        if cardinality_limit is not None:
            body["cardinality_limit"] = cardinality_limit
        return await self._t.request("POST", "/v1/monitoring/metrics", json=body)

    async def list(self, **filters: Any) -> list[dict]:
        params = {k: v for k, v in filters.items() if v is not None}
        data = await self._t.request(
            "GET", "/v1/monitoring/metrics", params=params or None
        )
        return data if isinstance(data, list) else list(data or [])

    async def get(self, key: str) -> dict:
        return await self._t.request("GET", f"/v1/monitoring/metrics/{key}")

    async def query(self, body: dict) -> dict:
        return await self._t.request("POST", "/v1/monitoring/metrics/query", json=body)
