"""
TennetCTL SQL Migrator

Enterprise-grade sequential SQL migration runner using asyncpg.

Migration files live inside their sub-feature directories:
  03_docs/features/{nn}_{feature}/05_sub_features/{nn}_{sub}/
    09_sql_migrations/
      02_in_progress/   ← pending (discovered + applied from here)
      01_migrated/      ← applied (file moved here after apply)

Seed files live alongside migrations:
  09_sql_migrations/seeds/*.yaml   (or *.json)

Format:
  -- UP ====
  CREATE TABLE ...;
  -- DOWN ====
  DROP TABLE ...;

Seed YAML format:
  schema: "03_iam"
  table: "01_dim_account_types"
  rows:
    - id: 1
      code: email_password
      label: Email + Password

Usage:
  python -m backend.01_migrator.runner apply
  python -m backend.01_migrator.runner apply --dry-run
  python -m backend.01_migrator.runner status
  python -m backend.01_migrator.runner rollback
  python -m backend.01_migrator.runner rollback --to 20260413_002_create-users.sql
  python -m backend.01_migrator.runner seed
  python -m backend.01_migrator.runner seed --dry-run
  python -m backend.01_migrator.runner new --name create-iam-schema --feature 03_iam --sub 00_bootstrap
  python -m backend.01_migrator.runner history
"""

from __future__ import annotations

import argparse
import asyncio
import getpass
import hashlib
import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import asyncpg

logger = logging.getLogger("migrator")

TRACKING_SCHEMA = "00_schema_migrations"
TRACKING_TABLE = f'"{TRACKING_SCHEMA}".applied_migrations'
SEED_TABLE = f'"{TRACKING_SCHEMA}".applied_seeds'

BOOTSTRAP_SQL = f"""
CREATE SCHEMA IF NOT EXISTS "{TRACKING_SCHEMA}";

CREATE TABLE IF NOT EXISTS {TRACKING_TABLE} (
    id              SERIAL PRIMARY KEY,
    filename        TEXT NOT NULL,
    checksum        TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'applied',
    applied_by      TEXT NOT NULL DEFAULT 'unknown',
    applied_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    rolled_back_at  TIMESTAMP,
    rolled_back_by  TEXT,
    duration_ms     INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT chk_status CHECK (status IN ('applied', 'rolled_back'))
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_applied_migrations_filename_active
    ON {TRACKING_TABLE} (filename)
    WHERE status = 'applied';

CREATE TABLE IF NOT EXISTS {SEED_TABLE} (
    id          SERIAL PRIMARY KEY,
    filename    TEXT NOT NULL UNIQUE,
    checksum    TEXT NOT NULL,
    applied_by  TEXT NOT NULL DEFAULT 'unknown',
    applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    row_count   INTEGER NOT NULL DEFAULT 0
);
"""

# Project root = three levels up from this file (backend/01_migrator/runner.py → root)
DEFAULT_ROOT_DIR = Path(__file__).resolve().parent.parent.parent

UP_MARKER = "-- UP ===="
DOWN_MARKER = "-- DOWN ===="

MIGRATION_TEMPLATE = """-- UP ====

-- TODO: Write your migration SQL here


-- DOWN ====

-- TODO: Write the rollback SQL here (must completely revert UP)

"""


# ── File discovery ────────────────────────────────────────────────────


def discover_pending(root_dir: Path) -> list[Path]:
    """
    Recursively find all .sql files in 09_sql_migrations/02_in_progress/
    directories under root_dir.

    Sorted globally by filename (YYYYMMDD_NNN_desc.sql convention ensures order).
    """
    files = list(root_dir.rglob("09_sql_migrations/02_in_progress/*.sql"))
    return sorted(files, key=lambda p: p.name)


def discover_migrated(root_dir: Path) -> dict[str, Path]:
    """
    Recursively find all .sql files in 09_sql_migrations/01_migrated/
    directories under root_dir.

    Returns {filename: full_path} mapping for rollback lookups.
    """
    files = root_dir.rglob("09_sql_migrations/01_migrated/*.sql")
    return {f.name: f for f in files}


