"""Rollup scheduler — calls monitoring_rollup_1m/5m/1h every 60/300/3600 seconds.

Pure-asyncio fallback for when pg_cron is unavailable (postgres:16-alpine).
Each loop catches exceptions and continues — a single failure does not kill
the scheduler. Stop is cooperative via asyncio.CancelledError.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("tennetctl.monitoring.rollup_scheduler")


class RollupScheduler:
    def __init__(self, pool: Any) -> None:
        self._pool = pool
        self._tasks: list[asyncio.Task[None]] = []
        self._stopped = False
        self.heartbeat_at: datetime | None = None

    async def _run_proc(self, proc: str) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(f'SELECT "05_monitoring".{proc}()')

    async def _loop(self, proc: str, interval_s: float) -> None:
        # Initial short stagger so all three don't collide on first tick.
        await asyncio.sleep(min(interval_s, 5.0))
        while not self._stopped:
            try:
                await self._run_proc(proc)
                self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                logger.warning("rollup %s failed: %r", proc, e)
            try:
                await asyncio.sleep(interval_s)
            except asyncio.CancelledError:
                return

    async def start(self) -> None:
        self._stopped = False
        self._tasks = [
            asyncio.create_task(self._loop("monitoring_rollup_1m",  60.0),  name="monitoring.rollup_1m"),
            asyncio.create_task(self._loop("monitoring_rollup_5m", 300.0),  name="monitoring.rollup_5m"),
            asyncio.create_task(self._loop("monitoring_rollup_1h", 3600.0), name="monitoring.rollup_1h"),
        ]
        logger.info("rollup scheduler started (1m / 5m / 1h)")
        # Keep this coroutine alive while children run.
        try:
            await asyncio.gather(*self._tasks)
        except asyncio.CancelledError:
            pass

    async def stop(self) -> None:
        self._stopped = True
        for t in self._tasks:
            t.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []
