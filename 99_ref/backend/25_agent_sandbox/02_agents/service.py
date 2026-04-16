from __future__ import annotations

import hashlib
import uuid
from importlib import import_module

from .repository import AgentRepository
from .schemas import (
    AgentListResponse,
    AgentResponse,
    AgentVersionResponse,
    CreateAgentRequest,
    UpdateAgentRequest,
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
_constants_module = import_module("backend.25_agent_sandbox.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AgentSandboxAuditEventType = _constants_module.AgentSandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_PREFIX = "asb:agents"
_CACHE_TTL = 300


@instrument_class_methods(namespace="agent_sandbox.agents.service", logger_name="backend.agent_sandbox.agents.instrumentation")
class AgentService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AgentRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.agent_sandbox.agents")

    # ── list ──────────────────────────────────────────────────

    async def list_agents(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        agent_status_code: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> AgentListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            records, total = await self._repository.list_agents(
                conn,
                org_id,
                workspace_id=workspace_id,
                agent_status_code=agent_status_code,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_agent_response(r) for r in records]
        return AgentListResponse(items=items, total=total)

    # ── get ───────────────────────────────────────────────────

    async def get_agent(self, *, user_id: str, agent_id: str) -> AgentResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            record = await self._repository.get_agent_by_id(conn, agent_id)
            if record is None:
                raise NotFoundError(f"Agent '{agent_id}' not found")
            props = await self._repository.get_agent_properties(conn, agent_id)
        resp = _agent_response(record)
        resp.properties = props
        resp.graph_source = props.get("graph_source")
        return resp

    # ── create ────────────────────────────────────────────────

    async def create_agent(
        self, *, user_id: str, tenant_key: str, org_id: str, request: CreateAgentRequest
    ) -> AgentResponse:
        if "name" not in request.properties:
            raise ValidationError("properties must include 'name'")
        if "graph_source" not in request.properties:
            raise ValidationError("properties must include 'graph_source'")

        graph_source = request.properties["graph_source"]
        python_hash = hashlib.sha256(graph_source.encode("utf-8")).hexdigest()

        now = utc_now_sql()
        agent_id = str(uuid.uuid4())

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            async with conn.transaction():
                version = await self._repository.get_next_version(conn, org_id, request.agent_code)
                await self._repository.create_agent(
                    conn,
                    id=agent_id,
                    tenant_key=tenant_key,
                    org_id=org_id,
                    workspace_id=request.workspace_id,
                    agent_code=request.agent_code,
                    version_number=version,
                    agent_status_code="draft",
                    graph_type=request.graph_type,
                    llm_model_id=request.llm_model_id,
                    temperature=request.temperature,
                    max_iterations=request.max_iterations,
                    max_tokens_budget=request.max_tokens_budget,
                    max_tool_calls=request.max_tool_calls,
                    max_duration_ms=request.max_duration_ms,
                    max_cost_usd=request.max_cost_usd,
                    requires_approval=request.requires_approval,
                    python_hash=python_hash,
                    created_by=user_id,
                    now=now,
                )
                await self._repository.upsert_properties(
                    conn, agent_id, request.properties, created_by=user_id, now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="agent",
                        entity_id=agent_id,
                        event_type="created",
                        event_category=AgentSandboxAuditEventType.AGENT_CREATED,
                        actor_id=user_id,
                        occurred_at=now,
                        properties={
                            "agent_code": request.agent_code,
                            "name": request.properties.get("name", ""),
                            "version_number": str(version),
                        },
                    ),
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self.get_agent(user_id=user_id, agent_id=agent_id)

    # ── update ────────────────────────────────────────────────

    async def update_agent(
        self, *, user_id: str, tenant_key: str, org_id: str, agent_id: str, request: UpdateAgentRequest
    ) -> AgentResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            record = await self._repository.get_agent_by_id(conn, agent_id)
            if record is None:
                raise NotFoundError(f"Agent '{agent_id}' not found")

            field_updates = {}
            for field in (
                "graph_type", "llm_model_id", "temperature",
                "max_iterations", "max_tokens_budget", "max_tool_calls",
                "max_duration_ms", "max_cost_usd", "requires_approval",
            ):
                val = getattr(request, field, None)
                if val is not None:
                    field_updates[field] = val

            if request.properties and "graph_source" in request.properties:
                python_hash = hashlib.sha256(
                    request.properties["graph_source"].encode("utf-8")
                ).hexdigest()
                field_updates["python_hash"] = python_hash

            async with conn.transaction():
                if field_updates:
                    await self._repository.update_agent_fields(
                        conn, agent_id, updates=field_updates, updated_by=user_id, now=now,
                    )
                if request.properties:
                    await self._repository.upsert_properties(
                        conn, agent_id, request.properties, created_by=user_id, now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="agent",
                        entity_id=agent_id,
                        event_type="updated",
                        event_category=AgentSandboxAuditEventType.AGENT_UPDATED,
                        actor_id=user_id,
                        occurred_at=now,
                        properties={"fields_updated": ",".join(field_updates.keys())},
                    ),
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self.get_agent(user_id=user_id, agent_id=agent_id)

    # ── delete ────────────────────────────────────────────────

    async def delete_agent(
        self, *, user_id: str, tenant_key: str, org_id: str, agent_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            record = await self._repository.get_agent_by_id(conn, agent_id)
            if record is None:
                raise NotFoundError(f"Agent '{agent_id}' not found")
            async with conn.transaction():
                deleted = await self._repository.soft_delete_agent(
                    conn, agent_id, deleted_by=user_id, now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Agent '{agent_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="agent",
                        entity_id=agent_id,
                        event_type="deleted",
                        event_category=AgentSandboxAuditEventType.AGENT_DELETED,
                        actor_id=user_id,
                        occurred_at=now,
                        properties={"agent_code": record.agent_code},
                    ),
                )
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    # ── versions ──────────────────────────────────────────────

    async def list_versions(
        self, *, user_id: str, org_id: str, agent_code: str
    ) -> list[AgentVersionResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            rows = await self._repository.list_versions(conn, org_id, agent_code)
        return [
            AgentVersionResponse(
                version_number=r["version_number"],
                agent_status_code=r["agent_status_code"],
                python_hash=r.get("python_hash"),
                created_at=r["created_at"],
                created_by=r.get("created_by"),
            )
            for r in rows
        ]

    # ── tool bindings ─────────────────────────────────────────

    async def bind_tool(
        self, *, user_id: str, tenant_key: str, org_id: str, agent_id: str, tool_id: str, sort_order: int = 0
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            record = await self._repository.get_agent_by_id(conn, agent_id)
            if record is None:
                raise NotFoundError(f"Agent '{agent_id}' not found")
            await self._repository.bind_tool(
                conn, agent_id, tool_id, sort_order=sort_order, created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="agent",
                    entity_id=agent_id,
                    event_type="tool_bound",
                    event_category=AgentSandboxAuditEventType.TOOL_BOUND,
                    actor_id=user_id,
                    occurred_at=now,
                    properties={"tool_id": tool_id},
                ),
            )
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def unbind_tool(
        self, *, user_id: str, tenant_key: str, org_id: str, agent_id: str, tool_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            removed = await self._repository.unbind_tool(conn, agent_id, tool_id)
            if not removed:
                raise NotFoundError("Tool binding not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="agent",
                    entity_id=agent_id,
                    event_type="tool_unbound",
                    event_category=AgentSandboxAuditEventType.TOOL_UNBOUND,
                    actor_id=user_id,
                    occurred_at=now,
                    properties={"tool_id": tool_id},
                ),
            )
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def list_bound_tools(
        self, *, user_id: str, agent_id: str
    ) -> list[dict]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            return await self._repository.list_bound_tools(conn, agent_id)


def _agent_response(r) -> AgentResponse:
    return AgentResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        agent_code=r.agent_code,
        version_number=r.version_number,
        agent_status_code=r.agent_status_code,
        agent_status_name=r.agent_status_name,
        graph_type=r.graph_type,
        llm_model_id=r.llm_model_id,
        temperature=r.temperature,
        max_iterations=r.max_iterations,
        max_tokens_budget=r.max_tokens_budget,
        max_tool_calls=r.max_tool_calls,
        max_duration_ms=r.max_duration_ms,
        max_cost_usd=r.max_cost_usd,
        requires_approval=r.requires_approval,
        python_hash=r.python_hash,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
    )
