"""FastAPI routes for iam.invites."""

from __future__ import annotations

from dataclasses import replace
from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request, Response

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_catalog_ctx: Any = import_module("backend.01_catalog.context")

_schemas: Any = import_module(
    "backend.02_features.03_iam.sub_features.17_invites.schemas"
)
_service: Any = import_module(
    "backend.02_features.03_iam.sub_features.17_invites.service"
)

InviteCreateBody  = _schemas.InviteCreateBody
AcceptInviteBody  = _schemas.AcceptInviteBody

router = APIRouter(tags=["iam.invites"])

SESSION_COOKIE = "tennetctl_session"


def _build_ctx(request: Request, pool: Any, *, audit_category: str = "system") -> Any:
    return _catalog_ctx.NodeContext(
        user_id=getattr(request.state, "user_id", None),
        session_id=getattr(request.state, "session_id", None),
        org_id=getattr(request.state, "org_id", None),
        workspace_id=None,
        trace_id=_core_id.uuid7(),
        span_id=_core_id.uuid7(),
        request_id=getattr(request.state, "request_id", "") or _core_id.uuid7(),
        audit_category=audit_category,
        pool=pool,
        extras={"pool": pool},
    )


def _vault(request: Request) -> Any:
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError("VAULT_DISABLED", "Vault not configured.", 503)
    return vault


def _set_session_cookie(request: Request, response: Response, token: str, max_age: int) -> None:
    secure = (
        request.url.scheme == "https"
        or request.headers.get("x-forwarded-proto", "").lower() == "https"
    )
    response.set_cookie(
        key=SESSION_COOKIE, value=token, max_age=max_age,
        httponly=True, samesite="lax", secure=secure, path="/",
    )


# ── Org-scoped invite endpoints ──────────────────────────────────────────────

@router.post("/v1/orgs/{org_id}/invites", status_code=201)
async def create_invite(org_id: str, body: InviteCreateBody, request: Request) -> dict:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            _raw_token, invite = await _service.create_invite(
                pool, conn, ctx,
                org_id=org_id,
                email=str(body.email),
                role_id=body.role_id,
                vault_client=vault,
            )
    # Never return the raw token — only the invite metadata
    return _response.success(
        {
            "id": invite["id"],
            "org_id": invite["org_id"],
            "email": invite["email"],
            "status": invite["status"],
            "expires_at": invite["expires_at"].isoformat() if invite["expires_at"] else None,
            "created_at": invite["created_at"].isoformat() if invite["created_at"] else None,
        },
    )


@router.get("/v1/orgs/{org_id}/invites", status_code=200)
async def list_invites(
    org_id: str,
    request: Request,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items, total = await _service.list_invites(
            conn,
            org_id=org_id,
            limit=limit,
            offset=offset,
        )

    def _fmt(row: dict) -> dict:
        return {
            "id": row["id"],
            "org_id": row["org_id"],
            "email": row["email"],
            "invited_by": row["invited_by"],
            "inviter_email": row.get("inviter_email"),
            "inviter_display_name": row.get("inviter_display_name"),
            "role_id": row.get("role_id"),
            "status": row["status"],
            "expires_at": row["expires_at"].isoformat() if row.get("expires_at") else None,
            "accepted_at": row["accepted_at"].isoformat() if row.get("accepted_at") else None,
            "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
            "updated_at": row["updated_at"].isoformat() if row.get("updated_at") else None,
        }

    return _response.paginated(
        [_fmt(r) for r in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.delete("/v1/orgs/{org_id}/invites/{invite_id}", status_code=204)
async def cancel_invite(org_id: str, invite_id: str, request: Request) -> Response:
    pool = request.app.state.pool
    ctx_base = _build_ctx(request, pool)
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            await _service.cancel_invite(
                pool, conn, ctx,
                org_id=org_id,
                invite_id=invite_id,
            )
    return Response(status_code=204)


# ── Public endpoint: accept invite ────────────────────────────────────────────

@router.post("/v1/auth/accept-invite", status_code=201)
async def accept_invite(body: AcceptInviteBody, request: Request) -> Response:
    pool = request.app.state.pool
    vault = _vault(request)
    ctx_base = _build_ctx(request, pool, audit_category="setup")
    async with pool.acquire() as conn:
        async with conn.transaction():
            ctx = replace(ctx_base, conn=conn)
            session_token, user, session = await _service.accept_invite(
                pool, conn, ctx,
                raw_token=body.token,
                password=body.password,
                display_name=body.display_name,
                vault_client=vault,
            )

    from datetime import datetime, timezone
    exp = session.get("expires_at")
    if isinstance(exp, str):
        delta = (
            datetime.fromisoformat(exp).replace(tzinfo=None)
            - datetime.now(timezone.utc).replace(tzinfo=None)
        )
        max_age = max(60, int(delta.total_seconds()))
    elif hasattr(exp, "isoformat"):
        delta = exp - datetime.now(timezone.utc).replace(tzinfo=None)
        max_age = max(60, int(delta.total_seconds()))
    else:
        max_age = 7 * 24 * 3600

    payload = {
        "token": session_token,
        "user": {
            "id": user["id"],
            "email": user.get("email"),
            "display_name": user.get("display_name"),
        },
    }
    resp = _response.success_response(payload, status_code=201)
    _set_session_cookie(request, resp, session_token, max_age)
    return resp
