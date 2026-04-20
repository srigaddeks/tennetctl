"""Incident grouper worker: listens for alert firing events and groups them into incidents.

Subscribes to Postgres LISTEN 'monitoring_alert_fired' (emitted by alert evaluator
after firing-transition commit). Per-event handler loads alert + rule + grouping_rule,
computes group_key, finds/creates incident, and emits NOTIFY 'monitoring_incident_opened'
for escalation and action workers to consume.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from importlib import import_module

_pool_factory = import_module("backend.01_core.database")
_core_id = import_module("backend.01_core.id")

logger = logging.getLogger("tennetctl.monitoring.incident_grouper_worker")


async def handle_alert_fired(
    pool: Any,
    alert_event_id: str,
) -> None:
    """Handle alert fired event: group into incident."""
    async with pool.acquire() as conn:
        # Load alert event
        alert = await conn.fetchrow(
            'SELECT * FROM "05_monitoring".v_monitoring_alert_events WHERE id = $1',
            alert_event_id,
        )
        if not alert:
            logger.warning(f"Alert event {alert_event_id} not found")
            return

        # Skip if already linked to an incident (shouldn't happen)
        linked = await conn.fetchval(
            """
            SELECT incident_id FROM "05_monitoring"."40_lnk_monitoring_incident_alerts"
            WHERE alert_event_id = $1
            LIMIT 1
            """,
            alert_event_id,
        )
        if linked:
            logger.debug(f"Alert {alert_event_id} already linked to incident {linked}")
            return

        # Invoke the group node via NCP
        _ncp = import_module("backend.01_core.ncp")
        node_result = await _ncp.invoke_node(
            conn,
            node_key="monitoring.incidents.group",
            input_data={
                "alert_event_id": alert_event_id,
                "rule_id": alert["rule_id"],
                "org_id": alert["org_id"],
                "fingerprint": alert["fingerprint"],
                "labels": alert.get("labels") or {},
                "severity_id": alert["severity_id"],
                "rule_name": alert.get("rule_name", ""),
            },
            ctx=None,  # System call, no user context
        )

        if node_result.get("incident_id"):
            logger.info(
                f"Alert {alert_event_id} grouped to incident {node_result['incident_id']} "
                f"(is_new={node_result.get('is_new')})"
            )
        else:
            logger.error(f"Failed to group alert {alert_event_id}: {node_result.get('error')}")


async def listen_for_alerts(pool: Any) -> None:
    """Long-running listener for 'monitoring_alert_fired' notifications."""
    async with pool.acquire() as conn:
        await conn.add_listener("monitoring_alert_fired", handle_alert_fired_callback)
        logger.info("Incident grouper listening on 'monitoring_alert_fired'")
        try:
            await asyncio.sleep(float("inf"))
        except asyncio.CancelledError:
            logger.info("Incident grouper listener cancelled")
            await conn.remove_listener("monitoring_alert_fired")


async def handle_alert_fired_callback(
    conn: Any,
    pid: int,
    channel: str,
    payload: str,
) -> None:
    """Callback for LISTEN notification."""
    try:
        alert_event_id = payload.strip()
        pool = conn._pool or await _pool_factory.get_pool()
        await handle_alert_fired(pool, alert_event_id)
    except Exception as e:
        logger.exception(f"Error handling alert fired: {e}")


async def run(pool: Any) -> None:
    """Worker entry point."""
    logger.info("Starting incident grouper worker")
    try:
        await listen_for_alerts(pool)
    except Exception as e:
        logger.exception(f"Incident grouper worker crashed: {e}")


__all__ = ["run", "handle_alert_fired"]
