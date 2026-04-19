from __future__ import annotations

import httpx
import pytest


async def test_signin_stores_session_token(respx_mock, session_client):
    respx_mock.post("/v1/auth/signin").mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "data": {
                    "token": "sess_abc123",
                    "user": {"id": "u1", "email": "a@b.c"},
                    "session": {"id": "s1", "expires_at": "2099-01-01T00:00:00Z"},
                },
            },
        )
    )
    data = await session_client.auth.signin(email="a@b.c", password="pw")
    assert data["user"]["email"] == "a@b.c"
    assert session_client.session_token == "sess_abc123"


async def test_signin_reads_token_from_nested_session(respx_mock, session_client):
    respx_mock.post("/v1/auth/signin").mock(
        return_value=httpx.Response(
            200,
            json={
                "ok": True,
                "data": {"user": {"id": "u1"}, "session": {"id": "s1", "token": "nested_tok"}},
            },
        )
    )
    await session_client.auth.signin(email="a@b.c", password="pw")
    assert session_client.session_token == "nested_tok"


async def test_signout_clears_session_token(respx_mock, session_client):
    session_client._t.set_session_token("existing_tok")
    respx_mock.post("/v1/auth/signout").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"signed_out": True}})
    )
    await session_client.auth.signout()
    assert session_client.session_token is None


async def test_signout_clears_token_even_on_failure(respx_mock, session_client):
    session_client._t.set_session_token("tok")
    respx_mock.post("/v1/auth/signout").mock(
        return_value=httpx.Response(500, json={"ok": False, "error": {"code": "BOOM", "message": ""}})
    )
    with pytest.raises(Exception):
        await session_client.auth.signout()
    assert session_client.session_token is None


async def test_me_returns_user(respx_mock, client):
    respx_mock.get("/v1/auth/me").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "data": {"id": "u1", "email": "a@b.c", "display_name": "A"}}
        )
    )
    user = await client.auth.me()
    assert user["email"] == "a@b.c"


async def test_signup_stores_session_token(respx_mock, session_client):
    respx_mock.post("/v1/auth/signup").mock(
        return_value=httpx.Response(
            201,
            json={
                "ok": True,
                "data": {"token": "new_tok", "user": {"id": "u2"}, "session": {"id": "s2"}},
            },
        )
    )
    data = await session_client.auth.signup(email="x@y.z", password="pw", display_name="X")
    assert data["user"]["id"] == "u2"
    assert session_client.session_token == "new_tok"


# ---- sessions ---------------------------------------------------------------


async def test_sessions_list(respx_mock, client):
    respx_mock.get("/v1/sessions").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "data": [{"id": "s1"}, {"id": "s2"}]}
        )
    )
    result = await client.auth.sessions.list()
    assert len(result) == 2
    assert result[0]["id"] == "s1"


async def test_sessions_get(respx_mock, client):
    respx_mock.get("/v1/sessions/s1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"id": "s1", "ua": "test"}})
    )
    result = await client.auth.sessions.get("s1")
    assert result["id"] == "s1"


async def test_sessions_revoke(respx_mock, client):
    route = respx_mock.delete("/v1/sessions/s1").mock(return_value=httpx.Response(204))
    result = await client.auth.sessions.revoke("s1")
    assert result is None
    assert route.called


async def test_sessions_update(respx_mock, client):
    respx_mock.patch("/v1/sessions/s1").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": {"id": "s1", "label": "laptop"}})
    )
    result = await client.auth.sessions.update("s1", label="laptop")
    assert result["label"] == "laptop"


# ---- api keys ---------------------------------------------------------------


async def test_api_keys_list(respx_mock, client):
    respx_mock.get("/v1/api-keys").mock(
        return_value=httpx.Response(200, json={"ok": True, "data": [{"id": "k1"}]})
    )
    result = await client.auth.api_keys.list()
    assert len(result) == 1


async def test_api_keys_create_returns_one_time_token(respx_mock, client):
    route = respx_mock.post("/v1/api-keys").mock(
        return_value=httpx.Response(
            201,
            json={
                "ok": True,
                "data": {"id": "k1", "token": "nk_k1.secret", "name": "ci", "scopes": ["audit:read"]},
            },
        )
    )
    result = await client.auth.api_keys.create(name="ci", scopes=["audit:read"])
    assert result["token"] == "nk_k1.secret"
    body = route.calls[0].request.content
    assert b"ci" in body
    assert b"audit:read" in body


async def test_api_keys_create_with_expires_at(respx_mock, client):
    route = respx_mock.post("/v1/api-keys").mock(
        return_value=httpx.Response(201, json={"ok": True, "data": {"id": "k1", "token": "nk.x"}})
    )
    await client.auth.api_keys.create(name="ci", scopes=["s"], expires_at="2027-01-01T00:00:00Z")
    assert b"2027-01-01" in route.calls[0].request.content


async def test_api_keys_revoke(respx_mock, client):
    route = respx_mock.delete("/v1/api-keys/k1").mock(return_value=httpx.Response(204))
    result = await client.auth.api_keys.revoke("k1")
    assert result is None
    assert route.called


async def test_api_keys_rotate(respx_mock, client):
    respx_mock.post("/v1/api-keys/k1/rotate").mock(
        return_value=httpx.Response(
            200, json={"ok": True, "data": {"id": "k1", "token": "nk_k1.new"}}
        )
    )
    result = await client.auth.api_keys.rotate("k1")
    assert result["token"] == "nk_k1.new"
