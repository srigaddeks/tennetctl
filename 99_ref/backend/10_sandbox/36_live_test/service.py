from __future__ import annotations

import asyncio
from importlib import import_module

from .schemas import LiveTestResponse, LiveTestResultItem

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_asset_repo_module = import_module("backend.10_sandbox.14_assets.repository")
_signal_repo_module = import_module("backend.10_sandbox.04_signals.repository")
_engine_module = import_module("backend.10_sandbox.07_execution.engine")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
AssetRepository = _asset_repo_module.AssetRepository
SignalRepository = _signal_repo_module.SignalRepository
SignalExecutionEngine = _engine_module.SignalExecutionEngine

# Maximum assets to test against in a single live test run
_MAX_ASSETS = 200
# Maximum concurrent signal executions
_MAX_CONCURRENT_EXECUTIONS = 10


@instrument_class_methods(
    namespace="sandbox.live_test.service",
    logger_name="backend.sandbox.live_test.instrumentation",
)
class LiveTestService:

    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._asset_repository = AssetRepository()
        self._signal_repository = SignalRepository()
        self._engine = SignalExecutionEngine(
            timeout_ms=settings.sandbox_execution_timeout_ms,
            max_memory_mb=settings.sandbox_execution_max_memory_mb,
            max_concurrent=_MAX_CONCURRENT_EXECUTIONS,
        )
        self._logger = get_logger("backend.sandbox.live_test")

    async def run_live_test(
        self,
        *,
        user_id: str,
        org_id: str,
        workspace_id: str,
        connector_id: str,
        signal_ids: list[str],
    ) -> LiveTestResponse:
        async with self._database_pool.acquire() as conn:
            # Check permission
            await require_permission(
                conn,
                user_id,
                "sandbox.execute",
                scope_org_id=org_id,
            )

            # Load assets for the connector
            assets, total_asset_count = await self._asset_repository.list_assets(
                conn,
                org_id=org_id,
                connector_id=connector_id,
                status="active",
                limit=_MAX_ASSETS,
                offset=0,
            )
            if not assets:
                raise ValidationError(
                    f"No active assets found for connector '{connector_id}'. "
                    "Run a collection first to discover assets."
                )

            # Load asset properties for each asset
            asset_data: list[dict] = []
            for asset in assets:
                props = await self._asset_repository.get_asset_properties(conn, asset.id)
                record: dict = {
                    "_asset_id": asset.id,
                    "_asset_type": asset.asset_type_code,
                    "_asset_external_id": asset.asset_external_id,
                    "_provider_code": asset.provider_code,
                }
                for prop in props:
                    record[prop.property_key] = prop.property_value
                asset_data.append(record)

            # Load signals and their python_source
            signals_with_source: list[tuple[str, str, str | None, str, int, int]] = []
            for signal_id in signal_ids:
                signal = await self._signal_repository.get_signal_by_id(conn, signal_id)
                if signal is None:
                    raise NotFoundError(f"Signal '{signal_id}' not found")
                python_source = signal.python_source
                if not python_source:
                    signal_props = await self._signal_repository.get_signal_properties(conn, signal_id)
                    python_source = signal_props.get("python_source", "")
                if not python_source:
                    raise ValidationError(f"Signal '{signal.signal_code}' has no python_source defined")
                signals_with_source.append((
                    signal.id,
                    signal.signal_code,
                    signal.name,
                    python_source,
                    signal.timeout_ms,
                    signal.max_memory_mb,
                ))

        # Execute each signal against each asset, using concurrency control
        semaphore = asyncio.Semaphore(_MAX_CONCURRENT_EXECUTIONS)
        results: list[LiveTestResultItem] = []

        async def _run_one(
            asset_record: dict,
            sig_id: str,
            sig_code: str,
            sig_name: str | None,
            source: str,
            timeout_ms: int,
            max_mem: int,
        ) -> LiveTestResultItem:
            async with semaphore:
                # Build the dataset dict the signal expects
                dataset = {
                    "records": [asset_record],
                    "items": [asset_record],
                    **asset_record,
                }
                exec_result = await self._engine.execute(
                    python_source=source,
                    dataset=dataset,
                    timeout_ms=timeout_ms,
                    max_memory_mb=max_mem,
                )

                if exec_result.status == "completed":
                    result_code = exec_result.result_code or "pass"
                    summary = exec_result.result_summary or ""
                    details = exec_result.result_details or []
                elif exec_result.status == "timeout":
                    result_code = "timeout"
                    summary = exec_result.error_message or "Execution timed out"
                    details = []
                else:
                    result_code = "error"
                    summary = exec_result.error_message or "Execution failed"
                    details = []

                return LiveTestResultItem(
                    asset_id=asset_record["_asset_id"],
                    asset_external_id=asset_record["_asset_external_id"],
                    asset_type=asset_record["_asset_type"],
                    signal_id=sig_id,
                    signal_code=sig_code,
                    signal_name=sig_name,
                    result=result_code,
                    summary=summary,
                    details=details,
                    execution_time_ms=exec_result.execution_time_ms,
                )

        # Build all tasks
        tasks = []
        for asset_record in asset_data:
            for sig_id, sig_code, sig_name, source, timeout_ms, max_mem in signals_with_source:
                tasks.append(
                    _run_one(asset_record, sig_id, sig_code, sig_name, source, timeout_ms, max_mem)
                )

        # Execute all concurrently
        if tasks:
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            for item in completed:
                if isinstance(item, Exception):
                    self._logger.error("Live test execution error: %s", item)
                    results.append(LiveTestResultItem(
                        asset_id="unknown",
                        asset_external_id="unknown",
                        asset_type="unknown",
                        signal_id="unknown",
                        signal_code="unknown",
                        signal_name=None,
                        result="error",
                        summary=str(item),
                        details=[],
                        execution_time_ms=0,
                    ))
                else:
                    results.append(item)

        passed = sum(1 for r in results if r.result == "pass")
        failed = sum(1 for r in results if r.result == "fail")
        warnings = sum(1 for r in results if r.result == "warning")
        errors = sum(1 for r in results if r.result in ("error", "timeout"))

        return LiveTestResponse(
            connector_id=connector_id,
            total_assets=len(asset_data),
            total_signals=len(signals_with_source),
            total_tests=len(results),
            passed=passed,
            failed=failed,
            warnings=warnings,
            errors=errors,
            results=results,
        )
