from __future__ import annotations

import uuid
from importlib import import_module

from .repository import AssessmentRepository
from .schemas import AssessmentResponse, CreateAssessmentRequest

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


@instrument_class_methods(namespace="risk.assessments.service", logger_name="backend.risk.assessments.instrumentation")
class AssessmentService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AssessmentRepository()
        self._risk_repository = RiskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.risk.assessments")

    async def list_assessments(
        self, *, user_id: str, risk_id: str
    ) -> list[AssessmentResponse]:
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
            records = await self._repository.list_assessments(conn, risk_id)
        return [_assessment_response(r) for r in records]

    async def create_assessment(
        self, *, user_id: str, risk_id: str, request: CreateAssessmentRequest
    ) -> AssessmentResponse:
        now = utc_now_sql()
        assessment_id = str(uuid.uuid4())
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

            assessment = await self._repository.create_assessment(
                conn,
                assessment_id=assessment_id,
                risk_id=risk_id,
                assessment_type=request.assessment_type,
                likelihood_score=request.likelihood_score,
                impact_score=request.impact_score,
                assessed_by=user_id,
                assessment_notes=request.assessment_notes,
                now=now,
            )

            # Auto-update risk level based on score
            risk_score = request.likelihood_score * request.impact_score
            new_level = await self._risk_repository.resolve_risk_level_for_score(conn, risk_score)
            if new_level is not None:
                await self._risk_repository.update_risk_level(
                    conn, risk_id, new_level, updated_by=user_id, now=now
                )

            # Create review event for assessment
            _review_repo_module = import_module("backend.06_risk_registry.06_review_events.repository")
            review_repo = _review_repo_module.ReviewEventRepository()
            await review_repo.create_review_event(
                conn,
                event_id=str(uuid.uuid4()),
                risk_id=risk_id,
                event_type="assessed",
                old_status=None,
                new_status=None,
                actor_id=user_id,
                comment=f"{request.assessment_type} assessment: L={request.likelihood_score} x I={request.impact_score} = {risk_score}",
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.RISK_ASSESSED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "assessment_id": assessment_id,
                        "assessment_type": request.assessment_type,
                        "likelihood_score": str(request.likelihood_score),
                        "impact_score": str(request.impact_score),
                        "risk_score": str(risk_score),
                        "new_level": new_level or "",
                    },
                ),
            )

        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")
        return _assessment_response(assessment)


def _assessment_response(r) -> AssessmentResponse:
    return AssessmentResponse(
        id=r.id,
        risk_id=r.risk_id,
        assessment_type=r.assessment_type,
        likelihood_score=r.likelihood_score,
        impact_score=r.impact_score,
        risk_score=r.risk_score,
        assessed_by=r.assessed_by,
        assessment_notes=r.assessment_notes,
        assessed_at=r.assessed_at,
    )
