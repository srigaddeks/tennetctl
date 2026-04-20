"""Alert evaluator worker — periodic loop over active rules.

Runs every ``config.monitoring_alert_eval_interval_s`` seconds. For each
active, non-paused alert rule it:

  1. Calls ``evaluator.evaluate_rule`` on its own transaction.
  2. Processes the returned ``AlertTransition`` list:
     - firing_new: INSERT new evt row (or UPDATE existing firing row with
       fresh value); check silences; call ``notify.send.transactional``
       unless silenced / throttled.
     - resolving: UPDATE evt SET state='resolved', resolved_at=now; send
       resolved notification.
  3. Updates rule state (last_eval_at, duration, error).

Throttle: do not notify more than once per ``monitoring_alert_notify_throttle_minutes``
for the same fingerprint.

Recipient resolution (v0.1):
  - ``rule.labels["recipient_user_id"]`` if present
  - else skip notify with a warning log (and bump a skipped counter)
Future work: a full recipient resolver (vault key, on-call rotations, etc.).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from datetime import datetime, timezone, timedelta
from importlib import import_module
from typing import Any

_catalog: Any = import_module("backend.01_catalog")
_catalog_ctx: Any = import_module("backend.01_catalog.context")
_core_id: Any = import_module("backend.01_core.id")
_sdk: Any = import_module("backend.02_features.05_monitoring.sdk")
_service: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.service"
)
_evaluator: Any = import_module(
    "backend.02_features.05_monitoring.sub_features.07_alerts.evaluator"
)

logger = logging.getLogger("tennetctl.monitoring.alerts.worker")


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class AlertEvaluatorWorker:
    """30s loop over active alert rules.

    Self-metrics:
      monitoring.alerts.evaluations_total (counter)
      monitoring.alerts.rules_active (gauge)
      monitoring.alerts.notify_failures_total (counter)
      monitoring.alerts.notify_skipped_no_recipient_total (counter)
    """

    def __init__(self, pool: Any, config: Any) -> None:
        self._pool = pool
        self._config = config
        self._interval_s = int(getattr(config, "monitoring_alert_eval_interval_s", 30))
        self._throttle_s = int(
            getattr(config, "monitoring_alert_notify_throttle_minutes", 15)
        ) * 60
        self._task: asyncio.Task[None] | None = None
        self._stopped = False
        self._semaphore = asyncio.Semaphore(10)
        self.heartbeat_at: datetime | None = None
        self._ctr_eval = _sdk.metrics.counter(
            "monitoring.alerts.evaluations_total",
            description="Total alert-rule evaluations.",
            unit="1",
        )
        self._gauge_active = _sdk.metrics.gauge(
            "monitoring.alerts.rules_active",
            description="Number of active alert rules this cycle.",
            unit="1",
        )
        self._ctr_notify_fail = _sdk.metrics.counter(
            "monitoring.alerts.notify_failures_total",
            description="Alert notification send failures.",
            unit="1",
        )
        self._ctr_notify_skipped = _sdk.metrics.counter(
            "monitoring.alerts.notify_skipped_no_recipient_total",
            description="Alerts not notified because no recipient could be resolved.",
            unit="1",
        )

    def _ctx_for_rule(self, rule: dict[str, Any]) -> Any:
        return _catalog_ctx.NodeContext(
            user_id=None,
            session_id=None,
            org_id=str(rule["org_id"]),
            workspace_id=None,
            trace_id=_core_id.uuid7(),
            span_id=_core_id.uuid7(),
            request_id=_core_id.uuid7(),
            audit_category="system",
            extras={"pool": self._pool},
        )

    def _resolve_recipient(self, rule: dict[str, Any]) -> str | None:
        labels = rule.get("labels") or {}
        if isinstance(labels, str):
            try:
                labels = json.loads(labels)
            except Exception:  # noqa: BLE001
                labels = {}
        rcpt = labels.get("recipient_user_id") if isinstance(labels, dict) else None
        if rcpt:
            return str(rcpt)
        return None

    async def _notify(
        self,
        rule: dict[str, Any],
        event_id: str,
        transition: Any,
        state_text: str,
        ctx: Any,
    ) -> bool:
        """Fire a notify.send.transactional call. Returns True on success."""
        recipient = self._resolve_recipient(rule)
        if not recipient:
            logger.warning(
                "alert %s has no resolvable recipient; skipping notify",
                rule.get("name"),
            )
            try:
                await self._ctr_notify_skipped.increment(ctx, value=1.0)
            except Exception:  # noqa: BLE001
                pass
            return False
        template_key = rule.get("notify_template_key") or "alert.default"
        variables = {
            "rule_name": str(rule.get("name") or ""),
            "value": str(transition.value),
            "threshold": str(transition.threshold),
            "labels": json.dumps(transition.labels or {}),
            "alert_url": f"/monitoring/alerts/{event_id}",
            "state": state_text,
            "severity": str(rule.get("severity_code") or ""),
        }
        try:
            await _catalog.run_node(
                self._pool,
                "notify.send.transactional",
                ctx,
                {
                    "org_id": rule["org_id"],
                    "template_key": template_key,
                    "recipient_user_id": recipient,
                    "channel_code": "email",
                    "variables": variables,
                },
            )
            return True
        except Exception as e:  # noqa: BLE001
            logger.exception(
                "notify failed for alert %s (event %s): %r", rule.get("name"), event_id, e,
            )
            try:
                await self._ctr_notify_fail.increment(ctx, value=1.0)
            except Exception:  # noqa: BLE001
                pass
            return False

    async def _handle_transition(
        self,
        rule: dict[str, Any],
        transition: Any,
        ctx: Any,
        now: datetime,
    ) -> None:
        """Process one transition under its own transaction."""
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                if transition.kind == "firing_new":
                    await self._handle_firing(conn, rule, transition, ctx, now)
                elif transition.kind == "resolving":
                    await self._handle_resolving(conn, rule, transition, ctx, now)

    async def _handle_firing(
        self,
        conn: Any,
        rule: dict[str, Any],
        transition: Any,
        ctx: Any,
        now: datetime,
    ) -> None:
        existing = await _service.find_firing_event(
            conn, rule_id=rule["id"], fingerprint=transition.fingerprint,
        )
        if existing is not None:
            # Existing firing row — update value, maybe re-notify on throttle.
            await _service.update_alert_event(
                conn, id=existing["id"], started_at=existing["started_at"],
                value=transition.value,
            )
            last = existing.get("last_notified_at")
            throttled = (
                last is not None and (now - last).total_seconds() < self._throttle_s
            )
            if existing.get("silenced") or throttled:
                return
            ok = await self._notify(rule, existing["id"], transition, "firing", ctx)
            if ok:
                await _service.update_alert_event(
                    conn, id=existing["id"], started_at=existing["started_at"],
                    last_notified_at=now,
                    notification_count=int(existing.get("notification_count") or 0) + 1,
                )
            return
        # Brand-new firing event.
        event_id = _core_id.uuid7()
        silence_id = await _service.find_matching_silences(
            conn, org_id=rule["org_id"], rule_id=rule["id"],
            labels=transition.labels, now=now,
        )
        await _service.insert_alert_event(
            conn,
            id=event_id, rule_id=rule["id"], fingerprint=transition.fingerprint,
            value=transition.value, threshold=transition.threshold,
            org_id=rule["org_id"], started_at=now,
            labels=transition.labels or {}, annotations={},
            silenced=silence_id is not None, silence_id=silence_id,
        )
        # Create escalation state if rule has escalation_policy_id
        if rule.get("escalation_policy_id"):
            _esc_repo: Any = import_module(
                "backend.02_features.05_monitoring.sub_features.08_escalation.repository"
            )
            await _esc_repo.create_escalation_state(
                conn,
                alert_event_id=event_id,
                policy_id=rule["escalation_policy_id"],
                next_action_at=now,
            )
        if silence_id is not None:
            return
        ok = await self._notify(rule, event_id, transition, "firing", ctx)
        if ok:
            await _service.update_alert_event(
                conn, id=event_id, started_at=now,
                last_notified_at=now, notification_count=1,
            )

    async def _handle_resolving(
        self,
        conn: Any,
        rule: dict[str, Any],
        transition: Any,
        ctx: Any,
        now: datetime,
    ) -> None:
        existing = await _service.find_firing_event(
            conn, rule_id=rule["id"], fingerprint=transition.fingerprint,
        )
        if existing is None:
            return
        await _service.update_alert_event(
            conn, id=existing["id"], started_at=existing["started_at"],
            state="resolved", resolved_at=now,
        )
        if existing.get("silenced"):
            return
        last = existing.get("last_notified_at")
        throttled = (
            last is not None and (now - last).total_seconds() < self._throttle_s
        )
        if throttled:
            return
        ok = await self._notify(rule, existing["id"], transition, "resolved", ctx)
        if ok:
            await _service.update_alert_event(
                conn, id=existing["id"], started_at=existing["started_at"],
                last_notified_at=now,
                notification_count=int(existing.get("notification_count") or 0) + 1,
            )

    async def _evaluate_one_rule(self, rule: dict[str, Any]) -> None:
        async with self._semaphore:
            ctx = self._ctx_for_rule(rule)
            t0 = time.perf_counter()
            now = _now()
            err_str: str | None = None
            try:
                async with self._pool.acquire() as conn:
                    async with conn.transaction():
                        transitions = await _evaluator.evaluate_rule(
                            conn, rule, ctx, now=now,
                        )
                for t in transitions:
                    try:
                        await self._handle_transition(rule, t, ctx, now)
                    except Exception as e:  # noqa: BLE001
                        logger.warning(
                            "transition handling failed for rule %s: %r",
                            rule.get("name"), e,
                        )
            except Exception as e:  # noqa: BLE001
                err_str = repr(e)
                logger.warning(
                    "alert evaluation failed rule=%s: %r", rule.get("name"), e,
                )
            duration_ms = int((time.perf_counter() - t0) * 1000)
            try:
                async with self._pool.acquire() as conn:
                    await _service.update_rule_state(
                        conn, rule_id=rule["id"],
                        last_eval_at=now,
                        last_eval_duration_ms=duration_ms,
                        last_error=err_str,
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning("failed to persist rule_state for %s: %r", rule.get("id"), e)
            try:
                await self._ctr_eval.increment(ctx, value=1.0)
            except Exception:  # noqa: BLE001
                pass

    async def _cycle(self) -> None:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, org_id, name, description, target, dsl, condition,
                       severity_id, severity_code, notify_template_key,
                       labels, is_active, paused_until, escalation_policy_id
                  FROM "05_monitoring"."v_monitoring_alert_rules"
                 WHERE is_active = TRUE
                   AND (paused_until IS NULL OR paused_until < $1)
                """,
                _now(),
            )
        rules = [dict(r) for r in rows]
        # rules_active gauge is emitted per-org (if any rules). Grouping by
        # first rule's org is a proxy — a full per-org rollup is v0.2.
        if rules:
            sample_ctx = self._ctx_for_rule(rules[0])
            try:
                await self._gauge_active.set(sample_ctx, value=float(len(rules)))
            except Exception:  # noqa: BLE001
                pass
        await asyncio.gather(
            *(self._evaluate_one_rule(r) for r in rules),
            return_exceptions=True,
        )
        self.heartbeat_at = _now()

    async def _loop(self) -> None:
        # Small initial stagger so first cycle doesn't stampede with startup tasks.
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            return
        while not self._stopped:
            try:
                await self._cycle()
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                logger.warning("alert evaluator cycle error: %r", e)
            try:
                await asyncio.sleep(self._interval_s)
            except asyncio.CancelledError:
                return

    async def start(self) -> None:
        self._stopped = False
        self._task = asyncio.create_task(self._loop(), name="monitoring.alert_evaluator")
        logger.info(
            "alert evaluator started (interval=%ds, throttle=%ds)",
            self._interval_s, self._throttle_s,
        )
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        self._stopped = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except Exception:  # noqa: BLE001
                pass
            self._task = None


__all__ = ["AlertEvaluatorWorker"]
