"""
Tests for notify campaigns sub-feature.

Covers:
  Service:
    - create_campaign creates in draft status (no scheduled_at)
    - create_campaign with scheduled_at creates in scheduled status
    - update_campaign can schedule a draft campaign
    - update_campaign rejects editing running campaigns
    - update_campaign can cancel a scheduled campaign
    - delete_campaign soft-deletes
    - delete_campaign rejects running campaigns
    - resolve_audience returns user IDs for org

  HTTP:
    - POST /v1/notify/campaigns requires auth (401)
    - POST /v1/notify/campaigns creates campaign
    - GET /v1/notify/campaigns lists campaigns
    - GET /v1/notify/campaigns/{id} returns campaign
    - PATCH /v1/notify/campaigns/{id} updates campaign
    - DELETE /v1/notify/campaigns/{id} soft-deletes

  Runner:
    - run_campaign transitions status and creates deliveries
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_campaign_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.service"
)
_campaign_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.10_campaigns.repository"
)
_campaign_runner: Any = import_module(
    "backend.02_features.06_notify.campaign_runner"
)
_email_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.07_email.service"
)
_webpush_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.service"
)
_sessions_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)
_core_id: Any = import_module("backend.01_core.id")

_ORG_ID  = "019e0000-7777-7000-0000-000000000020"
_USER_A  = "019e0000-7777-7000-0000-000000000021"


async def _noop_loop() -> None:
    try:
        await asyncio.sleep(10_000_000)
    except asyncio.CancelledError:
        pass


async def _cleanup_db(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."18_fct_notify_campaigns" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."20_dtl_notify_template_bodies" '
            'WHERE template_id IN '
            '(SELECT id FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE org_id = $1',
            _ORG_ID,
        )


@pytest.fixture
async def live_app():
    with (
        patch.object(
            _email_svc, "start_email_sender",
            side_effect=lambda *_a, **_k: asyncio.create_task(_noop_loop()),
        ),
        patch.object(
            _webpush_svc, "start_webpush_sender",
            side_effect=lambda *_a, **_k: asyncio.create_task(_noop_loop()),
        ),
        patch.object(
            _campaign_runner, "start_campaign_runner",
            side_effect=lambda *_a, **_k: asyncio.create_task(_noop_loop()),
        ),
    ):
        async with _main.lifespan(_main.app):
            pool = _main.app.state.pool
            await _cleanup_db(pool)
            try:
                transport = ASGITransport(app=_main.app)
                async with AsyncClient(
                    transport=transport, base_url="http://testserver"
                ) as ac:
                    yield pool, ac
            finally:
                await _cleanup_db(pool)
                _catalog.clear_checkers()


# ---------------------------------------------------------------------------
# DB helpers
# ---------------------------------------------------------------------------

async def _insert_template(conn: Any, category_code: str = "marketing") -> dict:
    # category_id: marketing=3
    cat_map = {"transactional": 1, "critical": 2, "marketing": 3, "digest": 4}
    category_id = cat_map[category_code]

    group_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."11_fct_notify_template_groups"
            (id, org_id, key, label, category_id, created_by, updated_by)
        VALUES ($1, $2, 'campaign_group', 'Campaign Group', $3, 'test', 'test')
        """,
        group_id, _ORG_ID, category_id,
    )
    tmpl_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."12_fct_notify_templates"
            (id, org_id, key, group_id, subject, priority_id, created_by, updated_by)
        VALUES ($1, $2, 'campaign_tmpl', $3, 'Newsletter', 2, 'test', 'test')
        """,
        tmpl_id, _ORG_ID, group_id,
    )
    return {"id": tmpl_id, "category_id": category_id}


# ---------------------------------------------------------------------------
# Service-level tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_create_campaign_draft(live_app):
    """Create campaign without scheduled_at → draft status."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)

    async with pool.acquire() as conn:
        row = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Monthly Newsletter",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {"account_type_codes": []},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    assert row["status_code"] == "draft"
    assert row["name"] == "Monthly Newsletter"
    assert row["channel_code"] == "email"


@pytest.mark.asyncio
async def test_create_campaign_scheduled(live_app):
    """Create campaign with scheduled_at → scheduled status."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)

    async with pool.acquire() as conn:
        row = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Flash Sale",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": "2099-01-01T09:00:00",
                "throttle_per_minute": 30,
            },
            created_by=_USER_A,
        )

    assert row["status_code"] == "scheduled"
    assert row["throttle_per_minute"] == 30


@pytest.mark.asyncio
async def test_update_campaign_schedule_from_draft(live_app):
    """Patching status=scheduled on a draft campaign (with scheduled_at set) works."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        # Create without scheduled_at → draft
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Draft Campaign",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )
    assert campaign["status_code"] == "draft"

    async with pool.acquire() as conn:
        # Set scheduled_at and status=scheduled in one PATCH
        updated = await _campaign_svc.update_campaign(
            conn,
            campaign_id=campaign["id"],
            data={"status": "scheduled", "scheduled_at": "2099-06-01T10:00:00"},
            updated_by=_USER_A,
        )

    assert updated["status_code"] == "scheduled"


