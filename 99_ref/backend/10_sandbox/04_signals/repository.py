from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import SignalRecord, SignalTestExpectationRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.signals.repository", logger_name="backend.sandbox.signals.repository.instrumentation")
class SignalRepository:
    _SIGNAL_SORT_COLUMNS = frozenset({"name", "signal_code", "created_at", "updated_at", "version_number"})

    # ── list ──────────────────────────────────────────────────

    async def list_signals(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        signal_status_code: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SignalRecord], int]:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if signal_status_code is not None:
            filters.append(f"signal_status_code = ${idx}")
            values.append(signal_status_code)
            idx += 1
        if search is not None:
            filters.append(f"(LOWER(name) LIKE ${idx} OR LOWER(signal_code) LIKE ${idx})")
            values.append(f"%{search.lower()}%")
            idx += 1

        where_clause = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."61_vw_signal_detail" WHERE {where_clause}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        sort_col = sort_by if sort_by in self._SIGNAL_SORT_COLUMNS else "created_at"
        sort_direction = "DESC" if sort_dir.upper() == "DESC" else "ASC"

        rows = await connection.fetch(
            f"""
            SELECT v.id, v.tenant_key, v.org_id, v.workspace_id, v.signal_code,
                   v.version_number, v.signal_status_code, v.signal_status_name,
                   v.python_hash, v.timeout_ms, v.max_memory_mb,
                   v.is_active, v.created_at::text, v.updated_at::text,
                   v.name, v.description, v.caep_event_type, v.risc_event_type,
                   ps.property_value AS python_source,
                   pp.property_value AS source_prompt
            FROM {SCHEMA}."61_vw_signal_detail" v
            LEFT JOIN {SCHEMA}."45_dtl_signal_properties" ps
                ON ps.signal_id = v.id AND ps.property_key = 'python_source'
            LEFT JOIN {SCHEMA}."45_dtl_signal_properties" pp
                ON pp.signal_id = v.id AND pp.property_key = 'source_prompt'
            WHERE {where_clause}
            ORDER BY {sort_col} {sort_direction}, signal_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_signal(r) for r in rows], total

    async def count_signals(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        workspace_id: str | None = None,
        signal_status_code: str | None = None,
    ) -> int:
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2
        if workspace_id is not None:
            filters.append(f"workspace_id = ${idx}")
            values.append(workspace_id)
            idx += 1
        if signal_status_code is not None:
            filters.append(f"signal_status_code = ${idx}")
            values.append(signal_status_code)
            idx += 1
        where_clause = " AND ".join(filters)
        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."61_vw_signal_detail" WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    # ── single ────────────────────────────────────────────────

    async def get_signal_by_id(
        self, connection: asyncpg.Connection, signal_id: str
    ) -> SignalRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT v.id, v.tenant_key, v.org_id, v.workspace_id, v.signal_code,
                   v.version_number, v.signal_status_code, v.signal_status_name,
                   v.python_hash, v.timeout_ms, v.max_memory_mb,
                   v.is_active, v.created_at::text, v.updated_at::text,
                   v.name, v.description, v.caep_event_type, v.risc_event_type,
                   ps.property_value AS python_source,
                   pp.property_value AS source_prompt
            FROM {SCHEMA}."61_vw_signal_detail" v
            LEFT JOIN {SCHEMA}."45_dtl_signal_properties" ps
                ON ps.signal_id = v.id AND ps.property_key = 'python_source'
            LEFT JOIN {SCHEMA}."45_dtl_signal_properties" pp
                ON pp.signal_id = v.id AND pp.property_key = 'source_prompt'
            WHERE v.id = $1
            """,
            signal_id,
        )
        return _row_to_signal(row) if row else None

    # ── properties ────────────────────────────────────────────

    async def get_signal_properties(
        self, connection: asyncpg.Connection, signal_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."45_dtl_signal_properties"
            WHERE signal_id = $1
            """,
            signal_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    async def list_signal_properties_batch(
        self, connection: asyncpg.Connection, signal_ids: list[str]
    ) -> dict[str, dict[str, str]]:
        """Batch load properties for multiple signals. Returns {signal_id: {key: value}}."""
        if not signal_ids:
            return {}
        rows = await connection.fetch(
            f'''SELECT signal_id, property_key, property_value
                FROM {SCHEMA}."45_dtl_signal_properties"
                WHERE signal_id = ANY($1)''',
            signal_ids,
        )
        result: dict[str, dict[str, str]] = {sid: {} for sid in signal_ids}
        for row in rows:
            result[row["signal_id"]][row["property_key"]] = row["property_value"]
        return result

    # ── create ────────────────────────────────────────────────

    async def create_signal(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        signal_code: str,
        version_number: int,
        signal_status_code: str,
        python_hash: str | None,
        timeout_ms: int,
        max_memory_mb: int,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."22_fct_signals"
                (id, tenant_key, org_id, workspace_id, signal_code,
                 version_number, signal_status_code, python_hash,
                 timeout_ms, max_memory_mb,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8,
                 $9, $10,
                 TRUE, FALSE,
                 $11, $12, $13, $14, NULL, NULL)
            """,
            id,
            tenant_key,
            org_id,
            workspace_id,
            signal_code,
            version_number,
            signal_status_code,
            python_hash,
            timeout_ms,
            max_memory_mb,
            now,
            now,
            created_by,
            created_by,
        )
        return id

    # ── versioning ────────────────────────────────────────────

    async def get_next_version(
        self, connection: asyncpg.Connection, org_id: str, signal_code: str
    ) -> int:
        """Returns the next version number, using an advisory lock to prevent races.
        Must be called inside a transaction."""
        # Advisory lock key: hash of (org_id + signal_code) → deterministic bigint
        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1))",
            f"sb:signal_version:{org_id}:{signal_code}",
        )
        row = await connection.fetchrow(
            f"""
            SELECT COALESCE(MAX(version_number), 0) + 1 AS next_version
            FROM {SCHEMA}."22_fct_signals"
            WHERE org_id = $1 AND signal_code = $2
            """,
            org_id,
            signal_code,
        )
        return row["next_version"]

    async def list_versions(
        self, connection: asyncpg.Connection, org_id: str, signal_code: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT id, version_number, signal_status_code, python_hash,
                   created_at::text, created_by
            FROM {SCHEMA}."22_fct_signals"
            WHERE org_id = $1 AND signal_code = $2 AND is_deleted = FALSE
            ORDER BY version_number DESC
            """,
            org_id,
            signal_code,
        )
        return [dict(r) for r in rows]

    # ── properties upsert ─────────────────────────────────────

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (signal_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."45_dtl_signal_properties"
                (id, signal_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (signal_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── update status ─────────────────────────────────────────

    async def update_signal_status(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
        new_status: str,
        *,
        updated_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."22_fct_signals"
            SET signal_status_code = $1, updated_at = $2, updated_by = $3
            WHERE id = $4 AND is_deleted = FALSE
            """,
            new_status, now, updated_by, signal_id,
        )
        return result != "UPDATE 0"

    # ── soft delete ───────────────────────────────────────────

    async def soft_delete_signal(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."22_fct_signals"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, signal_id,
        )
        return result != "UPDATE 0"

    # ── connector type mapping ────────────────────────────────

    async def add_connector_type_mapping(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
        connector_type_code: str,
        *,
        created_by: str,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."50_lnk_signal_connector_types"
                (id, signal_id, connector_type_code, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, NOW(), $3)
            ON CONFLICT (signal_id, connector_type_code) DO NOTHING
            """,
            signal_id, connector_type_code, created_by,
        )

    # ── test expectations ─────────────────────────────────────

    async def list_test_expectations(
        self, connection: asyncpg.Connection, signal_id: str
    ) -> list[SignalTestExpectationRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, signal_id, dataset_id, expected_result_code, expected_summary_pattern
            FROM {SCHEMA}."49_dtl_signal_test_expectations"
            WHERE signal_id = $1
            """,
            signal_id,
        )
        return [
            SignalTestExpectationRecord(
                id=r["id"],
                signal_id=r["signal_id"],
                dataset_id=r["dataset_id"],
                expected_result_code=r["expected_result_code"],
                expected_summary_pattern=r["expected_summary_pattern"],
            )
            for r in rows
        ]

    async def add_test_expectation(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        signal_id: str,
        dataset_id: str,
        expected_result_code: str,
        expected_summary_pattern: str | None,
        created_by: str,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."49_dtl_signal_test_expectations"
                (id, signal_id, dataset_id, expected_result_code,
                 expected_summary_pattern, created_at, created_by)
            VALUES ($1, $2, $3, $4, $5, NOW(), $6)
            """,
            id, signal_id, dataset_id, expected_result_code,
            expected_summary_pattern, created_by,
        )


def _row_to_signal(r) -> SignalRecord:
    return SignalRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        signal_code=r["signal_code"],
        version_number=r["version_number"],
        signal_status_code=r["signal_status_code"],
        signal_status_name=r.get("signal_status_name"),
        python_hash=r["python_hash"],
        timeout_ms=r["timeout_ms"],
        max_memory_mb=r["max_memory_mb"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r.get("name"),
        description=r.get("description"),
        python_source=r.get("python_source"),
        source_prompt=r.get("source_prompt"),
        caep_event_type=r.get("caep_event_type"),
        risc_event_type=r.get("risc_event_type"),
    )
