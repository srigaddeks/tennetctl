from __future__ import annotations

import json

import asyncpg
from importlib import import_module

from .models import PolicyRecord, PolicyExecutionRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.policies.repository", logger_name="backend.sandbox.policies.repository.instrumentation")
class PolicyRepository:

    async def list_policies(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        threat_type_id: str | None = None,
        is_enabled: bool | None = None,
        sort_by: str = "policy_code",
        sort_dir: str = "ASC",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PolicyRecord], int]:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"(workspace_id = ${idx} OR workspace_id IS NULL)")
            values.append(workspace_id)
            idx += 1
        if threat_type_id is not None:
            filters.append(f"threat_type_id = ${idx}")
            values.append(threat_type_id)
            idx += 1
        if is_enabled is not None:
            filters.append(f"is_enabled = ${idx}")
            values.append(is_enabled)
            idx += 1

        where_clause = " AND ".join(filters)

        allowed_sort = {"policy_code", "version_number", "created_at", "updated_at"}
        col = sort_by if sort_by in allowed_sort else "policy_code"
        direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, workspace_id, policy_code,
                   version_number, threat_type_id, threat_code,
                   actions::text, is_enabled, cooldown_minutes,
                   is_active, created_at::text, updated_at::text,
                   name, description,
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."63_vw_policy_detail"
            WHERE {where_clause}
            ORDER BY {col} {direction}
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_policy(r) for r in rows], total

    async def count_policies(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        threat_type_id: str | None = None,
        is_enabled: bool | None = None,
    ) -> int:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"(workspace_id = ${idx} OR workspace_id IS NULL)")
            values.append(workspace_id)
            idx += 1
        if threat_type_id is not None:
            filters.append(f"threat_type_id = ${idx}")
            values.append(threat_type_id)
            idx += 1
        if is_enabled is not None:
            filters.append(f"is_enabled = ${idx}")
            values.append(is_enabled)
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."63_vw_policy_detail" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    async def get_policy_by_id(
        self, connection: asyncpg.Connection, policy_id: str
    ) -> PolicyRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, workspace_id, policy_code,
                   version_number, threat_type_id, threat_code,
                   actions::text, is_enabled, cooldown_minutes,
                   is_active, created_at::text, updated_at::text,
                   name, description
            FROM {SCHEMA}."63_vw_policy_detail"
            WHERE id = $1
            """,
            policy_id,
        )
        return _row_to_policy(row) if row else None

    async def get_policy_properties(
        self, connection: asyncpg.Connection, policy_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."47_dtl_policy_properties"
            WHERE policy_id = $1
            """,
            policy_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    async def list_policy_properties_batch(
        self, connection: asyncpg.Connection, policy_ids: list[str]
    ) -> dict[str, dict[str, str]]:
        """Batch load properties for multiple policies. Returns {policy_id: {key: value}}."""
        if not policy_ids:
            return {}
        rows = await connection.fetch(
            f'''SELECT policy_id, property_key, property_value
                FROM {SCHEMA}."47_dtl_policy_properties"
                WHERE policy_id = ANY($1)''',
            policy_ids,
        )
        result: dict[str, dict[str, str]] = {pid: {} for pid in policy_ids}
        for row in rows:
            result[row["policy_id"]][row["property_key"]] = row["property_value"]
        return result

    async def create_policy(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        policy_code: str,
        version_number: int,
        threat_type_id: str,
        actions: list[dict],
        is_enabled: bool,
        cooldown_minutes: int,
        created_by: str,
        now: object,
    ) -> str:
        actions_json = json.dumps(actions)
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."24_fct_policies"
                (id, tenant_key, org_id, workspace_id, policy_code,
                 version_number, threat_type_id, actions, is_enabled,
                 cooldown_minutes, is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8::jsonb, $9,
                 $10, TRUE, FALSE,
                 $11, $12, $13, $14,
                 NULL, NULL)
            """,
            id,
            tenant_key,
            org_id,
            workspace_id,
            policy_code,
            version_number,
            threat_type_id,
            actions_json,
            is_enabled,
            cooldown_minutes,
            now,
            now,
            created_by,
            created_by,
        )
        return id

    async def get_next_version(
        self, connection: asyncpg.Connection, org_id: str, policy_code: str
    ) -> int:
        """Returns next version number with advisory lock to prevent races.
        Must be called inside a transaction."""
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            f"sb:policy_version:{org_id}:{policy_code}",
        )
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."24_fct_policies"
            WHERE org_id = $1 AND policy_code = $2
            """,
            org_id,
            policy_code,
        )
        return row["next_version"] if row else 1

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        policy_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (policy_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."47_dtl_policy_properties"
                (id, policy_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (policy_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    async def update_enabled(
        self,
        connection: asyncpg.Connection,
        policy_id: str,
        is_enabled: bool,
        *,
        updated_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."24_fct_policies"
            SET is_enabled = $1, updated_at = $2, updated_by = $3
            WHERE id = $4 AND is_deleted = FALSE
            """,
            is_enabled, now, updated_by, policy_id,
        )
        return result != "UPDATE 0"

    async def soft_delete(
        self,
        connection: asyncpg.Connection,
        policy_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."24_fct_policies"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, policy_id,
        )
        return result != "UPDATE 0"

    async def list_versions(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        policy_code: str,
    ) -> list[PolicyRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, workspace_id, policy_code,
                   version_number, threat_type_id, threat_code,
                   actions::text, is_enabled, cooldown_minutes,
                   is_active, created_at::text, updated_at::text,
                   name, description
            FROM {SCHEMA}."63_vw_policy_detail"
            WHERE org_id = $1 AND policy_code = $2
            ORDER BY version_number DESC
            """,
            org_id,
            policy_code,
        )
        return [_row_to_policy(r) for r in rows]

    async def insert_policy_execution(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        policy_id: str,
        threat_evaluation_id: str | None,
        actions_executed: list[dict],
        actions_failed: list[dict],
        created_by: str,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."27_trx_policy_executions"
                (id, tenant_key, org_id, policy_id, threat_evaluation_id,
                 actions_executed, actions_failed,
                 created_at, created_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6::jsonb, $7::jsonb,
                 NOW(), $8)
            """,
            id,
            tenant_key,
            org_id,
            policy_id,
            threat_evaluation_id,
            json.dumps(actions_executed),
            json.dumps(actions_failed),
            created_by,
        )
        return id

    async def list_policy_executions(
        self,
        connection: asyncpg.Connection,
        policy_id: str,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PolicyExecutionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, policy_id, threat_evaluation_id,
                   actions_executed::text, actions_failed::text,
                   created_at::text, created_by
            FROM {SCHEMA}."27_trx_policy_executions"
            WHERE policy_id = $1
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            policy_id,
        )
        return [_row_to_execution(r) for r in rows]


def _row_to_policy(r) -> PolicyRecord:
    actions_raw = r["actions"]
    if isinstance(actions_raw, str):
        actions = json.loads(actions_raw)
    elif actions_raw is None:
        actions = []
    else:
        actions = actions_raw

    return PolicyRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        policy_code=r["policy_code"],
        version_number=r["version_number"],
        threat_type_id=r["threat_type_id"],
        threat_code=r["threat_code"],
        actions=actions,
        is_enabled=r["is_enabled"],
        cooldown_minutes=r["cooldown_minutes"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
    )


def _row_to_execution(r) -> PolicyExecutionRecord:
    def _parse_json(val):
        if isinstance(val, str):
            return json.loads(val)
        return val if val is not None else []

    return PolicyExecutionRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        policy_id=r["policy_id"],
        threat_evaluation_id=r["threat_evaluation_id"],
        actions_executed=_parse_json(r["actions_executed"]),
        actions_failed=_parse_json(r["actions_failed"]),
        created_at=r["created_at"],
        created_by=r["created_by"],
    )
