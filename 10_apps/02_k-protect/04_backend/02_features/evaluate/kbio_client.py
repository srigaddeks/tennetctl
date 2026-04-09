"""kprotect kbio client.

HTTP client for calling kbio internal API endpoints.
Uses httpx with connection pooling. Handles timeouts and fallbacks.
"""
from __future__ import annotations

import importlib
import json
import time
from typing import Any

import httpx

_config = importlib.import_module("01_core.config")

# Module-level client (created lazily, connection-pooled)
_client: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        settings = _config.get_settings()
        _client = httpx.AsyncClient(
            base_url=settings.kbio_api_url.rstrip("/"),
            timeout=httpx.Timeout(connect=2.0, read=3.0, write=2.0, pool=5.0),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=50),
        )
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


async def ingest_batch(batch: dict[str, Any]) -> dict[str, Any]:
    """Forward a behavioral batch to kbio and return scores.

    Calls POST /v1/internal/ingest with the service token.
    Returns the score data from kbio, or a degraded response on failure.
    """
    settings = _config.get_settings()
    client = _get_client()
    start = time.perf_counter()

    try:
        resp = await client.post(
            "/v1/internal/ingest",
            json=batch,
            headers={"X-Internal-Service-Token": settings.kbio_service_token},
        )
        latency = round((time.perf_counter() - start) * 1000, 2)

        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return {"ok": True, "data": data["data"], "latency_ms": latency}

        return {
            "ok": False,
            "error": f"kbio returned {resp.status_code}",
            "latency_ms": latency,
        }
    except (httpx.TimeoutException, httpx.ConnectError) as e:
        latency = round((time.perf_counter() - start) * 1000, 2)
        return {
            "ok": False,
            "error": f"kbio unavailable: {type(e).__name__}",
            "latency_ms": latency,
        }


async def get_score(session_id: str, user_hash: str) -> dict[str, Any]:
    """Get on-demand composite score from kbio."""
    settings = _config.get_settings()
    client = _get_client()

    try:
        resp = await client.post(
            "/v1/internal/score",
            json={"session_id": session_id, "user_hash": user_hash},
            headers={"X-Internal-Service-Token": settings.kbio_service_token},
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return data["data"]
    except (httpx.TimeoutException, httpx.ConnectError):
        pass
    return {}


async def get_trust_profile(user_hash: str) -> dict[str, Any]:
    """Get trust profile from kbio."""
    settings = _config.get_settings()
    client = _get_client()

    try:
        resp = await client.get(
            f"/v1/internal/trust/{user_hash}",
            headers={"X-Internal-Service-Token": settings.kbio_service_token},
        )
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return data["data"]
    except (httpx.TimeoutException, httpx.ConnectError):
        pass
    return {}


async def get_policy_catalog() -> list[dict[str, Any]]:
    """Fetch the predefined policy catalog from kbio."""
    client = _get_client()

    try:
        resp = await client.get("/v1/kbio/policies?limit=500&offset=0")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("ok"):
                return data["data"].get("items", [])
    except (httpx.TimeoutException, httpx.ConnectError):
        pass
    return []
