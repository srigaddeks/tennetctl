from __future__ import annotations

import json
import re
import time
from contextlib import asynccontextmanager
from importlib import import_module
from pathlib import Path
from typing import AsyncIterator

import yaml

import asyncpg


_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
start_operation_span = _telemetry_module.start_operation_span
_LOGGER = get_logger("backend.database")


async def _init_connection(conn: asyncpg.Connection) -> None:
    """Return UUID columns as plain strings so repositories need no casts.
    Register a JSON codec so Python dicts/lists are accepted for jsonb columns."""
    await conn.set_type_codec(
        "uuid",
        encoder=str,
        decoder=str,
        schema="pg_catalog",
        format="text",
    )
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


class DatabasePool:
    def __init__(
        self,
        *,
        database_url: str,
        min_size: int,
        max_size: int,
        command_timeout_seconds: int,
        application_name: str,
    ) -> None:
        self._database_url = database_url
        self._min_size = min_size
        self._max_size = max_size
        self._command_timeout_seconds = command_timeout_seconds
        self._application_name = application_name
        self._pool: asyncpg.Pool | None = None

    async def open(self) -> None:
        if self._pool is not None:
            return
        with start_operation_span(
            "db.pool.open",
            attributes={
                "db.system": "postgresql",
                "db.pool.min_size": self._min_size,
                "db.pool.max_size": self._max_size,
            },
        ):
            self._pool = await asyncpg.create_pool(
                dsn=self._database_url,
                min_size=self._min_size,
                max_size=self._max_size,
                command_timeout=self._command_timeout_seconds,
                server_settings={"application_name": self._application_name},
                init=_init_connection,
            )
            _LOGGER.info("database_pool_opened")

    async def close(self) -> None:
        if self._pool is None:
            return
        with start_operation_span("db.pool.close", attributes={"db.system": "postgresql"}):
            await self._pool.close()
            self._pool = None
            _LOGGER.info("database_pool_closed")

    @property
    def pool(self) -> asyncpg.Pool:
        if self._pool is None:
            raise RuntimeError("Database pool is not initialized.")
        return self._pool

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        with start_operation_span("db.connection.acquire", attributes={"db.system": "postgresql"}):
            async with self.pool.acquire() as connection:
                yield connection

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        with start_operation_span("db.transaction", attributes={"db.system": "postgresql"}):
            async with self.pool.acquire() as connection:
                async with connection.transaction():
                    yield connection

    async def ping(self) -> None:
        with start_operation_span("db.ping", attributes={"db.system": "postgresql"}):
            async with self.acquire() as connection:
                await connection.execute("SELECT 1")
            _LOGGER.info("database_ping_succeeded")


_ADVISORY_LOCK_ID = 918273645
_FILENAME_PATTERN = re.compile(r"^\d{8}_.+\.sql$")

_BOOTSTRAP_SQL = """\
CREATE SCHEMA IF NOT EXISTS "01_dev_features";

CREATE TABLE IF NOT EXISTS "01_dev_features"."01_schema_migration" (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255)  NOT NULL UNIQUE,
    sql_query       TEXT          NOT NULL,
    sql_text        TEXT          NOT NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'pending',
    applied_at      TIMESTAMP     NULL,
    rolled_back_at  TIMESTAMP     NULL,
    execution_time  INT           NULL,
    error_message   TEXT          NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_01_schema_migration_status
    ON "01_dev_features"."01_schema_migration" (status);
CREATE INDEX IF NOT EXISTS idx_01_schema_migration_name
    ON "01_dev_features"."01_schema_migration" (name);
"""


def _warn_destructive_sql(name: str, script: str) -> None:
    dangerous = ["DROP TABLE", "TRUNCATE", "DROP COLUMN"]
    upper = script.upper()
    for keyword in dangerous:
        if keyword in upper:
            _LOGGER.warning(
                "destructive_sql_detected",
                extra={"migration": name, "keyword": keyword},
            )


