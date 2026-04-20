"""Routes for audit.retention_policy."""

from importlib import import_module
from uuid import UUID
from fastapi import APIRouter, Depends, Request

_response = import_module("backend.01_core.response")
_errors = import_module("backend.01_core.errors")
_ctx_mod = import_module("backend.01_catalog.context")

from . import schemas, service


router = APIRouter(prefix="/v1/audit", tags=["audit.retention"])


@router.get("/retention-policy", status_code=200)
async def get_retention_policy_route(
    request: Request,
    org_id: str,
) -> dict:
    """Retrieve org's audit retention policy."""
    pool = request.app.state.pool
    policy = await service.get_retention_policy(pool, UUID(org_id))
    if not policy:
        raise _errors.HTTPException(404, "Retention policy not found")
    return _response.ok(policy)


@router.patch("/retention-policy", status_code=200)
async def update_retention_policy_route(
    request: Request,
    org_id: str,
    body: schemas.RetentionPolicyUpdate,
) -> dict:
    """Update retention policy (admin only)."""
    pool = request.app.state.pool
    org_uuid = UUID(org_id)

    async with pool.acquire() as conn:
        # Fetch policy
        policy = await conn.fetchrow(
            "SELECT policy_id FROM 04_audit.fct_audit_retention_policies WHERE org_id = $1",
            org_uuid
        )
        if not policy:
            raise _errors.HTTPException(404, "Retention policy not found")

        # Update
        updated = await service.update_retention_policy(
            conn,
            policy["policy_id"],
            retention_days=body.retention_days,
            auto_purge_enabled=body.auto_purge_enabled,
            exclude_critical=body.exclude_critical,
            status=body.status,
        )

    return _response.ok(schemas.RetentionPolicyRead(**updated).model_dump())


@router.post("/retention-policy/purge", status_code=202)
async def trigger_purge_route(
    request: Request,
    org_id: str,
) -> dict:
    """Manually trigger purge job for org."""
    pool = request.app.state.pool
    org_uuid = UUID(org_id)

    # Get user from request state
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.HTTPException(403, "Authentication required")

    async with pool.acquire() as conn:
        # Get policy
        policy = await conn.fetchrow(
            "SELECT policy_id FROM 04_audit.fct_audit_retention_policies WHERE org_id = $1",
            org_uuid
        )
        if not policy:
            raise _errors.HTTPException(404, "Retention policy not found")

        # Create and execute purge job
        job = await service.execute_purge_job(
            conn,
            policy["policy_id"],
            UUID(user_id)
        )

    return _response.ok(schemas.PurgeJobRead(**job).model_dump())


@router.get("/retention-policy/purge-jobs", status_code=200)
async def list_purge_jobs_route(
    request: Request,
    org_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List purge jobs for org."""
    pool = request.app.state.pool
    org_uuid = UUID(org_id)

    async with pool.acquire() as conn:
        policy = await conn.fetchrow(
            "SELECT policy_id FROM 04_audit.fct_audit_retention_policies WHERE org_id = $1",
            org_uuid
        )
        if not policy:
            raise _errors.HTTPException(404, "Retention policy not found")

    jobs, total = await service.list_purge_jobs(
        pool,
        policy["policy_id"],
        limit=limit,
        offset=offset,
    )

    return _response.paginated(
        [schemas.PurgeJobRead(**j).model_dump() for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )
