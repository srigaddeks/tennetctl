"""Repository for AI test-control linking."""
from __future__ import annotations

from importlib import import_module

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.test_linker.repository")

_CONTROLS = '"05_grc_library"."13_fct_controls"'
_CONTROL_VIEW = '"05_grc_library"."41_vw_control_detail"'
_CONTROL_PROPS = '"05_grc_library"."23_dtl_control_properties"'
_TESTS = '"05_grc_library"."14_fct_control_tests"'
_TEST_VIEW = '"05_grc_library"."42_vw_test_detail"'
_TEST_PROPS = '"05_grc_library"."24_dtl_test_properties"'
_MAPPINGS = '"05_grc_library"."30_lnk_test_control_mappings"'
_FRAMEWORKS = '"05_grc_library"."10_fct_frameworks"'
_FRAMEWORK_DEPLOYMENTS = '"05_grc_library"."16_fct_framework_deployments"'
_JOBS = '"20_ai"."45_fct_job_queue"'


class TestLinkerRepository:
    async def list_controls_for_framework(
        self,
        conn: asyncpg.Connection,
        *,
        framework_id: str,
        tenant_key: str,
        deployed_org_id: str | None = None,
        deployed_workspace_id: str | None = None,
    ) -> list[dict]:
        return await self.list_all_controls(
            conn,
            tenant_key=tenant_key,
            framework_id=framework_id,
            deployed_org_id=deployed_org_id,
            deployed_workspace_id=deployed_workspace_id,
        )

    async def list_all_controls(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        framework_id: str | None = None,
        deployed_org_id: str | None = None,
        deployed_workspace_id: str | None = None,
        control_ids: list[str] | None = None,
        limit: int = 500,
    ) -> list[dict]:
        conditions = ["tenant_key = $1", "is_deleted = FALSE", "is_active = TRUE"]
        args: list[object] = [tenant_key]
        idx = 2

        if framework_id:
            conditions.append(f"framework_id = ${idx}::uuid")
            args.append(framework_id)
            idx += 1
        if control_ids:
            conditions.append(f"id = ANY(${idx}::uuid[])")
            args.append(control_ids)
            idx += 1
        if deployed_org_id:
            if deployed_workspace_id:
                conditions.append(
                    f"""
                    framework_id IN (
                        SELECT framework_id
                        FROM {_FRAMEWORK_DEPLOYMENTS}
                        WHERE org_id = ${idx}::uuid
                          AND deployment_status != 'removed'
                          AND (workspace_id = ${idx + 1}::uuid OR workspace_id IS NULL)
                    )
                    """
                )
                args.extend([deployed_org_id, deployed_workspace_id])
                idx += 2
            else:
                conditions.append(
                    f"""
                    framework_id IN (
                        SELECT framework_id
                        FROM {_FRAMEWORK_DEPLOYMENTS}
                        WHERE org_id = ${idx}::uuid
                          AND deployment_status != 'removed'
                    )
                    """
                )
                args.append(deployed_org_id)
                idx += 1

        args.append(limit)
        rows = await conn.fetch(
            f"""
            SELECT
                id::text,
                control_code,
                control_category_code,
                control_type,
                automation_potential,
                criticality_code,
                framework_id::text AS framework_id,
                framework_code,
                framework_name AS framework_name,
                name,
                description,
                requirement_name
            FROM {_CONTROL_VIEW}
            WHERE {" AND ".join(conditions)}
            ORDER BY framework_code, sort_order, control_code
            LIMIT ${idx}
            """,
            *args,
        )
        return [dict(r) for r in rows]

    async def get_control_detail(
        self,
        conn: asyncpg.Connection,
        *,
        control_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT
                c.id::text,
                c.control_code,
                c.control_category_code,
                c.control_type,
                c.criticality_code,
                c.framework_id::text AS framework_id,
                f.framework_code,
                f.scope_org_id::text AS scope_org_id,
                f.scope_workspace_id::text AS scope_workspace_id,
                p_name.property_value AS name,
                p_desc.property_value AS description
            FROM {_CONTROLS} c
            JOIN {_FRAMEWORKS} f ON f.id = c.framework_id
            LEFT JOIN {_CONTROL_PROPS} p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN {_CONTROL_PROPS} p_desc
                ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            WHERE c.id = $1::uuid
              AND c.tenant_key = $2
              AND c.is_active = TRUE
              AND c.is_deleted = FALSE
              AND f.is_deleted = FALSE
            """,
            control_id,
            tenant_key,
        )
        return dict(row) if row else None

    async def list_tests(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        test_ids: list[str] | None = None,
        limit: int = 500,
    ) -> list[dict]:
        conditions = ["tenant_key = $1", "is_deleted = FALSE", "is_active = TRUE"]
        args: list[object] = [tenant_key]
        idx = 2

        if scope_org_id is not None:
            conditions.append(f"(scope_org_id = ${idx}::uuid OR scope_org_id IS NULL)")
            args.append(scope_org_id)
            idx += 1
        if scope_workspace_id is not None:
            conditions.append(f"(scope_workspace_id = ${idx}::uuid OR scope_workspace_id IS NULL)")
            args.append(scope_workspace_id)
            idx += 1
        if test_ids:
            conditions.append(f"id = ANY(${idx}::uuid[])")
            args.append(test_ids)
            idx += 1

        args.append(limit)
        rows = await conn.fetch(
            f"""
            SELECT
                id::text,
                test_code,
                test_type_code,
                integration_type,
                monitoring_frequency,
                name,
                description,
                signal_type,
                LEFT(evaluation_rule, 500) AS evaluation_rule_summary,
                scope_org_id::text AS scope_org_id,
                scope_workspace_id::text AS scope_workspace_id
            FROM {_TEST_VIEW}
            WHERE {" AND ".join(conditions)}
            ORDER BY test_code
            LIMIT ${idx}
            """,
            *args,
        )
        return [dict(r) for r in rows]

    async def get_existing_mappings(self, conn: asyncpg.Connection, *, test_id: str) -> set[str]:
        rows = await conn.fetch(
            f"SELECT control_id::text FROM {_MAPPINGS} WHERE control_test_id = $1::uuid",
            test_id,
        )
        return {r["control_id"] for r in rows}

    async def get_existing_mappings_for_control(
        self,
        conn: asyncpg.Connection,
        *,
        control_id: str,
    ) -> set[str]:
        rows = await conn.fetch(
            f"SELECT control_test_id::text FROM {_MAPPINGS} WHERE control_id = $1::uuid",
            control_id,
        )
        return {r["control_test_id"] for r in rows}

    async def create_mapping_if_not_exists(
        self,
        conn: asyncpg.Connection,
        *,
        test_id: str,
        control_id: str,
        link_type: str,
        ai_confidence: float,
        ai_rationale: str,
        created_by: str,
    ) -> str | None:
        row = await conn.fetchrow(
            f"""
            INSERT INTO {_MAPPINGS} (
                id, control_test_id, control_id, is_primary, sort_order,
                link_type, approval_status, ai_confidence, ai_rationale,
                created_at, created_by
            ) VALUES (
                gen_random_uuid(), $1::uuid, $2::uuid, FALSE, 0,
                $3, 'pending', $4, $5,
                NOW(), $6::uuid
            )
            ON CONFLICT (control_test_id, control_id) DO NOTHING
            RETURNING id::text
            """,
            test_id,
            control_id,
            link_type,
            ai_confidence,
            ai_rationale,
            created_by,
        )
        return row["id"] if row else None

    async def approve_mapping(self, conn: asyncpg.Connection, *, mapping_id: str) -> None:
        await conn.execute(
            f"UPDATE {_MAPPINGS} SET approval_status = 'approved' WHERE id = $1::uuid",
            mapping_id,
        )

    async def reject_mapping(self, conn: asyncpg.Connection, *, mapping_id: str) -> None:
        await conn.execute(
            f"UPDATE {_MAPPINGS} SET approval_status = 'rejected' WHERE id = $1::uuid",
            mapping_id,
        )

    async def bulk_set_approval_status(
        self,
        conn: asyncpg.Connection,
        *,
        mapping_ids: list[str],
        status: str,
    ) -> int:
        result = await conn.execute(
            f"""
            UPDATE {_MAPPINGS}
            SET approval_status = $1
            WHERE id = ANY($2::uuid[])
              AND approval_status = 'pending'
            """,
            status,
            mapping_ids,
        )
        return int(result.split()[-1]) if result else 0

    async def list_pending_mappings(
        self,
        conn: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        framework_id: str | None = None,
        test_ids: list[str] | None = None,
        control_ids: list[str] | None = None,
        created_after: str | None = None,
        created_by: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        conditions = [
            "m.approval_status = 'pending'",
            "t.tenant_key = $1",
            "t.is_deleted = FALSE",
            "c.is_deleted = FALSE",
            "f.is_deleted = FALSE",
        ]
        args: list[object] = [tenant_key]
        idx = 2

        if org_id is not None:
            conditions.append(f"(t.scope_org_id = ${idx}::uuid OR t.scope_org_id IS NULL)")
            args.append(org_id)
            idx += 1
        if workspace_id is not None:
            conditions.append(f"(t.scope_workspace_id = ${idx}::uuid OR t.scope_workspace_id IS NULL)")
            args.append(workspace_id)
            idx += 1
        if framework_id is not None:
            conditions.append(f"f.id = ${idx}::uuid")
            args.append(framework_id)
            idx += 1
        if test_ids:
            conditions.append(f"m.control_test_id = ANY(${idx}::uuid[])")
            args.append(test_ids)
            idx += 1
        if control_ids:
            conditions.append(f"m.control_id = ANY(${idx}::uuid[])")
            args.append(control_ids)
            idx += 1
        if created_after is not None:
            conditions.append(f"m.created_at >= ${idx}::timestamp")
            args.append(created_after)
            idx += 1
        if created_by is not None:
            conditions.append(f"m.created_by = ${idx}::uuid")
            args.append(created_by)
            idx += 1

        where_clause = " AND ".join(conditions)
        count_row = await conn.fetchrow(
            f"""
            SELECT COUNT(*)::int AS total
            FROM {_MAPPINGS} m
            JOIN {_TESTS} t ON t.id = m.control_test_id
            JOIN {_CONTROLS} c ON c.id = m.control_id
            JOIN {_FRAMEWORKS} f ON f.id = c.framework_id
            WHERE {where_clause}
            """,
            *args,
        )
        total = count_row["total"] if count_row else 0

        args.extend([limit, offset])
        rows = await conn.fetch(
            f"""
            SELECT
                m.id::text,
                m.control_test_id::text,
                m.control_id::text,
                m.link_type,
                m.ai_confidence,
                m.ai_rationale,
                m.approval_status,
                m.created_at::text,
                m.created_by::text AS created_by,
                t.test_code,
                tp_name.property_value AS test_name,
                c.control_code,
                cp_name.property_value AS control_name,
                f.id::text AS framework_id,
                f.framework_code
            FROM {_MAPPINGS} m
            JOIN {_TESTS} t ON t.id = m.control_test_id
            JOIN {_CONTROLS} c ON c.id = m.control_id
            JOIN {_FRAMEWORKS} f ON f.id = c.framework_id
            LEFT JOIN {_TEST_PROPS} tp_name
                ON tp_name.test_id = m.control_test_id AND tp_name.property_key = 'name'
            LEFT JOIN {_CONTROL_PROPS} cp_name
                ON cp_name.control_id = m.control_id AND cp_name.property_key = 'name'
            WHERE {where_clause}
            ORDER BY m.created_at DESC, m.ai_confidence DESC NULLS LAST, t.test_code, c.control_code
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *args,
        )
        return [dict(r) for r in rows], total

    async def get_job_status(
        self,
        conn: asyncpg.Connection,
        job_id: str,
        tenant_key: str,
    ) -> dict | None:
        row = await conn.fetchrow(
            f"""
            SELECT
                id::text AS job_id,
                status_code,
                job_type,
                output_json,
                error_message,
                created_at::text,
                updated_at::text
            FROM {_JOBS}
            WHERE id = $1::uuid AND tenant_key = $2
            """,
            job_id,
            tenant_key,
        )
        return dict(row) if row else None
