from __future__ import annotations

from importlib import import_module

from .crypto import encrypt_value, parse_encryption_key
from .models import AgentConfigRecord, ResolvedLLMConfig
from .repository import AgentConfigRepository
from .resolver import AgentConfigResolver
from .schemas import (
    AgentConfigListResponse,
    AgentConfigResponse,
    CreateAgentConfigRequest,
    ResolvedConfigResponse,
    UpdateAgentConfigRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.20_ai.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ForbiddenError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AIAuditEventType = _constants_module.AIAuditEventType
require_permission = _perm_check_module.require_permission

_CACHE_KEY_PREFIX = "ai:agent_configs"
_CACHE_TTL = 300  # 5 min


def _to_response(record: AgentConfigRecord, has_key: bool = False) -> AgentConfigResponse:
    return AgentConfigResponse(
        id=record.id,
        tenant_key=record.tenant_key,
        agent_type_code=record.agent_type_code,
        org_id=record.org_id,
        provider_base_url=record.provider_base_url,
        provider_type=record.provider_type,
        has_api_key=has_key,
        model_id=record.model_id,
        temperature=float(record.temperature),
        max_tokens=record.max_tokens,
        is_active=record.is_active,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


@instrument_class_methods(
    namespace="ai.agent_config.service",
    logger_name="backend.ai.agent_config.instrumentation",
)
class AgentConfigService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AgentConfigRepository()
        self._resolver = AgentConfigResolver(
            repository=self._repository,
            database_pool=database_pool,
            settings=settings,
        )
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.agent_config")

    def _get_enc_key(self) -> bytes:
        if not self._settings.ai_encryption_key:
            raise ValueError("AI_ENCRYPTION_KEY not configured")
        return parse_encryption_key(self._settings.ai_encryption_key)

    async def list_configs(
        self,
        *,
        user_id: str,
        tenant_key: str,
        agent_type_code: str | None = None,
        org_id: str | None = None,
    ) -> AgentConfigListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{tenant_key}"
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            records = await self._repository.list_configs(
                conn, tenant_key=tenant_key,
                agent_type_code=agent_type_code, org_id=org_id,
            )
            # Check which ones have keys
            items = []
            for r in records:
                raw = await self._repository.get_encrypted_api_key(conn, config_id=r.id)
                items.append(_to_response(r, has_key=bool(raw)))
        return AgentConfigListResponse(items=items, total=len(items))

    async def get_config(self, *, config_id: str, tenant_key: str, user_id: str) -> AgentConfigResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            record = await self._repository.get_config(conn, config_id=config_id, tenant_key=tenant_key)
            if not record:
                raise NotFoundError(f"Agent config {config_id} not found")
            raw = await self._repository.get_encrypted_api_key(conn, config_id=config_id)
        return _to_response(record, has_key=bool(raw))

    async def resolve_config(
        self,
        *,
        agent_type_code: str,
        org_id: str | None = None,
    ) -> ResolvedLLMConfig:
        """Used internally by agent graphs — no permission check needed."""
        return await self._resolver.resolve(agent_type_code=agent_type_code, org_id=org_id)

    async def create_config(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateAgentConfigRequest,
    ) -> AgentConfigResponse:
        api_key_encrypted: str | None = None
        if request.api_key:
            api_key_encrypted = encrypt_value(request.api_key, self._get_enc_key())

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            record = await self._repository.create_config(
                conn,
                tenant_key=tenant_key,
                agent_type_code=request.agent_type_code,
                org_id=request.org_id,
                provider_base_url=request.provider_base_url,
                api_key_encrypted=api_key_encrypted,
                provider_type=request.provider_type,
                model_id=request.model_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                is_active=request.is_active,
            )
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(__import__("uuid").uuid4()),
                tenant_key=tenant_key,
                entity_type="agent_config",
                entity_id=record.id,
                event_type=AIAuditEventType.AGENT_CONFIG_CREATED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={"agent_type_code": record.agent_type_code, "org_id": record.org_id or "global"},
                occurred_at=__import__("datetime").datetime.utcnow(),
            ))
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{tenant_key}")
        return _to_response(record, has_key=bool(api_key_encrypted))

    async def update_config(
        self,
        *,
        user_id: str,
        tenant_key: str,
        config_id: str,
        request: UpdateAgentConfigRequest,
    ) -> AgentConfigResponse:
        api_key_encrypted: str | None = None
        clear_api_key = False
        if request.api_key is not None:
            if request.api_key == "":
                clear_api_key = True
            else:
                api_key_encrypted = encrypt_value(request.api_key, self._get_enc_key())

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            record = await self._repository.update_config(
                conn,
                config_id=config_id,
                tenant_key=tenant_key,
                provider_base_url=request.provider_base_url,
                api_key_encrypted=api_key_encrypted,
                clear_api_key=clear_api_key,
                provider_type=request.provider_type,
                model_id=request.model_id,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                is_active=request.is_active,
            )
            if not record:
                raise NotFoundError(f"Agent config {config_id} not found")
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(__import__("uuid").uuid4()),
                tenant_key=tenant_key,
                entity_type="agent_config",
                entity_id=config_id,
                event_type=AIAuditEventType.AGENT_CONFIG_UPDATED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={"agent_type_code": record.agent_type_code},
                occurred_at=__import__("datetime").datetime.utcnow(),
            ))
            raw = await self._repository.get_encrypted_api_key(conn, config_id=config_id)
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{tenant_key}")
        return _to_response(record, has_key=bool(raw))

    async def delete_config(
        self,
        *,
        user_id: str,
        tenant_key: str,
        config_id: str,
    ) -> None:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "ai_copilot.admin")
            deleted = await self._repository.delete_config(conn, config_id=config_id, tenant_key=tenant_key)
            if not deleted:
                raise NotFoundError(f"Agent config {config_id} not found")
            await self._audit_writer.write_entry(conn, AuditEntry(
                id=str(__import__("uuid").uuid4()),
                tenant_key=tenant_key,
                entity_type="agent_config",
                entity_id=config_id,
                event_type=AIAuditEventType.AGENT_CONFIG_DELETED,
                event_category="ai",
                actor_id=user_id,
                actor_type="user",
                properties={},
                occurred_at=__import__("datetime").datetime.utcnow(),
            ))
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{tenant_key}")
