from __future__ import annotations

import httpx


async def test_increment(respx_mock, client):
    route = respx_mock.post("/v1/monitoring/metrics/http_requests_total/increment").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"accepted": True}})
    )
    await client.metrics.increment("http_requests_total", value=1, labels={"route": "/x"})
    body = route.calls[0].request.content
    assert b"route" in body


async def test_set_gauge(respx_mock, client):
    respx_mock.post("/v1/monitoring/metrics/queue_depth/set").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"accepted": True}})
    )
    await client.metrics.set("queue_depth", value=42)


async def test_observe_histogram(respx_mock, client):
    respx_mock.post("/v1/monitoring/metrics/latency_ms/observe").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"accepted": True}})
    )
    await client.metrics.observe("latency_ms", value=123.0, labels={"route": "/x"})


async def test_register(respx_mock, client):
    route = respx_mock.post("/v1/monitoring/metrics").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"id": 1, "key": "k"}})
    )
    await client.metrics.register(
        key="http_requests_total",
        kind="counter",
        description="count",
        cardinality_limit=1000,
    )
    assert b"counter" in route.calls[0].request.content


async def test_list_metrics(respx_mock, client):
    respx_mock.get("/v1/monitoring/metrics").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": [{"key": "a"}]})
    )
    rows = await client.metrics.list()
    assert len(rows) == 1


async def test_get_metric(respx_mock, client):
    respx_mock.get("/v1/monitoring/metrics/http").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"key": "http"}})
    )
    row = await client.metrics.get("http")
    assert row["key"] == "http"


async def test_query_metrics(respx_mock, client):
    respx_mock.post("/v1/monitoring/metrics/query").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"series": []}})
    )
    result = await client.metrics.query({"key": "http", "from": "t", "to": "t"})
    assert "series" in result
