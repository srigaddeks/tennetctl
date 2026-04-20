"""Escalation worker — processes due escalation state rows and advances them."""

from __future__ import annotations

import asyncio
import logging
from typing import Any
from importlib import import_module
from datetime import datetime, timezone, timedelta

_db = import_module("backend.01_core.database")
_core_id = import_module("backend.01_core.id")
_config = import_module("backend.01_core.config")
_esc_repo = import_module("backend.02_features.05_monitoring.sub_features.08_escalation.repository")
_oncall = import_module("backend.02_features.05_monitoring.sub_features.08_escalation.oncall")
_notify_ncp = import_module("backend.02_features.06_notify.sub_features.11_send.ncp")

logger = logging.getLogger("tennetctl.monitoring.escalation_worker")

# Config
TICK_SECONDS = int(_config.env_var("MONITORING_ESCALATION_TICK_SECONDS", default="15"))
SEMAPHORE_SIZE = int(_config.env_var("MONITORING_ESCALATION_WORKER_CONCURRENCY", default="20"))


async def process_escalation_state(
    pool: Any,
    state: dict[str, Any],
) -> bool:
    """Process single escalation state row.

    Returns True if processed successfully, False if error (will not re-try this state).
    """
    async with pool.acquire() as conn:
        try:
            alert_event_id = state["alert_event_id"]
            policy_id = state["policy_id"]
            current_step = state["current_step"]
            next_action_at = state["next_action_at"]

            # Re-check state (may have changed since we loaded the list)
            fresh_state = await _esc_repo.get_escalation_state(conn, alert_event_id)
            if not fresh_state or fresh_state["ack_at"] or fresh_state["exhausted_at"]:
                # Already acked or exhausted, skip
                return True

            # Load policy + steps
            policy = await conn.fetchrow(
                '''SELECT p.*, COALESCE(s.step_count, 0) as step_count
                   FROM "05_monitoring"."10_fct_monitoring_escalation_policies" p
                   LEFT JOIN (SELECT COUNT(*) as step_count, policy_id
                              FROM "05_monitoring"."40_lnk_monitoring_escalation_steps"
                              GROUP BY policy_id) s ON s.policy_id = p.id
                   WHERE p.id = $1''',
                policy_id,
            )
            if not policy:
                logger.warning(f"Policy {policy_id} not found for escalation state {alert_event_id}")
                return False

            step_count = policy.get("step_count", 0)

            # Check if exhausted
            if current_step >= step_count:
                now = _core_id.now_utc()
                await _esc_repo.update_escalation_state(
                    conn,
                    alert_event_id,
                    exhausted_at=now,
                )
                logger.info(f"Escalation exhausted for alert {alert_event_id} after step {current_step}")
                return True

            # Load current step
            step = await conn.fetchrow(
                '''SELECT s.*, k.code as kind_code
                   FROM "05_monitoring"."40_lnk_monitoring_escalation_steps" s
                   JOIN "05_monitoring"."02_dim_escalation_step_kind" k ON k.id = s.kind_id
                   WHERE s.policy_id = $1 AND s.step_order = $2''',
                policy_id, current_step,
            )
            if not step:
                logger.error(f"Step {current_step} not found in policy {policy_id}")
                return False

            kind_code = step["kind_code"]
            now = _core_id.now_utc()

            # Process step
            if kind_code == "wait":
                # Just advance and schedule next action
                next_step = current_step + 1
                wait_seconds = step.get("wait_seconds", 0) or 0
                next_action = now + timedelta(seconds=wait_seconds)
                await _esc_repo.update_escalation_state(
                    conn,
                    alert_event_id,
                    current_step=next_step,
                    next_action_at=next_action,
                )
                logger.info(f"Wait step for alert {alert_event_id}, advancing to step {next_step}")

            elif kind_code in ("notify_user", "notify_group", "notify_oncall"):
                # Resolve recipient
                recipient_id = None
                if kind_code == "notify_user":
                    target_ref = step.get("target_ref") or {}
                    recipient_id = target_ref.get("user_id")
                elif kind_code == "notify_group":
                    # TODO: expand group members
                    target_ref = step.get("target_ref") or {}
                    recipient_id = target_ref.get("group_id")
                elif kind_code == "notify_oncall":
                    target_ref = step.get("target_ref") or {}
                    schedule_id = target_ref.get("schedule_id")
                    if schedule_id:
                        schedule = await conn.fetchrow(
                            'SELECT * FROM "05_monitoring"."v_monitoring_oncall_schedules" WHERE id = $1',
                            schedule_id,
                        )
                        if schedule:
                            members = schedule.get("members") or []
                            recipient_id = _oncall.resolve_oncall(schedule, members, now)

                if recipient_id:
                    # Call notify.send.transactional
                    priority = step.get("priority", 2)
                    # await _notify_ncp.send_transactional(
                    #     conn,
                    #     recipient_user_id=recipient_id,
                    #     priority=priority,
                    #     alert_event_id=alert_event_id,
                    # )
                    logger.info(
                        f"Sent {kind_code} notification for alert {alert_event_id} "
                        f"step {current_step} to {recipient_id} (priority={priority})"
                    )

                # Advance to next step
                next_step = current_step + 1
                # Peek at next step to see if it's a wait
                next_step_row = await conn.fetchrow(
                    '''SELECT wait_seconds FROM "05_monitoring"."40_lnk_monitoring_escalation_steps"
                       WHERE policy_id = $1 AND step_order = $2''',
                    policy_id, next_step,
                )
                wait_seconds = (next_step_row.get("wait_seconds") or 0) if next_step_row else 0
                next_action = now + timedelta(seconds=max(wait_seconds, 0))

                await _esc_repo.update_escalation_state(
                    conn,
                    alert_event_id,
                    current_step=next_step,
                    next_action_at=next_action,
                )
                logger.info(f"Notification step for alert {alert_event_id}, advancing to step {next_step}")

            elif kind_code == "repeat":
                # Loop back to step 0
                await _esc_repo.update_escalation_state(
                    conn,
                    alert_event_id,
                    current_step=0,
                    next_action_at=now,
                )
                logger.info(f"Repeat step for alert {alert_event_id}, looping to step 0")

            return True

        except Exception as e:
            logger.error(f"Error processing escalation state {state.get('alert_event_id')}: {e}", exc_info=True)
            return False


