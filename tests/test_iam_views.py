"""
Smoke tests for IAM views: v_orgs, v_workspaces, v_users.

Each test inserts a fct row + its dtl_attrs, then SELECTs via the view and
asserts the flat shape. Self-cleaning via DELETE in finally.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest

_db: Any = import_module("backend.01_core.database")
_core_id: Any = import_module("backend.01_core.id")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)


async def _attr_def_id(conn: Any, entity_type_id: int, code: str) -> int:
    row = await conn.fetchrow(
        'SELECT id FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = $1 AND code = $2',
        entity_type_id, code,
    )
    assert row is not None, f"attr_def not registered: ({entity_type_id}, {code})"
    return row["id"]


@pytest.mark.asyncio
async def test_v_orgs_surfaces_display_name() -> None:
    pool = await _db.create_pool(LIVE_DSN)
    org_id_named = _core_id.uuid7()
    org_id_empty = _core_id.uuid7()
    attr_id = _core_id.uuid7()
    try:
        async with pool.acquire() as conn:
            display_name_def = await _attr_def_id(conn, 1, "display_name")

            # Org WITH display_name attr
            await conn.execute(
                'INSERT INTO "03_iam"."10_fct_orgs" (id, slug, created_by, updated_by) VALUES ($1, $2, $3, $3)',
                org_id_named, "test-v-orgs-named", "sys",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text) VALUES ($1, 1, $2, $3, $4)',
                attr_id, org_id_named, display_name_def, "Named Corp",
            )

            # Org WITHOUT display_name attr
            await conn.execute(
                'INSERT INTO "03_iam"."10_fct_orgs" (id, slug, created_by, updated_by) VALUES ($1, $2, $3, $3)',
                org_id_empty, "test-v-orgs-empty", "sys",
            )

            # Named row has display_name
            row = await conn.fetchrow(
                'SELECT id, slug, display_name, is_active FROM "03_iam"."v_orgs" WHERE id = $1',
                org_id_named,
            )
            assert row is not None
            assert row["slug"] == "test-v-orgs-named"
            assert row["display_name"] == "Named Corp"
            assert row["is_active"] is True

            # Empty row has NULL display_name (LEFT JOIN)
            row = await conn.fetchrow(
                'SELECT id, slug, display_name FROM "03_iam"."v_orgs" WHERE id = $1',
                org_id_empty,
            )
            assert row is not None
            assert row["slug"] == "test-v-orgs-empty"
            assert row["display_name"] is None
    finally:
        async with pool.acquire() as conn:
            await conn.execute('DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id IN ($1, $2)', org_id_named, org_id_empty)
            await conn.execute('DELETE FROM "03_iam"."10_fct_orgs" WHERE id IN ($1, $2)', org_id_named, org_id_empty)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_v_workspaces_surfaces_display_name() -> None:
    pool = await _db.create_pool(LIVE_DSN)
    org_id = _core_id.uuid7()
    ws_id = _core_id.uuid7()
    attr_id = _core_id.uuid7()
    try:
        async with pool.acquire() as conn:
            display_name_def = await _attr_def_id(conn, 2, "display_name")

            await conn.execute(
                'INSERT INTO "03_iam"."10_fct_orgs" (id, slug, created_by, updated_by) VALUES ($1, $2, $3, $3)',
                org_id, "test-v-ws-org", "sys",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."11_fct_workspaces" (id, org_id, slug, created_by, updated_by) VALUES ($1, $2, $3, $4, $4)',
                ws_id, org_id, "test-ws-1", "sys",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text) VALUES ($1, 2, $2, $3, $4)',
                attr_id, ws_id, display_name_def, "Workspace One",
            )

            row = await conn.fetchrow(
                'SELECT id, org_id, slug, display_name FROM "03_iam"."v_workspaces" WHERE id = $1',
                ws_id,
            )
            assert row is not None
            assert row["org_id"] == org_id
            assert row["slug"] == "test-ws-1"
            assert row["display_name"] == "Workspace One"
    finally:
        async with pool.acquire() as conn:
            await conn.execute('DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id = $1', ws_id)
            await conn.execute('DELETE FROM "03_iam"."11_fct_workspaces" WHERE id = $1', ws_id)
            await conn.execute('DELETE FROM "03_iam"."10_fct_orgs" WHERE id = $1', org_id)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_v_users_resolves_account_type_and_attrs() -> None:
    pool = await _db.create_pool(LIVE_DSN)
    user_id = _core_id.uuid7()
    attr_ids = [_core_id.uuid7() for _ in range(3)]
    try:
        async with pool.acquire() as conn:
            email_def = await _attr_def_id(conn, 3, "email")
            name_def = await _attr_def_id(conn, 3, "display_name")
            avatar_def = await _attr_def_id(conn, 3, "avatar_url")

            await conn.execute(
                'INSERT INTO "03_iam"."12_fct_users" (id, account_type_id, created_by, updated_by) VALUES ($1, 1, $2, $2)',
                user_id, "sys",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text) VALUES ($1, 3, $2, $3, $4)',
                attr_ids[0], user_id, email_def, "alice@example.com",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text) VALUES ($1, 3, $2, $3, $4)',
                attr_ids[1], user_id, name_def, "Alice Example",
            )
            await conn.execute(
                'INSERT INTO "03_iam"."21_dtl_attrs" (id, entity_type_id, entity_id, attr_def_id, key_text) VALUES ($1, 3, $2, $3, $4)',
                attr_ids[2], user_id, avatar_def, "https://img.example.com/alice.png",
            )

            row = await conn.fetchrow(
                'SELECT * FROM "03_iam"."v_users" WHERE id = $1',
                user_id,
            )
            assert row is not None
            assert row["account_type"] == "email_password"  # resolved from dim
            assert row["email"] == "alice@example.com"
            assert row["display_name"] == "Alice Example"
            assert row["avatar_url"] == "https://img.example.com/alice.png"
            # account_type_id must NOT be exposed in the view
            assert "account_type_id" not in row.keys()
    finally:
        async with pool.acquire() as conn:
            await conn.execute('DELETE FROM "03_iam"."21_dtl_attrs" WHERE entity_id = $1', user_id)
            await conn.execute('DELETE FROM "03_iam"."12_fct_users" WHERE id = $1', user_id)
        await _db.close_pool(pool)
