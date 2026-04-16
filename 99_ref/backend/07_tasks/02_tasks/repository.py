from __future__ import annotations

from datetime import datetime

import asyncpg
from importlib import import_module

from .models import TaskDetailRecord, TaskRecord

SCHEMA = '"08_tasks"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


def _parse_dt(value: str | None) -> datetime | None:
    """Parse an ISO date/datetime string to a datetime object for asyncpg."""
    if value is None:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%f", 
        "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f"
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date string: {value!r}")

_PRIORITY_SORT = "CASE v.priority_code WHEN 'critical' THEN 1 WHEN 'high' THEN 2 WHEN 'medium' THEN 3 WHEN 'low' THEN 4 ELSE 5 END"
_VALID_SORT_FIELDS = {"due_date", "priority", "created_at", "updated_at"}


def _accessible_engagement_filter_sql(task_alias: str, param_ref: str) -> str:
    return f"""
        (
            {task_alias}.entity_type IS NULL
            OR {task_alias}.entity_id IS NULL
            OR {task_alias}.entity_type NOT IN ('engagement', 'framework', 'control', 'requirement')
            OR (
                {task_alias}.entity_type = 'engagement'
                AND {task_alias}.entity_id = ANY({param_ref}::uuid[])
            )
            OR (
                {task_alias}.entity_type = 'framework'
                AND {task_alias}.entity_id IN (
                    SELECT e.framework_id
                    FROM "12_engagements"."10_fct_audit_engagements" e
                    WHERE e.id = ANY({param_ref}::uuid[])
                      AND e.is_deleted = FALSE
                )
            )
            OR (
                {task_alias}.entity_type = 'control'
                AND {task_alias}.entity_id IN (
                    SELECT c.id
                    FROM "05_grc_library"."13_fct_controls" c
                    JOIN "12_engagements"."10_fct_audit_engagements" e
                      ON e.framework_id = c.framework_id
                    WHERE e.id = ANY({param_ref}::uuid[])
                      AND e.is_deleted = FALSE
                      AND c.is_deleted = FALSE
                )
            )
            OR (
                {task_alias}.entity_type = 'requirement'
                AND {task_alias}.entity_id IN (
                    SELECT r.id
                    FROM "05_grc_library"."12_fct_requirements" r
                    JOIN "12_engagements"."10_fct_audit_engagements" e
                      ON e.framework_id = r.framework_id
                    WHERE e.id = ANY({param_ref}::uuid[])
                      AND e.is_deleted = FALSE
                      AND r.is_deleted = FALSE
                )
            )
        )
    """


