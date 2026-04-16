from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import FrameworkDeploymentRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods

_SELECT_VIEW = f"""
    SELECT d.id, d.tenant_key, d.org_id::text, d.framework_id::text,
           d.deployed_version_id::text, d.deployment_status, d.workspace_id::text,
           d.is_active, d.created_at::text, d.updated_at::text, d.created_by::text,
           d.framework_code, d.framework_name, d.framework_description, d.publisher_name, d.logo_url,
           d.approval_status, d.is_marketplace_visible,
           d.deployed_version_code, d.deployed_lifecycle_state,
           COALESCE(source_latest.source_latest_version_id, d.latest_version_id) AS latest_version_id,
           COALESCE(source_latest.source_latest_version_code, d.latest_version_code) AS latest_version_code,
           CASE
               WHEN src_fw.property_value IS NOT NULL
                    THEN COALESCE(source_latest.source_latest_version_id, '') <> COALESCE(src_ver.property_value, '')
               ELSE d.has_update
           END AS has_update,
            src_fw.property_value AS source_framework_id,
            src_ver.property_value AS source_version_id,
            COALESCE(source_latest.source_latest_release_notes, d.latest_release_notes) AS latest_release_notes,
            COALESCE(source_latest.source_latest_change_severity, d.latest_change_severity) AS latest_change_severity,
            COALESCE(source_latest.source_latest_change_summary, d.latest_change_summary) AS latest_change_summary
    FROM {SCHEMA}."44_vw_framework_deployments" d
    LEFT JOIN {SCHEMA}."20_dtl_framework_properties" src_fw
        ON src_fw.framework_id = d.framework_id::uuid
       AND src_fw.property_key = 'source_framework_id'
    LEFT JOIN {SCHEMA}."20_dtl_framework_properties" src_ver
        ON src_ver.framework_id = d.framework_id::uuid
       AND src_ver.property_key = 'source_version_id'
    LEFT JOIN LATERAL (
        SELECT v.id::text AS source_latest_version_id, v.version_code AS source_latest_version_code,
               src_notes.property_value AS source_latest_release_notes,
               src_sev.property_value AS source_latest_change_severity,
               src_sum.property_value AS source_latest_change_summary
        FROM {SCHEMA}."11_fct_framework_versions" v
        LEFT JOIN {SCHEMA}."21_dtl_version_properties" src_notes
            ON src_notes.framework_version_id = v.id AND src_notes.property_key = 'release_notes'
        LEFT JOIN {SCHEMA}."21_dtl_version_properties" src_sev
            ON src_sev.framework_version_id = v.id AND src_sev.property_key = 'change_severity_label'
        LEFT JOIN {SCHEMA}."21_dtl_version_properties" src_sum
            ON src_sum.framework_version_id = v.id AND src_sum.property_key = 'change_summary'
        WHERE src_fw.property_value IS NOT NULL
          AND v.framework_id = src_fw.property_value::uuid
          AND v.lifecycle_state = 'published'
          AND v.is_deleted = FALSE
        ORDER BY v.created_at DESC
        LIMIT 1
    ) source_latest ON TRUE
"""


