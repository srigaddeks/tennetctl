"""Partition manager — runs monitoring_partition_manager() daily at 03:00 UTC.

Also runs once immediately on startup to ensure today/tomorrow partitions exist.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

logger = logging.getLogger("tennetctl.monitoring.partition_manager")


class PartitionManager:
    def __init__(self, pool: Any) -> None:
        self._pool = pool
        self._task: asyncio.Task[None] | None = None
        self._stopped = False
        self.heartbeat_at: datetime | None = None

    async def _run_once(self) -> None:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                'SELECT * FROM "05_monitoring".monitoring_partition_manager()'
            )
        total_created = sum(r["created"] for r in rows)
        total_dropped = sum(r["dropped"] for r in rows)
        logger.info(
            "partition manager: %d created, %d dropped across %d tables",
            total_created, total_dropped, len(rows),
        )
        self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)

    def _sleep_s_until_0300_utc(self) -> float:
        now = datetime.now(timezone.utc)
        target = now.replace(hour=3, minute=0, second=0, microsecond=0)
        if target <= now:
            target = target + timedelta(days=1)
        return max(1.0, (target - now).total_seconds())

    async def _loop(self) -> None:
        # Run once immediately so partitions for today/tomorrow exist.
        try:
            await self._run_once()
        except Exception as e:  # noqa: BLE001
            logger.warning("initial partition manager run failed: %r", e)
        while not self._stopped:
            sleep_s = self._sleep_s_until_0300_utc()
            try:
                await asyncio.sleep(sleep_s)
            except asyncio.CancelledError:
                return
            if self._stopped:
                return
            try:
                await self._run_once()
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                logger.warning("partition manager run failed: %r", e)

    async def start(self) -> None:
        self._stopped = False
        self._task = asyncio.create_task(self._loop(), name="monitoring.partition_manager")
        logger.info("partition manager started (daily at 03:00 UTC)")
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        self._stopped = True
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except Exception:  # noqa: BLE001
                pass
            self._task = None
