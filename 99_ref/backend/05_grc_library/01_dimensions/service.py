from __future__ import annotations

import json
from importlib import import_module

from .repository import DimensionRepository
from .schemas import DimensionResponse

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods

_CACHE_TTL_DIMENSIONS = 3600  # 1 hour (static dimension data)


@instrument_class_methods(namespace="grc.dimensions.service", logger_name="backend.grc.dimensions.instrumentation")
class DimensionService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = DimensionRepository()
        self._logger = get_logger("backend.grc.dimensions")

    async def list_dimension(self, *, dimension_name: str) -> list[DimensionResponse]:
        cache_key = f"grc:{dimension_name}:list"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            items = json.loads(cached)
            return [DimensionResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_dimension(conn, dimension_name=dimension_name)
        result = [
            DimensionResponse(
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
