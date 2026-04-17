"""LISTEN/NOTIFY worker — bridges Postgres NOTIFY to SSE broadcasters.

Holds a dedicated asyncpg connection (not pool-acquired) that LISTENs on
``monitoring_logs_new``. Every payload is fanned out to every subscriber via a
bounded asyncio.Queue (drop-oldest).
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

import asyncpg

logger = logging.getLogger("tennetctl.monitoring.notify_listener")


class Broadcaster:
    """Fan-out queue broadcaster with drop-oldest policy."""

    def __init__(self, max_queue: int = 500) -> None:
        self._subs: list[asyncio.Queue[dict[str, Any]]] = []
        self._max_queue = max_queue

    def subscribe(self) -> asyncio.Queue[dict[str, Any]]:
        q: asyncio.Queue[dict[str, Any]] = asyncio.Queue(maxsize=self._max_queue)
        self._subs.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[dict[str, Any]]) -> None:
        try:
            self._subs.remove(q)
        except ValueError:
            pass

    def publish(self, item: dict[str, Any]) -> None:
        for q in list(self._subs):
            try:
                q.put_nowait(item)
            except asyncio.QueueFull:
                # drop-oldest
                try:
                    q.get_nowait()
                    q.task_done()
                except Exception:  # noqa: BLE001
                    pass
                try:
                    q.put_nowait(item)
                except Exception:  # noqa: BLE001
                    pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subs)


class NotifyListener:
    CHANNEL = "monitoring_logs_new"

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: asyncpg.Connection | None = None
        self._task: asyncio.Task[None] | None = None
        self._stopped = False
        self.heartbeat_at: datetime | None = None
        self.broadcaster = Broadcaster(max_queue=500)

    def _on_notify(self, _conn: Any, _pid: int, _channel: str, payload: str) -> None:
        try:
            data = json.loads(payload)
        except Exception:  # noqa: BLE001
            data = {"raw": payload[:256]}
        self.broadcaster.publish(data)
        self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)

    async def _run(self) -> None:
        backoff = 1.0
        while not self._stopped:
            try:
                conn = await asyncpg.connect(self._dsn)
                self._conn = conn
                await conn.add_listener(self.CHANNEL, self._on_notify)
                logger.info("notify listener attached on channel %s", self.CHANNEL)
                backoff = 1.0
                # Keep alive with periodic heartbeat pings.
                while not self._stopped:
                    await asyncio.sleep(30)
                    try:
                        await conn.execute("SELECT 1")
                        self.heartbeat_at = datetime.now(timezone.utc).replace(tzinfo=None)
                    except Exception:
                        break
            except asyncio.CancelledError:
                return
            except Exception as e:  # noqa: BLE001
                logger.warning("notify listener error: %r (reconnect in %.1fs)", e, backoff)
            finally:
                if self._conn is not None:
                    try:
                        await self._conn.remove_listener(self.CHANNEL, self._on_notify)
                    except Exception:  # noqa: BLE001
                        pass
                    try:
                        await self._conn.close()
                    except Exception:  # noqa: BLE001
                        pass
                    self._conn = None
            try:
                await asyncio.sleep(backoff)
            except asyncio.CancelledError:
                return
            backoff = min(backoff * 2, 30.0)

    async def start(self) -> None:
        self._stopped = False
        self._task = asyncio.create_task(self._run(), name="monitoring.notify_listener")
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
