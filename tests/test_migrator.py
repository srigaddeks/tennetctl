"""Integration tests for the SQL migrator — runs against real Postgres."""

from __future__ import annotations

from importlib import import_module
from pathlib import Path

import asyncpg
import pytest

_runner = import_module("backend.01_migrator.runner")

TEST_DSN = "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl_test"

TRACKING_TABLE = '"00_schema_migrations".applied_migrations'


# ── Bootstrap ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_bootstrap_creates_schema_and_table(clean_db):
    """Migrator bootstrap creates 00_schema_migrations schema + tracking table."""
    conn = clean_db
    await _runner.bootstrap(conn)

    schema_exists = await conn.fetchval(
        "SELECT 1 FROM information_schema.schemata WHERE schema_name = '00_schema_migrations'"
    )
    assert schema_exists == 1

    table_exists = await conn.fetchval(
        "SELECT 1 FROM information_schema.tables "
        "WHERE table_schema = '00_schema_migrations' AND table_name = 'applied_migrations'"
    )
    assert table_exists == 1


@pytest.mark.asyncio
async def test_bootstrap_has_required_columns(clean_db):
    """Tracking table has all v2 columns: status, applied_by, rolled_back_at, etc."""
    conn = clean_db
    await _runner.bootstrap(conn)

    columns = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = '00_schema_migrations' AND table_name = 'applied_migrations'"
    )
    col_names = {row["column_name"] for row in columns}

    expected = {"id", "filename", "checksum", "status", "applied_by",
                "applied_at", "rolled_back_at", "rolled_back_by", "duration_ms"}
    assert expected.issubset(col_names)


# ── Parsing ──────────────────────────────────────────────────────────


def test_parse_migration_valid():
    """Parses UP and DOWN sections correctly."""
    content = "-- UP ====\nCREATE TABLE t (id int);\n-- DOWN ====\nDROP TABLE t;"
    sections = _runner.parse_migration(content)
    assert sections["up"] == "CREATE TABLE t (id int);"
    assert sections["down"] == "DROP TABLE t;"


def test_parse_migration_missing_up():
    """Raises ValueError when UP marker is missing."""
    with pytest.raises(ValueError, match="Missing"):
        _runner.parse_migration("-- DOWN ====\nDROP TABLE t;")


def test_parse_migration_missing_down():
    """Raises ValueError when DOWN marker is missing."""
    with pytest.raises(ValueError, match="Missing"):
        _runner.parse_migration("-- UP ====\nCREATE TABLE t (id int);")


def test_parse_migration_wrong_order():
    """Raises ValueError when DOWN comes before UP."""
    with pytest.raises(ValueError, match="must come after"):
        _runner.parse_migration("-- DOWN ====\nDROP TABLE t;\n-- UP ====\nCREATE TABLE t;")


# ── Apply ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_applies_migrations_in_order(clean_db, temp_migrations_dir):
    """Migrations are applied in filename sort order."""
    (temp_migrations_dir / "20260101_001_first.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_first (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_first;"
    )
    (temp_migrations_dir / "20260101_002_second.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_second (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_second;"
    )
    (temp_migrations_dir / "20260101_003_third.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_third (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_third;"
    )

    stats = await _runner.run_apply(TEST_DSN, temp_migrations_dir)

    assert stats["applied"] == 3
    assert stats["skipped"] == 0
    assert stats["total"] == 3

    # Verify order via tracking table
    conn = await asyncpg.connect(TEST_DSN)
    try:
        rows = await conn.fetch(
            f"SELECT filename FROM {TRACKING_TABLE} WHERE status = 'applied' ORDER BY id"
        )
        filenames = [r["filename"] for r in rows]
        assert filenames == [
            "20260101_001_first.sql",
            "20260101_002_second.sql",
            "20260101_003_third.sql",
        ]
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_skips_already_applied(clean_db, temp_migrations_dir):
    """Second run skips already-applied migrations."""
    (temp_migrations_dir / "20260101_001_test.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_skip (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_skip;"
    )

    stats_first = await _runner.run_apply(TEST_DSN, temp_migrations_dir)
    assert stats_first["applied"] == 1

    stats_second = await _runner.run_apply(TEST_DSN, temp_migrations_dir)
    assert stats_second["applied"] == 0
    assert stats_second["skipped"] == 1


