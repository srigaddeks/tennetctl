from pathlib import Path
import asyncio

from importlib import import_module

apply_sql_migrations = import_module("backend.01_core.database").apply_sql_migrations


class DummyConnection:
    """Simulates asyncpg.Connection for migration runner tests.

    Tracks executed SQL and responds to the tracking-table queries
    that the new migration runner issues.
    """

    def __init__(self):
        self.executed: list[str] = []
        self._applied: set[str] = set()

    async def execute(self, script, *args):
        self.executed.append(script)
        return "OK"

    async def fetch(self, query, *args):
        # Return empty applied set — all migrations are "new".
        return []


class DummyPool:
    def __init__(self):
        self._conn = DummyConnection()

    class _Tx:
        def __init__(self, conn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    class _Acquire:
        def __init__(self, conn):
            self._conn = conn

        async def __aenter__(self):
            return self._conn

        async def __aexit__(self, exc_type, exc, tb):
            return False

    def transaction(self):
        return DummyPool._Tx(self._conn)

    def acquire(self):
        return DummyPool._Acquire(self._conn)


def create_sql(tmp_dir: Path, name: str, sql: str):
    p = tmp_dir / name
    p.write_text(sql, encoding="utf-8")
    return p


async def run_migrations(tmp_dir: Path, dry_run=False):
    pool = DummyPool()
    await apply_sql_migrations(pool, tmp_dir, dry_run=dry_run)
    return pool


def test_sql_migration_execution(tmp_path):
    create_sql(
        tmp_path,
        "20260101_create_table.sql",
        "CREATE TABLE test_table(id INT);",
    )

    pool = asyncio.run(run_migrations(tmp_path))
    # Should have executed: bootstrap SQL, fetch applied, the migration, insert tracking
    assert any("CREATE TABLE test_table" in s for s in pool._conn.executed)


def test_dry_run_does_not_execute(tmp_path):
    create_sql(
        tmp_path,
        "20260103_create_table.sql",
        "CREATE TABLE dry_run_table(id INT);",
    )

    pool = asyncio.run(run_migrations(tmp_path, dry_run=True))
    # The actual migration SQL should NOT have been executed in dry-run
    assert not any("CREATE TABLE dry_run_table" in s for s in pool._conn.executed)


def test_destructive_sql_warning(tmp_path):
    create_sql(
        tmp_path,
        "20260104_drop_table.sql",
        "DROP TABLE users;",
    )

    pool = asyncio.run(run_migrations(tmp_path))
    # Should still execute (with a warning logged)
    assert any("DROP TABLE users" in s for s in pool._conn.executed)


def test_schema_creation_runs_first(tmp_path):
    create_sql(
        tmp_path,
        "20260105_create_tables.sql",
        "CREATE TABLE IF NOT EXISTS t1(id INT);",
    )
    create_sql(
        tmp_path,
        "20260105_create_schema.sql",
        'CREATE SCHEMA IF NOT EXISTS "my_schema";',
    )

    pool = asyncio.run(run_migrations(tmp_path))
    migration_sqls = [
        s for s in pool._conn.executed
        if "my_schema" in s or "t1" in s
    ]
    # Schema creation should come before table creation
    schema_idx = next(i for i, s in enumerate(migration_sqls) if "my_schema" in s)
    table_idx = next(i for i, s in enumerate(migration_sqls) if "t1" in s)
    assert schema_idx < table_idx
