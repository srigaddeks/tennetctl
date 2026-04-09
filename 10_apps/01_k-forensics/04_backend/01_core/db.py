"""kbio database connection pool.

Manages an asyncpg pool for the 10_kbio schema. Separate from the
tennetctl proxy — kbio owns its own Postgres connection.
"""

from __future__ import annotations

import json

import asyncpg

_pool: asyncpg.Pool | None = None


def _jsonb_encoder(value):
    return json.dumps(value)


def _jsonb_decoder(value):
    return json.loads(value)


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec(
        "jsonb",
        encoder=_jsonb_encoder,
        decoder=_jsonb_decoder,
        schema="pg_catalog",
    )


async def init_pool(dsn: str, *, min_size: int = 2, max_size: int = 20) -> None:
    global _pool
    if _pool is not None:
        return
    _pool = await asyncpg.create_pool(
        dsn,
        min_size=min_size,
        max_size=max_size,
        command_timeout=30,
        init=_init_conn,
    )


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("kbio database pool not initialised. Call init_pool() first.")
    return _pool
