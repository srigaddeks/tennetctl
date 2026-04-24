"""Smoke tests for somaerp /health endpoints.

These tests bypass the FastAPI lifespan (so no real Postgres or live
tennetctl is required) by instantiating the app via `create_app()` and
manually populating `app.state` (config, started_at_monotonic, tennetctl).

The tennetctl client is replaced with an in-process stub whose `ping()`
returns a successful envelope — proving the proxy round-trip path is
exercised without making a real network call.
"""

from __future__ import annotations

import os
import sys
import time
from importlib import import_module
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# Ensure the repo root is on sys.path so `apps.somaerp.backend.*` imports work.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Required env vars for Config.load_config() (set before importing main).
os.environ.setdefault("SOMAERP_PG_PASS", "test")
os.environ.setdefault("TENNETCTL_SERVICE_API_KEY", "test-service-key")


class _StubTennetctlClient:
    """Drop-in replacement for TennetctlClient in tests.

    Implements only `ping()` — the single method `service.get_health` calls.
    Returns a fixed successful envelope so the proxy round-trip is provably
    exercised without any real network I/O.
    """

    def __init__(self, base_url: str = "http://localhost:51734") -> None:
        self._base_url = base_url

    @property
    def base_url(self) -> str:
        return self._base_url

    async def start(self) -> None:  # pragma: no cover - parity with real client
        return None

    async def stop(self) -> None:  # pragma: no cover - parity with real client
        return None

    async def ping(self) -> dict:
        return {"ok": True, "data": {"service": "tennetctl", "status": "healthy"}}


@pytest_asyncio.fixture
async def client():
    """Build the app, populate state manually, yield an httpx AsyncClient.

    Uses a no-op lifespan via ASGITransport(lifespan="off") so we don't try
    to open a real asyncpg pool or HTTP client during tests.
    """
    _config_mod = import_module("apps.somaerp.backend.01_core.config")
    _main = import_module("apps.somaerp.backend.main")

    app = _main.create_app()
    cfg = _config_mod.load_config()
    app.state.config = cfg
    app.state.started_at_monotonic = time.monotonic()
    app.state.tennetctl = _StubTennetctlClient(base_url=cfg.tennetctl_base_url)
    app.state.pool = None

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_root_health_liveness(client: AsyncClient) -> None:
    """Low-level /health (no DB, no proxy) returns 200 + envelope."""
    r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["data"]["service"] == "somaerp"
    assert body["data"]["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_endpoint_returns_envelope(client: AsyncClient) -> None:
    """/v1/somaerp/health returns 200 + the full envelope shape."""
    r = await client.get("/v1/somaerp/health")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    data = body["data"]
    assert isinstance(data["somaerp_version"], str) and data["somaerp_version"]
    assert isinstance(data["somaerp_uptime_s"], (int, float))
    assert data["somaerp_uptime_s"] >= 0
    assert "tennetctl_proxy" in data
    proxy = data["tennetctl_proxy"]
    assert {"ok", "base_url", "latency_ms", "last_error"} <= set(proxy.keys())


@pytest.mark.asyncio
async def test_health_envelope_includes_tennetctl_proxy_status(
    client: AsyncClient,
) -> None:
    """tennetctl_proxy.base_url matches configured URL; ok is bool; last_error is str|None."""
    _config_mod = import_module("apps.somaerp.backend.01_core.config")
    cfg = _config_mod.load_config()

    r = await client.get("/v1/somaerp/health")
    assert r.status_code == 200
    proxy = r.json()["data"]["tennetctl_proxy"]

    assert proxy["base_url"] == cfg.tennetctl_base_url
    assert isinstance(proxy["ok"], bool)
    assert proxy["ok"] is True  # stub returns ok envelope
    assert proxy["last_error"] is None or isinstance(proxy["last_error"], str)
    assert isinstance(proxy["latency_ms"], (int, float))
    assert proxy["latency_ms"] >= 0
