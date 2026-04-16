from __future__ import annotations

import uuid
from importlib import import_module

from .repository import LibraryRepository
from .schemas import (
    AddConnectorTypeMappingRequest,
    AddPolicyRequest,
    CreateLibraryRequest,
    LibraryListResponse,
    LibraryPolicyResponse,
    LibraryResponse,
    RecommendedLibraryResponse,
    UpdateLibraryRequest,
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
_constants_module = import_module("backend.10_sandbox.constants")
_lifecycle_module = import_module("backend.10_sandbox.lifecycle")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
write_lifecycle_event = _lifecycle_module.write_lifecycle_event

_CACHE_KEY_PREFIX = "sb:libraries"
_CACHE_TTL = 300


@instrument_class_methods(namespace="sandbox.libraries.service", logger_name="backend.sandbox.libraries.instrumentation")
class LibraryService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = LibraryRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.libraries")

    async def _require_sandbox_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
        )

    # ── list ──────────────────────────────────────────────────

    async def list_libraries(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        library_type_code: str | None = None,
        is_published: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> LibraryListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{org_id}"
        if not any([library_type_code, is_published]) and offset == 0 and limit == 100:
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return LibraryListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records = await self._repository.list_libraries(
                conn,
                org_id,
                library_type_code=library_type_code,
                is_published=is_published,
                limit=limit,
                offset=offset,
            )
            total = await self._repository.count_libraries(
                conn,
                org_id,
                library_type_code=library_type_code,
                is_published=is_published,
            )

        items = [_library_response(r) for r in records]
        result = LibraryListResponse(items=items, total=total)

        if not any([library_type_code, is_published]) and offset == 0 and limit == 100:
            await self._cache.set_json(cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL)

        return result

    # ── get ───────────────────────────────────────────────────

    async def get_library(
        self, *, user_id: str, library_id: str
    ) -> LibraryResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
            properties = await self._repository.get_library_properties(conn, library_id)
        resp = _library_response(record)
        resp.properties = properties
        return resp

    # ── create ────────────────────────────────────────────────

    async def create_library(
        self, *, user_id: str, tenant_key: str, org_id: str, request: CreateLibraryRequest
    ) -> LibraryResponse:
        now = utc_now_sql()
        library_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
            )
            version_number = await self._repository.get_next_version(
                conn, org_id, request.library_code,
            )
            await self._repository.create_library(
                conn,
                id=library_id,
                tenant_key=tenant_key,
                org_id=org_id,
                library_code=request.library_code,
                library_type_code=request.library_type_code,
                version_number=version_number,
                created_by=user_id,
                now=now,
            )
            if request.properties:
                await self._repository.upsert_properties(
                    conn, library_id, request.properties, created_by=user_id, now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="library",
                    entity_id=library_id,
                    event_type=SandboxAuditEventType.LIBRARY_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "library_code": request.library_code,
                        "library_type_code": request.library_type_code,
                        "version_number": str(version_number),
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="library",
                entity_id=library_id,
                event_type="created",
                actor_id=user_id,
                properties={"library_code": request.library_code},
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            properties = await self._repository.get_library_properties(conn, library_id)
        resp = _library_response(record)
        resp.properties = properties
        return resp

    # ── update ────────────────────────────────────────────────

    async def update_library(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        library_id: str,
        request: UpdateLibraryRequest,
    ) -> LibraryResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            updated = await self._repository.update_library(
                conn,
                library_id,
                library_type_code=request.library_type_code,
                updated_by=user_id,
                now=now,
            )
            if not updated:
                raise NotFoundError(f"Library '{library_id}' not found")
            if request.properties:
                await self._repository.upsert_properties(
                    conn, library_id, request.properties, created_by=user_id, now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="library",
                    entity_id=library_id,
                    event_type=SandboxAuditEventType.LIBRARY_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            properties = await self._repository.get_library_properties(conn, library_id)
        resp = _library_response(record)
        resp.properties = properties
        return resp

    # ── delete ────────────────────────────────────────────────

    async def delete_library(
        self, *, user_id: str, tenant_key: str, org_id: str, library_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=record.org_id,
            )
            deleted = await self._repository.soft_delete(conn, library_id, deleted_by=user_id, now=now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="library",
                    entity_id=library_id,
                    event_type=SandboxAuditEventType.LIBRARY_DELETED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="library",
                entity_id=library_id,
                event_type="deleted",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    # ── publish ───────────────────────────────────────────────

    async def publish_library(
        self, *, user_id: str, tenant_key: str, org_id: str, library_id: str
    ) -> LibraryResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            published = await self._repository.publish_library(
                conn, library_id, updated_by=user_id, now=now,
            )
            if not published:
                raise NotFoundError(
                    f"Library '{library_id}' not found or already published"
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="library",
                    entity_id=library_id,
                    event_type=SandboxAuditEventType.LIBRARY_PUBLISHED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="library",
                entity_id=library_id,
                event_type="published",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
        return _library_response(record)

    # ── clone ─────────────────────────────────────────────────

    async def clone_library(
        self, *, user_id: str, tenant_key: str, org_id: str, library_id: str
    ) -> LibraryResponse:
        now = utc_now_sql()
        new_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            source = await self._repository.get_library_by_id(conn, library_id)
            if source is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=source.org_id,
            )
            new_version = await self._repository.get_next_version(
                conn, org_id, source.library_code,
            )
            await self._repository.clone_library(
                conn,
                library_id,
                new_id=new_id,
                new_version=new_version,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="library",
                    entity_id=new_id,
                    event_type=SandboxAuditEventType.LIBRARY_CLONED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "source_library_id": library_id,
                        "new_version": str(new_version),
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_library_by_id(conn, new_id)
            properties = await self._repository.get_library_properties(conn, new_id)
        resp = _library_response(record)
        resp.properties = properties
        return resp

    # ── policy management ─────────────────────────────────────

    async def add_policy(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        library_id: str,
        request: AddPolicyRequest,
    ) -> list[LibraryPolicyResponse]:
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            await self._repository.add_policy(
                conn,
                library_id=library_id,
                policy_id=request.policy_id,
                sort_order=request.sort_order,
                created_by=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            policies = await self._repository.list_library_policies(conn, library_id)
        return [_policy_response(p) for p in policies]

    async def remove_policy(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        library_id: str,
        policy_id: str,
    ) -> None:
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            removed = await self._repository.remove_policy(conn, library_id, policy_id)
            if not removed:
                raise NotFoundError(
                    f"Policy '{policy_id}' not found in library '{library_id}'"
                )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def list_library_policies(
        self, *, user_id: str, library_id: str
    ) -> list[LibraryPolicyResponse]:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
            policies = await self._repository.list_library_policies(conn, library_id)
        return [_policy_response(p) for p in policies]

    # ── connector type mapping ────────────────────────────────

    async def add_connector_type_mapping(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        library_id: str,
        request: AddConnectorTypeMappingRequest,
    ) -> None:
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_library_by_id(conn, library_id)
            if record is None:
                raise NotFoundError(f"Library '{library_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            await self._repository.add_connector_type_mapping(
                conn,
                library_id=library_id,
                connector_type_code=request.connector_type_code,
                asset_version_id=request.asset_version_id,
                is_recommended=request.is_recommended,
                created_by=user_id,
            )

    # ── recommended libraries ─────────────────────────────────

    async def get_recommended_libraries(
        self,
        *,
        user_id: str,
        connector_type_code: str,
        asset_version_id: str | None = None,
    ) -> list[RecommendedLibraryResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            records = await self._repository.list_recommended_libraries(
                conn, connector_type_code, asset_version_id,
            )
        return [
            RecommendedLibraryResponse(
                library_id=r.library_id,
                library_code=r.library_code,
                library_name=r.library_name,
                library_type_code=r.library_type_code,
                is_recommended=r.is_recommended,
                connector_type_code=r.connector_type_code,
                asset_version_code=r.asset_version_code,
            )
            for r in records
        ]


def _library_response(r) -> LibraryResponse:
    return LibraryResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        library_code=r.library_code,
        library_type_code=r.library_type_code,
        library_type_name=r.library_type_name,
        version_number=r.version_number,
        is_published=r.is_published,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
        policy_count=r.policy_count,
    )


def _policy_response(r) -> LibraryPolicyResponse:
    return LibraryPolicyResponse(
        id=r.id,
        library_id=r.library_id,
        policy_id=r.policy_id,
        policy_code=r.policy_code,
        policy_name=r.policy_name,
        sort_order=r.sort_order,
    )
