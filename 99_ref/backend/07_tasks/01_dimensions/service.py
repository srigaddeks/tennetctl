from __future__ import annotations

import json
from importlib import import_module

from .repository import DimensionRepository
from .schemas import TaskPriorityResponse, TaskStatusResponse, TaskTypeResponse

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

_CACHE_KEY_TASK_TYPES = "task_types:list"
_CACHE_KEY_TASK_PRIORITIES = "task_priorities:list"
_CACHE_KEY_TASK_STATUSES = "task_statuses:list"
_CACHE_TTL_DIMENSIONS = 3600  # 1 hour (static dimension data)


@instrument_class_methods(namespace="tasks.dimensions.service", logger_name="backend.tasks.dimensions.instrumentation")
class DimensionService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = DimensionRepository()
        self._logger = get_logger("backend.tasks.dimensions")

    async def list_task_types(self) -> list[TaskTypeResponse]:
        cached = await self._cache.get(_CACHE_KEY_TASK_TYPES)
        if cached is not None:
            items = json.loads(cached)
            return [TaskTypeResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            types = await self._repository.list_task_types(conn)
        result = [TaskTypeResponse(code=t.code, name=t.name, description=t.description, sort_order=t.sort_order) for t in types]
        await self._cache.set(_CACHE_KEY_TASK_TYPES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result

    async def list_task_priorities(self) -> list[TaskPriorityResponse]:
        cached = await self._cache.get(_CACHE_KEY_TASK_PRIORITIES)
        if cached is not None:
            items = json.loads(cached)
            return [TaskPriorityResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            priorities = await self._repository.list_task_priorities(conn)
        result = [TaskPriorityResponse(code=p.code, name=p.name, description=p.description, sort_order=p.sort_order) for p in priorities]
        await self._cache.set(_CACHE_KEY_TASK_PRIORITIES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result

    async def list_task_statuses(self) -> list[TaskStatusResponse]:
        cached = await self._cache.get(_CACHE_KEY_TASK_STATUSES)
        if cached is not None:
            items = json.loads(cached)
            return [TaskStatusResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            statuses = await self._repository.list_task_statuses(conn)
        result = [TaskStatusResponse(code=s.code, name=s.name, description=s.description, is_terminal=s.is_terminal, sort_order=s.sort_order) for s in statuses]
        await self._cache.set(_CACHE_KEY_TASK_STATUSES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_DIMENSIONS)
        return result
