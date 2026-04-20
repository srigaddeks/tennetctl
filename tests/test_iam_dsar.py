"""
Tests for iam.dsar — DSAR (Data Subject Access Request) sub-feature.

Operator-triggered requests: export (SAR) and delete (RTBF).
Uses live DB — assumes schemas are already migrated.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import pytest

LIVE_DSN = os.environ.get(
    "DATABASE_URL",
    "postgresql://tennetctl:tennetctl_dev@localhost:5434/tennetctl",
)

_core_id: Any = import_module("backend.01_core.id")
_repo: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.repository")
_service: Any = import_module("backend.02_features.03_iam.sub_features.08_dsar.service")


class MockContext:
    """Mock request context."""
    def __init__(self, user_id: str, org_id: str, session_id: str | None = None, workspace_id: str | None = None):
        self.user_id = user_id
        self.org_id = org_id
        self.session_id = session_id
        self.workspace_id = workspace_id


@pytest.fixture
async def pool() -> Any:
    """Pool connected to live DB."""
    try:
        import asyncpg
    except ImportError as e:
        pytest.skip(f"asyncpg not available: {e}")
    p = await asyncpg.create_pool(LIVE_DSN, min_size=1, max_size=3)
    yield p
    await p.close()


@pytest.fixture
async def test_org_and_users(pool: Any) -> dict:
    """Create test org and users for DSAR tests."""
    async with pool.acquire() as conn:
        # Create org
        org_id = _core_id.uuid7()
        await conn.execute(
            'INSERT INTO "03_iam"."10_fct_orgs" (id, slug, created_by, updated_by) VALUES ($1, $2, $3, $3)',
            org_id, f"test-org-{org_id[:8]}", "system",
        )

        # Create operator user
        operator_id = _core_id.uuid7()
        await conn.execute(
            'INSERT INTO "03_iam"."10_fct_users" (id, created_by, updated_by) VALUES ($1, $2, $2)',
            operator_id, "system",
        )

        # Create subject user
        subject_id = _core_id.uuid7()
        await conn.execute(
            'INSERT INTO "03_iam"."10_fct_users" (id, created_by, updated_by) VALUES ($1, $2, $2)',
            subject_id, "system",
        )

        # Add both users to org
        for uid in [operator_id, subject_id]:
            await conn.execute(
                'INSERT INTO "03_iam"."40_lnk_org_members" (id, org_id, user_id, created_by) '
                'VALUES ($1, $2, $3, $4)',
                _core_id.uuid7(), org_id, uid, "system",
            )

    return {
        "org_id": org_id,
        "operator_id": operator_id,
        "subject_id": subject_id,
    }


# ────────────────────────────────────────────────────────────────────────────
# Test: create_export_request
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_request_creates_job(pool: Any, test_org_and_users: dict) -> None:
    """Export request should INSERT job with status=requested."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id, session_id=_core_id.uuid7())

    async with pool.acquire() as conn:
        job = await _service.create_export_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )

    assert job is not None
    assert job["status"] == "requested"
    assert job["job_type"] == "export"
    assert job["subject_user_id"] == subject_id
    assert job["org_id"] == org_id


@pytest.mark.asyncio
async def test_export_request_rate_limit(pool: Any, test_org_and_users: dict) -> None:
    """11th request in 1 hour should fail with 429."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id, session_id=_core_id.uuid7())

    # Create 10 jobs
    async with pool.acquire() as conn:
        for _ in range(10):
            await _service.create_export_request(
                pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
            )

    # 11th should fail
    from importlib import import_module
    _errors = import_module("backend.01_core.errors")

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _service.create_export_request(
                pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
            )
        assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_export_request_nonexistent_user(pool: Any, test_org_and_users: dict) -> None:
    """Request for nonexistent user should fail with 404."""
    from importlib import import_module
    _errors = import_module("backend.01_core.errors")

    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    fake_user_id = _core_id.uuid7()

    ctx = MockContext(user_id=operator_id, org_id=org_id)

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _service.create_export_request(
                pool, conn, ctx, subject_user_id=fake_user_id, org_id=org_id
            )
        assert exc_info.value.status_code == 404


# ────────────────────────────────────────────────────────────────────────────
# Test: create_delete_request
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_request_creates_job(pool: Any, test_org_and_users: dict) -> None:
    """Delete request should INSERT job with status=requested."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id)

    async with pool.acquire() as conn:
        job = await _service.create_delete_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )

    assert job is not None
    assert job["status"] == "requested"
    assert job["job_type"] == "delete"


@pytest.mark.asyncio
async def test_delete_request_cascades_data(pool: Any, test_org_and_users: dict) -> None:
    """Worker should cascade-delete sessions, credentials, attributes."""
    from importlib import import_module
    _core_id_mod = import_module("backend.01_core.id")

    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    # Add a session for the subject
    async with pool.acquire() as conn:
        session_id = _core_id_mod.uuid7()
        await conn.execute(
            'INSERT INTO "03_iam"."12_fct_sessions" (id, user_id, created_by, updated_by) '
            'VALUES ($1, $2, $3, $3)',
            session_id, subject_id, "system",
        )

    # Create delete job
    ctx = MockContext(user_id=operator_id, org_id=org_id)
    async with pool.acquire() as conn:
        job = await _service.create_delete_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )

    job_id = job["id"]

    # Process delete job (call worker function directly)
    await _service._process_dsar_delete_job(pool, job_id)

    # Verify session deleted
    async with pool.acquire() as conn:
        session_count = await conn.fetchval(
            'SELECT COUNT(*) FROM "03_iam"."12_fct_sessions" WHERE user_id = $1',
            subject_id,
        )
        assert session_count == 0

        # Verify user soft-deleted
        user_row = await conn.fetchrow(
            'SELECT deleted_at FROM "03_iam"."10_fct_users" WHERE id = $1',
            subject_id,
        )
        assert user_row is not None
        assert user_row["deleted_at"] is not None


