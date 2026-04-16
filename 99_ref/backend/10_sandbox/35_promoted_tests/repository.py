"""
Repository for promoted control tests.

Reads/writes:
  15_sandbox.35_fct_promoted_tests
  15_sandbox.36_dtl_promoted_test_properties
  15_sandbox.66_vw_promoted_test_detail
"""
from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import PromotedTestRecord

_telemetry = import_module("backend.01_core.telemetry")
instrument_class_methods = _telemetry.instrument_class_methods

_TESTS = '"15_sandbox"."35_fct_promoted_tests"'
_PROPS = '"15_sandbox"."36_dtl_promoted_test_properties"'
_VIEW  = '"15_sandbox"."66_vw_promoted_test_detail"'

_VIEW_SELECT_COLS = f"""
    v.id, v.tenant_key, v.org_id, v.workspace_id, v.promotion_id,
    v.source_signal_id, v.source_policy_id, v.source_library_id, v.source_pack_id,
    v.test_code, v.test_type_code, v.monitoring_frequency,
    v.linked_asset_id, v.connector_type_code, v.connector_name,
    (
        SELECT property_value FROM {_PROPS}
        WHERE test_id = v.id::uuid AND property_key = 'policy_container_code'
        LIMIT 1
    ) AS policy_container_code,
    (
        SELECT property_value FROM {_PROPS}
        WHERE test_id = v.id::uuid AND property_key = 'policy_container_name'
        LIMIT 1
    ) AS policy_container_name,
    v.version_number, v.is_active, v.promoted_by, v.promoted_at, v.is_deleted,
    v.name, v.description, v.evaluation_rule, v.signal_type, v.integration_guide,
    v.control_test_id,
    v.created_at, v.updated_at
"""


def _row(r) -> PromotedTestRecord:
    d = dict(r)
    return PromotedTestRecord(
        id=d["id"],
        tenant_key=d["tenant_key"],
        org_id=d["org_id"],
        workspace_id=d.get("workspace_id"),
        promotion_id=d.get("promotion_id"),
        source_signal_id=d.get("source_signal_id"),
        source_policy_id=d.get("source_policy_id"),
        source_library_id=d.get("source_library_id"),
        source_pack_id=d.get("source_pack_id"),
        test_code=d["test_code"],
        test_type_code=d["test_type_code"],
        monitoring_frequency=d["monitoring_frequency"],
        linked_asset_id=d.get("linked_asset_id"),
        connector_type_code=d.get("connector_type_code"),
        connector_name=d.get("connector_name"),
        policy_container_code=d.get("policy_container_code"),
        policy_container_name=d.get("policy_container_name"),
        version_number=d["version_number"],
        is_active=d["is_active"],
        promoted_by=d["promoted_by"],
        promoted_at=d["promoted_at"],
        is_deleted=d["is_deleted"],
        name=d.get("name"),
        description=d.get("description"),
        evaluation_rule=d.get("evaluation_rule"),
        signal_type=d.get("signal_type"),
        integration_guide=d.get("integration_guide"),
        control_test_id=d.get("control_test_id"),
        created_at=d["created_at"],
        updated_at=d["updated_at"],
    )


class _MISSING_TYPE:
    pass

_MISSING = _MISSING_TYPE()


