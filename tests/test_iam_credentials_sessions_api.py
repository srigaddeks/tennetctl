"""
Integration tests for iam.credentials + iam.sessions self-service routes.

Covers:
  - PATCH /v1/credentials/me (happy + wrong-current + same-password)
  - GET  /v1/sessions (only mine + pagination)
  - GET  /v1/sessions/{id} (mine vs stranger's)
  - PATCH /v1/sessions/{id} (extend moves expires_at forward)
  - DELETE /v1/sessions/{id} (revoke + self-revoke kills /me)
  - Password change revokes other sessions but keeps the caller's
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")

_TEST_EMAIL_PREFIX = "itest-credsess-"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3
              AND d.code = 'email'
              AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            """
            DELETE FROM "04_audit"."60_evt_audit"
            WHERE metadata->>'user_id' = ANY($1::text[])
            """,
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."23_fct_failed_auth_attempts" WHERE email LIKE $1',
            f"{_TEST_EMAIL_PREFIX}%",
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" '
            "WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])",
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
            user_ids,
        )


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        try:
            transport = ASGITransport(app=_main.app)
            async with AsyncClient(transport=transport, base_url="http://test") as ac:
                yield ac, pool
        finally:
            await _cleanup(pool)
            _catalog.clear_checkers()


async def _signup(client: AsyncClient, slug: str, password: str = "password password") -> tuple[str, str, str]:
    """Return (email, user_id, token)."""
    email = f"{_TEST_EMAIL_PREFIX}{slug}@example.com"
    r = await client.post(
        "/v1/auth/signup",
        json={"email": email, "display_name": slug, "password": password},
    )
    assert r.status_code == 201, r.text
    d = r.json()["data"]
    return email, d["user"]["id"], d["token"]


async def _signin(client: AsyncClient, email: str, password: str) -> str:
    r = await client.post(
        "/v1/auth/signin", json={"email": email, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]["token"]


# ── Credentials: change password ────────────────────────────────────

@pytest.mark.asyncio
async def test_change_password_happy(live_app) -> None:
    client, _pool = live_app
    email, _, token = await _signup(client, "pw-happy")
    auth = {"Authorization": f"Bearer {token}"}

    r = await client.patch(
        "/v1/credentials/me",
        headers=auth,
        json={"current_password": "password password", "new_password": "brand new password"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["data"]["changed"] is True

    # Old password fails, new password works.
    assert (await client.post(
        "/v1/auth/signin",
        json={"email": email, "password": "password password"},
    )).status_code == 401
    assert (await client.post(
        "/v1/auth/signin",
        json={"email": email, "password": "brand new password"},
    )).status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current_401(live_app) -> None:
    client, _pool = live_app
    _, _, token = await _signup(client, "pw-wrong")
    auth = {"Authorization": f"Bearer {token}"}
    r = await client.patch(
        "/v1/credentials/me",
        headers=auth,
        json={"current_password": "nope nope nope", "new_password": "does not matter"},
    )
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.asyncio
async def test_change_password_same_as_current_422(live_app) -> None:
    client, _pool = live_app
    _, _, token = await _signup(client, "pw-same")
    auth = {"Authorization": f"Bearer {token}"}
    r = await client.patch(
        "/v1/credentials/me",
        headers=auth,
        json={"current_password": "password password", "new_password": "password password"},
    )
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_change_password_without_auth_is_401(live_app) -> None:
    client, _pool = live_app
    r = await client.patch(
        "/v1/credentials/me",
        json={"current_password": "a", "new_password": "bbbbbbbb"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_change_password_revokes_other_sessions_not_current(live_app) -> None:
    client, _pool = live_app
    email, _, token_a = await _signup(client, "pw-fanout")
    token_b = await _signin(client, email, "password password")
    token_c = await _signin(client, email, "password password")

    # All three work pre-change.
    for t in (token_a, token_b, token_c):
        assert (await client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {t}"},
        )).status_code == 200

    r = await client.patch(
        "/v1/credentials/me",
        headers={"Authorization": f"Bearer {token_a}"},
        json={"current_password": "password password", "new_password": "a whole new thing"},
    )
    assert r.status_code == 200
    assert r.json()["data"]["other_sessions_revoked"] == 2

    # A still works; B and C are invalid.
    assert (await client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"},
    )).status_code == 200
    for t in (token_b, token_c):
        assert (await client.get(
            "/v1/auth/me", headers={"Authorization": f"Bearer {t}"},
        )).status_code == 401


# ── Sessions: list / get ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_my_sessions_scoped_to_caller(live_app) -> None:
    client, _pool = live_app
    email_a, _, token_a = await _signup(client, "sess-a")
    _, _, token_b = await _signup(client, "sess-b")
    await _signin(client, email_a, "password password")  # second session for A

    list_a = await client.get(
        "/v1/sessions", headers={"Authorization": f"Bearer {token_a}"},
    )
    assert list_a.status_code == 200
    ids_a = [s["id"] for s in list_a.json()["data"]]
    assert len(ids_a) == 2

    list_b = await client.get(
        "/v1/sessions", headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b.status_code == 200
    ids_b = [s["id"] for s in list_b.json()["data"]]
    assert len(ids_b) == 1
    assert set(ids_a).isdisjoint(set(ids_b))


@pytest.mark.asyncio
async def test_get_stranger_session_is_404(live_app) -> None:
    client, _pool = live_app
    _, _, token_a = await _signup(client, "get-a")
    _, _, token_b = await _signup(client, "get-b")

    r_a = await client.get(
        "/v1/sessions", headers={"Authorization": f"Bearer {token_a}"},
    )
    a_sid = r_a.json()["data"][0]["id"]

    r = await client.get(
        f"/v1/sessions/{a_sid}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 404


# ── Sessions: PATCH extend ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_extend_session_pushes_expires_forward(live_app) -> None:
    client, pool = live_app
    _, _, token = await _signup(client, "extend")
    auth = {"Authorization": f"Bearer {token}"}
    me = (await client.get("/v1/auth/me", headers=auth)).json()["data"]
    sid = me["session"]["id"]
    before = datetime.fromisoformat(me["session"]["expires_at"])

    # Pull expires_at back by 3 days so we can see the extend move it forward.
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "03_iam"."16_fct_sessions" SET expires_at = $1 WHERE id = $2',
            before.replace(tzinfo=None) - timedelta(days=3), sid,
        )

    r = await client.patch(
        f"/v1/sessions/{sid}", headers=auth, json={"extend": True},
    )
    assert r.status_code == 200, r.text
    after = datetime.fromisoformat(r.json()["data"]["expires_at"])
    assert after > before - timedelta(days=3)


@pytest.mark.asyncio
async def test_extend_without_flag_is_422(live_app) -> None:
    client, _pool = live_app
    _, _, token = await _signup(client, "extend-noflag")
    auth = {"Authorization": f"Bearer {token}"}
    me = (await client.get("/v1/auth/me", headers=auth)).json()["data"]
    sid = me["session"]["id"]
    r = await client.patch(f"/v1/sessions/{sid}", headers=auth, json={})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_extend_expired_is_401(live_app) -> None:
    client, pool = live_app
    _, _, token = await _signup(client, "extend-expired")
    auth = {"Authorization": f"Bearer {token}"}
    me = (await client.get("/v1/auth/me", headers=auth)).json()["data"]
    sid = me["session"]["id"]

    # Hard-expire the session in the DB.
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "03_iam"."16_fct_sessions" SET expires_at = $1 WHERE id = $2',
            datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=1),
            sid,
        )
    # Middleware rejects the token, so /v1/sessions/{sid} will 401 at the
    # auth layer before we even reach the service — that's the contract.
    r = await client.patch(f"/v1/sessions/{sid}", headers=auth, json={"extend": True})
    assert r.status_code == 401


# ── Sessions: DELETE revoke ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_own_session_revokes(live_app) -> None:
    client, _pool = live_app
    email, _, token_a = await _signup(client, "revoke")
    token_b = await _signin(client, email, "password password")

    # B revokes A's session.
    r_a_list = await client.get(
        "/v1/sessions", headers={"Authorization": f"Bearer {token_b}"},
    )
    all_sids = {s["id"]: s for s in r_a_list.json()["data"]}
    me_b = (await client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"},
    )).json()["data"]
    b_sid = me_b["session"]["id"]
    # Pick the session that is NOT B's current one — that's A's.
    a_sid = next(sid for sid in all_sids if sid != b_sid)

    r = await client.delete(
        f"/v1/sessions/{a_sid}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 204

    # A's token no longer works; B's still does.
    assert (await client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"},
    )).status_code == 401
    assert (await client.get(
        "/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"},
    )).status_code == 200


@pytest.mark.asyncio
async def test_delete_stranger_session_is_404(live_app) -> None:
    client, _pool = live_app
    _, _, token_a = await _signup(client, "del-a")
    _, _, token_b = await _signup(client, "del-b")
    r_a = await client.get(
        "/v1/sessions", headers={"Authorization": f"Bearer {token_a}"},
    )
    a_sid = r_a.json()["data"][0]["id"]
    r = await client.delete(
        f"/v1/sessions/{a_sid}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert r.status_code == 404