@pytest.mark.asyncio
async def test_delete_request_idempotent(pool: Any, test_org_and_users: dict) -> None:
    """Second delete on same user should succeed (idempotent)."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id)

    # First delete request
    async with pool.acquire() as conn:
        job1 = await _service.create_delete_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )
    await _service._process_dsar_delete_job(pool, job1["id"])

    # Second delete request (should succeed)
    async with pool.acquire() as conn:
        job2 = await _service.create_delete_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )
    assert job2 is not None
    assert job2["status"] == "requested"


# ────────────────────────────────────────────────────────────────────────────
# Test: poll_dsar_job
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_poll_job_in_progress(pool: Any, test_org_and_users: dict) -> None:
    """Poll should show status=in_progress and null result_location."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id)

    async with pool.acquire() as conn:
        job = await _service.create_export_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )

    job_id = job["id"]

    # Update to in_progress
    async with pool.acquire() as conn:
        await _repo.update_dsar_job_status(
            conn,
            job_id=job_id,
            status="in_progress",
        )

    # Poll
    polled = await _service.poll_dsar_job(pool, ctx, job_id)
    assert polled["status"] == "in_progress"
    assert polled["result_location"] is None


@pytest.mark.asyncio
async def test_poll_job_completed(pool: Any, test_org_and_users: dict) -> None:
    """Poll completed export should include result_location."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id)

    async with pool.acquire() as conn:
        job = await _service.create_export_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )

    job_id = job["id"]

    # Mark completed with result location
    async with pool.acquire() as conn:
        await _repo.update_dsar_job_status(
            conn,
            job_id=job_id,
            status="completed",
            result_location="vault://dsar/abc123/export.json",
        )

    # Poll
    polled = await _service.poll_dsar_job(pool, ctx, job_id)
    assert polled["status"] == "completed"
    assert "vault://" in polled["result_location"]


# ────────────────────────────────────────────────────────────────────────────
# Test: export_user_data
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_data_includes_user_record(pool: Any, test_org_and_users: dict) -> None:
    """Export should include user record."""
    subject_id = test_org_and_users["subject_id"]
    org_id = test_org_and_users["org_id"]

    data = await _repo.export_user_data(pool, subject_id, org_id)

    # Check that users list is populated
    assert "users" in data
    assert len(data["users"]) > 0
    # Note: v_users view query must exist
    # For now, just verify the function completes


@pytest.mark.asyncio
async def test_delete_user_data_soft_deletes_user(pool: Any, test_org_and_users: dict) -> None:
    """Hard delete should soft-delete fct_users (set deleted_at)."""
    subject_id = test_org_and_users["subject_id"]
    org_id = test_org_and_users["org_id"]

    async with pool.acquire() as conn:
        counts = await _repo.delete_user_data(conn, subject_id, org_id)

    assert counts["users"] == 1

    # Verify user deleted_at is set
    async with pool.acquire() as conn:
        user = await conn.fetchrow(
            'SELECT deleted_at FROM "03_iam"."10_fct_users" WHERE id = $1',
            subject_id,
        )
        assert user is not None
        assert user["deleted_at"] is not None


# ────────────────────────────────────────────────────────────────────────────
# Test: cross-org checks
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cross_org_export_denied(pool: Any, test_org_and_users: dict) -> None:
    """Export request from wrong org context should fail with 403."""
    from importlib import import_module
    _errors = import_module("backend.01_core.errors")

    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    wrong_org_id = _core_id.uuid7()

    ctx = MockContext(user_id=operator_id, org_id=wrong_org_id)

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _service.create_export_request(
                pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
            )
        # Should fail because user doesn't belong to requested org_id
        assert exc_info.value.status_code in [403, 404]


@pytest.mark.asyncio
async def test_cross_org_delete_denied(pool: Any, test_org_and_users: dict) -> None:
    """Delete request from wrong org context should fail with 403."""
    from importlib import import_module
    _errors = import_module("backend.01_core.errors")

    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    wrong_org_id = _core_id.uuid7()

    ctx = MockContext(user_id=operator_id, org_id=wrong_org_id)

    async with pool.acquire() as conn:
        with pytest.raises(_errors.AppError) as exc_info:
            await _service.create_delete_request(
                pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
            )
        assert exc_info.value.status_code in [403, 404]


# ────────────────────────────────────────────────────────────────────────────
# Test: list_jobs
# ────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_jobs_paginated(pool: Any, test_org_and_users: dict) -> None:
    """List should return paginated results with total."""
    org_id = test_org_and_users["org_id"]
    operator_id = test_org_and_users["operator_id"]
    subject_id = test_org_and_users["subject_id"]

    ctx = MockContext(user_id=operator_id, org_id=org_id)

    # Create 2 jobs
    async with pool.acquire() as conn:
        await _service.create_export_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )
        await _service.create_export_request(
            pool, conn, ctx, subject_user_id=subject_id, org_id=org_id
        )

    # List
    result = await _service.list_jobs(pool, ctx, limit=50, offset=0)

    assert result["total"] >= 2
    assert len(result["jobs"]) >= 2
    assert result["limit"] == 50
    assert result["offset"] == 0
