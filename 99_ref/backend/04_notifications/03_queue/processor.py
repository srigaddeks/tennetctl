from __future__ import annotations

import asyncio
import re
import time
import uuid
from datetime import timedelta
from importlib import import_module
from urllib.parse import quote

_constants_module = import_module("backend.04_notifications.constants")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_database_module = import_module("backend.01_core.database")
_settings_module = import_module("backend.00_config.settings")
_channel_base_module = import_module("backend.04_notifications.04_channels.base")
_time_module = import_module("backend.01_core.time_utils")

NOTIFICATION_SCHEMA = _constants_module.NOTIFICATION_SCHEMA
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
DatabasePool = _database_module.DatabasePool
Settings = _settings_module.Settings
ChannelProvider = _channel_base_module.ChannelProvider
utc_now_sql = _time_module.utc_now_sql

from .repository import QueueRepository

_LOGGER = get_logger("backend.notifications.queue.processor")
_sse_module = import_module("backend.04_notifications.10_sse.manager")

# Exponential backoff base in seconds
_BACKOFF_BASE = 30
_BACKOFF_MULTIPLIER = 2
_DEFAULT_BATCH_SIZE = 20
_DEFAULT_POLL_INTERVAL = 5.0  # seconds


@instrument_class_methods(
    namespace="notifications.queue.processor",
    logger_name="backend.notifications.queue.processor.instrumentation",
)
class NotificationQueueProcessor:
    """Background queue processor that dequeues and delivers notifications."""

    def __init__(
        self,
        *,
        database_pool: DatabasePool,
        settings: Settings,
        email_provider: ChannelProvider | None = None,
        webpush_provider: ChannelProvider | None = None,
    ) -> None:
        self._database_pool = database_pool
        self._settings = settings
        self._email_provider = email_provider
        self._webpush_provider = webpush_provider
        self._repository = QueueRepository()
        self._batch_size = _DEFAULT_BATCH_SIZE
        self._poll_interval = _DEFAULT_POLL_INTERVAL
        self._running = False

    async def run_loop(self) -> None:
        """Main processing loop -- runs as asyncio background task."""
        self._running = True
        _LOGGER.info(
            "queue_processor_started",
            extra={
                "action": "run_loop",
                "outcome": "started",
                "batch_size": self._batch_size,
                "poll_interval": self._poll_interval,
            },
        )
        while self._running:
            try:
                processed = await self._process_batch()
                if processed == 0:
                    await asyncio.sleep(self._poll_interval)
            except asyncio.CancelledError:
                _LOGGER.info(
                    "queue_processor_cancelled",
                    extra={"action": "run_loop", "outcome": "cancelled"},
                )
                break
            except Exception:
                _LOGGER.error(
                    "queue_processor_error",
                    exc_info=True,
                    extra={"action": "run_loop", "outcome": "error"},
                )
                await asyncio.sleep(self._poll_interval)

    async def stop(self) -> None:
        """Signal the processor to stop after the current batch."""
        self._running = False

    async def _process_batch(self) -> int:
        """Process a batch of queued notifications. Returns count processed."""
        _env = getattr(self._settings, "environment", None)
        async with self._database_pool.transaction() as conn:
            rows = await self._repository.fetch_batch_for_processing(
                conn, self._batch_size, source_env=_env,
            )
            for row in rows:
                await self._process_one(conn, row)
            return len(rows)

    async def _process_one(self, conn, row) -> None:
        """Process a single notification."""
        notification_id = row["id"]
        channel_code = row["channel_code"]
        now = utc_now_sql()

        # Cooldown check: suppress if same user+type was sent too recently
        if row["user_id"] and row["notification_type_code"]:
            try:
                cooldown = await self._check_cooldown(
                    conn, row["user_id"], row["notification_type_code"], notification_id
                )
            except Exception:
                _LOGGER.warning("cooldown_check_failed", exc_info=True, extra={"notification_id": notification_id})
                cooldown = None
            if cooldown:
                await self._repository.update_status(
                    conn,
                    notification_id,
                    "suppressed",
                    last_error=f"Suppressed: cooldown ({cooldown}s) not elapsed for type {row['notification_type_code']}",
                    attempt_count=row["attempt_count"],
                )
                _LOGGER.info(
                    "notification_suppressed_cooldown",
                    extra={
                        "action": "process_one",
                        "outcome": "suppressed",
                        "notification_id": notification_id,
                        "notification_type_code": row["notification_type_code"],
                        "cooldown_seconds": cooldown,
                    },
                )
                return

        # Update to processing
        await self._repository.update_status(
            conn, notification_id, "processing"
        )

        # Get appropriate provider
        provider = self._get_provider(channel_code)
        if not provider:
            _LOGGER.warning(
                "no_provider_for_channel",
                extra={
                    "action": "process_one",
                    "outcome": "skipped",
                    "channel_code": channel_code,
                    "notification_id": notification_id,
                },
            )
            await self._repository.update_status(
                conn,
                notification_id,
                "dead_letter",
                last_error=f"No provider configured for channel: {channel_code}",
                attempt_count=row["attempt_count"] + 1,
            )
            return

        # Determine recipient
        recipient = row["recipient_email"] or row["recipient_push_endpoint"] or ""

        # Resolve HTML and plain-text bodies
        html_body = row["rendered_body_html"] or None
        text_body = row["rendered_body"] or None

        # Fallback: if rendered_body_html is empty but rendered_body looks like HTML
        if not html_body and text_body and text_body.strip().startswith("<"):
            html_body = text_body
            text_body = None

        # For email: inject tracking and build metadata
        send_metadata: dict[str, str] | None = None
        if channel_code == "email":
            if html_body:
                try:
                    html_body = self._inject_tracking(notification_id, html_body)
                except Exception:
                    _LOGGER.warning("tracking_injection_failed", exc_info=True, extra={"notification_id": notification_id})
            send_metadata = {"priority": row.get("priority_code") or ""}
            # Build unsubscribe URL for RFC 8058 header
            _tracking_base = getattr(self._settings, "notification_tracking_base_url", None)
            if _tracking_base and row["user_id"] and row["notification_type_code"]:
                send_metadata["unsubscribe_url"] = (
                    f"{_tracking_base.rstrip('/')}/api/v1/notifications/unsubscribe"
                    f"?user_id={quote(str(row['user_id']), safe='')}"
                    f"&type={quote(str(row['notification_type_code']), safe='')}"
                )

        # Send — always pass both html and text so the provider can build proper MIME
        start_time = time.monotonic()
        result = await provider.send(
            recipient=recipient,
            subject=row["rendered_subject"],
            body_html=html_body,
            body_text=text_body,
            body_short=None,
            metadata=send_metadata,
        )
        duration_ms = int((time.monotonic() - start_time) * 1000)

        new_attempt_count = row["attempt_count"] + 1

        # Log delivery attempt
        await self._repository.create_delivery_log(
            conn,
            log_id=str(uuid.uuid4()),
            notification_id=notification_id,
            channel_code=channel_code,
            attempt_number=new_attempt_count,
            status="sent" if result.success else "failed",
            provider_response=result.provider_response,
            provider_message_id=result.provider_message_id,
            error_code=result.error_code,
            error_message=result.error_message,
            duration_ms=duration_ms,
        )

        if result.success:
            await self._repository.update_status(
                conn,
                notification_id,
                "sent",
                attempt_count=new_attempt_count,
                completed_at=now,
            )
            _LOGGER.info(
                "notification_sent",
                extra={
                    "action": "process_one",
                    "outcome": "success",
                    "notification_id": notification_id,
                    "channel_code": channel_code,
                    "duration_ms": duration_ms,
                },
            )
            # Push real-time SSE event to connected inbox clients.
            if row["user_id"]:
                _sse_module.push_event(
                    str(row["user_id"]),
                    {
                        "type": "notification",
                        "notification_id": str(notification_id),
                        "channel_code": channel_code,
                        "notification_type_code": row.get("notification_type_code"),
                        "rendered_subject": row.get("rendered_subject"),
                    },
                )
        else:
            # 410 Gone — deactivate the push subscription so we never retry it
            if result.error_code == "subscription_gone" and row.get("recipient_push_endpoint"):
                _schema = f'"{NOTIFICATION_SCHEMA}"'
                endpoint_json = row["recipient_push_endpoint"]
                try:
                    import json as _json
                    _ep = _json.loads(endpoint_json).get("endpoint", endpoint_json)
                except Exception:
                    _ep = endpoint_json
                await conn.execute(
                    f"""
                    UPDATE {_schema}."13_fct_web_push_subscriptions"
                    SET is_active = FALSE, updated_at = NOW()
                    WHERE endpoint = $1
                    """,
                    _ep,
                )
                _LOGGER.info(
                    "push_subscription_deactivated_410",
                    extra={
                        "action": "process_one",
                        "outcome": "subscription_gone",
                        "notification_id": notification_id,
                    },
                )
                # Dead-letter without retrying
                await self._repository.update_status(
                    conn,
                    notification_id,
                    "dead_letter",
                    attempt_count=new_attempt_count,
                    last_error="Push endpoint returned 410 Gone — subscription deactivated",
                )
                return

            # Determine if we should retry or dead-letter
            if new_attempt_count >= row["max_attempts"]:
                new_status = "dead_letter"
                next_retry_at = None
            else:
                new_status = "failed"
                # Exponential backoff: 30s, 60s, 120s, ...
                backoff = _BACKOFF_BASE * (_BACKOFF_MULTIPLIER ** (new_attempt_count - 1))
                next_retry_at = now + timedelta(seconds=backoff)

            await self._repository.update_status(
                conn,
                notification_id,
                new_status,
                attempt_count=new_attempt_count,
                next_retry_at=next_retry_at,
                last_error=result.error_message,
            )
            _LOGGER.warning(
                "notification_send_failed",
                extra={
                    "action": "process_one",
                    "outcome": new_status,
                    "notification_id": notification_id,
                    "channel_code": channel_code,
                    "attempt_count": new_attempt_count,
                    "max_attempts": row["max_attempts"],
                    "error_code": result.error_code,
                    "duration_ms": duration_ms,
                },
            )

    async def _check_cooldown(
        self, conn, user_id: str, notification_type_code: str, current_notification_id: str
    ) -> int | None:
        """Return cooldown_seconds if suppressed, None if OK to send."""
        SCHEMA = f'"{NOTIFICATION_SCHEMA}"'
        row = await conn.fetchrow(
            f"""
            SELECT nt.cooldown_seconds
            FROM {SCHEMA}."04_dim_notification_types" nt
            WHERE nt.code = $1 AND nt.cooldown_seconds IS NOT NULL AND nt.cooldown_seconds > 0
            """,
            notification_type_code,
        )
        if not row:
            return None
        cooldown = row["cooldown_seconds"]
        recent = await conn.fetchrow(
            f"""
            SELECT id FROM {SCHEMA}."20_trx_notification_queue"
            WHERE user_id = $1
              AND notification_type_code = $2
              AND id != $3
              AND status_code IN ('sent', 'delivered', 'opened', 'clicked')
              AND completed_at >= NOW() - make_interval(secs => $4)
            LIMIT 1
            """,
            user_id,
            notification_type_code,
            current_notification_id,
            cooldown,
        )
        return cooldown if recent else None

    def _get_provider(self, channel_code: str) -> ChannelProvider | None:
        if channel_code == "email":
            return self._email_provider
        if channel_code == "web_push":
            return self._webpush_provider
        return None

    # ── Email tracking injection (Mautic/Mailchimp-style) ───────────────

    _HREF_RE = re.compile(r'<a\s+([^>]*?)href=["\']([^"\']+)["\']', re.IGNORECASE)
    # URLs that must never be rewritten for tracking
    _SKIP_PREFIXES = ("#", "mailto:", "tel:", "data:", "cid:", "javascript:", "")

    def _inject_tracking(self, notification_id: str, body_html: str) -> str:
        """Inject open-tracking pixel and rewrite links for click tracking.

        Follows email marketing best practices (Mautic, Mailchimp, SendGrid):
        - Every <a href> is wrapped through a click-tracking redirect
        - A 1x1 transparent pixel is appended for open tracking
        - Unsubscribe links are preserved (not rewritten) for RFC 8058 compliance
        - Cache-busting query param on the tracking pixel to prevent email client caching
        """
        base_url = getattr(self._settings, "notification_tracking_base_url", None)
        if not base_url:
            return body_html

        base_url = base_url.rstrip("/")
        track_prefix = f"{base_url}/api/v1/notifications/track"

        # 1. Rewrite <a href="..."> for click tracking
        def _rewrite_link(match: re.Match) -> str:
            attrs = match.group(1)
            original_url = match.group(2)
            # Skip non-http links
            if any(original_url.startswith(p) for p in self._SKIP_PREFIXES):
                return match.group(0)
            # Skip unsubscribe links — RFC 8058 compliance
            if "unsubscribe" in original_url.lower():
                return match.group(0)
            # Skip already-tracked links (idempotent)
            if "/track/click/" in original_url:
                return match.group(0)
            tracked = f"{track_prefix}/click/{notification_id}?url={quote(original_url, safe='')}"
            return f'<a {attrs}href="{tracked}"'

        tracked_html = self._HREF_RE.sub(_rewrite_link, body_html)

        # 2. Inject 1x1 open-tracking pixel with cache-busting nonce
        nonce = uuid.uuid4().hex[:8]
        pixel_url = f"{track_prefix}/open/{notification_id}?_cb={nonce}"
        pixel_tag = (
            f'<img src="{pixel_url}" width="1" height="1" '
            f'style="display:none;width:1px;height:1px;border:0;overflow:hidden;" alt="" />'
        )

        # Case-insensitive </body> insertion
        body_close_idx = tracked_html.lower().rfind("</body>")
        if body_close_idx >= 0:
            tracked_html = tracked_html[:body_close_idx] + pixel_tag + tracked_html[body_close_idx:]
        else:
            tracked_html += pixel_tag

        return tracked_html
