"""
Tests for notify.email channel:
  - Email sending (mocked SMTP + MockVault)
  - Open tracking endpoint
  - Click tracking endpoint
  - Bounce webhook
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import Any
from unittest.mock import AsyncMock, patch

import aiosmtplib
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
_del_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.repository"
)
_del_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.06_deliveries.service"
)
_core_id: Any = import_module("backend.01_core.id")

_ORG_ID = "019e0000-5555-7000-0000-000000000001"
_TEST_USER_ID = "019e0000-5555-7000-0000-000000000002"
_TEST_USER_EMAIL = "emailtest@tennetctl.test"
_BASE_TRACKING_URL = "http://testserver"


class MockVault:
    """Returns a fixed password for any vault key."""
    async def get(self, key: str) -> str:
        return "test_smtp_password_secret"


async def _noop_loop() -> None:
    """No-op coroutine used to replace the background email sender in tests."""
    try:
        await asyncio.sleep(10_000_000)
    except asyncio.CancelledError:
        pass


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------

async def _cleanup_db(pool) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."61_evt_notify_delivery_events" '
            'WHERE delivery_id IN (SELECT id FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."15_fct_notify_deliveries" WHERE org_id = $1', _ORG_ID
        )
        await conn.execute(
            'DELETE FROM "06_notify"."14_fct_notify_subscriptions" WHERE org_id = $1', _ORG_ID
        )
        await conn.execute(
            'DELETE FROM "06_notify"."20_dtl_notify_template_bodies" '
            'WHERE template_id IN (SELECT id FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."13_fct_notify_template_variables" '
            'WHERE template_id IN (SELECT id FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1)',
            _ORG_ID,
        )
        await conn.execute(
            'DELETE FROM "06_notify"."12_fct_notify_templates" WHERE org_id = $1', _ORG_ID
        )
        await conn.execute(
            'DELETE FROM "06_notify"."11_fct_notify_template_groups" WHERE org_id = $1', _ORG_ID
        )
        await conn.execute(
            'DELETE FROM "06_notify"."10_fct_notify_smtp_configs" WHERE org_id = $1', _ORG_ID
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id = $1', _TEST_USER_ID
        )
        await conn.execute(
            'DELETE FROM "03_iam"."12_fct_users" WHERE id = $1', _TEST_USER_ID
        )


@pytest.fixture
async def live_app():
    """
    Start the full app lifespan with the background email sender suppressed.
    Yields (pool, AsyncClient).
    """
    # Patch background senders to no-ops so they can't race with tests
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

async def _insert_iam_user(conn) -> None:
    await conn.execute(
        """
        INSERT INTO "03_iam"."12_fct_users"
            (id, account_type_id, is_active, is_test, created_by, updated_by)
        VALUES ($1, 1, true, true, 'test', 'test')
        ON CONFLICT (id) DO NOTHING
        """,
        _TEST_USER_ID,
    )
    attr_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "03_iam"."21_dtl_attrs"
            (id, entity_type_id, entity_id, attr_def_id, key_text)
        VALUES ($1, 3, $2, 3, $3)
        ON CONFLICT (entity_type_id, entity_id, attr_def_id) DO NOTHING
        """,
        attr_id, _TEST_USER_ID, _TEST_USER_EMAIL,
    )


async def _insert_smtp_config(conn) -> dict:
    config_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."10_fct_notify_smtp_configs"
            (id, org_id, key, label, host, port, tls, username, auth_vault_key,
             created_by, updated_by)
        VALUES ($1, $2, 'test_smtp', 'Test SMTP', 'localhost', 1025, false,
                'sender@test.local', 'notify.smtp.test_password', 'test', 'test')
        """,
        config_id, _ORG_ID,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "06_notify"."v_notify_smtp_configs" WHERE id = $1', config_id
    )
    return dict(row)


async def _insert_template_group(conn, smtp_config_id: str | None = None) -> dict:
    group_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."11_fct_notify_template_groups"
            (id, org_id, key, label, category_id, smtp_config_id, created_by, updated_by)
        VALUES ($1, $2, 'test_group', 'Test Group', 1, $3, 'test', 'test')
        """,
        group_id, _ORG_ID, smtp_config_id,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "06_notify"."v_notify_template_groups" WHERE id = $1', group_id
    )
    return dict(row)


