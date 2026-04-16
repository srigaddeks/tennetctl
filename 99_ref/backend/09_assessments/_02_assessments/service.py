from __future__ import annotations

import uuid
from datetime import datetime
from importlib import import_module

from .repository import AssessmentRepository

_models_module = import_module("backend.09_assessments.models")
AssessmentRecord = _models_module.AssessmentRecord

_schemas_module = import_module("backend.09_assessments.schemas")
AssessmentListResponse = _schemas_module.AssessmentListResponse
AssessmentResponse = _schemas_module.AssessmentResponse
AssessmentSummaryMatrix = _schemas_module.AssessmentSummaryMatrix
AssessmentSummaryResponse = _schemas_module.AssessmentSummaryResponse
CreateAssessmentRequest = _schemas_module.CreateAssessmentRequest
UpdateAssessmentRequest = _schemas_module.UpdateAssessmentRequest

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.09_assessments.constants")
_auth_constants_module = import_module("backend.03_auth_manage.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AssessmentAuditEventType = _constants_module.AssessmentAuditEventType
ASSESSMENT_STATUS_TRANSITIONS = _constants_module.ASSESSMENT_STATUS_TRANSITIONS
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_TTL_ASSESSMENTS = 300  # 5 minutes


@instrument_class_methods(
    namespace="assessments.assessments.service",
    logger_name="backend.assessments.assessments.instrumentation",
)
class AssessmentService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AssessmentRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.assessments.assessments")

    async def list_assessments(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        type_code: str | None = None,
        status_code: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> AssessmentListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "assessments.view")

        has_filters = any([workspace_id, type_code, status_code, search])
        cache_key = f"assessments:list:{tenant_key}:{org_id or 'all'}:{offset}:{limit}"
        if not has_filters:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return AssessmentListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            records, total = await self._repository.list_assessments(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                type_code=type_code,
                status_code=status_code,
                search=search,
                limit=limit,
                offset=offset,
            )

        result = AssessmentListResponse(
            items=[_assessment_response(r) for r in records],
            total=total,
            limit=limit,
            offset=offset,
        )
        if not has_filters:
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_ASSESSMENTS)
        return result

    async def get_assessment(
        self, *, user_id: str, assessment_id: str
    ) -> AssessmentResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "assessments.view")

        cache_key = f"assessment:{assessment_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return AssessmentResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_assessment_by_id(conn, assessment_id)
        if record is None:
            raise NotFoundError(f"Assessment '{assessment_id}' not found")

        result = _assessment_response(record)
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_ASSESSMENTS)
        return result

    async def create_assessment(
        self, *, user_id: str, tenant_key: str, request: CreateAssessmentRequest
    ) -> AssessmentResponse:
        now = utc_now_sql()
        assessment_id = str(uuid.uuid4())
        assessment_code = f"ASSESS-{uuid.uuid4().hex[:8].upper()}"

        scheduled_start = (
            datetime.fromisoformat(request.scheduled_start)
            if request.scheduled_start
            else None
        )
        scheduled_end = (
            datetime.fromisoformat(request.scheduled_end)
            if request.scheduled_end
            else None
        )

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "assessments.create")
            record = await self._repository.create_assessment(
                conn,
                assessment_id=assessment_id,
                tenant_key=tenant_key,
                assessment_code=assessment_code,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                framework_id=request.framework_id,
                assessment_type_code=request.assessment_type_code,
                lead_assessor_id=request.lead_assessor_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                created_by=user_id,
                now=now,
            )
            eav_pairs = _collect_eav_create_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_assessment_property(
                    conn,
                    assessment_id=assessment_id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="assessment",
                    entity_id=assessment_id,
                    event_type=AssessmentAuditEventType.ASSESSMENT_CREATED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "assessment_code": assessment_code,
                        "org_id": request.org_id,
                        "assessment_type_code": request.assessment_type_code,
                        "name": request.name,
                    },
                ),
            )

        await self._cache.delete_pattern("assessments:list:*")
        # Re-fetch via view to get enriched names
        async with self._database_pool.acquire() as conn:
            enriched = await self._repository.get_assessment_by_id(conn, assessment_id)
        return _assessment_response(enriched or record)

    async def update_assessment(
        self, *, user_id: str, assessment_id: str, request: UpdateAssessmentRequest
    ) -> AssessmentResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "assessments.update")
            existing = await self._repository.get_assessment_by_id(conn, assessment_id)
            if existing is None:
                raise NotFoundError(f"Assessment '{assessment_id}' not found")

            # Validate status transition
            if (
                request.assessment_status_code is not None
                and request.assessment_status_code != existing.assessment_status_code
            ):
                current_status = existing.assessment_status_code
                allowed = ASSESSMENT_STATUS_TRANSITIONS.get(current_status, set())
                if request.assessment_status_code not in allowed:
                    raise ValidationError(
                        f"Cannot transition assessment from '{current_status}' to "
                        f"'{request.assessment_status_code}'. "
                        f"Allowed transitions: {', '.join(sorted(allowed)) if allowed else 'none (terminal state)'}"
                    )

            # If cancelling, unlock the assessment
            is_locked: bool | None = None
            actual_end: datetime | None = None
            if request.assessment_status_code == "cancelled":
                is_locked = False
                actual_end = now

            scheduled_start = (
                datetime.fromisoformat(request.scheduled_start)
                if request.scheduled_start
                else None
            )
            scheduled_end = (
                datetime.fromisoformat(request.scheduled_end)
                if request.scheduled_end
                else None
            )

            await self._repository.update_assessment(
                conn,
                assessment_id=assessment_id,
                assessment_type_code=request.assessment_type_code,
                status_code=request.assessment_status_code,
                lead_assessor_id=request.lead_assessor_id,
                scheduled_start=scheduled_start,
                scheduled_end=scheduled_end,
                actual_start=None,
                actual_end=actual_end,
                is_locked=is_locked,
                updated_by=user_id,
                now=now,
            )

            eav_pairs = _collect_eav_update_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_assessment_property(
                    conn,
                    assessment_id=assessment_id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="assessment",
                    entity_id=assessment_id,
                    event_type=AssessmentAuditEventType.ASSESSMENT_UPDATED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "assessment_status_code": request.assessment_status_code,
                        "assessment_type_code": request.assessment_type_code,
                    },
                ),
            )

        await self._cache.delete_pattern("assessments:list:*")
        await self._cache.delete(f"assessment:{assessment_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_assessment_by_id(conn, assessment_id)
        if record is None:
            raise NotFoundError(f"Assessment '{assessment_id}' not found")
        return _assessment_response(record)

    async def complete_assessment(
        self, *, user_id: str, assessment_id: str
    ) -> AssessmentResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "assessments.update")
            existing = await self._repository.get_assessment_by_id(conn, assessment_id)
            if existing is None:
                raise NotFoundError(f"Assessment '{assessment_id}' not found")

            if existing.assessment_status_code not in {"in_progress", "review"}:
                raise ConflictError(
                    f"Cannot complete assessment in status '{existing.assessment_status_code}'. "
                    "Assessment must be 'in_progress' or 'review'."
                )

            await self._repository.update_assessment(
                conn,
                assessment_id=assessment_id,
                status_code="completed",
                is_locked=True,
                actual_end=now,
                updated_by=user_id,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="assessment",
                    entity_id=assessment_id,
                    event_type=AssessmentAuditEventType.ASSESSMENT_COMPLETED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "assessment_code": existing.assessment_code,
                    },
                ),
            )

        await self._cache.delete_pattern("assessments:list:*")
        await self._cache.delete(f"assessment:{assessment_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_assessment_by_id(conn, assessment_id)
        if record is None:
            raise NotFoundError(f"Assessment '{assessment_id}' not found")
        return _assessment_response(record)

    async def get_summary(
        self, *, user_id: str, assessment_id: str
    ) -> AssessmentSummaryResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "assessments.view")
            existing = await self._repository.get_assessment_by_id(conn, assessment_id)
            if existing is None:
                raise NotFoundError(f"Assessment '{assessment_id}' not found")
            rows = await self._repository.get_assessment_summary(conn, assessment_id)

        # Build severity × status matrix
        matrix: dict[str, AssessmentSummaryMatrix] = {}
        total_findings = 0

        _STATUS_MAP = {
            "open": "open",
            "in_remediation": "in_remediation",
            "verified_closed": "verified_closed",
            "accepted": "accepted",
            "disputed": "disputed",
        }

        for row in rows:
            severity = row["severity_code"]
            status = row["finding_status_code"]
            count = row["finding_count"]
            total_findings += count

            if severity not in matrix:
                matrix[severity] = AssessmentSummaryMatrix()

            current = matrix[severity]
            # Build updated matrix with the new count for this status
            updated_kwargs = {
                "open": current.open,
                "in_remediation": current.in_remediation,
                "verified_closed": current.verified_closed,
                "accepted": current.accepted,
                "disputed": current.disputed,
            }
            if status in updated_kwargs:
                updated_kwargs[status] = updated_kwargs[status] + count
            matrix[severity] = AssessmentSummaryMatrix(**updated_kwargs)

        return AssessmentSummaryResponse(
            assessment_id=assessment_id,
            total_findings=total_findings,
            matrix=matrix,
        )

    async def delete_assessment(self, *, user_id: str, assessment_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "assessments.delete")
            existing = await self._repository.get_assessment_by_id(conn, assessment_id)
            if existing is None:
                raise NotFoundError(f"Assessment '{assessment_id}' not found")
            removed = await self._repository.soft_delete_assessment(
                conn,
                assessment_id=assessment_id,
                deleted_by=user_id,
                now=now,
            )
            if not removed:
                raise NotFoundError(f"Assessment '{assessment_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=existing.tenant_key,
                    entity_type="assessment",
                    entity_id=assessment_id,
                    event_type=AssessmentAuditEventType.ASSESSMENT_DELETED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"assessment_code": existing.assessment_code},
                ),
            )
        await self._cache.delete_pattern("assessments:list:*")
        await self._cache.delete(f"assessment:{assessment_id}")


