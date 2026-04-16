from __future__ import annotations

import uuid
from importlib import import_module

from .repository import VersionRepository
from .schemas import (
    CreateVersionRequest,
    VersionListResponse,
    VersionResponse,
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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
FrameworkAuditEventType = _constants_module.FrameworkAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
FrameworkRepository = _frameworks_repo_module.FrameworkRepository

_CACHE_TTL_VERSIONS = 300


@instrument_class_methods(
    namespace="grc.versions.service", logger_name="backend.grc.versions.instrumentation"
)
class VersionService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = VersionRepository()
        self._framework_repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.versions")

    async def _get_framework_or_not_found(self, conn, framework_id: str):
        framework = await self._framework_repository.get_framework_by_id(
            conn, framework_id
        )
        if framework is None:
            raise NotFoundError(f"Framework '{framework_id}' not found")
        return framework

    async def _require_version_view_permission(
        self,
        conn,
        *,
        user_id: str,
        framework,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
    ) -> None:
        permission_scope_org_id = framework.scope_org_id
        permission_scope_workspace_id = framework.scope_workspace_id

        # Approved marketplace frameworks are visible to regular org/workspace users.
        # Use the caller's active scope for authorization in that case instead of the
        # framework's platform scope, which would otherwise require platform-level access.
        if framework.is_marketplace_visible and framework.approval_status == "approved":
            permission_scope_org_id = scope_org_id
            permission_scope_workspace_id = scope_workspace_id

        await require_permission(
            conn,
            user_id,
            "frameworks.view",
            scope_org_id=permission_scope_org_id,
            scope_workspace_id=permission_scope_workspace_id,
        )

    async def list_versions(
        self,
        *,
        user_id: str,
        framework_id: str,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
    ) -> VersionListResponse:
        async with self._database_pool.acquire() as conn:
            framework = await self._get_framework_or_not_found(conn, framework_id)
            await self._require_version_view_permission(
                conn,
                user_id=user_id,
                framework=framework,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            records = await self._repository.list_versions(
                conn, framework_id=framework_id
            )
        items = [_version_response(r) for r in records]
        return VersionListResponse(items=items, total=len(items))

    async def get_version(
        self,
        *,
        user_id: str,
        framework_id: str,
        version_id: str,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
    ) -> VersionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_version_by_id(conn, version_id)
            framework = await self._get_framework_or_not_found(conn, framework_id)
            await self._require_version_view_permission(
                conn,
                user_id=user_id,
                framework=framework,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
        if record is None or record.framework_id != framework_id:
            raise NotFoundError(f"Version '{version_id}' not found")
        return _version_response(record)

    async def create_version(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        request: CreateVersionRequest,
    ) -> VersionResponse:
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
                # Auto-generate version code as next semantic version
                next_version = await self._repository.next_version_number(
                    conn, framework_id=framework_id
                )
                version_code = next_version
                version = await self._repository.create_version(
                    conn,
                    version_id=str(uuid.uuid4()),
                    framework_id=framework_id,
                    version_code=version_code,
                    change_severity=request.change_severity,
                    previous_version_id=request.source_version_id,
                    created_by=user_id,
                    now=now,
                )
                props: dict[str, str] = {}
                if request.version_label:
                    props["version_label"] = request.version_label
                if request.release_notes:
                    props["release_notes"] = request.release_notes
                if request.change_summary:
                    props["change_summary"] = request.change_summary
                if props:
                    await self._repository.upsert_version_properties(
                        conn,
                        version_id=version.id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_version",
                        entity_id=version.id,
                        event_type=FrameworkAuditEventType.VERSION_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "version_code": version_code,
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        return _version_response(version)

    async def restore_version(
        self, *, user_id: str, tenant_key: str, framework_id: str, version_id: str
    ) -> VersionResponse:
        """Re-publish a deprecated/archived version by creating a new version that copies its state."""
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
                source = await self._repository.get_version_by_id(conn, version_id)
                if source is None or source.framework_id != framework_id:
                    raise NotFoundError(f"Version '{version_id}' not found")
                if source.lifecycle_state not in (
                    "published",
                    "deprecated",
                    "archived",
                ):
                    raise ConflictError(
                        "Only published or deprecated versions can be restored"
                    )
                # Auto-generate next version number for the restored copy
                next_version = await self._repository.next_version_number(
                    conn, framework_id=framework_id
                )
                new_version_code = next_version
                new_version = await self._repository.create_version(
                    conn,
                    version_id=str(uuid.uuid4()),
                    framework_id=framework_id,
                    version_code=new_version_code,
                    change_severity="minor",
                    previous_version_id=version_id,
                    created_by=user_id,
                    now=now,
                )
                # Immediately publish the new version
                await self._repository.snapshot_controls_to_version(
                    conn,
                    framework_id=framework_id,
                    version_id=new_version.id,
                    created_by=user_id,
                    now=now,
                )
                version = await self._repository.update_lifecycle_state(
                    conn,
                    new_version.id,
                    lifecycle_state="published",
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_version",
                        entity_id=version.id,
                        event_type=FrameworkAuditEventType.VERSION_PUBLISHED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "version_code": new_version_code,
                            "restored_from_version_id": version_id,
                            "restored_from_version_code": source.version_code,
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        return _version_response(version)

    async def publish_version(
        self, *, user_id: str, tenant_key: str, framework_id: str, version_id: str
    ) -> VersionResponse:
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
                record = await self._repository.get_version_by_id(conn, version_id)
                if record is None or record.framework_id != framework_id:
                    raise NotFoundError(f"Version '{version_id}' not found")
                if record.lifecycle_state != "draft":
                    raise ConflictError(
                        f"Version must be in 'draft' state to publish, currently '{record.lifecycle_state}'"
                    )
                # Snapshot controls
                await self._repository.snapshot_controls_to_version(
                    conn,
                    framework_id=framework_id,
                    version_id=version_id,
                    created_by=user_id,
                    now=now,
                )
                version = await self._repository.update_lifecycle_state(
                    conn,
                    version_id,
                    lifecycle_state="published",
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_version",
                        entity_id=version_id,
                        event_type=FrameworkAuditEventType.VERSION_PUBLISHED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "version_code": version.version_code,
                            "control_count": str(version.control_count),
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        return _version_response(version)

    async def deprecate_version(
        self, *, user_id: str, tenant_key: str, framework_id: str, version_id: str
    ) -> VersionResponse:
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
                record = await self._repository.get_version_by_id(conn, version_id)
                if record is None or record.framework_id != framework_id:
                    raise NotFoundError(f"Version '{version_id}' not found")
                if record.lifecycle_state != "published":
                    raise ConflictError(
                        f"Version must be 'published' to deprecate, currently '{record.lifecycle_state}'"
                    )
                version = await self._repository.update_lifecycle_state(
                    conn,
                    version_id,
                    lifecycle_state="deprecated",
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_version",
                        entity_id=version_id,
                        event_type=FrameworkAuditEventType.VERSION_DEPRECATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "version_code": version.version_code,
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        return _version_response(version)

    async def create_auto_version(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        change_type: str,
        change_summary: str | None = None,
    ) -> VersionResponse:
        """Create a new draft version automatically when framework content changes.

        Only creates a version if the framework is approved and no draft version exists.
        This prevents duplicate versions from rapid successive changes.
        """
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                framework = await self._get_framework_or_not_found(conn, framework_id)

                if framework.approval_status != "approved":
                    raise ConflictError(
                        f"Auto-versioning is only available for approved frameworks. "
                        f"Current status: '{framework.approval_status}'"
                    )

                existing_draft = await self._repository.has_draft_version(
                    conn, framework_id=framework_id
                )
                if existing_draft:
                    self._logger.info(
                        "Skipping auto-version for framework %s: draft version already exists",
                        framework_id,
                    )
                    return _version_response(existing_draft)

                next_version = await self._repository.next_version_number(
                    conn, framework_id=framework_id
                )
                version_code = next_version

                change_severity = self._determine_change_severity(change_type)

                version = await self._repository.create_version(
                    conn,
                    version_id=str(uuid.uuid4()),
                    framework_id=framework_id,
                    version_code=version_code,
                    change_severity=change_severity,
                    previous_version_id=None,
                    created_by=user_id,
                    now=now,
                )

                props: dict[str, str] = {
                    "auto_created": "true",
                    "auto_change_type": change_type,
                }
                if change_summary:
                    props["change_summary"] = change_summary
                    props["auto_change_summary"] = change_summary

                await self._repository.upsert_version_properties(
                    conn,
                    version_id=version.id,
                    properties=props,
                    created_by=user_id,
                    now=now,
                )

                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_version",
                        entity_id=version.id,
                        event_type=FrameworkAuditEventType.VERSION_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "version_code": version_code,
                            "auto_created": "true",
                            "change_type": change_type,
                        },
                    ),
                )

        await self._cache.delete_pattern("frameworks:list:*")
        return _version_response(version)

    @staticmethod
    def _determine_change_severity(change_type: str) -> str:
        """Determine version severity based on the type of change."""
        severity_map = {
            "requirement_added": "major",
            "requirement_removed": "major",
            "requirement_modified": "minor",
            "control_added": "minor",
            "control_removed": "minor",
            "control_modified": "patch",
            "framework_properties_changed": "patch",
        }
        return severity_map.get(change_type, "minor")


def _version_response(r) -> VersionResponse:
    return VersionResponse(
        id=r.id,
        framework_id=r.framework_id,
        version_code=r.version_code,
        change_severity=r.change_severity,
        lifecycle_state=r.lifecycle_state,
        control_count=r.control_count,
        previous_version_id=r.previous_version_id,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
        version_label=r.version_label,
        release_notes=r.release_notes,
        change_summary=r.change_summary,
    )