async def _insert_template_with_body(conn, group_id: str) -> dict:
    tmpl_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."12_fct_notify_templates"
            (id, org_id, key, group_id, subject, priority_id, created_by, updated_by)
        VALUES ($1, $2, 'test_email_tmpl', $3, 'Hello {{ name }}', 2, 'test', 'test')
        """,
        tmpl_id, _ORG_ID, group_id,
    )
    body_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."20_dtl_notify_template_bodies"
            (id, template_id, channel_id, body_html, body_text, preheader)
        VALUES ($1, $2, 1, '<p>Hello {{ name }}</p>', 'Hello {{ name }}', NULL)
        """,
        body_id, tmpl_id,
    )
    row = await conn.fetchrow(
        'SELECT * FROM "06_notify"."v_notify_templates" WHERE id = $1', tmpl_id
    )
    return dict(row)


async def _insert_email_delivery(
    conn, template_id: str, recipient: str = _TEST_USER_ID, status_id: int = 2
) -> dict:
    """Create a delivery row. status_id=2 means queued (default email send path)."""
    if status_id == 2:
        return await _del_svc.create_delivery(
            conn,
            subscription_id=None,
            org_id=_ORG_ID,
            template_id=template_id,
            recipient_user_id=recipient,
            channel_id=1,  # email
            priority_id=2,
            resolved_variables={"name": "Alice"},
        )
    delivery_id = _core_id.uuid7()
    await conn.execute(
        """
        INSERT INTO "06_notify"."15_fct_notify_deliveries"
            (id, org_id, template_id, recipient_user_id, channel_id,
             priority_id, status_id, resolved_variables)
        VALUES ($1, $2, $3, $4, 1, 2, $5, '{"name": "Alice"}')
        """,
        delivery_id, _ORG_ID, template_id, recipient, status_id,
    )
    return await _del_repo.get_delivery(conn, delivery_id)


# ---------------------------------------------------------------------------
# Unit tests: apply_email_tracking (pure Python, no DB)
# ---------------------------------------------------------------------------

def test_apply_email_tracking_adds_open_pixel():
    html = "<html><body><p>Hello</p></body></html>"
    tracked = _email_svc.apply_email_tracking(html, "del-001", _BASE_TRACKING_URL)
    assert "/v1/notify/email/track/o/" in tracked
    assert "<img" in tracked


def test_apply_email_tracking_wraps_links():
    html = '<html><body><a href="https://example.com">click</a></body></html>'
    tracked = _email_svc.apply_email_tracking(html, "del-002", _BASE_TRACKING_URL)
    assert "/v1/notify/email/track/c/" in tracked


# ---------------------------------------------------------------------------
# Integration tests: process_queued_email_deliveries (uses live_app pool)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_email_sent_updates_status_to_sent(live_app):
    """Successfully sending an email updates delivery status to 'sent'."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        await _insert_iam_user(conn)
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"])

    vault = MockVault()
    with patch.object(aiosmtplib, "send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = ({}, "250 OK")
        count = await _email_svc.process_queued_email_deliveries(
            pool, vault, _BASE_TRACKING_URL
        )

    assert count == 1
    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    assert d["status_code"] == "sent"
    assert d["delivered_at"] is not None


@pytest.mark.asyncio
async def test_email_send_failure_retries_then_fails(live_app):
    """SMTP error schedules retry; only marks 'failed' after max_attempts (3)."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        await _insert_iam_user(conn)
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"])

    vault = MockVault()
    with patch(
        "aiosmtplib.send",
        new_callable=AsyncMock,
        side_effect=Exception("Connection refused"),
    ):
        # First attempt → retry (status stays queued, next_retry_at set)
        count = await _email_svc.process_queued_email_deliveries(
            pool, vault, _BASE_TRACKING_URL
        )
        assert count == 0

    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    assert d["status_code"] == "queued"
    assert d["attempt_count"] == 1
    assert d["next_retry_at"] is not None
    assert "Connection refused" in (d["failure_reason"] or "")

    # Bypass backoff window to simulate retries 2 and 3.
    async with pool.acquire() as conn:
        await conn.execute(
            '''UPDATE "06_notify"."15_fct_notify_deliveries"
               SET next_retry_at = NULL WHERE id = $1''',
            delivery["id"],
        )
    with patch(
        "aiosmtplib.send",
        new_callable=AsyncMock,
        side_effect=Exception("Connection refused"),
    ):
        await _email_svc.process_queued_email_deliveries(pool, vault, _BASE_TRACKING_URL)

    async with pool.acquire() as conn:
        await conn.execute(
            '''UPDATE "06_notify"."15_fct_notify_deliveries"
               SET next_retry_at = NULL WHERE id = $1''',
            delivery["id"],
        )
    with patch(
        "aiosmtplib.send",
        new_callable=AsyncMock,
        side_effect=Exception("Connection refused"),
    ):
        await _email_svc.process_queued_email_deliveries(pool, vault, _BASE_TRACKING_URL)

    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    assert d["status_code"] == "failed"
    assert d["attempt_count"] == 3


