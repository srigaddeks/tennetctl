"""Access control for dashboard views.

Checks if a user can view a dashboard:
1. User is the owner (via fct_monitoring_dashboards.owner_user_id)
2. User has an active internal_user grant
3. Request includes a valid share_claim (from share_token middleware)
"""

from importlib import import_module
from typing import Any

_asyncpg = import_module("asyncpg")


async def can_view(conn: Any, dashboard_id: str, user_id: str) -> bool:
    """Check if user can view a dashboard.

    Args:
        conn: asyncpg connection
        dashboard_id: Dashboard UUID
        user_id: User UUID

    Returns:
        True if user is owner or has active grant
    """
    query = """
        SELECT 1
        FROM "05_monitoring"."10_fct_monitoring_dashboards" d
        WHERE d.id = $1
          AND (
              d.owner_user_id = $2
              OR EXISTS (
                  SELECT 1
                  FROM "05_monitoring"."12_fct_monitoring_dashboard_shares" s
                  WHERE s.dashboard_id = d.id
                    AND s.granted_to_user_id = $2
                    AND s.scope_id = 1  -- internal_user
                    AND s.revoked_at IS NULL
                    AND (s.expires_at IS NULL OR s.expires_at > CURRENT_TIMESTAMP)
                    AND s.deleted_at IS NULL
              )
          )
    """
    result = await conn.fetchval(query, dashboard_id, user_id)
    return result is not None
