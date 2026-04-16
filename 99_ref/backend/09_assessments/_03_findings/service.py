from __future__ import annotations

import uuid
from datetime import datetime
from importlib import import_module

from .repository import FindingRepository

_models_module = import_module("backend.09_assessments.models")
FindingRecord = _models_module.FindingRecord

_schemas_module = import_module("backend.09_assessments.schemas")
CreateFindingRequest = _schemas_module.CreateFindingRequest
FindingListResponse = _schemas_module.FindingListResponse
FindingResponse = _schemas_module.FindingResponse
UpdateFindingRequest = _schemas_module.UpdateFindingRequest

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
_tasks_constants_module = import_module("backend.07_tasks.constants")
_engagements_repo_module = import_module("backend.12_engagements.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
FINDING_STATUS_TRANSITIONS = _tasks_constants_module.FINDING_STATUS_TRANSITIONS
FINDING_TRANSITION_PERMISSION = _tasks_constants_module.FINDING_TRANSITION_PERMISSION
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AssessmentAuditEventType = _constants_module.AssessmentAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
EngagementRepository = _engagements_repo_module.EngagementRepository

_CACHE_TTL_FINDINGS = 300  # 5 minutes


@instrument_class_methods(
    namespace="assessments.findings.service",
    logger_name="backend.assessments.findings.instrumentation",
)
class FindingService:
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
        self._repository = FindingRepository()
        self._engagement_repository = EngagementRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.assessments.findings")

    async def _assert_user_globally_active(self, conn, *, user_id: str) -> None:
        if not await self._engagement_repository.is_user_globally_active(
            conn,
            user_id=user_id,
        ):
            raise AuthorizationError("User account is inactive or suspended.")

    async def list_findings(
        self,
        *,
        user_id: str,
        assessment_id: str,
        severity_code: str | None = None,
        status_code: str | None = None,
        finding_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FindingListResponse:
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            await require_permission(conn, user_id, "assessments.view")
        return await self.list_findings_prevalidated(
            user_id=user_id,
            assessment_id=assessment_id,
            severity_code=severity_code,
            status_code=status_code,
            finding_type=finding_type,
            limit=limit,
            offset=offset,
        )

    async def list_findings_prevalidated(
        self,
        *,
        user_id: str,
        assessment_id: str,
        severity_code: str | None = None,
        status_code: str | None = None,
        finding_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FindingListResponse:
        has_filters = any([severity_code, status_code, finding_type])
        cache_key = f"findings:{assessment_id}"
        if not has_filters and offset == 0:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return FindingListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            records, total = await self._repository.list_findings(
                conn,
                assessment_id=assessment_id,
                severity_code=severity_code,
                status_code=status_code,
                finding_type=finding_type,
                limit=limit,
                offset=offset,
            )

        result = FindingListResponse(
            items=[_finding_response(r) for r in records],
            total=total,
        )
        if not has_filters and offset == 0:
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_FINDINGS)
        return result

    async def create_finding(
        self,
        *,
        user_id: str,
        assessment_id: str,
        request: CreateFindingRequest,
    ) -> FindingResponse:
        async with self._database_pool.acquire() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            await require_permission(conn, user_id, "findings.create")
        return await self.create_finding_prevalidated(
            user_id=user_id,
            assessment_id=assessment_id,
            request=request,
        )

    async def create_finding_prevalidated(
        self,
        *,
        user_id: str,
        assessment_id: str,
        request: CreateFindingRequest,
    ) -> FindingResponse:
        now = utc_now_sql()
        finding_id = str(uuid.uuid4())

        remediation_due_date = (
            datetime.fromisoformat(request.remediation_due_date)
            if request.remediation_due_date
            else None
        )

        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            # Check assessment is not locked
            is_locked = await self._repository.check_assessment_locked(conn, assessment_id)
            if is_locked:
                raise ConflictError(
                    f"Assessment '{assessment_id}' is locked. Cannot add findings to a locked assessment."
                )

            record = await self._repository.create_finding(
                conn,
                finding_id=finding_id,
                assessment_id=assessment_id,
                control_id=request.control_id,
                risk_id=request.risk_id,
                severity_code=request.severity_code,
                finding_type=request.finding_type,
                assigned_to=request.assigned_to,
                remediation_due_date=remediation_due_date,
                created_by=user_id,
                now=now,
            )

            eav_pairs = _collect_eav_create_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_finding_property(
                    conn,
                    finding_id=finding_id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="",  # findings are assessment-scoped; tenant_key resolved via assessment
                    entity_type="finding",
                    entity_id=finding_id,
                    event_type=AssessmentAuditEventType.FINDING_CREATED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "assessment_id": assessment_id,
                        "severity_code": request.severity_code,
                        "finding_type": request.finding_type,
                        "title": request.title,
                    },
                ),
            )

        await self._cache.delete(f"findings:{assessment_id}")
        await self._cache.delete(f"assessment:{assessment_id}")

        # Re-fetch via view for enriched data
        async with self._database_pool.acquire() as conn:
            enriched = await self._repository.get_finding_by_id(conn, finding_id)
        return _finding_response(enriched or record)

    async def get_finding(self, *, finding_id: str) -> FindingResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_finding_by_id(conn, finding_id)
        if record is None:
            raise NotFoundError(f"Finding '{finding_id}' not found")
        return _finding_response(record)

    async def update_finding_prevalidated(
        self,
        *,
        user_id: str,
        finding_id: str,
        request: UpdateFindingRequest,
    ) -> FindingResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            existing = await self._repository.get_finding_by_id(conn, finding_id)
            if existing is None:
                raise NotFoundError(f"Finding '{finding_id}' not found")

            if (
                request.finding_status_code is not None
                and request.finding_status_code != existing.finding_status_code
            ):
                is_locked = await self._repository.check_assessment_locked(
                    conn, existing.assessment_id
                )
                if is_locked:
                    raise ConflictError(
                        f"Assessment '{existing.assessment_id}' is locked. "
                        "Cannot change finding status on a locked assessment."
                    )

                old_status = existing.finding_status_code
                new_status = request.finding_status_code
                allowed_next = FINDING_STATUS_TRANSITIONS.get(old_status, [])
                if new_status not in allowed_next:
                    raise ValidationError(
                        f"Invalid finding status transition: '{old_status}' -> '{new_status}'. "
                        f"Allowed: {allowed_next or 'none (terminal status)'}."
                    )

            remediation_due_date = (
                datetime.fromisoformat(request.remediation_due_date)
                if request.remediation_due_date
                else None
            )

            await self._repository.update_finding(
                conn,
                finding_id=finding_id,
                finding_status_code=request.finding_status_code,
                severity_code=request.severity_code,
                assigned_to=request.assigned_to,
                remediation_due_date=remediation_due_date,
                updated_by=user_id,
                now=now,
            )

            eav_pairs = _collect_eav_update_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_finding_property(
                    conn,
                    finding_id=finding_id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )

            status_changed = (
                request.finding_status_code is not None
                and request.finding_status_code != existing.finding_status_code
            )
            event_type = (
                AssessmentAuditEventType.FINDING_STATUS_CHANGED
                if status_changed
                else AssessmentAuditEventType.FINDING_UPDATED
            )
            audit_props: dict[str, str] = {
                "assessment_id": existing.assessment_id,
            }
            if status_changed:
                audit_props["old_status"] = existing.finding_status_code
                audit_props["new_status"] = request.finding_status_code or ""
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="",
                    entity_type="finding",
                    entity_id=finding_id,
                    event_type=event_type.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties=audit_props,
                ),
            )

        await self._cache.delete(f"findings:{existing.assessment_id}")
        await self._cache.delete(f"assessment:{existing.assessment_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_finding_by_id(conn, finding_id)
        if record is None:
            raise NotFoundError(f"Finding '{finding_id}' not found")
        return _finding_response(record)

    async def delete_finding_prevalidated(self, *, user_id: str, finding_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            existing = await self._repository.get_finding_by_id(conn, finding_id)
            if existing is None:
                raise NotFoundError(f"Finding '{finding_id}' not found")
            removed = await self._repository.soft_delete_finding(
                conn,
                finding_id=finding_id,
                deleted_by=user_id,
                now=now,
            )
            if not removed:
                raise NotFoundError(f"Finding '{finding_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="",
                    entity_type="finding",
                    entity_id=finding_id,
                    event_type=AssessmentAuditEventType.FINDING_DELETED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"assessment_id": existing.assessment_id},
                ),
            )
        await self._cache.delete(f"findings:{existing.assessment_id}")
        await self._cache.delete(f"assessment:{existing.assessment_id}")

    async def update_finding(
        self,
        *,
        user_id: str,
        finding_id: str,
        request: UpdateFindingRequest,
    ) -> FindingResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            await require_permission(conn, user_id, "findings.update")
            existing = await self._repository.get_finding_by_id(conn, finding_id)
            if existing is None:
                raise NotFoundError(f"Finding '{finding_id}' not found")

            # If changing status, check the parent assessment is not locked
            if (
                request.finding_status_code is not None
                and request.finding_status_code != existing.finding_status_code
            ):
                is_locked = await self._repository.check_assessment_locked(
                    conn, existing.assessment_id
                )
                if is_locked:
                    raise ConflictError(
                        f"Assessment '{existing.assessment_id}' is locked. "
                        "Cannot change finding status on a locked assessment."
                    )

                # Validate the transition is permitted
                old_status = existing.finding_status_code
                new_status = request.finding_status_code
                allowed_next = FINDING_STATUS_TRANSITIONS.get(old_status, [])
                if new_status not in allowed_next:
                    raise ValidationError(
                        f"Invalid finding status transition: '{old_status}' → '{new_status}'. "
                        f"Allowed: {allowed_next or 'none (terminal status)'}."
                    )

                # Check permission for this specific transition
                required_perm = FINDING_TRANSITION_PERMISSION.get((old_status, new_status))
                if required_perm:
                    await require_permission(conn, user_id, required_perm)

            remediation_due_date = (
                datetime.fromisoformat(request.remediation_due_date)
                if request.remediation_due_date
                else None
            )

            await self._repository.update_finding(
                conn,
                finding_id=finding_id,
                finding_status_code=request.finding_status_code,
                severity_code=request.severity_code,
                assigned_to=request.assigned_to,
                remediation_due_date=remediation_due_date,
                updated_by=user_id,
                now=now,
            )

            eav_pairs = _collect_eav_update_properties(request)
            for key, value in eav_pairs.items():
                await self._repository.upsert_finding_property(
                    conn,
                    finding_id=finding_id,
                    property_key=key,
                    property_value=value,
                    actor_id=user_id,
                    now=now,
                )

            status_changed = (
                request.finding_status_code is not None
                and request.finding_status_code != existing.finding_status_code
            )
            event_type = (
                AssessmentAuditEventType.FINDING_STATUS_CHANGED
                if status_changed
                else AssessmentAuditEventType.FINDING_UPDATED
            )

            audit_props: dict[str, str] = {
                "assessment_id": existing.assessment_id,
            }
            if status_changed:
                audit_props["old_status"] = existing.finding_status_code
                audit_props["new_status"] = request.finding_status_code or ""

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="",
                    entity_type="finding",
                    entity_id=finding_id,
                    event_type=event_type.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties=audit_props,
                ),
            )

        await self._cache.delete(f"findings:{existing.assessment_id}")
        await self._cache.delete(f"assessment:{existing.assessment_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_finding_by_id(conn, finding_id)
        if record is None:
            raise NotFoundError(f"Finding '{finding_id}' not found")
        return _finding_response(record)

    async def delete_finding(self, *, user_id: str, finding_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._assert_user_globally_active(conn, user_id=user_id)
            await require_permission(conn, user_id, "findings.delete")
            existing = await self._repository.get_finding_by_id(conn, finding_id)
            if existing is None:
                raise NotFoundError(f"Finding '{finding_id}' not found")
            removed = await self._repository.soft_delete_finding(
                conn,
                finding_id=finding_id,
                deleted_by=user_id,
                now=now,
            )
            if not removed:
                raise NotFoundError(f"Finding '{finding_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="",
                    entity_type="finding",
                    entity_id=finding_id,
                    event_type=AssessmentAuditEventType.FINDING_DELETED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"assessment_id": existing.assessment_id},
                ),
            )
        await self._cache.delete(f"findings:{existing.assessment_id}")
        await self._cache.delete(f"assessment:{existing.assessment_id}")


def _collect_eav_create_properties(request: CreateFindingRequest) -> dict[str, str]:
    props: dict[str, str] = {"title": request.title}
    if request.description is not None:
        props["description"] = request.description
    if request.recommendation is not None:
        props["recommendation"] = request.recommendation
    return props


def _collect_eav_update_properties(request: UpdateFindingRequest) -> dict[str, str]:
    props: dict[str, str] = {}
    if request.title is not None:
        props["title"] = request.title
    if request.description is not None:
        props["description"] = request.description
    if request.recommendation is not None:
        props["recommendation"] = request.recommendation
    return props


def _finding_response(r: FindingRecord) -> FindingResponse:
    return FindingResponse(
        id=r.id,
        assessment_id=r.assessment_id,
        control_id=r.control_id,
        risk_id=r.risk_id,
        severity_code=r.severity_code,
        finding_type=r.finding_type,
        finding_status_code=r.finding_status_code,
        assigned_to=r.assigned_to,
        remediation_due_date=r.remediation_due_date,
        severity_name=r.severity_name,
        finding_status_name=r.finding_status_name,
        title=r.title,
        description=r.description,
        recommendation=r.recommendation,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
    )
