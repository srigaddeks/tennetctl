from __future__ import annotations
from importlib import import_module
from .repository import ReportingRepository
from .schemas import AISummaryResponse, AgentRunStats

_telemetry_module = import_module("backend.01_core.telemetry")
_logging_module = import_module("backend.01_core.logging_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
require_permission = _perm_check_module.require_permission

@instrument_class_methods(namespace="ai.reporting.service", logger_name="backend.ai.reporting.instrumentation")
class ReportingService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ReportingRepository()
        self._logger = get_logger("backend.ai.reporting")

    async def get_summary(self, *, caller_id: str, tenant_key: str) -> AISummaryResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.view")
            data = await self._repository.get_summary(conn, tenant_key=tenant_key)
        return AISummaryResponse(**{k: v for k, v in data.items()})

    async def get_agent_run_stats(self, *, caller_id: str, tenant_key: str) -> list[AgentRunStats]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, caller_id, "ai_copilot.view")
            rows = await self._repository.get_agent_run_stats(conn, tenant_key=tenant_key)
        return [AgentRunStats(**r) for r in rows]
