"""
SolSocial migrator — thin wrapper over tennetctl's
`backend.01_migrator.runner` pointed at the solsocial repo subtree and the
solsocial Postgres database.

Everything about the migration format (file layout, `-- UP ====` / `-- DOWN ====`
markers, seed YAML shape, `01_migrated/` + `02_in_progress/` folders, tracking
schema `"00_schema_migrations"`) is inherited verbatim — we just pass
`--root apps/solsocial` and `--dsn <solsocial-url>` so the runner scans
solsocial's own `03_docs/features/**/09_sql_migrations/` tree and writes
tracking rows into the solsocial database.

Usage (same verbs as tennetctl):
    python -m apps.solsocial.backend.scripts.migrator apply
    python -m apps.solsocial.backend.scripts.migrator seed
    python -m apps.solsocial.backend.scripts.migrator status
    python -m apps.solsocial.backend.scripts.migrator history
    python -m apps.solsocial.backend.scripts.migrator rollback
    python -m apps.solsocial.backend.scripts.migrator new \
        --name add-something --feature 10_solsocial --sub 20_posts

The `apply` path will auto-create the `solsocial` database if it does not
yet exist (tennetctl's runner itself expects the DB to exist).
"""

from __future__ import annotations

import asyncio
import sys
from importlib import import_module
from pathlib import Path
from urllib.parse import urlparse

import asyncpg

_config = import_module("apps.solsocial.backend.01_core.config")
_runner = import_module("backend.01_migrator.runner")

SOLSOCIAL_ROOT = Path(__file__).resolve().parent.parent.parent  # apps/solsocial/


async def _ensure_database(dsn: str) -> None:
    u = urlparse(dsn)
    target = (u.path or "/").lstrip("/") or "solsocial"
    admin_dsn = f"{u.scheme}://{u.netloc}/postgres"
    if u.query:
        admin_dsn += f"?{u.query}"
    conn = await asyncpg.connect(admin_dsn)
    try:
        exists = await conn.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", target,
        )
        if not exists:
            safe = target.replace('"', '""')
            await conn.execute(f'CREATE DATABASE "{safe}"')
            print(f"[solsocial-migrator] created database {target}")
    finally:
        await conn.close()


def main() -> None:
    cfg = _config.load_config()
    asyncio.run(_ensure_database(cfg.database_url))

    # Rewrite argv so tennetctl's runner sees the right --root and --dsn,
    # while preserving any user-supplied command + flags.
    args = list(sys.argv[1:])
    # Strip any user-supplied --root / --dsn so ours wins.
    i = 0
    cleaned: list[str] = []
    while i < len(args):
        a = args[i]
        if a in ("--root", "--dsn"):
            i += 2
            continue
        if a.startswith("--root=") or a.startswith("--dsn="):
            i += 1
            continue
        cleaned.append(a)
        i += 1
    sys.argv = [
        "solsocial-migrator",
        *cleaned,
        "--root", str(SOLSOCIAL_ROOT),
        "--dsn", cfg.database_url,
    ]
    _runner.main()


if __name__ == "__main__":
    main()
