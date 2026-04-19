from __future__ import annotations

import hashlib
import json
import time
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ._transport import Transport

DEFAULT_TTL_SECONDS = 60.0


def _cache_key(key: str, entity: Any, context: Any) -> str:
    payload = json.dumps(
        {"k": key, "e": entity, "c": context}, sort_keys=True, default=str
    ).encode()
    return hashlib.sha256(payload).hexdigest()


class Flags:
    """Feature flag evaluation with a simple TTL cache.

    Cache policy (v0.2.1): fetch on first call, return cached result for up to
    `ttl_seconds` without a network round-trip. On expiry, a fresh fetch blocks
    the caller (no background refresh — true SWR lands in v0.2.2).
    """

    def __init__(self, transport: Transport, *, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> None:
        self._t = transport
        self._ttl = ttl_seconds
        self._cache: dict[str, tuple[float, Any]] = {}

    async def evaluate(self, key: str, *, entity: Any, context: Any | None = None) -> dict:
        ck = _cache_key(key, entity, context)
        now = time.monotonic()
        hit = self._cache.get(ck)
        if hit and (now - hit[0]) < self._ttl:
            return hit[1]

        body: dict[str, Any] = {"key": key, "entity": entity}
        if context is not None:
            body["context"] = context
        result = await self._t.request("POST", "/v1/evaluate", json=body)
        self._cache[ck] = (now, result)
        return result

    async def evaluate_bulk(self, evaluations: list[dict]) -> list[dict]:
        """Bulk evaluation — not cached (assumption: caller batches heterogeneous work)."""
        result = await self._t.request("POST", "/v1/evaluate/bulk", json={"evaluations": evaluations})
        return result if isinstance(result, list) else list(result or [])

    def clear_cache(self) -> None:
        self._cache.clear()

    def invalidate(self, key: str | None = None) -> None:
        """Invalidate all entries for a flag key, or everything if key is None."""
        if key is None:
            self.clear_cache()
            return
        # Cache keys are sha256 hashes — we don't reverse-index per flag key,
        # so invalidate-by-key wipes everything. Fine at v0.2.1 scale; better
        # index in v0.2.2.
        self.clear_cache()
