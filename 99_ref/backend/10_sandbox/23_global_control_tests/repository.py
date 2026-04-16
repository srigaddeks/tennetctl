from __future__ import annotations

import json
from importlib import import_module

import asyncpg

from .models import GlobalControlTestRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


def _row_to_record(row: asyncpg.Record) -> GlobalControlTestRecord:
    bundle_raw = row["bundle"]
    if isinstance(bundle_raw, (dict, list)):
        bundle_str = json.dumps(bundle_raw)
    else:
        bundle_str = str(bundle_raw) if bundle_raw else "{}"

    return GlobalControlTestRecord(
        id=str(row["id"]),
        global_code=row["global_code"],
        connector_type_code=row["connector_type_code"],
        connector_type_name=row.get("connector_type_name"),
        version_number=row["version_number"],
        bundle=bundle_str,
        source_signal_id=str(row["source_signal_id"]) if row.get("source_signal_id") else None,
        source_policy_id=str(row["source_policy_id"]) if row.get("source_policy_id") else None,
        source_library_id=str(row["source_library_id"]) if row.get("source_library_id") else None,
        source_org_id=str(row["source_org_id"]) if row.get("source_org_id") else None,
        linked_dataset_code=row.get("linked_dataset_code"),
        publish_status=row["publish_status"],
        is_featured=row["is_featured"],
        download_count=row["download_count"],
        signal_count=row["signal_count"],
        published_by=str(row["published_by"]) if row.get("published_by") else None,
        published_at=str(row["published_at"]) if row.get("published_at") else None,
        is_active=row["is_active"],
        is_deleted=row.get("is_deleted", False),
        created_at=str(row["created_at"]),
        updated_at=str(row["updated_at"]),
        name=row.get("name"),
        description=row.get("description"),
        tags=row.get("tags"),
        category=row.get("category"),
        changelog=row.get("changelog"),
        compliance_references=row.get("compliance_references"),
    )


