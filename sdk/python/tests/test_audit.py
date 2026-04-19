from __future__ import annotations

import httpx


async def test_audit_has_no_emit_method(client):
    assert not hasattr(client.audit, "emit")
    assert not hasattr(client.audit.events, "emit")


async def test_audit_events_list(respx_mock, client):
    respx_mock.get("/v1/audit-events").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "data": {"events": [{"id": "e1"}], "cursor": None}}
        )
    )
    data = await client.audit.events.list(category="iam", limit=10)
    assert data["events"][0]["id"] == "e1"


async def test_audit_events_get(respx_mock, client):
    respx_mock.get("/v1/audit-events/e1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"id": "e1", "key": "x"}})
    )
    evt = await client.audit.events.get("e1")
    assert evt["id"] == "e1"


async def test_audit_events_stats(respx_mock, client):
    respx_mock.get("/v1/audit-events/stats").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"total": 42}})
    )
    stats = await client.audit.events.stats()
    assert stats["total"] == 42


async def test_audit_events_tail(respx_mock, client):
    respx_mock.get("/v1/audit-events/tail").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"events": []}})
    )
    out = await client.audit.events.tail(category="iam")
    assert "events" in out


async def test_audit_events_funnel(respx_mock, client):
    route = respx_mock.post("/v1/audit-events/funnel").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"steps": []}})
    )
    await client.audit.events.funnel({"steps": [{"key": "a"}, {"key": "b"}]})
    assert route.called


async def test_audit_event_keys(respx_mock, client):
    respx_mock.get("/v1/audit-event-keys").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "data": [{"key": "iam.user.signed_in"}]}
        )
    )
    keys = await client.audit.events.event_keys()
    assert keys[0]["key"] == "iam.user.signed_in"


async def test_audit_events_outbox_cursor(respx_mock, client):
    respx_mock.get("/v1/audit-events/outbox-cursor").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"cursor": "c1"}})
    )
    c = await client.audit.events.outbox_cursor()
    assert c["cursor"] == "c1"


async def test_audit_events_retention(respx_mock, client):
    respx_mock.get("/v1/audit-events/retention").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"days": 90}})
    )
    r = await client.audit.events.retention()
    assert r["days"] == 90
