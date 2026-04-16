"""Tests for middleware + main app integration."""

from __future__ import annotations

from importlib import import_module

import pytest

_errors = import_module("backend.01_core.errors")


@pytest.mark.asyncio
async def test_health_returns_success_envelope(client):
    """GET /health returns standard success envelope."""
    resp = await client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"ok": True, "data": {"status": "healthy"}}


@pytest.mark.asyncio
async def test_request_id_header_present(client):
    """Every response includes X-Request-ID header."""
    resp = await client.get("/health")
    assert "x-request-id" in resp.headers
    request_id = resp.headers["x-request-id"]
    assert len(request_id) == 36  # UUID format


@pytest.mark.asyncio
async def test_request_id_is_unique(client):
    """Each request gets a unique X-Request-ID."""
    r1 = await client.get("/health")
    r2 = await client.get("/health")
    assert r1.headers["x-request-id"] != r2.headers["x-request-id"]


@pytest.mark.asyncio
async def test_unknown_route_returns_404(client):
    """Unknown routes return 404."""
    resp = await client.get("/nonexistent")
    assert resp.status_code == 404
