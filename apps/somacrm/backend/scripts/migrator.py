"""
somacrm migrator — thin wrapper over tennetctl's `backend.01_migrator.runner`.

Points the runner at apps/somacrm's own migration tree
(`apps/somacrm/03_docs/features/**/09_sql_migrations/`) and the somacrm
database (same Postgres as tennetctl, schema "12_somacrm").

Usage:
    python -m apps.somacrm.backend.scripts.migrator apply
    python -m apps.somacrm.backend.scripts.migrator status
    python -m apps.somacrm.backend.scripts.migrator new \\
        --name create-something --feature 12_somacrm --sub 00_bootstrap
"""

from __future__ import annotations

import sys
from importlib import import_module
from pathlib import Path

_config = import_module("apps.somacrm.backend.01_core.config")
_runner = import_module("backend.01_migrator.runner")

SOMACRM_ROOT = Path(__file__).resolve().parent.parent.parent  # apps/somacrm/


def main() -> None:
    cfg = _config.load_config()

    args = list(sys.argv[1:])
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
        "somacrm-migrator",
        *cleaned,
        "--root", str(SOMACRM_ROOT),
        "--dsn", cfg.database_url,
    ]
    _runner.main()


if __name__ == "__main__":
    main()
