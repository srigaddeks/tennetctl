from __future__ import annotations

from datetime import datetime
from importlib import import_module
from uuid import uuid4

import asyncpg

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

SCHEMA = '"03_auth_manage"'


@instrument_class_methods(namespace="license_profiles.repository", logger_name="backend.license_profiles.repository")
class LicenseProfileRepository:
    async def list_profiles(self, connection: asyncpg.Connection) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT p.id, p.code, p.name, p.description, p.tier, p.is_active, p.sort_order,
                   p.created_at, p.updated_at,
                   COALESCE(oc.cnt, 0) AS org_count
            FROM {SCHEMA}."37_fct_license_profiles" p
            LEFT JOIN (
                SELECT setting_value AS profile_code, COUNT(*) AS cnt
                FROM {SCHEMA}."30_dtl_org_settings"
                WHERE setting_key = 'license_profile'
                GROUP BY setting_value
            ) oc ON oc.profile_code = p.code
            ORDER BY p.sort_order, p.code
            """
        )
        return [dict(row) for row in rows]

    async def get_profile(self, connection: asyncpg.Connection, code: str) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, code, name, description, tier, is_active, sort_order, created_at, updated_at
            FROM {SCHEMA}."37_fct_license_profiles"
            WHERE code = $1
            """,
            code,
        )
        return dict(row) if row else None

    async def create_profile(
        self, connection: asyncpg.Connection, *, code: str, name: str, description: str, tier: str, sort_order: int, now: datetime
    ) -> dict:
        profile_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."37_fct_license_profiles" (id, code, name, description, tier, sort_order, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
            profile_id, code, name, description, tier, sort_order, now, now,
        )
        return {"id": profile_id, "code": code, "name": name, "description": description,
                "tier": tier, "is_active": True, "sort_order": sort_order, "created_at": now, "updated_at": now}

    async def update_profile(
        self, connection: asyncpg.Connection, *, code: str, name: str | None, description: str | None,
        tier: str | None, is_active: bool | None, sort_order: int | None, now: datetime,
    ) -> dict | None:
        sets: list[str] = ["updated_at = $1"]
        params: list[object] = [now]
        idx = 2

        def _add(col: str, val: object) -> None:
            nonlocal idx
            sets.append(f"{col} = ${idx}")
            params.append(val)
            idx += 1

        if name is not None:
            _add("name", name)
        if description is not None:
            _add("description", description)
        if tier is not None:
            _add("tier", tier)
        if is_active is not None:
            _add("is_active", is_active)
        if sort_order is not None:
            _add("sort_order", sort_order)

        params.append(code)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."37_fct_license_profiles"
            SET {", ".join(sets)}
            WHERE code = ${idx}
            RETURNING id, code, name, description, tier, is_active, sort_order, created_at, updated_at
            """,
            *params,
        )
        return dict(row) if row else None

    async def list_profile_settings(self, connection: asyncpg.Connection, profile_id: str) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT setting_key, setting_value
            FROM {SCHEMA}."38_dtl_license_profile_settings"
            WHERE profile_id = $1
            ORDER BY setting_key
            """,
            profile_id,
        )
        return [{"key": row["setting_key"], "value": row["setting_value"]} for row in rows]

    async def set_profile_setting(
        self, connection: asyncpg.Connection, *, profile_id: str, key: str, value: str, now: datetime
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."38_dtl_license_profile_settings" (id, profile_id, setting_key, setting_value, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (profile_id, setting_key)
            DO UPDATE SET setting_value = $4, updated_at = $6
            """,
            str(uuid4()), profile_id, key, value, now, now,
        )

    async def delete_profile_setting(self, connection: asyncpg.Connection, *, profile_id: str, key: str) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."38_dtl_license_profile_settings"
            WHERE profile_id = $1 AND setting_key = $2
            """,
            profile_id, key,
        )
        return result != "DELETE 0"

    async def get_profile_for_org(self, connection: asyncpg.Connection, org_id: str) -> dict | None:
        """Get the resolved license config for an org: profile defaults + org overrides merged."""
        row = await connection.fetchrow(
            f"""
            SELECT setting_value FROM {SCHEMA}."30_dtl_org_settings"
            WHERE org_id = $1 AND setting_key = 'license_profile'
            """,
            org_id,
        )
        if not row:
            return None
        profile_code = row["setting_value"]
        profile = await connection.fetchrow(
            f"""
            SELECT id, code, name, tier FROM {SCHEMA}."37_fct_license_profiles"
            WHERE code = $1 AND is_active = TRUE
            """,
            profile_code,
        )
        return dict(profile) if profile else None
