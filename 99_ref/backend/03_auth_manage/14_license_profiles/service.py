from __future__ import annotations

from importlib import import_module
from uuid import uuid4

from .repository import LicenseProfileRepository
from .schemas import (
    CreateLicenseProfileRequest,
    LicenseProfileListResponse,
    LicenseProfileResponse,
    LicenseProfileSettingResponse,
    UpdateLicenseProfileRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_time_module = import_module("backend.01_core.time_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

import asyncpg

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
require_permission = _perm_check_module.require_permission
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY = "license_profiles:list"
_CACHE_TTL = 600


@instrument_class_methods(namespace="license_profiles.service", logger_name="backend.license_profiles")
class LicenseProfileService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repo = LicenseProfileRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")

    async def list_profiles(self, *, actor_id: str) -> LicenseProfileListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.view")

        cached = await self._cache.get(_CACHE_KEY)
        if cached is not None:
            return LicenseProfileListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            profiles = await self._repo.list_profiles(conn)
            # Load settings for each profile
            for p in profiles:
                settings = await self._repo.list_profile_settings(conn, p["id"])
                p["settings"] = settings

        result = LicenseProfileListResponse(
            profiles=[
                LicenseProfileResponse(
                    id=p["id"], code=p["code"], name=p["name"], description=p["description"],
                    tier=p["tier"], is_active=p["is_active"], sort_order=p["sort_order"],
                    settings=[LicenseProfileSettingResponse(key=s["key"], value=s["value"]) for s in p.get("settings", [])],
                    org_count=p.get("org_count", 0),
                    created_at=p["created_at"], updated_at=p["updated_at"],
                )
                for p in profiles
            ]
        )
        await self._cache.set(_CACHE_KEY, result.model_dump_json(), _CACHE_TTL)
        return result

    async def create_profile(
        self, payload: CreateLicenseProfileRequest, *, actor_id: str,
        client_ip: str | None, session_id: str | None,
    ) -> LicenseProfileResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.create")
            try:
                profile = await self._repo.create_profile(
                    conn, code=payload.code, name=payload.name,
                    description=payload.description, tier=payload.tier,
                    sort_order=payload.sort_order, now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError(f"Profile '{payload.code}' already exists.")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()), tenant_key=self._settings.default_tenant_key,
                    entity_type="license_profile", entity_id=profile["id"],
                    event_type="license_profile_created", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={"code": payload.code, "name": payload.name},
                ),
            )
        await self._cache.delete(_CACHE_KEY)
        return LicenseProfileResponse(
            id=profile["id"], code=profile["code"], name=profile["name"],
            description=profile["description"], tier=profile["tier"],
            is_active=profile["is_active"], sort_order=profile["sort_order"], settings=[],
            created_at=profile["created_at"], updated_at=profile["updated_at"],
        )

    async def update_profile(
        self, code: str, payload: UpdateLicenseProfileRequest, *, actor_id: str,
        client_ip: str | None, session_id: str | None,
    ) -> LicenseProfileResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.update")
            profile = await self._repo.update_profile(
                conn, code=code, name=payload.name, description=payload.description,
                tier=payload.tier, is_active=payload.is_active, sort_order=payload.sort_order, now=now,
            )
            if profile is None:
                raise NotFoundError(f"Profile '{code}' not found.")
            settings = await self._repo.list_profile_settings(conn, profile["id"])
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()), tenant_key=self._settings.default_tenant_key,
                    entity_type="license_profile", entity_id=profile["id"],
                    event_type="license_profile_updated", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={"code": code},
                ),
            )
        await self._cache.delete(_CACHE_KEY)
        return LicenseProfileResponse(
            id=profile["id"], code=profile["code"], name=profile["name"],
            description=profile["description"], tier=profile["tier"],
            is_active=profile["is_active"], sort_order=profile["sort_order"],
            settings=[LicenseProfileSettingResponse(key=s["key"], value=s["value"]) for s in settings],
            created_at=profile["created_at"], updated_at=profile["updated_at"],
        )

    async def set_setting(
        self, code: str, key: str, value: str, *, actor_id: str,
        client_ip: str | None, session_id: str | None,
    ) -> LicenseProfileSettingResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.update")
            profile = await self._repo.get_profile(conn, code)
            if profile is None:
                raise NotFoundError(f"Profile '{code}' not found.")
            await self._repo.set_profile_setting(conn, profile_id=profile["id"], key=key, value=value, now=now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()), tenant_key=self._settings.default_tenant_key,
                    entity_type="license_profile", entity_id=profile["id"],
                    event_type="license_profile_setting_updated", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={"code": code, "setting_key": key, "setting_value": value},
                ),
            )
        await self._cache.delete(_CACHE_KEY)
        return LicenseProfileSettingResponse(key=key, value=value)

    async def delete_setting(
        self, code: str, key: str, *, actor_id: str,
        client_ip: str | None, session_id: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, actor_id, "feature_flag_registry.update")
            profile = await self._repo.get_profile(conn, code)
            if profile is None:
                raise NotFoundError(f"Profile '{code}' not found.")
            deleted = await self._repo.delete_profile_setting(conn, profile_id=profile["id"], key=key)
            if not deleted:
                raise NotFoundError(f"Setting '{key}' not found on profile '{code}'.")
        await self._cache.delete(_CACHE_KEY)
