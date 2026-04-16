#!/usr/bin/env python3
"""Grant platform_super_admin group membership to a user via direct DB insert."""

import asyncio
import os
import sys
import uuid
import datetime

import asyncpg


async def main(user_id: str) -> None:
    conn = await asyncpg.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ.get("DB_PORT", "5432")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASS"],
        database=os.environ["DB_NAME"],
    )
    try:
        group_id = await conn.fetchval(
            'SELECT id FROM "03_auth_manage"."17_fct_user_groups" '
            "WHERE code = 'platform_super_admin' AND tenant_key = 'default'"
        )
        if group_id is None:
            print("SKIP: platform_super_admin group not found")
            return

        now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
        membership_id = str(uuid.uuid4())
        await conn.execute(
            'INSERT INTO "03_auth_manage"."18_lnk_group_memberships" '
            "(id, group_id, user_id, membership_status, effective_from, "
            "is_active, is_disabled, is_deleted, is_test, is_system, is_locked, "
            "created_at, updated_at, created_by) "
            "VALUES ($1, $2, $3, 'active', $4, "
            "TRUE, FALSE, FALSE, FALSE, FALSE, FALSE, "
            "$5, $6, $7) "
            "ON CONFLICT DO NOTHING",
            membership_id,
            str(group_id),
            user_id,
            now,
            now,
            now,
            user_id,
        )
        print(f"OK: granted super_admin to {user_id}")
    finally:
        await conn.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python _grant_super_admin.py <user_id>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(sys.argv[1]))
