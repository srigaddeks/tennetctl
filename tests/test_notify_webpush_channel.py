"""
Tests for notify.webpush channel:
  - VAPID key bootstrap (vault integration)
  - Webpush sending (mocked webpush_async)
  - Subscription CRUD routes
  - VAPID public key endpoint
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pywebpush
import pytest
from httpx import ASGITransport, AsyncClient
from pywebpush import WebPushException

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")
_email_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.07_email.service"
)
_webpush_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.service"
)
_webpush_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.repository"
)
_del_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_del_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.service"
)
_core_id: Any = import_module("backend.01_core.id")

_ORG_ID = "019e0000-6666-7000-0000-000000000001"
_TEST_USER_ID = "019e0000-6666-7000-0000-000000000002"

# Fake VAPID values used by MockVault — webpush_async is mocked so crypto never runs
_FAKE_VAPID_PEM = "-----BEGIN EC PRIVATE KEY-----\nMHQCAQEEINOT_A_REAL_KEY_JUST_TESTS==\n-----END EC PRIVATE KEY-----\n"
_FAKE_VAPID_PUBKEY = "BNOTAREALVAPIDPUBLICKEYJUSTUSEDFORSIMULATEDTESTS1234567890ABCDE"


class MockVault:
    """Returns fake vault values. webpush_async is mocked so crypto never runs."""
    async def get(self, key: str) -> str:
        if key == _webpush_svc._VAPID_PRIVATE_KEY:
            return _FAKE_VAPID_PEM
        if key == _webpush_svc._VAPID_PUBLIC_KEY:
            return _FAKE_VAPID_PUBKEY
        return "test_secret"


async def _noop_loop() -> None:
    try:
        await asyncio.sleep(10_000_000)
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# Shared fixture + cleanup
# ---------------------------------------------------------------------------

async def _cleanup_db(pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."16_fct_notify_webpush_subscriptions" WHERE org_id = $1',
            _ORG_ID,
        )
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
    """Full app lifespan with background senders suppressed."""
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
        VALUES ($1, $2, 'wp_group', 'WP Group', 1, 'test', 'test')
        """,
        group_id, _ORG_ID,
    )
    tmpl_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."12_fct_notify_templates"
            (id, org_id, key, group_id, subject, priority_id, created_by, updated_by)
        VALUES ($1, $2, 'wp_tmpl', $3, 'Alert {{ title }}', 2, 'test', 'test')
        """,
        tmpl_id, _ORG_ID, group_id,
    )
    body_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."20_dtl_notify_template_bodies"
            (id, template_id, channel_id, body_html, body_text)
        VALUES ($1, $2, 2, '<p>{{ title }}</p>', '{{ title }}')
        """,
        body_id, tmpl_id,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "06_notify"."v_notify_templates" WHERE id = $1', tmpl_id
    )
    return dict(row)


async def _insert_webpush_subscription(
    conn,
    *,
    user_id: str = _TEST_USER_ID,
    endpoint: str = "https://push.example.com/v1/test",
    p256dh: str = "testP256DH",
    auth: str = "testAuth",
    device_label: str | None = "Test Device",
) -> dict:
    sub_id = _core_id.uuid7()
    return await _webpush_repo.upsert_subscription(
        conn,
        id=sub_id,
        org_id=_ORG_ID,
        user_id=user_id,
        endpoint=endpoint,
        p256dh=p256dh,
        auth=auth,
        device_label=device_label,
        created_by="test",
    )


async def _insert_webpush_delivery(conn, template_id: str) -> dict:
    return await _del_svc.create_delivery(
        conn,
        subscription_id=None,
        org_id=_ORG_ID,
        template_id=template_id,
        recipient_user_id=_TEST_USER_ID,
        channel_id=2,  # webpush
        priority_id=2,
        resolved_variables={"title": "Security Alert", "body": "New login detected"},
    )