@pytest.mark.asyncio
async def test_records_checksum_and_user(clean_db, temp_migrations_dir):
    """Applied migrations store correct checksum and username."""
    content = "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_cs (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_cs;"
    (temp_migrations_dir / "20260101_001_checksum.sql").write_text(content)

    await _runner.run_apply(TEST_DSN, temp_migrations_dir)

    expected_checksum = _runner.compute_checksum(content)

    conn = await asyncpg.connect(TEST_DSN)
    try:
        row = await conn.fetchrow(
            f"SELECT checksum, applied_by, status, duration_ms FROM {TRACKING_TABLE} "
            f"WHERE filename = $1 AND status = 'applied'",
            "20260101_001_checksum.sql",
        )
        assert row["checksum"] == expected_checksum
        assert row["applied_by"] != "unknown"
        assert row["status"] == "applied"
        assert row["duration_ms"] >= 0
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_checksum_mismatch_errors(clean_db, temp_migrations_dir):
    """Modified migration file after apply raises RuntimeError."""
    filepath = temp_migrations_dir / "20260101_001_mismatch.sql"
    filepath.write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_mm (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_mm;"
    )

    await _runner.run_apply(TEST_DSN, temp_migrations_dir)

    # Modify the file after applying
    filepath.write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_mm (id int, name text);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_mm;"
    )

    with pytest.raises(RuntimeError, match="Checksum mismatch"):
        await _runner.run_apply(TEST_DSN, temp_migrations_dir)


@pytest.mark.asyncio
async def test_dry_run_does_not_apply(clean_db, temp_migrations_dir):
    """Dry run reports pending without actually applying."""
    (temp_migrations_dir / "20260101_001_dryrun.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_dr (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_dr;"
    )

    stats = await _runner.run_apply(TEST_DSN, temp_migrations_dir, dry_run=True)
    assert stats["applied"] == 1  # reported as "would apply"

    conn = await asyncpg.connect(TEST_DSN)
    try:
        count = await conn.fetchval(
            f"SELECT count(*) FROM {TRACKING_TABLE} WHERE status = 'applied'"
        )
        assert count == 0
    finally:
        await conn.close()


# ── Rollback ─────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_rollback_last_migration(clean_db, temp_migrations_dir):
    """Rolling back reverses the last applied migration."""
    (temp_migrations_dir / "20260101_001_first.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_rb1 (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_rb1;"
    )
    (temp_migrations_dir / "20260101_002_second.sql").write_text(
        "-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_rb2 (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_rb2;"
    )

    await _runner.run_apply(TEST_DSN, temp_migrations_dir)
    stats = await _runner.run_rollback(TEST_DSN, temp_migrations_dir)

    assert stats["rolled_back"] == 1

    conn = await asyncpg.connect(TEST_DSN)
    try:
        # Second migration should be rolled back
        row = await conn.fetchrow(
            f"SELECT status, rolled_back_by FROM {TRACKING_TABLE} "
            f"WHERE filename = '20260101_002_second.sql'"
        )
        assert row["status"] == "rolled_back"
        assert row["rolled_back_by"] is not None

        # First should still be applied
        row = await conn.fetchrow(
            f"SELECT status FROM {TRACKING_TABLE} "
            f"WHERE filename = '20260101_001_first.sql'"
        )
        assert row["status"] == "applied"

        # Table should be gone
        exists = await conn.fetchval(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_name = 'test_rb2'"
        )
        assert exists is None
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_rollback_to_target(clean_db, temp_migrations_dir):
    """Rolling back to a target reverses all migrations from target onwards."""
    for i in range(1, 4):
        (temp_migrations_dir / f"20260101_{i:03d}_m{i}.sql").write_text(
            f"-- UP ====\nCREATE TABLE IF NOT EXISTS public.test_rbt{i} (id int);\n-- DOWN ====\nDROP TABLE IF EXISTS public.test_rbt{i};"
        )

    await _runner.run_apply(TEST_DSN, temp_migrations_dir)
    stats = await _runner.run_rollback(
        TEST_DSN, temp_migrations_dir, target="20260101_002_m2.sql"
    )

    assert stats["rolled_back"] == 2  # m2 and m3

    conn = await asyncpg.connect(TEST_DSN)
    try:
        applied = await conn.fetch(
            f"SELECT filename FROM {TRACKING_TABLE} WHERE status = 'applied' ORDER BY id"
        )
        assert len(applied) == 1
        assert applied[0]["filename"] == "20260101_001_m1.sql"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_rollback_empty_does_nothing(clean_db, temp_migrations_dir):
    """Rolling back with no applied migrations does nothing."""
    stats = await _runner.run_rollback(TEST_DSN, temp_migrations_dir)
    assert stats["rolled_back"] == 0


