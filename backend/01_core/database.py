"""
Database pool management — asyncpg only.

Pool lifecycle: create on app startup, close on shutdown.
Routes call pool.acquire() to get a connection, pass conn to service/repo.

The pool's init callback registers a JSONB codec so Python dicts are
automatically encoded to/from JSONB columns (no json.dumps needed in repos).
"""

from __future__ import annotations

import json

import asyncpg


async def _init_conn(conn: asyncpg.Connection) -> None:
    """Register type codecs on every new pool connection."""
    await conn.set_type_codec(
        "jsonb",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json",
        encoder=json.dumps,
        decoder=json.loads,
        schema="pg_catalog",
    )


async def create_pool(dsn: str, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    """Create and return an asyncpg connection pool with JSONB codec."""
    return await asyncpg.create_pool(
        dsn=dsn,
        min_size=min_size,
        max_size=max_size,
        init=_init_conn,
    )


async def close_pool(pool: asyncpg.Pool) -> None:
    """Close the connection pool."""
    await pool.close()