async def apply_sql_migrations(
    pool: DatabasePool,
    migration_directory: Path,
    *,
    dry_run: bool = False,
) -> None:
    """
    Tracked, HPA-safe migration runner.

    Acquires a PostgreSQL advisory lock so only one process runs migrations
    at a time.  Uses ``01_dev_features.01_schema_migration`` to track which
    files have already been applied, skipping them on subsequent startups.
    """

    with start_operation_span(
        "db.migrations.apply",
        attributes={
            "db.system": "postgresql",
            "db.migration.dry_run": dry_run,
        },
    ):
        async with pool.acquire() as lock_conn:
            await lock_conn.execute(
                f"SELECT pg_advisory_lock({_ADVISORY_LOCK_ID});"
            )

            try:
                # Bootstrap tracking infrastructure (idempotent).
                await lock_conn.execute(_BOOTSTRAP_SQL)

                # Fetch already-applied migration names.
                rows = await lock_conn.fetch(
                    'SELECT name FROM "01_dev_features"."01_schema_migration" '
                    "WHERE status = 'applied';"
                )
                applied: set[str] = {r["name"] for r in rows}

                # Discover migration files.
                if not migration_directory.exists():
                    _LOGGER.info(
                        "migration_directory_missing",
                        extra={"directory": str(migration_directory)},
                    )
                    return

                order_file = migration_directory / "migration-order.yaml"
                if order_file.exists():
                    with open(order_file, encoding="utf-8") as f:
                        ordered_names: list[str] = yaml.safe_load(f)["order"]

                    # Safety: warn about .sql files on disk but missing from YAML.
                    disk_sql = {
                        p.name
                        for p in migration_directory.glob("*.sql")
                    }
                    unlisted = disk_sql - set(ordered_names)
                    if unlisted:
                        _LOGGER.warning(
                            "migrations_not_in_yaml",
                            extra={"files": sorted(unlisted)},
                        )
                else:
                    # Fallback: glob + alphabetical sort (no YAML present).
                    _LOGGER.info("migration_yaml_not_found_using_glob_fallback")
                    ordered_names = sorted(
                        f.name
                        for f in migration_directory.glob("*.sql")
                        if _FILENAME_PATTERN.match(f.name)
                    )

                skipped = 0
                applied_count = 0

                for name in ordered_names:
                    if name in applied:
                        skipped += 1
                        continue

                    sql_file = migration_directory / name
                    if not sql_file.exists():
                        raise RuntimeError(
                            f"Migration listed in YAML not found on disk: {name}"
                        )
                    script = sql_file.read_text(encoding="utf-8")
                    if not script.strip():
                        continue

                    # Strip DOWN section — only execute the UP portion.
                    # Convention: "-- DOWN ===..." marks the rollback section.
                    _down_marker = "-- DOWN =="
                    if _down_marker in script:
                        script = script[: script.index(_down_marker)]

                    _warn_destructive_sql(name, script)

                    with start_operation_span(
                        "db.migration.execute",
                        attributes={
                            "db.system": "postgresql",
                            "db.migration.name": name,
                            "db.migration.dry_run": dry_run,
                        },
                    ):
                        if dry_run:
                            _LOGGER.info(
                                "migration_dry_run",
                                extra={"migration": name},
                            )
                            continue

                        _LOGGER.info(
                            "migration_applying",
                            extra={"migration": name},
                        )

                        sql_query = (script.split(";")[0] + ";") if ";" in script else script

                        t0 = time.monotonic()
                        try:
                            async with pool.transaction() as conn:
                                await conn.execute(script)
                        except Exception as exc:
                            elapsed_ms = int((time.monotonic() - t0) * 1000)
                            await lock_conn.execute(
                                'INSERT INTO "01_dev_features"."01_schema_migration" '
                                "(name, sql_query, sql_text, status, applied_at, execution_time, error_message) "
                                "VALUES ($1, $2, $3, 'failed', NOW(), $4, $5) "
                                "ON CONFLICT (name) DO UPDATE SET status = 'failed', "
                                "applied_at = NOW(), execution_time = EXCLUDED.execution_time, "
                                "error_message = EXCLUDED.error_message;",
                                name,
                                sql_query,
                                script,
                                elapsed_ms,
                                str(exc),
                            )
                            _LOGGER.error(
                                "migration_failed",
                                extra={
                                    "migration": name,
                                    "error": str(exc),
                                    "execution_time_ms": elapsed_ms,
                                },
                            )
                            raise

                        elapsed_ms = int((time.monotonic() - t0) * 1000)
                        await lock_conn.execute(
                            'INSERT INTO "01_dev_features"."01_schema_migration" '
                            "(name, sql_query, sql_text, status, applied_at, execution_time) "
                            "VALUES ($1, $2, $3, 'applied', NOW(), $4) "
                            "ON CONFLICT (name) DO UPDATE SET status = 'applied', "
                            "applied_at = NOW(), execution_time = EXCLUDED.execution_time, "
                            "error_message = NULL;",
                            name,
                            sql_query,
                            script,
                            elapsed_ms,
                        )

                        applied_count += 1
                        _LOGGER.info(
                            "migration_applied",
                            extra={
                                "migration": name,
                                "execution_time_ms": elapsed_ms,
                            },
                        )

                _LOGGER.info(
                    "migrations_summary",
                    extra={
                        "applied": applied_count,
                        "skipped": skipped,
                        "total_found": len(ordered_names),
                    },
                )

            finally:
                await lock_conn.execute(
                    f"SELECT pg_advisory_unlock({_ADVISORY_LOCK_ID});"
                )
                _LOGGER.info("migration_lock_released")
