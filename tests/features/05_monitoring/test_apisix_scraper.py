"""Unit tests for ApisixScraper — httpx mocked via httpx.MockTransport."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

_scraper_mod: Any = import_module("backend.02_features.05_monitoring.workers.apisix_scraper")
ApisixScraper = _scraper_mod.ApisixScraper


_SAMPLE_METRICS = """\
# HELP apisix_http_requests_total Total HTTP requests.
# TYPE apisix_http_requests_total counter
apisix_http_requests_total{route="r1",service="s1"} 42
# HELP apisix_etcd_reachable Etcd reachable flag.
# TYPE apisix_etcd_reachable gauge
apisix_etcd_reachable 1
"""


class _FakeConn:
    def __init__(self):
        self._tx = MagicMock()
        self._tx.__aenter__ = AsyncMock()
        self._tx.__aexit__ = AsyncMock()

    def transaction(self):
        return self._tx


class _FakePool:
    def __init__(self):
        self.conn = _FakeConn()

    def acquire(self):
        class _Ctx:
            def __init__(self, conn): self.conn = conn
            async def __aenter__(self): return self.conn
            async def __aexit__(self, *a): return None
        return _Ctx(self.conn)


def _make_config(url: str = "http://apisix.test/metrics") -> Any:
    c = MagicMock()
    c.monitoring_apisix_url = url
    c.monitoring_store_kind = "postgres"
    return c


@pytest.fixture
def scraper_fixture(monkeypatch):
    pool = _FakePool()
    metrics_store = AsyncMock()
    # register returns incrementing ids so we can verify caching.
    reg_calls = {"n": 0}
    async def _register(_conn, metric_def):
        reg_calls["n"] += 1
        return reg_calls["n"]
    metrics_store.register = _register
    metrics_store.increment = AsyncMock(return_value=True)
    metrics_store.set_gauge = AsyncMock(return_value=True)
    metrics_store.observe_histogram = AsyncMock(return_value=True)

    resources_store = AsyncMock()
    resources_store.upsert = AsyncMock(return_value=99)

    _stores = import_module("backend.02_features.05_monitoring.stores")
    monkeypatch.setattr(_stores, "get_metrics_store", lambda _p: metrics_store)
    monkeypatch.setattr(_stores, "get_resources_store", lambda _p: resources_store)

    scraper = ApisixScraper(pool=pool, config=_make_config())
    return scraper, metrics_store, resources_store, reg_calls


async def test_sample_prometheus_text_registers_and_writes(scraper_fixture):
    scraper, metrics_store, _resources, reg_calls = scraper_fixture
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, text=_SAMPLE_METRICS))
    async with httpx.AsyncClient(transport=transport) as client:
        written = await scraper.scrape_once(client)
    assert written >= 2  # counter + gauge
    # 2 unique metric families registered.
    assert reg_calls["n"] == 2
    # Counter called through increment (first scrape: delta == full value).
    metrics_store.increment.assert_awaited()
    metrics_store.set_gauge.assert_awaited()


async def test_http_500_logs_warning_no_raise(scraper_fixture):
    scraper, metrics_store, _resources, reg_calls = scraper_fixture
    transport = httpx.MockTransport(lambda _req: httpx.Response(500, text="oh no"))
    async with httpx.AsyncClient(transport=transport) as client:
        written = await scraper.scrape_once(client)
    assert written == 0
    assert reg_calls["n"] == 0
    metrics_store.increment.assert_not_awaited()


async def test_idempotent_register_across_scrapes(scraper_fixture):
    scraper, _metrics_store, _resources, reg_calls = scraper_fixture
    transport = httpx.MockTransport(lambda _req: httpx.Response(200, text=_SAMPLE_METRICS))
    async with httpx.AsyncClient(transport=transport) as client:
        await scraper.scrape_once(client)
        first = reg_calls["n"]
        await scraper.scrape_once(client)
    # Second scrape reuses cached metric_ids → no further register calls.
    assert reg_calls["n"] == first


async def test_connection_error_is_swallowed(scraper_fixture):
    scraper, _metrics_store, _resources, _reg = scraper_fixture

    def _boom(_req):
        raise httpx.ConnectError("no route")

    transport = httpx.MockTransport(_boom)
    async with httpx.AsyncClient(transport=transport) as client:
        written = await scraper.scrape_once(client)
    assert written == 0