@instrument_class_methods(namespace="tasks.repository", logger_name="backend.tasks.repository.instrumentation")
class TaskRepository:
    async def list_linked_engagement_ids_for_task_target(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        entity_type: str | None,
        entity_id: str | None,
    ) -> list[str]:
        normalized_entity_type = (entity_type or "").strip().lower()
        if not normalized_entity_type or not entity_id:
            return []

        if normalized_entity_type == "engagement":
            rows = await connection.fetch(
                """
                SELECT e.id::text
                FROM "12_engagements"."10_fct_audit_engagements" e
                WHERE e.id = $1::uuid
                  AND e.org_id = $2::uuid
                  AND e.is_deleted = FALSE
                """,
                entity_id,
                org_id,
            )
        elif normalized_entity_type == "framework":
            rows = await connection.fetch(
                """
                SELECT e.id::text
                FROM "12_engagements"."10_fct_audit_engagements" e
                WHERE e.framework_id = $1::uuid
                  AND e.org_id = $2::uuid
                  AND e.is_deleted = FALSE
                """,
                entity_id,
                org_id,
            )
        elif normalized_entity_type == "control":
            rows = await connection.fetch(
                """
                SELECT DISTINCT e.id::text
                FROM "12_engagements"."10_fct_audit_engagements" e
                JOIN "05_grc_library"."13_fct_controls" c
                  ON c.framework_id = e.framework_id
                 AND c.is_deleted = FALSE
                WHERE c.id = $1::uuid
                  AND e.org_id = $2::uuid
                  AND e.is_deleted = FALSE
                """,
                entity_id,
                org_id,
            )
        elif normalized_entity_type == "requirement":
            rows = await connection.fetch(
                """
                SELECT DISTINCT e.id::text
                FROM "12_engagements"."10_fct_audit_engagements" e
                JOIN "05_grc_library"."12_fct_requirements" r
                  ON r.framework_id = e.framework_id
                 AND r.is_deleted = FALSE
                WHERE r.id = $1::uuid
                  AND e.org_id = $2::uuid
                  AND e.is_deleted = FALSE
                """,
                entity_id,
                org_id,
            )
        else:
            return []

        return [row["id"] for row in rows]

    async def list_tasks(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        status_code: str | None = None,
        assignee_user_id: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
        priority_code: str | None = None,
        task_type_code: str | None = None,
        due_date_from: str | None = None,
        due_date_to: str | None = None,
        is_overdue: bool | None = None,
        reporter_user_id: str | None = None,
        scope_assignee_user_id: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
        engagement_id: str | None = None,
        accessible_engagement_ids: list[str] | None = None,
    ) -> tuple[list[TaskDetailRecord], int]:
        filters = ["v.tenant_key = $1"]
        values: list[object] = [tenant_key]
        idx = 2

        if org_id is not None:
            filters.append(f"v.org_id = ${idx}::uuid")
            values.append(org_id); idx += 1
        if workspace_id is not None:
            filters.append(f"v.workspace_id = ${idx}::uuid")
            values.append(workspace_id); idx += 1
        if status_code is not None:
            filters.append(f"v.status_code = ${idx}")
            values.append(status_code); idx += 1
        if assignee_user_id is not None:
            filters.append(f"v.assignee_user_id = ${idx}::uuid")
            values.append(assignee_user_id); idx += 1
        if entity_type == "framework" and entity_id is not None:
            filters.append(
                f"""
                (
                    (v.entity_type = 'framework' AND v.entity_id = ${idx}::uuid)
                    OR (v.entity_type = 'control' AND v.entity_id IN (SELECT id FROM "05_grc_library"."13_fct_controls" WHERE framework_id = ${idx}::uuid AND is_deleted = FALSE))
                    OR (v.entity_type = 'requirement' AND v.entity_id IN (SELECT id FROM "05_grc_library"."12_fct_requirements" WHERE framework_id = ${idx}::uuid AND is_deleted = FALSE))
                )
                """
            )
            values.append(entity_id); idx += 1
        else:
            if entity_type is not None:
                filters.append(f"v.entity_type = ${idx}")
                values.append(entity_type); idx += 1
            if entity_id is not None:
                filters.append(f"v.entity_id = ${idx}::uuid")
                values.append(entity_id); idx += 1
        if priority_code is not None:
            filters.append(f"v.priority_code = ${idx}")
            values.append(priority_code); idx += 1
        if task_type_code is not None:
            filters.append(f"v.task_type_code = ${idx}")
            values.append(task_type_code); idx += 1
        if due_date_from is not None:
            filters.append(f"v.due_date >= ${idx}")
            values.append(_parse_dt(due_date_from)); idx += 1
        if due_date_to is not None:
            filters.append(f"v.due_date <= ${idx}")
            values.append(_parse_dt(due_date_to)); idx += 1
        if is_overdue:
            filters.append("v.due_date < NOW() AND v.is_terminal = FALSE AND v.status_code != 'cancelled'")
        if reporter_user_id is not None:
            filters.append(f"v.reporter_user_id = ${idx}::uuid")
            values.append(reporter_user_id); idx += 1
        if engagement_id is not None:
            filters.append(
                f"""
                (
                    (v.entity_type = 'engagement' AND v.entity_id = ${idx}::uuid)
                    OR (v.entity_type = 'framework' AND v.entity_id IN (SELECT framework_id FROM "12_engagements"."10_fct_audit_engagements" WHERE id = ${idx}::uuid))
                    OR (v.entity_type = 'control' AND v.entity_id IN (
                         SELECT c.id FROM "05_grc_library"."13_fct_controls" c
                         JOIN "12_engagements"."10_fct_audit_engagements" eng ON eng.framework_id = c.framework_id
                         WHERE eng.id = ${idx}::uuid
                    ))
                    OR (v.entity_type = 'requirement' AND v.entity_id IN (
                         SELECT r.id FROM "05_grc_library"."12_fct_requirements" r
                         JOIN "12_engagements"."10_fct_audit_engagements" eng ON eng.framework_id = r.framework_id
                         WHERE eng.id = ${idx}::uuid
                    ))
                )
                """
            )
            values.append(engagement_id); idx += 1

        if scope_assignee_user_id is not None:
            filters.append(
                f"""
                (
                    v.assignee_user_id = ${idx}::uuid
                    OR EXISTS (
                        SELECT 1
                        FROM {SCHEMA}."31_lnk_task_assignments" AS a
                        WHERE a.task_id = v.id
                          AND a.user_id = ${idx}::uuid
                          AND a.is_deleted = FALSE
                    )
                )
                """
            )
            values.append(scope_assignee_user_id); idx += 1
        if accessible_engagement_ids is not None:
            filters.append(_accessible_engagement_filter_sql("v", f"${idx}"))
            values.append(accessible_engagement_ids)
            idx += 1

        where_clause = " AND ".join(filters)

        # Build ORDER BY (guard against injection via allowlist)
        safe_sort = sort_by if sort_by in _VALID_SORT_FIELDS else None
        if safe_sort == "priority":
            order_expr = _PRIORITY_SORT
        elif safe_sort == "due_date":
            order_expr = "v.due_date"
        elif safe_sort == "updated_at":
            order_expr = "v.updated_at"
        else:
            order_expr = "v.created_at"
        order_dir = "ASC" if sort_dir and sort_dir.lower() == "asc" else "DESC"

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."40_vw_task_detail" v WHERE {where_clause}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT v.id::text, v.tenant_key, v.org_id::text, v.workspace_id::text,
                   v.task_type_code, v.task_type_name, v.priority_code, v.priority_name,
                   v.status_code, v.status_name, v.is_terminal,
                   v.entity_type, v.entity_id::text,
                   v.assignee_user_id::text, v.reporter_user_id::text,
                   v.due_date::text, v.start_date::text, v.completed_at::text,
                   v.estimated_hours, v.actual_hours,
                   v.is_active, v.created_at::text, v.updated_at::text,
                   v.title, v.description, v.acceptance_criteria,
                   v.resolution_notes, v.remediation_plan,
                   v.co_assignee_count::int, v.blocker_count::int, v.comment_count::int
            FROM {SCHEMA}."40_vw_task_detail" v
            WHERE {where_clause}
            ORDER BY {order_expr} {order_dir}
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_task_detail(r) for r in rows], total

    async def get_task_detail(
        self,
        connection: asyncpg.Connection,
        task_id: str,
        *,
        scope_assignee_user_id: str | None = None,
    ) -> TaskDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT v.id::text, v.tenant_key, v.org_id::text, v.workspace_id::text,
                   v.task_type_code, v.task_type_name, v.priority_code, v.priority_name,
                   v.status_code, v.status_name, v.is_terminal,
                   v.entity_type, v.entity_id::text,
                   v.assignee_user_id::text, v.reporter_user_id::text,
                   v.due_date::text, v.start_date::text, v.completed_at::text,
                   v.estimated_hours, v.actual_hours,
                   v.is_active, v.created_at::text, v.updated_at::text,
                   v.title, v.description, v.acceptance_criteria,
                   v.resolution_notes, v.remediation_plan,
                   v.co_assignee_count::int, v.blocker_count::int, v.comment_count::int
            FROM {SCHEMA}."40_vw_task_detail" v
            WHERE v.id = $1::uuid
              AND (
                  $2::uuid IS NULL
                  OR (
                      v.assignee_user_id = $2::uuid
                      OR EXISTS (
                          SELECT 1
                          FROM {SCHEMA}."31_lnk_task_assignments" AS a
                          WHERE a.task_id = v.id
                            AND a.user_id = $2::uuid
                            AND a.is_deleted = FALSE
                      )
                  )
              )
            """,
            task_id,
            scope_assignee_user_id,
        )
        return _row_to_task_detail(row) if row else None

    async def get_task_by_id(
        self, connection: asyncpg.Connection, task_id: str
    ) -> TaskRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, org_id::text, workspace_id::text,
                   task_type_code, priority_code, status_code,
                   entity_type, entity_id::text,
                   assignee_user_id::text, reporter_user_id::text,
                   due_date::text, start_date::text, completed_at::text,
                   estimated_hours, actual_hours,
                   is_active, version, created_at::text, updated_at::text
            FROM {SCHEMA}."10_fct_tasks"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            task_id,
        )
        return _row_to_task(row) if row else None

    async def get_task_summary(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        scope_assignee_user_id: str | None = None,
        engagement_id: str | None = None,
        accessible_engagement_ids: list[str] | None = None,
    ) -> dict:
        base_filters = ["v.tenant_key = $1"]
        values: list[object] = [tenant_key]
        idx = 2
        if org_id is not None:
            base_filters.append(f"v.org_id = ${idx}::uuid")
            values.append(org_id); idx += 1
        if workspace_id is not None:
            base_filters.append(f"v.workspace_id = ${idx}::uuid")
            values.append(workspace_id); idx += 1
        if engagement_id is not None:
            base_filters.append(
                f"""
                (
                    (v.entity_type = 'engagement' AND v.entity_id = ${idx}::uuid)
                    OR (v.entity_type = 'framework' AND v.entity_id IN (SELECT framework_id FROM "12_engagements"."10_fct_audit_engagements" WHERE id = ${idx}::uuid))
                    OR (v.entity_type = 'control' AND v.entity_id IN (
                         SELECT c.id FROM "05_grc_library"."13_fct_controls" c
                         JOIN "12_engagements"."10_fct_audit_engagements" eng ON eng.framework_id = c.framework_id
                         WHERE eng.id = ${idx}::uuid
                    ))
                    OR (v.entity_type = 'requirement' AND v.entity_id IN (
                         SELECT r.id FROM "05_grc_library"."12_fct_requirements" r
                         JOIN "12_engagements"."10_fct_audit_engagements" eng ON eng.framework_id = r.framework_id
                         WHERE eng.id = ${idx}::uuid
                    ))
                )
                """
            )
            values.append(engagement_id); idx += 1

        if scope_assignee_user_id is not None:
            base_filters.append(
                f"""
                (
                    v.assignee_user_id = ${idx}::uuid
                    OR EXISTS (
                        SELECT 1
                        FROM {SCHEMA}."31_lnk_task_assignments" AS a
                        WHERE a.task_id = v.id
                          AND a.user_id = ${idx}::uuid
                          AND a.is_deleted = FALSE
                    )
                )
                """
            )
            values.append(scope_assignee_user_id); idx += 1
        if accessible_engagement_ids is not None:
            base_filters.append(_accessible_engagement_filter_sql("v", f"${idx}"))
            values.append(accessible_engagement_ids)
            idx += 1
        where = " AND ".join(base_filters)

        # Status counts
        status_rows = await connection.fetch(
            f'SELECT v.status_code, COUNT(*)::int AS cnt FROM {SCHEMA}."40_vw_task_detail" AS v WHERE {where} GROUP BY v.status_code',
            *values,
        )
        counts = {r["status_code"]: r["cnt"] for r in status_rows}

        # Overdue count
        overdue_row = await connection.fetchrow(
            f"""SELECT COUNT(*)::int AS cnt FROM {SCHEMA}."40_vw_task_detail" AS v
                WHERE {where} AND due_date < NOW()
                AND status_code NOT IN ('resolved', 'cancelled')""",
            *values,
        )
        overdue_count = overdue_row["cnt"] if overdue_row else 0

        # Resolved this week count
        resolved_week_row = await connection.fetchrow(
            f"""SELECT COUNT(*)::int AS cnt FROM {SCHEMA}."40_vw_task_detail" AS v
                WHERE {where} AND status_code = 'resolved'
                AND completed_at >= date_trunc('week', NOW() AT TIME ZONE 'UTC')""",
            *values,
        )
        resolved_this_week = resolved_week_row["cnt"] if resolved_week_row else 0

        # By-type counts
        type_rows = await connection.fetch(
            f"""SELECT v.task_type_code, d.name AS task_type_name, COUNT(*)::int AS cnt
                FROM {SCHEMA}."40_vw_task_detail" v
                LEFT JOIN {SCHEMA}."02_dim_task_types" d ON d.code = v.task_type_code
                WHERE {where}
                GROUP BY v.task_type_code, d.name
                ORDER BY cnt DESC""",
            *values,
        )

        return {
            "open_count": counts.get("open", 0),
            "in_progress_count": counts.get("in_progress", 0),
            "pending_verification_count": counts.get("pending_verification", 0),
            "resolved_count": counts.get("resolved", 0),
            "cancelled_count": counts.get("cancelled", 0),
            "overdue_count": overdue_count,
            "resolved_this_week_count": resolved_this_week,
            "by_type": [
                {"task_type_code": r["task_type_code"], "task_type_name": r["task_type_name"] or r["task_type_code"], "count": r["cnt"]}
                for r in type_rows
            ],
        }

    async def create_task(
        self,
        connection: asyncpg.Connection,
        *,
        task_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        task_type_code: str,
        priority_code: str,
        entity_type: str | None,
        entity_id: str | None,
        assignee_user_id: str | None,
        reporter_user_id: str,
        due_date: str | None,
        start_date: str | None,
        estimated_hours: float | None,
        created_by: str,
        now: object,
    ) -> TaskRecord:
        normalized_entity_type = str(entity_type or "").strip() or None
        normalized_entity_id = str(entity_id or "").strip() or None
        if normalized_entity_type is None:
            normalized_entity_id = None

        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."10_fct_tasks" (
                id, tenant_key, org_id, workspace_id, task_type_code, priority_code, status_code,
                entity_type, entity_id,
                assignee_user_id, reporter_user_id,
                due_date, start_date, completed_at,
                estimated_hours, actual_hours,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid, $5, $6, 'open',
                $7, $8::uuid,
                $9::uuid, $10::uuid,
                $11, $12, NULL,
                $13, NULL,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $14, $15, $16::uuid, $17::uuid, NULL, NULL
            )
            RETURNING id::text, tenant_key, org_id::text, workspace_id::text,
                      task_type_code, priority_code, status_code,
                      entity_type, entity_id::text,
                      assignee_user_id::text, reporter_user_id::text,
                      due_date::text, start_date::text, completed_at::text,
                      estimated_hours, actual_hours,
                      is_active, version, created_at::text, updated_at::text
            """,
            task_id, tenant_key, org_id, workspace_id,
            task_type_code, priority_code,
            normalized_entity_type, normalized_entity_id,
            assignee_user_id, reporter_user_id,
            _parse_dt(due_date), _parse_dt(start_date), estimated_hours,
            now, now, created_by, created_by,
        )
        return _row_to_task(row)

    async def update_task(
        self,
        connection: asyncpg.Connection,
        task_id: str,
        *,
        priority_code: str | None = None,
        status_code: str | None = None,
        assignee_user_id: str | None = None,
        due_date: str | None = None,
        start_date: str | None = None,
        estimated_hours: float | None = None,
        actual_hours: float | None = None,
        completed_at: object | None = None,
        updated_by: str,
        now: object,
    ) -> TaskRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2::uuid", "version = version + 1"]
        values: list[object] = [now, updated_by]
        idx = 3

        if priority_code is not None:
            fields.append(f"priority_code = ${idx}"); values.append(priority_code); idx += 1
        if status_code is not None:
            fields.append(f"status_code = ${idx}"); values.append(status_code); idx += 1
        if assignee_user_id is not None:
            fields.append(f"assignee_user_id = ${idx}::uuid"); values.append(assignee_user_id); idx += 1
        if due_date is not None:
            fields.append(f"due_date = ${idx}"); values.append(_parse_dt(due_date)); idx += 1
        if start_date is not None:
            fields.append(f"start_date = ${idx}"); values.append(_parse_dt(start_date)); idx += 1
        if estimated_hours is not None:
            fields.append(f"estimated_hours = ${idx}"); values.append(estimated_hours); idx += 1
        if actual_hours is not None:
            fields.append(f"actual_hours = ${idx}"); values.append(actual_hours); idx += 1
        if completed_at is not None:
            fields.append(f"completed_at = ${idx}"); values.append(completed_at); idx += 1

        values.append(task_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."10_fct_tasks"
            SET {set_clause}
            WHERE id = ${idx}::uuid AND is_deleted = FALSE
            RETURNING id::text, tenant_key, org_id::text, workspace_id::text,
                      task_type_code, priority_code, status_code,
                      entity_type, entity_id::text,
                      assignee_user_id::text, reporter_user_id::text,
                      due_date::text, start_date::text, completed_at::text,
                      estimated_hours, actual_hours,
                      is_active, version, created_at::text, updated_at::text
            """,
            *values,
        )
        return _row_to_task(row) if row else None

    async def soft_delete_task(
        self,
        connection: asyncpg.Connection,
        task_id: str,
        *,
        deleted_by: str,
        now: object,
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_tasks"
            SET is_active = FALSE, is_deleted = TRUE,
                deleted_at = $1, deleted_by = $2::uuid,
                updated_at = $3, updated_by = $4::uuid
            WHERE id = $5::uuid AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, task_id,
        )
        return result != "UPDATE 0"

    async def set_task_property(
        self,
        connection: asyncpg.Connection,
        *,
        prop_id: str,
        task_id: str,
        property_key: str,
        property_value: str,
        actor_id: str,
        now: object,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_dtl_task_properties" (
                id, task_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8::uuid)
            ON CONFLICT (task_id, property_key)
            DO UPDATE SET
                property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            prop_id, task_id, property_key, property_value,
            now, now, actor_id, actor_id,
        )

    async def bulk_update_tasks(
        self,
        connection: asyncpg.Connection,
        *,
        task_ids: list[str],
        tenant_key: str,
        status_code: str | None,
        priority_code: str | None,
        assignee_user_id: str | None,
        updated_by: str,
        now: object,
    ) -> int:
        """Update multiple tasks at once. Returns actual updated count."""
        if not task_ids:
            return 0

        # Fixed positions: $1=now, $2=updated_by, $3=tenant_key
        values: list[object] = [now, updated_by, tenant_key]
        idx = 4
        set_parts: list[str] = ["updated_at = $1", "updated_by = $2::uuid"]

        if status_code is not None:
            set_parts.append(f"status_code = ${idx}"); values.append(status_code); idx += 1
        if priority_code is not None:
            set_parts.append(f"priority_code = ${idx}"); values.append(priority_code); idx += 1
        if assignee_user_id is not None:
            set_parts.append(f"assignee_user_id = ${idx}::uuid"); values.append(assignee_user_id); idx += 1

        if len(set_parts) == 2:
            return 0  # Nothing to update

        id_placeholders = ", ".join(f"${idx + i}::uuid" for i in range(len(task_ids)))
        values.extend(task_ids)
        set_clause = ", ".join(set_parts)

        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."10_fct_tasks"
            SET {set_clause}
            WHERE tenant_key = $3
              AND id IN ({id_placeholders})
              AND is_deleted = FALSE
            """,
            *values,
        )
        try:
            return int(result.split()[-1])
        except (ValueError, IndexError):
            return 0

    async def is_terminal_status(
        self, connection: asyncpg.Connection, status_code: str
    ) -> bool:
        row = await connection.fetchrow(
            f'SELECT is_terminal FROM {SCHEMA}."04_dim_task_statuses" WHERE code = $1',
            status_code,
        )
        return row["is_terminal"] if row else False


