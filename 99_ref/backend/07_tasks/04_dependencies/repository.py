from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TaskDependencyRecord

SCHEMA = '"08_tasks"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="tasks.dependencies.repository", logger_name="backend.tasks.dependencies.repository.instrumentation")
class DependencyRepository:
    async def list_blockers(
        self, connection: asyncpg.Connection, task_id: str
    ) -> list[TaskDependencyRecord]:
        """Tasks that block the given task (must be resolved first)."""
        rows = await connection.fetch(
            f"""
            SELECT id::text, blocking_task_id::text, blocked_task_id::text,
                   created_at::text, created_by::text
            FROM {SCHEMA}."32_lnk_task_dependencies"
            WHERE blocked_task_id = $1::uuid
            ORDER BY created_at
            """,
            task_id,
        )
        return [_row_to_dependency(r) for r in rows]

    async def list_blocked_by(
        self, connection: asyncpg.Connection, task_id: str
    ) -> list[TaskDependencyRecord]:
        """Tasks that are blocked by the given task."""
        rows = await connection.fetch(
            f"""
            SELECT id::text, blocking_task_id::text, blocked_task_id::text,
                   created_at::text, created_by::text
            FROM {SCHEMA}."32_lnk_task_dependencies"
            WHERE blocking_task_id = $1::uuid
            ORDER BY created_at
            """,
            task_id,
        )
        return [_row_to_dependency(r) for r in rows]

    async def add_dependency(
        self,
        connection: asyncpg.Connection,
        *,
        dependency_id: str,
        blocking_task_id: str,
        blocked_task_id: str,
        created_by: str,
        now: object,
    ) -> TaskDependencyRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."32_lnk_task_dependencies" (
                id, blocking_task_id, blocked_task_id, created_at, created_by
            )
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5::uuid)
            RETURNING id::text, blocking_task_id::text, blocked_task_id::text,
                      created_at::text, created_by::text
            """,
            dependency_id,
            blocking_task_id,
            blocked_task_id,
            now,
            created_by,
        )
        return _row_to_dependency(row)

    async def remove_dependency(
        self,
        connection: asyncpg.Connection,
        *,
        dependency_id: str,
        task_id: str,
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."32_lnk_task_dependencies"
            WHERE id = $1::uuid
              AND (blocking_task_id = $2::uuid OR blocked_task_id = $2::uuid)
            """,
            dependency_id,
            task_id,
        )
        return result != "DELETE 0"

    async def would_create_cycle(
        self,
        connection: asyncpg.Connection,
        *,
        blocking_task_id: str,
        blocked_task_id: str,
    ) -> bool:
        """
        Check if adding blocking_task_id -> blocked_task_id would create a cycle.

        Uses a recursive CTE to traverse from blocking_task_id upward through
        existing dependencies. If we can reach blocked_task_id, adding this
        edge would create a cycle.
        """
        row = await connection.fetchrow(
            f"""
            WITH RECURSIVE dep_chain(task_id) AS (
                -- Start from what blocks the blocking task
                SELECT blocked_task_id AS task_id
                FROM {SCHEMA}."32_lnk_task_dependencies"
                WHERE blocking_task_id = $2::uuid
                UNION
                -- Follow the chain: for each task in the chain,
                -- find tasks that it blocks
                SELECT d.blocked_task_id
                FROM {SCHEMA}."32_lnk_task_dependencies" d
                JOIN dep_chain c ON c.task_id = d.blocking_task_id
            )
            SELECT 1 FROM dep_chain WHERE task_id = $1::uuid
            LIMIT 1
            """,
            blocking_task_id,
            blocked_task_id,
        )
        return row is not None


def _row_to_dependency(r) -> TaskDependencyRecord:
    return TaskDependencyRecord(
        id=r["id"],
        blocking_task_id=r["blocking_task_id"],
        blocked_task_id=r["blocked_task_id"],
        created_at=r["created_at"],
        created_by=r["created_by"],
    )
