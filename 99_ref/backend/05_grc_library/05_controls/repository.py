from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import ControlDetailRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module(
    "backend.01_core.telemetry"
).instrument_class_methods

_CONTROL_SELECT = """
    SELECT id, framework_id, requirement_id::text, tenant_key, control_code,
           control_category_code, category_name, criticality_code, criticality_name,
           control_type, automation_potential, sort_order, version,
           is_active, created_at::text, updated_at::text,
           name, description, guidance, implementation_notes,
           framework_code, framework_name, requirement_code, requirement_name,
           test_count
    FROM {schema}."41_vw_control_detail"
"""


@instrument_class_methods(
    namespace="grc.controls.repository",
    logger_name="backend.grc.controls.repository.instrumentation",
)
class ControlRepository:
    _CONTROL_SORT_COLUMNS = frozenset(
        {
            "name",
            "control_code",
            "sort_order",
            "created_at",
            "updated_at",
            "criticality_code",
        }
    )

    async def list_all_controls(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        search: str | None = None,
        framework_id: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        deployed_org_id: str | None = None,
        deployed_workspace_id: str | None = None,
        control_category_code: str | None = None,
        criticality_code: str | None = None,
        control_type: str | None = None,
        automation_potential: str | None = None,
        owner_user_id: str | None = None,
        sort_by: str = "sort_order",
        sort_dir: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ControlDetailRecord], int]:
        filters = ["tenant_key = $1", "is_deleted = FALSE"]
        values: list[object] = [tenant_key]
        idx = 2

        if search is not None:
            filters.append(
                f"(LOWER(name) LIKE ${idx} OR LOWER(control_code) LIKE ${idx})"
            )
            values.append(f"%{search.lower()}%")
            idx += 1
        if framework_id is not None:
            filters.append(f"framework_id = ${idx}::uuid")
            values.append(framework_id)
            idx += 1
        if scope_org_id is not None:
            filters.append(
                f'framework_id IN (SELECT id FROM {SCHEMA}."10_fct_frameworks" WHERE scope_org_id = ${idx}::uuid AND is_deleted = FALSE)'
            )
            values.append(scope_org_id)
            idx += 1
        if scope_workspace_id is not None:
            filters.append(
                f'framework_id IN (SELECT id FROM {SCHEMA}."10_fct_frameworks" WHERE scope_workspace_id = ${idx}::uuid AND is_deleted = FALSE)'
            )
            values.append(scope_workspace_id)
            idx += 1
        if deployed_org_id is not None:
            if deployed_workspace_id is not None:
                filters.append(
                    f'framework_id IN (SELECT framework_id FROM {SCHEMA}."16_fct_framework_deployments"'
                    f" WHERE org_id = ${idx}::uuid AND deployment_status != 'removed'"
                    f" AND (workspace_id = ${idx + 1}::uuid OR workspace_id IS NULL))"
                )
                values.append(deployed_org_id)
                values.append(deployed_workspace_id)
                idx += 2
            else:
                filters.append(
                    f'framework_id IN (SELECT framework_id FROM {SCHEMA}."16_fct_framework_deployments"'
                    f" WHERE org_id = ${idx}::uuid AND deployment_status != 'removed')"
                )
                values.append(deployed_org_id)
                idx += 1
        if control_category_code is not None:
            filters.append(f"control_category_code = ${idx}")
            values.append(control_category_code)
            idx += 1
        if criticality_code is not None:
            filters.append(f"criticality_code = ${idx}")
            values.append(criticality_code)
            idx += 1
        if control_type is not None:
            filters.append(f"control_type = ${idx}")
            values.append(control_type)
            idx += 1
        if automation_potential is not None:
            filters.append(f"automation_potential = ${idx}")
            values.append(automation_potential)
            idx += 1
        if owner_user_id is not None:
            # Filter to controls where owner_user_id EAV property matches the given user
            filters.append(
                f"id IN ("
                f'SELECT control_id FROM {SCHEMA}."23_dtl_control_properties"'
                f" WHERE property_key = 'owner_user_id' AND property_value = ${idx}"
                f")"
            )
            values.append(owner_user_id)
            idx += 1

        where_clause = " AND ".join(filters)
        schema = SCHEMA

        sort_col = sort_by if sort_by in self._CONTROL_SORT_COLUMNS else "sort_order"
        sort_direction = "DESC" if sort_dir == "desc" else "ASC"
        order_clause = f"{sort_col} {sort_direction}, control_code ASC"

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {schema}."41_vw_control_detail" WHERE {where_clause}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            {_CONTROL_SELECT.format(schema=schema)}
            WHERE {where_clause}
            ORDER BY {order_clause}
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_control(r) for r in rows], total

    async def list_controls(
        self,
        connection: asyncpg.Connection,
        *,
        framework_id: str,
        search: str | None = None,
        control_category_code: str | None = None,
        criticality_code: str | None = None,
        control_type: str | None = None,
        automation_potential: str | None = None,
        limit: int = 100,
        offset: int = 0,
        version_id: str | None = None,
    ) -> tuple[list[ControlDetailRecord], int]:
        filters = ["c.framework_id = $1", "c.is_deleted = FALSE"]
        values: list[object] = [framework_id]
        idx = 2

        if version_id:
            filters.append(f"""
                EXISTS (
                    SELECT 1 FROM {SCHEMA}."31_lnk_framework_version_controls" lvc
                    WHERE lvc.framework_version_id = ${idx}::uuid
                      AND lvc.control_id = c.id
                )
            """)
            values.append(version_id)
            idx += 1

        if search is not None:
            filters.append(
                f"(LOWER(p_name.property_value) LIKE ${idx} OR LOWER(c.control_code) LIKE ${idx})"
            )
            values.append(f"%{search.lower()}%")
            idx += 1
        if control_category_code is not None:
            filters.append(f"c.control_category_code = ${idx}")
            values.append(control_category_code)
            idx += 1
        if criticality_code is not None:
            filters.append(f"c.criticality_code = ${idx}")
            values.append(criticality_code)
            idx += 1
        if control_type is not None:
            filters.append(f"c.control_type = ${idx}")
            values.append(control_type)
            idx += 1
        if automation_potential is not None:
            filters.append(f"c.automation_potential = ${idx}")
            values.append(automation_potential)
            idx += 1

        where_clause = " AND ".join(filters)
        schema = SCHEMA

        count_row = await connection.fetchrow(
            f"""SELECT COUNT(*)::int AS total 
                FROM {schema}."13_fct_controls" c
                LEFT JOIN {schema}."23_dtl_control_properties" p_name 
                    ON p_name.control_id = c.id AND p_name.property_key = 'name'
                WHERE {where_clause}""",
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT c.id, c.framework_id, c.requirement_id::text, c.tenant_key, c.control_code,
                   c.control_category_code, cat.name AS category_name, c.criticality_code, crit.name AS criticality_name,
                   c.control_type, c.automation_potential, c.sort_order, c.version,
                   c.is_active, c.created_at::text, c.updated_at::text,
                   p_name.property_value AS name, p_desc.property_value AS description,
                   p_guid.property_value AS guidance, p_impl.property_value AS implementation_notes,
                   f.framework_code, fw_name.property_value AS framework_name,
                   r.requirement_code, rq_name.property_value AS requirement_name,
                   (SELECT COUNT(*) FROM {schema}."30_lnk_test_control_mappings" m WHERE m.control_id = c.id) AS test_count
            FROM {schema}."13_fct_controls" c
            LEFT JOIN {schema}."04_dim_control_categories" cat ON cat.code = c.control_category_code
            LEFT JOIN {schema}."05_dim_control_criticalities" crit ON crit.code = c.criticality_code
            LEFT JOIN {schema}."10_fct_frameworks" f ON f.id = c.framework_id
            LEFT JOIN {schema}."20_dtl_framework_properties" fw_name ON fw_name.framework_id = f.id AND fw_name.property_key = 'name'
            LEFT JOIN {schema}."12_fct_requirements" r ON r.id = c.requirement_id
            LEFT JOIN {schema}."22_dtl_requirement_properties" rq_name ON rq_name.requirement_id = r.id AND rq_name.property_key = 'name'
            LEFT JOIN {schema}."23_dtl_control_properties" p_name ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN {schema}."23_dtl_control_properties" p_desc ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN {schema}."23_dtl_control_properties" p_guid ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
            LEFT JOIN {schema}."23_dtl_control_properties" p_impl ON p_impl.control_id = c.id AND p_impl.property_key = 'implementation_notes'
            WHERE {where_clause}
            ORDER BY c.sort_order, c.control_code
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_control(r) for r in rows], total

    async def get_control_by_id(
        self, connection: asyncpg.Connection, control_id: str
    ) -> ControlDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            {_CONTROL_SELECT.format(schema=SCHEMA)}
            WHERE id = $1 AND is_deleted = FALSE
            """,
            control_id,
        )
        return _row_to_control(row) if row else None

    async def create_control(
        self,
        connection: asyncpg.Connection,
        *,
        control_id: str,
        framework_id: str,
        tenant_key: str,
        control_code: str,
        control_category_code: str,
        criticality_code: str,
        control_type: str,
        automation_potential: str,
        requirement_id: str | None,
        sort_order: int,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."13_fct_controls"
                (id, framework_id, requirement_id, tenant_key, control_code,
                 control_category_code, criticality_code, control_type, automation_potential,
                 sort_order,
                 is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                 created_at, updated_at, created_by, updated_by, deleted_at, deleted_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8, $9,
                 $10,
                 TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                 $11, $12, $13, $14, NULL, NULL)
            """,
            control_id,
            framework_id,
            requirement_id,
            tenant_key,
            control_code,
            control_category_code,
            criticality_code,
            control_type,
            automation_potential,
            sort_order,
            now,
            now,
            created_by,
            created_by,
        )
        return control_id

    async def update_control(
        self,
        connection: asyncpg.Connection,
        control_id: str,
        *,
        control_category_code: str | None = None,
        criticality_code: str | None = None,
        control_type: str | None = None,
        automation_potential: str | None = None,
        requirement_id: str | None = None,
        sort_order: int | None = None,
        updated_by: str,
        now: object,
    ) -> bool:
        fields: list[str] = [
            "updated_at = $1",
            "updated_by = $2",
            "version = version + 1",
        ]
        values: list[object] = [now, updated_by]
        idx = 3

        if control_category_code is not None:
            fields.append(f"control_category_code = ${idx}")
            values.append(control_category_code)
            idx += 1
        if criticality_code is not None:
            fields.append(f"criticality_code = ${idx}")
            values.append(criticality_code)
            idx += 1
        if control_type is not None:
            fields.append(f"control_type = ${idx}")
            values.append(control_type)
            idx += 1
        if automation_potential is not None:
            fields.append(f"automation_potential = ${idx}")
            values.append(automation_potential)
            idx += 1
        if requirement_id is not None:
            fields.append(f"requirement_id = ${idx}")
            values.append(requirement_id)
            idx += 1
        if sort_order is not None:
            fields.append(f"sort_order = ${idx}")
            values.append(sort_order)
            idx += 1

        values.append(control_id)
        set_clause = ", ".join(fields)

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."13_fct_controls"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            """,
            *values,
        )
        return result != "UPDATE 0"

    async def soft_delete_control(
        self,
        connection: asyncpg.Connection,
        control_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."13_fct_controls"
            SET is_deleted = TRUE, is_active = FALSE, deleted_at = $1,
                deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now,
            deleted_by,
            now,
            deleted_by,
            control_id,
        )
        return result != "UPDATE 0"

    async def upsert_control_properties(
        self,
        connection: asyncpg.Connection,
        *,
        control_id: str,
        properties: dict[str, str],
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (control_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
                INSERT INTO {SCHEMA}."23_dtl_control_properties"
                    (id, control_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (control_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
            rows,
        )

    async def get_all_properties(
        self, connection: asyncpg.Connection, control_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."23_dtl_control_properties"
            WHERE control_id = $1
            """,
            control_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    async def list_controls_with_properties(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> list[dict]:
        """Fetch all controls in a framework with all EAV properties merged.
        Single JOIN query — no N+1.
        """
        rows = await connection.fetch(
            f"""
            SELECT
                c.id, c.framework_id, c.requirement_id::text, c.tenant_key,
                c.control_code, c.control_category_code, c.category_name,
                c.criticality_code, c.criticality_name, c.control_type,
                c.automation_potential, c.sort_order, c.version, c.is_active,
                c.created_at::text, c.updated_at::text,
                c.name, c.description, c.guidance, c.implementation_notes,
                c.framework_code, c.framework_name, c.requirement_code, c.requirement_name,
                c.test_count,
                p.property_key, p.property_value
            FROM {SCHEMA}."41_vw_control_detail" c
            LEFT JOIN {SCHEMA}."23_dtl_control_properties" p ON p.control_id = c.id
            WHERE c.framework_id = $1 AND c.is_deleted = FALSE
            ORDER BY c.sort_order, c.control_code
            """,
            framework_id,
        )
        # Group rows by control id, merging EAV properties
        controls: dict[str, dict] = {}
        for row in rows:
            cid = str(row["id"])
            if cid not in controls:
                controls[cid] = dict(row)
                controls[cid]["_props"] = {}
            if row["property_key"]:
                controls[cid]["_props"][row["property_key"]] = row["property_value"]
        result = []
        for ctrl in controls.values():
            props = ctrl.pop("_props", {})
            ctrl["property_key"] = None
            ctrl["property_value"] = None
            ctrl.pop("property_key", None)
            ctrl.pop("property_value", None)
            ctrl["tags"] = props.get("tags")
            ctrl["implementation_guidance"] = props.get("implementation_guidance")
            ctrl["owner_user_id"] = props.get("owner_user_id")
            ctrl["owner_email"] = None  # resolved separately if needed
            ctrl["responsible_teams"] = props.get("responsible_teams")
            result.append(ctrl)
        return result

    async def list_controls_by_code(
        self, connection: asyncpg.Connection, *, framework_id: str
    ) -> dict[str, str]:
        """Return mapping of control_code -> control_id for a framework."""
        rows = await connection.fetch(
            f"""
            SELECT control_code, id::text AS control_id
            FROM {SCHEMA}."13_fct_controls"
            WHERE framework_id = $1 AND is_deleted = FALSE
            """,
            framework_id,
        )
        return {row["control_code"]: row["control_id"] for row in rows}

    async def resolve_owner_names_batch(
        self, connection: asyncpg.Connection, user_ids: list[str]
    ) -> dict[str, tuple[str | None, str | None]]:
        """Return {user_id: (display_name, email)} for a list of user IDs."""
        if not user_ids:
            return {}
        rows = await connection.fetch(
            """
            SELECT user_id::text, property_key, property_value
            FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = ANY($1::uuid[])
              AND property_key IN ('display_name', 'email')
            """,
            user_ids,
        )
        result: dict[str, dict[str, str]] = {}
        for row in rows:
            uid = row["user_id"]
            if uid not in result:
                result[uid] = {}
            result[uid][row["property_key"]] = row["property_value"]
        return {
            uid: (props.get("display_name"), props.get("email"))
            for uid, props in result.items()
        }


def _row_to_control(r) -> ControlDetailRecord:
    return ControlDetailRecord(
        id=r["id"],
        framework_id=r["framework_id"],
        requirement_id=r["requirement_id"],
        tenant_key=r["tenant_key"],
        control_code=r["control_code"],
        control_category_code=r["control_category_code"],
        category_name=r["category_name"],
        criticality_code=r["criticality_code"],
        criticality_name=r["criticality_name"],
        control_type=r["control_type"],
        automation_potential=r["automation_potential"],
        sort_order=r["sort_order"],
        version=r["version"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        name=r["name"],
        description=r["description"],
        guidance=r["guidance"],
        implementation_notes=r["implementation_notes"],
        framework_code=r["framework_code"],
        framework_name=r["framework_name"],
        requirement_code=r["requirement_code"],
        requirement_name=r["requirement_name"],
        test_count=r["test_count"],
    )
