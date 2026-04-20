"""API routes for dashboard sharing.

Admin endpoints (5):
- GET /v1/monitoring/dashboards/{id}/shares
- POST /v1/monitoring/dashboards/{id}/shares
- GET /v1/monitoring/dashboards/{id}/shares/{share_id}
- PATCH /v1/monitoring/dashboards/{id}/shares/{share_id}
- DELETE /v1/monitoring/dashboards/{id}/shares/{share_id}
- GET /v1/monitoring/dashboards/{id}/shares/{share_id}/events

Public edge endpoints (2):
- GET /api/share/dashboard/{token}
- POST /api/share/dashboard/{token}/unlock
"""

import time
from importlib import import_module

from fastapi import APIRouter, Depends, HTTPException, Request

from ... import service as monitoring_service
from .access import can_view
from .repository import get_share as get_share_db
from .repository import list_shares
from .repository import list_events
from .schemas import (
    CreateInternalShareRequest,
    CreatePublicShareRequest,
    DashboardShareDetailResponse,
    DashboardShareEventResponse,
    DashboardShareResponse,
    UnlockPublicShareRequest,
    UpdateShareRequest,
)
from .service import (
    create_internal_share,
    create_public_share,
    extend_expiry,
    record_passphrase_failure,
    record_view,
    revoke_share,
    rotate_public_token,
    set_passphrase,
    soft_delete,
    verify_passphrase,
)
from . import token as token_module

_core_middleware = import_module("backend.01_core.middleware.auth")
_core_response = import_module("backend.01_core.response")

router = APIRouter()


# ========== ADMIN ROUTES (requires IAM auth) ==========


