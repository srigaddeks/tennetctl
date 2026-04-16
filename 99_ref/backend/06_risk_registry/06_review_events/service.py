from __future__ import annotations

import uuid
from importlib import import_module

from .repository import ReviewEventRepository
from .schemas import CreateReviewEventRequest, ReviewEventResponse

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.06_risk_registry.constants")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_risk_repo_module = import_module("backend.06_risk_registry.02_risks.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
RiskAuditEventType = _constants_module.RiskAuditEventType
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
RiskRepository = _risk_repo_module.RiskRepository


@instrument_class_methods(namespace="risk.review_events.service", logger_name="backend.risk.review_events.instrumentation")
class ReviewEventService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ReviewEventRepository()
        self._risk_repository = RiskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.risk.review_events")

    async def list_review_events(
        self, *, user_id: str, risk_id: str
    ) -> list[ReviewEventResponse]:
        async with self._database_pool.acquire() as conn:
            risk = await self._risk_repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await require_permission(
                conn,
                user_id,
                "risks.view",
                scope_org_id=risk.org_id,
                scope_workspace_id=risk.workspace_id,
            )
            records = await self._repository.list_review_events(conn, risk_id)
        return [_event_response(r) for r in records]

    async def create_review_event(
        self, *, user_id: str, risk_id: str, request: CreateReviewEventRequest
    ) -> ReviewEventResponse:
        now = utc_now_sql()
        event_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            risk = await self._risk_repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await require_permission(
                conn,
                user_id,
                "risks.update",
                scope_org_id=risk.org_id,
                scope_workspace_id=risk.workspace_id,
            )

            event = await self._repository.create_review_event(
                conn,
                event_id=event_id,
                risk_id=risk_id,
                event_type=request.event_type,
                old_status=None,
                new_status=None,
                actor_id=user_id,
                comment=request.comment,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.REVIEW_EVENT_CREATED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "review_event_id": event_id,
                        "review_event_type": request.event_type,
                    },
                ),
            )

        return _event_response(event)


def _event_response(r) -> ReviewEventResponse:
    return ReviewEventResponse(
        id=r.id,
        risk_id=r.risk_id,
        event_type=r.event_type,
        old_status=r.old_status,
        new_status=r.new_status,
        actor_id=r.actor_id,
        comment=r.comment,
        occurred_at=r.occurred_at,
    )
