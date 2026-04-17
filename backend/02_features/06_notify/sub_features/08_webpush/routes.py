"""
Routes for notify.webpush:
  GET    /v1/notify/webpush/vapid-public-key          — VAPID public key for browser subscription
  GET    /v1/notify/webpush/subscriptions             — list caller's active push subscriptions
  POST   /v1/notify/webpush/subscriptions             — register/update a browser push subscription
  DELETE /v1/notify/webpush/subscriptions/{sub_id}   — unregister a subscription
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_resp: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")
_core_id: Any = import_module("backend.01_core.id")
_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.repository"
)
_svc: Any = import_module(
    "backend.02_features.06_notify.sub_features.08_webpush.service"
)

router = APIRouter(tags=["notify.webpush"])


def _require_auth(request: Request) -> str:
    """Return user_id or raise 401."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    return user_id


@router.get("/v1/notify/webpush/vapid-public-key")
async def get_vapid_public_key_route(request: Request) -> dict:
    """Return the VAPID base64url public key. No auth required — it is public."""
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise _errors.AppError(
            "SERVICE_UNAVAILABLE", "Vault not available.", 503
        )
    try:
        pub_key = await vault.get(_svc._VAPID_PUBLIC_KEY)
    except Exception as exc:
        raise _errors.AppError(
            "SERVICE_UNAVAILABLE", "VAPID keys not yet initialized.", 503
        ) from exc
    return _resp.success({"public_key": pub_key})


@router.get("/v1/notify/webpush/subscriptions")
async def list_subscriptions_route(request: Request) -> dict:
    """List all active webpush subscriptions for the authenticated user."""
    user_id = _require_auth(request)
    async with request.app.state.pool.acquire() as conn:
        subs = await _repo.list_subscriptions(conn, user_id=user_id)
    return _resp.success({"subscriptions": subs, "total": len(subs)})


@router.post("/v1/notify/webpush/subscriptions", status_code=201)
async def create_subscription_route(request: Request) -> dict:
    """Register or refresh a browser push subscription.

    Body: { endpoint, p256dh, auth, device_label? }
    If endpoint already exists, the subscription is refreshed with the new keys.
    """
    user_id = _require_auth(request)
    org_id = getattr(request.state, "org_id", None) or "global"

    body = await request.json()
    endpoint = body.get("endpoint") or ""
    p256dh = body.get("p256dh") or ""
    auth = body.get("auth") or ""
    device_label = body.get("device_label")

    if not endpoint or not p256dh or not auth:
        raise _errors.AppError(
            "VALIDATION_ERROR", "endpoint, p256dh, and auth are required.", 422
        )

    sub_id = _core_id.uuid7()
    async with request.app.state.pool.acquire() as conn:
        row = await _repo.upsert_subscription(
            conn,
            id=sub_id,
            org_id=org_id,
            user_id=user_id,
            endpoint=endpoint,
            p256dh=p256dh,
            auth=auth,
            device_label=device_label,
            created_by=user_id,
        )
    return _resp.success({"subscription": row})


@router.delete("/v1/notify/webpush/subscriptions/{sub_id}", status_code=204)
async def delete_subscription_route(sub_id: str, request: Request) -> None:
    """Unregister a push subscription (soft-delete)."""
    user_id = _require_auth(request)
    async with request.app.state.pool.acquire() as conn:
        deleted = await _repo.soft_delete_subscription(
            conn, sub_id=sub_id, updated_by=user_id
        )
    if not deleted:
        raise _errors.AppError("NOT_FOUND", f"Subscription {sub_id!r} not found.", 404)