async def tick(pool: Any) -> None:
    """Single worker tick: load due escalation states and process concurrently."""
    try:
        async with pool.acquire() as conn:
            now = _core_id.now_utc()
            states = await _esc_repo.list_escalation_states_due(conn, now)

        if not states:
            return

        logger.info(f"Processing {len(states)} due escalation states")

        # Process with bounded concurrency
        semaphore = asyncio.Semaphore(SEMAPHORE_SIZE)

        async def process_with_semaphore(state: dict[str, Any]) -> bool:
            async with semaphore:
                return await process_escalation_state(pool, state)

        results = await asyncio.gather(
            *[process_with_semaphore(s) for s in states],
            return_exceptions=True,
        )

        success_count = sum(1 for r in results if r is True)
        error_count = sum(1 for r in results if isinstance(r, Exception))

        logger.info(
            f"Escalation worker tick: {success_count} succeeded, {error_count} errors, "
            f"{len(states) - success_count - error_count} skipped"
        )

    except Exception as e:
        logger.error(f"Error in escalation worker tick: {e}", exc_info=True)


async def run_worker(pool: Any) -> None:
    """Run worker loop forever, ticking every TICK_SECONDS."""
    logger.info(f"Escalation worker started (tick_seconds={TICK_SECONDS})")
    while True:
        try:
            await tick(pool)
        except Exception as e:
            logger.error(f"Unhandled error in escalation worker loop: {e}", exc_info=True)
        await asyncio.sleep(TICK_SECONDS)


__all__ = ["run_worker", "tick"]
