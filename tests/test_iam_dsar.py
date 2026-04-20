"""
Tests for IAM DSAR (Data Subject Access Request) — export and delete operations.
Phase: 45-01
"""

import pytest
from uuid import UUID
from importlib import import_module

_db = import_module("backend.01_core.database")
_id = import_module("backend.01_core.id")
_dsar_repo = import_module("backend.02_features.03_iam.sub_features.08_dsar.repository")
_dsar_service = import_module("backend.02_features.03_iam.sub_features.08_dsar.service")
_dsar_schemas = import_module("backend.02_features.03_iam.sub_features.08_dsar.schemas")
_ctx_mod = import_module("backend.01_catalog.context")


@pytest.fixture
async def test_org_id(pool):
    """Create a test organization."""
    async with pool.acquire() as conn:
        org_id = await conn.fetchval(
            "INSERT INTO 03_iam.fct_orgs (org_id, org_name) VALUES ($1, $2) RETURNING org_id",
            _id.uuid7(), "Test Org"
        )
    return org_id


@pytest.fixture
async def test_user_id(pool, test_org_id):
    """Create a test user."""
    async with pool.acquire() as conn:
        user_id = await conn.fetchval(
            "INSERT INTO 03_iam.fct_users (user_id, email, created_by) VALUES ($1, $2, $3) RETURNING user_id",
            _id.uuid7(), f"test-{_id.uuid7()}@example.com", _id.uuid7()
        )
    return user_id


@pytest.fixture
async def test_actor_id(pool, test_org_id):
    """Create an operator user."""
    async with pool.acquire() as conn:
        actor_id = await conn.fetchval(
            "INSERT INTO 03_iam.fct_users (user_id, email, created_by) VALUES ($1, $2, $3) RETURNING user_id",
            _id.uuid7(), f"operator-{_id.uuid7()}@example.com", _id.uuid7()
        )
    return actor_id


@pytest.fixture
def test_ctx(pool, test_actor_id, test_org_id):
    """Create test NodeContext."""
    return _ctx_mod.NodeContext(
        user_id=test_actor_id,
        session_id=_id.uuid7(),
        org_id=test_org_id,
        workspace_id=_id.uuid7(),
        audit_category="system",
        trace_id=_id.uuid7(),
        span_id=_id.uuid7(),
        request_id=_id.uuid7(),
        pool=pool,
        actor_id=test_actor_id,
        extras={"pool": pool},
    )


@pytest.mark.asyncio
async def test_export_request_creates_job(pool, test_org_id, test_user_id, test_actor_id):
    """Export request inserts job with status=requested."""
    async with pool.acquire() as conn:
        job = await _dsar_repo.create_dsar_job(
            conn, test_actor_id, test_user_id, test_org_id, "export"
        )

    assert job is not None
    assert job["job_type"] == "export"
    assert job["actor_user_id"] == test_actor_id
    assert job["subject_user_id"] == test_user_id
    assert job["org_id"] == test_org_id
    assert job["status"] == "requested"
    assert job["row_counts"] is None


@pytest.mark.asyncio
async def test_delete_request_creates_job(pool, test_org_id, test_user_id, test_actor_id):
    """Delete request inserts job with status=requested."""
    async with pool.acquire() as conn:
        job = await _dsar_repo.create_dsar_job(
            conn, test_actor_id, test_user_id, test_org_id, "delete"
        )

    assert job is not None
    assert job["job_type"] == "delete"
    assert job["status"] == "requested"


@pytest.mark.asyncio
async def test_delete_soft_deletes_user(pool, test_org_id, test_user_id):
    """Delete soft-deletes user record (deleted_at set)."""
    async with pool.acquire() as conn:
        await _dsar_repo.delete_user_data(conn, test_user_id, test_org_id)

        user = await conn.fetchrow(
            "SELECT deleted_at FROM 03_iam.fct_users WHERE user_id = $1",
            test_user_id
        )

    assert user["deleted_at"] is not None


@pytest.mark.asyncio
async def test_delete_idempotent(pool, test_org_id, test_user_id):
    """Deleting same user twice is idempotent (no errors)."""
    async with pool.acquire() as conn:
        # First delete
        counts1 = await _dsar_repo.delete_user_data(conn, test_user_id, test_org_id)

        # Second delete (should succeed, return 0 counts)
        counts2 = await _dsar_repo.delete_user_data(conn, test_user_id, test_org_id)

    assert counts1["workspace_members"] >= 0
    assert counts2["workspace_members"] >= 0


@pytest.mark.asyncio
async def test_poll_job_in_progress(pool, test_org_id, test_user_id, test_actor_id):
    """Poll job returns status=requested with null result_location."""
    async with pool.acquire() as conn:
        job = await _dsar_repo.create_dsar_job(
            conn, test_actor_id, test_user_id, test_org_id, "export"
        )

    ctx = _ctx_mod.NodeContext(
        user_id=test_actor_id,
        org_id=test_org_id,
        trace_id=_id.uuid7(),
        span_id=_id.uuid7(),
        pool=pool,
        actor_id=test_actor_id,
        extras={"pool": pool},
    )

    job_data = await _dsar_service.poll_dsar_job(pool, ctx, job["job_id"], test_org_id)

    assert job_data["status"] in ["requested", "in_progress"]
    assert job_data["download_url"] is None


@pytest.mark.asyncio
async def test_poll_job_completed(pool, test_org_id, test_user_id, test_actor_id):
    """Poll completed job returns download URL."""
    async with pool.acquire() as conn:
        job = await _dsar_repo.create_dsar_job(
            conn, test_actor_id, test_user_id, test_org_id, "export"
        )

        # Manually mark as completed
        await _dsar_repo.update_dsar_job_status(
            conn,
            job["job_id"],
            "completed",
            row_counts={"total": 5},
            result_location="iam.dsar.test-key"
        )

    ctx = _ctx_mod.NodeContext(
        user_id=test_actor_id,
        org_id=test_org_id,
        trace_id=_id.uuid7(),
        span_id=_id.uuid7(),
        pool=pool,
        actor_id=test_actor_id,
        extras={"pool": pool},
    )

    job_data = await _dsar_service.poll_dsar_job(pool, ctx, job["job_id"], test_org_id)

    assert job_data["status"] == "completed"
    assert job_data["row_counts"] == {"total": 5}
    assert job_data["download_url"] is not None


def test_dsar_export_request_schema():
    """DsarExportRequest schema is valid."""
    from uuid import uuid4
    user_id = uuid4()
    org_id = uuid4()

    req = _dsar_schemas.DsarExportRequest(
        subject_user_id=user_id,
        org_id=org_id
    )

    assert req.subject_user_id == user_id
    assert req.org_id == org_id


def test_dsar_delete_request_schema():
    """DsarDeleteRequest schema is valid."""
    from uuid import uuid4
    user_id = uuid4()
    org_id = uuid4()

    req = _dsar_schemas.DsarDeleteRequest(
        subject_user_id=user_id,
        org_id=org_id
    )

    assert req.subject_user_id == user_id
    assert req.org_id == org_id
