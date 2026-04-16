from __future__ import annotations

import re
from importlib import import_module

from .repository import ProviderRepository
from .schemas import (
    ProviderConfigSchemaFieldSchema,
    ProviderDefinitionSchema,
    ProviderListResponse,
    ProviderVersionSchema,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
require_permission = _perm_check_module.require_permission

_CACHE_KEY_PREFIX = "sb:providers"
_CACHE_TTL = 600  # 10 minutes — provider definitions are largely static


@instrument_class_methods(
    namespace="sandbox.providers.service",
    logger_name="backend.sandbox.providers.instrumentation",
)
class ProviderService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ProviderRepository()
        self._logger = get_logger("backend.sandbox.providers")

    async def list_providers(
        self,
        *,
        user_id: str,
    ) -> ProviderListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")

            cache_key = f"{_CACHE_KEY_PREFIX}:list"
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return ProviderListResponse(**cached)

            records = await self._repository.list_providers(conn, is_active=True)

        items = [_provider_schema(r) for r in records]
        result = ProviderListResponse(items=items, total=len(items))
        await self._cache.set_json(
            cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL
        )
        return result

    async def get_provider(
        self,
        *,
        user_id: str,
        code: str,
    ) -> ProviderDefinitionSchema:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            record = await self._repository.get_provider(conn, code)
        if record is None:
            raise NotFoundError(f"Provider '{code}' not found")
        return _provider_schema(record)

    async def list_provider_versions(
        self,
        *,
        user_id: str,
        provider_code: str,
    ) -> list[ProviderVersionSchema]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            provider = await self._repository.get_provider(conn, provider_code)
            if provider is None:
                raise NotFoundError(f"Provider '{provider_code}' not found")
            records = await self._repository.list_provider_versions(conn, provider_code)
        return [_version_schema(r) for r in records]

    async def validate_connection_config(
        self,
        *,
        provider_code: str,
        config: dict,
        version_code: str | None = None,
    ) -> list[str]:
        async with self._database_pool.acquire() as conn:
            provider = await self._repository.get_provider(conn, provider_code)
            if provider is None:
                return [f"Unknown provider '{provider_code}'"]

            version_override: dict | None = None
            if version_code is not None:
                version = await self._repository.get_provider_version(
                    conn, provider_code, version_code
                )
                if version is not None:
                    version_override = version.config_schema_override

        schema_fields = provider.effective_schema(version_override)
        errors: list[str] = []

        for schema_field in schema_fields:
            value = config.get(schema_field.key)

            if schema_field.required and (value is None or value == ""):
                errors.append(f"Field '{schema_field.key}' is required")
                continue

            if value is not None and schema_field.validation:
                try:
                    if not re.fullmatch(schema_field.validation, str(value)):
                        errors.append(
                            f"Field '{schema_field.key}' failed validation: "
                            f"value does not match pattern '{schema_field.validation}'"
                        )
                except re.error:
                    pass  # Invalid regex in schema — skip pattern check

        return errors


def _provider_schema(record) -> ProviderDefinitionSchema:
    fields = record.effective_schema()
    config_fields = [
        ProviderConfigSchemaFieldSchema(
            key=f.key,
            label=f.label,
            type=f.type,
            required=f.required,
            credential=f.credential,
            placeholder=f.placeholder,
            hint=f.hint,
            validation=f.validation,
            default=f.default,
            order=f.order,
        )
        for f in fields
    ]
    return ProviderDefinitionSchema(
        id=record.id,
        code=record.code,
        name=record.name,
        driver_module=record.driver_module,
        default_auth_method=record.default_auth_method,
        supports_log_collection=record.supports_log_collection,
        supports_steampipe=record.supports_steampipe,
        supports_custom_driver=record.supports_custom_driver,
        steampipe_plugin=record.steampipe_plugin,
        rate_limit_rpm=record.rate_limit_rpm,
        is_active=record.is_active,
        is_coming_soon=record.is_coming_soon,
        created_at=record.created_at,
        updated_at=record.updated_at,
        config_fields=config_fields,
    )


def _version_schema(record) -> ProviderVersionSchema:
    return ProviderVersionSchema(
        id=record.id,
        provider_code=record.provider_code,
        version_code=record.version_code,
        name=record.name,
        config_schema_override=record.config_schema_override,
        is_active=record.is_active,
        is_default=record.is_default,
        created_at=record.created_at,
    )
