"""
Plan 20-06: TOTP backup codes integration tests.

Covers:
  - Enrolling TOTP returns 10 backup codes
  - A backup code can be verified (returns session)
  - A consumed backup code cannot be reused
  - Regenerate issues 10 new codes and invalidates old ones
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient

_main: Any = import_module("backend.main")

_TEST_EMAIL_PREFIX = "itest-bkp-"


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
            f"{_TEST_EMAIL_PREFIX}%",
        )
        user_ids = [r["user_id"] for r in rows]
        if not user_ids:
            return
        for tbl in [
            '"03_iam"."28_fct_totp_backup_codes"',
            '"03_iam"."24_fct_iam_totp_credentials"',
            '"03_iam"."16_fct_sessions"',
            '"03_iam"."22_dtl_credentials"',
            '"03_iam"."40_lnk_user_orgs"',
        ]:
            try:
                await conn.execute(f'DELETE FROM {tbl} WHERE user_id = ANY($1::text[])', user_ids)
            except Exception:
                pass
        await conn.execute(
            'DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_type_id = 3 AND entity_id = ANY($1::text[])',
            user_ids,
        )
        await conn.execute('DELETE FROM "03_iam"."12_fct_users" WHERE id = ANY($1::text[])', user_ids)


@pytest.fixture
async def live_app():
    async with _main.lifespan(_main.app):
        pool = _main.app.state.pool
        await _cleanup(pool)
        transport = ASGITransport(app=_main.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client, pool
        await _cleanup(pool)


async def _signup_token(client: AsyncClient, email: str) -> tuple[str, str]:
    """Return (user_id, token)."""
    resp = await client.post("/v1/auth/signup", json={
        "email": email, "password": "Test@1234", "display_name": "BKP Test",
    })
    assert resp.status_code in (200, 201), resp.text
    data = resp.json()["data"]
    return data["user"]["id"], data["token"]


async def _totp_setup(client: AsyncClient, token: str) -> tuple[str, list[str]]:
    resp = await client.post(
        "/v1/auth/totp/setup",
        json={"device_name": "test-device"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()["data"]
    return data["credential_id"], data.get("backup_codes", [])


@pytest.mark.asyncio
async def test_totp_enrollment_returns_10_backup_codes(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}enroll@example.com"
    user_id, token = await _signup_token(client, email)
    _, backup_codes = await _totp_setup(client, token)
    assert len(backup_codes) == 10
    assert all(isinstance(c, str) and len(c) > 0 for c in backup_codes)


@pytest.mark.asyncio
async def test_backup_code_can_verify(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}use@example.com"
    user_id, token = await _signup_token(client, email)
    _, backup_codes = await _totp_setup(client, token)
    assert backup_codes

    resp = await client.post("/v1/auth/totp/backup-codes/verify", json={
        "user_id": user_id, "code": backup_codes[0],
    })
    assert resp.status_code == 200, resp.text


@pytest.mark.asyncio
async def test_backup_code_single_use(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}once@example.com"
    user_id, token = await _signup_token(client, email)
    _, backup_codes = await _totp_setup(client, token)
    assert backup_codes
    code = backup_codes[0]

    r1 = await client.post("/v1/auth/totp/backup-codes/verify", json={"user_id": user_id, "code": code})
    assert r1.status_code == 200

    r2 = await client.post("/v1/auth/totp/backup-codes/verify", json={"user_id": user_id, "code": code})
    assert r2.status_code in (400, 401, 404, 422)


@pytest.mark.asyncio
async def test_regenerate_invalidates_old_codes(live_app) -> None:
    client, pool = live_app
    email = f"{_TEST_EMAIL_PREFIX}regen@example.com"
    user_id, token = await _signup_token(client, email)
    _, old_codes = await _totp_setup(client, token)
    assert old_codes

    resp = await client.post("/v1/auth/totp/backup-codes/regenerate",
                             json={}, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    new_codes = resp.json()["data"]["backup_codes"]
    assert len(new_codes) == 10

    r = await client.post("/v1/auth/totp/backup-codes/verify", json={"user_id": user_id, "code": old_codes[0]})
    assert r.status_code in (400, 401, 404, 422), "Old code should no longer work"