def _collect_eav_create_properties(request: CreateAssessmentRequest) -> dict[str, str]:
    props: dict[str, str] = {"name": request.name}
    if request.description is not None:
        props["description"] = request.description
    if request.scope_notes is not None:
        props["scope_notes"] = request.scope_notes
    return props


def _collect_eav_update_properties(request: UpdateAssessmentRequest) -> dict[str, str]:
    props: dict[str, str] = {}
    if request.name is not None:
        props["name"] = request.name
    if request.description is not None:
        props["description"] = request.description
    if request.scope_notes is not None:
        props["scope_notes"] = request.scope_notes
    return props


def _assessment_response(r: AssessmentRecord) -> AssessmentResponse:
    return AssessmentResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        assessment_code=r.assessment_code,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        framework_id=r.framework_id,
        assessment_type_code=r.assessment_type_code,
        assessment_status_code=r.assessment_status_code,
        lead_assessor_id=r.lead_assessor_id,
        scheduled_start=r.scheduled_start,
        scheduled_end=r.scheduled_end,
        actual_start=r.actual_start,
        actual_end=r.actual_end,
        is_locked=r.is_locked,
        assessment_type_name=r.assessment_type_name,
        assessment_status_name=r.assessment_status_name,
        name=r.name,
        description=r.description,
        scope_notes=r.scope_notes,
        finding_count=r.finding_count,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
    )
