"""Service layer for incidents sub-feature — business logic + audit."""

from __future__ import annotations

from typing import Any
from importlib import import_module

from . import repository
from . import schemas

_errors = import_module("backend.01_core.errors")
_audit = import_module("backend.02_features.04_audit.service")
_resp = import_module("backend.01_core.response")

# Service functions orchestrate repo calls + audit emission. No raw SQL here.


async def list_incidents(
    conn: Any,
    org_id: str,
    state_id: int | None = None,
    severity_id: int | None = None,
    rule_id: str | None = None,
    label_search: str | None = None,
    opened_after: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """List incidents with filters."""
    rows, total = await repository.list_incidents(
        conn,
        org_id=org_id,
        state_id=state_id,
        severity_id=severity_id,
        rule_id=rule_id,
        label_search=label_search,
        opened_after=opened_after,
        limit=limit,
        offset=offset,
    )
    return rows, total


async def get_incident_detail(
    conn: Any,
    org_id: str,
    incident_id: str,
) -> dict:
    """Get incident with linked alerts and timeline summary."""
    incident = await repository.get_incident(conn, incident_id)
    if not incident:
        raise _errors.AppError("NOT_FOUND", f"Incident '{incident_id}' not found.", 404)
    if incident["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access incident from another org.", 403)

    # Load linked alerts
    alerts = await repository.get_linked_alerts(conn, incident_id)
    incident["linked_alerts"] = alerts

    # Load timeline summary (last 10 events)
    timeline = await repository.get_incident_timeline(conn, incident_id, limit=10)
    incident["timeline_events"] = timeline

    return incident


async def update_incident_state(
    conn: Any,
    org_id: str,
    incident_id: str,
    user_id: str,
    req: schemas.IncidentStateTransition,
) -> dict:
    """Handle incident state transition with audit."""
    incident = await repository.get_incident(conn, incident_id)
    if not incident:
        raise _errors.AppError("NOT_FOUND", f"Incident '{incident_id}' not found.", 404)
    if incident["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access incident from another org.", 403)

    target_state = req.state
    state_map = {"acknowledged": 2, "resolved": 3, "closed": 4}
    target_state_id = state_map.get(target_state)

    if target_state == "closed":
        if not req.root_cause or not req.summary:
            raise _errors.AppError(
                "INVALID_REQUEST",
                "root_cause and summary required for closed state.",
                400,
            )

    # Update state
    await repository.update_incident_state(conn, incident_id, target_state_id, user_id)

    # Update summary/root_cause/postmortem if provided
    if req.summary or req.root_cause or req.postmortem_ref:
        await repository.update_incident_summary(
            conn,
            incident_id,
            summary=req.summary,
            root_cause=req.root_cause,
            postmortem_ref=req.postmortem_ref,
        )

    # Record timeline event
    event_kind_map = {"acknowledged": 3, "resolved": 7, "closed": 8}
    event_kind_id = event_kind_map.get(target_state, 1)
    await repository.add_timeline_event(
        conn,
        incident_id,
        event_kind_id,
        actor_user_id=user_id,
        payload={"state": target_state},
    )

    # Emit audit
    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.incident.state_change",
        object_type="incident",
        object_id=incident_id,
        changes={
            "old_state": incident["state_code"],
            "new_state": target_state,
            "root_cause": req.root_cause,
        },
    )

    # Reload and return
    return await repository.get_incident(conn, incident_id) or {}


async def add_incident_comment(
    conn: Any,
    org_id: str,
    incident_id: str,
    user_id: str,
    req: schemas.IncidentCommentCreate,
) -> dict:
    """Add comment to incident timeline with audit."""
    incident = await repository.get_incident(conn, incident_id)
    if not incident:
        raise _errors.AppError("NOT_FOUND", f"Incident '{incident_id}' not found.", 404)
    if incident["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access incident from another org.", 403)

    # Add timeline event
    event = await repository.add_timeline_event(
        conn,
        incident_id,
        6,  # comment_added kind_id
        actor_user_id=user_id,
        payload={"body": req.body},
    )

    # Emit audit
    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.incident.comment_added",
        object_type="incident",
        object_id=incident_id,
        changes={"comment_length": len(req.body)},
    )

    return event


async def get_grouping_rule(
    conn: Any,
    rule_id: str,
) -> dict | None:
    """Get grouping rule for alert rule."""
    return await repository.get_grouping_rule(conn, rule_id)


async def create_or_update_grouping_rule(
    conn: Any,
    org_id: str,
    user_id: str,
    rule_id: str,
    req: schemas.GroupingRuleCreate,
) -> dict:
    """Create or update grouping rule with audit."""
    # Verify rule exists and belongs to org
    rule = await conn.fetchrow(
        'SELECT * FROM "05_monitoring".v_monitoring_alert_rules WHERE id = $1',
        rule_id,
    )
    if not rule:
        raise _errors.AppError("NOT_FOUND", f"Alert rule '{rule_id}' not found.", 404)
    if rule["org_id"] != org_id:
        raise _errors.AppError("FORBIDDEN", "Cannot access rule from another org.", 403)

    await repository.upsert_grouping_rule(
        conn,
        rule_id=rule_id,
        dedup_strategy=req.dedup_strategy,
        group_by=req.group_by,
        group_window_seconds=req.group_window_seconds,
        custom_template=req.custom_template,
        is_active=req.is_active,
    )

    await _audit.emit_audit_event(
        conn,
        org_id=org_id,
        actor_id=user_id,
        category="monitoring.incident.grouping_rule_update",
        object_type="alert_rule",
        object_id=rule_id,
        changes={
            "dedup_strategy": req.dedup_strategy,
            "group_by": req.group_by,
            "group_window_seconds": req.group_window_seconds,
        },
    )

    return await repository.get_grouping_rule(conn, rule_id) or {}
