"""Database repository for dashboard sharing.

All reads from v_monitoring_dashboard_shares view.
All writes to fct_monitoring_dashboard_shares + dtl_monitoring_dashboard_share_token tables.
"""

from datetime import datetime
from importlib import import_module
from typing import Any, Optional

_core_id = import_module("backend.01_core.id")


async def list_shares(
    conn: Any, dashboard_id: str, skip: int = 0, limit: int = 100
) -> list[dict]:
    """List all shares for a dashboard."""
    query = """
        SELECT
            id, dashboard_id, scope_code, granted_by_user_id, granted_to_user_id,
            grantee_display, recipient_email, status, has_passphrase, view_count,
            last_viewed_at, expires_at, revoked_at, created_at, updated_at
        FROM "05_monitoring"."v_monitoring_dashboard_shares"
        WHERE dashboard_id = $1
        ORDER BY created_at DESC
        OFFSET $2 LIMIT $3
    """
    return await conn.fetch(query, dashboard_id, skip, limit)


async def get_share(conn: Any, share_id: str) -> Optional[dict]:
    """Get a single share by ID."""
    query = """
        SELECT
            id, dashboard_id, scope_code, granted_by_user_id, granted_to_user_id,
            grantee_display, recipient_email, status, has_passphrase, view_count,
            last_viewed_at, expires_at, revoked_at, created_at, updated_at,
            token_hash, key_version
        FROM "05_monitoring"."v_monitoring_dashboard_shares"
        WHERE id = $1
    """
    return await conn.fetchrow(query, share_id)


async def create_internal_grant(
    conn: Any,
    dashboard_id: str,
    org_id: str,
    granted_by_user_id: str,
    granted_to_user_id: str,
    expires_at: Optional[datetime],
) -> str:
    """Create an internal user grant. Returns share ID."""
    share_id = _core_id.uuid7()
    query = """
        INSERT INTO "05_monitoring"."12_fct_monitoring_dashboard_shares"
            (id, org_id, dashboard_id, scope_id, granted_by_user_id, granted_to_user_id, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """
    await conn.execute(query, share_id, org_id, dashboard_id, 1, granted_by_user_id, granted_to_user_id, expires_at)
    return share_id


async def create_public_token_grant(
    conn: Any,
    dashboard_id: str,
    org_id: str,
    granted_by_user_id: str,
    expires_at: Optional[datetime],
    recipient_email: Optional[str],
    token_hash: str,
    key_version: int,
    passphrase_hash: Optional[str],
) -> str:
    """Create a public token share. Returns share ID."""
    share_id = _core_id.uuid7()

    # Insert share record
    query = """
        INSERT INTO "05_monitoring"."12_fct_monitoring_dashboard_shares"
            (id, org_id, dashboard_id, scope_id, granted_by_user_id, recipient_email, expires_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7)
    """
    await conn.execute(
        query, share_id, org_id, dashboard_id, 2, granted_by_user_id, recipient_email, expires_at
    )

    # Insert token metadata
    token_query = """
        INSERT INTO "05_monitoring"."22_dtl_monitoring_dashboard_share_token"
            (share_id, token_hash, key_version, passphrase_hash)
        VALUES ($1, $2, $3, $4)
    """
    await conn.execute(token_query, share_id, token_hash, key_version, passphrase_hash)

    return share_id


async def get_token_hash(conn: Any, share_id: str) -> Optional[str]:
    """Get token hash for a public share."""
    query = """
        SELECT token_hash
        FROM "05_monitoring"."22_dtl_monitoring_dashboard_share_token"
        WHERE share_id = $1
    """
    result = await conn.fetchval(query, share_id)
    return result


async def get_token_metadata(conn: Any, share_id: str) -> Optional[dict]:
    """Get token metadata (hash, key_version, passphrase_hash, view_count)."""
    query = """
        SELECT token_hash, key_version, passphrase_hash, view_count, last_viewed_at
        FROM "05_monitoring"."22_dtl_monitoring_dashboard_share_token"
        WHERE share_id = $1
    """
    return await conn.fetchrow(query, share_id)


async def update_share_expiry(
    conn: Any, share_id: str, expires_at: Optional[datetime]
) -> None:
    """Update share expiration."""
    query = """
        UPDATE "05_monitoring"."12_fct_monitoring_dashboard_shares"
        SET expires_at = $1, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
    """
    await conn.execute(query, expires_at, share_id)


