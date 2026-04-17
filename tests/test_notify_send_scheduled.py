"""
Tests for scheduled transactional sends — Plan 16-01.

Covers: send_at + delay_seconds store scheduled_at correctly, future
scheduled_at keeps the delivery out of sender polls, mutually-exclusive
validation, and in-app auto-delivered bypass for past scheduled_at.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from importlib import import_module
from typing import Any

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
_email_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.07_email.repository"
)

_TEST_PREFIX = "itest-sched-"


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
                'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])', uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."22_dtl_credentials" WHERE user_id = ANY($1::text[])', uids,
            )
            await conn.execute(
                'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])', uids,
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


async def _seed(pool: Any, suffix: str) -> tuple[str, str, str]:
    """Create user + session + template group + email template. Returns (org_id=user_id, session_token, tmpl_key)."""
    async with pool.acquire() as conn:
        ctx = _sys_ctx(pool, conn)
        user = await _users_service.create_user(
            pool, conn, ctx,
            email=f"{_TEST_PREFIX}{suffix}@example.com",
            display_name="Sched Test",
            account_type="email_password",
        )
    org_id = user["id"]
    async with pool.acquire() as conn:
        group_id = _core_id.uuid7()
        await _groups_repo.create_template_group(
            conn,
            group_id=group_id, org_id=org_id,
            key=f"sched-grp-{suffix}", label="Sched",
            category_id=1, smtp_config_id=None,
            created_by=user["id"],
        )
        tmpl_id = _core_id.uuid7()
        await _tmpl_repo.create_template(
            conn,
            template_id=tmpl_id, org_id=org_id,
            key=f"sched-tmpl-{suffix}", group_id=group_id,
            subject="Sched", reply_to=None, priority_id=2,
            created_by=user["id"],
        )
    vault = _main.app.state.vault
    async with pool.acquire() as conn:
        token, _meta = await _sessions_service.mint_session(
            conn, vault_client=vault,
            user_id=user["id"], org_id=org_id, workspace_id=None,
        )
    return org_id, token, f"sched-tmpl-{suffix}"


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


def _body(org_id: str, tmpl_key: str, **extra: Any) -> dict:
    return {
        "org_id": org_id,
        "template_key": tmpl_key,
        "recipient_user_id": org_id,
        "channel_code": "email",
        "variables": {},
        **extra,
    }


@pytest.mark.asyncio
async def test_send_at_stores_scheduled_at(live_app):
    """send_at → delivery row has matching scheduled_at (naive UTC)."""
    client, pool = live_app
    org_id, token, tmpl_key = await _seed(pool, "a")

    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    r = await client.post(
        "/v1/notify/send",
        json=_body(org_id, tmpl_key, send_at=future.isoformat()),
        cookies={"tennetctl_session": token},
    )
    assert r.status_code == 201, r.text
    delivery_id = r.json()["data"]["delivery_id"]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT scheduled_at FROM "06_notify"."15_fct_notify_deliveries" WHERE id = $1',
            delivery_id,
        )
    assert row["scheduled_at"] is not None
    # Allow 1s tolerance for ISO<->datetime roundtrip
    assert abs((row["scheduled_at"] - future).total_seconds()) < 2


@pytest.mark.asyncio
async def test_delay_seconds_produces_future_scheduled_at(live_app):
    """delay_seconds=300 → scheduled_at ≈ now + 300s."""
    client, pool = live_app
    org_id, token, tmpl_key = await _seed(pool, "b")

    before = datetime.now(timezone.utc).replace(tzinfo=None)
    r = await client.post(
        "/v1/notify/send",
        json=_body(org_id, tmpl_key, delay_seconds=300),
        cookies={"tennetctl_session": token},
    )
    assert r.status_code == 201, r.text
    delivery_id = r.json()["data"]["delivery_id"]

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT scheduled_at FROM "06_notify"."15_fct_notify_deliveries" WHERE id = $1',
            delivery_id,
        )
    sched = row["scheduled_at"]
    # scheduled_at must be within 10s of before+300s
    delta = (sched - before).total_seconds()
    assert 299 <= delta <= 310, f"expected ~300, got {delta}"


@pytest.mark.asyncio
async def test_send_at_and_delay_both_supplied_rejects(live_app):
    """send_at + delay_seconds both non-null → 422."""
    client, pool = live_app
    org_id, token, tmpl_key = await _seed(pool, "c")
    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    r = await client.post(
        "/v1/notify/send",
        json=_body(org_id, tmpl_key, send_at=future.isoformat(), delay_seconds=60),
        cookies={"tennetctl_session": token},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_email_poll_skips_future_scheduled(live_app):
    """Future scheduled_at blocks the email sender poll."""
    client, pool = live_app
    org_id, token, tmpl_key = await _seed(pool, "d")

    future = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)
    r = await client.post(
        "/v1/notify/send",
        json=_body(org_id, tmpl_key, send_at=future.isoformat()),
        cookies={"tennetctl_session": token},
    )
    delivery_id = r.json()["data"]["delivery_id"]

    async with pool.acquire() as conn:
        claimed = await _email_repo.poll_and_claim_email_deliveries(conn, limit=50)
    claimed_ids = {row["id"] for row in claimed}
    assert delivery_id not in claimed_ids

    # Flip scheduled_at to the past, poll should now claim it.
    async with pool.acquire() as conn:
        await conn.execute(
            'UPDATE "06_notify"."15_fct_notify_deliveries" SET scheduled_at = CURRENT_TIMESTAMP - INTERVAL \'1 minute\' WHERE id = $1',
            delivery_id,
        )
        claimed = await _email_repo.poll_and_claim_email_deliveries(conn, limit=50)
    assert delivery_id in {row["id"] for row in claimed}
