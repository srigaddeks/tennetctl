"""
Idempotency tests for POST /v1/notify/send — Plan 14-01.

Covers: same Idempotency-Key returns same delivery_id, one row, one audit
event. Different keys create separate deliveries. No header → no uniqueness
constraint applied (new delivery every time).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_core_id: Any = import_module("backend.01_core.id")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)
_ctx_mod: Any = import_module("backend.01_catalog.context")
_groups_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.02_template_groups.repository"
)
_tmpl_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.repository"
)

_TEST_KEY = "itest-idem-tmpl"
_TEST_EMAIL_PREFIX = "itest-idem-"


async def _cleanup(pool: Any) -> None:
    async with pool.acquire() as conn:
        # Find users created by this test (and their deliveries/audit).
        rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND d.code = 'email' AND a.key_text LIKE $1
            """,
            f"{_TEST_EMAIL_PREFIX}%",
        )
        uids = [r["user_id"] for r in rows]
        if uids:
            await conn.execute(
                '''DELETE FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = ANY($1::text[])''',
                uids,
            )
            await conn.execute(
                '''DELETE FROM "06_notify"."12_fct_notify_templates" WHERE org_id = ANY($1::text[])''',
                uids,
            )
            await conn.execute(
                '''DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE org_id = ANY($1::text[])''',
                uids,
            )
            await conn.execute(
                '''DELETE FROM "04_audit"."60_evt_audit" WHERE actor_user_id = ANY($1::text[])''',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])', uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])', uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."40_lnk_user_orgs" WHERE user_id = ANY($1::text[])', uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
                uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])', uids,
            )


def _sys_ctx(pool: Any, conn: Any) -> Any:
    return _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        conn=conn,
        extras={"pool": pool},
    )


async def _seed(pool: Any, suffix: str = "a") -> tuple[str, str, str]:
    """Create a user, session, template group + template.

    Returns (user_id, session_token, template_key). Uses the user's own uuid
    as the org_id (same pattern as api-keys test — valid for users without
    an explicit org).
    """
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        user = await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_EMAIL_PREFIX}{suffix}@example.com",
            display_name="Idem Test",
            account_type="email_password",
        )
    org_id = user["id"]  # user is their own org for this test

    async with pool.acquire() as conn:
        group_id = _core_id.uuid7()
        await _groups_repo.create_template_group(
            conn,
            group_id=group_id,
            org_id=org_id,
            key=f"idem-grp-{suffix}",
            label="Idem Group",
            category_id=1,
            smtp_config_id=None,
            created_by=user["id"],
        )
        template_id = _core_id.uuid7()
        await _tmpl_repo.create_template(
            conn,
            template_id=template_id,
            org_id=org_id,
            key=f"{_TEST_KEY}-{suffix}",
            group_id=group_id,
            subject="Idem subject",
            reply_to=None,
            priority_id=2,
            created_by=user["id"],
        )

    vault = _main.app.state.vault
    async with pool.acquire() as conn:
        token, _meta = await _sessions_service.mint_session(
            conn, vault_client=vault,
            user_id=user["id"], org_id=org_id, workspace_id=None,
        )
    return user["id"], token, f"{_TEST_KEY}-{suffix}"


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


async def _count(pool: Any, org_id: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            '''SELECT COUNT(*) FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1''',
            org_id,
        ) or 0


async def _audit_count(pool: Any, user_id: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            '''SELECT COUNT(*) FROM "04_audit"."60_evt_audit"
               WHERE event_key = 'notify.send.transactional' AND actor_user_id = $1''',
            user_id,
        ) or 0


def _body(template_key: str, org_id: str, user_id: str) -> dict:
    return {
        "org_id": org_id,
        "template_key": template_key,
        "recipient_user_id": user_id,
        "channel_code": "in_app",
        "variables": {"subject": "idem-test"},
    }


async def _send(client: Any, body: dict, token: str, key: str | None = None) -> Any:
    headers: dict[str, str] = {}
    if key is not None:
        headers["Idempotency-Key"] = key
    return await client.post(
        "/v1/notify/send",
        json=body,
        headers=headers,
        cookies={"tennetctl_session": token},
    )


@pytest.mark.asyncio
async def test_same_idempotency_key_returns_same_delivery(live_app):
    """Two calls with identical Idempotency-Key → same delivery_id, one row, one audit."""
    client, pool = live_app
    user_id, token, tmpl_key = await _seed(pool, "a")

    r1 = await _send(client, _body(tmpl_key, user_id, user_id), token, key="dup-key-1")
    assert r1.status_code == 201, r1.text
    d1 = r1.json()["data"]

    r2 = await _send(client, _body(tmpl_key, user_id, user_id), token, key="dup-key-1")
    assert r2.status_code == 201, r2.text
    d2 = r2.json()["data"]

    assert d1["delivery_id"] == d2["delivery_id"]
    assert d1["idempotent_replay"] is False
    assert d2["idempotent_replay"] is True
    assert await _count(pool, user_id) == 1
    assert await _audit_count(pool, user_id) == 1


@pytest.mark.asyncio
async def test_different_keys_create_separate_deliveries(live_app):
    """Distinct Idempotency-Key values → two rows, two audit events."""
    client, pool = live_app
    user_id, token, tmpl_key = await _seed(pool, "b")

    r1 = await _send(client, _body(tmpl_key, user_id, user_id), token, key="k-A")
    r2 = await _send(client, _body(tmpl_key, user_id, user_id), token, key="k-B")
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["data"]["delivery_id"] != r2.json()["data"]["delivery_id"]
    assert await _count(pool, user_id) == 2
    assert await _audit_count(pool, user_id) == 2


@pytest.mark.asyncio
async def test_no_idempotency_key_always_new_delivery(live_app):
    """Two calls with no Idempotency-Key header → two rows."""
    client, pool = live_app
    user_id, token, tmpl_key = await _seed(pool, "c")

    r1 = await _send(client, _body(tmpl_key, user_id, user_id), token)
    r2 = await _send(client, _body(tmpl_key, user_id, user_id), token)
    assert r1.status_code == r2.status_code == 201
    assert r1.json()["data"]["delivery_id"] != r2.json()["data"]["delivery_id"]
    assert await _count(pool, user_id) == 2
