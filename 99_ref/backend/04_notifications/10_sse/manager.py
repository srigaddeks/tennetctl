from __future__ import annotations

"""SSE manager for real-time in-app notification delivery.

One asyncio.Queue per connected user.  The processor signals the manager
after a successful in_app delivery so the inbox updates instantly without
the client polling.
"""

import asyncio
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Module-level singleton — shared across all requests in the same process.
_queues: dict[str, list[asyncio.Queue[str]]] = defaultdict(list)


def register(user_id: str) -> asyncio.Queue[str]:
    """Register a new SSE connection for *user_id*. Returns its queue."""
    q: asyncio.Queue[str] = asyncio.Queue(maxsize=50)
    _queues[user_id].append(q)
    logger.debug("SSE: registered connection for user %s (%d total)", user_id, len(_queues[user_id]))
    return q


def unregister(user_id: str, q: asyncio.Queue[str]) -> None:
    """Remove *q* from the user's connection list."""
    try:
        _queues[user_id].remove(q)
    except ValueError:
        pass
    if not _queues[user_id]:
        del _queues[user_id]
    logger.debug("SSE: unregistered connection for user %s", user_id)


def push_event(user_id: str, payload: dict) -> None:
    """Non-blocking: fan out *payload* to all open SSE connections for *user_id*."""
    queues = _queues.get(user_id)
    if not queues:
        return
    data = json.dumps(payload)
    for q in list(queues):
        try:
            q.put_nowait(data)
        except asyncio.QueueFull:
            logger.warning("SSE: queue full for user %s, dropping event", user_id)


async def event_stream(user_id: str):
    """Async generator that yields SSE-formatted strings for the given user."""
    q = register(user_id)
    try:
        while True:
            # Keepalive comment every 25 s to prevent proxy/browser timeout.
            try:
                data = await asyncio.wait_for(q.get(), timeout=25)
                yield f"data: {data}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    finally:
        unregister(user_id, q)