@router.get("/v1/monitoring/dashboards/{dashboard_id}/shares")
async def list_dashboard_shares(
    dashboard_id: str,
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    """List shares for a dashboard (admin only)."""
    # Auth check: user must own dashboard or have admin role
    # Simplified: just check if user has any grants
    user_id = request.state.session.user_id if hasattr(request.state, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        shares = await list_shares(conn, dashboard_id, skip, limit)
        return _core_response.success(data=[dict(s) for s in shares])
    finally:
        await pool.release(conn)


@router.post("/v1/monitoring/dashboards/{dashboard_id}/shares")
async def create_share(
    dashboard_id: str,
    request: Request,
    body: CreateInternalShareRequest | CreatePublicShareRequest,
) -> dict:
    """Create a new share (internal user or public token)."""
    user_id = request.state.session.user_id if hasattr(request.state, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Get dashboard to verify ownership and org
        dashboard = await conn.fetchrow(
            'SELECT id, org_id, owner_user_id FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dashboard_id,
        )
        if not dashboard or dashboard["owner_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not dashboard owner")

        org_id = dashboard["org_id"]

        if body.scope == "internal_user":
            req = CreateInternalShareRequest(**body.model_dump())
            share = await create_internal_share(
                conn,
                dashboard_id,
                org_id,
                user_id,
                req.granted_to_user_id,
                req.expires_at,
            )
        else:  # public_token
            req = CreatePublicShareRequest(**body.model_dump())
            vault_client = getattr(request.app.state, "vault_client", None)
            share = await create_public_share(
                conn,
                dashboard_id,
                org_id,
                user_id,
                req.expires_at,
                req.passphrase,
                req.recipient_email,
                vault_client,
            )

        return _core_response.success(data=share, status_code=201)
    finally:
        await pool.release(conn)


@router.get("/v1/monitoring/dashboards/{dashboard_id}/shares/{share_id}")
async def get_share_detail(
    dashboard_id: str,
    share_id: str,
    request: Request,
) -> dict:
    """Get share detail (never returns plaintext token)."""
    user_id = request.state.session.user_id if hasattr(request.state, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Verify ownership
        dashboard = await conn.fetchrow(
            'SELECT owner_user_id FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dashboard_id,
        )
        if not dashboard or dashboard["owner_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not dashboard owner")

        share = await get_share_db(conn, share_id)
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")

        return _core_response.success(data=dict(share))
    finally:
        await pool.release(conn)


@router.patch("/v1/monitoring/dashboards/{dashboard_id}/shares/{share_id}")
async def update_share(
    dashboard_id: str,
    share_id: str,
    request: Request,
    body: UpdateShareRequest,
) -> dict:
    """Update share (extend expiry, set passphrase, rotate token, revoke)."""
    user_id = request.state.session.user_id if hasattr(request.state, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Verify ownership
        dashboard = await conn.fetchrow(
            'SELECT owner_user_id FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dashboard_id,
        )
        if not dashboard or dashboard["owner_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not dashboard owner")

        # Revoke?
        if body.revoked_at == "now":
            await revoke_share(conn, share_id, user_id)
        else:
            # Extend expiry?
            if body.expires_at is not None:
                await extend_expiry(conn, share_id, body.expires_at)

            # Set passphrase?
            if body.passphrase is not None:
                await set_passphrase(conn, share_id, body.passphrase)

            # Rotate token?
            if body.rotate_token:
                vault_client = getattr(request.app.state, "vault_client", None)
                share = await rotate_public_token(
                    conn, share_id, user_id, vault_client
                )
                return _core_response.success(data=share)

        share = await get_share_db(conn, share_id)
        return _core_response.success(data=dict(share) if share else {})
    finally:
        await pool.release(conn)


@router.delete("/v1/monitoring/dashboards/{dashboard_id}/shares/{share_id}")
async def delete_share(
    dashboard_id: str,
    share_id: str,
    request: Request,
) -> dict:
    """Soft-delete a share."""
    user_id = request.state.session.user_id if hasattr(request.state, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Verify ownership
        dashboard = await conn.fetchrow(
            'SELECT owner_user_id FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dashboard_id,
        )
        if not dashboard or dashboard["owner_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not dashboard owner")

        await soft_delete(conn, share_id)
        return _core_response.success(data={}, status_code=204)
    finally:
        await pool.release(conn)


@router.get("/v1/monitoring/dashboards/{dashboard_id}/shares/{share_id}/events")
async def get_share_events(
    dashboard_id: str,
    share_id: str,
    request: Request,
    skip: int = 0,
    limit: int = 100,
) -> dict:
    """Get event timeline for a share."""
    user_id = request.state.session.user_id if hasattr(request.state, "session") else None
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Verify ownership
        dashboard = await conn.fetchrow(
            'SELECT owner_user_id FROM "05_monitoring"."10_fct_monitoring_dashboards" WHERE id = $1',
            dashboard_id,
        )
        if not dashboard or dashboard["owner_user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Not dashboard owner")

        events = await list_events(conn, share_id, skip, limit)
        return _core_response.success(data=[dict(e) for e in events])
    finally:
        await pool.release(conn)


# ========== PUBLIC EDGE ROUTES (no IAM required; share_token middleware) ==========


@router.get("/api/share/dashboard/{token}")
async def view_shared_dashboard(
    token: str,
    request: Request,
) -> dict:
    """View a shared dashboard via token (read-only)."""
    # Middleware should have set share_claim if valid
    share_claim = getattr(request.state, "share_claim", None)
    if share_claim is None:
        raise HTTPException(status_code=401, detail="Invalid or missing share token")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Get share and check passphrase
        share = await get_share_db(conn, share_claim.share_id)
        if not share:
            raise HTTPException(status_code=404, detail="Share not found")

        # If passphrase protected, require unlock
        if share.get("has_passphrase"):
            # Check if session has passphrase_verified flag
            has_passphrase_session = getattr(
                request.state, "passphrase_verified", False
            )
            if not has_passphrase_session:
                raise HTTPException(
                    status_code=401,
                    detail="Passphrase required",
                    headers={"X-Share-Passphrase-Required": "true"},
                )

        # Record view
        viewer_ip = request.client.host if request.client else None
        viewer_ua = request.headers.get("user-agent")
        await record_view(conn, share_claim.share_id, viewer_ip, viewer_ua, None)

        # Return dashboard read-only payload
        dashboard_id = share["dashboard_id"]
        dashboard = await conn.fetchrow(
            """
            SELECT id, org_id, owner_user_id, name, description, layout, panel_count, created_at
            FROM "05_monitoring"."v_monitoring_dashboards"
            WHERE id = $1
            """,
            dashboard_id,
        )
        if not dashboard:
            raise HTTPException(status_code=404, detail="Dashboard not found")

        # Get panels (read-only)
        panels = await conn.fetch(
            """
            SELECT id, dashboard_id, title, panel_type, dsl, grid_pos, display_opts, created_at
            FROM "05_monitoring"."v_monitoring_panels"
            WHERE dashboard_id = $1
            """,
            dashboard_id,
        )

        return _core_response.success(
            data={
                "dashboard": dict(dashboard),
                "panels": [dict(p) for p in panels],
                "access": "read_only",
            }
        )
    finally:
        await pool.release(conn)


@router.post("/api/share/dashboard/{token}/unlock")
async def unlock_public_share(
    token: str,
    request: Request,
    body: UnlockPublicShareRequest,
) -> dict:
    """Unlock a passphrase-protected share."""
    share_claim = getattr(request.state, "share_claim", None)
    if share_claim is None:
        raise HTTPException(status_code=401, detail="Invalid or missing share token")

    pool = request.app.state.db_pool
    conn = await pool.acquire()
    try:
        # Verify passphrase
        is_valid = await verify_passphrase(
            conn, share_claim.share_id, body.passphrase
        )
        if not is_valid:
            # Record failure and check brute-force
            viewer_ip = request.client.host if request.client else None
            auto_revoked = await record_passphrase_failure(
                conn, share_claim.share_id, viewer_ip
            )
            raise HTTPException(
                status_code=401,
                detail="Invalid passphrase"
                if not auto_revoked
                else "Too many attempts; share revoked",
            )

        # Mark passphrase as verified in session
        request.state.passphrase_verified = True

        return _core_response.success(
            data={"status": "unlocked", "expires_in_seconds": 900}
        )
    finally:
        await pool.release(conn)
