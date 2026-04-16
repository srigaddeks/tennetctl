from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import RiskDetailRecord, RiskRecord

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


_VALID_RISK_SORT_FIELDS = {"created_at", "updated_at", "risk_level", "title"}


@instrument_class_methods(namespace="risk.risks.repository", logger_name="backend.risk.risks.repository.instrumentation")
class RiskRepository:
    async def list_risks_for_control(
        self,
        connection: asyncpg.Connection,
        *,
        control_id: str,
        tenant_key: str,
    ) -> list[RiskDetailRecord]:
        rows = await connection.fetch(
            f"""
            SELECT
                v.id::text, v.tenant_key, v.risk_code,
                v.org_id::text, v.workspace_id::text,
                v.risk_category_code, v.category_name,
                v.risk_level_code, v.risk_level_name, v.risk_level_color,
                v.treatment_type_code, v.treatment_type_name,
                v.source_type, v.risk_status, v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text,
                v.title, v.description, v.notes, v.owner_user_id,
                v.business_impact,
                v.inherent_risk_score, v.residual_risk_score,
                v.linked_control_count, v.treatment_plan_status,
                v.treatment_plan_target_date, v.version
            FROM {SCHEMA}."40_vw_risk_detail" v
            JOIN {SCHEMA}."30_lnk_risk_control_mappings" m
                ON m.risk_id = v.id
            WHERE m.control_id = $1::uuid
              AND v.is_deleted = FALSE
              AND v.tenant_key = $2
            ORDER BY v.created_at
            """,
            control_id,
            tenant_key,
        )
        return [_row_to_detail(r) for r in rows]

    async def list_risks(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        category: str | None = None,
        status: str | None = None,
        level: str | None = None,
        search: str | None = None,
        treatment_type: str | None = None,
        control_id: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[RiskDetailRecord], int]:
        conditions = ["v.is_deleted = FALSE", "v.tenant_key = $1"]
        args: list[object] = [tenant_key]
        idx = 2

        if org_id is not None:
            conditions.append(f"v.org_id = ${idx}::uuid")
            args.append(org_id)
            idx += 1
        if workspace_id is not None:
            conditions.append(f"v.workspace_id = ${idx}::uuid")
            args.append(workspace_id)
            idx += 1
        if category is not None:
            conditions.append(f"v.risk_category_code = ${idx}")
            args.append(category)
            idx += 1
        if status is not None:
            conditions.append(f"v.risk_status = ${idx}")
            args.append(status)
            idx += 1
        if level is not None:
            conditions.append(f"v.risk_level_code = ${idx}")
            args.append(level)
            idx += 1
        if treatment_type is not None:
            conditions.append(f"v.treatment_type_code = ${idx}")
            args.append(treatment_type)
            idx += 1
        if search is not None:
            conditions.append(f"(v.title ILIKE ${idx} OR v.risk_code ILIKE ${idx})")
            args.append(f"%{search}%")
            idx += 1
        if control_id is not None:
            conditions.append(
                f"EXISTS (SELECT 1 FROM {SCHEMA}.\"30_lnk_risk_control_mappings\" m WHERE m.risk_id = v.id AND m.control_id = ${idx}::uuid)"
            )
            args.append(control_id)
            idx += 1

        where_clause = " AND ".join(conditions)

        # Build ORDER BY
        safe_sort = sort_by if sort_by in _VALID_RISK_SORT_FIELDS else None
        if safe_sort == "risk_level":
            order_expr = "v.risk_level_code"
        elif safe_sort == "title":
            order_expr = "v.title"
        elif safe_sort == "updated_at":
            order_expr = "v.updated_at"
        else:
            order_expr = "v.created_at"
        order_dir = "ASC" if sort_dir and sort_dir.lower() == "asc" else "DESC"

        rows = await connection.fetch(
            f"""
            SELECT
                v.id::text, v.tenant_key, v.risk_code,
                v.org_id::text, v.workspace_id::text,
                v.risk_category_code, v.category_name,
                v.risk_level_code, v.risk_level_name, v.risk_level_color,
                v.treatment_type_code, v.treatment_type_name,
                v.source_type, v.risk_status, v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text,
                v.title, v.description, v.notes, v.owner_user_id,
                v.business_impact,
                v.inherent_risk_score, v.residual_risk_score,
                v.linked_control_count, v.treatment_plan_status,
                v.treatment_plan_target_date, v.version,
                COUNT(*) OVER() AS _total
            FROM {SCHEMA}."40_vw_risk_detail" v
            WHERE {where_clause}
            ORDER BY {order_expr} {order_dir}
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_detail(r) for r in rows], total

    async def get_risk_detail(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> RiskDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT
                v.id::text, v.tenant_key, v.risk_code,
                v.org_id::text, v.workspace_id::text,
                v.risk_category_code, v.category_name,
                v.risk_level_code, v.risk_level_name, v.risk_level_color,
                v.treatment_type_code, v.treatment_type_name,
                v.source_type, v.risk_status, v.is_active,
                v.created_at::text, v.updated_at::text, v.created_by::text,
                v.title, v.description, v.notes, v.owner_user_id,
                v.business_impact,
                v.inherent_risk_score, v.residual_risk_score,
                v.linked_control_count, v.treatment_plan_status,
                v.treatment_plan_target_date, v.version
            FROM {SCHEMA}."40_vw_risk_detail" v
            WHERE v.id = $1::uuid AND v.is_deleted = FALSE
            """,
            risk_id,
        )
        return _row_to_detail(row) if row else None

    async def get_risk_by_id(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> RiskRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, risk_code, org_id::text, workspace_id::text,
                   risk_category_code, risk_level_code, treatment_type_code,
                   source_type, risk_status, is_active, version,
                   created_at::text, updated_at::text, created_by::text
            FROM {SCHEMA}."10_fct_risks"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            risk_id,
        )
        return _row_to_risk(row) if row else None

    async def create_risk(
        self,
        connection: asyncpg.Connection,
        *,
        risk_id: str,
        tenant_key: str,
        risk_code: str,
        org_id: str,
        workspace_id: str,
        risk_category_code: str,
        risk_level_code: str = "medium",
        treatment_type_code: str,
        source_type: str,
        created_by: str,
        now: datetime,
    ) -> RiskRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."10_fct_risks" (
                id, tenant_key, risk_code, org_id, workspace_id,
                risk_category_code, risk_level_code, treatment_type_code,
                source_type, risk_status,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES (
                $1::uuid, $2, $3, $4::uuid, $5::uuid,
                $6, $7, $8,
                $9, 'identified',
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $10, $11, $12::uuid, $13::uuid, NULL, NULL
            )
            RETURNING id::text, tenant_key, risk_code, org_id::text, workspace_id::text,
                      risk_category_code, risk_level_code, treatment_type_code,
                      source_type, risk_status, is_active, version,
                      created_at::text, updated_at::text, created_by::text
            """,
            risk_id,
            tenant_key,
            risk_code,
            org_id,
            workspace_id,
            risk_category_code,
            risk_level_code,
            treatment_type_code,
            source_type,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_risk(row)

    async def upsert_risk_property(
        self,
        connection: asyncpg.Connection,
        *,
        prop_id: str,
        risk_id: str,
        property_key: str,
        property_value: str,
        actor_id: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_dtl_risk_properties" (
                id, risk_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8::uuid)
            ON CONFLICT (risk_id, property_key)
            DO UPDATE SET
                property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            prop_id,
            risk_id,
            property_key,
            property_value,
            now,
            now,
            actor_id,
            actor_id,
        )

    async def upsert_risk_properties_batch(
        self,
        connection: asyncpg.Connection,
        *,
        risk_id: str,
        properties: dict[str, str],
        actor_id: str,
        now: datetime,
    ) -> None:
        if not properties:
            return
        from uuid import uuid4
        rows = [
            (str(uuid4()), risk_id, key, value, now, now, actor_id, actor_id)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."20_dtl_risk_properties" (
                id, risk_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8::uuid)
            ON CONFLICT (risk_id, property_key)
            DO UPDATE SET
                property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    async def update_risk(
        self,
        connection: asyncpg.Connection,
        risk_id: str,
        *,
        risk_category_code: str | None = None,
        risk_level_code: str | None = None,
        treatment_type_code: str | None = None,
        risk_status: str | None = None,
        is_disabled: bool | None = None,
        updated_by: str,
        now: datetime,
    ) -> RiskRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2::uuid", "version = version + 1"]
        values: list[object] = [now, updated_by]
        idx = 3

        if risk_category_code is not None:
            fields.append(f"risk_category_code = ${idx}")
            values.append(risk_category_code)
            idx += 1
        if risk_level_code is not None:
            fields.append(f"risk_level_code = ${idx}")
            values.append(risk_level_code)
            idx += 1
        if treatment_type_code is not None:
            fields.append(f"treatment_type_code = ${idx}")
            values.append(treatment_type_code)
            idx += 1
        if risk_status is not None:
            fields.append(f"risk_status = ${idx}")
            values.append(risk_status)
            idx += 1
        if is_disabled is not None:
            fields.append(f"is_active = ${idx}")
            values.append(not is_disabled)
            idx += 1

        values.append(risk_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."10_fct_risks"
            SET {set_clause}
            WHERE id = ${idx}::uuid AND is_deleted = FALSE
            RETURNING id::text, tenant_key, risk_code, org_id::text, workspace_id::text,
                      risk_category_code, risk_level_code, treatment_type_code,
                      source_type, risk_status, is_active, version,
                      created_at::text, updated_at::text, created_by::text
            """,
            *values,
        )
        return _row_to_risk(row) if row else None

    async def soft_delete_risk(
        self,
        connection: asyncpg.Connection,
        risk_id: str,
        *,
        deleted_by: str,
        now: datetime,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_risks"
            SET is_active = FALSE, is_deleted = TRUE,
                updated_at = $1, updated_by = $2::uuid,
                deleted_at = $3, deleted_by = $4::uuid
            WHERE id = $5::uuid AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            risk_id,
        )
        return result != "UPDATE 0"

    async def update_risk_level(
        self,
        connection: asyncpg.Connection,
        risk_id: str,
        risk_level_code: str,
        *,
        updated_by: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_risks"
            SET risk_level_code = $1, updated_at = $2, updated_by = $3::uuid
            WHERE id = $4::uuid AND is_deleted = FALSE
            """,
            risk_level_code,
            now,
            updated_by,
            risk_id,
        )

    async def get_heat_map_data(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict]:
        """Aggregate risks into a 5x5 heat map matrix (likelihood x impact)."""
        query = """
            WITH latest_assessments AS (
                SELECT DISTINCT ON (ra.risk_id)
                    ra.risk_id,
                    ra.likelihood_score,
                    ra.impact_score,
                    ra.risk_score
                FROM "14_risk_registry"."32_trx_risk_assessments" ra
                JOIN "14_risk_registry"."10_fct_risks" r ON r.id = ra.risk_id
                WHERE r.tenant_key = $1 AND r.is_deleted = FALSE AND r.is_active = TRUE
        """
        params: list[object] = [tenant_key]
        idx = 2
        if org_id:
            query += f" AND r.org_id = ${idx}::uuid"
            params.append(org_id)
            idx += 1
        if workspace_id:
            query += f" AND r.workspace_id = ${idx}::uuid"
            params.append(workspace_id)
            idx += 1

        query += """
                ORDER BY ra.risk_id, ra.assessed_at DESC
            )
            SELECT
                la.likelihood_score,
                la.impact_score,
                COUNT(*)::int AS risk_count,
                ARRAY_AGG(la.risk_id::text) AS risk_ids
            FROM latest_assessments la
            GROUP BY la.likelihood_score, la.impact_score
            ORDER BY la.likelihood_score, la.impact_score
        """
        rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

    async def get_risk_summary(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> dict:
        """Get risk dashboard KPIs."""
        base_where = "WHERE r.tenant_key = $1 AND r.is_deleted = FALSE AND r.is_active = TRUE"
        params: list[object] = [tenant_key]
        idx = 2
        if org_id:
            base_where += f" AND r.org_id = ${idx}::uuid"
            params.append(org_id)
            idx += 1
        if workspace_id:
            base_where += f" AND r.workspace_id = ${idx}::uuid"
            params.append(workspace_id)
            idx += 1

        query = f"""
            SELECT
                COUNT(*)::int AS total_risks,
                COUNT(*) FILTER (WHERE r.risk_status = 'identified')::int AS identified_count,
                COUNT(*) FILTER (WHERE r.risk_status = 'assessed')::int AS assessed_count,
                COUNT(*) FILTER (WHERE r.risk_status = 'treating')::int AS treating_count,
                COUNT(*) FILTER (WHERE r.risk_status = 'accepted')::int AS accepted_count,
                COUNT(*) FILTER (WHERE r.risk_status = 'closed')::int AS closed_count,
                COUNT(*) FILTER (WHERE r.risk_level_code = 'critical')::int AS critical_count,
                COUNT(*) FILTER (WHERE r.risk_level_code = 'high')::int AS high_count,
                COUNT(*) FILTER (WHERE r.risk_level_code = 'medium')::int AS medium_count,
                COUNT(*) FILTER (WHERE r.risk_level_code = 'low')::int AS low_count,
                COUNT(*) FILTER (WHERE r.risk_status NOT IN ('accepted', 'closed'))::int AS open_count,
                COUNT(*) FILTER (WHERE r.created_at >= NOW() - INTERVAL '7 days')::int AS created_this_week,
                COUNT(*) FILTER (WHERE r.risk_status = 'closed' AND r.updated_at >= NOW() - INTERVAL '7 days')::int AS closed_this_week
            FROM "14_risk_registry"."10_fct_risks" r
            {base_where}
        """
        row = await connection.fetchrow(query, *params)
        return dict(row)

    async def export_risks_for_csv(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> list[dict]:
        """Fetch all risk data flattened for CSV export."""
        query = """
            SELECT
                r.risk_code, r.risk_status, r.risk_category_code, r.risk_level_code,
                r.treatment_type_code, r.source_type, r.created_at::text, r.updated_at::text,
                title.property_value AS title,
                descr.property_value AS description,
                owner.property_value AS owner_user_id,
                impact.property_value AS business_impact
            FROM "14_risk_registry"."10_fct_risks" r
            LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" title
                ON title.risk_id = r.id AND title.property_key = 'title'
            LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" descr
                ON descr.risk_id = r.id AND descr.property_key = 'description'
            LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" owner
                ON owner.risk_id = r.id AND owner.property_key = 'owner_user_id'
            LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" impact
                ON impact.risk_id = r.id AND impact.property_key = 'business_impact'
            WHERE r.tenant_key = $1 AND r.is_deleted = FALSE
        """
        params: list[object] = [tenant_key]
        idx = 2
        if org_id:
            query += f" AND r.org_id = ${idx}::uuid"
            params.append(org_id)
            idx += 1
        if workspace_id:
            query += f" AND r.workspace_id = ${idx}::uuid"
            params.append(workspace_id)
            idx += 1

        query += " ORDER BY r.created_at DESC"
        rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

    async def resolve_owner_display_name(
        self, connection: asyncpg.Connection, user_id: str
    ) -> str | None:
        """Resolve a user ID to display name."""
        row = await connection.fetchrow(
            """
            SELECT property_value FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = $1::uuid AND property_key = 'display_name'
            """,
            user_id,
        )
        return row["property_value"] if row else None

    async def resolve_owner_names_batch(
        self, connection: asyncpg.Connection, user_ids: list[str]
    ) -> dict[str, str]:
        """Batch resolve user IDs to display names."""
        if not user_ids:
            return {}
        rows = await connection.fetch(
            """
            SELECT user_id::text, property_value
            FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = ANY($1::uuid[]) AND property_key = 'display_name'
            """,
            user_ids,
        )
        return {row["user_id"]: row["property_value"] for row in rows}

    # ─── Group Assignment ────────────────────────────────────────────────

    async def list_risk_groups(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT rga.id::text, rga.risk_id::text, rga.group_id::text, rga.role,
                   rga.assigned_by::text, rga.assigned_at::text,
                   ug.name AS group_name
            FROM {SCHEMA}."34_lnk_risk_group_assignments" rga
            LEFT JOIN "03_auth_manage"."17_fct_user_groups" ug ON ug.id = rga.group_id
            WHERE rga.risk_id = $1::uuid
            ORDER BY rga.assigned_at
            """,
            risk_id,
        )
        return [dict(row) for row in rows]

    async def assign_risk_group(
        self,
        connection: asyncpg.Connection,
        risk_id: str,
        group_id: str,
        role: str,
        assigned_by: str,
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."34_lnk_risk_group_assignments"
                (risk_id, group_id, role, assigned_by)
            VALUES ($1::uuid, $2::uuid, $3, $4::uuid)
            ON CONFLICT (risk_id, group_id, role) DO NOTHING
            RETURNING id::text, risk_id::text, group_id::text, role,
                      assigned_by::text, assigned_at::text
            """,
            risk_id,
            group_id,
            role,
            assigned_by,
        )
        return dict(row) if row else None

    async def unassign_risk_group(
        self, connection: asyncpg.Connection, assignment_id: str
    ) -> bool:
        result = await connection.execute(
            f'DELETE FROM {SCHEMA}."34_lnk_risk_group_assignments" WHERE id = $1::uuid',
            assignment_id,
        )
        return result == "DELETE 1"

    # ─── Risk Appetite / Tolerance ───────────────────────────────────────

    async def get_risk_appetite(
        self, connection: asyncpg.Connection, org_id: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, tenant_key, org_id::text, risk_category_code,
                   appetite_level_code, tolerance_threshold, max_acceptable_score,
                   description, is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."35_fct_risk_appetite"
            WHERE org_id = $1::uuid AND is_active = TRUE
            ORDER BY risk_category_code
            """,
            org_id,
        )
        return [dict(row) for row in rows]

    async def upsert_risk_appetite(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        tenant_key: str,
        category_code: str,
        appetite_level_code: str,
        tolerance_threshold: int,
        max_acceptable_score: int,
        description: str | None,
        created_by: str,
    ) -> dict:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."35_fct_risk_appetite"
                (tenant_key, org_id, risk_category_code, appetite_level_code,
                 tolerance_threshold, max_acceptable_score, description, created_by)
            VALUES ($1, $2::uuid, $3, $4, $5, $6, $7, $8::uuid)
            ON CONFLICT (org_id, risk_category_code)
            DO UPDATE SET appetite_level_code = $4, tolerance_threshold = $5,
                max_acceptable_score = $6, description = $7,
                updated_by = $8::uuid, updated_at = NOW()
            RETURNING id::text, tenant_key, org_id::text, risk_category_code,
                appetite_level_code, tolerance_threshold, max_acceptable_score, description
            """,
            tenant_key,
            org_id,
            category_code,
            appetite_level_code,
            tolerance_threshold,
            max_acceptable_score,
            description,
            created_by,
        )
        return dict(row)

    # ─── Scheduled Reviews ───────────────────────────────────────────────

    async def get_review_schedule(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> dict | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, risk_id::text, tenant_key, review_frequency,
                   next_review_date::text, last_reviewed_at::text,
                   last_reviewed_by::text, assigned_reviewer_id::text,
                   is_overdue, is_active
            FROM {SCHEMA}."36_trx_scheduled_reviews"
            WHERE risk_id = $1::uuid AND is_active = TRUE
            """,
            risk_id,
        )
        return dict(row) if row else None

    async def upsert_review_schedule(
        self,
        connection: asyncpg.Connection,
        *,
        risk_id: str,
        tenant_key: str,
        frequency: str,
        next_review_date: str,
        reviewer_id: str | None,
        created_by: str,
    ) -> dict:
        from datetime import date as date_type

        parsed_date = date_type.fromisoformat(next_review_date)
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."36_trx_scheduled_reviews"
                (risk_id, tenant_key, review_frequency, next_review_date,
                 assigned_reviewer_id, created_by)
            VALUES ($1::uuid, $2, $3, $4, $5::uuid, $6::uuid)
            ON CONFLICT (risk_id)
            DO UPDATE SET review_frequency = $3, next_review_date = $4,
                assigned_reviewer_id = $5::uuid, updated_at = NOW()
            RETURNING id::text, risk_id::text, review_frequency,
                next_review_date::text, assigned_reviewer_id::text,
                is_overdue, is_active
            """,
            risk_id,
            tenant_key,
            frequency,
            parsed_date,
            reviewer_id,
            created_by,
        )
        return dict(row)

    async def complete_review(
        self,
        connection: asyncpg.Connection,
        risk_id: str,
        reviewer_id: str,
        next_date: str,
    ) -> dict | None:
        from datetime import date as date_type

        parsed_date = date_type.fromisoformat(next_date)
        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."36_trx_scheduled_reviews"
            SET last_reviewed_at = NOW(), last_reviewed_by = $2::uuid,
                next_review_date = $3, updated_at = NOW()
            WHERE risk_id = $1::uuid AND is_active = TRUE
            RETURNING id::text, risk_id::text, review_frequency,
                next_review_date::text, last_reviewed_at::text,
                last_reviewed_by::text, is_overdue
            """,
            risk_id,
            reviewer_id,
            parsed_date,
        )
        return dict(row) if row else None

    async def list_overdue_reviews(
        self,
        connection: asyncpg.Connection,
        tenant_key: str,
        org_id: str | None = None,
    ) -> list[dict]:
        query = f"""
            SELECT sr.id::text, sr.risk_id::text, sr.review_frequency,
                   sr.next_review_date::text, sr.assigned_reviewer_id::text,
                   sr.is_overdue,
                   rp.property_value AS risk_title
            FROM {SCHEMA}."36_trx_scheduled_reviews" sr
            JOIN {SCHEMA}."10_fct_risks" r ON r.id = sr.risk_id
            LEFT JOIN {SCHEMA}."20_dtl_risk_properties" rp
                ON rp.risk_id = sr.risk_id AND rp.property_key = 'title'
            WHERE sr.is_active = TRUE AND r.tenant_key = $1 AND r.is_deleted = FALSE
            AND sr.next_review_date <= CURRENT_DATE
        """
        params: list[object] = [tenant_key]
        if org_id:
            query += " AND r.org_id = $2::uuid"
            params.append(org_id)
        query += " ORDER BY sr.next_review_date ASC"
        rows = await connection.fetch(query, *params)
        return [dict(row) for row in rows]

    async def resolve_risk_level_for_score(
        self, connection: asyncpg.Connection, score: int
    ) -> str | None:
        row = await connection.fetchrow(
            f"""
            SELECT code FROM {SCHEMA}."04_dim_risk_levels"
            WHERE score_min <= $1 AND $1 <= score_max AND is_active = TRUE
            ORDER BY sort_order LIMIT 1
            """,
            score,
        )
        return row["code"] if row else None


