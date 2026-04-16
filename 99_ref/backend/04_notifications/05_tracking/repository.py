from __future__ import annotations

import asyncpg
from importlib import import_module

from ..models import TrackingEventRecord

SCHEMA = '"03_notifications"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="tracking.repository", logger_name="backend.notifications.tracking.repository.instrumentation")
class TrackingRepository:
    async def create_tracking_event(
        self,
        connection: asyncpg.Connection,
        *,
        event_id: str,
        notification_id: str,
        tracking_event_type_code: str,
        channel_code: str,
        click_url: str | None,
        user_agent: str | None,
        ip_address: str | None,
        now: datetime,
    ) -> TrackingEventRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."22_trx_tracking_events"
                (id, notification_id, tracking_event_type_code, channel_code,
                 click_url, user_agent, ip_address, occurred_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING id, notification_id, tracking_event_type_code, channel_code,
                      click_url, user_agent, ip_address,
                      occurred_at::text, created_at::text
            """,
            event_id,
            notification_id,
            tracking_event_type_code,
            channel_code,
            click_url,
            user_agent,
            ip_address,
            now,
            now,
        )
        return _row_to_tracking_event(row)

    async def get_notification_by_id(
        self, connection: asyncpg.Connection, notification_id: str
    ) -> asyncpg.Record | None:
        return await connection.fetchrow(
            f"""
            SELECT id, status_code, user_id, channel_code
            FROM {SCHEMA}."20_trx_notification_queue"
            WHERE id = $1
            """,
            notification_id,
        )

    async def update_notification_status(
        self,
        connection: asyncpg.Connection,
        notification_id: str,
        status_code: str,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."20_trx_notification_queue"
            SET status_code = $1, updated_at = NOW()
            WHERE id = $2
            """,
            status_code,
            notification_id,
        )


def _row_to_tracking_event(r) -> TrackingEventRecord:
    return TrackingEventRecord(
        id=r["id"],
        notification_id=r["notification_id"],
        tracking_event_type_code=r["tracking_event_type_code"],
        channel_code=r["channel_code"],
        click_url=r["click_url"],
        user_agent=r["user_agent"],
        ip_address=r["ip_address"],
        occurred_at=r["occurred_at"],
        created_at=r["created_at"],
    )
