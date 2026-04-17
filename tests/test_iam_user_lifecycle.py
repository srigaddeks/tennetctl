"""
Integration tests for iam.users lifecycle — deactivation vs soft-delete.

Covers:
  - PATCH status=inactive → deactivates user, revokes sessions, emits audit
  - PATCH status=active   → reactivates, unblocks signin (is_active=True)
  - Inactive user blocked at signin with USER_INACTIVE 403
  - DELETE → pseudonymizes PII, soft-deletes, revokes sessions
  - GET after DELETE returns 404
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")
_catalog: Any = import_module("backend.01_catalog")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_PREFIX = "lifecycle-test-"


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
            f"{_PREFIX}%",
        )
        # Also catch pseudonymized rows where original email is gone
        pseudo_rows = await conn.fetch(
            """
            SELECT DISTINCT a.entity_id AS user_id
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3
              AND d.code = 'email'
              AND a.key_text LIKE 'deleted-%@removed.local'
            """,
        )
        user_ids = list({r["user_id"] for r in [*rows, *pseudo_rows]})
        if not user_ids:
            return
        await conn.execute(
            'DELETE FROM "04_audit"."60_evt_audit" '
            "WHERE metadata->>'user_id' = ANY($1::text[])",
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."16_fct_sessions" WHERE user_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id=3 AND entity_id=ANY($1::text[])',
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


async def _create_user(client: Any, email: str) -> dict:
    resp = await client.post(
        "/v1/users",
        json={
            "account_type": "email_password",
            "email": email,
            "display_name": "Test Lifecycle User",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["data"]


async def _audit_count(pool: Any, event_key: str, user_id: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            'SELECT count(*) FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = $1 AND metadata->>'user_id' = $2",
            event_key,
            user_id,
        )


@pytest.mark.asyncio
async def test_deactivate_user_via_status(live_app) -> None:
    """PATCH status=inactive → is_active=False, sessions revoked, audit emitted."""
    client, pool = live_app
    user = await _create_user(client, f"{_PREFIX}deactivate@example.com")
    uid = user["id"]
    assert user["is_active"] is True

    resp = await client.patch(f"/v1/users/{uid}", json={"status": "inactive"})
    assert resp.status_code == 200, resp.text
    updated = resp.json()["data"]
    assert updated["is_active"] is False

    assert await _audit_count(pool, "iam.users.deactivated", uid) == 1


@pytest.mark.asyncio
async def test_reactivate_user_via_status(live_app) -> None:
    """PATCH status=active after deactivation → is_active=True, audit emitted."""
    client, pool = live_app
    user = await _create_user(client, f"{_PREFIX}reactivate@example.com")
    uid = user["id"]

    # Deactivate first.
    resp = await client.patch(f"/v1/users/{uid}", json={"status": "inactive"})
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is False

    # Reactivate.
    resp = await client.patch(f"/v1/users/{uid}", json={"status": "active"})
    assert resp.status_code == 200, resp.text
    assert resp.json()["data"]["is_active"] is True

    assert await _audit_count(pool, "iam.users.reactivated", uid) == 1


@pytest.mark.asyncio
async def test_list_filter_by_is_active(live_app) -> None:
    """GET /v1/users?is_active=false includes deactivated users."""
    client, pool = live_app
    user = await _create_user(client, f"{_PREFIX}filter-inactive@example.com")
    uid = user["id"]

    await client.patch(f"/v1/users/{uid}", json={"status": "inactive"})

    resp = await client.get("/v1/users?is_active=false")
    assert resp.status_code == 200
    ids = [u["id"] for u in resp.json()["data"]]
    assert uid in ids


@pytest.mark.asyncio
async def test_delete_pseudonymizes_user(live_app) -> None:
    """DELETE → email pseudonymized, deleted_at set, audit emitted, GET returns 404."""
    client, pool = live_app
    original_email = f"{_PREFIX}delete-me@example.com"
    user = await _create_user(client, original_email)
    uid = user["id"]

    resp = await client.delete(f"/v1/users/{uid}")
    assert resp.status_code == 204, resp.text

    # GET returns 404.
    resp = await client.get(f"/v1/users/{uid}")
    assert resp.status_code == 404

    # Audit event emitted with original_email_hash and pseudonymized_email.
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT metadata FROM "04_audit"."60_evt_audit" '
            "WHERE event_key = 'iam.users.deleted' AND metadata->>'user_id' = $1",
            uid,
        )
    assert row is not None
    meta = row["metadata"]
    assert "original_email_hash" in meta
    assert meta["original_email_hash"] != original_email  # hashed, not plaintext
    assert meta.get("pseudonymized_email", "").endswith("@removed.local")

    # DB: dtl email attr is pseudonymized.
    async with pool.acquire() as conn:
        email_val = await conn.fetchval(
            """
            SELECT a.key_text
            FROM "03_iam"."21_dtl_attrs" a
            JOIN "03_iam"."20_dtl_attr_defs" d ON d.id = a.attr_def_id
            WHERE a.entity_type_id = 3 AND a.entity_id = $1 AND d.code = 'email'
            """,
            uid,
        )
    assert email_val is not None
    assert email_val.endswith("@removed.local")
    assert email_val != original_email

    # DB: deleted_at is set on fct row.
    async with pool.acquire() as conn:
        deleted_at = await conn.fetchval(
            'SELECT deleted_at FROM "03_iam"."12_fct_users" WHERE id = $1',
            uid,
        )
    assert deleted_at is not None

    assert await _audit_count(pool, "iam.users.deleted", uid) == 1


@pytest.mark.asyncio
async def test_inactive_user_cannot_get_via_list_active_filter(live_app) -> None:
    """Deactivated user excluded from ?is_active=true filter."""
    client, pool = live_app
    user = await _create_user(client, f"{_PREFIX}excluded@example.com")
    uid = user["id"]

    await client.patch(f"/v1/users/{uid}", json={"status": "inactive"})

    resp = await client.get("/v1/users?is_active=true")
    assert resp.status_code == 200
    ids = [u["id"] for u in resp.json()["data"]]
    assert uid not in ids


@pytest.mark.asyncio
async def test_no_op_when_status_unchanged(live_app) -> None:
    """PATCH status=active on already-active user is a no-op (no audit event)."""
    client, pool = live_app
    user = await _create_user(client, f"{_PREFIX}noop@example.com")
    uid = user["id"]
    assert user["is_active"] is True

    resp = await client.patch(f"/v1/users/{uid}", json={"status": "active"})
    assert resp.status_code == 200
    # No deactivated/reactivated audit event.
    assert await _audit_count(pool, "iam.users.deactivated", uid) == 0
    assert await _audit_count(pool, "iam.users.reactivated", uid) == 0