async def update_passphrase(
    conn: Any, share_id: str, passphrase_hash: Optional[str]
) -> None:
    """Update passphrase hash."""
    query = """
        UPDATE "05_monitoring"."22_dtl_monitoring_dashboard_share_token"
        SET passphrase_hash = $1
        WHERE share_id = $2
    """
    await conn.execute(query, passphrase_hash, share_id)


async def rotate_token(
    conn: Any,
    share_id: str,
    token_hash: str,
    key_version: int,
) -> None:
    """Rotate token (update hash and key_version)."""
    query = """
        UPDATE "05_monitoring"."22_dtl_monitoring_dashboard_share_token"
        SET token_hash = $1, key_version = $2, view_count = 0, last_viewed_at = NULL
        WHERE share_id = $3
    """
    await conn.execute(query, token_hash, key_version, share_id)


async def revoke_share(
    conn: Any, share_id: str, revoked_by_user_id: str
) -> None:
    """Revoke a share immediately."""
    query = """
        UPDATE "05_monitoring"."12_fct_monitoring_dashboard_shares"
        SET revoked_at = CURRENT_TIMESTAMP, revoked_by_user_id = $1, updated_at = CURRENT_TIMESTAMP
        WHERE id = $2
    """
    await conn.execute(query, revoked_by_user_id, share_id)


async def is_share_revoked(conn: Any, share_id: str) -> bool:
    """Check if share is revoked."""
    query = """
        SELECT 1
        FROM "05_monitoring"."12_fct_monitoring_dashboard_shares"
        WHERE id = $1 AND revoked_at IS NOT NULL
    """
    result = await conn.fetchval(query, share_id)
    return result is not None


async def soft_delete_share(conn: Any, share_id: str) -> None:
    """Soft-delete a share."""
    query = """
        UPDATE "05_monitoring"."12_fct_monitoring_dashboard_shares"
        SET deleted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE id = $1
    """
    await conn.execute(query, share_id)


async def record_event(
    conn: Any,
    share_id: str,
    kind_id: int,
    actor_user_id: Optional[str],
    viewer_email: Optional[str],
    viewer_ip: Optional[str],
    viewer_ua: Optional[str],
    payload: dict,
) -> str:
    """Record an event. Returns event ID."""
    event_id = _core_id.uuid7()
    query = """
        INSERT INTO "05_monitoring"."63_evt_monitoring_dashboard_share_events"
            (id, share_id, kind_id, actor_user_id, viewer_email, viewer_ip, viewer_ua, payload)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
    """
    await conn.execute(
        query, event_id, share_id, kind_id, actor_user_id, viewer_email, viewer_ip, viewer_ua, payload
    )
    return event_id


async def list_events(
    conn: Any, share_id: str, skip: int = 0, limit: int = 100
) -> list[dict]:
    """List events for a share in chronological order."""
    query = """
        SELECT
            e.id,
            dk.code AS kind_code,
            e.actor_user_id,
            e.viewer_email,
            e.viewer_ip,
            e.viewer_ua,
            e.payload,
            e.occurred_at
        FROM "05_monitoring"."63_evt_monitoring_dashboard_share_events" e
        LEFT JOIN "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind" dk
            ON dk.id = e.kind_id
        WHERE e.share_id = $1
        ORDER BY e.occurred_at DESC
        OFFSET $2 LIMIT $3
    """
    return await conn.fetch(query, share_id, skip, limit)


async def increment_view_count(conn: Any, share_id: str) -> None:
    """Increment view count and update last_viewed_at."""
    query = """
        UPDATE "05_monitoring"."22_dtl_monitoring_dashboard_share_token"
        SET view_count = view_count + 1, last_viewed_at = CURRENT_TIMESTAMP
        WHERE share_id = $1
    """
    await conn.execute(query, share_id)


async def count_recent_passphrase_failures(
    conn: Any, share_id: str, viewer_ip: str, minutes: int = 10
) -> int:
    """Count passphrase failures for this share from this IP in the last N minutes."""
    query = """
        SELECT COUNT(*)
        FROM "05_monitoring"."63_evt_monitoring_dashboard_share_events" e
        WHERE e.share_id = $1
          AND e.kind_id = 7  -- passphrase_failed
          AND e.viewer_ip = $2::inet
          AND e.occurred_at > CURRENT_TIMESTAMP - INTERVAL '1 minute' * $3
    """
    result = await conn.fetchval(query, share_id, viewer_ip, minutes)
    return result or 0
