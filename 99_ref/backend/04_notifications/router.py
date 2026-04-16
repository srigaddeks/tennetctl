from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status
from fastapi.responses import StreamingResponse

from .dependencies import get_notification_service
from .schemas import (
    DeliveryReportResponse,
    InboxResponse,
    MarkReadRequest,
    NotificationConfigResponse,
    NotificationDetailResponse,
    NotificationHistoryResponse,
    PreferenceMatrixResponse,
    PreferenceResponse,
    QueueActionRequest,
    QueueActionResponse,
    QueueAdminResponse,
    SendTestNotificationRequest,
    SendTestNotificationResponse,
    SetPreferenceRequest,
    SmtpConfigRequest,
    SmtpConfigResponse,
    SmtpTestRequest,
    SmtpTestResponse,
    WebPushSubscribeRequest,
    WebPushSubscriptionResponse,
)
from .service import NotificationService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")
_sse_module = import_module("backend.04_notifications.10_sse.manager")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/notifications", tags=["notifications"])


# ------------------------------------------------------------------ #
# Config (all dimension data in one call)
# ------------------------------------------------------------------ #


@router.get("/config", response_model=NotificationConfigResponse)
async def get_config(
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> NotificationConfigResponse:
    return await service.get_config()


# ------------------------------------------------------------------ #
# Preferences
# ------------------------------------------------------------------ #


@router.get("/preferences", response_model=PreferenceMatrixResponse)
async def list_preferences(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> PreferenceMatrixResponse:
    return await service.list_preferences(
        user_id=claims.subject, tenant_key=claims.tenant_key
    )


@router.put(
    "/preferences",
    response_model=PreferenceResponse,
    status_code=status.HTTP_200_OK,
)
async def set_preference(
    body: SetPreferenceRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> PreferenceResponse:
    return await service.set_preference(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.delete(
    "/preferences/{preference_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_preference(
    preference_id: str,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_preference(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        preference_id=preference_id,
    )


# ------------------------------------------------------------------ #
# Notification history
# ------------------------------------------------------------------ #


@router.get("/history", response_model=NotificationHistoryResponse)
async def get_notification_history(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> NotificationHistoryResponse:
    return await service.get_history(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        limit=limit,
        offset=offset,
    )


# ------------------------------------------------------------------ #
# Web push subscriptions
# ------------------------------------------------------------------ #


@router.get("/web-push/vapid-public-key")
async def get_vapid_public_key(
    service: Annotated[NotificationService, Depends(get_notification_service)],
) -> dict:
    """Return the VAPID public key (applicationServerKey) needed by the frontend to subscribe."""
    return {"vapid_public_key": service.get_vapid_public_key()}


@router.get("/web-push/subscriptions", response_model=list[WebPushSubscriptionResponse])
async def list_web_push_subscriptions(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> list[WebPushSubscriptionResponse]:
    return await service.list_web_push_subscriptions(
        user_id=claims.subject, tenant_key=claims.tenant_key
    )


@router.post(
    "/web-push/subscribe",
    response_model=WebPushSubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def subscribe_web_push(
    body: WebPushSubscribeRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> WebPushSubscriptionResponse:
    return await service.subscribe_web_push(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.post("/web-push/test")
async def send_test_web_push(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
    title: str = Query(default=None),
    body: str = Query(default=None),
    deep_link: str = Query(default="/notifications"),
) -> dict:
    """Fire a test push notification to all active subscriptions of the current user."""
    return await service.send_test_web_push(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        title=title,
        body=body,
        deep_link=deep_link,
    )


@router.delete(
    "/web-push/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def unsubscribe_web_push(
    subscription_id: str,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.unsubscribe_web_push(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        subscription_id=subscription_id,
    )


# ------------------------------------------------------------------ #
# User notification inbox
# ------------------------------------------------------------------ #


@router.get("/inbox", response_model=InboxResponse)
async def get_inbox(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
    is_read: bool | None = Query(default=None),
    category_code: str | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> InboxResponse:
    return await service.get_inbox(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        is_read=is_read,
        category_code=category_code,
        channel_code=channel_code,
        limit=limit,
        offset=offset,
    )


@router.post("/inbox/mark-read", status_code=status.HTTP_200_OK)
async def mark_inbox_read(
    body: MarkReadRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    return await service.mark_inbox_read(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        notification_ids=body.notification_ids,
    )


@router.get("/inbox/unread-count")
async def get_unread_count(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> dict:
    """Return the count of unread in-app notifications for the current user."""
    count = await service.get_unread_count(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
    )
    return {"unread_count": count}


@router.get("/inbox/stream")
async def inbox_stream(
    request: Request,
    token: str | None = Query(default=None, description="Bearer token (for EventSource clients that cannot set headers)"),
) -> StreamingResponse:
    """Server-Sent Events stream — delivers real-time inbox events to the browser.

    Accepts the JWT via the standard Authorization header **or** the `?token=` query
    parameter (needed because the browser EventSource API cannot set custom headers).
    """
    _auth_module = import_module("backend.03_auth_manage.dependencies")
    _service_module = import_module("backend.03_auth_manage.service")
    _errors_module = import_module("backend.01_core.errors")

    # Resolve token from query param or Authorization header
    bearer = token
    if not bearer:
        auth_header = request.headers.get("authorization", "")
        if auth_header.lower().startswith("bearer "):
            bearer = auth_header[7:]

    if not bearer:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Authentication required")

    auth_service = _service_module.AuthService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
    claims = auth_service.decode_access_token(bearer)
    claims = await auth_service.require_active_access_claims(claims)

    async def _generator():
        async for chunk in _sse_module.event_stream(claims.subject):
            if await request.is_disconnected():
                break
            yield chunk

    return StreamingResponse(
        _generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ------------------------------------------------------------------ #
# Admin: delivery queue monitor
# ------------------------------------------------------------------ #


@router.get("/queue", response_model=QueueAdminResponse)
async def get_queue_admin(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
    status_code: str | None = Query(default=None),
    channel_code: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> QueueAdminResponse:
    return await service.get_queue_admin(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        status_code=status_code,
        channel_code=channel_code,
        limit=limit,
        offset=offset,
    )


# ------------------------------------------------------------------ #
# Admin: SMTP configuration
# ------------------------------------------------------------------ #


@router.get("/smtp/config", response_model=SmtpConfigResponse)
async def get_smtp_config(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> SmtpConfigResponse:
    return await service.get_smtp_config(user_id=claims.subject)


@router.put("/smtp/config", response_model=SmtpConfigResponse)
async def save_smtp_config(
    body: SmtpConfigRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> SmtpConfigResponse:
    return await service.save_smtp_config(user_id=claims.subject, request=body)


@router.post("/smtp/test", response_model=SmtpTestResponse)
async def test_smtp(
    body: SmtpTestRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> SmtpTestResponse:
    return await service.test_smtp(user_id=claims.subject, request=body)


# ------------------------------------------------------------------ #
# Admin: send test notification
# ------------------------------------------------------------------ #


@router.post(
    "/send-test",
    response_model=SendTestNotificationResponse,
    status_code=status.HTTP_200_OK,
)
async def send_test_notification(
    body: SendTestNotificationRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> SendTestNotificationResponse:
    return await service.send_test_notification(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=body,
    )


# ------------------------------------------------------------------ #
# Admin: delivery reports
# ------------------------------------------------------------------ #


@router.get("/reports/delivery", response_model=DeliveryReportResponse)
async def get_delivery_report(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
    period_hours: int = Query(default=24, ge=1, le=720),
) -> DeliveryReportResponse:
    return await service.get_delivery_report(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        period_hours=period_hours,
    )


# ------------------------------------------------------------------ #
# Admin: queue item detail (delivery logs + tracking events)
# ------------------------------------------------------------------ #


@router.get("/queue/{notification_id}", response_model=NotificationDetailResponse)
async def get_notification_detail(
    notification_id: str,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> NotificationDetailResponse:
    return await service.get_notification_detail(
        user_id=claims.subject,
        notification_id=notification_id,
        tenant_key=claims.tenant_key,
    )


@router.post(
    "/queue/{notification_id}/retry",
    response_model=QueueActionResponse,
)
async def retry_queue_item(
    notification_id: str,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> QueueActionResponse:
    return await service.retry_queue_item(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        notification_id=notification_id,
    )


@router.post(
    "/queue/{notification_id}/dead-letter",
    response_model=QueueActionResponse,
)
async def dead_letter_queue_item(
    notification_id: str,
    body: QueueActionRequest,
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
) -> QueueActionResponse:
    return await service.dead_letter_queue_item(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        notification_id=notification_id,
        reason=body.reason,
    )


@router.post(
    "/queue/bulk-retry",
    response_model=QueueActionResponse,
    status_code=status.HTTP_200_OK,
)
async def bulk_retry_queue(
    service: Annotated[NotificationService, Depends(get_notification_service)],
    claims=Depends(get_current_access_claims),
    status_filter: str = Query(default="failed,dead_letter", description="Comma-separated status codes to retry"),
) -> QueueActionResponse:
    """Requeue all failed/dead_letter notifications — useful after an SMTP outage is resolved."""
    return await service.bulk_retry_queue(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        status_filter=status_filter,
    )


# ------------------------------------------------------------------ #
# Public: one-click email unsubscribe
# ------------------------------------------------------------------ #


@router.get(
    "/unsubscribe",
    status_code=status.HTTP_200_OK,
    tags=["notifications", "public"],
)
async def unsubscribe(
    token: str = Query(..., description="HMAC-signed unsubscribe token"),
    request: Request = None,
) -> dict:
    """One-click unsubscribe endpoint linked from email footers.

    Verifies the HMAC token and disables the matching notification preference.
    Safe to call without authentication — the token is the credential.
    """
    _unsubscribe_module = import_module("backend.04_notifications.11_unsubscribe.tokens")
    settings = request.app.state.settings
    try:
        user_id, category_code = _unsubscribe_module.verify_token(
            token, settings.notification_unsubscribe_secret
        )
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(exc))

    # Disable all preferences for this user + category via the service
    _db_pool = request.app.state.database_pool
    async with _db_pool.acquire() as conn:
        await conn.execute(
            f"""
            UPDATE "03_notifications"."17_lnk_user_notification_preferences"
            SET is_enabled = FALSE, updated_at = NOW()
            WHERE user_id = $1 AND category_code = $2
            """,
            user_id,
            category_code,
        )

    return {
        "success": True,
        "message": f"You have been unsubscribed from '{category_code}' notifications.",
    }


