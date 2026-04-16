from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import PromotionRecord

SCHEMA = '"15_sandbox"'
GRC_SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.promotions.repository", logger_name="backend.sandbox.promotions.repository.instrumentation")
class PromotionRepository:

    # ── insert ────────────────────────────────────────────────

    async def insert_promotion(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        signal_id: str | None = None,
        policy_id: str | None = None,
        library_id: str | None = None,
        target_test_id: str | None = None,
        promotion_status: str,
        promoted_at: object | None = None,
        promoted_by: str | None = None,
        review_notes: str | None = None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."30_trx_promotions"
                (id, tenant_key, signal_id, policy_id, library_id,
                 target_test_id, promotion_status,
                 promoted_at, promoted_by, review_notes,
                 created_at, created_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7,
                 $8, $9, $10,
                 $11, $12)
            """,
            id,
            tenant_key,
            signal_id,
            policy_id,
            library_id,
            target_test_id,
            promotion_status,
            promoted_at,
            promoted_by,
            review_notes,
            now,
            created_by,
        )
        return id

    # ── list ──────────────────────────────────────────────────

    async def list_promotions(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        *,
        org_id: str | None = None,
        signal_id: str | None = None,
        policy_id: str | None = None,
        library_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PromotionRecord]:
        filters = ["p.tenant_key = $1"]
        values: list[object] = [tenant_key]
        idx = 2

        if signal_id is not None:
            filters.append(f"p.signal_id = ${idx}")
            values.append(signal_id)
            idx += 1
        if policy_id is not None:
            filters.append(f"p.policy_id = ${idx}")
            values.append(policy_id)
            idx += 1
        if library_id is not None:
            filters.append(f"p.library_id = ${idx}")
            values.append(library_id)
            idx += 1
        if org_id is not None:
            filters.append(
                f"""COALESCE(
                    (SELECT s.org_id::text FROM {SCHEMA}."22_fct_signals" s WHERE s.id = p.signal_id LIMIT 1),
                    (SELECT pol.org_id::text FROM {SCHEMA}."24_fct_policies" pol WHERE pol.id = p.policy_id LIMIT 1),
                    (SELECT lib.org_id::text FROM {SCHEMA}."29_fct_libraries" lib WHERE lib.id = p.library_id LIMIT 1)
                ) = ${idx}"""
            )
            values.append(org_id)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT p.id::text, p.tenant_key, p.signal_id::text, p.policy_id::text,
                   p.library_id::text, p.target_test_id::text,
                   p.promotion_status, p.promoted_at::text, p.promoted_by::text,
                   p.review_notes, p.created_at::text, p.created_by::text,
                   COALESCE(
                       (SELECT prop.property_value FROM {SCHEMA}."45_dtl_signal_properties" prop
                        WHERE prop.signal_id = p.signal_id AND prop.property_key = 'name' LIMIT 1),
                       (SELECT prop.property_value FROM {SCHEMA}."47_dtl_policy_properties" prop
                        WHERE prop.policy_id = p.policy_id AND prop.property_key = 'name' LIMIT 1),
                       (SELECT prop.property_value FROM {SCHEMA}."48_dtl_library_properties" prop
                        WHERE prop.library_id = p.library_id AND prop.property_key = 'name' LIMIT 1)
                   ) AS source_name,
                   COALESCE(
                       (SELECT s.signal_code FROM {SCHEMA}."22_fct_signals" s WHERE s.id = p.signal_id LIMIT 1),
                       (SELECT pol.policy_code FROM {SCHEMA}."24_fct_policies" pol WHERE pol.id = p.policy_id LIMIT 1),
                       (SELECT lib.library_code FROM {SCHEMA}."29_fct_libraries" lib WHERE lib.id = p.library_id LIMIT 1)
                   ) AS source_code,
                   COALESCE(
                       (SELECT s.org_id::text FROM {SCHEMA}."22_fct_signals" s WHERE s.id = p.signal_id LIMIT 1),
                       (SELECT pol.org_id::text FROM {SCHEMA}."24_fct_policies" pol WHERE pol.id = p.policy_id LIMIT 1),
                       (SELECT lib.org_id::text FROM {SCHEMA}."29_fct_libraries" lib WHERE lib.id = p.library_id LIMIT 1)
                   ) AS source_org_id,
                   (SELECT ct.test_code FROM {GRC_SCHEMA}."14_fct_control_tests" ct WHERE ct.id = p.target_test_id LIMIT 1) AS target_test_code
            FROM {SCHEMA}."30_trx_promotions" p
            WHERE {where_clause}
            ORDER BY p.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_promotion(r) for r in rows]

    async def count_promotions(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        *,
        org_id: str | None = None,
        signal_id: str | None = None,
        policy_id: str | None = None,
        library_id: str | None = None,
    ) -> int:
        filters = ["tenant_key = $1"]
        values: list[object] = [tenant_key]
        idx = 2

        if signal_id is not None:
            filters.append(f"signal_id = ${idx}")
            values.append(signal_id)
            idx += 1
        if policy_id is not None:
            filters.append(f"policy_id = ${idx}")
            values.append(policy_id)
            idx += 1
        if library_id is not None:
            filters.append(f"library_id = ${idx}")
            values.append(library_id)
            idx += 1
        if org_id is not None:
            filters.append(
                f"""COALESCE(
                    (SELECT s.org_id::text FROM {SCHEMA}."22_fct_signals" s WHERE s.id = p.signal_id LIMIT 1),
                    (SELECT pol.org_id::text FROM {SCHEMA}."24_fct_policies" pol WHERE pol.id = p.policy_id LIMIT 1),
                    (SELECT lib.org_id::text FROM {SCHEMA}."29_fct_libraries" lib WHERE lib.id = p.library_id LIMIT 1)
                ) = ${idx}"""
            )
            values.append(org_id)
            idx += 1

        where_clause = " AND ".join(filters)

        row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."30_trx_promotions" p WHERE {where_clause}',
            *values,
        )
        return row["total"] if row else 0

    # ── get ───────────────────────────────────────────────────

    async def get_promotion(
        self, connection: asyncpg.Connection, promotion_id: str
    ) -> PromotionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT p.id::text, p.tenant_key, p.signal_id::text, p.policy_id::text,
                   p.library_id::text, p.target_test_id::text,
                   p.promotion_status, p.promoted_at::text, p.promoted_by::text,
                   p.review_notes, p.created_at::text, p.created_by::text,
                   COALESCE(
                       (SELECT prop.property_value FROM {SCHEMA}."45_dtl_signal_properties" prop
                        WHERE prop.signal_id = p.signal_id AND prop.property_key = 'name' LIMIT 1),
                       (SELECT prop.property_value FROM {SCHEMA}."47_dtl_policy_properties" prop
                        WHERE prop.policy_id = p.policy_id AND prop.property_key = 'name' LIMIT 1),
                       (SELECT prop.property_value FROM {SCHEMA}."48_dtl_library_properties" prop
                        WHERE prop.library_id = p.library_id AND prop.property_key = 'name' LIMIT 1)
                   ) AS source_name,
                   COALESCE(
                       (SELECT s.signal_code FROM {SCHEMA}."22_fct_signals" s WHERE s.id = p.signal_id LIMIT 1),
                       (SELECT pol.policy_code FROM {SCHEMA}."24_fct_policies" pol WHERE pol.id = p.policy_id LIMIT 1),
                       (SELECT lib.library_code FROM {SCHEMA}."29_fct_libraries" lib WHERE lib.id = p.library_id LIMIT 1)
                   ) AS source_code,
                   COALESCE(
                       (SELECT s.org_id::text FROM {SCHEMA}."22_fct_signals" s WHERE s.id = p.signal_id LIMIT 1),
                       (SELECT pol.org_id::text FROM {SCHEMA}."24_fct_policies" pol WHERE pol.id = p.policy_id LIMIT 1),
                       (SELECT lib.org_id::text FROM {SCHEMA}."29_fct_libraries" lib WHERE lib.id = p.library_id LIMIT 1)
                   ) AS source_org_id,
                   (SELECT ct.test_code FROM {GRC_SCHEMA}."14_fct_control_tests" ct WHERE ct.id = p.target_test_id LIMIT 1) AS target_test_code
            FROM {SCHEMA}."30_trx_promotions" p
            WHERE p.id = $1
            """,
            promotion_id,
        )
        return _row_to_promotion(row) if row else None

    # ── cross-schema: create GRC control test ─────────────────

    async def create_control_test(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        test_code: str,
        test_type_code: str,
        integration_type: str | None = None,
        monitoring_frequency: str = "manual",
        created_by: str,
        now: object,
    ) -> str:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {GRC_SCHEMA}."14_fct_control_tests"
                (id, tenant_key, test_code, test_type_code,
                 integration_type, monitoring_frequency,
                 is_platform_managed, is_active, is_disabled,
                 is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4,
                 $5, $6,
                 FALSE, TRUE, FALSE,
                 FALSE, FALSE, FALSE, FALSE,
                 $7, $8, $9, $10,
                 NULL, NULL)
            ON CONFLICT (tenant_key, test_code) DO UPDATE
                SET test_type_code = EXCLUDED.test_type_code,
                    integration_type = EXCLUDED.integration_type,
                    monitoring_frequency = EXCLUDED.monitoring_frequency,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
            RETURNING id::text
            """,
            id,
            tenant_key,
            test_code,
            test_type_code,
            integration_type,
            monitoring_frequency,
            now,
            now,
            created_by,
            created_by,
        )
        return row["id"] if row else id

    async def upsert_control_test_properties(
        self,
        connection: asyncpg.Connection,
        test_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (test_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {GRC_SCHEMA}."24_dtl_test_properties"
                (id, test_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (test_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    # ── cross-schema: update signal status ────────────────────

    async def update_signal_status(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
        status_code: str,
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
            status_code, now, updated_by, signal_id,
        )
        return result != "UPDATE 0"

    # ── read signal for promotion ─────────────────────────────

    async def get_signal_for_promotion(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT s.id::text, s.tenant_key, s.org_id::text, s.workspace_id::text,
                   s.signal_code, s.signal_status_code,
                   v.name, v.description, v.caep_event_type, v.risc_event_type,
                   (SELECT property_value FROM {SCHEMA}."45_dtl_signal_properties"
                    WHERE signal_id = s.id AND property_key = 'python_source') AS python_source,
                   (SELECT property_value FROM {SCHEMA}."45_dtl_signal_properties"
                    WHERE signal_id = s.id AND property_key = 'source_prompt') AS source_prompt,
                   (SELECT connector_type_code FROM {SCHEMA}."50_lnk_signal_connector_types"
                    WHERE signal_id = s.id LIMIT 1) AS connector_type_code
            FROM {SCHEMA}."22_fct_signals" s
            JOIN {SCHEMA}."61_vw_signal_detail" v ON v.id = s.id
            WHERE s.id = $1 AND s.is_deleted = FALSE
            """,
            signal_id,
        )
        return dict(row) if row else None

    # ── read signal properties ────────────────────────────────

    async def get_signal_properties(
        self,
        connection: asyncpg.Connection,
        signal_id: str,
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

    async def get_signal_properties_for_threat_type(
        self,
        connection: asyncpg.Connection,
        threat_type_id: str,
    ) -> dict[str, str] | None:
        row = await connection.fetchrow(
            f"""
            SELECT sp.property_key, sp.property_value
            FROM {SCHEMA}."45_dtl_signal_properties" sp
            JOIN {SCHEMA}."22_fct_signals" s ON s.id = sp.signal_id
            JOIN {SCHEMA}."23_fct_threat_types" tt ON tt.expression_tree::text LIKE '%' || s.signal_code || '%'
            WHERE tt.id = $1 AND s.is_deleted = FALSE
            ORDER BY s.created_at DESC
            LIMIT 1
            """,
            threat_type_id,
        )
        if not row:
            return None
        rows = await connection.fetch(
            f"""
            SELECT sp.property_key, sp.property_value
            FROM {SCHEMA}."45_dtl_signal_properties" sp
            JOIN {SCHEMA}."22_fct_signals" s ON s.id = sp.signal_id
            WHERE s.id = (SELECT signal_id FROM {SCHEMA}."45_dtl_signal_properties" WHERE property_key = 'name' AND signal_id IN (
                SELECT signal_id FROM {SCHEMA}."50_lnk_signal_connector_types" WHERE signal_id IN (
                    SELECT signal_id FROM {SCHEMA}."52_lnk_live_session_signals" WHERE signal_id IN (
                        SELECT signal_id FROM {SCHEMA}."23_fct_threat_types" tt WHERE tt.id = $1
                    )
                )
            ) ORDER BY (SELECT created_at FROM {SCHEMA}."22_fct_signals" WHERE id = signal_id) DESC LIMIT 1)
            """,
            threat_type_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows} if rows else None

    # ── read policy for promotion ─────────────────────────────

    async def get_policy_for_promotion(
        self,
        connection: asyncpg.Connection,
        policy_id: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, org_id::text, workspace_id::text, policy_code,
                   threat_type_id::text, threat_code, name, description,
                   (SELECT p.property_value
                    FROM {SCHEMA}."47_dtl_policy_properties" p
                    WHERE p.policy_id = v.id AND p.property_key = 'policy_container_code'
                    LIMIT 1) AS policy_container_code,
                   (SELECT p.property_value
                    FROM {SCHEMA}."47_dtl_policy_properties" p
                    WHERE p.policy_id = v.id AND p.property_key = 'policy_container_name'
                    LIMIT 1) AS policy_container_name
            FROM {SCHEMA}."63_vw_policy_detail"
            AS v
            WHERE id = $1
            """,
            policy_id,
        )
        return dict(row) if row else None

    # ── promoted tests dual-write ─────────────────────────────

    async def get_next_promoted_version(
        self, connection: asyncpg.Connection, tenant_key: str, test_code: str
    ) -> int:
        val = await connection.fetchval(
            f'SELECT COALESCE(MAX(version_number), 0) + 1 FROM {SCHEMA}."35_fct_promoted_tests" WHERE tenant_key = $1 AND test_code = $2',
            tenant_key, test_code,
        )
        return int(val)

    async def deactivate_promoted_versions(
        self, connection: asyncpg.Connection, tenant_key: str, test_code: str
    ) -> None:
        await connection.execute(
            f'UPDATE {SCHEMA}."35_fct_promoted_tests" SET is_active = FALSE, updated_at = NOW() WHERE tenant_key = $1 AND test_code = $2 AND is_active = TRUE',
            tenant_key, test_code,
        )

    async def create_promoted_test(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        promotion_id: str,
        source_signal_id: str | None = None,
        source_policy_id: str | None = None,
        source_library_id: str | None = None,
        test_code: str,
        test_type_code: str = "automated",
        monitoring_frequency: str = "manual",
        linked_asset_id: str | None = None,
        version_number: int,
        promoted_by: str,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."35_fct_promoted_tests" (
                id, tenant_key, org_id, workspace_id,
                promotion_id, source_signal_id, source_policy_id, source_library_id,
                test_code, test_type_code, monitoring_frequency,
                linked_asset_id, version_number, is_active,
                promoted_by, promoted_at, created_at, updated_at
            ) VALUES (
                $1, $2, $3::uuid, $4::uuid,
                $5::uuid, $6::uuid, $7::uuid, $8::uuid,
                $9, $10, $11,
                $12::uuid, $13, TRUE,
                $14::uuid, $15, $15, $15
            )
            """,
            id, tenant_key, org_id, workspace_id,
            promotion_id, source_signal_id, source_policy_id, source_library_id,
            test_code, test_type_code, monitoring_frequency,
            linked_asset_id, version_number,
            promoted_by, now,
        )

    async def upsert_promoted_test_properties(
        self,
        connection: asyncpg.Connection,
        test_id: str,
        props: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        for key, value in props.items():
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."36_dtl_promoted_test_properties"
                    (test_id, property_key, property_value, created_by, created_at, updated_at)
                VALUES ($1, $2, $3, $4::uuid, $5, $5)
                ON CONFLICT (test_id, property_key) DO UPDATE
                    SET property_value = EXCLUDED.property_value,
                        updated_at = EXCLUDED.updated_at
                """,
                test_id, key, value, created_by, now,
            )

    # ── read library policies for bulk promotion ──────────────

    async def get_library_policy_ids(
        self,
        connection: asyncpg.Connection,
        library_id: str,
    ) -> list[str]:
        rows = await connection.fetch(
            f"""
            SELECT policy_id::text
            FROM {SCHEMA}."51_lnk_library_policies"
            WHERE library_id = $1
            ORDER BY sort_order ASC
            """,
            library_id,
        )
        return [r["policy_id"] for r in rows]


def _row_to_promotion(r) -> PromotionRecord:
    keys = r.keys() if hasattr(r, "keys") else {}
    return PromotionRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        signal_id=r["signal_id"],
        policy_id=r["policy_id"],
        library_id=r["library_id"],
        target_test_id=r["target_test_id"],
        promotion_status=r["promotion_status"],
        promoted_at=r["promoted_at"],
        promoted_by=r["promoted_by"],
        review_notes=r["review_notes"],
        created_at=r["created_at"],
        created_by=r["created_by"],
        source_name=r["source_name"] if "source_name" in keys else None,
        source_code=r["source_code"] if "source_code" in keys else None,
        target_test_code=r["target_test_code"] if "target_test_code" in keys else None,
        source_org_id=r["source_org_id"] if "source_org_id" in keys else None,
    )
