"""
Smoke test for backend/01_catalog/ — end-to-end pipeline against the live
tennetctl DB (not the tennetctl_test DB, because the 01_catalog schema is
applied via the migrator to the main DB).

Runs against the fixture feature at tests/fixtures/features/99_test_fixture/.

Always self-cleans so repeated runs start from an empty catalog.
"""

from __future__ import annotations

import asyncio
import os
from importlib import import_module

import asyncpg
import pytest

_catalog = import_module("backend.01_catalog")
_db = import_module("backend.01_core.database")

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

FIXTURE_FEATURE_KEY = "core"
FIXTURE_SUB_KEY = "core.sample"
FIXTURE_NODE_KEY = "core.sample.ping"


async def _clean(pool: asyncpg.Pool) -> None:
    """Delete fixture rows (reverse FK order)."""
    async with pool.acquire() as conn:
        await conn.execute(
            'DELETE FROM "01_catalog"."12_fct_nodes" WHERE key LIKE $1',
            f"{FIXTURE_FEATURE_KEY}.%",
        )
        await conn.execute(
            'DELETE FROM "01_catalog"."11_fct_sub_features" WHERE key LIKE $1',
            f"{FIXTURE_FEATURE_KEY}.%",
        )
        await conn.execute(
            'DELETE FROM "01_catalog"."10_fct_features" WHERE key = $1',
            FIXTURE_FEATURE_KEY,
        )


async def _count(pool: asyncpg.Pool, table: str, key: str) -> int:
    async with pool.acquire() as conn:
        return await conn.fetchval(
            f'SELECT count(*) FROM "01_catalog"."{table}" WHERE key = $1', key
        )


@pytest.mark.asyncio
async def test_fixture_feature_registers() -> None:
    """Fixture feature registers idempotently and cleans up."""
    pool = await _db.create_pool(LIVE_DSN)
    try:
        await _clean(pool)
        # Run 1: insert
        report1 = await _catalog.upsert_all(
            pool, frozenset({"core"}), fixtures=True
        )
        assert report1.features_upserted == 1
        assert report1.sub_features_upserted == 1
        # Fixture now exposes 5 nodes (ping/echo/slow/flaky/broken) for runner tests.
        assert report1.nodes_upserted == 5
        assert not report1.errors

        assert await _count(pool, "10_fct_features", FIXTURE_FEATURE_KEY) == 1
        assert await _count(pool, "11_fct_sub_features", FIXTURE_SUB_KEY) == 1
        assert await _count(pool, "12_fct_nodes", FIXTURE_NODE_KEY) == 1

        # Run 2: idempotent — no new rows
        report2 = await _catalog.upsert_all(
            pool, frozenset({"core"}), fixtures=True
        )
        assert report2.features_upserted == 1  # upsert counts as "upserted" even if row exists
        assert await _count(pool, "10_fct_features", FIXTURE_FEATURE_KEY) == 1
        assert await _count(pool, "11_fct_sub_features", FIXTURE_SUB_KEY) == 1
        assert await _count(pool, "12_fct_nodes", FIXTURE_NODE_KEY) == 1
        # Total node rows under "core.sample.*" should still be exactly 5 (no dupes).
        async with pool.acquire() as conn:
            total = await conn.fetchval(
                'SELECT count(*) FROM "01_catalog"."12_fct_nodes" WHERE key LIKE $1',
                f"{FIXTURE_FEATURE_KEY}.%",
            )
            assert total == 5

        # Verify the node has expected attributes.
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                'SELECT kind_id, emits_audit, handler_path '
                'FROM "01_catalog"."12_fct_nodes" WHERE key = $1',
                FIXTURE_NODE_KEY,
            )
            assert row is not None
            assert row["kind_id"] == 3  # control
            assert row["emits_audit"] is False
            assert row["handler_path"].endswith("PingNode")
    finally:
        await _clean(pool)
        await _db.close_pool(pool)


@pytest.mark.asyncio
async def test_invalid_manifest_raises(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Effect node with emits_audit=false must be rejected at parse time."""
    bad = tmp_path / "feature.manifest.yaml"
    bad.write_text(
        """
apiVersion: tennetctl/v1
kind: Feature
metadata:
  key: core
  number: 99
  module: core
  label: X
  manifest_version: 1
spec:
  sub_features:
    - key: core.bad
      number: 1
      label: Bad
      nodes:
        - key: core.bad.violates
          kind: effect
          handler: h.Y
          label: Y
          emits_audit: false
""",
        encoding="utf-8",
    )
    with pytest.raises(_catalog.ManifestInvalid):
        _catalog.parse_manifest(bad)


if __name__ == "__main__":
    asyncio.run(test_fixture_feature_registers())
    print("manual run ok")
