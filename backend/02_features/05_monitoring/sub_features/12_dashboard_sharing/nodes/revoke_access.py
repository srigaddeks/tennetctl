"""Node: monitoring.dashboard_share.revoke_access

Effect node that revokes a dashboard share grant.
Emits audit event for the revocation.
"""

from importlib import import_module
from typing import Any

_monitoring_sharing_service = import_module(
    "backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.service"
)

NODE_DEFINITION = {
    "key": "monitoring.dashboard_share.revoke_access",
    "kind": "effect",
    "emits_audit": True,
    "config_schema": {},
    "input_schema": {
        "type": "object",
        "properties": {
            "share_id": {"type": "string", "description": "Share UUID to revoke"},
        },
        "required": ["share_id"],
    },
    "output_schema": {
        "type": "object",
        "properties": {
            "share_id": {"type": "string", "description": "Revoked share UUID"},
            "status": {"type": "string", "enum": ["revoked"]},
        },
        "required": ["share_id", "status"],
    },
}


async def handler(
    inputs: dict,
    ctx: Any,
) -> dict:
    """Revoke a share grant.

    Args:
        inputs: dict with share_id
        ctx: NodeContext with conn (from caller tx), audit scope

    Returns:
        dict with share_id, status
    """
    conn = ctx.conn
    user_id = ctx.audit_scope.user_id

    share_id = inputs["share_id"]

    # Revoke
    await _monitoring_sharing_service.revoke_share(conn, share_id, user_id)

    return {"share_id": share_id, "status": "revoked"}
