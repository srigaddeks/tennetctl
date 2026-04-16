from __future__ import annotations

from datetime import datetime
from importlib import import_module
from uuid import uuid4

import asyncpg

from .models import FeatureCategoryRecord, FeatureFlagRecord, FeaturePermissionRecord, PermissionActionRecord

SCHEMA = '"03_auth_manage"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="feature_flags.repository", logger_name="backend.feature_flags.repository.instrumentation")
class FeatureFlagRepository:
    async def list_categories(self, connection: asyncpg.Connection) -> list[FeatureCategoryRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, name, description, sort_order
            FROM {SCHEMA}."11_dim_feature_flag_categories"
            ORDER BY sort_order
            """
        )
        return [
            FeatureCategoryRecord(
                id=row["id"],
                code=row["code"],
                name=row["name"],
                description=row["description"],
                sort_order=row["sort_order"],
            )
            for row in rows
        ]

    async def create_category(
        self,
        connection: asyncpg.Connection,
        *,
        category_id: str,
        code: str,
        name: str,
        description: str,
        sort_order: int,
        now: datetime,
    ) -> FeatureCategoryRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."11_dim_feature_flag_categories"
                (id, code, name, description, sort_order, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, code, name, description, sort_order
            """,
            category_id, code, name, description, sort_order, now, now,
        )
        return FeatureCategoryRecord(
            id=str(row["id"]),
            code=row["code"],
            name=row["name"],
            description=row["description"],
            sort_order=row["sort_order"],
        )

    async def list_feature_flags(self, connection: asyncpg.Connection) -> list[FeatureFlagRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, name, description, feature_flag_category_code,
                   feature_scope, access_mode, lifecycle_state, initial_audience,
                   env_dev, env_staging, env_prod, created_at, updated_at
            FROM {SCHEMA}."14_dim_feature_flags"
            ORDER BY feature_flag_category_code, code
            """
        )
        return [_row_to_flag(row) for row in rows]

    async def get_feature_flag_by_code(
        self, connection: asyncpg.Connection, code: str
    ) -> FeatureFlagRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, code, name, description, feature_flag_category_code,
                   feature_scope, access_mode, lifecycle_state, initial_audience,
                   env_dev, env_staging, env_prod, created_at, updated_at
            FROM {SCHEMA}."14_dim_feature_flags"
            WHERE code = $1
            """,
            code,
        )
        return _row_to_flag(row) if row else None

    async def list_flag_settings_batch(
        self, connection: asyncpg.Connection, setting_keys: list[str]
    ) -> dict[str, dict[str, str]]:
        """Batch-fetch specific settings for ALL feature flags in one query.

        Returns: { flag_code: { setting_key: value, ... }, ... }
        """
        if not setting_keys:
            return {}
        rows = await connection.fetch(
            f"""
            SELECT f.code AS flag_code, s.setting_key, s.setting_value
            FROM {SCHEMA}."21_dtl_feature_flag_settings" s
            JOIN {SCHEMA}."14_dim_feature_flags" f ON f.id = s.feature_flag_id
            WHERE s.setting_key = ANY($1)
            """,
            setting_keys,
        )
        result: dict[str, dict[str, str]] = {}
        for row in rows:
            result.setdefault(row["flag_code"], {})[row["setting_key"]] = row["setting_value"]
        return result

    async def create_feature_flag(
        self,
        connection: asyncpg.Connection,
        *,
        code: str,
        name: str,
        description: str,
        category_code: str,
        feature_scope: str,
        access_mode: str,
        lifecycle_state: str,
        initial_audience: str,
        env_dev: bool,
        env_staging: bool,
        env_prod: bool,
        now: datetime,
    ) -> FeatureFlagRecord:
        flag_id = str(uuid4())
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."14_dim_feature_flags" (
                id, code, name, description, feature_flag_category_code,
                feature_scope, access_mode, lifecycle_state, initial_audience,
                env_dev, env_staging, env_prod, created_at, updated_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """,
            flag_id, code, name, description, category_code,
            feature_scope, access_mode, lifecycle_state, initial_audience,
            env_dev, env_staging, env_prod, now, now,
        )
        row = await connection.fetchrow(
            f"""
            SELECT id, code, name, description, feature_flag_category_code,
                   feature_scope, access_mode, lifecycle_state, initial_audience,
                   env_dev, env_staging, env_prod, created_at, updated_at
            FROM {SCHEMA}."14_dim_feature_flags" WHERE id = $1
            """,
            flag_id,
        )
        return _row_to_flag(row)  # type: ignore[arg-type]

    async def update_feature_flag(
        self,
        connection: asyncpg.Connection,
        *,
        code: str,
        name: str | None,
        description: str | None,
        category_code: str | None,
        feature_scope: str | None,
        access_mode: str | None,
        lifecycle_state: str | None,
        env_dev: bool | None,
        env_staging: bool | None,
        env_prod: bool | None,
        now: datetime,
    ) -> FeatureFlagRecord | None:
        sets: list[str] = ["updated_at = $1"]
        params: list[object] = [now]
        idx = [2]

        def _add(col: str, val: object) -> None:
            sets.append(f"{col} = ${idx[0]}")
            params.append(val)
            idx[0] += 1

        if name is not None:
            _add("name", name)
        if description is not None:
            _add("description", description)
        if category_code is not None:
            _add("feature_flag_category_code", category_code)
        if feature_scope is not None:
            _add("feature_scope", feature_scope)
        if access_mode is not None:
            _add("access_mode", access_mode)
        if lifecycle_state is not None:
            _add("lifecycle_state", lifecycle_state)
        if env_dev is not None:
            _add("env_dev", env_dev)
        if env_staging is not None:
            _add("env_staging", env_staging)
        if env_prod is not None:
            _add("env_prod", env_prod)

        params.append(code)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."14_dim_feature_flags"
            SET {", ".join(sets)}
            WHERE code = ${idx[0]}
            RETURNING id, code, name, description, feature_flag_category_code,
                      feature_scope, access_mode, lifecycle_state, initial_audience,
                      env_dev, env_staging, env_prod, created_at, updated_at
            """,
            *params,
        )
        return _row_to_flag(row) if row else None

    async def create_feature_permission(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        code: str,
        feature_flag_code: str,
        permission_action_code: str,
        name: str,
        description: str,
        now: datetime,
    ) -> FeaturePermissionRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."15_dim_feature_permissions"
                (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, code, feature_flag_code, permission_action_code, name, description
            """,
            id, code, feature_flag_code, permission_action_code, name, description, now, now,
        )
        return _row_to_permission(row)

    async def list_org_available_flags(self, connection: asyncpg.Connection) -> list[dict]:
        """Return org-scoped flags with org_visibility and required_license settings.

        Single query with two LEFT JOINs — no N+1. Excludes hidden flags.
        """
        rows = await connection.fetch(
            f"""
            SELECT f.id, f.code, f.name, f.description, f.feature_flag_category_code,
                   f.feature_scope, f.lifecycle_state,
                   f.env_dev, f.env_staging, f.env_prod,
                   COALESCE(sv.setting_value, 'hidden') AS org_visibility,
                   sl.setting_value AS required_license
            FROM {SCHEMA}."14_dim_feature_flags" f
            LEFT JOIN {SCHEMA}."21_dtl_feature_flag_settings" sv
              ON sv.feature_flag_id = f.id AND sv.setting_key = 'org_visibility'
            LEFT JOIN {SCHEMA}."21_dtl_feature_flag_settings" sl
              ON sl.feature_flag_id = f.id AND sl.setting_key = 'required_license'
            WHERE f.feature_scope = 'org'
              AND COALESCE(sv.setting_value, 'hidden') IN ('locked', 'unlocked')
            ORDER BY f.feature_flag_category_code, f.code
            """
        )
        return [dict(row) for row in rows]

    async def list_permissions_for_flag(
        self, connection: asyncpg.Connection, flag_code: str
    ) -> list[FeaturePermissionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, feature_flag_code, permission_action_code, name, description
            FROM {SCHEMA}."15_dim_feature_permissions"
            WHERE feature_flag_code = $1
            ORDER BY permission_action_code
            """,
            flag_code,
        )
        return [_row_to_permission(row) for row in rows]

    async def list_all_permissions(
        self, connection: asyncpg.Connection
    ) -> list[FeaturePermissionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, feature_flag_code, permission_action_code, name, description
            FROM {SCHEMA}."15_dim_feature_permissions"
            ORDER BY feature_flag_code, permission_action_code
            """
        )
        return [_row_to_permission(row) for row in rows]

    async def list_permission_actions(self, connection: asyncpg.Connection) -> list[PermissionActionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, name, description, sort_order
            FROM {SCHEMA}."12_dim_feature_permission_actions"
            ORDER BY sort_order
            """
        )
        return [
            PermissionActionRecord(
                id=str(row["id"]),
                code=row["code"],
                name=row["name"],
                description=row["description"],
                sort_order=row["sort_order"],
            )
            for row in rows
        ]

    async def get_permission_by_id(
        self, connection: asyncpg.Connection, permission_id: str
    ) -> FeaturePermissionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, code, feature_flag_code, permission_action_code, name, description
            FROM {SCHEMA}."15_dim_feature_permissions"
            WHERE id = $1
            """,
            permission_id,
        )
        return _row_to_permission(row) if row else None

    async def get_permission_by_flag_and_action(
        self, connection: asyncpg.Connection, flag_code: str, action_code: str
    ) -> FeaturePermissionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, code, feature_flag_code, permission_action_code, name, description
            FROM {SCHEMA}."15_dim_feature_permissions"
            WHERE feature_flag_code = $1 AND permission_action_code = $2
            """,
            flag_code, action_code,
        )
        return _row_to_permission(row) if row else None

    async def create_permission(
        self,
        connection: asyncpg.Connection,
        *,
        flag_code: str,
        action_code: str,
        now: datetime,
    ) -> FeaturePermissionRecord:
        perm_id = str(uuid4())
        perm_code = f"{flag_code}.{action_code}"
        perm_name = f"{flag_code.replace('_', ' ').title()} — {action_code.capitalize()}"
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."15_dim_feature_permissions"
                (id, code, feature_flag_code, permission_action_code, name, description, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id, code, feature_flag_code, permission_action_code, name, description
            """,
            perm_id, perm_code, flag_code, action_code,
            perm_name, f"Permission to {action_code} {flag_code.replace('_', ' ')}.",
            now, now,
        )
        return _row_to_permission(row)  # type: ignore[arg-type]

    async def delete_permission(
        self, connection: asyncpg.Connection, permission_id: str
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."15_dim_feature_permissions" WHERE id = $1
            """,
            permission_id,
        )
        return result == "DELETE 1"

    async def list_permission_action_types(
        self, connection: asyncpg.Connection
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT code, name, description, sort_order
            FROM {SCHEMA}."12_dim_feature_permission_actions"
            ORDER BY sort_order
            """
        )
        return [dict(row) for row in rows]


    async def delete_permissions_by_flag_code(
        self, connection: asyncpg.Connection, flag_code: str
    ) -> None:
        await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."15_dim_feature_permissions"
            WHERE feature_flag_code = $1
            """,
            flag_code,
        )


def _row_to_flag(row: asyncpg.Record) -> FeatureFlagRecord:
    return FeatureFlagRecord(
        id=row["id"],
        code=row["code"],
        name=row["name"],
        description=row["description"],
        category_code=row["feature_flag_category_code"],
        feature_scope=row["feature_scope"],
        access_mode=row["access_mode"],
        lifecycle_state=row["lifecycle_state"],
        initial_audience=row["initial_audience"],
        env_dev=row["env_dev"],
        env_staging=row["env_staging"],
        env_prod=row["env_prod"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def _row_to_permission(row: asyncpg.Record) -> FeaturePermissionRecord:
    return FeaturePermissionRecord(
        id=row["id"],
        code=row["code"],
        feature_flag_code=row["feature_flag_code"],
        permission_action_code=row["permission_action_code"],
        name=row["name"],
        description=row["description"],
    )