def _row_to_risk(r) -> RiskRecord:
    return RiskRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        risk_code=r["risk_code"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        risk_category_code=r["risk_category_code"],
        risk_level_code=r["risk_level_code"],
        treatment_type_code=r["treatment_type_code"],
        source_type=r["source_type"],
        risk_status=r["risk_status"],
        is_active=r["is_active"],
        version=r["version"] if "version" in r.keys() else 1,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )


def _row_to_detail(r) -> RiskDetailRecord:
    return RiskDetailRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        risk_code=r["risk_code"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        risk_category_code=r["risk_category_code"],
        category_name=r["category_name"],
        risk_level_code=r["risk_level_code"],
        risk_level_name=r["risk_level_name"],
        risk_level_color=r["risk_level_color"],
        treatment_type_code=r["treatment_type_code"],
        treatment_type_name=r["treatment_type_name"],
        source_type=r["source_type"],
        risk_status=r["risk_status"],
        is_active=r["is_active"],
        version=r["version"] if "version" in r.keys() else 1,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
        title=r["title"],
        description=r["description"],
        notes=r["notes"],
        owner_user_id=r["owner_user_id"],
        business_impact=r["business_impact"],
        inherent_risk_score=r["inherent_risk_score"],
        residual_risk_score=r["residual_risk_score"],
        linked_control_count=r["linked_control_count"],
        treatment_plan_status=r["treatment_plan_status"],
        treatment_plan_target_date=r["treatment_plan_target_date"],
    )