@instrument_class_methods(
    namespace="grc.deployments.repository",
    logger_name="backend.grc.deployments.repository.instrumentation",
)
class DeploymentRepository:
    async def list_deployments(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        has_update: bool | None = None,
    ) -> tuple[list[FrameworkDeploymentRecord], int]:
        conditions = [
            "d.tenant_key = $1",
            "d.org_id = $2",
            "d.deployment_status != 'removed'",
        ]
        args: list[object] = [tenant_key, org_id]
        idx = 3

        if workspace_id is not None:
            conditions.append(f"d.workspace_id = ${idx}")
            args.append(workspace_id)
            idx += 1
            # Workspace deployments are considered valid only when the deployed
            # framework is materialized in the same workspace (clone, not pointer).
            conditions.append(
                f"""
                EXISTS (
                    SELECT 1
                    FROM {SCHEMA}."10_fct_frameworks" fw
                    WHERE fw.id = d.framework_id::uuid
                      AND fw.is_deleted = FALSE
                      AND fw.scope_workspace_id = d.workspace_id::uuid
                )
                """
            )

        if has_update is not None:
            conditions.append(f"d.has_update = ${idx}")
            args.append(has_update)
            idx += 1

        where = " AND ".join(conditions)
        where_with_active = f"{where} AND d.is_active = TRUE"
        count_row = await connection.fetchrow(
            f"SELECT COUNT(*)::int AS total FROM ({_SELECT_VIEW}) d WHERE {where_with_active}",
            *args,
        )
        total = count_row["total"] if count_row else 0
        rows = await connection.fetch(
            f"SELECT * FROM ({_SELECT_VIEW}) d WHERE {where_with_active} ORDER BY d.framework_name ASC NULLS LAST",
            *args,
        )
        return [_row_to_record(r) for r in rows], total

    async def get_deployment(
        self, connection: asyncpg.Connection, deployment_id: str
    ) -> FrameworkDeploymentRecord | None:
        row = await connection.fetchrow(
            f"SELECT * FROM ({_SELECT_VIEW}) d WHERE d.id = $1",
            deployment_id,
        )
        return _row_to_record(row) if row else None

    async def get_deployment_by_org_framework(
        self, connection: asyncpg.Connection, org_id: str, framework_id: str
    ) -> FrameworkDeploymentRecord | None:
        row = await connection.fetchrow(
            f"SELECT * FROM ({_SELECT_VIEW}) d WHERE d.org_id = $1 AND d.framework_id = $2",
            org_id,
            framework_id,
        )
        return _row_to_record(row) if row else None

    async def get_deployment_for_source(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        workspace_id: str | None,
        source_framework_id: str,
    ) -> FrameworkDeploymentRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT * FROM ({_SELECT_VIEW}) d
            WHERE d.org_id = $1
              AND d.deployment_status != 'removed'
              AND d.workspace_id IS NOT DISTINCT FROM $2
              AND (d.framework_id = $3 OR d.source_framework_id = $3)
            ORDER BY d.updated_at DESC
            LIMIT 1
            """,
            org_id,
            workspace_id,
            source_framework_id,
        )
        return _row_to_record(row) if row else None

    async def create_deployment(
        self,
        connection: asyncpg.Connection,
        *,
        deployment_id: str,
        tenant_key: str,
        org_id: str,
        framework_id: str,
        version_id: str,
        workspace_id: str | None,
        created_by: str,
        now: object,
    ) -> FrameworkDeploymentRecord:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."16_fct_framework_deployments"
                (id, tenant_key, org_id, framework_id, deployed_version_id,
                 deployment_status, workspace_id, is_active,
                 created_at, updated_at, created_by, updated_by)
            VALUES
                ($1, $2, $3::uuid, $4::uuid, $5::uuid,
                 'active', $6::uuid, TRUE,
                 $7, $8, $9::uuid, $10::uuid)
            """,
            deployment_id,
            tenant_key,
            org_id,
            framework_id,
            version_id,
            workspace_id,
            now,
            now,
            created_by,
            created_by,
        )
        row = await connection.fetchrow(
            f"SELECT * FROM ({_SELECT_VIEW}) d WHERE d.id = $1",
            deployment_id,
        )
        return _row_to_record(row)

    async def update_deployment(
        self,
        connection: asyncpg.Connection,
        deployment_id: str,
        *,
        framework_id: str | None = None,
        version_id: str | None = None,
        deployment_status: str | None = None,
        workspace_id: str | None = None,
        updated_by: str,
        now: object,
    ) -> FrameworkDeploymentRecord | None:
        fields = ["updated_at = $1", "updated_by = $2::uuid"]
        values: list[object] = [now, updated_by]
        idx = 3

        if framework_id is not None:
            fields.append(f"framework_id = ${idx}::uuid")
            values.append(framework_id)
            idx += 1
        if version_id is not None:
            fields.append(f"deployed_version_id = ${idx}::uuid")
            values.append(version_id)
            idx += 1
        if deployment_status is not None:
            fields.append(f"deployment_status = ${idx}")
            values.append(deployment_status)
            idx += 1
        if workspace_id is not None:
            fields.append(f"workspace_id = ${idx}::uuid")
            values.append(workspace_id)
            idx += 1

        values.append(deployment_id)
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."16_fct_framework_deployments"
            SET {", ".join(fields)}
            WHERE id = ${idx}
            """,
            *values,
        )
        row = await connection.fetchrow(
            f"SELECT * FROM ({_SELECT_VIEW}) d WHERE d.id = $1",
            deployment_id,
        )
        return _row_to_record(row) if row else None

    async def list_deployment_controls(
        self,
        connection: asyncpg.Connection,
        *,
        deployment_id: str,
    ) -> list[dict]:
        """Return controls snapshotted in the deployment's version."""
        rows = await connection.fetch(
            f"""
            SELECT c.id::text, c.control_code, c.control_type, c.automation_potential,
                   c.sort_order, c.control_category_code, c.criticality_code,
                   lvc.sort_order AS version_sort_order,
                   cp_name.property_value  AS name,
                   cp_desc.property_value  AS description,
                   cp_guid.property_value  AS guidance,
                   cat.name                AS category_name,
                   crit.name               AS criticality_name
            FROM {SCHEMA}."16_fct_framework_deployments" d
            JOIN {SCHEMA}."31_lnk_framework_version_controls" lvc
                ON lvc.framework_version_id = d.deployed_version_id
            JOIN {SCHEMA}."13_fct_controls" c
                ON c.id = lvc.control_id AND c.is_deleted = FALSE
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" cp_name
                ON cp_name.control_id = c.id AND cp_name.property_key = 'name'
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" cp_desc
                ON cp_desc.control_id = c.id AND cp_desc.property_key = 'description'
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" cp_guid
                ON cp_guid.control_id = c.id AND cp_guid.property_key = 'implementation_guidance'
            LEFT JOIN {SCHEMA}."04_dim_control_categories" cat
                ON cat.code = c.control_category_code
            LEFT JOIN {SCHEMA}."05_dim_control_criticalities" crit
                ON crit.code = c.criticality_code
            WHERE d.id = $1
            ORDER BY lvc.sort_order ASC NULLS LAST, c.control_code ASC
            """,
            deployment_id,
        )
        return [dict(r) for r in rows]

    async def get_upgrade_diff(
        self,
        connection: asyncpg.Connection,
        *,
        deployment_id: str,
        new_version_id: str,
    ) -> dict:
        """Return added/removed controls between current deployed version and a new version."""
        rows = await connection.fetch(
            f"""
            WITH current_controls AS (
                SELECT lvc.control_id
                FROM {SCHEMA}."16_fct_framework_deployments" d
                JOIN {SCHEMA}."31_lnk_framework_version_controls" lvc
                    ON lvc.framework_version_id = d.deployed_version_id
                WHERE d.id = $1
            ),
            new_controls AS (
                SELECT lvc.control_id
                FROM {SCHEMA}."31_lnk_framework_version_controls" lvc
                WHERE lvc.framework_version_id = $2
            ),
            combined AS (
                SELECT control_id, 'added' AS change_type
                FROM new_controls WHERE control_id NOT IN (SELECT control_id FROM current_controls)
                UNION ALL
                SELECT control_id, 'removed' AS change_type
                FROM current_controls WHERE control_id NOT IN (SELECT control_id FROM new_controls)
            )
            SELECT cm.change_type, c.id::text, c.control_code,
                   cp_name.property_value AS name,
                   c.control_category_code, c.criticality_code
            FROM combined cm
            JOIN {SCHEMA}."13_fct_controls" c ON c.id = cm.control_id AND c.is_deleted = FALSE
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" cp_name
                ON cp_name.control_id = c.id AND cp_name.property_key = 'name'
            ORDER BY cm.change_type, c.control_code
            """,
            deployment_id,
            new_version_id,
        )
        added = [dict(r) for r in rows if r["change_type"] == "added"]
        removed = [dict(r) for r in rows if r["change_type"] == "removed"]
        return {
            "added": added,
            "removed": removed,
            "added_count": len(added),
            "removed_count": len(removed),
        }

    async def get_source_upgrade_diff(
        self,
        connection: asyncpg.Connection,
        *,
        from_version_id: str,
        new_version_id: str,
    ) -> dict:
        """Return added/removed controls between two source versions using control_code diff."""
        rows = await connection.fetch(
            f"""
            WITH from_controls AS (
                SELECT c.id::text, c.control_code, c.control_category_code, c.criticality_code,
                       cp_name.property_value AS name
                FROM {SCHEMA}."31_lnk_framework_version_controls" lvc
                JOIN {SCHEMA}."13_fct_controls" c
                    ON c.id = lvc.control_id AND c.is_deleted = FALSE
                LEFT JOIN {SCHEMA}."23_dtl_control_properties" cp_name
                    ON cp_name.control_id = c.id AND cp_name.property_key = 'name'
                WHERE lvc.framework_version_id = $1::uuid
            ),
            to_controls AS (
                SELECT c.id::text, c.control_code, c.control_category_code, c.criticality_code,
                       cp_name.property_value AS name
                FROM {SCHEMA}."31_lnk_framework_version_controls" lvc
                JOIN {SCHEMA}."13_fct_controls" c
                    ON c.id = lvc.control_id AND c.is_deleted = FALSE
                LEFT JOIN {SCHEMA}."23_dtl_control_properties" cp_name
                    ON cp_name.control_id = c.id AND cp_name.property_key = 'name'
                WHERE lvc.framework_version_id = $2::uuid
            )
            SELECT 'added' AS change_type, t.id, t.control_code, t.name,
                   t.control_category_code, t.criticality_code
            FROM to_controls t
            WHERE NOT EXISTS (SELECT 1 FROM from_controls f WHERE f.control_code = t.control_code)
            UNION ALL
            SELECT 'removed' AS change_type, f.id, f.control_code, f.name,
                   f.control_category_code, f.criticality_code
            FROM from_controls f
            WHERE NOT EXISTS (SELECT 1 FROM to_controls t WHERE t.control_code = f.control_code)
            ORDER BY change_type, control_code
            """,
            from_version_id,
            new_version_id,
        )
        added = [dict(r) for r in rows if r["change_type"] == "added"]
        removed = [dict(r) for r in rows if r["change_type"] == "removed"]
        return {
            "added": added,
            "removed": removed,
            "added_count": len(added),
            "removed_count": len(removed),
        }


def _row_to_record(r) -> FrameworkDeploymentRecord:
    return FrameworkDeploymentRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        framework_id=r["framework_id"],
        deployed_version_id=r["deployed_version_id"],
        deployment_status=r["deployment_status"],
        workspace_id=r["workspace_id"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
        framework_code=r["framework_code"],
        framework_name=r["framework_name"],
        framework_description=r["framework_description"],
        publisher_name=r["publisher_name"],
        logo_url=r["logo_url"],
        approval_status=r["approval_status"],
        is_marketplace_visible=r["is_marketplace_visible"],
        deployed_version_code=r["deployed_version_code"],
        deployed_lifecycle_state=r["deployed_lifecycle_state"],
        latest_version_id=r["latest_version_id"],
        latest_version_code=r["latest_version_code"],
        has_update=r["has_update"] or False,
        source_framework_id=r["source_framework_id"],
        source_version_id=r["source_version_id"],
        latest_release_notes=r.get("latest_release_notes"),
        latest_change_severity=r.get("latest_change_severity"),
        latest_change_summary=r.get("latest_change_summary"),
    )
