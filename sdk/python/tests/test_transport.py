from __future__ import annotations

import httpx
import pytest

from tennetctl import (
    AuthError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TennetctlError,
    ValidationError,
)


# ---- envelope parsing -------------------------------------------------------


async def test_ok_envelope_returns_data(respx_mock, client):
    respx_mock.get("/v1/ping").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"pong": 1}})
    )
    result = await client._t.request("GET", "/v1/ping")
    assert result == {"pong": 1}


async def test_204_returns_none(respx_mock, client):
    respx_mock.delete("/v1/thing").mock(return_value=httpx.Response(204))
    assert await client._t.request("DELETE", "/v1/thing") is None


async def test_bearer_header_set(respx_mock, client):
    route = respx_mock.get("/v1/ping").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {}})
    )
    await client._t.request("GET", "/v1/ping")
    assert route.calls[0].request.headers["authorization"] == "Bearer nk_test.secret"


# ---- error mapping ----------------------------------------------------------


@pytest.mark.parametrize(
    "status,exc_type,code",
    [
        (400, ValidationError, "BAD"),
        (401, AuthError, "UNAUTH"),
        (403, AuthError, "FORBIDDEN"),
        (404, NotFoundError, "NOT_FOUND"),
        (409, ConflictError, "CONFLICT"),
        (422, ValidationError, "INVALID"),
        (429, RateLimitError, "LIMIT"),
        (500, ServerError, "BOOM"),
    ],
)
async def test_error_envelope_maps_to_typed_exception(respx_mock, client, status, exc_type, code):
    respx_mock.get("/v1/err").mock(
        return_value=httpx.Response(
            status, json={"ok": False, "error": {"code": code, "message": "nope"}}
        )
    )
    with pytest.raises(exc_type) as excinfo:
        await client._t.request("GET", "/v1/err")
    assert excinfo.value.code == code
    assert excinfo.value.status == status
    assert "nope" in excinfo.value.message


async def test_unmapped_status_falls_back_to_base_error(respx_mock, client):
    respx_mock.get("/v1/teapot").mock(
        return_value=httpx.Response(418, json={"ok": False, "error": {"code": "TEAPOT", "message": "short + stout"}})
    )
    with pytest.raises(TennetctlError) as excinfo:
        await client._t.request("GET", "/v1/teapot")
    # Should NOT be a subclass that we specifically map
    assert excinfo.value.code == "TEAPOT"
    assert excinfo.value.status == 418


async def test_non_envelope_error_body_still_raises(respx_mock, client):
    respx_mock.get("/v1/err").mock(return_value=httpx.Response(500, text="plain text boom"))
    with pytest.raises(ServerError) as excinfo:
        await client._t.request("GET", "/v1/err")
    assert excinfo.value.status == 500


# ---- retry policy -----------------------------------------------------------


async def test_retry_on_503_then_success(respx_mock, client, monkeypatch):
    # Patch sleep to zero so test is fast
    monkeypatch.setattr("tennetctl._transport.asyncio.sleep", _fast_sleep)
    route = respx_mock.get("/v1/flaky").mock(
        side_effect=[
            httpx.Response(503, json={"ok": False, "error": {"code": "UNAVAILABLE", "message": ""}}),
            httpx.Response(503, json={"ok": False, "error": {"code": "UNAVAILABLE", "message": ""}}),
            httpx.Response(200, json={"ok": True, "data": {"ok": True}}),
        ]
    )
    result = await client._t.request("GET", "/v1/flaky")
    assert result == {"ok": True}
    assert route.call_count == 3


async def test_retry_exhaustion_raises_server_error(respx_mock, client, monkeypatch):
    monkeypatch.setattr("tennetctl._transport.asyncio.sleep", _fast_sleep)
    route = respx_mock.get("/v1/down").mock(
        return_value=httpx.Response(503, json={"ok": False, "error": {"code": "DOWN", "message": ""}})
    )
    with pytest.raises(ServerError):
        await client._t.request("GET", "/v1/down")
    assert route.call_count == 4  # 1 + 3 retries


async def test_no_retry_on_400(respx_mock, client):
    route = respx_mock.post("/v1/bad").mock(
        return_value=httpx.Response(400, json={"ok": False, "error": {"code": "BAD", "message": "nope"}})
    )
    with pytest.raises(ValidationError):
        await client._t.request("POST", "/v1/bad", json={"x": 1})
    assert route.call_count == 1


async def test_network_error_raises_after_retries(respx_mock, client, monkeypatch):
    monkeypatch.setattr("tennetctl._transport.asyncio.sleep", _fast_sleep)
    respx_mock.get("/v1/netfail").mock(side_effect=httpx.ConnectError("boom"))
    with pytest.raises(NetworkError):
        await client._t.request("GET", "/v1/netfail")


# ---- session token management ----------------------------------------------


async def test_session_token_set_and_clear(respx_mock, session_client):
    assert session_client.session_token is None
    session_client._t.set_session_token("tok_abc")
    assert session_client.session_token == "tok_abc"
    session_client._t.set_session_token(None)
    assert session_client.session_token is None


# ---- helpers ---------------------------------------------------------------


async def _fast_sleep(_seconds: float) -> None:
    return None  # no-op; avoid monkeypatch recursion
