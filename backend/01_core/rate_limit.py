"""In-memory token-bucket rate limiter.

Lightweight baseline intended for intake endpoints (OTLP, etc.) where we
want to shed load per-source without a round-trip to Postgres on every
request. Per-process only — a horizontally-scaled deployment should front
this with a gateway-level limiter (APISIX) for cross-process correctness.
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _Bucket:
    tokens: float
    last_refill: float


@dataclass
class TokenBucketLimiter:
    """Per-key token bucket.

    capacity: max burst size (tokens)
    refill_per_sec: steady-state allowed rate
    """

    capacity: float
    refill_per_sec: float
    _buckets: dict[str, _Bucket] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def acquire(self, key: str, cost: float = 1.0) -> bool:
        now = time.monotonic()
        async with self._lock:
            b = self._buckets.get(key)
            if b is None:
                b = _Bucket(tokens=self.capacity, last_refill=now)
                self._buckets[key] = b
            elapsed = now - b.last_refill
            if elapsed > 0:
                b.tokens = min(self.capacity, b.tokens + elapsed * self.refill_per_sec)
                b.last_refill = now
            if b.tokens >= cost:
                b.tokens -= cost
                return True
            return False


def client_key(request: Any, *, prefix: str) -> str:
    """Derive a rate-limit key from a FastAPI request.

    Prefers an authenticated org/user when present, falls back to client IP.
    """
    state = getattr(request, "state", None)
    org_id = getattr(state, "org_id", None) if state else None
    user_id = getattr(state, "user_id", None) if state else None
    if org_id or user_id:
        return f"{prefix}:org={org_id or '-'}:user={user_id or '-'}"
    xff = request.headers.get("x-forwarded-for") if hasattr(request, "headers") else None
    if xff:
        ip = xff.split(",", 1)[0].strip()
    elif hasattr(request, "client") and request.client is not None:
        ip = request.client.host
    else:
        ip = "unknown"
    return f"{prefix}:ip={ip}"