@instrument_class_methods(namespace="sandbox.promoted_tests.repository", logger_name="backend.sandbox.promoted_tests.repository.instrumentation")
class PromotedTestRepository:

    async def get_next_version(
        self, conn: asyncpg.Connection, tenant_key: str, test_code: str
    ) -> int:
        val = await conn.fetchval(
            f"SELECT COALESCE(MAX(version_number), 0) + 1 FROM {_TESTS} WHERE tenant_key = $1 AND test_code = $2",
            tenant_key, test_code,
        )
        return int(val)

    async def deactivate_previous_versions(
        self, conn: asyncpg.Connection, tenant_key: str, test_code: str
    ) -> None:
        await conn.execute(
            f"UPDATE {_TESTS} SET is_active = FALSE, updated_at = NOW() WHERE tenant_key = $1 AND test_code = $2 AND is_active = TRUE",
            tenant_key, test_code,
        )

    async def create(
        self,
        conn: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        promotion_id: str | None,
        source_signal_id: str | None,
        source_policy_id: str | None,
        source_library_id: str | None,
        source_pack_id: str | None,
        test_code: str,
        test_type_code: str,
        monitoring_frequency: str,
        linked_asset_id: str | None,
        version_number: int,
        promoted_by: str,
        now: str,
    ) -> None:
        await conn.execute(
            f"""
            INSERT INTO {_TESTS} (
                id, tenant_key, org_id, workspace_id,
                promotion_id, source_signal_id, source_policy_id,
                source_library_id, source_pack_id,
                test_code, test_type_code, monitoring_frequency,
                linked_asset_id, version_number, is_active,
                promoted_by, promoted_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3::uuid, $4::uuid,
                $5::uuid, $6::uuid, $7::uuid,
                $8::uuid, $9::uuid,
                $10, $11, $12,
                $13::uuid, $14, TRUE,
                $15::uuid, $16, $16, $16
            )
            """,
            id, tenant_key, org_id, workspace_id,
            promotion_id, source_signal_id, source_policy_id,
            source_library_id, source_pack_id,
            test_code, test_type_code, monitoring_frequency,
            linked_asset_id, version_number,
            promoted_by, now,
        )

    async def upsert_properties(
        self,
        conn: asyncpg.Connection,
        test_id: str,
        props: dict[str, str],
        created_by: str,
        now: str,
    ) -> None:
        for key, value in props.items():
            await conn.execute(
                f"""
                INSERT INTO {_PROPS} (test_id, property_key, property_value, created_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4::uuid, $5, $5)
                ON CONFLICT (test_id, property_key) DO UPDATE
                    SET property_value = EXCLUDED.property_value,
                        updated_at = EXCLUDED.updated_at
                """,
                test_id, key, value, created_by, now,
            )

    async def list(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        search: str | None = None,
        linked_asset_id: str | None = None,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PromotedTestRecord], int]:
        filters = ["tenant_key = $1", "org_id = $2", "is_deleted = FALSE"]
        values: list = [tenant_key, org_id]
        idx = 3

        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1

        if search:
            filters.append(f"(LOWER(test_code) LIKE ${idx} OR LOWER(name) LIKE ${idx})")
            values.append(f"%{search.lower()}%")
            idx += 1

        if linked_asset_id is not None:
            filters.append(f"linked_asset_id = ${idx}::uuid")
            values.append(linked_asset_id)
            idx += 1

        if is_active is not None:
            filters.append(f"is_active = ${idx}")
            values.append(is_active)
            idx += 1

        where = " AND ".join(filters)
        rows = await conn.fetch(
            f"SELECT {_VIEW_SELECT_COLS} FROM {_VIEW} v WHERE {where} ORDER BY test_code ASC, version_number DESC LIMIT ${idx} OFFSET ${idx + 1}",
            *values, limit, offset,
        )
        total = await conn.fetchval(
            f"SELECT COUNT(*) FROM {_VIEW} v WHERE {where}",
            *values,
        )
        return [_row(r) for r in rows], int(total)

    async def get_by_id(
        self, conn: asyncpg.Connection, id: str, tenant_key: str
    ) -> PromotedTestRecord | None:
        row = await conn.fetchrow(
            f"SELECT {_VIEW_SELECT_COLS} FROM {_VIEW} v WHERE v.id = $1 AND v.tenant_key = $2",
            id, tenant_key,
        )
        return _row(row) if row else None

    async def get_version_history(
        self, conn: asyncpg.Connection, tenant_key: str, org_id: str, test_code: str
    ) -> list[PromotedTestRecord]:
        rows = await conn.fetch(
            f"""
            SELECT {_VIEW_SELECT_COLS} FROM {_VIEW} v
            WHERE v.tenant_key = $1 AND v.org_id = $2 AND v.test_code = $3
            ORDER BY version_number DESC
            """,
            tenant_key, org_id, test_code,
        )
        return [_row(r) for r in rows]

    async def update(
        self,
        conn: asyncpg.Connection,
        id: str,
        tenant_key: str,
        *,
        fields: dict,
        now: str,
    ) -> None:
        """Update arbitrary columns. `fields` is a dict of column_name -> value."""
        if not fields:
            return
        sets = []
        values: list = [id, tenant_key, now]
        idx = 4
        for col, val in fields.items():
            if col == "linked_asset_id":
                sets.append(f"{col} = ${idx}::uuid")
            else:
                sets.append(f"{col} = ${idx}")
            values.append(val)
            idx += 1

        await conn.execute(
            f"UPDATE {_TESTS} SET {', '.join(sets)}, updated_at = $3 WHERE id = $1 AND tenant_key = $2",
            *values,
        )

    async def soft_delete(
        self, conn: asyncpg.Connection, id: str, tenant_key: str, now: str
    ) -> None:
        await conn.execute(
            f"UPDATE {_TESTS} SET is_deleted = TRUE, is_active = FALSE, updated_at = $3 WHERE id = $1 AND tenant_key = $2",
            id, tenant_key, now,
        )
