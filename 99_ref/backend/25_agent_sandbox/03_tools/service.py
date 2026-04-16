from __future__ import annotations

import uuid
from importlib import import_module

from .repository import AgentToolRepository
from .schemas import (
    CreateToolRequest,
    ToolListResponse,
    ToolResponse,
    UpdateToolRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.25_agent_sandbox.constants")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AgentSandboxAuditEventType = _constants_module.AgentSandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_PREFIX = "asb:tools"
_CACHE_TTL = 300


@instrument_class_methods(namespace="agent_sandbox.tools.service", logger_name="backend.agent_sandbox.tools.instrumentation")
class AgentToolService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AgentToolRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.agent_sandbox.tools")

    # ── list ──────────────────────────────────────────────────

    async def list_tools(
        self,
        *,
        user_id: str,
        org_id: str,
        tool_type_code: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> ToolListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            records, total = await self._repository.list_tools(
                conn, org_id,
                tool_type_code=tool_type_code,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_tool_response(r) for r in records]
        return ToolListResponse(items=items, total=total)

    # ── get ───────────────────────────────────────────────────

    async def get_tool(self, *, user_id: str, tool_id: str) -> ToolResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.view")
            record = await self._repository.get_tool_by_id(conn, tool_id)
            if record is None:
                raise NotFoundError(f"Tool '{tool_id}' not found")
            props = await self._repository.get_tool_properties(conn, tool_id)
        resp = _tool_response(record)
        resp.properties = props
        return resp

    # ── create ────────────────────────────────────────────────

    async def create_tool(
        self, *, user_id: str, tenant_key: str, org_id: str, request: CreateToolRequest
    ) -> ToolResponse:
        now = utc_now_sql()
        tool_id = str(uuid.uuid4())

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            async with conn.transaction():
                await self._repository.create_tool(
                    conn,
                    id=tool_id,
                    tenant_key=tenant_key,
                    org_id=org_id,
                    tool_code=request.tool_code,
                    tool_type_code=request.tool_type_code,
                    input_schema=request.input_schema,
                    output_schema=request.output_schema,
                    endpoint_url=request.endpoint_url,
                    mcp_server_url=request.mcp_server_url,
                    python_source=request.python_source,
                    signal_id=request.signal_id,
                    requires_approval=request.requires_approval,
                    is_destructive=request.is_destructive,
                    timeout_ms=request.timeout_ms,
                    created_by=user_id,
                    now=now,
                )
                if request.properties:
                    await self._repository.upsert_properties(
                        conn, tool_id, request.properties, created_by=user_id, now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="agent_tool",
                        entity_id=tool_id,
                        event_type="created",
                        event_category=AgentSandboxAuditEventType.TOOL_REGISTERED,
                        actor_id=user_id,
                        occurred_at=now,
                        properties={
                            "tool_code": request.tool_code,
                            "tool_type_code": request.tool_type_code,
                        },
                    ),
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self.get_tool(user_id=user_id, tool_id=tool_id)

    # ── update ────────────────────────────────────────────────

    async def update_tool(
        self, *, user_id: str, tenant_key: str, org_id: str, tool_id: str, request: UpdateToolRequest
    ) -> ToolResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.create")
            record = await self._repository.get_tool_by_id(conn, tool_id)
            if record is None:
                raise NotFoundError(f"Tool '{tool_id}' not found")

            field_updates = {}
            for field in (
                "input_schema", "output_schema", "endpoint_url",
                "mcp_server_url", "python_source", "signal_id",
                "requires_approval", "is_destructive", "timeout_ms",
            ):
                val = getattr(request, field, None)
                if val is not None:
                    field_updates[field] = val

            async with conn.transaction():
                if field_updates:
                    await self._repository.update_tool_fields(
                        conn, tool_id, updates=field_updates, updated_by=user_id, now=now,
                    )
                if request.properties:
                    await self._repository.upsert_properties(
                        conn, tool_id, request.properties, created_by=user_id, now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="agent_tool",
                        entity_id=tool_id,
                        event_type="updated",
                        event_category=AgentSandboxAuditEventType.TOOL_UPDATED,
                        actor_id=user_id,
                        occurred_at=now,
                        properties={"fields_updated": ",".join(field_updates.keys())},
                    ),
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return await self.get_tool(user_id=user_id, tool_id=tool_id)

    # ── delete ────────────────────────────────────────────────

    async def delete_tool(
        self, *, user_id: str, tenant_key: str, org_id: str, tool_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "agent_sandbox.manage")
            record = await self._repository.get_tool_by_id(conn, tool_id)
            if record is None:
                raise NotFoundError(f"Tool '{tool_id}' not found")
            async with conn.transaction():
                deleted = await self._repository.soft_delete_tool(
                    conn, tool_id, deleted_by=user_id, now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Tool '{tool_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="agent_tool",
                        entity_id=tool_id,
                        event_type="deleted",
                        event_category=AgentSandboxAuditEventType.TOOL_DELETED,
                        actor_id=user_id,
                        occurred_at=now,
                        properties={"tool_code": record.tool_code},
                    ),
                )
        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")


def _tool_response(r) -> ToolResponse:
    return ToolResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        tool_code=r.tool_code,
        tool_type_code=r.tool_type_code,
        input_schema=r.input_schema,
        output_schema=r.output_schema,
        endpoint_url=r.endpoint_url,
        mcp_server_url=r.mcp_server_url,
        python_source=r.python_source,
        signal_id=r.signal_id,
        requires_approval=r.requires_approval,
        is_destructive=r.is_destructive,
        timeout_ms=r.timeout_ms,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
    )