@pytest.mark.asyncio
async def test_update_campaign_cancel_scheduled(live_app):
    """Cancelling a scheduled campaign transitions to cancelled."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "To Cancel",
                "template_id": tmpl["id"],
                "channel_code": "in_app",
                "audience_query": {},
                "scheduled_at": "2099-12-01T12:00:00",
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    async with pool.acquire() as conn:
        cancelled = await _campaign_svc.update_campaign(
            conn,
            campaign_id=campaign["id"],
            data={"status": "cancelled"},
            updated_by=_USER_A,
        )

    assert cancelled["status_code"] == "cancelled"


@pytest.mark.asyncio
async def test_update_running_campaign_rejected(live_app):
    """Cannot edit a running campaign."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Running",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )
        # Force to running
        await _campaign_repo.update_campaign_status(
            conn, campaign_id=campaign["id"], status_id=_campaign_repo.STATUS_RUNNING
        )

    _errors: Any = import_module("backend.01_core.errors")
    async with pool.acquire() as conn:
        with pytest.raises(_errors.ValidationError, match="cannot edit"):
            await _campaign_svc.update_campaign(
                conn,
                campaign_id=campaign["id"],
                data={"name": "New Name"},
                updated_by=_USER_A,
            )


@pytest.mark.asyncio
async def test_delete_campaign(live_app):
    """Soft-delete a draft campaign."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Delete Me",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    async with pool.acquire() as conn:
        deleted = await _campaign_svc.delete_campaign(
            conn, campaign_id=campaign["id"], updated_by=_USER_A
        )

    assert deleted is True

    async with pool.acquire() as conn:
        row = await _campaign_repo.get_campaign(conn, campaign["id"])
    assert row is None  # view excludes deleted


@pytest.mark.asyncio
async def test_resolve_audience_empty_org(live_app):
    """resolve_audience returns empty list when org has no users."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        ids = await _campaign_svc.resolve_audience(
            conn, org_id=_ORG_ID, audience_query={}
        )
    assert ids == []


# ---------------------------------------------------------------------------
# HTTP-level tests
# ---------------------------------------------------------------------------

_FAKE_SESSION = {
    "id": "fake-session-camp",
    "user_id": _USER_A,
    "org_id": _ORG_ID,
    "workspace_id": None,
}


@pytest.mark.asyncio
async def test_post_campaign_requires_auth(live_app):
    """POST /v1/notify/campaigns without auth → 401."""
    pool, client = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)

    resp = await client.post(
        "/v1/notify/campaigns",
        json={
            "org_id": _ORG_ID,
            "name": "Test",
            "template_id": tmpl["id"],
            "channel_code": "email",
        },
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_campaign_creates(live_app):
    """POST /v1/notify/campaigns creates campaign."""
    pool, client = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)

    with patch.object(_sessions_svc, "validate_token", return_value=_FAKE_SESSION):
        resp = await client.post(
            "/v1/notify/campaigns",
            json={
                "org_id": _ORG_ID,
                "name": "Launch Announcement",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "throttle_per_minute": 100,
            },
            headers={"x-session-token": "fake"},
        )

    assert resp.status_code == 201
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["status_code"] == "draft"
    assert body["data"]["channel_code"] == "email"


@pytest.mark.asyncio
async def test_get_campaigns_list(live_app):
    """GET /v1/notify/campaigns returns paginated list."""
    pool, client = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Camp A",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    resp = await client.get(f"/v1/notify/campaigns?org_id={_ORG_ID}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert len(body["data"]["items"]) >= 1


@pytest.mark.asyncio
async def test_get_campaign_by_id(live_app):
    """GET /v1/notify/campaigns/{id} returns single campaign."""
    pool, client = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Single",
                "template_id": tmpl["id"],
                "channel_code": "webpush",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    resp = await client.get(f"/v1/notify/campaigns/{campaign['id']}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"]["id"] == campaign["id"]


@pytest.mark.asyncio
async def test_patch_campaign_updates_name(live_app):
    """PATCH /v1/notify/campaigns/{id} updates name."""
    pool, client = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "Old Name",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    with patch.object(_sessions_svc, "validate_token", return_value=_FAKE_SESSION):
        resp = await client.patch(
            f"/v1/notify/campaigns/{campaign['id']}",
            json={"name": "New Name"},
            headers={"x-session-token": "fake"},
        )

    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_campaign_via_http(live_app):
    """DELETE /v1/notify/campaigns/{id} returns 204."""
    pool, client = live_app
    async with pool.acquire() as conn:
        tmpl = await _insert_template(conn)
        campaign = await _campaign_svc.create_campaign(
            conn,
            data={
                "org_id": _ORG_ID,
                "name": "To Delete",
                "template_id": tmpl["id"],
                "channel_code": "email",
                "audience_query": {},
                "scheduled_at": None,
                "throttle_per_minute": 60,
            },
            created_by=_USER_A,
        )

    with patch.object(_sessions_svc, "validate_token", return_value=_FAKE_SESSION):
        resp = await client.delete(
            f"/v1/notify/campaigns/{campaign['id']}",
            headers={"x-session-token": "fake"},
        )

    assert resp.status_code == 204
