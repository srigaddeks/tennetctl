from __future__ import annotations

import json
from importlib import import_module

from .repository import SandboxDimensionRepository
from .schemas import SandboxDimensionResponse, AssetVersionResponse, ConnectorConfigSchemaResponse, ConnectorConfigField

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
require_permission = _perm_check_module.require_permission

_CACHE_TTL_DIMENSIONS = 3600  # 1 hour (static dimension data)
_SCHEMA = '"15_sandbox"'


@instrument_class_methods(namespace="sandbox.dimensions.service", logger_name="backend.sandbox.dimensions.instrumentation")
class SandboxDimensionService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = SandboxDimensionRepository()
        self._logger = get_logger("backend.sandbox.dimensions")

    async def _require_sandbox_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
        workspace_id: str | None = None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def list_dimension(
        self,
        *,
        dimension_name: str,
        filter_code: str | None = None,
    ) -> list[SandboxDimensionResponse]:
        cache_suffix = f":{filter_code}" if filter_code else ""
        cache_key = f"sb:dimensions:{dimension_name}{cache_suffix}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            items = json.loads(cached)
            return [SandboxDimensionResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_dimension(
                conn, dimension_name=dimension_name, filter_code=filter_code,
            )
        result = [
            SandboxDimensionResponse(
                id=r.id,
                code=r.code,
                name=r.name,
                description=r.description,
                sort_order=r.sort_order,
                is_active=r.is_active,
            )
            for r in records
        ]
        await self._cache.set(cache_key, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result

    async def list_asset_versions(
        self,
        *,
        connector_type_code: str | None = None,
    ) -> list[AssetVersionResponse]:
        cache_suffix = f":{connector_type_code}" if connector_type_code else ""
        cache_key = f"sb:dimensions:asset_versions{cache_suffix}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            items = json.loads(cached)
            return [AssetVersionResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_asset_versions(
                conn, connector_type_code=connector_type_code,
            )
        result = [
            AssetVersionResponse(
                id=r.id,
                connector_type_code=r.connector_type_code,
                version_code=r.version_code,
                version_label=r.version_label,
                is_latest=r.is_latest,
                is_active=r.is_active,
                sort_order=r.sort_order,
            )
            for r in records
        ]
        await self._cache.set(cache_key, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result

    async def get_connector_config_schema(
        self,
        *,
        connector_type_code: str,
    ) -> ConnectorConfigSchemaResponse | None:
        cache_key = f"sb:connector_schema:{connector_type_code}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            import json as _json
            data = _json.loads(cached)
            return ConnectorConfigSchemaResponse(**data)

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_connector_config_schema(
                conn, connector_type_code=connector_type_code,
            )
        if not record:
            return None

        fields = [
            ConnectorConfigField(**f)
            for f in sorted(record.config_schema.get("fields", []), key=lambda x: x.get("order", 0))
        ]
        result = ConnectorConfigSchemaResponse(
            connector_type_code=record.connector_type_code,
            fields=fields,
            supports_steampipe=record.supports_steampipe,
            steampipe_plugin=record.steampipe_plugin,
        )
        import json as _json
        await self._cache.set(cache_key, _json.dumps(result.model_dump()), _CACHE_TTL_DIMENSIONS)
        return result

    async def get_sandbox_stats(self, *, user_id: str, org_id: str) -> dict:
        """Return aggregate counts for the sandbox dashboard."""
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            stats = {}
            for table, schema, key in [
                ('"20_fct_connector_instances"', _SCHEMA, "connector_count"),
                ('"21_fct_datasets"', _SCHEMA, "dataset_count"),
                ('"22_fct_signals"', _SCHEMA, "signal_count"),
                ('"23_fct_threat_types"', _SCHEMA, "threat_type_count"),
                ('"24_fct_policies"', _SCHEMA, "policy_count"),
                ('"29_fct_libraries"', _SCHEMA, "library_count"),
            ]:
                row = await conn.fetchrow(
                    f'SELECT count(*) AS cnt FROM {schema}.{table} WHERE org_id = $1 AND is_deleted = FALSE',
                    org_id,
                )
                stats[key] = row["cnt"]
            # Active policies
            row = await conn.fetchrow(
                f'SELECT count(*) AS cnt FROM {_SCHEMA}."24_fct_policies" WHERE org_id = $1 AND is_deleted = FALSE AND is_enabled = TRUE',
                org_id,
            )
            stats["active_policy_count"] = row["cnt"]
            # Recent collection runs (last 24h)
            row = await conn.fetchrow(
                f"SELECT count(*) AS cnt FROM {_SCHEMA}.\"35_fct_collection_runs\" WHERE org_id = $1 AND created_at > NOW() - INTERVAL '24 hours'",
                org_id,
            )
            stats["recent_run_count_24h"] = row["cnt"]
            # Active live sessions
            row = await conn.fetchrow(
                f'SELECT count(*) AS cnt FROM {_SCHEMA}."28_fct_live_sessions" WHERE org_id = $1 AND session_status IN (\'starting\', \'active\', \'paused\')',
                org_id,
            )
            stats["active_session_count"] = row["cnt"]
            return stats
