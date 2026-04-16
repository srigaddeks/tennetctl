from __future__ import annotations

import asyncpg

from .models import ControlCandidate

_RISKS_VIEW = '"14_risk_registry"."40_vw_risk_detail"'
_RISKS = '"14_risk_registry"."10_fct_risks"'
_MAPPINGS = '"14_risk_registry"."30_lnk_risk_control_mappings"'
_CONTROLS = '"05_grc_library"."13_fct_controls"'
_FRAMEWORKS = '"05_grc_library"."10_fct_frameworks"'
_CTRL_PROPS = '"05_grc_library"."23_dtl_control_properties"'
_FW_PROPS = '"05_grc_library"."20_dtl_framework_properties"'
_JOBS = '"20_ai"."45_fct_job_queue"'


class RiskAdvisorRepository:

    async def fetch_risk_detail(
        self, conn: asyncpg.Connection, risk_id: str
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT
                v.id::text, v.risk_code, v.risk_category_code, v.category_name,
                v.risk_level_code, v.risk_level_name,
                v.title, v.description, v.business_impact, v.notes,
                v.org_id::text, v.workspace_id::text, v.tenant_key
            FROM {_RISKS_VIEW} v
            WHERE v.id = $1::uuid AND v.is_deleted = FALSE
            """,
            risk_id,
        )
        return dict(row) if row else None

    async def fetch_already_linked_control_ids(
        self, conn: asyncpg.Connection, risk_id: str
    ) -> list[str]:
        rows = await conn.fetch(
            f"SELECT control_id::text FROM {_MAPPINGS} WHERE risk_id = $1::uuid",
            risk_id,
        )
        return [r["control_id"] for r in rows]

    async def fetch_candidate_controls(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        framework_ids: list[str] | None = None,
        limit: int = 200,
    ) -> list[ControlCandidate]:
        params: list = [tenant_key, org_id]
        fw_filter = ""
        if framework_ids:
            params.append(framework_ids)
            fw_filter = f"AND f.id = ANY(${len(params)}::uuid[])"

        params.extend([limit])
        limit_ph = f"${len(params)}"

        rows = await conn.fetch(
            f"""
            SELECT
                c.id::text          AS control_id,
                c.control_code,
                c.criticality_code,
                c.control_category_code,
                c.framework_id::text,
                f.framework_code,
                p_name.property_value   AS control_name,
                p_desc.property_value   AS description,
                p_tags.property_value   AS tags,
                p_fw.property_value     AS framework_name
            FROM {_CONTROLS} c
            JOIN {_FRAMEWORKS} f
                ON f.id = c.framework_id
                AND f.is_active = TRUE AND f.is_deleted = FALSE
                AND f.tenant_key = $1
                AND (f.scope_org_id IS NULL OR f.scope_org_id = $2::uuid)
                {fw_filter}
            LEFT JOIN {_CTRL_PROPS} p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN {_CTRL_PROPS} p_desc
                ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN {_CTRL_PROPS} p_tags
                ON p_tags.control_id = c.id AND p_tags.property_key = 'tags'
            LEFT JOIN {_FW_PROPS} p_fw
                ON p_fw.framework_id = f.id AND p_fw.property_key = 'name'
            WHERE c.is_active = TRUE AND c.is_deleted = FALSE
            ORDER BY f.framework_code, c.control_code
            LIMIT {limit_ph}
            """,
            *params,
        )
        return [
            ControlCandidate(
                control_id=r["control_id"],
                control_code=r["control_code"],
                control_name=r["control_name"],
                control_category_code=r["control_category_code"],
                criticality_code=r["criticality_code"],
                framework_id=r["framework_id"],
                framework_code=r["framework_code"],
                framework_name=r["framework_name"],
                tags=r["tags"],
                description=r["description"],
            )
            for r in rows
        ]

    async def fetch_risks_for_bulk(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        risk_id: str | None = None,
        limit: int = 500,
    ) -> list[dict]:
        rows = await conn.fetch(
            f"""
            SELECT
                v.id::text, v.risk_code, v.risk_category_code,
                v.risk_level_code, v.title, v.description, v.business_impact
            FROM {_RISKS_VIEW} v
            WHERE v.tenant_key = $1
              AND v.org_id = $2::uuid
              AND ($3::uuid IS NULL OR v.workspace_id = $3::uuid)
              AND ($5::uuid IS NULL OR v.id = $5::uuid)
              AND v.is_active = TRUE AND v.is_deleted = FALSE
            ORDER BY v.risk_level_code DESC, v.created_at
            LIMIT $4
            """,
            tenant_key, org_id, workspace_id, limit, risk_id,
        )
        return [dict(r) for r in rows]

    async def create_mapping_if_not_exists(
        self,
        conn: asyncpg.Connection,
        *,
        mapping_id: str,
        risk_id: str,
        control_id: str,
        link_type: str,
        notes: str | None,
        created_by: str | None,
        approval_status: str = "pending",
        ai_confidence: float | None = None,
        ai_rationale: str | None = None,
    ) -> bool:
        """Returns True if inserted, False if already existed (approved or pending)."""
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_MAPPINGS} (
                id, risk_id, control_id, link_type, notes,
                created_at, created_by,
                approval_status, ai_confidence, ai_rationale
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, NOW(), $6::uuid, $7, $8, $9)
            ON CONFLICT (risk_id, control_id) DO NOTHING
            RETURNING id
            """,
            mapping_id, risk_id, control_id, link_type, notes, created_by,
            approval_status, ai_confidence, ai_rationale,
        )
        return row is not None

    async def delete_all_bulk_link_jobs(
        self, conn, tenant_key: str
    ) -> int:
        result = await conn.execute(
            f"""
            DELETE FROM {_JOBS}
            WHERE tenant_key = $1 AND job_type = 'risk_advisor_bulk_link'
            """,
            tenant_key,
        )
        # result is like "DELETE 5"
        try:
            return int(result.split()[-1])
        except Exception:
            return 0

    async def get_job_status(
        self, conn: asyncpg.Connection, job_id: str, tenant_key: str
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT id::text AS job_id, status_code, job_type,
                   progress_pct, output_json, error_message,
                   created_at::text, updated_at::text
            FROM {_JOBS}
            WHERE id = $1::uuid AND tenant_key = $2
            """,
            job_id, tenant_key,
        )
        return dict(row) if row else None

    async def list_bulk_link_jobs(
        self, conn: asyncpg.Connection, tenant_key: str, limit: int = 20
    ) -> list[dict]:
        rows = await conn.fetch(
            f"""
            SELECT id::text AS job_id, status_code, job_type,
                   progress_pct, output_json, error_message,
                   created_at::text, updated_at::text
            FROM {_JOBS}
            WHERE tenant_key = $1 AND job_type = 'risk_advisor_bulk_link'
            ORDER BY created_at DESC
            LIMIT $2
            """,
            tenant_key, limit,
        )
        return [dict(r) for r in rows]