def discover_seeds(root_dir: Path) -> list[Path]:
    """
    Recursively find all seed files (*.yaml, *.json) in
    09_sql_migrations/seeds/ directories under root_dir.

    Sorted by filename for deterministic order.
    """
    yaml_files = list(root_dir.rglob("09_sql_migrations/seeds/*.yaml"))
    json_files = list(root_dir.rglob("09_sql_migrations/seeds/*.json"))
    return sorted(yaml_files + json_files, key=lambda p: p.name)


def move_to_migrated(filepath: Path) -> Path:
    """Move an applied migration from 02_in_progress/ to 01_migrated/."""
    migrated_dir = filepath.parent.parent / "01_migrated"
    migrated_dir.mkdir(parents=True, exist_ok=True)
    dest = migrated_dir / filepath.name
    filepath.rename(dest)
    return dest


def move_to_in_progress(filepath: Path) -> Path:
    """Move a rolled-back migration from 01_migrated/ back to 02_in_progress/."""
    in_progress_dir = filepath.parent.parent / "02_in_progress"
    in_progress_dir.mkdir(parents=True, exist_ok=True)
    dest = in_progress_dir / filepath.name
    filepath.rename(dest)
    return dest


# ── Parsing ──────────────────────────────────────────────────────────


def parse_migration(content: str) -> dict[str, str]:
    """
    Parse a migration file into UP and DOWN sections.
    Returns {"up": str, "down": str}. Raises ValueError if markers are missing.
    """
    up_idx = content.find(UP_MARKER)
    down_idx = content.find(DOWN_MARKER)

    if up_idx == -1:
        raise ValueError(f"Missing '{UP_MARKER}' marker")
    if down_idx == -1:
        raise ValueError(f"Missing '{DOWN_MARKER}' marker")
    if down_idx < up_idx:
        raise ValueError(f"'{DOWN_MARKER}' must come after '{UP_MARKER}'")

    up_sql = content[up_idx + len(UP_MARKER):down_idx].strip()
    down_sql = content[down_idx + len(DOWN_MARKER):].strip()

    return {"up": up_sql, "down": down_sql}


def parse_seed(content: str, filepath: Path) -> dict[str, Any]:
    """
    Parse a seed file (YAML or JSON).

    Expected shape:
      schema: "03_iam"          (optional — used for display only)
      table: "01_dim_account_types"
      rows:
        - id: 1
          code: email_password
          label: Email + Password
    """
    suffix = filepath.suffix.lower()
    if suffix in (".yaml", ".yml"):
        try:
            import yaml  # type: ignore[import]
        except ImportError:
            raise RuntimeError(
                "PyYAML is required for seed files: pip install pyyaml"
            )
        data = yaml.safe_load(content)
    elif suffix == ".json":
        data = json.loads(content)
    else:
        raise ValueError(f"Unsupported seed format: {suffix}")

    if not isinstance(data, dict):
        raise ValueError(f"Seed file must be a mapping, got {type(data).__name__}")
    if "table" not in data:
        raise ValueError("Seed file missing required 'table' key")
    if "rows" not in data or not isinstance(data["rows"], list):
        raise ValueError("Seed file missing required 'rows' list")

    return data