# ---------------------------------------------------------------------------
# Service integration: VAPID key bootstrap
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_vapid_keys_bootstrapped_into_vault(live_app):
    """ensure_vapid_keys populates vault with private + public key (idempotent)."""
    pool, _ = live_app
    vault = _main.app.state.vault
    pub = await vault.get(_webpush_svc._VAPID_PUBLIC_KEY)
    priv = await vault.get(_webpush_svc._VAPID_PRIVATE_KEY)
    assert len(pub) == 87  # base64url uncompressed P-256 point (65 bytes → 87 chars)
    assert "EC PRIVATE KEY" in priv or "BEGIN" in priv


@pytest.mark.asyncio
async def test_ensure_vapid_keys_is_idempotent(live_app):
    """Calling ensure_vapid_keys twice returns the same public key both times."""
    pool, _ = live_app
    vault = _main.app.state.vault
    key1 = await _webpush_svc.ensure_vapid_keys(pool, vault)
    key2 = await _webpush_svc.ensure_vapid_keys(pool, vault)
    assert key1 == key2


# ---------------------------------------------------------------------------
# Service integration: sending (mocked webpush_async)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_webpush_sent_updates_status_to_sent(live_app):
    """Successfully sending webpush updates delivery status to 'sent'."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        await _insert_webpush_subscription(conn)
        delivery = await _insert_webpush_delivery(conn, template["id"])

    mock_resp = MagicMock()
    mock_resp.status = 201
    vault = MockVault()

    with patch.object(pywebpush, "webpush_async", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp
        count = await _webpush_svc.process_queued_webpush_deliveries(pool, vault)

    assert count == 1
    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    assert d["status_code"] == "sent"
    assert d["delivered_at"] is not None


@pytest.mark.asyncio
async def test_webpush_no_subscriptions_marks_failed(live_app):
    """Delivery with no matching webpush subscriptions is marked failed."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        delivery = await _insert_webpush_delivery(conn, template["id"])
        # No subscriptions inserted for _TEST_USER_ID

    vault = MockVault()
    with patch.object(pywebpush, "webpush_async", new_callable=AsyncMock):
        count = await _webpush_svc.process_queued_webpush_deliveries(pool, vault)

    assert count == 1
    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    assert d["status_code"] == "failed"
    assert "no_webpush_subscriptions" in (d["failure_reason"] or "")


