"""Routes for notify.suppression.

/v1/notify/suppressions — session-only CRUD for admins.
/v1/notify/unsubscribe — public, cookie-less, one-click (RFC 8058).
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

_errors: Any = import_module("backend.01_core.errors")
_response: Any = import_module("backend.01_core.response")
_core_id: Any = import_module("backend.01_core.id")
_schemas: Any = import_module("backend.02_features.06_notify.sub_features.16_suppression.schemas")
_service: Any = import_module("backend.02_features.06_notify.sub_features.16_suppression.service")
SuppressionRow = _schemas.SuppressionRow
SuppressionAdd = _schemas.SuppressionAdd


router = APIRouter(tags=["notify.suppression"])


# ── Admin CRUD (session auth) ─────────────────────────────────────────────

@router.get("/v1/notify/suppressions", status_code=200)
async def list_suppressions_route(request: Request) -> dict:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    org_id = request.query_params.get("org_id") or getattr(request.state, "org_id", None)
    if not org_id:
        raise _errors.ValidationError("org_id is required")

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        items = await _service.list_suppressions(conn, org_id=org_id)
    data = [SuppressionRow(**r).model_dump() for r in items]
    return _response.success({"items": data, "total": len(data)})


@router.post("/v1/notify/suppressions", status_code=201)
async def add_suppression_route(request: Request, body: SuppressionAdd) -> dict:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await _service.add_suppression(
            conn,
            org_id=body.org_id,
            email=str(body.email),
            reason_code=body.reason_code,
            created_by=user_id,
            notes=body.notes,
        )
    if row is None:
        raise _errors.AppError("INTERNAL", "Failed to add suppression.", 500)
    return _response.success(SuppressionRow(**row).model_dump())


@router.delete("/v1/notify/suppressions/{id}", status_code=204)
async def delete_suppression_route(request: Request, id: str) -> None:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)

    pool = request.app.state.pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            'SELECT org_id, email FROM "06_notify"."v_notify_suppressions" WHERE id = $1',
            id,
        )
        if row is None:
            raise _errors.NotFoundError(f"suppression {id!r} not found")
        await _service.remove_suppression(conn, org_id=row["org_id"], email=row["email"])


# ── Public unsubscribe endpoints (no auth required; HMAC-signed tokens) ───

_UNSUB_HTML = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Unsubscribed</title>
<style>body{font-family:system-ui,sans-serif;max-width:480px;margin:80px auto;padding:0 20px;color:#18181b}h1{font-size:20px;margin-bottom:8px}p{color:#71717a;line-height:1.5}</style></head>
<body><h1>You've been unsubscribed</h1>
<p>The address <strong>{email}</strong> has been removed from <strong>{category}</strong> emails.</p>
<p>If this was a mistake, sign in to your account and re-enable this category in your notification preferences.</p>
</body></html>"""


async def _apply_unsubscribe(
    request: Request, token: str,
) -> tuple[str, str]:
    """Validate token, flip preferences, add to suppression list. Returns (email, category_code)."""
    pool = request.app.state.pool
    vault = request.app.state.vault
    if vault is None:
        raise _errors.AppError("SERVICE_UNAVAILABLE", "Vault not ready.", 503)

    signing_key = await _service._signing_key_bytes(vault)
    payload = _service.parse_unsubscribe_token(token, signing_key)
    if payload is None:
        raise _errors.ValidationError("invalid or expired unsubscribe token")

    org_id = payload["org_id"]
    email = payload["email"]
    category_code = payload.get("category_code") or "marketing"

    async with pool.acquire() as conn:
        # Suppression list is the authoritative block — it runs BEFORE the
        # preferences check in the email sender, and the recipient address
        # is what we have in the token (not necessarily mapped to a user).
        await _service.add_suppression(
            conn,
            org_id=org_id,
            email=email,
            reason_code="unsubscribe",
            created_by="unsubscribe-link",
            notes=f"category={category_code}",
        )

    return email, category_code


@router.get("/v1/notify/unsubscribe", status_code=200, response_class=HTMLResponse)
async def unsubscribe_preview_route(request: Request, token: str) -> HTMLResponse:
    email, category = await _apply_unsubscribe(request, token)
    return HTMLResponse(content=_UNSUB_HTML.format(email=email, category=category))


@router.post("/v1/notify/unsubscribe", status_code=200)
async def unsubscribe_one_click_route(request: Request) -> dict:
    """RFC 8058 one-click unsubscribe — token on query string, form-encoded body."""
    token: str | None = request.query_params.get("token")
    if not token:
        # Body may carry the token instead (some mail clients POST the URL).
        try:
            form = await request.form()
            raw = form.get("token") if form else None
            token = raw if isinstance(raw, str) else None
        except Exception:
            token = None
    if not token:
        raise _errors.ValidationError("token is required")
    email, category = await _apply_unsubscribe(request, token)
    return _response.success({"email": email, "category": category, "unsubscribed": True})