def compute_checksum(content: str) -> str:
    """SHA256 hex digest of full file content."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def get_current_user() -> str:
    """Get the current OS username for tracking."""
    try:
        return getpass.getuser()
    except Exception:
        return "unknown"


# ── Bootstrap ────────────────────────────────────────────────────────


async def bootstrap(conn: asyncpg.Connection) -> None:
    """Ensure tracking schema and tables exist. Upgrades old schema if needed."""
    old_table = await conn.fetchval(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = '00_schema_migrations' AND table_name = 'applied_migrations'"
    )

    if old_table:
        has_status = await conn.fetchval(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = '00_schema_migrations' "
            "AND table_name = 'applied_migrations' "
            "AND column_name = 'status'"
        )
        if not has_status:
            logger.info("Upgrading tracking table to v2 schema...")
            await conn.execute(f"""
                ALTER TABLE {TRACKING_TABLE}
                    ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'applied',
                    ADD COLUMN IF NOT EXISTS applied_by TEXT NOT NULL DEFAULT 'unknown',
                    ADD COLUMN IF NOT EXISTS rolled_back_at TIMESTAMP,
                    ADD COLUMN IF NOT EXISTS rolled_back_by TEXT,
                    ADD COLUMN IF NOT EXISTS duration_ms INTEGER NOT NULL DEFAULT 0;
            """)
            await conn.execute(f"""
                ALTER TABLE {TRACKING_TABLE}
                    ADD CONSTRAINT chk_status CHECK (status IN ('applied', 'rolled_back'));
            """)
            await conn.execute(f"""
                DROP INDEX IF EXISTS "{TRACKING_SCHEMA}".applied_migrations_filename_key;
                CREATE UNIQUE INDEX IF NOT EXISTS uq_applied_migrations_filename_active
                    ON {TRACKING_TABLE} (filename)
                    WHERE status = 'applied';
            """)
            logger.info("Tracking table upgraded.")

        # Ensure seed table exists even on upgraded installs
        await conn.execute(f"""
            CREATE TABLE IF NOT EXISTS {SEED_TABLE} (
                id          SERIAL PRIMARY KEY,
                filename    TEXT NOT NULL UNIQUE,
                checksum    TEXT NOT NULL,
                applied_by  TEXT NOT NULL DEFAULT 'unknown',
                applied_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                row_count   INTEGER NOT NULL DEFAULT 0
            );
        """)
        return

    # Fresh install
    await conn.execute(BOOTSTRAP_SQL)
    logger.info("Tracking tables ready in schema: %s", TRACKING_SCHEMA)


# ── Applied queries ───────────────────────────────────────────────────


async def get_applied(conn: asyncpg.Connection) -> dict[str, dict]:
    """Return {filename: info} for all actively applied migrations."""
    rows = await conn.fetch(
        f"SELECT id, filename, checksum, applied_at, applied_by, duration_ms "
        f"FROM {TRACKING_TABLE} "
        f"WHERE status = 'applied' "
        f"ORDER BY id"
    )
    return {
        row["filename"]: {
            "id": row["id"],
            "checksum": row["checksum"],
            "applied_at": row["applied_at"],
            "applied_by": row["applied_by"],
            "duration_ms": row["duration_ms"],
        }
        for row in rows
    }


async def get_applied_seeds(conn: asyncpg.Connection) -> dict[str, dict]:
    """Return {filename: info} for all applied seeds."""
    rows = await conn.fetch(
        f"SELECT id, filename, checksum, applied_at, applied_by, row_count "
        f"FROM {SEED_TABLE} ORDER BY id"
    )
    return {
        row["filename"]: {
            "id": row["id"],
            "checksum": row["checksum"],
            "applied_at": row["applied_at"],
            "applied_by": row["applied_by"],
            "row_count": row["row_count"],
        }
        for row in rows
    }


async def get_full_history(conn: asyncpg.Connection) -> list[dict]:
    """Return complete migration history including rollbacks."""
    rows = await conn.fetch(
        f"SELECT id, filename, checksum, status, applied_by, applied_at, "
        f"rolled_back_at, rolled_back_by, duration_ms "
        f"FROM {TRACKING_TABLE} ORDER BY id"
    )
    return [dict(row) for row in rows]


# ── Apply ────────────────────────────────────────────────────────────


async def apply_single(
    conn: asyncpg.Connection,
    filepath: Path,
    filename: str,
    checksum: str,
    up_sql: str,
    user: str,
    dry_run: bool = False,
) -> int:
    """
    Apply a single migration's UP section and move it to 01_migrated/.
    Returns duration_ms.
    """
    start = time.monotonic()

    if dry_run:
        logger.info("[DRY RUN] Would apply: %s", filename)
        return 0

    async with conn.transaction():
        await conn.execute(up_sql)
        duration_ms = int((time.monotonic() - start) * 1000)
        await conn.execute(
            f"INSERT INTO {TRACKING_TABLE} "
            f"(filename, checksum, status, applied_by, duration_ms) "
            f"VALUES ($1, $2, 'applied', $3, $4)",
            filename,
            checksum,
            user,
            duration_ms,
        )

    move_to_migrated(filepath)
    return duration_ms


async def run_apply(
    dsn: str,
    root_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Apply all pending migrations discovered under root_dir.

    Returns {"applied": N, "skipped": N, "total": N}
    """
    if root_dir is None:
        root_dir = DEFAULT_ROOT_DIR

    user = get_current_user()
    conn = await asyncpg.connect(dsn)
    try:
        await bootstrap(conn)

        applied = await get_applied(conn)
        pending = discover_pending(root_dir)

        stats = {"applied": 0, "skipped": 0, "total": len(pending)}

        for filepath in pending:
            filename = filepath.name
            content = filepath.read_text(encoding="utf-8")
            checksum = compute_checksum(content)

            if filename in applied:
                existing = applied[filename]
                if existing["checksum"] != checksum:
                    msg = (
                        f"Checksum mismatch for {filename}: "
                        f"applied={existing['checksum'][:12]}... "
                        f"current={checksum[:12]}... "
                        f"Migration file was modified after it was applied."
                    )
                    logger.error(msg)
                    raise RuntimeError(msg)

                logger.debug("Skipping (already applied): %s", filename)
                stats["skipped"] += 1
                continue

            try:
                sections = parse_migration(content)
            except ValueError as exc:
                raise RuntimeError(f"Invalid migration {filename}: {exc}") from exc

            if not sections["up"]:
                logger.warning("Empty UP section in %s — skipping", filename)
                stats["skipped"] += 1
                continue

            duration_ms = await apply_single(
                conn, filepath, filename, checksum, sections["up"], user, dry_run
            )

            if dry_run:
                stats["applied"] += 1
                continue

            logger.info(
                "Applied: %s → 01_migrated/ (%dms)",
                filename,
                duration_ms,
            )
            stats["applied"] += 1

        logger.info(
            "Migration complete: %d applied, %d skipped, %d total",
            stats["applied"],
            stats["skipped"],
            stats["total"],
        )
        return stats

    finally:
        await conn.close()