def _row_to_task(r) -> TaskRecord:
    return TaskRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        task_type_code=r["task_type_code"],
        priority_code=r["priority_code"],
        status_code=r["status_code"],
        entity_type=r["entity_type"],
        entity_id=r["entity_id"],
        assignee_user_id=r["assignee_user_id"],
        reporter_user_id=r["reporter_user_id"],
        due_date=r["due_date"],
        start_date=r["start_date"],
        completed_at=r["completed_at"],
        estimated_hours=r["estimated_hours"],
        actual_hours=r["actual_hours"],
        is_active=r["is_active"],
        version=r["version"] if "version" in r.keys() else 1,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_task_detail(r) -> TaskDetailRecord:
    return TaskDetailRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        task_type_code=r["task_type_code"],
        task_type_name=r["task_type_name"],
        priority_code=r["priority_code"],
        priority_name=r["priority_name"],
        status_code=r["status_code"],
        status_name=r["status_name"],
        is_terminal=r["is_terminal"],
        entity_type=r["entity_type"],
        entity_id=r["entity_id"],
        assignee_user_id=r["assignee_user_id"],
        reporter_user_id=r["reporter_user_id"],
        due_date=r["due_date"],
        start_date=r["start_date"],
        completed_at=r["completed_at"],
        estimated_hours=r["estimated_hours"],
        actual_hours=r["actual_hours"],
        is_active=r["is_active"],
        version=1,
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        title=r["title"],
        description=r["description"],
        acceptance_criteria=r["acceptance_criteria"],
        resolution_notes=r["resolution_notes"],
        remediation_plan=r["remediation_plan"],
        co_assignee_count=r["co_assignee_count"],
        blocker_count=r["blocker_count"],
        comment_count=r["comment_count"],
    )
