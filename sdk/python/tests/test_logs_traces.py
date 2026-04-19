from __future__ import annotations

import httpx


async def test_logs_emit_otlp(respx_mock, client):
    route = respx_mock.post("/v1/monitoring/otlp/v1/logs").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"partialSuccess": {}}})
    )
    await client.logs.emit(
        severity="INFO",
        body="hello",
        attributes={"user_id": "u1", "count": 3, "ok": True},
        service_name="my-service",
    )
    body = route.calls[0].request.content
    assert b"resourceLogs" in body
    assert b"my-service" in body
    assert b"hello" in body


async def test_logs_query(respx_mock, client):
    respx_mock.post("/v1/monitoring/logs/query").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"logs": []}})
    )
    result = await client.logs.query({"severity": "INFO"})
    assert "logs" in result


async def test_logs_tail(respx_mock, client):
    respx_mock.get("/v1/monitoring/logs/tail").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"logs": []}})
    )
    result = await client.logs.tail(severity="ERROR")
    assert "logs" in result


async def test_traces_emit(respx_mock, client):
    respx_mock.post("/v1/monitoring/otlp/v1/traces").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"partialSuccess": {}}})
    )
    await client.traces.emit_batch([
        {
            "resource": {"attributes": []},
            "scopeSpans": [{"spans": [{"traceId": "t1", "spanId": "s1", "name": "op"}]}],
        }
    ])


async def test_traces_get(respx_mock, client):
    respx_mock.get("/v1/monitoring/traces/t1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"trace_id": "t1", "spans": []}})
    )
    trace = await client.traces.get("t1")
    assert trace["trace_id"] == "t1"


async def test_traces_query(respx_mock, client):
    respx_mock.post("/v1/monitoring/traces/query").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"traces": []}})
    )
    result = await client.traces.query({"service": "x"})
    assert "traces" in result
