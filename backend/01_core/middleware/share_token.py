"""Middleware for share token verification.

Extracts and verifies share tokens from query param (?st=...) or Authorization header.
Sets request.state.share_claim if valid.
Emits expired/revoked events and returns appropriate HTTP responses.

Only active on /api/share/dashboard/* routes.
"""

import time
from importlib import import_module
from typing import Any

from fastapi import Request, Response
from fastapi.responses import JSONResponse

_monitoring_sharing_token = import_module(
    "backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.token"
)
_monitoring_sharing_repository = import_module(
    "backend.02_features.05_monitoring.sub_features.12_dashboard_sharing.repository"
)

# Sentinel for requests without share token
NO_SHARE_CLAIM = object()


async def share_token_middleware(request: Request, call_next: Any) -> Response:
    """Extract and verify share token from query param or Authorization header.

    Sets request.state.share_claim to ShareClaim if valid, or leaves it unset.
    Returns 410 Gone for expired tokens, 403 for revoked/invalid tokens.
    """
    # Default: no share claim
    request.state.share_claim = NO_SHARE_CLAIM

    # Extract token from ?st=... or Authorization: Share <token>
    token_str = None

    # Try query param first
    if "st" in request.query_params:
        token_str = request.query_params["st"]
    # Try Authorization header
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.lower().startswith("share "):
            token_str = auth_header[6:].strip()

    if not token_str:
        # No token provided; continue to handler
        return await call_next(request)

    # Verify token
    try:
        # Get connection from pool (stored by FastAPI lifespan)
        pool = request.app.state.db_pool
        conn = await pool.acquire()
        try:
            # Resolve Vault key for verification
            vault_client = request.app.state.vault_client

            def secret_resolver(key_version: int) -> bytes:
                """Resolve signing key from Vault."""
                # In production, load from Vault at monitoring/dashboard_share/signing_key/{key_version}
                # For now, use a test key (must be provisioned by ops)
                key_path = f"monitoring/dashboard_share/signing_key/{key_version}"
                try:
                    secret = vault_client.get_secret(key_path)
                    # Expect secret.data to contain 'secret_bytes' (base64-encoded)
                    import base64

                    secret_bytes = base64.b64decode(secret.get("secret_bytes", ""))
                    if len(secret_bytes) < 32:
                        raise ValueError(f"Key too short: {len(secret_bytes)} bytes")
                    return secret_bytes
                except Exception as e:
                    raise _monitoring_sharing_token.InvalidToken(
                        f"Failed to resolve signing key: {e}"
                    )

            # Verify token structure
            claim = _monitoring_sharing_token.verify(token_str, secret_resolver)

            # Check if expired
            if claim.exp < time.time():
                # Emit expired event and return 410
                share_id = claim.share_id
                try:
                    # Record expired event (if not already recorded)
                    await _monitoring_sharing_repository.record_event(
                        conn,
                        share_id=share_id,
                        kind_id=6,  # expired
                        actor_user_id=None,
                        viewer_email=None,
                        viewer_ip=request.client.host if request.client else None,
                        viewer_ua=request.headers.get("user-agent"),
                        payload={"reason": "token_expired"},
                    )
                except Exception:
                    pass  # Non-fatal; don't block response
                return JSONResponse(
                    {"ok": False, "error": {"code": "TOKEN_EXPIRED", "message": "Share token expired"}},
                    status_code=410,
                )

            # Check if revoked
            is_revoked = await _monitoring_sharing_repository.is_share_revoked(
                conn, share_id=claim.share_id
            )
            if is_revoked:
                return JSONResponse(
                    {"ok": False, "error": {"code": "SHARE_REVOKED", "message": "Share has been revoked"}},
                    status_code=403,
                )

            # Valid token; attach claim
            request.state.share_claim = claim
            request.state.share_token = token_str  # For passphrase validation

        finally:
            await pool.release(conn)

    except _monitoring_sharing_token.InvalidToken as e:
        return JSONResponse(
            {"ok": False, "error": {"code": "INVALID_TOKEN", "message": "Invalid share token"}},
            status_code=403,
        )

    return await call_next(request)
