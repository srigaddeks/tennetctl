from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import GlobalRiskDetailRecord, GlobalRiskRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_VALID_SORT_FIELDS = {"title", "created_at", "updated_at", "inherent_risk_score", "risk_category_code"}


@instrument_class_methods(namespace="grc.global_risks.repository", logger_name="backend.grc.global_risks.repository.instrumentation")
class GlobalRiskRepository:

    async def list_global_risks(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        category: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[GlobalRiskDetailRecord], int]:
        conditions = ["v.tenant_key = $1", "v.is_deleted = FALSE"]
        args: list[object] = [tenant_key]
        idx = 2

        if category is not None:
            conditions.append(f"v.risk_category_code = ${idx}")
            args.append(category)
            idx += 1
        if search is not None:
            conditions.append(f"(v.title ILIKE ${idx} OR v.risk_code ILIKE ${idx})")
            args.append(f"%{search}%")
            idx += 1

        where = " AND ".join(conditions)
        safe_sort = sort_by if sort_by in _VALID_SORT_FIELDS else "title"
        order_dir = "ASC" if not sort_dir or sort_dir.lower() == "asc" else "DESC"

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."69_vw_global_risk_detail" v WHERE {where}',
            *args,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, risk_code, risk_category_code, risk_category_name,
                   risk_level_code, risk_level_name, risk_level_color,
                   inherent_likelihood, inherent_impact, inherent_risk_score,
                   is_active,
                   created_at::text, updated_at::text, created_by::text,
                   title, description, short_description, mitigation_guidance, detection_guidance,
                   linked_control_count
            FROM {SCHEMA}."69_vw_global_risk_detail" v
            WHERE {where}
            ORDER BY v.{safe_sort} {order_dir}, v.risk_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        return [_row_to_detail(r) for r in rows], total

    async def get_by_id(
        self, connection: asyncpg.Connection, global_risk_id: str
    ) -> GlobalRiskDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, risk_code, risk_category_code, risk_category_name,
                   risk_level_code, risk_level_name, risk_level_color,
                   inherent_likelihood, inherent_impact, inherent_risk_score,
                   is_active,
                   created_at::text, updated_at::text, created_by::text,
                   title, description, short_description, mitigation_guidance, detection_guidance,
                   linked_control_count
            FROM {SCHEMA}."69_vw_global_risk_detail"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            global_risk_id,
        )
        return _row_to_detail(row) if row else None

    async def get_by_code(
        self, connection: asyncpg.Connection, risk_code: str
    ) -> GlobalRiskRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, risk_code, risk_category_code, risk_level_code,
                   inherent_likelihood, inherent_impact, inherent_risk_score,
                   is_active,
                   created_at::text, updated_at::text, created_by::text
            FROM {SCHEMA}."50_fct_global_risks"
            WHERE risk_code = $1 AND is_deleted = FALSE
            """,
            risk_code,
        )
        return _row_to_record(row) if row else None

    async def create(
        self,
        connection: asyncpg.Connection,
        *,
        risk_id: str,
        tenant_key: str,
        risk_code: str,
        risk_category_code: str,
        risk_level_code: str | None,
        inherent_likelihood: int | None,
        inherent_impact: int | None,
        created_by: str,
        now: object,
    ) -> GlobalRiskRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."50_fct_global_risks"
                (id, tenant_key, risk_code, risk_category_code, risk_level_code,
                 inherent_likelihood, inherent_impact,
                 is_active, is_deleted, is_system,
                 created_at, updated_at, created_by, updated_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7,
                 TRUE, FALSE, FALSE,
                 $8, $9, $10, $11)
            RETURNING id, tenant_key, risk_code, risk_category_code, risk_level_code,
                      inherent_likelihood, inherent_impact, inherent_risk_score,
                      is_active,
                      created_at::text, updated_at::text, created_by::text
            """,
            risk_id, tenant_key, risk_code, risk_category_code, risk_level_code,
            inherent_likelihood, inherent_impact, now, now, created_by, created_by,
        )
        return _row_to_record(row)

    async def update(
        self,
        connection: asyncpg.Connection,
        global_risk_id: str,
        *,
        risk_category_code: str | None = None,
        risk_level_code: str | None = None,
        inherent_likelihood: int | None = None,
        inherent_impact: int | None = None,
        updated_by: str,
        now: object,
    ) -> GlobalRiskRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        for col, val in [
            ("risk_category_code", risk_category_code),
            ("risk_level_code", risk_level_code),
            ("inherent_likelihood", inherent_likelihood),
            ("inherent_impact", inherent_impact),
        ]:
            if val is not None:
                fields.append(f"{col} = ${idx}")
                values.append(val)
                idx += 1

        values.append(global_risk_id)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."50_fct_global_risks"
            SET {", ".join(fields)}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, tenant_key, risk_code, risk_category_code, risk_level_code,
                      inherent_likelihood, inherent_impact, inherent_risk_score,
                      is_active,
                      created_at::text, updated_at::text, created_by::text
            """,
            *values,
        )
        return _row_to_record(row) if row else None

    async def soft_delete(
        self, connection: asyncpg.Connection, global_risk_id: str, *, deleted_by: str, now: object
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."50_fct_global_risks"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1, deleted_by = $2,
                updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, global_risk_id,
        )
        return result != "UPDATE 0"

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        *,
        global_risk_id: str,
        properties: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (global_risk_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {SCHEMA}."56_dtl_global_risk_properties"
                    (id, global_risk_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (global_risk_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
            rows,
        )

    async def link_control(
        self,
        connection: asyncpg.Connection,
        *,
        global_risk_id: str,
        control_id: str,
        mapping_type: str,
        created_by: str,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."61_lnk_global_risk_control_mappings"
                (id, global_risk_id, control_id, mapping_type, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
            ON CONFLICT (global_risk_id, control_id) DO UPDATE
            SET mapping_type = EXCLUDED.mapping_type
            """,
            global_risk_id, control_id, mapping_type, now, created_by,
        )

    async def unlink_control(
        self, connection: asyncpg.Connection, *, global_risk_id: str, control_id: str
    ) -> bool:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."61_lnk_global_risk_control_mappings" WHERE global_risk_id = $1 AND control_id = $2',
            global_risk_id, control_id,
        )
        return result != "DELETE 0"

    async def write_review_event(
        self,
        connection: asyncpg.Connection,
        *,
        global_risk_id: str,
        event_type: str,
        from_status: str | None = None,
        to_status: str | None = None,
        actor_id: str | None = None,
        notes: str | None = None,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."66_trx_global_risk_review_events"
                (id, global_risk_id, event_type, from_status, to_status, actor_id, notes, occurred_at)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            """,
            global_risk_id, event_type, from_status, to_status, actor_id, notes, now,
        )


def _row_to_record(r) -> GlobalRiskRecord:
    return GlobalRiskRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        risk_code=r["risk_code"],
        risk_category_code=r["risk_category_code"],
        risk_level_code=r["risk_level_code"],
        inherent_likelihood=r["inherent_likelihood"],
        inherent_impact=r["inherent_impact"],
        inherent_risk_score=r["inherent_risk_score"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )


def _row_to_detail(r) -> GlobalRiskDetailRecord:
    return GlobalRiskDetailRecord(
        id=str(r["id"]),
        tenant_key=r["tenant_key"],
        risk_code=r["risk_code"],
        risk_category_code=r["risk_category_code"],
        risk_category_name=r["risk_category_name"],
        risk_level_code=r["risk_level_code"],
        risk_level_name=r["risk_level_name"],
        risk_level_color=r["risk_level_color"],
        inherent_likelihood=r["inherent_likelihood"],
        inherent_impact=r["inherent_impact"],
        inherent_risk_score=r["inherent_risk_score"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
        title=r["title"],
        description=r["description"],
        short_description=r["short_description"],
        mitigation_guidance=r["mitigation_guidance"],
        detection_guidance=r["detection_guidance"],
        linked_control_count=r["linked_control_count"],
    )
