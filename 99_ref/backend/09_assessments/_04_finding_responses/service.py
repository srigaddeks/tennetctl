from __future__ import annotations

import uuid
from importlib import import_module

from .repository import FindingResponseRepository

_schemas_module = import_module("backend.09_assessments.schemas")
CreateFindingResponseRequest = _schemas_module.CreateFindingResponseRequest
FindingResponseListResponse = _schemas_module.FindingResponseListResponse
FindingResponseResponse = _schemas_module.FindingResponseResponse

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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AssessmentAuditEventType = _constants_module.AssessmentAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_TTL_RESPONSES = 300  # 5 minutes


@instrument_class_methods(
    namespace="assessments.finding_responses.service",
    logger_name="backend.assessments.finding_responses.instrumentation",
)
class FindingResponseService:
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
        self._repository = FindingResponseRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.assessments.finding_responses")

    async def list_responses(
        self, *, user_id: str, finding_id: str
    ) -> FindingResponseListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "assessments.view")

        cache_key = f"finding:responses:{finding_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return FindingResponseListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_responses(conn, finding_id)

        result = FindingResponseListResponse(
            items=[
                FindingResponseResponse(
                    id=r.id,
                    finding_id=r.finding_id,
                    responder_id=r.responder_id,
                    response_text=r.response_text,
                    responded_at=r.responded_at,
                    created_at=r.created_at,
                )
                for r in records
            ]
        )
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_RESPONSES)
        return result

    async def create_response(
        self,
        *,
        user_id: str,
        finding_id: str,
        request: CreateFindingResponseRequest,
    ) -> FindingResponseResponse:
        now = utc_now_sql()
        response_id = str(uuid.uuid4())

        # Validate finding exists — re-use findings repo lazily
        _findings_repo_module = import_module(
            "backend.09_assessments._03_findings.repository"
        )
        findings_repo = _findings_repo_module.FindingRepository()

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "findings.update")

            finding = await findings_repo.get_finding_by_id(conn, finding_id)
            if finding is None:
                raise NotFoundError(f"Finding '{finding_id}' not found")

            # NOTE: responses are allowed even on completed/locked assessments

            record = await self._repository.create_response(
                conn,
                response_id=response_id,
                finding_id=finding_id,
                responder_id=user_id,
                response_text=request.response_text,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="",
                    entity_type="finding_response",
                    entity_id=response_id,
                    event_type=AssessmentAuditEventType.FINDING_RESPONSE_SUBMITTED.value,
                    event_category="assessment",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "finding_id": finding_id,
                        "assessment_id": finding.assessment_id,
                    },
                ),
            )

        await self._cache.delete(f"finding:responses:{finding_id}")

        return FindingResponseResponse(
            id=record.id,
            finding_id=record.finding_id,
            responder_id=record.responder_id,
            response_text=record.response_text,
            responded_at=record.responded_at,
            created_at=record.created_at,
        )
