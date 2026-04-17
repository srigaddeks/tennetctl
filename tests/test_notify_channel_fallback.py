"""
Channel fallback — Plan 17-01.

Template.fallback_chain creates scheduled deliveries on additional channels.
When the primary reaches opened/clicked, the fallback is marked superseded
instead of sent.
"""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_core_id: Any = import_module("backend.01_core.id")
_ctx_mod: Any = import_module("backend.01_catalog.context")
_users_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.03_users.service"
)
_sessions_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)
_groups_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.02_template_groups.repository"
)
_tmpl_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.03_templates.repository"
)
_email_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.07_email.service"
)

_TEST_PREFIX = "itest-fb-"


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
            await conn.execute('DELETE FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = ANY($1::text[])', uids)
            await conn.execute('DELETE FROM "06_notify"."12_fct_notify_templates" WHERE org_id = ANY($1::text[])', uids)
            await conn.execute('DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE org_id = ANY($1::text[])', uids)
            await conn.execute('DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])', uids)
            await conn.execute('DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])', uids)
            await conn.execute('DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])', uids)
            await conn.execute('DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])', uids)


def _sys_ctx(pool: Any, conn: Any) -> Any:
    return _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        conn=conn,
        extras={"pool": pool},
    )


async def _seed(pool: Any, suffix: str, fallback: list) -> tuple[str, str, str]:
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        user = await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_PREFIX}{suffix}@example.com",
            display_name="FB Test",
            account_type="email_password",
        )
    org_id = user["id"]
    async with pool.acquire() as conn:
        group_id = _core_id.uuid7()
        await _groups_repo.create_template_group(
            conn,
            group_id=group_id, org_id=org_id,
            key=f"fb-grp-{suffix}", label="FB",
            category_id=1, smtp_config_id=None,
            created_by=user["id"],
        )
        tmpl_id = _core_id.uuid7()
        await _tmpl_repo.create_template(
            conn,
            template_id=tmpl_id, org_id=org_id,
            key=f"fb-tmpl-{suffix}", group_id=group_id,
            subject="FB", reply_to=None, priority_id=2,
            created_by=user["id"],
        )
        await conn.execute(
            '''UPDATE "06_notify"."12_fct_notify_templates"
               SET fallback_chain = $2::jsonb WHERE id = $1''',
            tmpl_id, __import__("json").dumps(fallback),
        )
    vault = _main.app.state.vault
    async with pool.acquire() as conn:
        token, _m = await _sessions_service.mint_session(
            conn, vault_client=vault,
            user_id=user["id"], org_id=org_id, workspace_id=None,
        )
    return org_id, token, f"fb-tmpl-{suffix}"


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


@pytest.mark.asyncio
async def test_send_creates_primary_and_scheduled_fallback(live_app):
    """Template with fallback_chain → two delivery rows (primary + scheduled)."""
    client, pool = live_app
    org_id, token, tmpl = await _seed(pool, "a", [{"channel_id": 1, "wait_seconds": 60}])

    r = await client.post(
        "/v1/notify/send",
        json={
            "org_id": org_id, "template_key": tmpl,
            "recipient_user_id": org_id,
            "channel_code": "in_app", "variables": {},
        },
        cookies={"tennetctl_session": token},
    )
    assert r.status_code == 201

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            '''SELECT channel_id, scheduled_at FROM "06_notify"."15_fct_notify_deliveries"
               WHERE org_id = $1 ORDER BY channel_id''',
            org_id,
        )
    channels = {r["channel_id"] for r in rows}
    assert channels == {1, 3}  # in_app primary + email fallback
    email_row = next(r for r in rows if r["channel_id"] == 1)
    assert email_row["scheduled_at"] is not None


@pytest.mark.asyncio
async def test_fallback_skipped_when_primary_opened(live_app):
    """If the primary delivery has status 'opened', the fallback email is superseded."""
    client, pool = live_app
    org_id, token, tmpl = await _seed(pool, "b", [{"channel_id": 1, "wait_seconds": 1}])

    # Create deliveries via Send.
    await client.post(
        "/v1/notify/send",
        json={
            "org_id": org_id, "template_key": tmpl,
            "recipient_user_id": org_id,
            "channel_code": "in_app", "variables": {},
        },
        cookies={"tennetctl_session": token},
    )
    # Mark primary (in_app) as opened and fallback scheduled_at → now.
    async with pool.acquire() as conn:
        await conn.execute(
            '''UPDATE "06_notify"."15_fct_notify_deliveries"
               SET status_id = 5 WHERE org_id = $1 AND channel_id = 3''',
            org_id,
        )
        await conn.execute(
            '''UPDATE "06_notify"."15_fct_notify_deliveries"
               SET scheduled_at = CURRENT_TIMESTAMP - INTERVAL '1 minute'
               WHERE org_id = $1 AND channel_id = 1''',
            org_id,
        )
        fb_id = await conn.fetchval(
            '''SELECT id FROM "06_notify"."15_fct_notify_deliveries"
               WHERE org_id = $1 AND channel_id = 1''',
            org_id,
        )

    # Run the email sender loop; aiosmtplib.send must NOT be called.
    vault = _main.app.state.vault
    with patch("aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        await _email_svc.process_queued_email_deliveries(
            pool, vault, "http://localhost:51734"
        )

    mock_send.assert_not_awaited()
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            '''SELECT status_code, failure_reason FROM "06_notify"."v_notify_deliveries"
               WHERE id = $1''',
            fb_id,
        )
    assert row["status_code"] == "unsubscribed"
    assert row["failure_reason"] == "superseded_by_primary"
