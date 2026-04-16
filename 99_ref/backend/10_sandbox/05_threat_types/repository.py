from __future__ import annotations

import json

import asyncpg
from importlib import import_module

from .models import ThreatTypeRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.threat_types.repository", logger_name="backend.sandbox.threat_types.repository.instrumentation")
class ThreatTypeRepository:

    async def list_threat_types(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        severity_code: str | None = None,
        search: str | None = None,
        sort_by: str = "threat_code",
        sort_dir: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ThreatTypeRecord], int]:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"(workspace_id = ${idx} OR workspace_id IS NULL)")
            values.append(workspace_id)
            idx += 1
        if severity_code is not None:
            filters.append(f"severity_code = ${idx}")
            values.append(severity_code)
            idx += 1
        if search is not None:
            filters.append(f"(threat_code ILIKE ${idx} OR name ILIKE ${idx})")
            values.append(f"%{search}%")
            idx += 1

        where_clause = " AND ".join(filters)

        allowed_sort = {"threat_code", "version_number", "severity_code", "created_at", "updated_at", "name"}
        if sort_by not in allowed_sort:
            sort_by = "threat_code"
        sort_dir = "DESC" if sort_dir.upper() == "DESC" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, workspace_id, threat_code,
                   version_number, severity_code, severity_name,
                   expression_tree::text, is_active,
                   created_at::text, updated_at::text,
                   name, description,
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."62_vw_threat_type_detail"
            WHERE {where_clause}
            ORDER BY {sort_by} {sort_dir}
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_threat_type(r) for r in rows], total

    async def count_threat_types(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        severity_code: str | None = None,
        search: str | None = None,
    ) -> int:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"(workspace_id = ${idx} OR workspace_id IS NULL)")
            values.append(workspace_id)
            idx += 1
        if severity_code is not None:
            filters.append(f"severity_code = ${idx}")
            values.append(severity_code)
            idx += 1
        if search is not None:
            filters.append(f"(threat_code ILIKE ${idx} OR name ILIKE ${idx})")
            values.append(f"%{search}%")
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."62_vw_threat_type_detail" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    async def get_threat_type_by_id(
        self, connection: asyncpg.Connection, threat_type_id: str
    ) -> ThreatTypeRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, workspace_id, threat_code,
                   version_number, severity_code, severity_name,
                   expression_tree::text, is_active,
                   created_at::text, updated_at::text,
                   name, description
            FROM {SCHEMA}."62_vw_threat_type_detail"
            WHERE id = $1
            """,
            threat_type_id,
        )
        return _row_to_threat_type(row) if row else None

    async def get_threat_type_properties(
        self, connection: asyncpg.Connection, threat_type_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."46_dtl_threat_type_properties"
            WHERE threat_type_id = $1
            """,
            threat_type_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    async def list_threat_type_properties_batch(
        self, connection: asyncpg.Connection, threat_type_ids: list[str]
    ) -> dict[str, dict[str, str]]:
        """Batch load properties for multiple threat types. Returns {threat_type_id: {key: value}}."""
        if not threat_type_ids:
            return {}
        rows = await connection.fetch(
            f'''SELECT threat_type_id, property_key, property_value
                FROM {SCHEMA}."46_dtl_threat_type_properties"
                WHERE threat_type_id = ANY($1)''',
            threat_type_ids,
        )
        result: dict[str, dict[str, str]] = {tid: {} for tid in threat_type_ids}
        for row in rows:
            result[row["threat_type_id"]][row["property_key"]] = row["property_value"]
        return result

    async def create_threat_type(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        threat_code: str,
        version_number: int,
        severity_code: str,
        expression_tree: dict,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."23_fct_threat_types"
                (id, tenant_key, org_id, workspace_id, threat_code,
                 version_number, severity_code, expression_tree,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8::jsonb,
                 TRUE, FALSE,
                 $9, $10, $11, $12, NULL, NULL)
            """,
            id,
            tenant_key,
            org_id,
            workspace_id,
            threat_code,
            version_number,
            severity_code,
            json.dumps(expression_tree),
            now,
            now,
            created_by,
            created_by,
        )
        return id

    async def get_next_version(
        self, connection: asyncpg.Connection, org_id: str, threat_code: str
    ) -> int:
        """Returns next version number with advisory lock to prevent races.
        Must be called inside a transaction."""
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            f"sb:threat_version:{org_id}:{threat_code}",
        )
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."23_fct_threat_types"
            WHERE org_id = $1 AND threat_code = $2
            """,
            org_id, threat_code,
        )
        return row["next_version"] if row else 1

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        threat_type_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (threat_type_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."46_dtl_threat_type_properties"
                (id, threat_type_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (threat_type_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    async def soft_delete(
        self,
        connection: asyncpg.Connection,
        threat_type_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."23_fct_threat_types"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, threat_type_id,
        )
        return result != "UPDATE 0"

    async def list_versions(
        self, connection: asyncpg.Connection, org_id: str, threat_code: str
    ) -> list[ThreatTypeRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, workspace_id, threat_code,
                   version_number, severity_code, severity_name,
                   expression_tree::text, is_active,
                   created_at::text, updated_at::text,
                   name, description
            FROM {SCHEMA}."62_vw_threat_type_detail"
            WHERE org_id = $1 AND threat_code = $2
            ORDER BY version_number DESC
            """,
            org_id, threat_code,
        )
        return [_row_to_threat_type(r) for r in rows]


def _row_to_threat_type(r) -> ThreatTypeRecord:
    expression_tree = r["expression_tree"]
    if isinstance(expression_tree, str):
        try:
            expression_tree = json.loads(expression_tree)
        except (json.JSONDecodeError, TypeError):
            expression_tree = None

    return ThreatTypeRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        threat_code=r["threat_code"],
        version_number=r["version_number"],
        severity_code=r["severity_code"],
        severity_name=r["severity_name"],
        expression_tree=expression_tree,
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
    )
