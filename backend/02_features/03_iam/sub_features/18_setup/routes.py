"""iam.setup — FastAPI routes.

Endpoints:
  GET  /v1/setup/status          → setup status (always public)
  POST /v1/setup/initial-admin   → create first super-admin (only in setup mode)
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_id: Any = import_module("backend.01_core.id")
_svc: Any = import_module(
    "backend.02_features.03_iam.sub_features.18_setup.service"
)
_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.18_setup.schemas"
)

router = APIRouter(prefix="/v1/setup", tags=["setup"])

_COOKIE_NAME = "tennetctl_session"
_COOKIE_MAX_AGE = 7 * 24 * 3600  # 7 days


@router.get("/status")
async def get_setup_status(request: Request):
    """Return setup status. Safe to call any time — never 503'd by middleware."""
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        user_count = await conn.fetchrow(
            'SELECT COUNT(*) AS cnt FROM "03_iam"."12_fct_users" WHERE deleted_at IS NULL',
        )
        count = int(user_count["cnt"]) if user_count else 0
        initialized = count > 0

        # Also check vault config as authoritative flag.
        if not initialized:
            try:
                vault = getattr(request.app.state, "vault", None)
                if vault is not None:
                    val = await vault.get("system.initialized")
                    if str(val).lower() == "true":
                        initialized = True
            except Exception:
                pass

    return _response.success({
        "initialized": initialized,
        "user_count": count,
        "setup_required": not initialized,
    })


@router.post("/initial-admin", status_code=201)
async def create_initial_admin(
    request: Request,
    body: _schemas.InitialAdminBody,
):
    """Create the first super-admin user. Returns TOTP secret + backup codes once."""
    pool = request.app.state.pool
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError(
            "VAULT_UNAVAILABLE",
            "Vault is required for initial admin setup.",
            503,
        )

    _ctx_mod: Any = import_module("backend.01_catalog.context")
    ctx = _ctx_mod.NodeContext(
        audit_category="setup",
        trace_id=_id.uuid7(),
        span_id=_id.uuid7(),
        user_id=None,
        session_id=None,
        org_id=None,
        workspace_id=None,
    )

    async with pool.acquire() as conn:
        result = await _svc.complete_initial_admin(
            pool,
            conn,
            ctx,
            email=body.email,
            password=body.password,
            display_name=body.display_name,
            vault_client=vault,
        )

    # Invalidate the setup mode cache on app.state.
    if hasattr(request.app.state, "setup_initialized"):
        request.app.state.setup_initialized = True

    from fastapi.responses import JSONResponse
    import datetime as _dt

    def _serialize(obj: object) -> object:
        """Recursively convert non-JSON-native types."""
        if isinstance(obj, dict):
            return {k: _serialize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_serialize(v) for v in obj]
        if isinstance(obj, _dt.datetime):
            return obj.isoformat()
        return obj

    content = _response.success(_serialize(result))
    response = JSONResponse(content=content, status_code=201)

    response.set_cookie(
        _COOKIE_NAME,
        result["session_token"],
        max_age=_COOKIE_MAX_AGE,
        httponly=True,
        samesite="lax",
        secure=False,  # local dev; set True in production behind TLS
    )
    return response
