from __future__ import annotations

from importlib import import_module

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_telemetry_module = import_module("backend.01_core.telemetry")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
instrument_class_methods = _telemetry_module.instrument_class_methods

SCHEMA = '"25_agent_sandbox"'
_CACHE_KEY_PREFIX = "asb:dimensions"
_CACHE_TTL = 3600

_DIMENSION_TABLES = {
    "agent_statuses": "02_dim_agent_statuses",
    "tool_types": "03_dim_tool_types",
    "scenario_types": "04_dim_scenario_types",
    "evaluation_methods": "05_dim_evaluation_methods",
    "execution_statuses": "06_dim_execution_statuses",
}


@instrument_class_methods(namespace="agent_sandbox.dimensions.service", logger_name="backend.agent_sandbox.dimensions.instrumentation")
class AgentSandboxDimensionService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache

    async def list_dimension(self, *, dimension_name: str) -> list[dict]:
        cache_key = f"{_CACHE_KEY_PREFIX}:{dimension_name}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        table = _DIMENSION_TABLES.get(dimension_name)
        if table is None:
            return []

        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id::text, code, name, description, sort_order
                FROM {SCHEMA}."{table}"
                ORDER BY sort_order, code
                """
            )
        result = [dict(r) for r in rows]
        await self._cache.set(cache_key, result, ttl=_CACHE_TTL)
        return result

    async def get_stats(self, *, user_id: str, org_id: str) -> dict:
        async with self._database_pool.acquire() as conn:
            agents_row = await conn.fetchrow(
                f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."20_fct_agents" WHERE org_id = $1 AND is_deleted = FALSE',
                org_id,
            )
            tools_row = await conn.fetchrow(
                f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."21_fct_agent_tools" WHERE org_id = $1 AND is_deleted = FALSE',
                org_id,
            )
            runs_row = await conn.fetchrow(
                f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."70_fct_agent_runs" WHERE org_id = $1',
                org_id,
            )
            scenarios_row = await conn.fetchrow(
                f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."22_fct_test_scenarios" WHERE org_id = $1 AND is_deleted = FALSE',
                org_id,
            )
        return {
            "agents": agents_row["total"] if agents_row else 0,
            "tools": tools_row["total"] if tools_row else 0,
            "runs": runs_row["total"] if runs_row else 0,
            "test_scenarios": scenarios_row["total"] if scenarios_row else 0,
        }
