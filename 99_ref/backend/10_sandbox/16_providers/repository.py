from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import ProviderDefinition, ProviderDefinitionProperty, ProviderVersion

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(
    namespace="sandbox.providers.repository",
    logger_name="backend.sandbox.providers.repository.instrumentation",
)
class ProviderRepository:

    async def list_providers(
        self,
        connection: asyncpg.Connection,
        *,
        is_active: bool = True,
    ) -> list[ProviderDefinition]:
        rows = await connection.fetch(
            f"""
            SELECT id, code, name, driver_module, default_auth_method,
                   supports_log_collection, supports_steampipe, supports_custom_driver,
                   steampipe_plugin, rate_limit_rpm, config_schema,
                   is_active, is_coming_soon, created_at::text, updated_at::text
            FROM {SCHEMA}."16_dim_provider_definitions"
            WHERE is_active = $1
            ORDER BY name ASC
            """,
            is_active,
        )
        return [_row_to_provider(r) for r in rows]

    async def get_provider(
        self,
        connection: asyncpg.Connection,
        code: str,
    ) -> ProviderDefinition | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, code, name, driver_module, default_auth_method,
                   supports_log_collection, supports_steampipe, supports_custom_driver,
                   steampipe_plugin, rate_limit_rpm, config_schema,
                   is_active, is_coming_soon, created_at::text, updated_at::text
            FROM {SCHEMA}."16_dim_provider_definitions"
            WHERE code = $1
            """,
            code,
        )
        return _row_to_provider(row) if row else None

    async def list_provider_versions(
        self,
        connection: asyncpg.Connection,
        provider_code: str,
    ) -> list[ProviderVersion]:
        rows = await connection.fetch(
            f"""
            SELECT id, provider_code, version_code, name,
                   config_schema_override, is_active, is_default, created_at::text
            FROM {SCHEMA}."17_dim_provider_versions"
            WHERE provider_code = $1
            ORDER BY is_default DESC, version_code ASC
            """,
            provider_code,
        )
        return [_row_to_version(r) for r in rows]

    async def get_provider_version(
        self,
        connection: asyncpg.Connection,
        provider_code: str,
        version_code: str,
    ) -> ProviderVersion | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, provider_code, version_code, name,
                   config_schema_override, is_active, is_default, created_at::text
            FROM {SCHEMA}."17_dim_provider_versions"
            WHERE provider_code = $1 AND version_code = $2
            """,
            provider_code,
            version_code,
        )
        return _row_to_version(row) if row else None

    async def list_provider_properties(
        self,
        connection: asyncpg.Connection,
        provider_code: str,
    ) -> list[ProviderDefinitionProperty]:
        rows = await connection.fetch(
            f"""
            SELECT provider_code, meta_key, meta_value
            FROM {SCHEMA}."56_dtl_provider_definition_properties"
            WHERE provider_code = $1
            ORDER BY meta_key ASC
            """,
            provider_code,
        )
        return [_row_to_property(r) for r in rows]


def _row_to_provider(r) -> ProviderDefinition:
    d = dict(r)
    return ProviderDefinition(
        id=d["id"],
        code=d["code"],
        name=d["name"],
        driver_module=d["driver_module"],
        default_auth_method=d["default_auth_method"],
        supports_log_collection=d["supports_log_collection"],
        supports_steampipe=d["supports_steampipe"],
        supports_custom_driver=d["supports_custom_driver"],
        steampipe_plugin=d["steampipe_plugin"],
        rate_limit_rpm=d["rate_limit_rpm"],
        config_schema=d["config_schema"] if isinstance(d["config_schema"], dict) else {},
        is_active=d["is_active"],
        is_coming_soon=d["is_coming_soon"],
        created_at=d["created_at"],
        updated_at=d["updated_at"],
    )


def _row_to_version(r) -> ProviderVersion:
    d = dict(r)
    return ProviderVersion(
        id=d["id"],
        provider_code=d["provider_code"],
        version_code=d["version_code"],
        name=d["name"],
        config_schema_override=d["config_schema_override"]
        if isinstance(d.get("config_schema_override"), dict)
        else None,
        is_active=d["is_active"],
        is_default=d["is_default"],
        created_at=d["created_at"],
    )


def _row_to_property(r) -> ProviderDefinitionProperty:
    d = dict(r)
    return ProviderDefinitionProperty(
        provider_code=d["provider_code"],
        meta_key=d["meta_key"],
        meta_value=d["meta_value"],
    )
