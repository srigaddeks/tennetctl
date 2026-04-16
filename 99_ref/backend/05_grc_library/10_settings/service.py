from __future__ import annotations

import uuid
from importlib import import_module

from .repository import FrameworkSettingRepository
from .schemas import (
    FrameworkSettingListResponse,
    FrameworkSettingResponse,
    SetFrameworkSettingRequest,
)

_framework_repo_module = import_module("backend.05_grc_library.02_frameworks.repository")
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
FrameworkRepository = _framework_repo_module.FrameworkRepository

_CACHE_TTL_SETTINGS = 300


@instrument_class_methods(namespace="grc.settings.service", logger_name="backend.grc.settings.instrumentation")
class FrameworkSettingService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = FrameworkSettingRepository()
        self._framework_repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.settings")

    async def _require_framework_permission(
        self,
        conn,
        *,
        user_id: str,
        framework_id: str,
        permission_code: str,
    ) -> None:
        framework = await self._framework_repository.get_framework_by_id(conn, framework_id)
        if framework is None:
            raise NotFoundError(f"Framework '{framework_id}' not found")
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=framework.scope_org_id,
            scope_workspace_id=framework.scope_workspace_id,
        )

    async def list_settings(self, *, user_id: str, framework_id: str) -> FrameworkSettingListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_framework_permission(
                conn,
                user_id=user_id,
                framework_id=framework_id,
                permission_code="frameworks.view",
            )
            records = await self._repository.list_settings(conn, framework_id=framework_id)
        items = [_setting_response(r) for r in records]
        return FrameworkSettingListResponse(items=items, total=len(items))

    async def set_setting(
        self, *, user_id: str, tenant_key: str, framework_id: str, setting_key: str,
        request: SetFrameworkSettingRequest
    ) -> FrameworkSettingResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    framework_id=framework_id,
                    permission_code="frameworks.update",
                )
                record = await self._repository.upsert_setting(
                    conn,
                    framework_id=framework_id,
                    setting_key=setting_key,
                    setting_value=request.setting_value,
                    created_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_setting",
                        entity_id=framework_id,
                        event_type=FrameworkAuditEventType.SETTING_UPDATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "setting_key": setting_key,
                            "setting_value": request.setting_value,
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        return _setting_response(record)

    async def delete_setting(
        self, *, user_id: str, tenant_key: str, framework_id: str, setting_key: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    framework_id=framework_id,
                    permission_code="frameworks.update",
                )
                deleted = await self._repository.delete_setting(
                    conn, framework_id=framework_id, setting_key=setting_key,
                )
                if not deleted:
                    raise NotFoundError(f"Setting '{setting_key}' not found for framework '{framework_id}'")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_setting",
                        entity_id=framework_id,
                        event_type=FrameworkAuditEventType.SETTING_DELETED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"setting_key": setting_key},
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")


def _setting_response(r) -> FrameworkSettingResponse:
    return FrameworkSettingResponse(
        id=r.id,
        framework_id=r.framework_id,
        setting_key=r.setting_key,
        setting_value=r.setting_value,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
