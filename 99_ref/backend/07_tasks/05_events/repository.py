from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TaskEventRecord

SCHEMA = '"08_tasks"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="tasks.events.repository", logger_name="backend.tasks.events.repository.instrumentation")
class EventRepository:
    async def list_events(
        self, connection: asyncpg.Connection, task_id: str
    ) -> list[TaskEventRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id::text, task_id::text, event_type,
                   old_value, new_value, comment,
                   actor_id::text, occurred_at::text
            FROM {SCHEMA}."30_trx_task_events"
            WHERE task_id = $1::uuid
            ORDER BY occurred_at DESC
            """,
            task_id,
        )
        return [_row_to_event(r) for r in rows]

    async def create_event(
        self,
        connection: asyncpg.Connection,
        *,
        event_id: str,
        task_id: str,
        event_type: str,
        old_value: str | None,
        new_value: str | None,
        comment: str | None,
        actor_id: str,
        now: object,
    ) -> TaskEventRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."30_trx_task_events" (
                id, task_id, event_type, old_value, new_value, comment,
                actor_id, occurred_at
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8)
            RETURNING id::text, task_id::text, event_type,
                      old_value, new_value, comment,
                      actor_id::text, occurred_at::text
            """,
            event_id,
            task_id,
            event_type,
            old_value,
            new_value,
            comment,
            actor_id,
            now,
        )
        return _row_to_event(row)


def _row_to_event(r) -> TaskEventRecord:
    return TaskEventRecord(
        id=r["id"],
        task_id=r["task_id"],
        event_type=r["event_type"],
        old_value=r["old_value"],
        new_value=r["new_value"],
        comment=r["comment"],
        actor_id=r["actor_id"],
        occurred_at=r["occurred_at"],
    )
