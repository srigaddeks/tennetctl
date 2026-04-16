from __future__ import annotations

import uuid
from importlib import import_module

from .repository import EventRepository
from .schemas import AddCommentRequest, TaskEventListResponse, TaskEventResponse

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.07_tasks.constants")
_auth_constants_module = import_module("backend.03_auth_manage.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
TaskAuditEventType = _constants_module.TaskAuditEventType
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_task_repo_module = import_module("backend.07_tasks.02_tasks.repository")
TaskRepository = _task_repo_module.TaskRepository


@instrument_class_methods(namespace="tasks.events.service", logger_name="backend.tasks.events.instrumentation")
class EventService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = EventRepository()
        self._task_repository = TaskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.tasks.events")

    async def _require_task_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        task,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=task.org_id,
            scope_workspace_id=task.workspace_id,
        )

    async def list_events(self, *, user_id: str, task_id: str) -> TaskEventListResponse:
        async with self._database_pool.acquire() as conn:
            task = await self._task_repository.get_task_by_id(conn, task_id)
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.view",
                task=task,
            )

        async with self._database_pool.acquire() as conn:
            events = await self._repository.list_events(conn, task_id)
        items = [_event_response(e) for e in events]
        return TaskEventListResponse(items=items, total=len(items))

    async def add_comment(
        self, *, user_id: str, task_id: str, request: AddCommentRequest
    ) -> TaskEventResponse:
        now = utc_now_sql()
        event_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            task = await self._task_repository.get_task_detail(conn, task_id)
            if task is None:
                raise NotFoundError(f"Task '{task_id}' not found")
            await self._require_task_permission(
                conn,
                user_id=user_id,
                permission_code="tasks.update",
                task=task,
            )
            event = await self._repository.create_event(
                conn,
                event_id=event_id,
                task_id=task_id,
                event_type="comment_added",
                old_value=None,
                new_value=None,
                comment=request.comment,
                actor_id=user_id,
                now=now,
            )
            # Build task URL
            _base_url = (
                getattr(self._settings, "notification_tracking_base_url", "") or
                getattr(self._settings, "platform_base_url", "") or ""
            ).rstrip("/")
            _task_url = f"{_base_url}/tasks/{task_id}" if _base_url else f"/tasks/{task_id}"
            audit_entry = AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=task.tenant_key,
                entity_type="task",
                entity_id=task_id,
                event_type=TaskAuditEventType.TASK_COMMENT_ADDED.value,
                event_category=AuditEventCategory.TASK.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                properties={
                    "event_id": event_id,
                    "task.title": task.title or "",
                    "task.url": _task_url,
                    "comment.body": (request.comment or "")[:300],
                },
            )
            await self._audit_writer.write_entry(conn, audit_entry)

        # Invalidate task detail cache (comment_count changed)
        await self._cache.delete(f"task:{task_id}")

        # Notify task participants (fire and forget, best-effort)
        if self._settings.notification_enabled:
            import asyncio as _asyncio
            _dispatcher_module = import_module(
                "backend.04_notifications.02_dispatcher.dispatcher"
            )
            NotificationDispatcher = _dispatcher_module.NotificationDispatcher
            dispatcher = NotificationDispatcher(
                database_pool=self._database_pool,
                settings=self._settings,
            )
            # Notify assignee and reporter, skip the commenter themselves
            _recipients = {task.assignee_user_id, task.reporter_user_id} - {user_id, None}
            for _recipient_id in _recipients:
                _asyncio.create_task(
                    dispatcher.dispatch_direct(
                        audit_entry,
                        target_user_id=_recipient_id,
                        template_code="task_comment_added_email",
                        notification_type_code="task_comment_added",
                    )
                )

        return _event_response(event)


def _event_response(e) -> TaskEventResponse:
    return TaskEventResponse(
        id=e.id,
        task_id=e.task_id,
        event_type=e.event_type,
        old_value=e.old_value,
        new_value=e.new_value,
        comment=e.comment,
        actor_id=e.actor_id,
        occurred_at=e.occurred_at,
    )
