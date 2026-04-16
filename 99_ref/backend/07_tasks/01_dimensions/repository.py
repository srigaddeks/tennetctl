from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TaskPriorityRecord, TaskStatusRecord, TaskTypeRecord

SCHEMA = '"08_tasks"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="tasks.dimensions.repository", logger_name="backend.tasks.dimensions.repository.instrumentation")
class DimensionRepository:
    async def list_task_types(self, connection: asyncpg.Connection) -> list[TaskTypeRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, sort_order FROM {SCHEMA}."02_dim_task_types" WHERE is_active = TRUE ORDER BY sort_order'
        )
        return [TaskTypeRecord(code=r["code"], name=r["name"], description=r["description"], sort_order=r["sort_order"]) for r in rows]

    async def list_task_priorities(self, connection: asyncpg.Connection) -> list[TaskPriorityRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, sort_order FROM {SCHEMA}."03_dim_task_priorities" WHERE is_active = TRUE ORDER BY sort_order'
        )
        return [TaskPriorityRecord(code=r["code"], name=r["name"], description=r["description"], sort_order=r["sort_order"]) for r in rows]

    async def list_task_statuses(self, connection: asyncpg.Connection) -> list[TaskStatusRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, is_terminal, sort_order FROM {SCHEMA}."04_dim_task_statuses" WHERE is_active = TRUE ORDER BY sort_order'
        )
        return [TaskStatusRecord(code=r["code"], name=r["name"], description=r["description"], is_terminal=r["is_terminal"], sort_order=r["sort_order"]) for r in rows]