@pytest.mark.asyncio
async def test_direct_email_address_as_recipient(live_app):
    """recipient_user_id containing '@' is used directly as the To address."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(
            conn, template["id"], recipient="direct@test.local"
        )

    vault = MockVault()
    captured: list = []

    async def _mock_send(msg, **kwargs):
        captured.append(msg)
        return {}, "250 OK"

    with patch.object(aiosmtplib, "send", side_effect=_mock_send):
        count = await _email_svc.process_queued_email_deliveries(
            pool, vault, _BASE_TRACKING_URL
        )

    assert count == 1
    assert captured[0]["To"] == "direct@test.local"


@pytest.mark.asyncio
async def test_no_smtp_config_schedules_retry(live_app):
    """Template group without smtp_config_id triggers the retryable error path."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        group = await _insert_template_group(conn, smtp_config_id=None)
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"])

    vault = MockVault()
    with patch.object(aiosmtplib, "send", new_callable=AsyncMock):
        count = await _email_svc.process_queued_email_deliveries(
            pool, vault, _BASE_TRACKING_URL
        )

    assert count == 0
    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    # First attempt leaves delivery queued with a scheduled retry.
    assert d["status_code"] == "queued"
    assert d["attempt_count"] == 1
    assert d["next_retry_at"] is not None


