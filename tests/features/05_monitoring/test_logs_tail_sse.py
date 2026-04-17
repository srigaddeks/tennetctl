"""Unit tests for the logs SSE live-tail generator.

httpx.ASGITransport buffers the full response body before returning, so the
SSE endpoint cannot be end-to-end tested via ASGITransport. We therefore
exercise the async generator directly (bypassing HTTP) for all behavioural
assertions, plus one minimal route-registration assertion.
"""

from __future__ import annotations

import asyncio
import base64
import json
import os
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

import pytest

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_core_id: Any = import_module("backend.01_core.id")
_stores: Any = import_module("backend.02_features.05_monitoring.stores")
_types: Any = import_module("backend.02_features.05_monitoring.stores.types")
_log_routes: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.01_logs.routes"
)

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_ORG_ID = "019e0000-aaaa-7000-0000-000000000001"
_WS_ID = "019e0000-aaaa-7000-0000-000000000002"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "05_monitoring"."60_evt_monitoring_logs" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "05_monitoring"."11_fct_monitoring_resources" WHERE org_id = $1',
            _ORG_ID,
        )


async def _seed_logs(
    pool: Any, n: int, body_prefix: str = "tail-log",
    severity_id: int = 17,
) -> list[str]:
    ids: list[str] = []
    async with pool.acquire() as conn:
        rstore = _stores.get_resources_store(pool)
        rid = await rstore.upsert(conn, _types.ResourceRecord(
            org_id=_ORG_ID,
            service_name="tail-service",
            service_instance_id=None,
            service_version=None,
            attributes={},
        ))
        lstore = _stores.get_logs_store(pool)
        records = []
        for i in range(n):
            log_id = _core_id.uuid7()
            ids.append(log_id)
            records.append(_types.LogRecord(
                id=log_id,
                org_id=_ORG_ID,
                workspace_id=_WS_ID,
                resource_id=rid,
                recorded_at=_now(),
                observed_at=_now(),
                severity_id=severity_id,
                severity_text="ERROR",
                body=f"{body_prefix} {i}",
                trace_id=None,
                span_id=None,
                trace_flags=None,
                scope_name=None,
                scope_version=None,
                attributes={"seq": i},
                dropped_attributes_count=0,
            ))
        await lstore.insert_batch(conn, records)
    return ids


@pytest.fixture
async def live_pool():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            yield pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


def test_tail_route_is_registered():
    """Sanity: the SSE route is mounted and declares text/event-stream."""
    router = _log_routes.router
    paths = [r.path for r in router.routes]  # type: ignore[attr-defined]
    assert "/v1/monitoring/logs/tail" in paths
    # Content type is declared on the StreamingResponse inside the handler;
    # assert here that the SSE header helper uses event-stream conventions.
    assert _log_routes._SSE_HEADERS["Cache-Control"] == "no-cache"
    assert _log_routes._SSE_HEADERS["X-Accel-Buffering"] == "no"


@pytest.mark.asyncio
async def test_tail_generator_emits_ready_and_data(live_pool):
    """Generator yields `: ready` immediately, then a `data:` frame per row."""
    pool = live_pool

    async def _drive():
        gen = _log_routes._tail_generator(pool, _ORG_ID, None)
        first = await gen.__anext__()
        assert first == b": ready\n\n"
        # Seed rows after first yield (simulates runtime arrival).
        await _seed_logs(pool, n=2)

        # Drain up to ~5s looking for data frames.
        got: list[bytes] = []
        end_at = asyncio.get_event_loop().time() + 6.0
        while asyncio.get_event_loop().time() < end_at:
            try:
                chunk = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
            except asyncio.TimeoutError:
                break
            got.append(chunk)
            if sum(1 for g in got if g.startswith(b"data: ")) >= 2:
                break
        await gen.aclose()
        return got

    chunks = await _drive()
    joined = b"".join(chunks)
    assert joined.count(b"data: ") >= 2, f"expected >=2 data frames, got: {joined!r}"
    assert b"tail-log" in joined


@pytest.mark.asyncio
async def test_tail_generator_emits_heartbeat_when_idle(live_pool):
    """With no new rows, generator emits `: keepalive` after heartbeat interval."""
    pool = live_pool
    # Monkey-patch heartbeat to 2s so the test stays fast.
    gen = _log_routes._tail_generator(
        pool, _ORG_ID, None,
        poll_interval_s=0.3,
        heartbeat_interval_s=1.0,
    )
    try:
        first = await gen.__anext__()
        assert first == b": ready\n\n"
        seen_hb = False
        end_at = asyncio.get_event_loop().time() + 6.0
        while asyncio.get_event_loop().time() < end_at:
            try:
                chunk = await asyncio.wait_for(gen.__anext__(), timeout=2.0)
            except asyncio.TimeoutError:
                break
            if chunk.startswith(b": keepalive"):
                seen_hb = True
                break
        assert seen_hb, "no heartbeat in 6s"
    finally:
        await gen.aclose()


@pytest.mark.asyncio
async def test_tail_generator_filter_applied(live_pool):
    """severity_min filter excludes seeded rows at lower severity."""
    pool = live_pool
    gen = _log_routes._tail_generator(
        pool, _ORG_ID,
        {"severity_min": 21},  # only FATAL+ — seeded rows are 17 (ERROR)
        poll_interval_s=0.3,
        heartbeat_interval_s=2.0,
    )
    got: list[bytes] = []

    async def _consume() -> None:
        async for chunk in gen:
            got.append(chunk)

    task = asyncio.create_task(_consume())
    try:
        # Wait for ": ready" to arrive, then seed rows that should be filtered.
        for _ in range(20):
            if got and got[0] == b": ready\n\n":
                break
            await asyncio.sleep(0.1)
        await _seed_logs(pool, n=2, severity_id=17)
        # Wait long enough to cover several polls.
        await asyncio.sleep(3.0)
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        await gen.aclose()
    # None of the collected chunks should be data frames — rows are below
    # the severity floor.
    for c in got:
        assert not c.startswith(b"data: "), f"unexpected data frame: {c!r}"


def test_decode_filter_base64():
    """filter_b64 helper decodes URL-safe base64 JSON into a dict."""
    payload = {"severity_min": 17, "service_name": "svc-a"}
    b64 = base64.urlsafe_b64encode(
        json.dumps(payload).encode("utf-8")
    ).decode("ascii").rstrip("=")
    got = _log_routes._decode_filter(b64)
    assert got == payload
    assert _log_routes._decode_filter(None) is None