@instrument_class_methods(namespace="sandbox.global_control_tests.repository", logger_name="backend.sandbox.global_control_tests.repository.instrumentation")
class GlobalControlTestRepository:
    _SORT_COLUMNS = frozenset({"name", "global_code", "created_at", "download_count", "signal_count"})

    async def list_tests(
        self,
        connection: asyncpg.Connection,
        *,
        connector_type_code: str | None = None,
        category: str | None = None,
        search: str | None = None,
        linked_dataset_code: str | None = None,
        publish_status: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[GlobalControlTestRecord], int]:
        filters = ["v.is_active = TRUE", "v.is_deleted = FALSE"]
        values: list[object] = []
        idx = 1

        if connector_type_code:
            filters.append(f"v.connector_type_code = ${idx}")
            values.append(connector_type_code)
            idx += 1
        if category:
            filters.append(f"v.category = ${idx}")
            values.append(category)
            idx += 1
        if search:
            filters.append(f"(v.name ILIKE ${idx} OR v.global_code ILIKE ${idx} OR v.description ILIKE ${idx} OR v.tags ILIKE ${idx})")
            values.append(f"%{search}%")
            idx += 1
        if linked_dataset_code:
            filters.append(f"v.linked_dataset_code = ${idx}")
            values.append(linked_dataset_code)
            idx += 1
        if publish_status:
            filters.append(f"v.publish_status = ${idx}")
            values.append(publish_status)
            idx += 1

        where = " AND ".join(filters)
        safe_sort = sort_by if sort_by in self._SORT_COLUMNS else "created_at"
        safe_dir = "ASC" if sort_dir.upper() == "ASC" else "DESC"

        count_row = await connection.fetchrow(
            f'SELECT COUNT(DISTINCT v.global_code)::int AS total FROM {SCHEMA}."87_vw_global_control_test_detail" v WHERE {where}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT * FROM (
                SELECT DISTINCT ON (v.global_code) *
                FROM {SCHEMA}."87_vw_global_control_test_detail" v
                WHERE {where}
                ORDER BY v.global_code, v.version_number DESC
            ) latest_v
            ORDER BY latest_v.{safe_sort} {safe_dir} NULLS LAST
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *values, limit, offset,
        )
        return [_row_to_record(r) for r in rows], total

    async def get_by_id(self, connection: asyncpg.Connection, test_id: str) -> GlobalControlTestRecord | None:
        row = await connection.fetchrow(
            f'SELECT * FROM {SCHEMA}."87_vw_global_control_test_detail" WHERE id = $1::uuid AND is_active AND NOT is_deleted',
            test_id,
        )
        return _row_to_record(row) if row else None

    async def get_max_version(self, connection: asyncpg.Connection, global_code: str) -> int:
        row = await connection.fetchrow(
            f'SELECT COALESCE(MAX(version_number), 0)::int AS mv FROM {SCHEMA}."84_fct_global_control_tests" WHERE global_code = $1',
            global_code,
        )
        return row["mv"] if row else 0

    async def create(
        self,
        connection: asyncpg.Connection,
        *,
        test_id: str,
        global_code: str,
        connector_type_code: str,
        version_number: int,
        bundle: dict,
        source_signal_id: str | None,
        source_policy_id: str | None,
        source_library_id: str | None,
        source_org_id: str | None,
        linked_dataset_code: str | None,
        signal_count: int,
        published_by: str | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."84_fct_global_control_tests"
                (id, global_code, connector_type_code, version_number,
                 bundle, source_signal_id, source_policy_id, source_library_id,
                 source_org_id, linked_dataset_code, signal_count,
                 publish_status, published_by, published_at)
            VALUES ($1::uuid, $2, $3, $4, $5::jsonb, $6::uuid, $7::uuid, $8::uuid, $9::uuid, $10, $11, 'published', $12::uuid, NOW())
            """,
            test_id, global_code, connector_type_code, version_number,
            json.dumps(bundle), source_signal_id, source_policy_id, source_library_id,
            source_org_id, linked_dataset_code, signal_count, published_by,
        )
        return test_id

    async def set_properties(self, connection: asyncpg.Connection, test_id: str, properties: dict[str, str]) -> None:
        for key, value in properties.items():
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."85_dtl_global_control_test_properties" (test_id, property_key, property_value)
                VALUES ($1::uuid, $2, $3)
                ON CONFLICT (test_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                test_id, key, value,
            )

    async def update_metadata(self, connection: asyncpg.Connection, test_id: str, *, is_featured: bool | None = None, publish_status: str | None = None) -> None:
        sets: list[str] = ["updated_at = NOW()"]
        values: list[object] = []
        idx = 1
        if is_featured is not None:
            sets.append(f"is_featured = ${idx}")
            values.append(is_featured)
            idx += 1
        if publish_status is not None:
            sets.append(f"publish_status = ${idx}")
            values.append(publish_status)
            idx += 1
        values.append(test_id)
        await connection.execute(
            f'UPDATE {SCHEMA}."84_fct_global_control_tests" SET {", ".join(sets)} WHERE id = ${idx}::uuid',
            *values,
        )

    async def increment_download_count(self, connection: asyncpg.Connection, test_id: str) -> None:
        await connection.execute(
            f'UPDATE {SCHEMA}."84_fct_global_control_tests" SET download_count = download_count + 1, updated_at = NOW() WHERE id = $1::uuid',
            test_id,
        )

    async def record_pull(
        self, connection: asyncpg.Connection, *,
        pull_id: str, global_test_id: str, pulled_version: int,
        target_org_id: str, target_workspace_id: str | None,
        deploy_type: str, created_signal_ids: list[str] | None,
        created_threat_id: str | None, created_policy_id: str | None,
        pulled_by: str,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."86_trx_global_control_test_pulls"
                (id, global_test_id, pulled_version, target_org_id, target_workspace_id,
                 deploy_type, created_signal_ids, created_threat_id, created_policy_id, pulled_by)
            VALUES ($1::uuid, $2::uuid, $3, $4::uuid, $5::uuid, $6, $7::uuid[], $8::uuid, $9::uuid, $10::uuid)
            """,
            pull_id, global_test_id, pulled_version, target_org_id, target_workspace_id,
            deploy_type, created_signal_ids, created_threat_id, created_policy_id, pulled_by,
        )

    async def list_deployed_global_test_ids(
        self, connection: asyncpg.Connection, *,
        org_id: str, workspace_id: str | None = None,
    ) -> list[str]:
        """Return global_test_ids that have been deployed to this org (optionally workspace)."""
        filters = ["p.target_org_id = $1::uuid"]
        values: list[object] = [org_id]
        if workspace_id:
            filters.append("p.target_workspace_id = $2::uuid")
            values.append(workspace_id)
        rows = await connection.fetch(
            f"""SELECT DISTINCT p.global_test_id::text
                FROM {SCHEMA}."86_trx_global_control_test_pulls" p
                WHERE {' AND '.join(filters)}""",
            *values,
        )
        return [r["global_test_id"] for r in rows]

    async def get_stats(self, connection: asyncpg.Connection) -> dict:
        total_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."84_fct_global_control_tests" WHERE is_active AND NOT is_deleted',
        )
        type_rows = await connection.fetch(
            f'SELECT connector_type_code, COUNT(*)::int AS cnt FROM {SCHEMA}."84_fct_global_control_tests" WHERE is_active AND NOT is_deleted GROUP BY connector_type_code',
        )
        cat_rows = await connection.fetch(
            f'SELECT v.category, COUNT(*)::int AS cnt FROM {SCHEMA}."87_vw_global_control_test_detail" v WHERE v.is_active AND NOT v.is_deleted AND v.category IS NOT NULL GROUP BY v.category',
        )
        featured_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS cnt FROM {SCHEMA}."84_fct_global_control_tests" WHERE is_active AND NOT is_deleted AND is_featured',
        )
        return {
            "total": total_row["total"] if total_row else 0,
            "by_connector_type": {r["connector_type_code"]: r["cnt"] for r in type_rows},
            "by_category": {r["category"]: r["cnt"] for r in cat_rows},
            "featured_count": featured_row["cnt"] if featured_row else 0,
        }
