"""
Tests for notify user preferences sub-feature.

Covers:
  Service:
    - list_preferences returns all 16 combos with defaults (all opted-in)
    - list_preferences reflects stored rows
    - critical category is always opted-in even if stored as False
    - upsert_preference stores opted-out state
    - upsert_preference silently forces critical to True
    - upsert_preference rejects unknown channel_code
    - upsert_preference rejects unknown category_code
    - is_opted_in returns True when no row (default)
    - is_opted_in returns stored value
    - is_opted_in always returns True for critical category

  HTTP:
    - GET /v1/notify/preferences requires auth (401)
    - GET /v1/notify/preferences returns 16 rows
    - PATCH /v1/notify/preferences requires auth (401)
    - PATCH /v1/notify/preferences updates preferences
    - PATCH /v1/notify/preferences cannot opt out of critical
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
_pref_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.09_preferences.service"
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

_ORG_ID  = "019e0000-7777-7000-0000-000000000010"
_USER_A  = "019e0000-7777-7000-0000-000000000011"


async def _noop_loop() -> None:
    try:
        await asyncio.sleep(10_000_000)
    except asyncio.CancelledError:
        pass


async def _cleanup_db(pool: Any) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "06_notify"."17_fct_notify_user_preferences" WHERE org_id = $1',
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
# Service-level tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_all_16_defaults(live_app):
    """list_preferences returns all 16 combos defaulting to is_opted_in=True."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        prefs = await _pref_svc.list_preferences(conn, user_id=_USER_A, org_id=_ORG_ID)

    assert len(prefs) == 16
    assert all(p["is_opted_in"] for p in prefs)


@pytest.mark.asyncio
async def test_list_reflects_stored_row(live_app):
    """Stored is_opted_in=False is returned for matching (channel, category)."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        # Opt out of marketing emails (channel=email/1, category=marketing/3)
        await _pref_svc.upsert_preference(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_code="email",
            category_code="marketing",
            is_opted_in=False,
            updated_by=_USER_A,
        )

    async with pool.acquire() as conn:
        prefs = await _pref_svc.list_preferences(conn, user_id=_USER_A, org_id=_ORG_ID)

    email_marketing = next(
        p for p in prefs if p["channel_code"] == "email" and p["category_code"] == "marketing"
    )
    assert email_marketing["is_opted_in"] is False
    # All others still True
    others = [p for p in prefs if p is not email_marketing]
    assert all(o["is_opted_in"] for o in others)


@pytest.mark.asyncio
async def test_critical_always_opted_in_in_list(live_app):
    """Even if critical row is stored as is_opted_in=False, list returns True."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        # Forcibly insert a False row for critical (bypassing service layer)
        _core_id: Any = import_module("backend.01_core.id")
        await conn.execute(
            'INSERT INTO "06_notify"."17_fct_notify_user_preferences" '
            '(id, org_id, user_id, channel_id, category_id, is_opted_in, created_by, updated_by) '
            'VALUES ($1, $2, $3, 1, 2, FALSE, $4, $4)',
            _core_id.uuid7(), _ORG_ID, _USER_A, _USER_A,
        )

    async with pool.acquire() as conn:
        prefs = await _pref_svc.list_preferences(conn, user_id=_USER_A, org_id=_ORG_ID)

    critical_rows = [p for p in prefs if p["category_code"] == "critical"]
    assert all(p["is_opted_in"] for p in critical_rows)
    assert all(p["is_locked"] for p in critical_rows)


@pytest.mark.asyncio
async def test_upsert_preference_stores_opt_out(live_app):
    """upsert_preference stores is_opted_in=False for non-critical."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        row = await _pref_svc.upsert_preference(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_code="webpush",
            category_code="digest",
            is_opted_in=False,
            updated_by=_USER_A,
        )

    assert row["is_opted_in"] is False
    assert row["channel_code"] == "webpush"
    assert row["category_code"] == "digest"
    assert row["is_locked"] is False


@pytest.mark.asyncio
async def test_upsert_critical_forced_to_true(live_app):
    """upsert_preference silently forces critical category to is_opted_in=True."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        row = await _pref_svc.upsert_preference(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_code="email",
            category_code="critical",
            is_opted_in=False,
            updated_by=_USER_A,
        )

    assert row["is_opted_in"] is True
    assert row["is_locked"] is True


@pytest.mark.asyncio
async def test_upsert_unknown_channel_raises(live_app):
    """upsert_preference raises ValidationError for unknown channel_code."""
    pool, _ = live_app
    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.ValidationError, match="unknown channel_code"):
            await _pref_svc.upsert_preference(
                conn,
                user_id=_USER_A,
                org_id=_ORG_ID,
                channel_code="carrier_pigeon",
                category_code="marketing",
                is_opted_in=False,
                updated_by=_USER_A,
            )


