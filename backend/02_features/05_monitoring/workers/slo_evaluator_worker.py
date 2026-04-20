"""SLO evaluator worker — 60s loop evaluating all active SLOs.

For each active SLO:
  1. Acquires an advisory lock keyed on slo_id (prevents parallel double-evaluation).
  2. Loads indicator queries + thresholds.
  3. Calls evaluate node to compute attainment + burn rates.
  4. Detects burn rate breaches; inserts breach event + emits synthetic alert.
  5. Resolves previous breaches if condition clears.

Self-metrics:
  monitoring.slos.evaluations_total (counter)
  monitoring.slos.active (gauge)
  monitoring.slos.breaches_detected_total (counter)
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_sdk: Any = import_module("backend.02_features.05_monitoring.sdk")
_repo: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.repository"
)
_evaluate_node: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.nodes.evaluate"
)
_burn_alert_node: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.11_slo.nodes.burn_alert"
)

logger = logging.getLogger("tennetctl.monitoring.slos.worker")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class SloEvaluatorWorker:
    """60s loop evaluating all active SLOs and tracking burn rate breaches."""

    def __init__(self, pool: Any, config: Any) -> None:
        self._pool = pool
        self._config = config
        self._interval_s = int(getattr(config, "monitoring_slo_eval_interval_s", 60))
        self._task: asyncio.Task[None] | None = None
        self._stopped = False
        self._semaphore = asyncio.Semaphore(10)
        self.heartbeat_at: datetime | None = None

        self._ctr_eval = _sdk.metrics.counter(
            "monitoring.slos.evaluations_total",
            description="Total SLO evaluations.",
            unit="1",
        )
        self._gauge_active = _sdk.metrics.gauge(
            "monitoring.slos.active",
            description="Number of active SLOs.",
            unit="1",
        )
        self._ctr_breaches = _sdk.metrics.counter(
            "monitoring.slos.breaches_detected_total",
            description="SLO burn rate breaches detected.",
            unit="1",
        )

    def _ctx_for_slo(self, slo: dict[str, Any]) -> Any:
        return _catalog_ctx.NodeContext(
            user_id=None,
            session_id=None,
            org_id=str(slo["org_id"]),
            workspace_id=slo.get("workspace_id"),
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(),
            audit_category="system",
        )

    async def _evaluate_one(
        self,
        conn: Any,
        slo: dict[str, Any],
    ) -> None:
        """Evaluate a single SLO; detect and emit breaches."""
        slo_id = slo["id"]
        ctx = self._ctx_for_slo(slo)

        # Advisory lock to prevent parallel evaluation
        lock_id = hash(slo_id) % (2**31 - 1)
        try:
            acquired = await conn.execute(f"SELECT pg_advisory_lock({lock_id})")
        except Exception as e:
            logger.warning(f"Failed to acquire lock for SLO {slo_id}: {e}")
            return

        try:
            # Evaluate SLO
            eval_result = await _evaluate_node.evaluate_slo_node(
                conn, ctx, slo_id=slo_id
            )

            if eval_result.get("status") == "skipped_inactive":
                return

            self._ctr_eval.add(1)

            # Check burn rate breaches
            burn_rate_1h = eval_result.get("burn_rate_1h", 0.0)
            burn_rate_6h = eval_result.get("burn_rate_6h", 0.0)
            fast_threshold = float(slo.get("fast_burn_rate", 14.4))
            slow_threshold = float(slo.get("slow_burn_rate", 6.0))
            page_on_fast = bool(slo.get("page_on_fast", True))
            page_on_slow = bool(slo.get("page_on_slow", True))

            # Fast burn check (1h window)
            if page_on_fast and burn_rate_1h >= fast_threshold:
                open_breach = await _repo.get_open_breach(
                    conn, slo_id, "fast_burn"
                )
                if not open_breach:
                    breach_id = _core_id.uuid7()
                    alert_event_id = await _burn_alert_node.emit_synthetic_alert(
                        conn,
                        slo_id=slo_id,
                        org_id=slo["org_id"],
                        breach_kind="fast_burn",
                        burn_rate=burn_rate_1h,
                        severity_id=int(slo["severity_id"]),
                    )
                    await _repo.insert_breach(
                        conn,
                        id=breach_id,
                        slo_id=slo_id,
                        org_id=slo["org_id"],
                        breach_kind="fast_burn",
                        burn_rate=burn_rate_1h,
                        alert_event_id=alert_event_id,
                    )
                    self._ctr_breaches.add(1)
                    logger.info(
                        f"SLO {slo_id} fast burn breach detected: {burn_rate_1h}×"
                    )
            else:
                # Resolve fast burn breach if no longer breaching
                open_breach = await _repo.get_open_breach(
                    conn, slo_id, "fast_burn"
                )
                if open_breach:
                    await _repo.resolve_breach(conn, open_breach["id"])

            # Slow burn check (6h window)
            if page_on_slow and burn_rate_6h >= slow_threshold:
                open_breach = await _repo.get_open_breach(
                    conn, slo_id, "slow_burn"
                )
                if not open_breach:
                    breach_id = _core_id.uuid7()
                    alert_event_id = await _burn_alert_node.emit_synthetic_alert(
                        conn,
                        slo_id=slo_id,
                        org_id=slo["org_id"],
                        breach_kind="slow_burn",
                        burn_rate=burn_rate_6h,
                        severity_id=int(slo["severity_id"]),
                    )
                    await _repo.insert_breach(
                        conn,
                        id=breach_id,
                        slo_id=slo_id,
                        org_id=slo["org_id"],
                        breach_kind="slow_burn",
                        burn_rate=burn_rate_6h,
                        alert_event_id=alert_event_id,
                    )
                    self._ctr_breaches.add(1)
                    logger.info(
                        f"SLO {slo_id} slow burn breach detected: {burn_rate_6h}×"
                    )
            else:
                # Resolve slow burn breach if no longer breaching
                open_breach = await _repo.get_open_breach(
                    conn, slo_id, "slow_burn"
                )
                if open_breach:
                    await _repo.resolve_breach(conn, open_breach["id"])

            # Check budget exhaustion
            if eval_result.get("is_breached"):
                open_breach = await _repo.get_open_breach(
                    conn, slo_id, "budget_exhausted"
                )
                if not open_breach:
                    breach_id = _core_id.uuid7()
                    alert_event_id = await _burn_alert_node.emit_synthetic_alert(
                        conn,
                        slo_id=slo_id,
                        org_id=slo["org_id"],
                        breach_kind="budget_exhausted",
                        burn_rate=None,
                        severity_id=int(slo["severity_id"]),
                    )
                    await _repo.insert_breach(
                        conn,
                        id=breach_id,
                        slo_id=slo_id,
                        org_id=slo["org_id"],
                        breach_kind="budget_exhausted",
                        burn_rate=None,
                        alert_event_id=alert_event_id,
                    )
                    self._ctr_breaches.add(1)
                    logger.info(f"SLO {slo_id} budget exhausted")
            else:
                # Resolve budget breach if no longer breaching
                open_breach = await _repo.get_open_breach(
                    conn, slo_id, "budget_exhausted"
                )
                if open_breach:
                    await _repo.resolve_breach(conn, open_breach["id"])

        except Exception as e:
            logger.error(f"Failed to evaluate SLO {slo_id}: {e}", exc_info=True)
        finally:
            try:
                await conn.execute(f"SELECT pg_advisory_unlock({lock_id})")
            except Exception:
                pass

    async def _tick(self) -> None:
        """One evaluation cycle: load active SLOs, evaluate each."""
        async with self._pool.acquire() as conn:
            # Load all active SLOs
            slos = await conn.fetch(
                """
                SELECT * FROM "05_monitoring".v_monitoring_slos
                WHERE is_active = true AND deleted_at IS NULL
                """
            )
            slos = [dict(s) for s in slos]

        self._gauge_active.set(len(slos))
        logger.info(f"Evaluating {len(slos)} active SLOs")

        # Evaluate in parallel with semaphore to limit concurrency
        async def _eval_task(slo: dict[str, Any]) -> None:
            async with self._semaphore:
                async with self._pool.acquire() as conn:
                    await self._evaluate_one(conn, slo)

        await asyncio.gather(
            *[_eval_task(slo) for slo in slos],
            return_exceptions=True,
        )

        self.heartbeat_at = _now()

    async def _loop(self) -> None:
        """Main worker loop."""
        logger.info(f"SLO evaluator worker started (interval={self._interval_s}s)")

        while not self._stopped:
            try:
                await self._tick()
            except Exception as e:
                logger.error(f"Error in SLO evaluator tick: {e}", exc_info=True)

            await asyncio.sleep(self._interval_s)

    def start(self) -> None:
        """Start the worker loop."""
        if self._task is None:
            self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        """Stop the worker gracefully."""
        self._stopped = True
        if self._task:
            await self._task


__all__ = ["SloEvaluatorWorker"]
