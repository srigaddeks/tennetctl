from __future__ import annotations

import json
from importlib import import_module

from .repository import AssessmentTypesRepository

_schemas_module = import_module("backend.09_assessments.schemas")
DimensionItemResponse = _schemas_module.DimensionItemResponse
DimensionListResponse = _schemas_module.DimensionListResponse

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

_CACHE_KEY_ASSESSMENT_TYPES = "as:assessment_types:list"
_CACHE_KEY_ASSESSMENT_STATUSES = "as:assessment_statuses:list"
_CACHE_KEY_FINDING_SEVERITIES = "as:finding_severities:list"
_CACHE_KEY_FINDING_STATUSES = "as:finding_statuses:list"
_CACHE_TTL_DIMENSIONS = 3600  # 1 hour (static dimension data)


@instrument_class_methods(
    namespace="assessments.types.service",
    logger_name="backend.assessments.types.instrumentation",
)
class AssessmentTypesService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AssessmentTypesRepository()
        self._logger = get_logger("backend.assessments.types")

    async def list_assessment_types(self) -> DimensionListResponse:
        cached = await self._cache.get(_CACHE_KEY_ASSESSMENT_TYPES)
        if cached is not None:
            items = json.loads(cached)
            return DimensionListResponse(items=[DimensionItemResponse(**i) for i in items])

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_assessment_types(conn)
        result = [
            DimensionItemResponse(
                id=r.id,
                code=r.code,
                name=r.name,
                description=r.description,
                sort_order=r.sort_order,
                is_active=r.is_active,
            )
            for r in records
        ]
        await self._cache.set(
            _CACHE_KEY_ASSESSMENT_TYPES,
            json.dumps([i.model_dump() for i in result]),
            _CACHE_TTL_DIMENSIONS,
        )
        return DimensionListResponse(items=result)

    async def list_assessment_statuses(self) -> DimensionListResponse:
        cached = await self._cache.get(_CACHE_KEY_ASSESSMENT_STATUSES)
        if cached is not None:
            items = json.loads(cached)
            return DimensionListResponse(items=[DimensionItemResponse(**i) for i in items])

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_assessment_statuses(conn)
        result = [
            DimensionItemResponse(
                id=r.id,
                code=r.code,
                name=r.name,
                description=r.description,
                sort_order=r.sort_order,
                is_active=r.is_active,
            )
            for r in records
        ]
        await self._cache.set(
            _CACHE_KEY_ASSESSMENT_STATUSES,
            json.dumps([i.model_dump() for i in result]),
            _CACHE_TTL_DIMENSIONS,
        )
        return DimensionListResponse(items=result)

    async def list_finding_severities(self) -> DimensionListResponse:
        cached = await self._cache.get(_CACHE_KEY_FINDING_SEVERITIES)
        if cached is not None:
            items = json.loads(cached)
            return DimensionListResponse(items=[DimensionItemResponse(**i) for i in items])

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_finding_severities(conn)
        result = [
            DimensionItemResponse(
                id=r.id,
                code=r.code,
                name=r.name,
                description=r.description,
                sort_order=r.sort_order,
                is_active=r.is_active,
            )
            for r in records
        ]
        await self._cache.set(
            _CACHE_KEY_FINDING_SEVERITIES,
            json.dumps([i.model_dump() for i in result]),
            _CACHE_TTL_DIMENSIONS,
        )
        return DimensionListResponse(items=result)

    async def list_finding_statuses(self) -> DimensionListResponse:
        cached = await self._cache.get(_CACHE_KEY_FINDING_STATUSES)
        if cached is not None:
            items = json.loads(cached)
            return DimensionListResponse(items=[DimensionItemResponse(**i) for i in items])

        async with self._database_pool.acquire() as conn:
            records = await self._repository.list_finding_statuses(conn)
        result = [
            DimensionItemResponse(
                id=r.id,
                code=r.code,
                name=r.name,
                description=r.description,
                sort_order=r.sort_order,
                is_active=r.is_active,
            )
            for r in records
        ]
        await self._cache.set(
            _CACHE_KEY_FINDING_STATUSES,
            json.dumps([i.model_dump() for i in result]),
            _CACHE_TTL_DIMENSIONS,
        )
        return DimensionListResponse(items=result)
