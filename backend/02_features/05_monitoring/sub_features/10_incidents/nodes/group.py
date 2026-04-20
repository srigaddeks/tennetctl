"""Incident grouper node: effect tx=own. Worker entry point for incident creation/joining."""

from __future__ import annotations

from typing import Any
from importlib import import_module

from .. import repository
from .. import grouper as grouper_module

_core_id = import_module("backend.01_core.id")
_audit = import_module("backend.02_features.04_audit.service")

# Node interface
kind = "effect"
handler_key = "monitoring.incidents.group"
tx = "own"  # Own transaction — advisory lock + incident upsert


async def execute(
    conn: Any,
    input_data: dict[str, Any],
    ctx: Any,
) -> dict[str, Any]:
    """Group alert event into incident.

    Input:
    {
        "alert_event_id": str,
        "rule_id": str,
        "org_id": str,
        "fingerprint": str,
        "labels": {label_key: value},
        "severity_id": int,
        "rule_name": str,
    }

    Output:
    {
        "incident_id": str,
        "is_new": bool,
        "alert_count": int,
    }
    """
    alert_event_id = input_data["alert_event_id"]
    rule_id = input_data["rule_id"]
    org_id = input_data["org_id"]
    fingerprint = input_data["fingerprint"]
    labels = input_data.get("labels", {})
    severity_id = input_data["severity_id"]
    rule_name = input_data.get("rule_name", f"Rule {rule_id}")

    # Load alert rule + grouping config
    rule = await conn.fetchrow(
        'SELECT * FROM "05_monitoring".v_monitoring_alert_rules WHERE id = $1',
        rule_id,
    )
    if not rule:
        return {"incident_id": None, "is_new": False, "error": f"Rule {rule_id} not found"}

    grouping_rule = await repository.get_grouping_rule(conn, rule_id)

    # Compute group key
    group_key = grouper_module.compute_group_key(
        rule_id,
        fingerprint,
        labels,
        grouping_rule=grouping_rule,
    )

    # Use advisory lock to prevent race conditions on (org_id, group_key)
    lock_key = hash((org_id, group_key)) % (2**31)
    await conn.execute("SELECT pg_advisory_lock($1)", lock_key)

    try:
        # Find open incident
        window_seconds = grouping_rule.get("group_window_seconds", 300) if grouping_rule else 300
        incident = await grouper_module.find_open_incident(
            conn,
            org_id,
            group_key,
            window_seconds=window_seconds,
        )

        is_new = False
        if incident:
            # Join alert to existing incident
            incident_id = incident["id"]
            await repository.link_alert_to_incident(conn, incident_id, alert_event_id)
            await repository.add_timeline_event(
                conn,
                incident_id,
                2,  # alert_joined kind_id
                payload={"alert_event_id": alert_event_id, "fingerprint": fingerprint},
            )
            # Emit metric
            await conn.execute(
                """
                INSERT INTO "05_monitoring"."61_evt_monitoring_metric_points"
                    (id, org_id, metric_key, labels, value, observed_at, recorded_at)
                VALUES ($1, $2, 'monitoring.incidents.dedup_total', $3, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """,
                _core_id.uuid7(),
                org_id,
                json.dumps({"rule_id": rule_id}),
            )
        else:
            # Create new incident
            is_new = True
            title = f"{rule_name} - {fingerprint[:8]}"
            incident_row = await repository.create_incident(
                conn,
                org_id=org_id,
                group_key=group_key,
                title=title,
                severity_id=severity_id,
            )
            incident_id = incident_row["id"]

            # Link the first alert
            await repository.link_alert_to_incident(conn, incident_id, alert_event_id)

            # Add timeline events: created + alert_joined
            await repository.add_timeline_event(
                conn,
                incident_id,
                1,  # created kind_id
                payload={"group_key": group_key, "rule_id": rule_id},
            )
            await repository.add_timeline_event(
                conn,
                incident_id,
                2,  # alert_joined kind_id
                payload={"alert_event_id": alert_event_id, "fingerprint": fingerprint},
            )

            # Emit audit
            await _audit.emit_audit_event(
                conn,
                org_id=org_id,
                actor_id=None,  # System
                category="monitoring.incident.created",
                object_type="incident",
                object_id=incident_id,
                changes={
                    "group_key": group_key,
                    "rule_id": rule_id,
                    "severity_id": severity_id,
                },
            )

            # Emit notification (via NOTIFY)
            await conn.execute(
                "SELECT pg_notify('monitoring_incident_opened', $1)",
                incident_id,
            )

        # Fetch updated alert count
        alert_count_row = await conn.fetchrow(
            """
            SELECT COUNT(*) as cnt FROM "05_monitoring"."40_lnk_monitoring_incident_alerts"
            WHERE incident_id = $1
            """,
            incident_id,
        )
        alert_count = alert_count_row["cnt"] if alert_count_row else 1

        return {
            "incident_id": incident_id,
            "is_new": is_new,
            "alert_count": alert_count,
        }

    finally:
        await conn.execute("SELECT pg_advisory_unlock($1)", lock_key)


__all__ = ["execute", "kind", "handler_key", "tx"]