@pytest.mark.asyncio
async def test_non_email_deliveries_not_picked_up(live_app):
    """Email sender only claims channel=email (channel_id=1) deliveries."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        # webpush delivery (channel_id=2)
        webpush_id = _core_id.uuid7()
        await conn.execute(
            """
            INSERT INTO "06_notify"."15_fct_notify_deliveries"
                (id, org_id, template_id, recipient_user_id, channel_id,
                 priority_id, status_id, resolved_variables)
            VALUES ($1, $2, $3, $4, 2, 2, 2, '{}')
            """,
            webpush_id, _ORG_ID, template["id"], _TEST_USER_ID,
        )

    vault = MockVault()
    with patch.object(aiosmtplib, "send", new_callable=AsyncMock) as mock_send:
        count = await _email_svc.process_queued_email_deliveries(
            pool, vault, _BASE_TRACKING_URL
        )

    assert count == 0
    mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# Helpers: encode pytracking tokens
# ---------------------------------------------------------------------------

def _make_open_token(delivery_id: str) -> str:
    import pytracking
    config = pytracking.Configuration(
        base_open_tracking_url=f"{_BASE_TRACKING_URL}/v1/notify/email/track/o/",
    )
    full = config.get_open_tracking_url({"delivery_id": delivery_id})
    return full.replace(f"{_BASE_TRACKING_URL}/v1/notify/email/track/o/", "")


def _make_click_token(delivery_id: str, url: str) -> str:
    import pytracking
    config = pytracking.Configuration(
        base_click_tracking_url=f"{_BASE_TRACKING_URL}/v1/notify/email/track/c/",
    )
    full = config.get_click_tracking_url(url, {"delivery_id": delivery_id})
    return full.replace(f"{_BASE_TRACKING_URL}/v1/notify/email/track/c/", "")


# ---------------------------------------------------------------------------
# Integration tests: tracking + bounce webhook routes
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_open_tracking_creates_event(live_app):
    """GET /v1/notify/email/track/o/{token} → 1px GIF + creates open event."""
    pool, client = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"], status_id=3)

    token = _make_open_token(delivery["id"])
    resp = await client.get(f"/v1/notify/email/track/o/{token}")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/gif"

    async with pool.acquire() as conn:
        events = await conn.fetch(
            'SELECT event_type FROM "06_notify"."v_notify_delivery_events" WHERE delivery_id = $1',
            delivery["id"],
        )
    assert any(e["event_type"] == "open" for e in events)


@pytest.mark.asyncio
async def test_open_tracking_advances_status_to_opened(live_app):
    """Open tracking pixel advances delivery status from sent(3) → opened(5)."""
    pool, client = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"], status_id=3)

    token = _make_open_token(delivery["id"])
    await client.get(f"/v1/notify/email/track/o/{token}")

    async with pool.acquire() as conn:
        d = await _del_repo.get_delivery(conn, delivery["id"])
    assert d["status_code"] == "opened"


@pytest.mark.asyncio
async def test_click_tracking_redirects_and_creates_event(live_app):
    """GET /v1/notify/email/track/c/{token} → 302 redirect + click event."""
    pool, client = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"], status_id=3)

    original_url = "https://example.com/landing"
    token = _make_click_token(delivery["id"], original_url)
    resp = await client.get(
        f"/v1/notify/email/track/c/{token}", follow_redirects=False
    )
    assert resp.status_code == 302
    assert resp.headers["location"] == original_url

    async with pool.acquire() as conn:
        events = await conn.fetch(
            'SELECT event_type FROM "06_notify"."v_notify_delivery_events" WHERE delivery_id = $1',
            delivery["id"],
        )
    assert any(e["event_type"] == "click" for e in events)


@pytest.mark.asyncio
async def test_open_tracking_invalid_token_returns_gif(live_app):
    """Invalid open token still returns 200 GIF — never breaks email receipt."""
    _, client = live_app
    resp = await client.get("/v1/notify/email/track/o/INVALID_TOKEN_GARBAGE")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/gif"


@pytest.mark.asyncio
async def test_bounce_webhook_updates_status_to_bounced(live_app):
    """POST /v1/notify/email/webhooks/bounce → delivery status = 'bounced'."""
    pool, client = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"], status_id=3)

    resp = await client.post(
        "/v1/notify/email/webhooks/bounce",
        json={"delivery_id": delivery["id"], "reason": "550 mailbox not found"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["data"]["delivery"]["status_code"] == "bounced"


@pytest.mark.asyncio
async def test_bounce_webhook_creates_bounce_event(live_app):
    """Bounce webhook also creates a delivery_event of type='bounce'."""
    pool, client = live_app
    async with pool.acquire() as conn:
        smtp = await _insert_smtp_config(conn)
        group = await _insert_template_group(conn, smtp["id"])
        template = await _insert_template_with_body(conn, group["id"])
        delivery = await _insert_email_delivery(conn, template["id"], status_id=3)

    await client.post(
        "/v1/notify/email/webhooks/bounce",
        json={"delivery_id": delivery["id"], "reason": "mailbox full"},
    )
    async with pool.acquire() as conn:
        events = await conn.fetch(
            'SELECT event_type FROM "06_notify"."v_notify_delivery_events" WHERE delivery_id = $1',
            delivery["id"],
        )
    assert any(e["event_type"] == "bounce" for e in events)


@pytest.mark.asyncio
async def test_bounce_webhook_unknown_delivery_returns_404(live_app):
    """Bounce webhook returns 404 for an unknown delivery_id."""
    _, client = live_app
    resp = await client.post(
        "/v1/notify/email/webhooks/bounce",
        json={"delivery_id": "does-not-exist-00000000"},
    )
    assert resp.status_code == 404
