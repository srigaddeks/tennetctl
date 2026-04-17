"""
Tests for PATCH /v1/notify/deliveries/{delivery_id} (mark-read for in-app).

Covers:
  - Mark in-app delivery as read: status advances to 'opened', event created
  - Idempotent: re-marking already-opened delivery is a no-op
  - Forbidden: different user cannot mark read
  - Channel guard: non-in_app deliveries rejected
  - Auth guard: unauthenticated request → 401
  - Status guard: unsupported status value → 422
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
_email_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.07_email.service"
)
_webpush_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.service"
)
_del_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.service"
)
_del_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_sessions_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.09_sessions.service"
)
_core_id: Any = import_module("backend.01_core.id")

_ORG_ID = "019e0000-7777-7000-0000-000000000001"
_USER_A = "019e0000-7777-7000-0000-000000000002"
_USER_B = "019e0000-7777-7000-0000-000000000003"
_FAKE_SESSION_TOKEN = "test-session-token-for-patch-tests"


async def _noop_loop() -> None:
    try:
        await asyncio.sleep(10_000_000)
    except asyncio.CancelledError:
        pass


async def _cleanup_db(pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."61_evt_notify_delivery_events" '
            'WHERE delivery_id IN '
            '(SELECT id FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1',
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

async def _insert_template(conn) -> dict:
    group_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."11_fct_notify_template_groups"
            (id, org_id, key, label, category_id, created_by, updated_by)
        VALUES ($1, $2, 'in_app_group', 'In-App Group', 1, 'test', 'test')
        """,
        group_id, _ORG_ID,
    )
    tmpl_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."12_fct_notify_templates"
            (id, org_id, key, group_id, subject, priority_id, created_by, updated_by)
        VALUES ($1, $2, 'in_app_tmpl', $3, 'Alert', 2, 'test', 'test')
        """,
        tmpl_id, _ORG_ID, group_id,
    )
    body_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."20_dtl_notify_template_bodies"
            (id, template_id, channel_id, body_html, body_text)
        VALUES ($1, $2, 3, '<p>Alert</p>', 'Alert')
        """,
        body_id, tmpl_id,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "06_notify"."v_notify_templates" WHERE id = $1', tmpl_id
    )
    return dict(row)


async def _insert_in_app_delivery(
    conn, template_id: str, recipient_user_id: str = _USER_A, status_id: int = 3
) -> dict:
    delivery_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."15_fct_notify_deliveries"
            (id, org_id, template_id, recipient_user_id, channel_id,
             priority_id, status_id, resolved_variables)
        VALUES ($1, $2, $3, $4, 3, 2, $5, '{"title": "Test Alert"}')
        """,
        delivery_id, _ORG_ID, template_id, recipient_user_id, status_id,
    )
    row = await _del_repo.get_delivery(conn, delivery_id)
    return row


async def _insert_email_delivery(conn, template_id: str) -> dict:
    delivery_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."15_fct_notify_deliveries"
            (id, org_id, template_id, recipient_user_id, channel_id,
             priority_id, status_id, resolved_variables)
        VALUES ($1, $2, $3, $4, 1, 2, 3, '{}')
        """,
        delivery_id, _ORG_ID, template_id, _USER_A,
    )
    return await _del_repo.get_delivery(conn, delivery_id)


# ---------------------------------------------------------------------------
# Service-level tests (no HTTP — faster + less setup)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_mark_in_app_read_advances_to_opened(live_app):
    """mark_in_app_read updates status to 'opened' and creates an open event."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_in_app_delivery(conn, template["id"], status_id=3)

    async with pool.acquire() as conn:
        updated = await _del_svc.mark_in_app_read(
            conn, delivery_id=delivery["id"], user_id=_USER_A
        )
        events = await conn.fetch(
            'SELECT event_type FROM "06_notify"."v_notify_delivery_events" '
            'WHERE delivery_id = $1',
            delivery["id"],
        )

    assert updated["status_code"] == "opened"
    assert any(e["event_type"] == "open" for e in events)


@pytest.mark.asyncio
async def test_mark_in_app_read_is_idempotent(live_app):
    """Calling mark_in_app_read twice does not create duplicate events."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_in_app_delivery(conn, template["id"], status_id=3)

    async with pool.acquire() as conn:
        await _del_svc.mark_in_app_read(
            conn, delivery_id=delivery["id"], user_id=_USER_A
        )

    async with pool.acquire() as conn:
        result = await _del_svc.mark_in_app_read(
            conn, delivery_id=delivery["id"], user_id=_USER_A
        )
        events = await conn.fetch(
            'SELECT event_type FROM "06_notify"."v_notify_delivery_events" '
            'WHERE delivery_id = $1',
            delivery["id"],
        )

    assert result["status_code"] == "opened"
    open_events = [e for e in events if e["event_type"] == "open"]
    assert len(open_events) == 1  # not duplicated


