from __future__ import annotations

from importlib import import_module
import asyncio
import argparse


load_settings = import_module("backend.00_config.settings").load_settings
DatabasePool = import_module("backend.01_core.database").DatabasePool
apply_sql_migrations = import_module("backend.01_core.database").apply_sql_migrations

try:
    _telemetry_module = import_module("backend.01_core.telemetry")
except ModuleNotFoundError:  # pragma: no cover
    configure_observability = lambda settings: None

    class _NoOpSpan:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, tb):
            return False

    def start_operation_span(name: str, *, attributes=None):
        del name, attributes
        return _NoOpSpan()
else:
    configure_observability = _telemetry_module.configure_observability
    start_operation_span = _telemetry_module.start_operation_span


async def _main(*, dry_run: bool) -> None:
    settings = load_settings()
    configure_observability(settings)
    pool = DatabasePool(
        database_url=settings.database_url,
        min_size=settings.database_min_pool_size,
        max_size=settings.database_max_pool_size,
        command_timeout_seconds=settings.database_command_timeout_seconds,
        application_name=settings.app_name,
    )
    with start_operation_span(
        "script.apply_migrations",
        attributes={"entrypoint": "backend.91_scripts.apply_migrations"},
    ):
        await pool.open()
        try:
            await apply_sql_migrations(
                pool,
                settings.migration_directory,
                dry_run=dry_run,
            )
            if dry_run:
                print("Dry run complete. No migrations executed.")
            else:
                print("Applied SQL migrations.")
        finally:
            await pool.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run SQL migrations.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migrations without executing them.",
    )
    args = parser.parse_args()

    asyncio.run(_main(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
