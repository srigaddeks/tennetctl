from __future__ import annotations

from importlib import import_module

from .repository import DimensionsRepository
from .schemas import RiskCategoryResponse, RiskLevelResponse, RiskTreatmentTypeResponse

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

_CACHE_KEY_RISK_CATEGORIES = "rr:risk_categories:list"
_CACHE_KEY_TREATMENT_TYPES = "rr:treatment_types:list"
_CACHE_KEY_RISK_LEVELS = "rr:risk_levels:list"
_CACHE_TTL_DIMENSIONS = 3600  # 1 hour (static dimension data)


@instrument_class_methods(namespace="risk.dimensions.service", logger_name="backend.risk.dimensions.instrumentation")
class DimensionsService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = DimensionsRepository()
        self._logger = get_logger("backend.risk.dimensions")

    async def list_risk_categories(self) -> list[RiskCategoryResponse]:
        cached = await self._cache.get(_CACHE_KEY_RISK_CATEGORIES)
        if cached is not None:
            import json
            items = json.loads(cached)
            return [RiskCategoryResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_risk_categories(conn)
        result = [RiskCategoryResponse(
            code=r.code, name=r.name, description=r.description,
            sort_order=r.sort_order, is_active=r.is_active,
        ) for r in records]
        import json
        await self._cache.set(_CACHE_KEY_RISK_CATEGORIES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result

    async def list_treatment_types(self) -> list[RiskTreatmentTypeResponse]:
        cached = await self._cache.get(_CACHE_KEY_TREATMENT_TYPES)
        if cached is not None:
            import json
            items = json.loads(cached)
            return [RiskTreatmentTypeResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_treatment_types(conn)
        result = [RiskTreatmentTypeResponse(
            code=r.code, name=r.name, description=r.description,
            sort_order=r.sort_order, is_active=r.is_active,
        ) for r in records]
        import json
        await self._cache.set(_CACHE_KEY_TREATMENT_TYPES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result

    async def list_risk_levels(self) -> list[RiskLevelResponse]:
        cached = await self._cache.get(_CACHE_KEY_RISK_LEVELS)
        if cached is not None:
            import json
            items = json.loads(cached)
            return [RiskLevelResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_risk_levels(conn)
        result = [RiskLevelResponse(
            code=r.code, name=r.name, description=r.description,
            score_min=r.score_min, score_max=r.score_max, color_hex=r.color_hex,
            sort_order=r.sort_order, is_active=r.is_active,
        ) for r in records]
        import json
        await self._cache.set(_CACHE_KEY_RISK_LEVELS, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result
