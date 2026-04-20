"""Incident comment node: effect tx=caller."""

from __future__ import annotations

from typing import Any
from importlib import import_module

from .. import repository

_audit = import_module("backend.02_features.04_audit.service")

# Node interface
kind = "effect"
handler_key = "monitoring.incidents.comment_add"
tx = "caller"


async def execute(
    conn: Any,
    input_data: dict[str, Any],
    ctx: Any,
) -> dict[str, Any]:
    """Add comment to incident timeline.

    Input:
    {
        "incident_id": str,
        "user_id": str,
        "body": str,
    }

    Output:
    {
        "event_id": str,
        "incident_id": str,
    }
    """
    incident_id = input_data["incident_id"]
    user_id = input_data["user_id"]
    body = input_data["body"]

    # Fetch incident
    incident = await repository.get_incident(conn, incident_id)
    if not incident:
        return {"event_id": None, "error": f"Incident {incident_id} not found"}

    # Add timeline event
    event = await repository.add_timeline_event(
        conn,
        incident_id,
        6,  # comment_added kind_id
        actor_user_id=user_id,
        payload={"body": body},
    )

    # Emit audit
    await _audit.emit_audit_event(
        conn,
        org_id=incident["org_id"],
        actor_id=user_id,
        category="monitoring.incident.comment_added",
        object_type="incident",
        object_id=incident_id,
        changes={"comment_length": len(body)},
    )

    return {
        "event_id": event.get("id"),
        "incident_id": incident_id,
    }


__all__ = ["execute", "kind", "handler_key", "tx"]
