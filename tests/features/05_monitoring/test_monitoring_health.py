"""Tests for GET /health/monitoring."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(
                transport=transport, base_url="http://test",
            ) as ac:
                yield ac
        finally:
            _catalog.clear_checkers()


@pytest.mark.asyncio
async def test_monitoring_health_shape(live_app):
    client = live_app
    r = await client.get("/health/monitoring")
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert "workers" in data
    assert "nats" in data
    assert "store" in data
    assert data["store"]["kind"] == "postgres"


@pytest.mark.asyncio
async def test_monitoring_health_workers_list(live_app):
    client = live_app
    r = await client.get("/health/monitoring")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data["workers"], list)