# ── Rollback ─────────────────────────────────────────────────────────


async def run_rollback(
    dsn: str,
    root_dir: Path | None = None,
    target: str | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Roll back migrations (reads files from 01_migrated/, moves them back to
    02_in_progress/ after rollback).

    If target is None: rolls back the last applied migration.
    If target is a filename: rolls back everything from target onwards.
    """
    if root_dir is None:
        root_dir = DEFAULT_ROOT_DIR

    user = get_current_user()
    conn = await asyncpg.connect(dsn)
    try:
        await bootstrap(conn)

        applied = await get_applied(conn)
        if not applied:
            logger.info("Nothing to roll back — no applied migrations.")
            return {"rolled_back": 0}

        applied_ordered = sorted(applied.items(), key=lambda x: x[1]["id"])

        if target is None:
            to_rollback = [applied_ordered[-1]]
        else:
            target_found = False
            to_rollback = []
            for filename, info in applied_ordered:
                if filename == target:
                    target_found = True
                if target_found:
                    to_rollback.append((filename, info))
            if not target_found:
                raise RuntimeError(
                    f"Target migration not found in applied: {target}"
                )
            to_rollback.reverse()

        # Map filename → path in 01_migrated/
        migrated_files = discover_migrated(root_dir)

        stats = {"rolled_back": 0}

        for filename, _ in to_rollback:
            if filename not in migrated_files:
                raise RuntimeError(
                    f"Cannot roll back {filename}: file not found in any "
                    f"09_sql_migrations/01_migrated/ directory. "
                    f"Was it manually deleted?"
                )

            filepath = migrated_files[filename]
            content = filepath.read_text(encoding="utf-8")

            try:
                sections = parse_migration(content)
            except ValueError as exc:
                raise RuntimeError(
                    f"Cannot parse {filename} for rollback: {exc}"
                ) from exc

            if not sections["down"]:
                raise RuntimeError(
                    f"Cannot roll back {filename}: empty DOWN section"
                )

            if dry_run:
                logger.info("[DRY RUN] Would roll back: %s", filename)
                stats["rolled_back"] += 1
                continue

            start = time.monotonic()
            async with conn.transaction():
                await conn.execute(sections["down"])
                await conn.execute(
                    f"UPDATE {TRACKING_TABLE} "
                    f"SET status = 'rolled_back', "
                    f"    rolled_back_at = CURRENT_TIMESTAMP, "
                    f"    rolled_back_by = $1 "
                    f"WHERE filename = $2 AND status = 'applied'",
                    user,
                    filename,
                )

            duration_ms = int((time.monotonic() - start) * 1000)
            move_to_in_progress(filepath)
            logger.info(
                "Rolled back: %s → 02_in_progress/ (%dms)",
                filename,
                duration_ms,
            )
            stats["rolled_back"] += 1

        logger.info("Rollback complete: %d rolled back", stats["rolled_back"])
        return stats

    finally:
        await conn.close()


# ── Status ───────────────────────────────────────────────────────────


async def run_status(
    dsn: str,
    root_dir: Path | None = None,
) -> dict[str, list[str]]:
    """Show migration status: applied (in 01_migrated/) vs pending (in 02_in_progress/)."""
    if root_dir is None:
        root_dir = DEFAULT_ROOT_DIR

    conn = await asyncpg.connect(dsn)
    try:
        await bootstrap(conn)

        applied = await get_applied(conn)
        pending = discover_pending(root_dir)

        applied_list = []
        pending_list = []

        # Applied migrations (from tracking table — files are in 01_migrated/)
        for filename, info in sorted(applied.items(), key=lambda x: x[1]["id"]):
            applied_list.append(
                f"  ✓ {filename}  "
                f"({info['applied_at'].strftime('%Y-%m-%d %H:%M')} "
                f"by {info['applied_by']}, {info['duration_ms']}ms)"
            )

        # Pending migrations (files in 02_in_progress/ not yet tracked)
        for filepath in pending:
            pending_list.append(
                f"  ○ {filepath.name}  "
                f"[{filepath.relative_to(root_dir).parent.parent.parent}]"
            )

        print()
        print(
            f"Migrations — {len(applied_list)} applied, {len(pending_list)} pending"
        )
        print("─" * 70)

        if applied_list:
            print("\nApplied (in 01_migrated/):")
            for line in applied_list:
                print(line)

        if pending_list:
            print("\nPending (in 02_in_progress/):")
            for line in pending_list:
                print(line)

        if not pending_list:
            print("\nDatabase is up to date.")

        print()
        return {
            "applied": list(applied.keys()),
            "pending": [f.name for f in pending],
        }

    finally:
        await conn.close()


# ── History ──────────────────────────────────────────────────────────


async def run_history(dsn: str) -> list[dict]:
    """Show full migration history including rollbacks."""
    conn = await asyncpg.connect(dsn)
    try:
        await bootstrap(conn)
        history = await get_full_history(conn)

        print()
        print(f"Migration history — {len(history)} entries")
        print("─" * 80)

        if not history:
            print("  No migration history yet.")
            print()
            return []

        print(
            f"  {'ID':>4}  {'Status':<12}  {'Filename':<45}  "
            f"{'When':<16}  {'By':<10}  {'ms':>5}"
        )
        print(
            f"  {'─'*4}  {'─'*12}  {'─'*45}  {'─'*16}  {'─'*10}  {'─'*5}"
        )

        for row in history:
            status = row["status"]
            when = row["applied_at"].strftime("%Y-%m-%d %H:%M")
            marker = "✓" if status == "applied" else "✗"
            print(
                f"  {row['id']:>4}  {marker} {status:<10}  "
                f"{row['filename']:<45}  {when:<16}  "
                f"{row['applied_by']:<10}  {row['duration_ms']:>5}"
            )

            if status == "rolled_back" and row.get("rolled_back_at"):
                rb_when = row["rolled_back_at"].strftime("%Y-%m-%d %H:%M")
                print(
                    f"        ↳ rolled back {rb_when} "
                    f"by {row.get('rolled_back_by', '?')}"
                )

        print()
        return history

    finally:
        await conn.close()


# ── Seeds ────────────────────────────────────────────────────────────


async def apply_seed(
    conn: asyncpg.Connection,
    filename: str,
    checksum: str,
    seed_data: dict[str, Any],
    user: str,
) -> int:
    """
    Apply a seed file (insert rows into the target table).
    Returns the number of rows inserted.
    """
    schema = seed_data.get("schema", "public")
    table = seed_data["table"]
    rows: list[dict] = seed_data["rows"]

    if not rows:
        return 0

    full_table = f'"{schema}"."{table}"'

    # Build parameterised INSERT for each row (ON CONFLICT DO NOTHING for idempotency)
    row_count = 0
    async with conn.transaction():
        for row in rows:
            columns = list(row.keys())
            col_list = ", ".join(f'"{c}"' for c in columns)
            placeholders = ", ".join(f"${i+1}" for i in range(len(columns)))
            values = [row[c] for c in columns]

            await conn.execute(
                f"INSERT INTO {full_table} ({col_list}) "
                f"VALUES ({placeholders}) "
                f"ON CONFLICT DO NOTHING",
                *values,
            )
            row_count += 1  # noqa: SIM113 — intentional per-row count

        await conn.execute(
            f"INSERT INTO {SEED_TABLE} (filename, checksum, applied_by, row_count) "
            f"VALUES ($1, $2, $3, $4)",
            filename,
            checksum,
            user,
            row_count,
        )

    return row_count


async def run_seed(
    dsn: str,
    root_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, int]:
    """
    Apply all pending seed files discovered under root_dir.

    Seed files already applied (by filename) are skipped.
    Checksum mismatch is a warning, not an error (seeds are idempotent).

    Returns {"applied": N, "skipped": N, "total": N}
    """
    if root_dir is None:
        root_dir = DEFAULT_ROOT_DIR

    user = get_current_user()
    conn = await asyncpg.connect(dsn)
    try:
        await bootstrap(conn)

        applied_seeds = await get_applied_seeds(conn)
        seed_files = discover_seeds(root_dir)

        stats = {"applied": 0, "skipped": 0, "total": len(seed_files)}

        for filepath in seed_files:
            filename = filepath.name
            content = filepath.read_text(encoding="utf-8")
            checksum = compute_checksum(content)

            if filename in applied_seeds:
                existing = applied_seeds[filename]
                if existing["checksum"] != checksum:
                    logger.warning(
                        "Seed %s changed since it was applied "
                        "(was=%s..., now=%s...) — skipping",
                        filename,
                        existing["checksum"][:12],
                        checksum[:12],
                    )
                else:
                    logger.debug("Skipping (already applied): %s", filename)
                stats["skipped"] += 1
                continue

            try:
                seed_data = parse_seed(content, filepath)
            except (ValueError, RuntimeError) as exc:
                raise RuntimeError(f"Invalid seed {filename}: {exc}") from exc

            if dry_run:
                logger.info(
                    "[DRY RUN] Would seed: %s → %s rows into %s.%s",
                    filename,
                    len(seed_data["rows"]),
                    seed_data.get("schema", "public"),
                    seed_data["table"],
                )
                stats["applied"] += 1
                continue

            row_count = await apply_seed(
                conn, filename, checksum, seed_data, user
            )
            logger.info(
                "Seeded: %s (%d rows → %s.%s)",
                filename,
                row_count,
                seed_data.get("schema", "public"),
                seed_data["table"],
            )
            stats["applied"] += 1

        logger.info(
            "Seed complete: %d applied, %d skipped, %d total",
            stats["applied"],
            stats["skipped"],
            stats["total"],
        )
        return stats

    finally:
        await conn.close()


# ── New migration scaffold ───────────────────────────────────────────


def run_new(
    root_dir: Path | None = None,
    name: str = "unnamed",
    feature: str | None = None,
    sub: str | None = None,
) -> Path:
    """
    Scaffold a new migration file in the appropriate sub-feature directory.

    Path: 03_docs/features/{feature}/05_sub_features/{sub}/09_sql_migrations/02_in_progress/
    If feature/sub not provided, falls back to 03_docs/features/unassigned/09_sql_migrations/02_in_progress/
    """
    if root_dir is None:
        root_dir = DEFAULT_ROOT_DIR

    if feature and sub:
        target_dir = (
            root_dir
            / "03_docs"
            / "features"
            / feature
            / "05_sub_features"
            / sub
            / "09_sql_migrations"
            / "02_in_progress"
        )
    elif feature:
        target_dir = (
            root_dir
            / "03_docs"
            / "features"
            / feature
            / "09_sql_migrations"
            / "02_in_progress"
        )
    else:
        target_dir = (
            root_dir
            / "03_docs"
            / "features"
            / "unassigned"
            / "09_sql_migrations"
            / "02_in_progress"
        )

    target_dir.mkdir(parents=True, exist_ok=True)

    # Determine next global sequence number across all in_progress + migrated dirs
    all_sql = list(root_dir.rglob("09_sql_migrations/02_in_progress/*.sql"))
    all_sql += list(root_dir.rglob("09_sql_migrations/01_migrated/*.sql"))

    max_seq = 0
    for f in all_sql:
        parts = f.stem.split("_", 2)
        if len(parts) >= 2 and parts[1].isdigit():
            max_seq = max(max_seq, int(parts[1]))

    next_seq = max_seq + 1
    date_prefix = datetime.now(timezone.utc).strftime("%Y%m%d")
    filename = f"{date_prefix}_{next_seq:03d}_{name}.sql"
    filepath = target_dir / filename

    filepath.write_text(MIGRATION_TEMPLATE, encoding="utf-8")

    rel_path = filepath.relative_to(root_dir)
    logger.info("Created: %s", rel_path)
    print(f"\nNew migration: {rel_path}")
    print(f"Edit the file, then run: python -m backend.01_migrator.runner apply\n")

    return filepath


# ── CLI ──────────────────────────────────────────────────────────────


def main() -> None:
    parser = argparse.ArgumentParser(
        description="TennetCTL SQL Migrator — feature-distributed schema management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
commands:
  apply       Apply all pending migrations from 02_in_progress/ dirs (default)
  rollback    Roll back the last applied migration (or --to target)
  seed        Apply pending seed files (YAML/JSON) from 09_sql_migrations/seeds/
  status      Show applied and pending migrations
  history     Show full migration history with rollbacks
  new         Scaffold a new migration file in the right sub-feature directory

examples:
  python -m backend.01_migrator.runner apply
  python -m backend.01_migrator.runner apply --dry-run
  python -m backend.01_migrator.runner status
  python -m backend.01_migrator.runner rollback
  python -m backend.01_migrator.runner rollback --to 20260413_002_create-users.sql
  python -m backend.01_migrator.runner seed
  python -m backend.01_migrator.runner seed --dry-run
  python -m backend.01_migrator.runner new --name create-iam-schema --feature 03_iam --sub 00_bootstrap
  python -m backend.01_migrator.runner history
""",
    )

    parser.add_argument(
        "command",
        nargs="?",
        default="apply",
        choices=["apply", "rollback", "seed", "status", "history", "new"],
        help="Command to run (default: apply)",
    )
    parser.add_argument(
        "--dsn",
        default=os.environ.get(
            "DATABASE_URL",
            "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
        ),
        help="PostgreSQL connection string (default: DATABASE_URL env var)",
    )
    parser.add_argument(
        "--root",
        default=str(DEFAULT_ROOT_DIR),
        help="Project root directory — migrator scans recursively from here "
             "(default: project root)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would happen without making changes",
    )
    parser.add_argument(
        "--to",
        dest="target",
        help="Rollback target filename (roll back to and including this migration)",
    )
    parser.add_argument(
        "--name",
        default="unnamed",
        help="Name for new migration file (used with 'new' command)",
    )
    parser.add_argument(
        "--feature",
        help="Feature directory name for 'new' command (e.g. 03_iam)",
    )
    parser.add_argument(
        "--sub",
        help="Sub-feature directory name for 'new' command (e.g. 00_bootstrap)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable debug logging",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    root_dir = Path(args.root)

    try:
        if args.command == "apply":
            stats = asyncio.run(run_apply(args.dsn, root_dir, args.dry_run))
            if stats["applied"] == 0 and stats["skipped"] == stats["total"]:
                logger.info("Database is up to date.")

        elif args.command == "rollback":
            asyncio.run(run_rollback(args.dsn, root_dir, args.target, args.dry_run))

        elif args.command == "seed":
            asyncio.run(run_seed(args.dsn, root_dir, args.dry_run))

        elif args.command == "status":
            asyncio.run(run_status(args.dsn, root_dir))

        elif args.command == "history":
            asyncio.run(run_history(args.dsn))

        elif args.command == "new":
            run_new(root_dir, args.name, args.feature, args.sub)

        sys.exit(0)

    except RuntimeError as exc:
        logger.error("Failed: %s", exc)
        sys.exit(1)
    except asyncpg.PostgresError as exc:
        logger.error("Database error: %s", exc)
        sys.exit(1)
    except OSError as exc:
        logger.error("Connection error: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
