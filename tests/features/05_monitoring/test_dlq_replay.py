"""Tests for POST /v1/monitoring/dlq/replay.

Does not exercise a real JetStream. Instead validates the scope gate + shape
by stubbing the NATS client at module level.
"""

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
async def test_dlq_replay_without_scope_403(live_app):
    client = live_app
    r = await client.post("/v1/monitoring/dlq/replay", json={
        "subject": "monitoring.dlq.logs",
        "limit": 5,
    })
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_dlq_replay_invalid_subject_422(live_app):
    client = live_app
    r = await client.post(
        "/v1/monitoring/dlq/replay",
        json={"subject": "monitoring.dlq.evil", "limit": 5},
        headers={"x-monitoring-admin": "1"},
    )
    assert r.status_code == 422
