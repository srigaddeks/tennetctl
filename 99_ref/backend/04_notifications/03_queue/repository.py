from __future__ import annotations

from importlib import import_module

import asyncpg

_constants_module = import_module("backend.04_notifications.constants")
_models_module = import_module("backend.04_notifications.models")
_telemetry_module = import_module("backend.01_core.telemetry")

NOTIFICATION_SCHEMA = _constants_module.NOTIFICATION_SCHEMA
NotificationQueueRecord = _models_module.NotificationQueueRecord
DeliveryLogRecord = _models_module.DeliveryLogRecord
instrument_class_methods = _telemetry_module.instrument_class_methods

SCHEMA = f'"{NOTIFICATION_SCHEMA}"'


@instrument_class_methods(
    namespace="notifications.queue.repository",
    logger_name="backend.notifications.queue.repository.instrumentation",
)
class QueueRepository:
    async def fetch_batch_for_processing(
        self,
        connection: asyncpg.Connection,
        limit: int,
        source_env: str | None = None,
    ) -> list[asyncpg.Record]:
        """Fetch a batch of queued notifications using SELECT FOR UPDATE SKIP LOCKED.

        When source_env is set, only picks up notifications created by this
        environment — prevents cross-environment duplicate sends when multiple
        environments (local, dev, staging) share the same database.
        """
        if source_env:
            return await connection.fetch(
                f"""
                SELECT q.*
                FROM {SCHEMA}."20_trx_notification_queue" q
                JOIN {SCHEMA}."06_dim_notification_priorities" p
                    ON p.code = q.priority_code
                WHERE q.status_code IN ('queued', 'failed')
                  AND q.scheduled_at <= NOW()
                  AND (q.next_retry_at IS NULL OR q.next_retry_at <= NOW())
                  AND (q.source_env = $2 OR q.source_env IS NULL)
                ORDER BY p.weight DESC, q.scheduled_at ASC
                LIMIT $1
                FOR UPDATE OF q SKIP LOCKED
                """,
                limit,
                source_env,
            )
        return await connection.fetch(
            f"""
            SELECT q.*
            FROM {SCHEMA}."20_trx_notification_queue" q
            JOIN {SCHEMA}."06_dim_notification_priorities" p
                ON p.code = q.priority_code
            WHERE q.status_code IN ('queued', 'failed')
              AND q.scheduled_at <= NOW()
              AND (q.next_retry_at IS NULL OR q.next_retry_at <= NOW())
            ORDER BY p.weight DESC, q.scheduled_at ASC
            LIMIT $1
            FOR UPDATE OF q SKIP LOCKED
            """,
            limit,
        )

    async def update_status(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
        status_code: str,
        **kwargs: object,
    ) -> None:
        """Update the status and optional fields of a notification queue entry."""
        fields: list[str] = ["status_code = $1", "updated_at = NOW()"]
        values: list[object] = [status_code]
        idx = 2

        for key in ("attempt_count", "next_retry_at", "last_error", "completed_at"):
            if key in kwargs:
                fields.append(f"{key} = ${idx}")
                values.append(kwargs[key])
                idx += 1

        values.append(notification_id)
        set_clause = ", ".join(fields)

        await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_trx_notification_queue"
            SET {set_clause}
            WHERE id = ${idx}
            """,
            *values,
        )

    async def create_delivery_log(
        self,
        connection: asyncpg.Connection,
        *,
        log_id: str,
        notification_id: str,
        channel_code: str,
        attempt_number: int,
        status: str,
        provider_response: str | None = None,
        provider_message_id: str | None = None,
        error_code: str | None = None,
        error_message: str | None = None,
        duration_ms: int | None = None,
    ) -> DeliveryLogRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."21_trx_delivery_log" (
                id, notification_id, channel_code, attempt_number, status,
                provider_response, provider_message_id, error_code, error_message,
                duration_ms, occurred_at, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
            RETURNING id, notification_id, channel_code, attempt_number, status,
                      provider_response, provider_message_id, error_code, error_message,
                      duration_ms, occurred_at::text, created_at::text
            """,
            log_id,
            notification_id,
            channel_code,
            attempt_number,
            status,
            provider_response,
            provider_message_id,
            error_code,
            error_message,
            duration_ms,
        )
        return _row_to_delivery_log(row)

    async def get_user_notification_history(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        *,
        tenant_key: str,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[NotificationQueueRecord], int]:
        """Return paginated notification history for a user."""
        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS total
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE user_id = $1 AND tenant_key = $2
            """,
            user_id,
            tenant_key,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, user_id, notification_type_code, channel_code,
                   status_code, priority_code, template_id, template_version_id,
                   source_audit_event_id, source_rule_id, broadcast_id,
                   rendered_subject, rendered_body, rendered_body_html,
                   recipient_email, recipient_push_endpoint,
                   scheduled_at::text, attempt_count, max_attempts,
                   next_retry_at::text, last_error, idempotency_key,
                   created_at::text, updated_at::text, completed_at::text
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE user_id = $1 AND tenant_key = $2
            ORDER BY created_at DESC
            LIMIT $3 OFFSET $4
            """,
            user_id,
            tenant_key,
            limit,
            offset,
        )
        return [_row_to_queue_record(r) for r in rows], total

    async def list_queue_admin(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        status_code: str | None = None,
        channel_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[asyncpg.Record], int]:
        """Return paginated platform-wide queue entries for admin monitoring."""
        conditions = ["tenant_key = $1"]
        values: list[object] = [tenant_key]
        idx = 2

        if status_code:
            conditions.append(f"status_code = ${idx}")
            values.append(status_code)
            idx += 1
        if channel_code:
            conditions.append(f"channel_code = ${idx}")
            values.append(channel_code)
            idx += 1

        where_clause = " AND ".join(conditions)

        count_row = await connection.fetchrow(
            f"""
            SELECT COUNT(*) AS total
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE {where_clause}
            """,
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, user_id, notification_type_code, channel_code,
                   status_code, priority_code, template_id, template_version_id,
                   source_audit_event_id, source_rule_id, broadcast_id,
                   rendered_subject,
                   recipient_email,
                   scheduled_at::text, attempt_count, max_attempts,
                   next_retry_at::text, last_error, idempotency_key,
                   created_at::text, updated_at::text, completed_at::text
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *values,
            limit,
            offset,
        )
        return rows, total

    async def get_queue_stats(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
    ) -> asyncpg.Record | None:
        """Return aggregate counts grouped by status_code."""
        return await connection.fetchrow(
            f"""
            SELECT
                COUNT(*) FILTER (WHERE status_code = 'queued')     AS queued,
                COUNT(*) FILTER (WHERE status_code = 'processing') AS processing,
                COUNT(*) FILTER (WHERE status_code = 'sent')       AS sent,
                COUNT(*) FILTER (WHERE status_code = 'delivered')  AS delivered,
                COUNT(*) FILTER (WHERE status_code = 'failed')     AS failed,
                COUNT(*) FILTER (WHERE status_code = 'dead_letter') AS dead_letter,
                COUNT(*) FILTER (WHERE status_code = 'suppressed') AS suppressed
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE tenant_key = $1
              AND created_at >= NOW() - INTERVAL '7 days'
            """,
            tenant_key,
        )

    async def get_notification_by_id(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
    ) -> NotificationQueueRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, user_id, notification_type_code, channel_code,
                   status_code, priority_code, template_id, template_version_id,
                   source_audit_event_id, source_rule_id, broadcast_id,
                   rendered_subject, rendered_body, rendered_body_html,
                   recipient_email, recipient_push_endpoint,
                   scheduled_at::text, attempt_count, max_attempts,
                   next_retry_at::text, last_error, idempotency_key,
                   created_at::text, updated_at::text, completed_at::text
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE id = $1
            """,
            notification_id,
        )
        return _row_to_queue_record(row) if row else None


    async def retry_notification(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
    ) -> bool:
        """Reset a failed/dead_letter notification to queued for retry. Returns True if updated."""
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_trx_notification_queue"
            SET status_code = 'queued',
                next_retry_at = NULL,
                last_error = NULL,
                updated_at = NOW()
            WHERE id = $1 AND status_code IN ('failed', 'dead_letter')
            """,
            notification_id,
        )
        return result != "UPDATE 0"

    async def dead_letter_notification(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
        reason: str,
    ) -> bool:
        """Move a notification to dead_letter. Returns True if updated."""
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_trx_notification_queue"
            SET status_code = 'dead_letter',
                last_error = $2,
                completed_at = NOW(),
                updated_at = NOW()
            WHERE id = $1 AND status_code NOT IN ('sent', 'delivered', 'opened', 'clicked', 'dead_letter')
            """,
            notification_id,
            reason,
        )
        return result != "UPDATE 0"

    async def get_delivery_logs(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
    ) -> list[asyncpg.Record]:
        """Return all delivery log entries for a notification."""
        return await connection.fetch(
            f"""
            SELECT id, notification_id, channel_code, attempt_number, status,
                   provider_response, provider_message_id, error_code, error_message,
                   duration_ms, occurred_at::text, created_at::text
            FROM {SCHEMA}."21_trx_delivery_log"
            WHERE notification_id = $1
            ORDER BY attempt_number ASC
            """,
            notification_id,
        )

    async def get_tracking_events(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
    ) -> list[asyncpg.Record]:
        """Return all tracking events for a notification."""
        return await connection.fetch(
            f"""
            SELECT id, notification_id, tracking_event_type_code, channel_code,
                   click_url, user_agent, ip_address,
                   occurred_at::text, created_at::text
            FROM {SCHEMA}."22_trx_tracking_events"
            WHERE notification_id = $1
            ORDER BY occurred_at ASC
            """,
            notification_id,
        )


def _row_to_queue_record(r: asyncpg.Record) -> NotificationQueueRecord:
    return NotificationQueueRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        user_id=r["user_id"],
        notification_type_code=r["notification_type_code"],
        channel_code=r["channel_code"],
        status_code=r["status_code"],
        priority_code=r["priority_code"],
        template_id=r["template_id"],
        template_version_id=r["template_version_id"],
        source_audit_event_id=r["source_audit_event_id"],
        source_rule_id=r["source_rule_id"],
        broadcast_id=r["broadcast_id"],
        rendered_subject=r["rendered_subject"],
        rendered_body=r["rendered_body"],
        rendered_body_html=r.get("rendered_body_html"),
        recipient_email=r["recipient_email"],
        recipient_push_endpoint=r["recipient_push_endpoint"],
        scheduled_at=r["scheduled_at"],
        attempt_count=r["attempt_count"],
        max_attempts=r["max_attempts"],
        next_retry_at=r["next_retry_at"],
        last_error=r["last_error"],
        idempotency_key=r["idempotency_key"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        completed_at=r["completed_at"],
    )


def _row_to_delivery_log(r: asyncpg.Record) -> DeliveryLogRecord:
    return DeliveryLogRecord(
        id=r["id"],
        notification_id=r["notification_id"],
        channel_code=r["channel_code"],
        attempt_number=r["attempt_number"],
        status=r["status"],
        provider_response=r["provider_response"],
        provider_message_id=r["provider_message_id"],
        error_code=r["error_code"],
        error_message=r["error_message"],
        duration_ms=r["duration_ms"],
        occurred_at=r["occurred_at"],
        created_at=r["created_at"],
    )
