"""
Background scheduler for connector collection and auto-execution of linked control tests.

Reads `collection_schedule` from connectors and triggers:
1. Steampipe collection on schedule
2. Auto-execute all promoted tests linked to that connector
3. Auto-create remediation tasks on failure

Schedule values: manual (skip), realtime (every 60s), hourly, daily, weekly
"""
from __future__ import annotations

import asyncio
import json
import uuid
from datetime import datetime, timedelta, timezone
from importlib import import_module

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_settings_module = import_module("backend.00_config.settings")

DatabasePool = _database_module.DatabasePool
Settings = _settings_module.Settings
get_logger = _logging_module.get_logger

logger = get_logger(__name__)

SCHEDULE_INTERVALS = {
    "realtime": timedelta(seconds=60),
    "hourly": timedelta(hours=1),
    "daily": timedelta(days=1),
    "weekly": timedelta(weeks=1),
}

SCHEMA = '"15_sandbox"'


class CollectionScheduler:
    """Background task that polls connectors and auto-runs collections + tests."""

    def __init__(self, *, database_pool: DatabasePool, settings: Settings):
        self._pool = database_pool
        self._settings = settings
        self._check_interval = 30  # check every 30 seconds

    async def run_loop(self) -> None:
        logger.info("collection_scheduler_started", extra={"action": "scheduler.start", "outcome": "success"})
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                logger.info("collection_scheduler_stopped", extra={"action": "scheduler.stop"})
                return
            except Exception as e:
                logger.error(f"collection_scheduler_error: {e}", extra={"action": "scheduler.error"})
            await asyncio.sleep(self._check_interval)

    async def _tick(self) -> None:
        """Check all connectors with non-manual schedules and run if due."""
        async with self._pool.acquire() as conn:
            # Find connectors that are due for collection
            rows = await conn.fetch(f"""
                SELECT ci.id, ci.org_id, ci.connector_type_code, ci.collection_schedule,
                       ci.last_collected_at, ci.health_status,
                       MAX(CASE WHEN p.property_key = 'name' THEN p.property_value END) AS name
                FROM {SCHEMA}."20_fct_connector_instances" ci
                LEFT JOIN {SCHEMA}."40_dtl_connector_instance_properties" p ON p.connector_instance_id = ci.id
                WHERE ci.is_deleted = FALSE AND ci.is_active = TRUE AND ci.is_draft = FALSE
                  AND ci.collection_schedule != 'manual'
                  AND ci.collection_schedule IS NOT NULL
                GROUP BY ci.id
            """)

            now = datetime.now(timezone.utc)
            for row in rows:
                schedule = row["collection_schedule"]
                interval = SCHEDULE_INTERVALS.get(schedule)
                if not interval:
                    continue

                # Skip degraded/error connectors — no point collecting from broken connections
                health = (row["health_status"] or "").lower()
                if health in ("degraded", "error", "unhealthy", "failed"):
                    continue

                last_collected = row["last_collected_at"]
                if last_collected and (now - last_collected) < interval:
                    continue  # not due yet

                connector_id = str(row["id"])
                org_id = str(row["org_id"])
                connector_name = row.get("name") or connector_id

                logger.info(
                    f"scheduler_collection_due: {connector_name} ({schedule})",
                    extra={"action": "scheduler.collection_due", "connector_id": connector_id},
                )

                # Run collection + tests in background (don't block the tick loop)
                asyncio.create_task(
                    self._run_collection_and_tests(connector_id, org_id, connector_name)
                )

    async def _run_collection_and_tests(self, connector_id: str, org_id: str, connector_name: str) -> None:
        """Trigger collection for a connector and then execute linked tests."""
        try:
            # Step 1: Trigger collection
            logger.info(f"scheduler_starting_collection: {connector_name}", extra={"action": "scheduler.collect"})

            # Use the collection runs service to trigger
            try:
                _collection_service_module = import_module("backend.10_sandbox.15_collection_runs.service")
                CollectionRunService = _collection_service_module.CollectionRunService
                _cache_module = import_module("backend.01_core.cache")
                collection_service = CollectionRunService(
                    settings=self._settings,
                    database_pool=self._pool,
                    cache=_cache_module.NullCacheManager(),
                )
                # Trigger collection (this is async and may take time)
                await collection_service.trigger_collection(
                    connector_id=connector_id,
                    org_id=org_id,
                    user_id=None,  # system-triggered
                )
                logger.info(f"scheduler_collection_triggered: {connector_name}", extra={"action": "scheduler.collect.done"})
            except Exception as e:
                logger.warning(f"scheduler_collection_failed: {connector_name}: {e}", extra={"action": "scheduler.collect.error"})
                # Continue to test execution even if collection fails — use existing data

            # Step 2: Find and execute linked promoted tests
            await self._execute_linked_tests(connector_id, org_id, connector_name)

        except Exception as e:
            logger.error(f"scheduler_run_error: {connector_name}: {e}", extra={"action": "scheduler.run.error"})

    async def _execute_linked_tests(self, connector_id: str, org_id: str, connector_name: str) -> None:
        """Find promoted tests linked to this connector and execute them."""
        async with self._pool.acquire() as conn:
            # Find promoted tests linked to this connector
            test_rows = await conn.fetch(f"""
                SELECT id, test_code, tenant_key
                FROM {SCHEMA}."35_fct_promoted_tests"
                WHERE linked_asset_id = $1
                  AND is_active = TRUE AND is_deleted = FALSE
                ORDER BY test_code
            """, connector_id)

            if not test_rows:
                return

            logger.info(
                f"scheduler_executing_tests: {len(test_rows)} tests for {connector_name}",
                extra={"action": "scheduler.execute", "test_count": len(test_rows)},
            )

        # Execute each test
        for test_row in test_rows:
            test_id = str(test_row["id"])
            test_code = test_row["test_code"]
            tenant_key = test_row["tenant_key"]
            try:
                _promoted_service_module = import_module("backend.10_sandbox.35_promoted_tests.service")
                PromotedTestService = _promoted_service_module.PromotedTestService
                _cache_module = import_module("backend.01_core.cache")
                NullCacheManager = _cache_module.NullCacheManager

                service = PromotedTestService(
                    settings=self._settings,
                    database_pool=self._pool,
                    cache=NullCacheManager(),
                )
                result = await service.execute_test(
                    user_id="00000000-0000-0000-0000-000000000000",  # system user
                    tenant_key=tenant_key,
                    test_id=test_id,
                )
                logger.info(
                    f"scheduler_test_result: {test_code} = {result.result_status}",
                    extra={
                        "action": "scheduler.test.done",
                        "test_code": test_code,
                        "result": result.result_status,
                        "task_created": result.task_created,
                    },
                )
            except Exception as e:
                logger.warning(
                    f"scheduler_test_failed: {test_code}: {e}",
                    extra={"action": "scheduler.test.error", "test_code": test_code},
                )
