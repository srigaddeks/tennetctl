"""kbio Valkey (Redis-compatible) client.

Provides a lazy singleton async client for hot caching of session state,
user profiles, device records, and batch idempotency.
"""

from __future__ import annotations

import valkey.asyncio as valkey

_client: valkey.Valkey | None = None


async def init_client(url: str) -> None:
    global _client
    if _client is not None:
        return
    _client = valkey.from_url(
        url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
    )


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def get_client() -> valkey.Valkey:
    if _client is None:
        raise RuntimeError("kbio Valkey client not initialised. Call init_client() first.")
    return _client
