"""kbio policies routes.

Public endpoints for the predefined policy catalog (no auth — kprotect reads these).
Also exposes a service manifest endpoint.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")

from .service import list_policies, get_policy

router = APIRouter(prefix="/v1/kbio", tags=["kbio-policies"])

# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------

_MANIFEST = {
    "service": "kbio",
    "version": "1.0.0",
    "score_types": [
        {"code": "behavioral_drift", "range": [0.0, 1.0]},
        {"code": "device_drift", "range": [0.0, 1.0]},
        {"code": "network_drift", "range": [0.0, 1.0]},
        {"code": "bot_score", "range": [0.0, 1.0]},
        {"code": "credential_drift", "range": [0.0, 1.0]},
        {"code": "composite_score", "range": [0.0, 1.0]},
    ],
    "policy_categories": [
        "fraud",
        "auth",
        "bot",
        "compliance",
        "risk",
        "trust",
        "session",
        "geo",
        "credential",
    ],
}


@router.get(
    "/manifest",
    summary="kbio service manifest",
)
async def get_manifest() -> dict:
    """Return the kbio service manifest.

    No authentication required — describes score types and policy categories
    so kprotect can self-configure.

    Returns:
        200: {"ok": true, "data": {...manifest...}}
    """
    return _resp.success_response(_MANIFEST)


# ---------------------------------------------------------------------------
# Policy catalog (public)
# ---------------------------------------------------------------------------


@router.get(
    "/policies",
    summary="List all predefined policies",
)
async def list_policies_endpoint(
    request: Request,
    limit: int = Query(default=50, ge=1, le=200, description="Page size"),
    offset: int = Query(default=0, ge=0, description="Page offset"),
    category: str | None = Query(default=None, description="Filter by category"),
    tag: str | None = Query(default=None, description="Filter by tag (substring match)"),
) -> dict:
    """Return a paginated list of active predefined policies.

    No authentication required — the policy catalog is public so kprotect
    can bootstrap itself without a service token.

    Returns:
        200: {"ok": true, "data": {"items": [...], "total": N, "limit": N, "offset": N}}
        422: invalid pagination params
    """
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            result = await list_policies(
                conn,
                limit=limit,
                offset=offset,
                category=category,
                tag=tag,
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_list_response(
        [item.model_dump() for item in result.items],
        total=result.total,
        limit=result.limit,
        offset=result.offset,
    )


@router.get(
    "/policies/{code}",
    summary="Get a predefined policy by code",
)
async def get_policy_endpoint(
    code: str,
    request: Request,
) -> dict:
    """Return a single predefined policy by its unique code.

    No authentication required.

    Returns:
        200: {"ok": true, "data": PredefinedPolicyData}
        404: policy not found or inactive
    """
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            policy = await get_policy(conn, code)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(policy.model_dump())
