from __future__ import annotations

import uuid
from importlib import import_module

from .repository import TrackingRepository

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.04_notifications.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
utc_now_sql = _time_module.utc_now_sql
NotificationStatus = _constants_module.NotificationStatus
TrackingEventType = _constants_module.TrackingEventType

# Statuses that can transition to opened
_OPENABLE_STATUSES = {NotificationStatus.SENT, NotificationStatus.DELIVERED}
# Statuses that can transition to clicked
_CLICKABLE_STATUSES = {
    NotificationStatus.SENT,
    NotificationStatus.DELIVERED,
    NotificationStatus.OPENED,
}


@instrument_class_methods(namespace="tracking.service", logger_name="backend.notifications.tracking.instrumentation")
class TrackingService:
    def __init__(
        self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TrackingRepository()
        self._logger = get_logger("backend.notifications.tracking")

    _DEDUP_WINDOW_SECONDS = 3600  # 1 hour — same event within window is deduplicated

    async def _has_recent_event(
        self, conn, notification_id: str, event_type: str,
    ) -> bool:
        """Check if a tracking event of this type was already recorded within the dedup window."""
        _schema = f'"{_constants_module.NOTIFICATION_SCHEMA}"'
        row = await conn.fetchrow(
            f"""
            SELECT 1 FROM {_schema}."22_trx_tracking_events"
            WHERE notification_id = $1
              AND tracking_event_type_code = $2
              AND occurred_at >= NOW() - make_interval(secs => $3)
            LIMIT 1
            """,
            notification_id,
            event_type,
            self._DEDUP_WINDOW_SECONDS,
        )
        return row is not None

    async def record_open(
        self, notification_id: str, user_agent: str | None, ip_address: str | None
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            notification = await self._repository.get_notification_by_id(conn, notification_id)
            if notification is None:
                return

            # Dedup: skip if already opened within the last hour
            if await self._has_recent_event(conn, notification_id, TrackingEventType.OPENED):
                return

            channel_code = notification["channel_code"]

            await self._repository.create_tracking_event(
                conn,
                event_id=str(uuid.uuid4()),
                notification_id=notification_id,
                tracking_event_type_code=TrackingEventType.OPENED,
                channel_code=channel_code,
                click_url=None,
                user_agent=user_agent,
                ip_address=ip_address,
                now=now,
            )

            current_status = notification["status_code"]
            if current_status in _OPENABLE_STATUSES:
                await self._repository.update_notification_status(
                    conn, notification_id, NotificationStatus.OPENED
                )

    async def record_click(
        self,
        notification_id: str,
        url: str,
        user_agent: str | None,
        ip_address: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            notification = await self._repository.get_notification_by_id(conn, notification_id)
            if notification is None:
                return

            # Dedup: skip if same URL clicked within the last hour
            _schema = f'"{_constants_module.NOTIFICATION_SCHEMA}"'
            dup = await conn.fetchrow(
                f"""
                SELECT 1 FROM {_schema}."22_trx_tracking_events"
                WHERE notification_id = $1
                  AND tracking_event_type_code = $2
                  AND click_url = $3
                  AND occurred_at >= NOW() - make_interval(secs => $4)
                LIMIT 1
                """,
                notification_id,
                TrackingEventType.CLICKED,
                url,
                self._DEDUP_WINDOW_SECONDS,
            )
            if dup is not None:
                return

            channel_code = notification["channel_code"]

            await self._repository.create_tracking_event(
                conn,
                event_id=str(uuid.uuid4()),
                notification_id=notification_id,
                tracking_event_type_code=TrackingEventType.CLICKED,
                channel_code=channel_code,
                click_url=url,
                user_agent=user_agent,
                ip_address=ip_address,
                now=now,
            )

            current_status = notification["status_code"]
            if current_status in _CLICKABLE_STATUSES:
                await self._repository.update_notification_status(
                    conn, notification_id, NotificationStatus.CLICKED
                )
