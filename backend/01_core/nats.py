"""
NATS / JetStream core client — module-level singletons.

Public surface:
- connect(url)       -> idempotent connect with 3x backoff retry
- close()            -> flush + drain if connected
- get_nats() / get_js() -> raise if not connected

Monitoring-optional: backend.main catches exceptions from connect() and logs
a WARNING so the app continues to boot when NATS is unreachable.
"""

from __future__ import annotations

import asyncio
import logging
import nats  # pyright: ignore[reportMissingTypeStubs]
from nats.aio.client import Client as NATS  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]
from nats.js import JetStreamContext  # pyright: ignore[reportMissingImports, reportMissingTypeStubs]

logger = logging.getLogger("tennetctl.nats")

_client: NATS | None = None
_js: JetStreamContext | None = None
_url: str | None = None


async def connect(url: str) -> None:
    """Connect to NATS with 3x exponential backoff. Idempotent."""
    global _client, _js, _url
    if _client is not None and _client.is_connected:
        if url == _url:
            return
        raise RuntimeError(
            f"NATS already connected to {_url!r}; refusing to re-connect to {url!r}"
        )
    delay = 0.25
    last_exc: Exception | None = None
    for attempt in range(3):
        try:
            _client = await nats.connect(url, connect_timeout=5)  # pyright: ignore[reportCallIssue]
            assert _client is not None
            _js = _client.jetstream()
            _url = url
            logger.info("NATS connected: %s", url)
            return
        except Exception as e:  # noqa: BLE001
            last_exc = e
            logger.warning("NATS connect attempt %d failed: %s", attempt + 1, e)
            if attempt < 2:
                await asyncio.sleep(delay)
                delay *= 2
    assert last_exc is not None
    raise last_exc


async def close() -> None:
    """Flush + drain + close. No-op if not connected."""
    global _client, _js, _url
    if _client is None:
        return
    try:
        if _client.is_connected:
            await _client.drain()
    except Exception as e:  # noqa: BLE001
        logger.warning("NATS drain failed: %s", e)
    _client = None
    _js = None
    _url = None


def get_nats() -> NATS:
    if _client is None:
        raise RuntimeError("NATS not connected. Call connect(url) first.")
    return _client


def get_js() -> JetStreamContext:
    if _js is None:
        raise RuntimeError("JetStream not available. Call connect(url) first.")
    return _js


__all__ = ["connect", "close", "get_nats", "get_js", "_reset_for_tests"]


# Test/reset helper — not part of public surface but exported for conftest.
def _reset_for_tests() -> None:
    global _client, _js, _url
    _client = None
    _js = None
    _url = None
