from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TreatmentPlanRepository
from .schemas import (
    CreateTreatmentPlanRequest,
    TreatmentPlanResponse,
    UpdateTreatmentPlanRequest,
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
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
RiskAuditEventType = _constants_module.RiskAuditEventType
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
RiskRepository = _risk_repo_module.RiskRepository


@instrument_class_methods(namespace="risk.treatment_plans.service", logger_name="backend.risk.treatment_plans.instrumentation")
class TreatmentPlanService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TreatmentPlanRepository()
        self._risk_repository = RiskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.risk.treatment_plans")

    async def get_treatment_plan(
        self, *, user_id: str, risk_id: str
    ) -> TreatmentPlanResponse | None:
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
            plan = await self._repository.get_treatment_plan(conn, risk_id)
        if plan is None:
            return None
        async with self._database_pool.acquire() as conn:
            props = await self._repository.list_treatment_plan_properties(conn, plan.id)
        return _plan_response(plan, props)

    async def create_treatment_plan(
        self, *, user_id: str, risk_id: str, request: CreateTreatmentPlanRequest
    ) -> TreatmentPlanResponse:
        now = utc_now_sql()
        plan_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            risk = await self._risk_repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await require_permission(
                conn,
                user_id,
                "risks.create",
                scope_org_id=risk.org_id,
                scope_workspace_id=risk.workspace_id,
            )

            # Check no existing plan
            existing = await self._repository.get_treatment_plan(conn, risk_id)
            if existing is not None:
                raise ConflictError(f"Treatment plan already exists for risk '{risk_id}'")

            plan = await self._repository.create_treatment_plan(
                conn,
                plan_id=plan_id,
                risk_id=risk_id,
                tenant_key=risk.tenant_key,
                plan_status=request.plan_status,
                target_date=request.target_date,
                created_by=user_id,
                now=now,
            )

            # Write EAV properties
            eav_pairs = _collect_eav_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_treatment_plan_property(
                    conn,
                    prop_id=str(uuid.uuid4()),
                    treatment_plan_id=plan_id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )

            # Create review event
            _review_repo_module = import_module("backend.06_risk_registry.06_review_events.repository")
            review_repo = _review_repo_module.ReviewEventRepository()
            await review_repo.create_review_event(
                conn,
                event_id=str(uuid.uuid4()),
                risk_id=risk_id,
                event_type="treatment_updated",
                old_status=None,
                new_status=request.plan_status,
                actor_id=user_id,
                comment="Treatment plan created",
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.TREATMENT_PLAN_CREATED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "treatment_plan_id": plan_id,
                        "plan_status": request.plan_status,
                    },
                ),
            )

        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")
        props = _collect_eav_properties(request)
        return _plan_response(plan, props)

    async def update_treatment_plan(
        self, *, user_id: str, risk_id: str, request: UpdateTreatmentPlanRequest
    ) -> TreatmentPlanResponse:
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

            existing = await self._repository.get_treatment_plan(conn, risk_id)
            if existing is None:
                raise NotFoundError(f"Treatment plan for risk '{risk_id}' not found")

            plan = await self._repository.update_treatment_plan(
                conn,
                risk_id,
                plan_status=request.plan_status,
                target_date=request.target_date,
                updated_by=user_id,
                now=now,
            )
            if plan is None:
                raise NotFoundError(f"Treatment plan for risk '{risk_id}' not found")

            # Write EAV properties
            eav_pairs = _collect_eav_update_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_treatment_plan_property(
                    conn,
                    prop_id=str(uuid.uuid4()),
                    treatment_plan_id=plan.id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=plan.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.TREATMENT_PLAN_UPDATED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "treatment_plan_id": plan.id,
                        "plan_status": request.plan_status,
                    },
                ),
            )

        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")
        async with self._database_pool.acquire() as conn2:
            props = await self._repository.list_treatment_plan_properties(conn2, plan.id)
        return _plan_response(plan, props)


def _collect_eav_properties(request: CreateTreatmentPlanRequest) -> dict[str, str]:
    props: dict[str, str] = {}
    if request.plan_description is not None:
        props["plan_description"] = request.plan_description
    if request.action_items is not None:
        props["action_items"] = request.action_items
    if request.compensating_control_description is not None:
        props["compensating_control_description"] = request.compensating_control_description
    if request.approver_user_id is not None:
        props["approver_user_id"] = request.approver_user_id
    if request.approval_notes is not None:
        props["approval_notes"] = request.approval_notes
    if request.review_frequency is not None:
        props["review_frequency"] = request.review_frequency
    if request.properties:
        props.update(request.properties)
    return props


def _collect_eav_update_properties(request: UpdateTreatmentPlanRequest) -> dict[str, str]:
    props: dict[str, str] = {}
    if request.plan_description is not None:
        props["plan_description"] = request.plan_description
    if request.action_items is not None:
        props["action_items"] = request.action_items
    if request.compensating_control_description is not None:
        props["compensating_control_description"] = request.compensating_control_description
    if request.approver_user_id is not None:
        props["approver_user_id"] = request.approver_user_id
    if request.approval_notes is not None:
        props["approval_notes"] = request.approval_notes
    if request.review_frequency is not None:
        props["review_frequency"] = request.review_frequency
    if request.properties:
        props.update(request.properties)
    return props


def _plan_response(p, props: dict[str, str] | None = None) -> TreatmentPlanResponse:
    return TreatmentPlanResponse(
        id=p.id,
        risk_id=p.risk_id,
        tenant_key=p.tenant_key,
        plan_status=p.plan_status,
        target_date=p.target_date,
        completed_at=p.completed_at,
        is_active=p.is_active,
        created_at=p.created_at,
        updated_at=p.updated_at,
        created_by=p.created_by,
        properties=props if props else None,
    )