@pytest.mark.asyncio
async def test_mark_in_app_read_forbidden_for_other_user(live_app):
    """Different user cannot mark another user's delivery as read."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_in_app_delivery(conn, template["id"])

    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.ForbiddenError):
            await _del_svc.mark_in_app_read(
                conn, delivery_id=delivery["id"], user_id=_USER_B
            )


@pytest.mark.asyncio
async def test_mark_read_rejected_for_email_delivery(live_app):
    """mark_in_app_read raises ValidationError for non-in_app deliveries."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        email_delivery = await _insert_email_delivery(conn, template["id"])

    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.ValidationError):
            await _del_svc.mark_in_app_read(
                conn, delivery_id=email_delivery["id"], user_id=_USER_A
            )


@pytest.mark.asyncio
async def test_mark_read_not_found(live_app):
    """mark_in_app_read raises NotFoundError for unknown delivery_id."""
    pool, _ = live_app
    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.NotFoundError):
            await _del_svc.mark_in_app_read(
                conn, delivery_id="00000000-0000-0000-0000-000000000000", user_id=_USER_A
            )


# ---------------------------------------------------------------------------
# HTTP-level tests (auth via request.state injection via middleware mock)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_patch_delivery_requires_auth(live_app):
    """PATCH without session token → 401."""
    pool, client = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_in_app_delivery(conn, template["id"])

    resp = await client.patch(
        f"/v1/notify/deliveries/{delivery['id']}",
        json={"status": "opened"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_patch_delivery_unsupported_status(live_app):
    """PATCH with unsupported status → 422. Auth via mocked validate_token."""
    pool, client = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_in_app_delivery(conn, template["id"])

    # Patch the session validator to return a fake session for our user
    fake_session = {
        "id": "fake-session-id",
        "user_id": _USER_A,
        "org_id": _ORG_ID,
        "workspace_id": None,
    }
    with patch.object(_sessions_svc, "validate_token", return_value=fake_session):
        resp = await client.patch(
            f"/v1/notify/deliveries/{delivery['id']}",
            json={"status": "deleted"},
            headers={"x-session-token": "fake-token"},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_patch_delivery_mark_read_via_http(live_app):
    """PATCH /v1/notify/deliveries/{id} with status=opened marks delivery as read."""
    pool, client = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_in_app_delivery(conn, template["id"], status_id=3)

    fake_session = {
        "id": "fake-session-id",
        "user_id": _USER_A,
        "org_id": _ORG_ID,
        "workspace_id": None,
    }
    with patch.object(_sessions_svc, "validate_token", return_value=fake_session):
        resp = await client.patch(
            f"/v1/notify/deliveries/{delivery['id']}",
            json={"status": "opened"},
            headers={"x-session-token": "fake-token"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["status_code"] == "opened"


@pytest.mark.asyncio
async def test_list_deliveries_channel_filter(live_app):
    """GET /v1/notify/deliveries?channel=in_app filters to in-app only."""
    pool, client = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        await _insert_in_app_delivery(conn, template["id"])
        await _insert_email_delivery(conn, template["id"])

    resp = await client.get(
        f"/v1/notify/deliveries?org_id={_ORG_ID}&channel=in_app"
    )
    assert resp.status_code == 200
    body = resp.json()
    assert all(d["channel_code"] == "in_app" for d in body["data"]["items"])
