"""WorkerPool supervisor.

Spawns the 3 monitoring workers as asyncio tasks, each wrapped in a
supervised loop that restarts on crash with exponential backoff
(1, 2, 4, 8, 16, 32, 60 seconds cap). ``stop(timeout)`` cancels all tasks
and waits up to ``timeout`` seconds for them to drain.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any, Awaitable, Callable

_redaction_mod: Any = import_module("backend.02_features.05_monitoring.workers.redaction")
_logs_mod: Any = import_module("backend.02_features.05_monitoring.workers.logs_consumer")
_spans_mod: Any = import_module("backend.02_features.05_monitoring.workers.spans_consumer")
_scraper_mod: Any = import_module("backend.02_features.05_monitoring.workers.apisix_scraper")
_rollup_mod: Any = import_module("backend.02_features.05_monitoring.workers.rollup_scheduler")
_partition_mod: Any = import_module("backend.02_features.05_monitoring.workers.partition_manager")
_synthetic_mod: Any = import_module("backend.02_features.05_monitoring.workers.synthetic_runner")
_notify_mod: Any = import_module("backend.02_features.05_monitoring.workers.notify_listener")
_alert_eval_mod: Any = import_module(
    "backend.02_features.05_monitoring.workers.alert_evaluator_worker"
)
_config_mod: Any = import_module("backend.01_core.config")

logger = logging.getLogger("tennetctl.monitoring.runner")

_BACKOFF_SEQ = (1, 2, 4, 8, 16, 32, 60)


class WorkerState:
    def __init__(self, name: str) -> None:
        self.name = name
        self.running = False
        self.last_heartbeat: datetime | None = None
        self.restart_count = 0
        self.last_error: str | None = None

    def snapshot(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "running": self.running,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "restart_count": self.restart_count,
            "last_error": self.last_error,
        }


class WorkerPool:
    """Supervises monitoring workers. Designed to be started in FastAPI lifespan."""

    def __init__(self) -> None:
        self._tasks: list[asyncio.Task[None]] = []
        self._states: dict[str, WorkerState] = {}
        self._workers: dict[str, Any] = {}
        self._stopped = False
        # Test hook — override backoff seq for fast restart testing.
        self._backoff_override: tuple[float, ...] | None = None

    def _backoff(self, attempt: int) -> float:
        if self._backoff_override is not None:
            seq = self._backoff_override
        else:
            seq = _BACKOFF_SEQ
        if not seq:
            return 1.0
        return float(seq[min(attempt, len(seq) - 1)])

    async def _supervised(self, name: str, factory: Callable[[], Awaitable[None]]) -> None:
        state = self._states[name]
        attempt = 0
        while not self._stopped:
            state.running = True
            try:
                await factory()
                # Normal return — worker decided it's done.
                state.running = False
                return
            except asyncio.CancelledError:
                state.running = False
                raise
            except Exception as e:  # noqa: BLE001
                state.running = False
                state.restart_count += 1
                state.last_error = repr(e)
                delay = self._backoff(attempt)
                logger.warning(
                    "worker %s crashed (attempt %d): %s — restarting in %.1fs",
                    name, attempt + 1, e, delay,
                )
                attempt += 1
                try:
                    await asyncio.sleep(delay)
                except asyncio.CancelledError:
                    return

    async def start(self, pool: Any, js: Any, config: Any) -> None:
        """Start supervised workers.

        ``js`` may be None when NATS is unavailable — in that case only the
        scraper runs (it doesn't need NATS).
        """
        redaction = _redaction_mod.RedactionEngine()
        self._workers["redaction"] = redaction

        if js is not None:
            # In single-tenant mode, resolve the default org UUID so OTLP-ingested
            # data is stored under the same org_id that session-authenticated users
            # receive — allowing the query endpoints to find it.
            resolved_org_id = "tennetctl"
            app_config = _config_mod.load_config()
            if getattr(app_config, "single_tenant", False):
                try:
                    _orgs_repo: Any = import_module(
                        "backend.02_features.03_iam.sub_features.01_orgs.repository"
                    )
                    async with pool.acquire() as _conn:
                        default_org = await _orgs_repo.get_by_slug(_conn, "default")
                    if default_org is not None:
                        resolved_org_id = default_org["id"]
                except Exception:  # noqa: BLE001
                    pass  # fall back to 'tennetctl' if IAM not migrated yet

            logs = _logs_mod.LogsConsumer(pool, js, config, redaction, org_id=resolved_org_id)
            self._workers["logs_consumer"] = logs
            self._states["logs_consumer"] = WorkerState("logs_consumer")
            self._tasks.append(asyncio.create_task(
                self._supervised("logs_consumer", logs.start),
                name="monitoring.logs_consumer",
            ))

            spans = _spans_mod.SpansConsumer(pool, js, config, org_id=resolved_org_id)
            self._workers["spans_consumer"] = spans
            self._states["spans_consumer"] = WorkerState("spans_consumer")
            self._tasks.append(asyncio.create_task(
                self._supervised("spans_consumer", spans.start),
                name="monitoring.spans_consumer",
            ))

        if getattr(config, "monitoring_apisix_scrape_enabled", False):
            scraper = _scraper_mod.ApisixScraper(pool, config)
            self._workers["apisix_scraper"] = scraper
            self._states["apisix_scraper"] = WorkerState("apisix_scraper")
            self._tasks.append(asyncio.create_task(
                self._supervised("apisix_scraper", scraper.start),
                name="monitoring.apisix_scraper",
            ))

        # 13-07: rollup scheduler
        if getattr(config, "monitoring_rollup_enabled", True):
            rollup = _rollup_mod.RollupScheduler(pool)
            self._workers["rollup_scheduler"] = rollup
            self._states["rollup_scheduler"] = WorkerState("rollup_scheduler")
            self._tasks.append(asyncio.create_task(
                self._supervised("rollup_scheduler", rollup.start),
                name="monitoring.rollup_scheduler",
            ))

        # 13-07: partition manager
        if getattr(config, "monitoring_partition_manager_enabled", True):
            partmgr = _partition_mod.PartitionManager(pool)
            self._workers["partition_manager"] = partmgr
            self._states["partition_manager"] = WorkerState("partition_manager")
            self._tasks.append(asyncio.create_task(
                self._supervised("partition_manager", partmgr.start),
                name="monitoring.partition_manager",
            ))

        # 13-07: synthetic runner
        if getattr(config, "monitoring_synthetic_runner_enabled", True):
            synrun = _synthetic_mod.SyntheticRunner(pool)
            self._workers["synthetic_runner"] = synrun
            self._states["synthetic_runner"] = WorkerState("synthetic_runner")
            self._tasks.append(asyncio.create_task(
                self._supervised("synthetic_runner", synrun.start),
                name="monitoring.synthetic_runner",
            ))

        # 13-07: LISTEN/NOTIFY listener for log live-tail
        if getattr(config, "monitoring_notify_listener_enabled", True):
            dsn = getattr(config, "database_url", None) or \
                "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl"
            listener = _notify_mod.NotifyListener(dsn)
            self._workers["notify_listener"] = listener
            self._states["notify_listener"] = WorkerState("notify_listener")
            self._tasks.append(asyncio.create_task(
                self._supervised("notify_listener", listener.start),
                name="monitoring.notify_listener",
            ))

        # 13-08b: alert evaluator
        if getattr(config, "monitoring_alert_evaluator_enabled", True):
            alert_worker = _alert_eval_mod.AlertEvaluatorWorker(pool, config)
            self._workers["alert_evaluator"] = alert_worker
            self._states["alert_evaluator"] = WorkerState("alert_evaluator")
            self._tasks.append(asyncio.create_task(
                self._supervised("alert_evaluator", alert_worker.start),
                name="monitoring.alert_evaluator",
            ))

        logger.info("WorkerPool started with %d workers", len(self._tasks))

    async def stop(self, timeout: float = 10.0) -> None:
        """Cancel all workers; wait up to ``timeout`` seconds for drain."""
        self._stopped = True
        # Ask workers to stop gracefully first.
        for worker in self._workers.values():
            stop_fn = getattr(worker, "stop", None)
            if stop_fn is not None:
                try:
                    await stop_fn()
                except Exception:  # noqa: BLE001
                    pass
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.wait(self._tasks, timeout=timeout)
        logger.info("WorkerPool stopped")

    def health(self) -> dict[str, dict[str, Any]]:
        """Return per-worker health snapshot."""
        out: dict[str, dict[str, Any]] = {}
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        for name, state in self._states.items():
            # Pull heartbeat from worker if available.
            worker = self._workers.get(name)
            hb = getattr(worker, "heartbeat_at", None) if worker else None
            if hb is not None:
                state.last_heartbeat = hb
            snap = state.snapshot()
            if state.last_heartbeat:
                snap["heartbeat_age_s"] = (now - state.last_heartbeat).total_seconds()
            out[name] = snap
        return out


__all__ = ["WorkerPool", "WorkerState"]
