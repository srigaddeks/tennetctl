from __future__ import annotations

import uuid
from importlib import import_module

from .repository import RequirementRepository
from .schemas import (
    CreateRequirementRequest,
    RequirementListResponse,
    RequirementResponse,
    UpdateRequirementRequest,
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
_constants_module = import_module("backend.05_grc_library.constants")
_frameworks_repo_module = import_module(
    "backend.05_grc_library.02_frameworks.repository"
)
_versions_repo_module = import_module("backend.05_grc_library.03_versions.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
FrameworkAuditEventType = _constants_module.FrameworkAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
FrameworkRepository = _frameworks_repo_module.FrameworkRepository


@instrument_class_methods(
    namespace="grc.requirements.service",
    logger_name="backend.grc.requirements.instrumentation",
)
class RequirementService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = RequirementRepository()
        self._framework_repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.requirements")

    async def _get_framework_or_not_found(self, conn, framework_id: str):
        framework = await self._framework_repository.get_framework_by_id(
            conn, framework_id
        )
        if framework is None:
            raise NotFoundError(f"Framework '{framework_id}' not found")
        return framework

    async def _get_latest_published_version_id(
        self, conn, framework_id: str
    ) -> str | None:
        """Get the latest published version ID for a framework, or None if no published version exists."""
        row = await conn.fetchrow(
            """
            SELECT id FROM "05_grc_library"."11_fct_framework_versions"
            WHERE framework_id = $1 AND lifecycle_state = 'published' AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            framework_id,
        )
        return row["id"] if row else None

    async def list_requirements(
        self, *, user_id: str, framework_id: str, version_id: str | None = None
    ) -> RequirementListResponse:
        async with self._database_pool.acquire() as conn:
            framework = await self._get_framework_or_not_found(conn, framework_id)
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=framework.scope_org_id,
                scope_workspace_id=framework.scope_workspace_id,
            )

            # Workspace frameworks show ALL requirements - not filtered by library version
            # version_id is only used when explicitly requested by the caller
            # This ensures workspace requirements don't auto-update until user takes pull

            records = await self._repository.list_requirements(
                conn, framework_id=framework_id, version_id=version_id
            )
        items = [_requirement_response(r) for r in records]
        return RequirementListResponse(items=items, total=len(items))

    async def create_requirement(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        request: CreateRequirementRequest,
    ) -> RequirementResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                framework = await self._get_framework_or_not_found(conn, framework_id)
                await require_permission(
                    conn,
                    user_id,
                    "frameworks.create",
                    scope_org_id=framework.scope_org_id,
                    scope_workspace_id=framework.scope_workspace_id,
                )
                # Auto-revert framework to draft if published
                auto_reverted = False
                if framework.approval_status == "approved":
                    await self._framework_repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="draft",
                        is_marketplace_visible=False,
                        updated_by=user_id,
                        now=now,
                    )
                    auto_reverted = True
                record = await self._repository.create_requirement(
                    conn,
                    requirement_id=str(uuid.uuid4()),
                    framework_id=framework_id,
                    requirement_code=request.requirement_code,
                    sort_order=request.sort_order,
                    parent_requirement_id=request.parent_requirement_id,
                    created_by=user_id,
                    now=now,
                )
                props: dict[str, str] = {}
                if request.name:
                    props["name"] = request.name
                if request.description:
                    props["description"] = request.description
                if props:
                    await self._repository.upsert_requirement_properties(
                        conn,
                        requirement_id=record.id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="requirement",
                        entity_id=record.id,
                        event_type=FrameworkAuditEventType.REQUIREMENT_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "requirement_code": request.requirement_code,
                            "name": request.name,
                            "auto_reverted_to_draft": str(auto_reverted),
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_requirement_by_id(conn, record.id)
        return _requirement_response(record)

    async def update_requirement(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        requirement_id: str,
        request: UpdateRequirementRequest,
    ) -> RequirementResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                framework = await self._get_framework_or_not_found(conn, framework_id)
                await require_permission(
                    conn,
                    user_id,
                    "frameworks.update",
                    scope_org_id=framework.scope_org_id,
                    scope_workspace_id=framework.scope_workspace_id,
                )
                # Auto-revert framework to draft if published
                auto_reverted = False
                if framework.approval_status == "approved":
                    await self._framework_repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="draft",
                        is_marketplace_visible=False,
                        updated_by=user_id,
                        now=now,
                    )
                    auto_reverted = True
                record = await self._repository.update_requirement(
                    conn,
                    requirement_id,
                    requirement_code=request.requirement_code,
                    sort_order=request.sort_order,
                    parent_requirement_id=request.parent_requirement_id,
                    updated_by=user_id,
                    now=now,
                )
                if record is None:
                    raise NotFoundError(f"Requirement '{requirement_id}' not found")
                if record.framework_id != framework_id:
                    raise NotFoundError(
                        f"Requirement '{requirement_id}' not found in framework '{framework_id}'"
                    )
                props: dict[str, str] = {}
                if request.name is not None:
                    props["name"] = request.name
                if request.description is not None:
                    props["description"] = request.description
                if props:
                    await self._repository.upsert_requirement_properties(
                        conn,
                        requirement_id=requirement_id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="requirement",
                        entity_id=requirement_id,
                        event_type=FrameworkAuditEventType.REQUIREMENT_UPDATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "auto_reverted_to_draft": str(auto_reverted),
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_requirement_by_id(conn, requirement_id)
        return _requirement_response(record)

    async def delete_requirement(
        self, *, user_id: str, tenant_key: str, framework_id: str, requirement_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                framework = await self._get_framework_or_not_found(conn, framework_id)
                await require_permission(
                    conn,
                    user_id,
                    "frameworks.delete",
                    scope_org_id=framework.scope_org_id,
                    scope_workspace_id=framework.scope_workspace_id,
                )
                # Auto-revert framework to draft if published
                auto_reverted = False
                if framework.approval_status == "approved":
                    await self._framework_repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="draft",
                        is_marketplace_visible=False,
                        updated_by=user_id,
                        now=now,
                    )
                    auto_reverted = True
                existing = await self._repository.get_requirement_by_id(
                    conn, requirement_id
                )
                if existing is None or existing.framework_id != framework_id:
                    raise NotFoundError(
                        f"Requirement '{requirement_id}' not found in framework '{framework_id}'"
                    )
                deleted = await self._repository.soft_delete_requirement(
                    conn,
                    requirement_id,
                    deleted_by=user_id,
                    now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Requirement '{requirement_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="requirement",
                        entity_id=requirement_id,
                        event_type=FrameworkAuditEventType.REQUIREMENT_DELETED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "auto_reverted_to_draft": str(auto_reverted),
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")


def _requirement_response(r) -> RequirementResponse:
    return RequirementResponse(
        id=r.id,
        framework_id=r.framework_id,
        requirement_code=r.requirement_code,
        sort_order=r.sort_order,
        parent_requirement_id=r.parent_requirement_id,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
    )
