"""Routes for audit.retention_policy.

Per FIX-19: every endpoint enforces session-bound org scoping. The org_id
query param must match the caller's session org (or the caller must be a
member of the requested org via authz_helpers).
"""

from importlib import import_module
from uuid import UUID

from fastapi import APIRouter, Request

_response = import_module("backend.01_core.response")
_errors = import_module("backend.01_core.errors")
_authz = import_module(
    "backend.02_features.03_iam.sub_features.29_authz_gates.authz_helpers"
)

from . import schemas, service


router = APIRouter(prefix="/v1/audit", tags=["audit.retention"])


def _require_user(request: Request) -> str:
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.UnauthorizedError("Authentication required.")
    return user_id


async def _require_org_membership(conn, user_id: str, org_id: str) -> None:
    """Reject if the caller is not a member of the requested org."""
    await _authz.require_org_member_or_raise(conn, user_id, org_id)


async def _fetch_policy_id(conn, org_id: UUID) -> UUID:
    row = await conn.fetchrow(
        'SELECT id FROM "04_audit"."10_fct_audit_retention_policies" '
        'WHERE org_id = $1 AND deleted_at IS NULL',
        str(org_id),
    )
    if not row:
        raise _errors.NotFoundError("Retention policy not found")
    return UUID(str(row["id"]))


@router.get("/retention-policy", status_code=200)
async def get_retention_policy_route(request: Request, org_id: str) -> dict:
    """Retrieve org's audit retention policy."""
    user_id = _require_user(request)
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        await _require_org_membership(conn, user_id, org_id)
        policy = await service.get_retention_policy(conn, UUID(org_id))
    if not policy:
        raise _errors.NotFoundError("Retention policy not found")
    return _response.success_response(policy)


@router.patch("/retention-policy", status_code=200)
async def update_retention_policy_route(
    request: Request,
    org_id: str,
    body: schemas.RetentionPolicyUpdate,
) -> dict:
    """Update retention policy (org member only)."""
    user_id = _require_user(request)
    pool = request.app.state.pool
    org_uuid = UUID(org_id)

    async with pool.acquire() as conn:
        await _require_org_membership(conn, user_id, org_id)
        policy_id = await _fetch_policy_id(conn, org_uuid)
        updated = await service.update_retention_policy(
            conn,
            policy_id,
            retention_days=body.retention_days,
            auto_purge_enabled=body.auto_purge_enabled,
            exclude_critical=body.exclude_critical,
            status=body.status,
        )

    return _response.success_response(
        schemas.RetentionPolicyRead(**updated).model_dump(),
    )


@router.post("/retention-policy/purge", status_code=202)
async def trigger_purge_route(request: Request, org_id: str) -> dict:
    """Manually trigger a purge job (org member only)."""
    user_id = _require_user(request)
    pool = request.app.state.pool
    org_uuid = UUID(org_id)

    async with pool.acquire() as conn:
        await _require_org_membership(conn, user_id, org_id)
        policy_id = await _fetch_policy_id(conn, org_uuid)
        job = await service.execute_purge_job(conn, policy_id, UUID(user_id))

    return _response.success_response(
        schemas.PurgeJobRead(**job).model_dump(),
        status_code=202,
    )


@router.get("/retention-policy/purge-jobs", status_code=200)
async def list_purge_jobs_route(
    request: Request,
    org_id: str,
    limit: int = 50,
    offset: int = 0,
) -> dict:
    """List purge jobs for the caller's org."""
    user_id = _require_user(request)
    pool = request.app.state.pool
    org_uuid = UUID(org_id)

    async with pool.acquire() as conn:
        await _require_org_membership(conn, user_id, org_id)
        policy_id = await _fetch_policy_id(conn, org_uuid)
        jobs, total = await service.list_purge_jobs(
            conn, policy_id, limit=limit, offset=offset,
        )

    return _response.success_list_response(
        [schemas.PurgeJobRead(**j).model_dump() for j in jobs],
        total=total,
        limit=limit,
        offset=offset,
    )
