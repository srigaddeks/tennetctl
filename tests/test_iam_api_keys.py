"""
Integration tests for iam.api_keys — Plan 14-01.

Covers: mint / list / revoke, token shape, argon2 hash storage, Bearer-auth
middleware populating request.state, revoked-key rejection, scope enforcement.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")

_TEST_PREFIX = "itest-apikey-"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email' AND a.key_text LIKE $1
            """,
            f"{_TEST_PREFIX}%",
        )
        uids = [r["user_id"] for r in rows]
        if uids:
            await conn.execute(
                'DELETE FROM "03_iam"."28_fct_iam_api_keys" WHERE user_id = ANY($1::text[])',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])',
                uids,
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


def _sys_ctx(pool: Any, conn: Any) -> Any:
    return _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        conn=conn,
        extras={"pool": pool},
    )


async def _make_user_and_session(pool: Any, suffix: str = "u1") -> tuple[dict, str]:
    """Create a user + session and return (user, session_token)."""
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        user = await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_PREFIX}{suffix}@example.com",
            display_name="API Key Test",
            account_type="email_password",
        )
    vault = _main.app.state.vault
    async with pool.acquire() as conn:
        token, _metadata = await _sessions_service.mint_session(
            conn, vault_client=vault,
            user_id=user["id"],
            org_id=None,
            workspace_id=None,
        )
    return user, token


@pytest.mark.asyncio
async def test_mint_returns_token_once_and_persists_hash(live_app):
    """POST /v1/api-keys returns the full token; DB stores only the argon2 hash."""
    client, pool = live_app
    _, session_token = await _make_user_and_session(pool)

    r = await client.post(
        "/v1/api-keys",
        json={"label": "CI bot", "scopes": ["notify:send"]},
        cookies={"tennetctl_session": session_token},
    )
    assert r.status_code == 201, r.text
    data = r.json()["data"]
    token: str = data["token"]
    assert token.startswith("nk_")
    assert "." in token[3:]
    assert data["label"] == "CI bot"
    assert data["scopes"] == ["notify:send"]

    # DB stores argon2id hash, not the plaintext.
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT secret_hash FROM "03_iam"."28_fct_iam_api_keys" WHERE id = $1',
            data["id"],
        )
    assert row is not None
    assert row["secret_hash"].startswith("$argon2id$")
    assert token.split(".", 1)[1] not in row["secret_hash"]


@pytest.mark.asyncio
async def test_bearer_auth_populates_request_state(live_app):
    """Valid Bearer nk_… auth: API-key-accepting endpoint sees state.user_id.

    /v1/auth/me requires state.session_id (set only by cookie auth), so we
    verify Bearer auth via /v1/notify/unread-count which needs only
    user_id + org_id — both populated by the Bearer middleware.
    """
    client, pool = live_app
    user, session_token = await _make_user_and_session(pool, suffix="u2")

    r = await client.post(
        "/v1/api-keys",
        json={"label": "bot2", "scopes": ["notify:send", "notify:read"]},
        cookies={"tennetctl_session": session_token},
    )
    token = r.json()["data"]["token"]

    # With the Bearer token, request.state is populated and the endpoint
    # honors ?recipient_user_id without explicit auth checks.
    r2 = await client.get(
        f"/v1/notify/unread-count?org_id={user['id']}&recipient_user_id={user['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text
    assert r2.json()["ok"] is True


@pytest.mark.asyncio
async def test_revoked_key_is_rejected(live_app):
    """DELETE /v1/api-keys/{id} revokes; subsequent Bearer calls are unauth'd.

    We verify via /v1/notify/send which requires notify:send scope. Before
    revoke it returns either 404 (template not found) or 403 (scope) — both
    indicate the key authenticated. After revoke it must return 401.
    """
    client, pool = live_app
    user, session_token = await _make_user_and_session(pool, suffix="u3")

    r = await client.post(
        "/v1/api-keys",
        json={"label": "revoke-me", "scopes": ["notify:send"]},
        cookies={"tennetctl_session": session_token},
    )
    data = r.json()["data"]
    token, key_row_id = data["token"], data["id"]

    # Sanity: before revoke, Bearer auth reaches the route. Template is
    # missing so the route raises NotFound — status 404 proves auth + scope
    # passed. A 401/403 here would mean the test is wrong.
    ok = await client.post(
        "/v1/notify/send",
        json={
            "org_id": user["id"],
            "template_key": "nope",
            "recipient_user_id": user["id"],
            "channel_code": "in_app",
            "variables": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert ok.status_code == 404, ok.text

    rev = await client.delete(
        f"/v1/api-keys/{key_row_id}",
        cookies={"tennetctl_session": session_token},
    )
    assert rev.status_code == 204

    # After revoke the middleware sees no valid auth and require_scope raises
    # UNAUTHORIZED.
    after = await client.post(
        "/v1/notify/send",
        json={
            "org_id": user["id"],
            "template_key": "nope",
            "recipient_user_id": user["id"],
            "channel_code": "in_app",
            "variables": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert after.status_code == 401


@pytest.mark.asyncio
async def test_scope_enforcement_on_notify_send(live_app):
    """An API key without notify:send scope gets 403 from POST /v1/notify/send."""
    client, pool = live_app
    user, session_token = await _make_user_and_session(pool, suffix="u4")

    # Ensure the session has an org_id so orgs propagate into the key.
    async with pool.acquire() as conn:
        org_row = await conn.fetchrow(
            'SELECT id FROM "03_iam"."10_fct_orgs" WHERE deleted_at IS NULL LIMIT 1'
        )
        if org_row:
            await conn.execute(
                """
                UPDATE "03_iam"."16_fct_sessions"
                SET org_id = $2 WHERE user_id = $1
                """,
                user["id"], org_row["id"],
            )

    r = await client.post(
        "/v1/api-keys",
        json={"label": "read-only", "scopes": ["notify:read"]},
        cookies={"tennetctl_session": session_token},
    )
    token = r.json()["data"]["token"]

    send = await client.post(
        "/v1/notify/send",
        json={
            "org_id": org_row["id"] if org_row else "00000000-0000-7000-0000-000000000000",
            "template_key": "does-not-matter",
            "recipient_user_id": user["id"],
            "channel_code": "in_app",
            "variables": {},
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert send.status_code == 403
    assert "notify:send" in send.text
