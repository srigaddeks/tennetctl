from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TaskAssignmentRecord

SCHEMA = '"08_tasks"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="tasks.assignments.repository", logger_name="backend.tasks.assignments.repository.instrumentation")
class AssignmentRepository:
    async def list_assignments(
        self, connection: asyncpg.Connection, task_id: str
    ) -> list[TaskAssignmentRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, task_id::text, user_id::text, role,
                   assigned_at::text, assigned_by::text
            FROM {SCHEMA}."31_lnk_task_assignments"
            WHERE task_id = $1::uuid
              AND is_deleted = FALSE
            ORDER BY assigned_at
            """,
            task_id,
        )
        return [_row_to_assignment(r) for r in rows]

    async def add_assignment(
        self,
        connection: asyncpg.Connection,
        *,
        assignment_id: str,
        task_id: str,
        user_id: str,
        role: str,
        assigned_by: str,
        now: object,
    ) -> TaskAssignmentRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."31_lnk_task_assignments" (
                id, task_id, user_id, role, is_deleted, assigned_at, assigned_by
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, FALSE, $5, $6::uuid)
            ON CONFLICT (task_id, user_id)
            DO UPDATE SET
                is_deleted = FALSE,
                role = EXCLUDED.role,
                assigned_at = EXCLUDED.assigned_at,
                assigned_by = EXCLUDED.assigned_by
            RETURNING id::text, task_id::text, user_id::text, role,
                      assigned_at::text, assigned_by::text
            """,
            assignment_id,
            task_id,
            user_id,
            role,
            now,
            assigned_by,
        )
        return _row_to_assignment(row)

    async def remove_assignment(
        self,
        connection: asyncpg.Connection,
        *,
        assignment_id: str,
        task_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."31_lnk_task_assignments"
            WHERE id = $1::uuid AND task_id = $2::uuid
            """,
            assignment_id,
            task_id,
        )
        return result != "DELETE 0"


def _row_to_assignment(r) -> TaskAssignmentRecord:
    return TaskAssignmentRecord(
        id=r["id"],
        task_id=r["task_id"],
        user_id=r["user_id"],
        role=r["role"],
        assigned_at=r["assigned_at"],
        assigned_by=r["assigned_by"],
    )