# ── Status ───────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_status_shows_applied_and_pending(clean_db, temp_migrations_dir):
    """Status reports applied and pending migrations correctly."""
    (temp_migrations_dir / "20260101_001_done.sql").write_text(
        "-- UP ====\nSELECT 1;\n-- DOWN ====\nSELECT 1;"
    )
    (temp_migrations_dir / "20260101_002_pending.sql").write_text(
        "-- UP ====\nSELECT 1;\n-- DOWN ====\nSELECT 1;"
    )

    # Apply only the first
    conn = await asyncpg.connect(TEST_DSN)
    try:
        await _runner.bootstrap(conn)
        content = (temp_migrations_dir / "20260101_001_done.sql").read_text()
        sections = _runner.parse_migration(content)
        await _runner.apply_single(
            conn, temp_migrations_dir / "20260101_001_done.sql",
            "20260101_001_done.sql",
            _runner.compute_checksum(content),
            sections["up"], "test",
        )
    finally:
        await conn.close()

    result = await _runner.run_status(TEST_DSN, temp_migrations_dir)
    assert result["applied"] == ["20260101_001_done.sql"]
    assert result["pending"] == ["20260101_002_pending.sql"]


# ── New migration scaffold ───────────────────────────────────────────


def test_new_migration_creates_file(temp_migrations_dir):
    """Scaffolding creates a file with UP/DOWN markers."""
    filepath = _runner.run_new(temp_migrations_dir, "create-users")

    assert filepath.exists()
    content = filepath.read_text()
    assert "-- UP ====" in content
    assert "-- DOWN ====" in content
    assert "create-users" in filepath.name


def test_new_migration_increments_sequence(temp_migrations_dir):
    """Sequence number increments from last existing migration."""
    (temp_migrations_dir / "20260101_005_existing.sql").write_text("-- UP ====\n-- DOWN ====")

    filepath = _runner.run_new(temp_migrations_dir, "next")
    # Should be _006_ since last was _005_
    assert "_006_" in filepath.name


# ── Utilities ────────────────────────────────────────────────────────


def test_discover_migrations_sorted(temp_migrations_dir):
    """Migrations are discovered in sorted filename order."""
    (temp_migrations_dir / "20260103_001_c.sql").write_text("-- UP ====\n-- DOWN ====")
    (temp_migrations_dir / "20260101_001_a.sql").write_text("-- UP ====\n-- DOWN ====")
    (temp_migrations_dir / "20260102_001_b.sql").write_text("-- UP ====\n-- DOWN ====")
    (temp_migrations_dir / "not_sql.txt").write_text("ignore me")

    results = _runner.discover_migrations(temp_migrations_dir)
    names = [p.name for p in results]
    assert names == [
        "20260101_001_a.sql",
        "20260102_001_b.sql",
        "20260103_001_c.sql",
    ]


def test_empty_migrations_dir(temp_migrations_dir):
    """Empty migrations directory returns empty list."""
    results = _runner.discover_migrations(temp_migrations_dir)
    assert results == []


def test_compute_checksum_consistent():
    """SHA256 checksum is consistent and correct."""
    content = "SELECT 1;"
    checksum1 = _runner.compute_checksum(content)
    checksum2 = _runner.compute_checksum(content)
    assert checksum1 == checksum2
    assert len(checksum1) == 64

    different = _runner.compute_checksum("SELECT 2;")
    assert different != checksum1