@pytest.mark.asyncio
async def test_upsert_unknown_category_raises(live_app):
    """upsert_preference raises ValidationError for unknown category_code."""
    pool, _ = live_app
    _errors: Any = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.ValidationError, match="unknown category_code"):
            await _pref_svc.upsert_preference(
                conn,
                user_id=_USER_A,
                org_id=_ORG_ID,
                channel_code="email",
                category_code="gossip",
                is_opted_in=True,
                updated_by=_USER_A,
            )


@pytest.mark.asyncio
async def test_is_opted_in_defaults_true_when_no_row(live_app):
    """is_opted_in returns True when no preference row exists."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        result = await _pref_svc.is_opted_in(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_id=1,  # email
            category_id=3,  # marketing
        )

    assert result is True


@pytest.mark.asyncio
async def test_is_opted_in_returns_stored_false(live_app):
    """is_opted_in returns False when stored."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        await _pref_svc.upsert_preference(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_code="in_app",
            category_code="marketing",
            is_opted_in=False,
            updated_by=_USER_A,
        )

    async with pool.acquire() as conn:
        result = await _pref_svc.is_opted_in(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_id=3,  # in_app
            category_id=3,  # marketing
        )

    assert result is False


@pytest.mark.asyncio
async def test_is_opted_in_always_true_for_critical(live_app):
    """is_opted_in always returns True for critical category, no DB hit needed."""
    pool, _ = live_app
    async with pool.acquire() as conn:
        result = await _pref_svc.is_opted_in(
            conn,
            user_id=_USER_A,
            org_id=_ORG_ID,
            channel_id=1,  # email
            category_id=2,  # critical
        )

    assert result is True


# ---------------------------------------------------------------------------
# HTTP-level tests
# ---------------------------------------------------------------------------

_FAKE_SESSION = {
    "id": "fake-session-pref",
    "user_id": _USER_A,
    "org_id": _ORG_ID,
    "workspace_id": None,
}


@pytest.mark.asyncio
async def test_get_preferences_requires_auth(live_app):
    """GET /v1/notify/preferences without session → 401."""
    _, client = live_app
    resp = await client.get(f"/v1/notify/preferences?org_id={_ORG_ID}")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_get_preferences_returns_16_rows(live_app):
    """GET /v1/notify/preferences returns 16 (channel × category) rows."""
    _, client = live_app
    with patch.object(_sessions_svc, "validate_token", return_value=_FAKE_SESSION):
        resp = await client.get(
            "/v1/notify/preferences",
            headers={"x-session-token": "fake"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert len(body["data"]) == 16
    # All default to opted-in
    assert all(row["is_opted_in"] for row in body["data"])
    # Critical rows are locked
    critical_rows = [r for r in body["data"] if r["category_code"] == "critical"]
    assert len(critical_rows) == 4
    assert all(r["is_locked"] for r in critical_rows)


@pytest.mark.asyncio
async def test_patch_preferences_requires_auth(live_app):
    """PATCH /v1/notify/preferences without session → 401."""
    _, client = live_app
    resp = await client.patch(
        "/v1/notify/preferences",
        json={"preferences": [{"channel_code": "email", "category_code": "marketing", "is_opted_in": False}]},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_patch_preferences_updates(live_app):
    """PATCH /v1/notify/preferences updates specified preferences."""
    _, client = live_app
    with patch.object(_sessions_svc, "validate_token", return_value=_FAKE_SESSION):
        resp = await client.patch(
            "/v1/notify/preferences",
            json={"preferences": [
                {"channel_code": "email", "category_code": "marketing", "is_opted_in": False},
                {"channel_code": "webpush", "category_code": "digest", "is_opted_in": False},
            ]},
            headers={"x-session-token": "fake"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    updated = body["data"]
    assert len(updated) == 2
    assert all(not r["is_opted_in"] for r in updated)


@pytest.mark.asyncio
async def test_patch_cannot_opt_out_of_critical(live_app):
    """PATCH with is_opted_in=False for critical forces it to True."""
    _, client = live_app
    with patch.object(_sessions_svc, "validate_token", return_value=_FAKE_SESSION):
        resp = await client.patch(
            "/v1/notify/preferences",
            json={"preferences": [
                {"channel_code": "email", "category_code": "critical", "is_opted_in": False},
            ]},
            headers={"x-session-token": "fake"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    row = body["data"][0]
    assert row["is_opted_in"] is True
    assert row["is_locked"] is True
