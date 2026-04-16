"""Shared test fixtures for TennetCTL test suite."""

from __future__ import annotations

import asyncio
import os
import tempfile
from importlib import import_module
from pathlib import Path

import asyncpg
import pytest
from httpx import ASGITransport, AsyncClient

TEST_DSN = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl_test",
)

# Base DSN without database name — for creating/dropping the test DB
_parts = TEST_DSN.rsplit("/", 1)
BASE_DSN = _parts[0] + "/postgres"
TEST_DB_NAME = _parts[1] if len(_parts) > 1 else "tennetctl_test"


@pytest.fixture(scope="session")
def event_loop():
    """Session-scoped event loop for async fixtures."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Create the test database before the test suite, drop it after."""
    conn = await asyncpg.connect(BASE_DSN)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", TEST_DB_NAME
        )
        if not exists:
            await conn.execute(f'CREATE DATABASE "{TEST_DB_NAME}"')
    finally:
        await conn.close()

    yield

    conn = await asyncpg.connect(BASE_DSN)
    try:
        # Terminate connections to test DB before dropping
        await conn.execute(f"""
            SELECT pg_terminate_backend(pid)
            FROM pg_stat_activity
            WHERE datname = '{TEST_DB_NAME}' AND pid != pg_backend_pid()
        """)
        await conn.execute(f'DROP DATABASE IF EXISTS "{TEST_DB_NAME}"')
    finally:
        await conn.close()


@pytest.fixture
async def db_conn():
    """Fresh connection to the test database."""
    conn = await asyncpg.connect(TEST_DSN)
    try:
        yield conn
    finally:
        await conn.close()


@pytest.fixture
async def clean_db(db_conn):
    """Drop and recreate the migration tracking schema for a clean state."""
    await db_conn.execute('DROP SCHEMA IF EXISTS "00_schema_migrations" CASCADE')
    return db_conn


@pytest.fixture
def temp_migrations_dir():
    """Temporary directory for test migration files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
async def client():
    """Async HTTP client against the FastAPI app."""
    _main = import_module("backend.main")
    transport = ASGITransport(app=_main.app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
