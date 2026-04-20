"""Incident state transition node: effect tx=caller."""

from __future__ import annotations

from typing import Any, Literal
from importlib import import_module

from .. import repository

_audit = import_module("backend.02_features.04_audit.service")

# Node interface
kind = "effect"
handler_key = "monitoring.incidents.transition"
tx = "caller"


async def execute(
    conn: Any,
    input_data: dict[str, Any],
    ctx: Any,
) -> dict[str, Any]:
    """Transition incident state.

    Input:
    {
        "incident_id": str,
        "target_state": "acknowledged" | "resolved" | "closed",
        "user_id": str (who triggered),
        "summary": str (optional),
        "root_cause": str (optional),
        "postmortem_ref": str (optional),
    }

    Output:
    {
        "incident_id": str,
        "old_state": str,
        "new_state": str,
    }
    """
    incident_id = input_data["incident_id"]
    target_state = input_data["target_state"]
    user_id = input_data["user_id"]
    summary = input_data.get("summary")
    root_cause = input_data.get("root_cause")
    postmortem_ref = input_data.get("postmortem_ref")

    # Fetch current incident
    incident = await repository.get_incident(conn, incident_id)
    if not incident:
        return {"incident_id": None, "error": f"Incident {incident_id} not found"}

    old_state = incident["state_code"]
    state_map = {"acknowledged": 2, "resolved": 3, "closed": 4}
    target_state_id = state_map.get(target_state)

    if not target_state_id:
        return {"incident_id": None, "error": f"Invalid target state: {target_state}"}

    # Update state
    await repository.update_incident_state(conn, incident_id, target_state_id, user_id)

    # Update summary/root_cause/postmortem if provided
    if summary or root_cause or postmortem_ref:
        await repository.update_incident_summary(
            conn,
            incident_id,
            summary=summary,
            root_cause=root_cause,
            postmortem_ref=postmortem_ref,
        )

    # Add timeline event
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
        org_id=incident["org_id"],
        actor_id=user_id,
        category="monitoring.incident.state_change",
        object_type="incident",
        object_id=incident_id,
        changes={
            "old_state": old_state,
            "new_state": target_state,
        },
    )

    return {
        "incident_id": incident_id,
        "old_state": old_state,
        "new_state": target_state,
    }


__all__ = ["execute", "kind", "handler_key", "tx"]
