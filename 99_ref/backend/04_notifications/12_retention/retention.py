from __future__ import annotations

"""Notification inbox retention background task.

Runs once per day:
- Archive (mark is_archived=TRUE) notifications older than ARCHIVE_AFTER_DAYS.
- Hard-delete archived notifications older than DELETE_AFTER_DAYS.

Both thresholds are configurable via settings.
"""

import asyncio
import logging
from importlib import import_module

_LOGGER = logging.getLogger("backend.notifications.retention")

# Defaults: archive after 90 days, hard-delete after 365 days.
_DEFAULT_ARCHIVE_DAYS = 90
_DEFAULT_DELETE_DAYS = 365
_RUN_INTERVAL_SECONDS = 86400  # 24 hours


class InboxRetentionTask:
    def __init__(
        self,
        *,
        database_pool,
        archive_after_days: int = _DEFAULT_ARCHIVE_DAYS,
        delete_after_days: int = _DEFAULT_DELETE_DAYS,
    ) -> None:
        self._pool = database_pool
        self._archive_after = archive_after_days
        self._delete_after = delete_after_days
        self._running = False
        self._task: asyncio.Task | None = None

    def start(self) -> None:
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self) -> None:
        _LOGGER.info("inbox_retention_started")
        while self._running:
            try:
                await self._run_once()
            except asyncio.CancelledError:
                break
            except Exception:
                _LOGGER.error("inbox_retention_error", exc_info=True)
            try:
                await asyncio.sleep(_RUN_INTERVAL_SECONDS)
            except asyncio.CancelledError:
                break

    async def _run_once(self) -> None:
        schema = '"03_notifications"'
        async with self._pool.acquire() as conn:
            # Archive old delivered notifications
            archived = await conn.execute(
                f"""
                UPDATE {schema}."20_trx_notification_queue"
                SET is_archived = TRUE, updated_at = NOW()
                WHERE is_archived = FALSE
                  AND status_code IN ('sent', 'delivered', 'opened', 'clicked')
                  AND completed_at < NOW() - make_interval(days => $1)
                """,
                self._archive_after,
            )
            # Hard-delete very old archived notifications
            deleted = await conn.execute(
                f"""
                DELETE FROM {schema}."20_trx_notification_queue"
                WHERE is_archived = TRUE
                  AND completed_at < NOW() - make_interval(days => $1)
                """,
                self._delete_after,
            )

        _LOGGER.info(
            "inbox_retention_ran",
            extra={
                "archived": archived,
                "deleted": deleted,
                "archive_after_days": self._archive_after,
                "delete_after_days": self._delete_after,
            },
        )
