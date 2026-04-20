"""Node: monitoring.dashboard_share.grant_access

Effect node that grants dashboard access to an internal user.
Emits audit event for the grant.
"""

from importlib import import_module
from typing import Any

_monitoring_sharing_service = import_module(
    "backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.service"
)

NODE_DEFINITION = {
    "key": "monitoring.dashboard_share.grant_access",
    "kind": "effect",
    "emits_audit": True,
    "config_schema": {},
    "input_schema": {
        "type": "object",
        "properties": {
            "dashboard_id": {"type": "string", "description": "Dashboard UUID"},
            "org_id": {"type": "string", "description": "Org UUID"},
            "granted_to_user_id": {"type": "string", "description": "User to grant access to"},
            "expires_at": {
                "type": ["string", "null"],
                "description": "ISO8601 expiration time or null",
            },
        },
        "required": ["dashboard_id", "org_id", "granted_to_user_id"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "share_id": {"type": "string", "description": "Created share UUID"},
            "status": {"type": "string", "enum": ["created"]},
        },
        "required": ["share_id", "status"],
    },
}


async def handler(
    inputs: dict,
    ctx: Any,
) -> dict:
    """Grant access to a user.

    Args:
        inputs: dict with dashboard_id, org_id, granted_to_user_id, expires_at
        ctx: NodeContext with conn (from caller tx), audit scope

    Returns:
        dict with share_id, status
    """
    conn = ctx.conn
    user_id = ctx.audit_scope.user_id

    dashboard_id = inputs["dashboard_id"]
    org_id = inputs["org_id"]
    granted_to_user_id = inputs["granted_to_user_id"]
    expires_at = inputs.get("expires_at")

    # Parse expires_at if string
    if isinstance(expires_at, str):
        from datetime import datetime

        expires_at = datetime.fromisoformat(expires_at)

    # Create grant
    share = await _monitoring_sharing_service.create_internal_share(
        conn,
        dashboard_id,
        org_id,
        user_id,
        granted_to_user_id,
        expires_at,
    )

    return {"share_id": share.get("id"), "status": "created"}
