"""
Internal helper for auto-creating tasks from other domains (risks, test mappings).
Bypasses permission checks — caller is responsible for using within a trusted context.
"""
from __future__ import annotations

import uuid
from importlib import import_module

_time_module = import_module("backend.01_core.time_utils")
_tasks_repo_module = import_module("backend.07_tasks.02_tasks.repository")
_events_repo_module = import_module("backend.07_tasks.05_events.repository")

TaskRepository = _tasks_repo_module.TaskRepository
EventRepository = _events_repo_module.EventRepository
utc_now_sql = _time_module.utc_now_sql

_task_repo = TaskRepository()
_event_repo = EventRepository()


async def auto_create_task(
    connection,
    *,
    tenant_key: str,
    org_id: str,
    workspace_id: str,
    task_type_code: str,
    priority_code: str,
    title: str,
    description: str | None = None,
    entity_type: str | None = None,
    entity_id: str | None = None,
    reporter_user_id: str,
) -> str:
    """
    Create a task without a permission check (for system-generated tasks).
    Returns the new task_id.
    """
    now = utc_now_sql()
    task_id = str(uuid.uuid4())

    await _task_repo.create_task(
        connection,
        task_id=task_id,
        tenant_key=tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        task_type_code=task_type_code,
        priority_code=priority_code,
        entity_type=entity_type,
        entity_id=entity_id,
        assignee_user_id=None,
        reporter_user_id=reporter_user_id,
        due_date=None,
        start_date=None,
        estimated_hours=None,
        created_by=reporter_user_id,
        now=now,
    )
    await _task_repo.set_task_property(
        connection,
        prop_id=str(uuid.uuid4()),
        task_id=task_id,
        property_key="title",
        property_value=title,
        actor_id=reporter_user_id,
        now=now,
    )
    if description:
        await _task_repo.set_task_property(
            connection,
            prop_id=str(uuid.uuid4()),
            task_id=task_id,
            property_key="description",
            property_value=description,
            actor_id=reporter_user_id,
            now=now,
        )
    await _event_repo.create_event(
        connection,
        event_id=str(uuid.uuid4()),
        task_id=task_id,
        event_type="created",
        old_value=None,
        new_value=None,
        comment="Auto-created by system",
        actor_id=reporter_user_id,
        now=now,
    )
    return task_id
