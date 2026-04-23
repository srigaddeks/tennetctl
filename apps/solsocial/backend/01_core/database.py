"""
Asyncpg pool management — solsocial DB only.

Pool is created on app startup, closed on shutdown. Routes acquire a
connection and pass `conn` to service/repo. Service/repo never touch the pool.

JSONB codec is registered on every new connection so Python dicts are
auto-encoded; never call json.dumps() in repos.
"""

from __future__ import annotations

import json

import asyncpg


async def _init_conn(conn: asyncpg.Connection) -> None:
    await conn.set_type_codec(
        "jsonb", encoder=json.dumps, decoder=json.loads, schema="pg_catalog",
    )
    await conn.set_type_codec(
        "json", encoder=json.dumps, decoder=json.loads, schema="pg_catalog",
    )


async def create_pool(dsn: str, min_size: int = 2, max_size: int = 10) -> asyncpg.Pool:
    return await asyncpg.create_pool(
        dsn=dsn, min_size=min_size, max_size=max_size, init=_init_conn,
    )


async def close_pool(pool: asyncpg.Pool) -> None:
    await pool.close()
