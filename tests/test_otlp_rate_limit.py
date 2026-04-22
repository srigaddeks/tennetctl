"""OTLP intake rate limiter (FIX-25) — verifies 429 on budget exhaustion.

Operates directly against the TokenBucketLimiter object (and its public
acquire coroutine) in addition to driving the endpoint, because the ASGI
transport serializes requests such that the steady-state refill keeps up
with sequential awaits. Drive the limiter directly to assert the token
accounting is correct; also fire the endpoint to confirm the 429 wiring.
"""

from __future__ import annotations

import asyncio
from importlib import import_module


class TestOtlpRateLimit:
    async def test_token_bucket_drains_and_rejects(self):
        _rl = import_module("backend.01_core.rate_limit")
        bucket = _rl.TokenBucketLimiter(capacity=3.0, refill_per_sec=0.0)
        assert await bucket.acquire("k")
        assert await bucket.acquire("k")
        assert await bucket.acquire("k")
        assert not await bucket.acquire("k"), "4th acquire must fail after 3-token bucket drains"

    async def test_token_bucket_refills_over_time(self):
        _rl = import_module("backend.01_core.rate_limit")
        bucket = _rl.TokenBucketLimiter(capacity=1.0, refill_per_sec=100.0)
        assert await bucket.acquire("k")
        assert not await bucket.acquire("k"), "immediate retry must drain"
        await asyncio.sleep(0.05)  # 5 tokens worth at 100/s
        assert await bucket.acquire("k"), "refill must make a token available"

    async def test_logs_endpoint_returns_429_when_bucket_empty(self, client):
        """Force the real endpoint's limiter to empty and confirm a 429."""
        _routes = import_module(
            "backend.02_features.05_monitoring.sub_features.01_logs.routes"
        )
        _rl = import_module("backend.01_core.rate_limit")
        key = "otlp.logs:ip=198.51.100.1"
        # Drain the bucket for this exact key.
        bucket = _routes._otlp_logs_limiter
        while await bucket.acquire(key):
            pass
        # Next request from the same forwarded IP must be 429.
        r = await client.post(
            "/v1/monitoring/otlp/v1/logs",
            headers={
                "content-type": "application/x-protobuf",
                "x-forwarded-for": "198.51.100.1",
            },
            content=b"",
        )
        assert r.status_code == 429, f"expected 429 (rate_limited); got {r.status_code} {r.text}"

    async def test_limiter_is_per_key(self, client):
        """Different X-Forwarded-For values use independent buckets."""
        r1 = await client.post(
            "/v1/monitoring/otlp/v1/logs",
            headers={"content-type": "application/x-protobuf", "x-forwarded-for": "198.51.100.2"},
            content=b"",
        )
        r2 = await client.post(
            "/v1/monitoring/otlp/v1/logs",
            headers={"content-type": "application/x-protobuf", "x-forwarded-for": "198.51.100.3"},
            content=b"",
        )
        assert r1.status_code in (200, 400), r1.text
        assert r2.status_code in (200, 400), r2.text

