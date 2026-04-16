"""Business logic for the feedback & support ticket domain."""
from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TicketRepository
from .schemas import (
    AdminUpdateRequest,
    AssignTicketRequest,
    AssignmentResponse,
    CreateTicketRequest,
    TicketDimensionsResponse,
    TicketEventsResponse,
    TicketListResponse,
    TicketPriorityDimResponse,
    TicketResponse,
    TicketStatusDimResponse,
    TicketTypeDimResponse,
    UpdateTicketRequest,
    UpdateTicketStatusRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_time_module = import_module("backend.01_core.time_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_audit_module = import_module("backend.01_core.audit")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_constants_module = import_module("backend.10_feedback.constants")

instrument_class_methods = _telemetry_module.instrument_class_methods
get_logger = _logging_module.get_logger
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
AuditWriter = _audit_module.AuditWriter
AuditEntry = _audit_module.AuditEntry
AuditEventCategory = _auth_constants_module.AuditEventCategory
VALID_TRANSITIONS = _constants_module.VALID_TRANSITIONS
TERMINAL_STATUSES = _constants_module.TERMINAL_STATUSES
INTERNAL_PROPERTY_KEYS = _constants_module.INTERNAL_PROPERTY_KEYS
USER_PROPERTY_KEYS = _constants_module.USER_PROPERTY_KEYS
FeedbackAuditEventType = _constants_module.FeedbackAuditEventType


@instrument_class_methods(
    namespace="feedback.service",
    logger_name="backend.feedback.instrumentation",
)
class TicketService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TicketRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.feedback")

    # ── Cache helpers ─────────────────────────────────────────────────────────

    def _cache_key_user(self, tenant_key: str, user_id: str) -> str:
        return f"fb:tickets:{tenant_key}:{user_id}"

    def _cache_key_admin(self, tenant_key: str) -> str:
        return f"fb:tickets:admin:{tenant_key}"

    async def _invalidate_caches(self, tenant_key: str, user_id: str) -> None:
        await self._cache.delete(self._cache_key_user(tenant_key, user_id))
        await self._cache.delete(self._cache_key_admin(tenant_key))

    # ── Dimensions ─────────────────────────────────────────────────────────────

    async def list_dimensions(self) -> TicketDimensionsResponse:
        async with self._database_pool.acquire() as conn:
            types = await self._repository.list_ticket_types(conn)
            statuses = await self._repository.list_ticket_statuses(conn)
            priorities = await self._repository.list_ticket_priorities(conn)
        return TicketDimensionsResponse(
            ticket_types=[TicketTypeDimResponse(**t.__dict__) for t in types],
            ticket_statuses=[TicketStatusDimResponse(**s.__dict__) for s in statuses],
            ticket_priorities=[TicketPriorityDimResponse(**p.__dict__) for p in priorities],
        )

    # ── User-facing ticket operations ─────────────────────────────────────────

    async def list_my_tickets(
        self,
        *,
        user_id: str,
        tenant_key: str,
        status_code: str | None = None,
        ticket_type_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TicketListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.view")
            total = await self._repository.count_tickets(
                conn,
                tenant_key=tenant_key,
                submitted_by=user_id,
                status_code=status_code,
                ticket_type_code=ticket_type_code,
            )
            records = await self._repository.list_tickets(
                conn,
                tenant_key=tenant_key,
                submitted_by=user_id,
                status_code=status_code,
                ticket_type_code=ticket_type_code,
                limit=limit,
                offset=offset,
            )
        return TicketListResponse(
            items=[_to_ticket_response(r, include_internal=False) for r in records],
            total=total,
        )

    async def get_ticket(
        self,
        *,
        user_id: str,
        ticket_id: str,
        include_internal: bool = False,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
            if not raw:
                raise NotFoundError(f"Ticket {ticket_id} not found.")
            # Access control: own ticket (feedback.view) or admin (feedback.manage)
            if raw.submitted_by == user_id:
                await require_permission(conn, user_id, "feedback.view")
            else:
                await require_permission(conn, user_id, "feedback.manage")
                include_internal = True
            record = await self._repository.get_ticket_detail(conn, ticket_id)
        if not record:
            raise NotFoundError(f"Ticket {ticket_id} not found.")
        return _to_ticket_response(record, include_internal=include_internal)

    async def create_ticket(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateTicketRequest,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.create")
            if not await self._repository.ticket_type_exists(conn, request.ticket_type_code):
                raise ValidationError(f"Unknown ticket type: {request.ticket_type_code!r}")
            if not await self._repository.priority_exists(conn, request.priority_code):
                raise ValidationError(f"Unknown priority: {request.priority_code!r}")

        ticket_id = str(uuid.uuid4())
        now = utc_now_sql()

        # Collect non-None properties
        properties: dict[str, str] = {}
        field_map = {
            "title": request.title,
            "description": request.description,
            "context_url": request.context_url,
            "browser_info": request.browser_info,
            "steps_to_reproduce": request.steps_to_reproduce,
            "expected_behavior": request.expected_behavior,
            "actual_behavior": request.actual_behavior,
            "version_info": request.version_info,
        }
        for key, val in field_map.items():
            if val is not None:
                properties[key] = val

        async with self._database_pool.transaction() as conn:
            await self._repository.create_ticket(
                conn,
                ticket_id=ticket_id,
                tenant_key=tenant_key,
                submitted_by=user_id,
                ticket_type_code=request.ticket_type_code,
                status_code="open",
                priority_code=request.priority_code,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                now=now,
            )
            if properties:
                await self._repository.upsert_properties(
                    conn,
                    ticket_id=ticket_id,
                    properties=properties,
                    is_internal=False,
                    actor_id=user_id,
                    now=now,
                )
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=tenant_key,
                event_type=FeedbackAuditEventType.TICKET_CREATED,
                actor_id=user_id,
                old_value=None,
                new_value="open",
                note=None,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="feedback_ticket",
                    entity_id=ticket_id,
                    event_type="feedback_ticket_created",
                    event_category=AuditEventCategory.SYSTEM.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"ticket_type": request.ticket_type_code, "priority": request.priority_code},
                ),
            )

        await self._invalidate_caches(tenant_key, user_id)
        record = await self._get_ticket_detail_direct(ticket_id)
        return _to_ticket_response(record, include_internal=False)

    async def update_ticket(
        self,
        *,
        user_id: str,
        ticket_id: str,
        request: UpdateTicketRequest,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")

        # Only owner can update, and only when not terminal
        async with self._database_pool.acquire() as conn:
            if raw.submitted_by != user_id:
                await require_permission(conn, user_id, "feedback.manage")
            else:
                await require_permission(conn, user_id, "feedback.update")

        if raw.status_code in TERMINAL_STATUSES and raw.submitted_by == user_id:
            raise ValidationError("Cannot update a ticket in a terminal status.")

        now = utc_now_sql()
        updates: dict[str, str] = {}
        for key in ("title", "description", "context_url", "browser_info"):
            val = getattr(request, key, None)
            if val is not None:
                updates[key] = val

        async with self._database_pool.transaction() as conn:
            if updates:
                await self._repository.upsert_properties(
                    conn,
                    ticket_id=ticket_id,
                    properties=updates,
                    is_internal=False,
                    actor_id=user_id,
                    now=now,
                )
            if request.priority_code and request.priority_code != raw.priority_code:
                await self._repository.update_ticket_priority(
                    conn,
                    ticket_id,
                    priority_code=request.priority_code,
                    updated_by=user_id,
                    now=now,
                )
                await self._repository.write_event(
                    conn,
                    event_id=str(uuid.uuid4()),
                    ticket_id=ticket_id,
                    tenant_key=raw.tenant_key,
                    event_type=FeedbackAuditEventType.PRIORITY_CHANGED,
                    actor_id=user_id,
                    old_value=raw.priority_code,
                    new_value=request.priority_code,
                    note=None,
                    now=now,
                )
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=raw.tenant_key,
                event_type=FeedbackAuditEventType.TICKET_UPDATED,
                actor_id=user_id,
                old_value=None,
                new_value=None,
                note=None,
                now=now,
            )

        await self._invalidate_caches(raw.tenant_key, raw.submitted_by)
        record = await self._get_ticket_detail_direct(ticket_id)
        include_internal = raw.submitted_by != user_id
        return _to_ticket_response(record, include_internal=include_internal)

    async def delete_ticket(self, *, user_id: str, ticket_id: str) -> None:
        async with self._database_pool.acquire() as conn:
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")

        async with self._database_pool.acquire() as conn:
            if raw.submitted_by != user_id:
                await require_permission(conn, user_id, "feedback.manage")
            else:
                await require_permission(conn, user_id, "feedback.delete")
                if raw.status_code not in ("open", "in_review"):
                    raise ValidationError(
                        "You can only delete tickets in 'open' or 'in_review' status."
                    )

        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._repository.soft_delete_ticket(
                conn, ticket_id, deleted_by=user_id, now=now
            )
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=raw.tenant_key,
                event_type=FeedbackAuditEventType.TICKET_DELETED,
                actor_id=user_id,
                old_value=raw.status_code,
                new_value=None,
                note=None,
                now=now,
            )

        await self._invalidate_caches(raw.tenant_key, raw.submitted_by)

    # ── Admin ticket operations ───────────────────────────────────────────────

    async def list_all_tickets(
        self,
        *,
        user_id: str,
        tenant_key: str | None = None,
        status_code: str | None = None,
        ticket_type_code: str | None = None,
        priority_code: str | None = None,
        submitted_by_filter: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TicketListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.manage")
            total = await self._repository.count_tickets(
                conn,
                tenant_key=tenant_key,
                submitted_by=submitted_by_filter,
                status_code=status_code,
                ticket_type_code=ticket_type_code,
                priority_code=priority_code,
            )
            records = await self._repository.list_tickets(
                conn,
                tenant_key=tenant_key,
                submitted_by=submitted_by_filter,
                status_code=status_code,
                ticket_type_code=ticket_type_code,
                priority_code=priority_code,
                limit=limit,
                offset=offset,
            )
        return TicketListResponse(
            items=[_to_ticket_response(r, include_internal=True) for r in records],
            total=total,
        )

    async def change_status(
        self,
        *,
        user_id: str,
        ticket_id: str,
        request: UpdateTicketStatusRequest,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.manage")
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")

        allowed = VALID_TRANSITIONS.get(raw.status_code, frozenset())
        if request.status_code not in allowed:
            raise ValidationError(
                f"Cannot transition from {raw.status_code!r} to {request.status_code!r}. "
                f"Allowed: {sorted(allowed)}"
            )

        now = utc_now_sql()
        is_terminal = request.status_code in TERMINAL_STATUSES
        resolved_at = now if is_terminal and request.status_code == "resolved" else None
        resolved_by = user_id if resolved_at else None

        async with self._database_pool.transaction() as conn:
            await self._repository.update_ticket_status(
                conn,
                ticket_id,
                status_code=request.status_code,
                resolved_at=resolved_at,
                resolved_by=resolved_by,
                updated_by=user_id,
                now=now,
            )
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=raw.tenant_key,
                event_type=FeedbackAuditEventType.STATUS_CHANGED,
                actor_id=user_id,
                old_value=raw.status_code,
                new_value=request.status_code,
                note=request.note,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=raw.tenant_key,
                    entity_type="feedback_ticket",
                    entity_id=ticket_id,
                    event_type="feedback_ticket_status_changed",
                    event_category=AuditEventCategory.SYSTEM.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"old_status": raw.status_code, "new_status": request.status_code},
                ),
            )

        await self._invalidate_caches(raw.tenant_key, raw.submitted_by)
        record = await self._get_ticket_detail_direct(ticket_id)
        return _to_ticket_response(record, include_internal=True)

    async def assign_ticket(
        self,
        *,
        user_id: str,
        ticket_id: str,
        request: AssignTicketRequest,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.manage")
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")

        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._repository.create_assignment(
                conn,
                ticket_id=ticket_id,
                assigned_to=request.assigned_to,
                assigned_by=user_id,
                note=request.note,
                now=now,
            )
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=raw.tenant_key,
                event_type=FeedbackAuditEventType.TICKET_ASSIGNED,
                actor_id=user_id,
                old_value=None,
                new_value=request.assigned_to,
                note=request.note,
                now=now,
            )

        await self._invalidate_caches(raw.tenant_key, raw.submitted_by)
        record = await self._get_ticket_detail_direct(ticket_id)
        return _to_ticket_response(record, include_internal=True)

    async def unassign_ticket(
        self,
        *,
        user_id: str,
        ticket_id: str,
        assigned_to: str,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.manage")
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")

        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            removed = await self._repository.deactivate_assignment(
                conn,
                ticket_id=ticket_id,
                assigned_to=assigned_to,
                unassigned_by=user_id,
                now=now,
            )
            if not removed:
                raise NotFoundError(f"No active assignment for user {assigned_to} on ticket {ticket_id}.")
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=raw.tenant_key,
                event_type=FeedbackAuditEventType.TICKET_UNASSIGNED,
                actor_id=user_id,
                old_value=assigned_to,
                new_value=None,
                note=None,
                now=now,
            )

        await self._invalidate_caches(raw.tenant_key, raw.submitted_by)
        record = await self._get_ticket_detail_direct(ticket_id)
        return _to_ticket_response(record, include_internal=True)

    async def admin_update(
        self,
        *,
        user_id: str,
        ticket_id: str,
        request: AdminUpdateRequest,
    ) -> TicketResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "feedback.manage")
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")

        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            if request.status_code and request.status_code != raw.status_code:
                allowed = VALID_TRANSITIONS.get(raw.status_code, frozenset())
                if request.status_code not in allowed:
                    raise ValidationError(
                        f"Cannot transition from {raw.status_code!r} to {request.status_code!r}."
                    )
                is_terminal = request.status_code in TERMINAL_STATUSES
                resolved_at = now if is_terminal and request.status_code == "resolved" else None
                resolved_by = user_id if resolved_at else None
                await self._repository.update_ticket_status(
                    conn, ticket_id,
                    status_code=request.status_code,
                    resolved_at=resolved_at,
                    resolved_by=resolved_by,
                    updated_by=user_id,
                    now=now,
                )
                await self._repository.write_event(
                    conn,
                    event_id=str(uuid.uuid4()),
                    ticket_id=ticket_id,
                    tenant_key=raw.tenant_key,
                    event_type=FeedbackAuditEventType.STATUS_CHANGED,
                    actor_id=user_id,
                    old_value=raw.status_code,
                    new_value=request.status_code,
                    note=None,
                    now=now,
                )
            if request.priority_code and request.priority_code != raw.priority_code:
                await self._repository.update_ticket_priority(
                    conn, ticket_id,
                    priority_code=request.priority_code,
                    updated_by=user_id,
                    now=now,
                )
                await self._repository.write_event(
                    conn,
                    event_id=str(uuid.uuid4()),
                    ticket_id=ticket_id,
                    tenant_key=raw.tenant_key,
                    event_type=FeedbackAuditEventType.PRIORITY_CHANGED,
                    actor_id=user_id,
                    old_value=raw.priority_code,
                    new_value=request.priority_code,
                    note=None,
                    now=now,
                )
            if request.admin_note is not None:
                await self._repository.upsert_properties(
                    conn,
                    ticket_id=ticket_id,
                    properties={"admin_note": request.admin_note},
                    is_internal=True,
                    actor_id=user_id,
                    now=now,
                )
            await self._repository.write_event(
                conn,
                event_id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                tenant_key=raw.tenant_key,
                event_type=FeedbackAuditEventType.TICKET_UPDATED,
                actor_id=user_id,
                old_value=None,
                new_value=None,
                note="Admin update",
                now=now,
            )

        await self._invalidate_caches(raw.tenant_key, raw.submitted_by)
        record = await self._get_ticket_detail_direct(ticket_id)
        return _to_ticket_response(record, include_internal=True)

    async def list_events(
        self,
        *,
        user_id: str,
        ticket_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> TicketEventsResponse:
        async with self._database_pool.acquire() as conn:
            raw = await self._repository.get_ticket_raw(conn, ticket_id)
        if not raw:
            raise NotFoundError(f"Ticket {ticket_id} not found.")
        async with self._database_pool.acquire() as conn:
            if raw.submitted_by == user_id:
                await require_permission(conn, user_id, "feedback.view")
            else:
                await require_permission(conn, user_id, "feedback.manage")
            events, total = await self._repository.list_events(
                conn, ticket_id, limit=limit, offset=offset
            )
        return TicketEventsResponse(
            items=[_event_to_response(e) for e in events],
            total=total,
        )

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get_ticket_detail_direct(self, ticket_id: str):
        async with self._database_pool.acquire() as conn:
            return await self._repository.get_ticket_detail(conn, ticket_id)


# ── Response mappers ──────────────────────────────────────────────────────────

def _to_ticket_response(record, *, include_internal: bool) -> TicketResponse:
    if record is None:
        raise ValueError("Cannot convert None record to TicketResponse")
    assignments = [
        AssignmentResponse(
            assigned_to=a["assigned_to"],
            assigned_by=a["assigned_by"],
            assigned_at=a["assigned_at"],
        )
        for a in record.active_assignments
    ]
    return TicketResponse(
        id=record.id,
        tenant_key=record.tenant_key,
        submitted_by=record.submitted_by,
        ticket_type_code=record.ticket_type_code,
        status_code=record.status_code,
        priority_code=record.priority_code,
        org_id=record.org_id,
        workspace_id=record.workspace_id,
        title=record.title,
        description=record.description,
        context_url=record.context_url,
        browser_info=record.browser_info,
        steps_to_reproduce=record.steps_to_reproduce,
        expected_behavior=record.expected_behavior,
        actual_behavior=record.actual_behavior,
        version_info=record.version_info,
        admin_note=record.admin_note if include_internal else None,
        submitter_email=record.submitter_email,
        submitter_display_name=record.submitter_display_name,
        active_assignments=assignments,
        created_at=record.created_at,
        updated_at=record.updated_at,
        resolved_at=record.resolved_at,
    )


def _event_to_response(e) -> "TicketEventResponse":
    from .schemas import TicketEventResponse
    return TicketEventResponse(
        id=e.id,
        ticket_id=e.ticket_id,
        event_type=e.event_type,
        actor_id=e.actor_id,
        occurred_at=e.occurred_at,
        old_value=e.old_value,
        new_value=e.new_value,
        note=e.note,
    )