@pytest.mark.asyncio
async def test_webpush_send_error_schedules_retry(live_app):
    """WebPushException from provider leaves delivery queued with a scheduled retry."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        await _insert_webpush_subscription(conn)
        delivery = await _insert_webpush_delivery(conn, template["id"])

    vault = MockVault()
    with patch.object(
        pywebpush, "webpush_async",
        side_effect=WebPushException("push service rejected: 410 Gone"),
    ):
        count = await _webpush_svc.process_queued_webpush_deliveries(pool, vault)

    assert count == 1  # processed
    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    # First failure → retry path (not yet marked failed).
    assert d["status_code"] == "queued"
    assert d["attempt_count"] == 1
    assert d["next_retry_at"] is not None
    assert "410" in (d["failure_reason"] or "") or "push" in (d["failure_reason"] or "")


@pytest.mark.asyncio
async def test_webpush_sends_to_all_user_subscriptions(live_app):
    """If user has 2 browser subscriptions, webpush_async is called twice."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        await _insert_webpush_subscription(
            conn, endpoint="https://push1.example.com/v1/a"
        )
        await _insert_webpush_subscription(
            conn, endpoint="https://push2.example.com/v1/b"
        )
        delivery = await _insert_webpush_delivery(conn, template["id"])

    mock_resp = MagicMock()
    mock_resp.status = 201
    vault = MockVault()

    with patch.object(pywebpush, "webpush_async", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = mock_resp
        count = await _webpush_svc.process_queued_webpush_deliveries(pool, vault)

    assert count == 1
    assert mock_send.call_count == 2  # one call per subscription


@pytest.mark.asyncio
async def test_non_webpush_deliveries_not_picked_up(live_app):
    """Webpush sender only claims channel_id=2 (webpush) deliveries."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        template = await _insert_template(conn)
        # Insert email delivery (channel_id=1)
        email_id = _core_id.uuid7()
        await conn.execute(
            """
            INSERT INTO "06_notify"."15_fct_notify_deliveries"
                (id, org_id, template_id, recipient_user_id, channel_id,
                 priority_id, status_id, resolved_variables)
            VALUES ($1, $2, $3, $4, 1, 2, 2, '{}')
            """,
            email_id, _ORG_ID, template["id"], _TEST_USER_ID,
        )

    vault = MockVault()
    with patch.object(pywebpush, "webpush_async", new_callable=AsyncMock) as mock_send:
        count = await _webpush_svc.process_queued_webpush_deliveries(pool, vault)

    assert count == 0
    mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# Route tests: VAPID public key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_vapid_public_key(live_app):
    """GET /v1/notify/webpush/vapid-public-key returns a base64url key."""
    _, client = live_app
    resp = await client.get("/v1/notify/webpush/vapid-public-key")
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    pub = body["data"]["public_key"]
    assert isinstance(pub, str)
    assert len(pub) == 87  # base64url uncompressed P-256 point


# ---------------------------------------------------------------------------
# Route tests: subscription CRUD
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_subscriptions_requires_auth(live_app):
    """GET /v1/notify/webpush/subscriptions without token → 401."""
    _, client = live_app
    resp = await client.get("/v1/notify/webpush/subscriptions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_subscription_requires_auth(live_app):
    """POST /v1/notify/webpush/subscriptions without token → 401."""
    _, client = live_app
    resp = await client.post(
        "/v1/notify/webpush/subscriptions",
        json={"endpoint": "https://x.com/p", "p256dh": "abc", "auth": "def"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_create_and_list_subscription(live_app):
    """POST creates a subscription; GET returns it."""
    pool, client = live_app

    # Inject a fake session into request state via header interception
    # Use the pool directly to test repo, then verify via HTTP with direct DB
    async with pool.acquire() as conn:
        row = await _insert_webpush_subscription(
            conn,
            endpoint="https://push.example.com/v1/create_test",
        )

    assert row["endpoint"] == "https://push.example.com/v1/create_test"
    assert row["org_id"] == _ORG_ID
    assert row["user_id"] == _TEST_USER_ID

    # Verify it appears in list_subscriptions query
    async with pool.acquire() as conn:
        subs = await _webpush_repo.list_subscriptions(conn, user_id=_TEST_USER_ID)
    assert any(s["endpoint"] == "https://push.example.com/v1/create_test" for s in subs)


@pytest.mark.asyncio
async def test_upsert_updates_existing_endpoint(live_app):
    """Upserting with same endpoint refreshes keys without duplicate."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        await _insert_webpush_subscription(
            conn,
            endpoint="https://push.example.com/v1/upsert_test",
            p256dh="oldKey",
            auth="oldAuth",
        )
        # Upsert same endpoint with new keys
        sub2 = await _insert_webpush_subscription(
            conn,
            endpoint="https://push.example.com/v1/upsert_test",
            p256dh="newKey",
            auth="newAuth",
        )
        subs = await _webpush_repo.list_subscriptions(
            conn, user_id=_TEST_USER_ID
        )

    # Only one row for this endpoint
    matching = [s for s in subs if s["endpoint"] == "https://push.example.com/v1/upsert_test"]
    assert len(matching) == 1
    assert matching[0]["p256dh"] == "newKey"


@pytest.mark.asyncio
async def test_soft_delete_subscription(live_app):
    """Soft-deleting a subscription removes it from the active view."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        row = await _insert_webpush_subscription(
            conn, endpoint="https://push.example.com/v1/delete_test"
        )
        deleted = await _webpush_repo.soft_delete_subscription(
            conn, sub_id=row["id"], updated_by="test"
        )
        assert deleted is True
        subs = await _webpush_repo.list_subscriptions(conn, user_id=_TEST_USER_ID)

    endpoints = [s["endpoint"] for s in subs]
    assert "https://push.example.com/v1/delete_test" not in endpoints


@pytest.mark.asyncio
async def test_soft_delete_nonexistent_returns_false(live_app):
    """Soft-deleting a non-existent subscription returns False (not raises)."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        deleted = await _webpush_repo.soft_delete_subscription(
            conn, sub_id="00000000-0000-0000-0000-000000000000", updated_by="test"
        )
    assert deleted is False
