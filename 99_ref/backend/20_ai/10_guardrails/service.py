from __future__ import annotations

import uuid
import datetime
from importlib import import_module

from .pipeline import GuardrailPipeline, PipelineResult
from .repository import GuardrailRepository
from .schemas import (
    GuardrailConfigResponse,
    GuardrailEventListResponse,
    GuardrailEventResponse,
    UpsertGuardrailConfigRequest,
)

_telemetry_module = import_module("backend.01_core.telemetry")
_logging_module = import_module("backend.01_core.logging_utils")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission


@instrument_class_methods(
    namespace="ai.guardrails.service",
    logger_name="backend.ai.guardrails.instrumentation",
)
class GuardrailService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = GuardrailRepository()
        self._pipeline = GuardrailPipeline(
            repository=self._repository,
            database_pool=database_pool,
            settings=settings,
        )
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.guardrails")

    # ── Internal use by agent pipeline ──────────────────────────────────────

    async def filter_input(
        self, content: str, *, user_id: str, tenant_key: str,
        org_id: str | None = None, agent_run_id: str | None = None,
    ) -> PipelineResult:
        return await self._pipeline.filter_input(
            content, user_id=user_id, tenant_key=tenant_key,
            org_id=org_id, agent_run_id=agent_run_id,
        )

    async def filter_output(
        self, content: str, *, user_id: str, tenant_key: str,
        org_id: str | None = None, agent_run_id: str | None = None,
    ) -> PipelineResult:
        return await self._pipeline.filter_output(
            content, user_id=user_id, tenant_key=tenant_key,
            org_id=org_id, agent_run_id=agent_run_id,
        )

    # ── Admin API ────────────────────────────────────────────────────────────

    async def list_configs(
        self, *, user_id: str, tenant_key: str, org_id: str | None = None,
    ) -> list[GuardrailConfigResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            configs = await self._repository.get_org_configs(conn, tenant_key=tenant_key, org_id=org_id)
        return [GuardrailConfigResponse(
            id=c.id, tenant_key=c.tenant_key, org_id=c.org_id,
            guardrail_type_code=c.guardrail_type_code,
            is_enabled=c.is_enabled, config_json=c.config_json,
        ) for c in configs]

    async def upsert_config(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None,
        request: UpsertGuardrailConfigRequest,
    ) -> GuardrailConfigResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            config = await self._repository.upsert_config(
                conn, tenant_key=tenant_key, org_id=org_id,
                guardrail_type_code=request.guardrail_type_code,
                is_enabled=request.is_enabled, config_json=request.config_json,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="guardrail_config",
                entity_id=config.id,
                event_type=AIAuditEventType.GUARDRAIL_CONFIG_UPDATED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={"guardrail_type": request.guardrail_type_code, "org_id": org_id or "global"},
                occurred_at=datetime.datetime.utcnow(),
            ))
        return GuardrailConfigResponse(
            id=config.id, tenant_key=config.tenant_key, org_id=config.org_id,
            guardrail_type_code=config.guardrail_type_code,
            is_enabled=config.is_enabled, config_json=config.config_json,
        )

    async def list_events(
        self,
        *,
        user_id: str,
        tenant_key: str,
        filter_user_id: str | None = None,
        guardrail_type_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> GuardrailEventListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            rows = await self._repository.list_events(
                conn, tenant_key=tenant_key,
                user_id=filter_user_id,
                guardrail_type_code=guardrail_type_code,
                limit=limit, offset=offset,
            )
        items = [GuardrailEventResponse(**r) for r in rows]
        return GuardrailEventListResponse(items=items, total=len(items))
