from __future__ import annotations

import uuid
import datetime
from importlib import import_module

from .assembler import PromptAssembler
from .models import PromptTemplateRecord
from .repository import PromptTemplateRepository
from .schemas import (
    CreatePromptTemplateRequest,
    PromptPreviewRequest,
    PromptPreviewResponse,
    PromptTemplateListResponse,
    PromptTemplateResponse,
    UpdatePromptTemplateRequest,
)

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission


def _to_response(r: PromptTemplateRecord) -> PromptTemplateResponse:
    return PromptTemplateResponse(
        id=r.id, tenant_key=r.tenant_key, scope_code=r.scope_code,
        agent_type_code=r.agent_type_code, feature_code=r.feature_code,
        org_id=r.org_id, prompt_text=r.prompt_text, version=r.version,
        is_active=r.is_active, created_by=r.created_by,
        created_at=r.created_at, updated_at=r.updated_at,
    )


@instrument_class_methods(
    namespace="ai.prompt_config.service",
    logger_name="backend.ai.prompt_config.instrumentation",
)
class PromptConfigService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = PromptTemplateRepository()
        self._assembler = PromptAssembler(
            repository=self._repository,
            database_pool=database_pool,
        )
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.prompt_config")

    async def list_templates(
        self,
        *,
        user_id: str,
        tenant_key: str,
        scope_code: str | None = None,
        agent_type_code: str | None = None,
        feature_code: str | None = None,
        org_id: str | None = None,
    ) -> PromptTemplateListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            records = await self._repository.list_templates(
                conn, tenant_key=tenant_key,
                scope_code=scope_code,
                agent_type_code=agent_type_code,
                feature_code=feature_code,
                org_id=org_id,
                active_only=False,
            )
        items = [_to_response(r) for r in records]
        return PromptTemplateListResponse(items=items, total=len(items))

    async def get_template(self, *, template_id: str, tenant_key: str, user_id: str) -> PromptTemplateResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            record = await self._repository.get_template(conn, template_id=template_id, tenant_key=tenant_key)
        if not record:
            raise NotFoundError(f"Prompt template {template_id} not found")
        return _to_response(record)

    async def create_template(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreatePromptTemplateRequest,
    ) -> PromptTemplateResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            record = await self._repository.create_template(
                conn,
                tenant_key=tenant_key,
                scope_code=request.scope_code,
                agent_type_code=request.agent_type_code,
                feature_code=request.feature_code,
                org_id=request.org_id,
                prompt_text=request.prompt_text,
                is_active=request.is_active,
                created_by=user_id,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="prompt_template",
                entity_id=record.id,
                event_type=AIAuditEventType.PROMPT_TEMPLATE_CREATED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={"scope_code": record.scope_code, "agent_type_code": record.agent_type_code or ""},
                occurred_at=datetime.datetime.utcnow(),
            ))
        return _to_response(record)

    async def update_template(
        self,
        *,
        user_id: str,
        tenant_key: str,
        template_id: str,
        request: UpdatePromptTemplateRequest,
    ) -> PromptTemplateResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            record = await self._repository.update_template(
                conn,
                template_id=template_id,
                tenant_key=tenant_key,
                prompt_text=request.prompt_text,
                is_active=request.is_active,
            )
            if not record:
                raise NotFoundError(f"Prompt template {template_id} not found")
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="prompt_template",
                entity_id=template_id,
                event_type=AIAuditEventType.PROMPT_TEMPLATE_UPDATED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={"scope_code": record.scope_code},
                occurred_at=datetime.datetime.utcnow(),
            ))
        return _to_response(record)

    async def delete_template(self, *, user_id: str, tenant_key: str, template_id: str) -> None:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            deleted = await self._repository.delete_template(conn, template_id=template_id, tenant_key=tenant_key)
            if not deleted:
                raise NotFoundError(f"Prompt template {template_id} not found")
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="prompt_template",
                entity_id=template_id,
                event_type=AIAuditEventType.PROMPT_TEMPLATE_DELETED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={},
                occurred_at=datetime.datetime.utcnow(),
            ))

    async def preview_prompt(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: PromptPreviewRequest,
    ) -> PromptPreviewResponse:
        """Compose and return the full 3-layer prompt without executing an agent run."""
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
        composed, layers = await self._assembler.compose(
            agent_type_code=request.agent_type_code,
            feature_code=request.feature_code,
            org_id=request.org_id,
        )
        return PromptPreviewResponse(
            agent_type_code=request.agent_type_code,
            feature_code=request.feature_code,
            org_id=request.org_id,
            layers=layers,
            composed_prompt=composed,
            char_count=len(composed),
        )

    async def compose_system_prompt(
        self,
        *,
        agent_type_code: str,
        feature_code: str | None = None,
        org_id: str | None = None,
    ) -> str:
        """Used internally by agent graphs — no permission check."""
        composed, _ = await self._assembler.compose(
            agent_type_code=agent_type_code,
            feature_code=feature_code,
            org_id=org_id,
        )
        return composed
