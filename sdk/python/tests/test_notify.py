from __future__ import annotations

import httpx


async def test_notify_send_posts_body(respx_mock, client):
    route = respx_mock.post("/v1/notify/send").mock(
        return_value=httpx.Response(
            201, json={"ok": True, "data": {"delivery_id": "d1", "status": "queued"}}
        )
    )
    result = await client.notify.send(
        template_key="password_reset",
        recipient_user_id="user:123",
        variables={"link": "https://x"},
    )
    assert result["delivery_id"] == "d1"
    body = route.calls[0].request.content
    assert b"password_reset" in body
    assert b"user:123" in body


async def test_notify_send_passes_idempotency_key(respx_mock, client):
    route = respx_mock.post("/v1/notify/send").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"delivery_id": "d2"}})
    )
    await client.notify.send(
        template_key="welcome",
        recipient_user_id="u1",
        idempotency_key="abc-123",
    )
    headers = route.calls[0].request.headers
    assert headers.get("idempotency-key") == "abc-123"


async def test_notify_send_channel_override(respx_mock, client):
    route = respx_mock.post("/v1/notify/send").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"delivery_id": "d3"}})
    )
    await client.notify.send(
        template_key="alert",
        recipient_user_id="u1",
        channel="webpush",
    )
    assert b"webpush" in route.calls[0].request.content


async def test_notify_send_omits_optional_fields(respx_mock, client):
    route = respx_mock.post("/v1/notify/send").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"delivery_id": "d4"}})
    )
    await client.notify.send(template_key="x", recipient_user_id="u1")
    body = route.calls[0].request.content
    assert b"variables" not in body
    assert b"channel" not in body
