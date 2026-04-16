"""
Catalog CLI — lint + upsert commands.

Usage:
  python -m backend.01_catalog.cli lint [--path backend/02_features]
  python -m backend.01_catalog.cli upsert [--fixtures]
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from importlib import import_module as _import_module
from pathlib import Path
from typing import Any

_linter: Any = _import_module("backend.01_catalog.linter")
_loader: Any = _import_module("backend.01_catalog.loader")
_config_mod: Any = _import_module("backend.01_core.config")
_db: Any = _import_module("backend.01_core.database")


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_lint(args: argparse.Namespace) -> int:
    default_root = _project_root() / "backend" / "02_features"
    target = Path(args.path) if args.path else default_root
    if not target.exists():
        # Default path may legitimately not exist yet (no features written).
        # Treat as clean; only error if user specified an explicit --path.
        if args.path is not None:
            print(f"Path does not exist: {target}", file=sys.stderr)
            return 2
        print("lint: clean (no features to check)")
        return 0
    violations = _linter.check_tree(target)
    if not violations:
        print("lint: clean")
        return 0
    for v in violations:
        print(f"{v.file}:{v.line}: {v.imported} [{v.reason}]")
    print(f"\nlint: {len(violations)} violation(s)", file=sys.stderr)
    return 1


async def _run_upsert(fixtures: bool) -> int:
    config = _config_mod.load_config()
    pool = await _db.create_pool(config.database_url)
    try:
        report = await _loader.upsert_all(pool, config.modules, fixtures=fixtures)
        print(
            f"upsert: {report.features_upserted} features, "
            f"{report.sub_features_upserted} sub-features, "
            f"{report.nodes_upserted} nodes, "
            f"{report.deprecated} deprecated"
        )
        if report.errors:
            for path, code, msg in report.errors:
                print(f"  error [{code}] at {path}: {msg}", file=sys.stderr)
            return 1
        return 0
    finally:
        await _db.close_pool(pool)


def cmd_upsert(args: argparse.Namespace) -> int:
    return asyncio.run(_run_upsert(fixtures=args.fixtures))


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="backend.01_catalog.cli")
    sub = parser.add_subparsers(dest="command", required=True)

    lint_p = sub.add_parser("lint", help="Check for cross-sub-feature imports")
    lint_p.add_argument("--path", default=None, help="Root to scan (default: backend/02_features)")
    lint_p.set_defaults(func=cmd_lint)

    upsert_p = sub.add_parser("upsert", help="Run catalog boot upsert against the live DB")
    upsert_p.add_argument("--fixtures", action="store_true", help="Also load test fixtures")
    upsert_p.set_defaults(func=cmd_upsert)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
