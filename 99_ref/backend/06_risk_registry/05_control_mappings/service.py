from __future__ import annotations

import uuid
from importlib import import_module

from .repository import ControlMappingRepository
from .schemas import (
    ApproveControlMappingRequest,
    AssignRiskToControlRequest,
    BulkApproveRequest,
    BulkRejectRequest,
    ControlMappingResponse,
    CreateControlMappingRequest,
    PendingMappingsResponse,
    RejectControlMappingRequest,
)

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
ForbiddenError = _errors_module.ForbiddenError if hasattr(_errors_module, "ForbiddenError") else _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
RiskAuditEventType = _constants_module.RiskAuditEventType
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
RiskRepository = _risk_repo_module.RiskRepository


@instrument_class_methods(namespace="risk.control_mappings.service", logger_name="backend.risk.control_mappings.instrumentation")
class ControlMappingService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ControlMappingRepository()
        self._risk_repository = RiskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.risk.control_mappings")

    async def list_control_mappings(
        self, *, user_id: str, risk_id: str
    ) -> list[ControlMappingResponse]:
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
            records = await self._repository.list_control_mappings(conn, risk_id)
        return [_mapping_response(r) for r in records]

    async def list_risks_for_control(
        self, *, user_id: str, control_id: str, org_id: str
    ) -> list[ControlMappingResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "risks.view",
                scope_org_id=org_id,
            )
            records = await self._repository.list_risks_for_control(conn, control_id)
        return [_mapping_response(r) for r in records]

    async def assign_risk_to_control(
        self, *, user_id: str, control_id: str, org_id: str, request: AssignRiskToControlRequest
    ) -> ControlMappingResponse:
        now = utc_now_sql()
        mapping_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "risks.update",
                scope_org_id=org_id,
            )
            record = await self._repository.create_control_mapping(
                conn,
                mapping_id=mapping_id,
                risk_id=request.risk_id,
                control_id=control_id,
                link_type=request.link_type,
                notes=request.notes,
                created_by=user_id,
                now=now,
                approval_status="approved",
            )
        return _mapping_response(record)

    async def list_pending_mappings(
        self,
        *,
        user_id: str,
        org_id: str,
        workspace_id: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> PendingMappingsResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "risks.view",
                scope_org_id=org_id,
            )
            records, total = await self._repository.list_pending_mappings(
                conn,
                org_id=org_id,
                workspace_id=workspace_id,
                limit=limit,
                offset=offset,
            )
        return PendingMappingsResponse(
            items=[_mapping_response(r) for r in records],
            total=total,
        )

    async def create_control_mapping(
        self, *, user_id: str, risk_id: str, request: CreateControlMappingRequest
    ) -> ControlMappingResponse:
        now = utc_now_sql()
        mapping_id = str(uuid.uuid4())
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

            mapping = await self._repository.create_control_mapping(
                conn,
                mapping_id=mapping_id,
                risk_id=risk_id,
                control_id=request.control_id,
                link_type=request.link_type,
                notes=request.notes,
                created_by=user_id,
                now=now,
                approval_status="approved",  # manual links are auto-approved
            )

            _review_repo_module = import_module("backend.06_risk_registry.06_review_events.repository")
            review_repo = _review_repo_module.ReviewEventRepository()
            await review_repo.create_review_event(
                conn,
                event_id=str(uuid.uuid4()),
                risk_id=risk_id,
                event_type="control_linked",
                old_status=None,
                new_status=None,
                actor_id=user_id,
                comment=f"Control {request.control_id} linked as {request.link_type}",
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.CONTROL_LINKED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "mapping_id": mapping_id,
                        "control_id": request.control_id,
                        "link_type": request.link_type,
                    },
                ),
            )

        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")
        return _mapping_response(mapping)

    async def approve_control_mapping(
        self,
        *,
        user_id: str,
        risk_id: str,
        mapping_id: str,
        request: ApproveControlMappingRequest,
    ) -> ControlMappingResponse:
        now = utc_now_sql()
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

            mapping = await self._repository.approve_mapping(
                conn,
                mapping_id=mapping_id,
                approved_by=user_id,
                now=now,
                notes=request.notes,
            )
            if mapping is None:
                raise NotFoundError(f"Pending mapping '{mapping_id}' not found")

            _review_repo_module = import_module("backend.06_risk_registry.06_review_events.repository")
            review_repo = _review_repo_module.ReviewEventRepository()
            await review_repo.create_review_event(
                conn,
                event_id=str(uuid.uuid4()),
                risk_id=risk_id,
                event_type="control_linked",
                old_status=None,
                new_status=None,
                actor_id=user_id,
                comment=f"AI-proposed control mapping approved",
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.CONTROL_LINKED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"mapping_id": mapping_id, "action": "approved"},
                ),
            )

        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")
        return _mapping_response(mapping)

    async def reject_control_mapping(
        self,
        *,
        user_id: str,
        risk_id: str,
        mapping_id: str,
        request: RejectControlMappingRequest,
    ) -> None:
        now = utc_now_sql()
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

            removed = await self._repository.reject_mapping(
                conn,
                mapping_id=mapping_id,
                rejected_by=user_id,
                now=now,
                rejection_reason=request.rejection_reason,
            )
            if not removed:
                raise NotFoundError(f"Pending mapping '{mapping_id}' not found")

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.CONTROL_UNLINKED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"mapping_id": mapping_id, "action": "rejected"},
                ),
            )

    async def bulk_approve(
        self, *, user_id: str, org_id: str, request: BulkApproveRequest
    ) -> dict:
        now = utc_now_sql()
        approved = 0
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "risks.update", scope_org_id=org_id)
            for mapping_id in request.mapping_ids:
                result = await self._repository.approve_mapping(
                    conn,
                    mapping_id=mapping_id,
                    approved_by=user_id,
                    now=now,
                )
                if result:
                    approved += 1
        await self._cache.delete_pattern("risks:list:*")
        return {"approved": approved}

    async def bulk_reject(
        self, *, user_id: str, org_id: str, request: BulkRejectRequest
    ) -> dict:
        now = utc_now_sql()
        rejected = 0
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "risks.update", scope_org_id=org_id)
            for mapping_id in request.mapping_ids:
                ok = await self._repository.reject_mapping(
                    conn,
                    mapping_id=mapping_id,
                    rejected_by=user_id,
                    now=now,
                    rejection_reason=request.rejection_reason,
                )
                if ok:
                    rejected += 1
        return {"rejected": rejected}

    async def delete_control_mapping(
        self, *, user_id: str, risk_id: str, mapping_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            mapping = await self._repository.get_control_mapping_by_id(conn, mapping_id)
            if mapping is None:
                raise NotFoundError(f"Control mapping '{mapping_id}' not found")

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

            removed = await self._repository.delete_control_mapping(conn, mapping_id)
            if not removed:
                raise NotFoundError(f"Control mapping '{mapping_id}' not found")

            _review_repo_module = import_module("backend.06_risk_registry.06_review_events.repository")
            review_repo = _review_repo_module.ReviewEventRepository()
            await review_repo.create_review_event(
                conn,
                event_id=str(uuid.uuid4()),
                risk_id=risk_id,
                event_type="control_unlinked",
                old_status=None,
                new_status=None,
                actor_id=user_id,
                comment=f"Control {mapping.control_id} unlinked",
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.CONTROL_UNLINKED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "mapping_id": mapping_id,
                        "control_id": mapping.control_id,
                    },
                ),
            )

        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")


def _mapping_response(r) -> ControlMappingResponse:
    return ControlMappingResponse(
        id=r.id,
        risk_id=r.risk_id,
        control_id=r.control_id,
        link_type=r.link_type,
        notes=r.notes,
        created_at=r.created_at,
        created_by=r.created_by,
        approval_status=r.approval_status,
        approved_by=r.approved_by,
        approved_at=r.approved_at,
        rejection_reason=r.rejection_reason,
        ai_confidence=r.ai_confidence,
        ai_rationale=r.ai_rationale,
        control_code=r.control_code,
        control_name=r.control_name,
        risk_code=r.risk_code,
        risk_title=r.risk_title,
    )
