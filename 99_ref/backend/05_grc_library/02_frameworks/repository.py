from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import FrameworkCatalogRecord, FrameworkRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods


_VALID_FRAMEWORK_SORT_FIELDS = {
    "name",
    "created_at",
    "updated_at",
    "approval_status",
    "control_count",
}


@instrument_class_methods(
    namespace="grc.frameworks.repository",
    logger_name="backend.grc.frameworks.repository.instrumentation",
)
class FrameworkRepository:
    async def list_frameworks(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        category: str | None = None,
        framework_type: str | None = None,
        approval_status: str | None = None,
        is_active: bool | None = None,
        is_marketplace_visible: bool | None = None,
        search: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        deployed_org_id: str | None = None,
        deployed_workspace_id: str | None = None,
        only_engaged: bool = False,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
        mask_status: bool = False,
    ) -> tuple[list[FrameworkCatalogRecord], int]:
        conditions = ["v.tenant_key = $1", "v.is_deleted = FALSE"]
        args: list[object] = [tenant_key]
        idx = 2

        if category is not None:
            conditions.append(f"v.framework_category_code = ${idx}")
            args.append(category)
            idx += 1
        if framework_type is not None:
            conditions.append(f"v.framework_type_code = ${idx}")
            args.append(framework_type)
            idx += 1
        if approval_status is not None:
            conditions.append(f"v.approval_status = ${idx}")
            args.append(approval_status)
            idx += 1
        if is_active is not None:
            conditions.append(f"v.is_active = ${idx}")
            args.append(is_active)
            idx += 1
        if is_marketplace_visible is not None:
            conditions.append(f"v.is_marketplace_visible = ${idx}")
            args.append(is_marketplace_visible)
            idx += 1
        if search is not None:
            conditions.append(f"(v.name ILIKE ${idx} OR v.framework_code ILIKE ${idx})")
            args.append(f"%{search}%")
            idx += 1
        if scope_org_id is not None:
            # Include: 1) Matches my org, 2) Matches my workspace (if ws provided), 3) Global Marketplace standards
            if scope_workspace_id is not None:
                conditions.append(
                    f"(v.scope_org_id = ${idx}::uuid OR v.scope_workspace_id = ${idx + 1}::uuid OR (v.scope_org_id IS NULL AND v.is_marketplace_visible = TRUE))"
                )
                args.append(scope_org_id)
                args.append(scope_workspace_id)
                idx += 2
                # Skip the default workspace filter below since we merged it
                scope_workspace_id = None
            else:
                conditions.append(
                    f"(v.scope_org_id = ${idx}::uuid OR (v.scope_org_id IS NULL AND v.is_marketplace_visible = TRUE))"
                )
                args.append(scope_org_id)
                idx += 1

        if scope_workspace_id is not None:
            conditions.append(
                f"(v.scope_workspace_id = ${idx}::uuid OR (v.scope_org_id IS NULL AND v.scope_workspace_id IS NULL AND v.is_marketplace_visible = TRUE))"
            )
            args.append(scope_workspace_id)
            idx += 1
        if deployed_org_id is not None:
            if deployed_workspace_id is not None:
                conditions.append(
                    f'v.id IN (SELECT framework_id FROM {SCHEMA}."16_fct_framework_deployments"'
                    f" WHERE org_id = ${idx}::uuid AND deployment_status != 'removed'"
                    f" AND (workspace_id = ${idx + 1}::uuid OR workspace_id IS NULL))"
                )
                args.append(deployed_org_id)
                args.append(deployed_workspace_id)
                idx += 2
            else:
                conditions.append(
                    f'v.id IN (SELECT framework_id FROM {SCHEMA}."16_fct_framework_deployments"'
                    f" WHERE org_id = ${idx}::uuid AND deployment_status != 'removed')"
                )
                args.append(deployed_org_id)
                idx += 1

        if only_engaged:
            conditions.append(
                f'v.id IN (SELECT framework_id FROM "12_engagements"."10_fct_audit_engagements"'
                f" WHERE is_deleted = FALSE AND is_active = TRUE)"
            )

        where = " AND ".join(conditions)

        # Build ORDER BY (injection-safe via allowlist)
        safe_sort = sort_by if sort_by in _VALID_FRAMEWORK_SORT_FIELDS else None
        order_col = safe_sort or "name"
        order_dir = "ASC" if not sort_dir or sort_dir.lower() == "asc" else "DESC"

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."40_vw_framework_catalog" v WHERE {where}',
            *args,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            WITH latest_published AS (
                SELECT 
                    v.framework_id, 
                    v.id as version_id, 
                    v.version_code, 
                    v.control_count,
                    ROW_NUMBER() OVER (PARTITION BY v.framework_id ORDER BY v.created_at DESC) as rnk
                FROM "05_grc_library"."11_fct_framework_versions" v
                WHERE v.lifecycle_state = 'published' AND v.is_deleted = FALSE
            )
            SELECT v.id, v.tenant_key, v.framework_code, v.framework_type_code, v.type_name,
                   v.framework_category_code, v.category_name, v.scope_org_id::text, v.scope_workspace_id::text,
                   v.approval_status, v.is_marketplace_visible, v.is_active,
                   v.created_at::text, v.updated_at::text, v.created_by::text,
                   v.name, v.description, v.short_description, v.publisher_type, v.publisher_name,
                   v.logo_url, v.documentation_url,
                   
                   -- Stable/Published Fallbacks (independent of view columns)
                   p_vname.property_value          AS published_name,
                   p_vdesc.property_value          AS published_description,
                   p_vshort.property_value         AS published_short_description,
                   p_vpub_type.property_value      AS published_publisher_type,
                   p_vpub_name.property_value      AS published_publisher_name,
                   p_vlogo.property_value          AS published_logo_url,
                   p_vdocs.property_value          AS published_documentation_url,

                   lp.version_code                 AS latest_version_code,
                   COALESCE(lp.control_count, v.control_count) AS control_count,
                   (SELECT COUNT(*) FROM "05_grc_library"."13_fct_controls" cc WHERE cc.framework_id = v.id AND cc.is_deleted = FALSE) AS working_control_count,
                   (NOT EXISTS (
                       SELECT 1 FROM "05_grc_library"."11_fct_framework_versions" v2
                       WHERE v2.framework_id = v.id AND v2.lifecycle_state = 'published' AND v2.is_deleted = FALSE
                   ) OR EXISTS (
                       SELECT 1 FROM "05_grc_library"."13_fct_controls" c
                       WHERE c.framework_id = v.id AND c.is_deleted = FALSE
                         AND (c.created_at > (
                             SELECT MAX(v3.created_at) FROM "05_grc_library"."11_fct_framework_versions" v3
                             WHERE v3.framework_id = v.id AND v3.lifecycle_state = 'published' AND v3.is_deleted = FALSE
                         ) OR c.updated_at > (
                             SELECT MAX(v4.created_at) FROM "05_grc_library"."11_fct_framework_versions" v4
                             WHERE v4.framework_id = v.id AND v4.lifecycle_state = 'published' AND v4.is_deleted = FALSE
                         ))
                   ) OR EXISTS (
                       SELECT 1 FROM "05_grc_library"."20_dtl_framework_properties" p
                       WHERE p.framework_id = v.id
                         AND (p.created_at > (
                             SELECT MAX(v5.created_at) FROM "05_grc_library"."11_fct_framework_versions" v5
                             WHERE v5.framework_id = v.id AND v5.lifecycle_state = 'published' AND v5.is_deleted = FALSE
                         ) OR p.updated_at > (
                             SELECT MAX(v6.created_at) FROM "05_grc_library"."11_fct_framework_versions" v6
                             WHERE v6.framework_id = v.id AND v6.lifecycle_state = 'published' AND v6.is_deleted = FALSE
                         ))
                   )) AS has_pending_changes
            FROM {SCHEMA}."40_vw_framework_catalog" v
            LEFT JOIN latest_published lp ON lp.framework_id = v.id AND lp.rnk = 1
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vname
                ON p_vname.framework_version_id = lp.version_id AND p_vname.property_key = 'name'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vdesc
                ON p_vdesc.framework_version_id = lp.version_id AND p_vdesc.property_key = 'description'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vshort
                ON p_vshort.framework_version_id = lp.version_id AND p_vshort.property_key = 'short_description'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vpub_type
                ON p_vpub_type.framework_version_id = lp.version_id AND p_vpub_type.property_key = 'publisher_type'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vpub_name
                ON p_vpub_name.framework_version_id = lp.version_id AND p_vpub_name.property_key = 'publisher_name'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vlogo
                ON p_vlogo.framework_version_id = lp.version_id AND p_vlogo.property_key = 'logo_url'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vdocs
                ON p_vdocs.framework_version_id = lp.version_id AND p_vdocs.property_key = 'documentation_url'
            WHERE {where}
            ORDER BY v.{order_col} {order_dir}, v.framework_code ASC
            LIMIT {limit} OFFSET {offset}
            """,
            *args,
        )
        return [_row_to_catalog(r, mask_status=mask_status) for r in rows], total

    async def get_framework_by_id(
        self, connection: asyncpg.Connection, framework_id: str, mask_status: bool = False
    ) -> FrameworkCatalogRecord | None:
        row = await connection.fetchrow(
            f"""
            WITH latest_published AS (
                SELECT 
                    v.framework_id, 
                    v.id as version_id, 
                    v.version_code, 
                    v.control_count,
                    ROW_NUMBER() OVER (PARTITION BY v.framework_id ORDER BY v.created_at DESC) as rnk
                FROM "05_grc_library"."11_fct_framework_versions" v
                WHERE v.lifecycle_state = 'published' AND v.is_deleted = FALSE
            )
            SELECT v.id, v.tenant_key, v.framework_code, v.framework_type_code, v.type_name,
                   v.framework_category_code, v.category_name, v.scope_org_id::text, v.scope_workspace_id::text,
                   v.approval_status, v.is_marketplace_visible, v.is_active,
                   v.created_at::text, v.updated_at::text, v.created_by::text,
                   v.name, v.description, v.short_description, v.publisher_type, v.publisher_name,
                   v.logo_url, v.documentation_url,

                   -- Stable/Published Fallbacks (independent of view columns)
                   p_vname.property_value          AS published_name,
                   p_vdesc.property_value          AS published_description,
                   p_vshort.property_value         AS published_short_description,
                   p_vpub_type.property_value      AS published_publisher_type,
                   p_vpub_name.property_value      AS published_publisher_name,
                   p_vlogo.property_value          AS published_logo_url,
                   p_vdocs.property_value          AS published_documentation_url,

                   lp.version_code                 AS latest_version_code,
                   COALESCE(lp.control_count, v.control_count) AS control_count,
                   (SELECT COUNT(*) FROM "05_grc_library"."13_fct_controls" cc WHERE cc.framework_id = v.id AND cc.is_deleted = FALSE) AS working_control_count,
                   (NOT EXISTS (
                       SELECT 1 FROM "05_grc_library"."11_fct_framework_versions" v2
                       WHERE v2.framework_id = v.id AND v2.lifecycle_state = 'published' AND v2.is_deleted = FALSE
                   ) OR EXISTS (
                       SELECT 1 FROM "05_grc_library"."13_fct_controls" c
                       WHERE c.framework_id = v.id AND c.is_deleted = FALSE
                         AND (c.created_at > (
                             SELECT MAX(v3.created_at) FROM "05_grc_library"."11_fct_framework_versions" v3
                             WHERE v3.framework_id = v.id AND v3.lifecycle_state = 'published' AND v3.is_deleted = FALSE
                         ) OR c.updated_at > (
                             SELECT MAX(v4.created_at) FROM "05_grc_library"."11_fct_framework_versions" v4
                             WHERE v4.framework_id = v.id AND v4.lifecycle_state = 'published' AND v4.is_deleted = FALSE
                         ))
                   ) OR EXISTS (
                       SELECT 1 FROM "05_grc_library"."20_dtl_framework_properties" p
                       WHERE p.framework_id = v.id
                         AND (p.created_at > (
                             SELECT MAX(v5.created_at) FROM "05_grc_library"."11_fct_framework_versions" v5
                             WHERE v5.framework_id = v.id AND v5.lifecycle_state = 'published' AND v5.is_deleted = FALSE
                         ) OR p.updated_at > (
                             SELECT MAX(v6.created_at) FROM "05_grc_library"."11_fct_framework_versions" v6
                             WHERE v6.framework_id = v.id AND v6.lifecycle_state = 'published' AND v6.is_deleted = FALSE
                         ))
                   )) AS has_pending_changes
            FROM {SCHEMA}."40_vw_framework_catalog" v
            LEFT JOIN latest_published lp ON lp.framework_id = v.id AND lp.rnk = 1
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vname
                ON p_vname.framework_version_id = lp.version_id AND p_vname.property_key = 'name'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vdesc
                ON p_vdesc.framework_version_id = lp.version_id AND p_vdesc.property_key = 'description'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vshort
                ON p_vshort.framework_version_id = lp.version_id AND p_vshort.property_key = 'short_description'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vpub_type
                ON p_vpub_type.framework_version_id = lp.version_id AND p_vpub_type.property_key = 'publisher_type'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vpub_name
                ON p_vpub_name.framework_version_id = lp.version_id AND p_vpub_name.property_key = 'publisher_name'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vlogo
                ON p_vlogo.framework_version_id = lp.version_id AND p_vlogo.property_key = 'logo_url'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_vdocs
                ON p_vdocs.framework_version_id = lp.version_id AND p_vdocs.property_key = 'documentation_url'
            WHERE v.id = $1 AND v.is_deleted = FALSE
            """,
            framework_id,
        )
        return _row_to_catalog(row, mask_status=mask_status) if row else None

    async def get_framework_by_code(
        self,
        connection: asyncpg.Connection,
        framework_code: str,
        tenant_key: str,
        *,
        include_deleted: bool = False,
    ) -> FrameworkRecord | None:
        deleted_filter = "AND is_deleted = FALSE" if not include_deleted else ""
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, framework_code, framework_type_code,
                   framework_category_code, scope_org_id::text, scope_workspace_id::text,
                   approval_status, is_marketplace_visible, is_active,
                   created_at::text, updated_at::text, created_by::text
            FROM {SCHEMA}."10_fct_frameworks"
            WHERE framework_code = $1 AND tenant_key = $2 {deleted_filter}
            """,
            framework_code,
            tenant_key,
        )
        return _row_to_framework(row) if row else None

    async def create_framework(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        tenant_key: str,
        framework_code: str,
        framework_type_code: str,
        framework_category_code: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
        created_by: str,
        now: object,
    ) -> FrameworkRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."10_fct_frameworks"
                (id, tenant_key, framework_code, framework_type_code,
                 framework_category_code, scope_org_id, scope_workspace_id,
                 approval_status, is_marketplace_visible,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4,
                 $5, $6, $7,
                 'draft', FALSE,
                 TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                 $8, $9, $10, $11, NULL, NULL)
            RETURNING id, tenant_key, framework_code, framework_type_code,
                      framework_category_code, scope_org_id::text, scope_workspace_id::text,
                      approval_status, is_marketplace_visible, is_active,
                      created_at::text, updated_at::text, created_by::text
            """,
            framework_id,
            tenant_key,
            framework_code,
            framework_type_code,
            framework_category_code,
            scope_org_id,
            scope_workspace_id,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_framework(row)

    async def update_framework(
        self,
        connection: asyncpg.Connection,
        framework_id: str,
        *,
        framework_type_code: str | None = None,
        framework_category_code: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        approval_status: str | None = None,
        is_marketplace_visible: bool | None = None,
        updated_by: str,
        now: object,
    ) -> FrameworkRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if framework_type_code is not None:
            fields.append(f"framework_type_code = ${idx}")
            values.append(framework_type_code)
            idx += 1
        if framework_category_code is not None:
            fields.append(f"framework_category_code = ${idx}")
            values.append(framework_category_code)
            idx += 1
        if scope_org_id is not None:
            fields.append(f"scope_org_id = ${idx}::uuid")
            values.append(scope_org_id)
            idx += 1
        if scope_workspace_id is not None:
            fields.append(f"scope_workspace_id = ${idx}::uuid")
            values.append(scope_workspace_id)
            idx += 1
        if approval_status is not None:
            fields.append(f"approval_status = ${idx}")
            values.append(approval_status)
            idx += 1
        if is_marketplace_visible is not None:
            fields.append(f"is_marketplace_visible = ${idx}")
            values.append(is_marketplace_visible)
            idx += 1

        values.append(framework_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."10_fct_frameworks"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, tenant_key, framework_code, framework_type_code,
                      framework_category_code, scope_org_id::text, scope_workspace_id::text,
                      approval_status, is_marketplace_visible, is_active,
                      created_at::text, updated_at::text, created_by::text
            """,
            *values,
        )
        return _row_to_framework(row) if row else None

    async def soft_delete_framework(
        self,
        connection: asyncpg.Connection,
        framework_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_frameworks"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            framework_id,
        )
        return result != "UPDATE 0"

    async def soft_delete_framework_graph(
        self,
        connection: asyncpg.Connection,
        framework_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."13_fct_controls"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE framework_id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            framework_id,
        )
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."12_fct_requirements"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE framework_id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            framework_id,
        )
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."11_fct_framework_versions"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE framework_id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            framework_id,
        )
        return await self.soft_delete_framework(
            connection,
            framework_id,
            deleted_by=deleted_by,
            now=now,
        )

    async def upsert_framework_properties(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        properties: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (framework_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {SCHEMA}."20_dtl_framework_properties"
                    (id, framework_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (framework_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
            rows,
        )

    # ── Bundle helpers ────────────────────────────────────────────────────────

    async def list_requirements_for_bundle(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> list[dict]:
        rows = await connection.fetch(
            f"""
            SELECT r.id::text, r.requirement_code, r.sort_order,
                   r.parent_requirement_id::text,
                   p_name.property_value AS name,
                   p_desc.property_value AS description
            FROM {SCHEMA}."12_fct_requirements" r
            LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_name
                ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN {SCHEMA}."22_dtl_requirement_properties" p_desc
                ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            WHERE r.framework_id = $1 AND r.is_deleted = FALSE
            ORDER BY r.sort_order, r.requirement_code
            """,
            framework_id,
        )
        return [dict(r) for r in rows]

    async def list_requirements_by_code(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> dict[str, str]:
        """Return {requirement_code: requirement_id}."""
        rows = await connection.fetch(
            f"""
            SELECT requirement_code, id::text AS req_id
            FROM {SCHEMA}."12_fct_requirements"
            WHERE framework_id = $1 AND is_deleted = FALSE
            """,
            framework_id,
        )
        return {r["requirement_code"]: r["req_id"] for r in rows}

    async def upsert_requirement(
        self,
        connection: asyncpg.Connection,
        *,
        requirement_id: str,
        framework_id: str,
        requirement_code: str,
        sort_order: int,
        parent_requirement_id: str | None,
        name: str | None,
        description: str | None,
        created_by: str,
        now: object,
    ) -> tuple[str, bool]:
        """Upsert by (framework_id, requirement_code). Returns (id, created)."""
        row = await connection.fetchrow(
            f"""
            SELECT id::text FROM {SCHEMA}."12_fct_requirements"
            WHERE framework_id = $1 AND requirement_code = $2 AND is_deleted = FALSE
            """,
            framework_id,
            requirement_code,
        )
        if row:
            req_id = row["id"]
            await connection.execute(
                f"""
                UPDATE {SCHEMA}."12_fct_requirements"
                SET sort_order = $1, parent_requirement_id = $2, updated_at = $3, updated_by = $4
                WHERE id = $5
                """,
                sort_order,
                parent_requirement_id,
                now,
                created_by,
                req_id,
            )
            created = False
        else:
            req_id = requirement_id
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."12_fct_requirements"
                    (id, framework_id, requirement_code, sort_order, parent_requirement_id,
                     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                     created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
                VALUES ($1, $2, $3, $4, $5, TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                        $6, $7, $8, $9, NULL, NULL)
                """,
                req_id,
                framework_id,
                requirement_code,
                sort_order,
                parent_requirement_id,
                now,
                now,
                created_by,
                created_by,
            )
            created = True
        req_props: dict[str, str] = {}
        if name:
            req_props["name"] = name
        if description:
            req_props["description"] = description
        for key, value in req_props.items():
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."22_dtl_requirement_properties"
                    (id, requirement_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (requirement_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by
                """,
                req_id,
                key,
                value,
                now,
                now,
                created_by,
                created_by,
            )
        return req_id, created

    async def list_global_risks_by_framework(
        self, connection: asyncpg.Connection, *, tenant_key: str, framework_id: str
    ) -> list[dict]:
        """Fetch global risks linked to any control in this framework."""
        rows = await connection.fetch(
            f"""
            SELECT DISTINCT gr.id::text, gr.risk_code, gr.risk_category_code,
                   gr.risk_level_code, gr.inherent_likelihood, gr.inherent_impact,
                   gt.property_value AS title,
                   gd.property_value AS description,
                   gs.property_value AS short_description,
                   gm.property_value AS mitigation_guidance,
                   gdet.property_value AS detection_guidance
            FROM {SCHEMA}."50_fct_global_risks" gr
            LEFT JOIN {SCHEMA}."56_dtl_global_risk_properties" gt
                ON gt.global_risk_id = gr.id AND gt.property_key = 'title'
            LEFT JOIN {SCHEMA}."56_dtl_global_risk_properties" gd
                ON gd.global_risk_id = gr.id AND gd.property_key = 'description'
            LEFT JOIN {SCHEMA}."56_dtl_global_risk_properties" gs
                ON gs.global_risk_id = gr.id AND gs.property_key = 'short_description'
            LEFT JOIN {SCHEMA}."56_dtl_global_risk_properties" gm
                ON gm.global_risk_id = gr.id AND gm.property_key = 'mitigation_guidance'
            LEFT JOIN {SCHEMA}."56_dtl_global_risk_properties" gdet
                ON gdet.global_risk_id = gr.id AND gdet.property_key = 'detection_guidance'
            JOIN {SCHEMA}."61_lnk_global_risk_control_mappings" lnk ON lnk.global_risk_id = gr.id
            JOIN {SCHEMA}."13_fct_controls" c ON c.id = lnk.control_id
            WHERE gr.tenant_key = $1 AND gr.is_deleted = FALSE
              AND c.framework_id = $2 AND c.is_deleted = FALSE
            ORDER BY gr.risk_code
            """,
            tenant_key,
            framework_id,
        )
        return [dict(r) for r in rows]

    async def list_risk_control_codes_for_framework(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> list[tuple[str, str]]:
        """Return [(risk_code, control_code)] for all risk-control mappings in this framework."""
        rows = await connection.fetch(
            f"""
            SELECT gr.risk_code, c.control_code
            FROM {SCHEMA}."61_lnk_global_risk_control_mappings" lnk
            JOIN {SCHEMA}."50_fct_global_risks" gr ON gr.id = lnk.global_risk_id
            JOIN {SCHEMA}."13_fct_controls" c ON c.id = lnk.control_id
            WHERE c.framework_id = $1 AND c.is_deleted = FALSE AND gr.is_deleted = FALSE
            """,
            framework_id,
        )
        return [(r["risk_code"], r["control_code"]) for r in rows]

    async def upsert_global_risk(
        self,
        connection: asyncpg.Connection,
        *,
        global_risk_id: str,
        tenant_key: str,
        risk_code: str,
        risk_category_code: str | None,
        risk_level_code: str | None,
        inherent_likelihood: int | None,
        inherent_impact: int | None,
        title: str | None,
        description: str | None,
        short_description: str | None,
        mitigation_guidance: str | None,
        detection_guidance: str | None,
        created_by: str,
        now: object,
    ) -> tuple[str, bool]:
        """Upsert global risk by (tenant_key, risk_code). Returns (id, created)."""
        row = await connection.fetchrow(
            f"""
            SELECT id::text FROM {SCHEMA}."50_fct_global_risks"
            WHERE tenant_key = $1 AND risk_code = $2 AND is_deleted = FALSE
            """,
            tenant_key,
            risk_code,
        )
        if row:
            gr_id = row["id"]
            await connection.execute(
                f"""
                UPDATE {SCHEMA}."50_fct_global_risks"
                SET risk_category_code = COALESCE($1, risk_category_code),
                    risk_level_code = COALESCE($2, risk_level_code),
                    inherent_likelihood = COALESCE($3, inherent_likelihood),
                    inherent_impact = COALESCE($4, inherent_impact),
                    updated_at = $5, updated_by = $6
                WHERE id = $7
                """,
                risk_category_code,
                risk_level_code,
                inherent_likelihood,
                inherent_impact,
                now,
                created_by,
                gr_id,
            )
            created = False
        else:
            gr_id = global_risk_id
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."50_fct_global_risks"
                    (id, tenant_key, risk_code, risk_category_code, risk_level_code,
                     inherent_likelihood, inherent_impact,
                     is_active, is_deleted, is_system,
                     created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
                VALUES ($1, $2, $3, $4, $5, $6, $7,
                        TRUE, FALSE, FALSE,
                        $8, $9, $10, $11, NULL, NULL)
                """,
                gr_id,
                tenant_key,
                risk_code,
                risk_category_code,
                risk_level_code,
                inherent_likelihood,
                inherent_impact,
                now,
                now,
                created_by,
                created_by,
            )
            created = True
        props: dict[str, str] = {}
        if title:
            props["title"] = title
        if description:
            props["description"] = description
        if short_description:
            props["short_description"] = short_description
        if mitigation_guidance:
            props["mitigation_guidance"] = mitigation_guidance
        if detection_guidance:
            props["detection_guidance"] = detection_guidance
        for key, value in props.items():
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."56_dtl_global_risk_properties"
                    (id, global_risk_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (global_risk_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by
                """,
                gr_id,
                key,
                value,
                now,
                now,
                created_by,
                created_by,
            )
        return gr_id, created

    async def get_latest_published_version_controls(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> tuple[str | None, list[dict]]:
        """Return (version_code, [control dicts]) for the latest published version."""
        version_row = await connection.fetchrow(
            f"""
            SELECT id::text, version_code
            FROM {SCHEMA}."11_fct_framework_versions"
            WHERE framework_id = $1 AND lifecycle_state = 'published' AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            framework_id,
        )
        if not version_row:
            return None, []
        version_id = version_row["id"]
        version_code = version_row["version_code"]
        rows = await connection.fetch(
            f"""
            SELECT c.control_code,
                   c.criticality_code, c.control_type, c.automation_potential,
                   c.control_category_code, c.requirement_id::text,
                   req.requirement_code AS requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_guid.property_value AS guidance
            FROM {SCHEMA}."31_lnk_framework_version_controls" lnk
            JOIN {SCHEMA}."13_fct_controls" c ON c.id = lnk.control_id
            LEFT JOIN {SCHEMA}."12_fct_requirements" req ON req.id = c.requirement_id
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_desc
                ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_guid
                ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
            WHERE lnk.framework_version_id = $1
            ORDER BY c.sort_order, c.control_code
            """,
            version_id,
        )
        return version_code, [dict(r) for r in rows]

    async def get_previous_published_version_controls(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        current_version_id: str | None = None,
    ) -> tuple[str | None, list[dict]]:
        """Return (version_code, [control dicts]) for the previous published version before current."""
        if current_version_id:
            version_row = await connection.fetchrow(
                f"""
                SELECT id::text, version_code
                FROM {SCHEMA}."11_fct_framework_versions"
                WHERE framework_id = $1 AND lifecycle_state = 'published' AND is_deleted = FALSE
                  AND id != $2 AND created_at < (
                    SELECT created_at FROM {SCHEMA}."11_fct_framework_versions" WHERE id = $2
                  )
                ORDER BY created_at DESC
                LIMIT 1
                """,
                framework_id,
                current_version_id,
            )
        else:
            version_row = await connection.fetchrow(
                f"""
                SELECT id::text, version_code
                FROM {SCHEMA}."11_fct_framework_versions"
                WHERE framework_id = $1 AND lifecycle_state = 'published' AND is_deleted = FALSE
                ORDER BY created_at DESC
                LIMIT 1
                """,
                framework_id,
            )
        if not version_row:
            return None, []
        version_id = version_row["id"]
        version_code = version_row["version_code"]
        rows = await connection.fetch(
            f"""
            SELECT c.id::text as control_id,
                   c.control_code,
                   c.criticality_code, c.control_type, c.automation_potential,
                   c.control_category_code, c.requirement_id::text,
                   req.requirement_code AS requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_guid.property_value AS guidance
            FROM {SCHEMA}."31_lnk_framework_version_controls" lnk
            JOIN {SCHEMA}."13_fct_controls" c ON c.id = lnk.control_id
            LEFT JOIN {SCHEMA}."12_fct_requirements" req ON req.id = c.requirement_id
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_desc
                ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p_guid
                ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
            WHERE lnk.framework_version_id = $1
            ORDER BY c.sort_order, c.control_code
            """,
            version_id,
        )
        return version_code, [dict(r) for r in rows]

    async def link_global_risk_to_control(
        self,
        connection: asyncpg.Connection,
        *,
        global_risk_id: str,
        control_id: str,
        mapping_type: str = "mitigating",
        created_by: str,
        now: object,
    ) -> bool:
        """Insert risk-control link. Returns True if inserted, False if already exists."""
        result = await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."61_lnk_global_risk_control_mappings"
                (id, global_risk_id, control_id, mapping_type, created_at, created_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5)
            ON CONFLICT (global_risk_id, control_id) DO NOTHING
            """,
            global_risk_id,
            control_id,
            mapping_type,
            now,
            created_by,
        )
        return result != "INSERT 0 0"


def _row_to_framework(r) -> FrameworkRecord:
    return FrameworkRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        framework_code=r["framework_code"],
        framework_type_code=r["framework_type_code"],
        framework_category_code=r["framework_category_code"],
        scope_org_id=r["scope_org_id"],
        scope_workspace_id=r["scope_workspace_id"],
        approval_status=r["approval_status"],
        is_marketplace_visible=r["is_marketplace_visible"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )


def _row_to_catalog(r, mask_status: bool = False) -> FrameworkCatalogRecord:
    # If viewed in the marketplace context (is_marketplace_visible=True), 
    # and not currently in 'approved' status, fallback to published stable metadata.
    # We detect marketplace context if the record is currently 'pending_review' or 'draft'
    # but still shows up in an 'approved' filter list.
    use_stable = (
        mask_status
        and r["is_marketplace_visible"] 
        and r["latest_version_code"] is not None 
        and r["approval_status"] != "approved"
    )

    return FrameworkCatalogRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        framework_code=r["framework_code"],
        framework_type_code=r["framework_type_code"],
        type_name=r["type_name"],
        framework_category_code=r["framework_category_code"],
        category_name=r["category_name"],
        scope_org_id=r["scope_org_id"],
        scope_workspace_id=r["scope_workspace_id"],
        approval_status="approved" if use_stable else r["approval_status"],
        is_marketplace_visible=r["is_marketplace_visible"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
        name=r["published_name"] if use_stable and r.get("published_name") else r["name"],
        description=r["published_description"] if use_stable and r.get("published_description") else r["description"],
        short_description=r["published_short_description"] if use_stable and r.get("published_short_description") else r["short_description"],
        publisher_type=r["published_publisher_type"] if use_stable and r.get("published_publisher_type") else r["publisher_type"],
        publisher_name=r["published_publisher_name"] if use_stable and r.get("published_publisher_name") else r["publisher_name"],
        logo_url=r["published_logo_url"] if use_stable and r.get("published_logo_url") else r["logo_url"],
        documentation_url=r["published_documentation_url"] if use_stable and r.get("published_documentation_url") else r["documentation_url"],
        latest_version_code=r["latest_version_code"],
        control_count=r["control_count"],
        working_control_count=r.get("working_control_count", 0),
        has_pending_changes=r.get("has_pending_changes", False),
    )
