"""kbio API key routes.

CRUD endpoints for managing API keys. Dashboard-facing (not SDK-facing).
All endpoints require API key or service token auth.
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_service = importlib.import_module("03_kbio.api_keys.service")
_schemas = importlib.import_module("03_kbio.api_keys.schemas")
_auth = importlib.import_module("01_core.api_key_auth")
_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")

router = APIRouter(prefix="/v1/api-keys", tags=["kbio-api-keys"])


@router.get("")
async def list_api_keys(request: Request) -> dict:
    """List API keys for the authenticated org.

    Returns:
        200: {"ok": true, "data": {"items": [...], "total": N, "limit": N, "offset": N}}
        401: missing/invalid auth
    """
    auth = await _auth.validate_api_key(request)
    org_id = request.query_params.get("org_id", auth["org_id"])
    limit = int(request.query_params.get("limit", "50"))
    offset = int(request.query_params.get("offset", "0"))

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        items, total = await _service.list_api_keys(conn, org_id=org_id, limit=limit, offset=offset)

    return _resp.success_list_response(items, total=total, limit=limit, offset=offset)


@router.post("", status_code=201)
async def create_api_key(request: Request) -> dict:
    """Create a new API key. Returns the raw key (shown once).

    Returns:
        201: {"ok": true, "data": {"id": ..., "raw_key": ..., "key_prefix": ..., "name": ...}}
        401: missing/invalid auth
    """
    auth = await _auth.validate_api_key(request)
    body = await request.json()
    req = _schemas.CreateApiKeyRequest(**body)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.create_api_key(
            conn,
            org_id=req.org_id,
            workspace_id=req.workspace_id,
            name=req.name,
            description=req.description,
            permissions=req.permissions,
            rate_limit=req.rate_limit,
            expires_at=req.expires_at,
            actor_id=auth.get("key_id", "system"),
        )

    return _resp.success_response(result)


@router.get("/{key_id}")
async def get_api_key(request: Request, key_id: str) -> dict:
    """Get a single API key by ID.

    Returns:
        200: {"ok": true, "data": {...}}
        401: missing/invalid auth
        404: not found
    """
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.get_api_key(conn, key_id)

    return _resp.success_response(result)


@router.patch("/{key_id}")
async def update_api_key(request: Request, key_id: str) -> dict:
    """Update API key attributes (name, description, rate_limit, permissions).

    Returns:
        200: {"ok": true, "data": {...}}
        401: missing/invalid auth
        404: not found
    """
    auth = await _auth.validate_api_key(request)
    body = await request.json()
    req = _schemas.UpdateApiKeyRequest(**body)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.update_api_key(
            conn, key_id,
            attrs=req.model_dump(exclude_none=True),
            actor_id=auth.get("key_id", "system"),
        )

    return _resp.success_response(result)


@router.delete("/{key_id}", status_code=204)
async def delete_api_key(request: Request, key_id: str) -> JSONResponse:
    """Soft-delete an API key.

    Returns:
        204: deleted
        401: missing/invalid auth
        404: not found
    """
    auth = await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        await _service.delete_api_key(conn, key_id, actor_id=auth.get("key_id", "system"))

    return JSONResponse(status_code=204, content=None)


@router.post("/{key_id}/revoke")
async def revoke_api_key(request: Request, key_id: str) -> dict:
    """Revoke an API key (cannot be undone).

    Returns:
        200: {"ok": true, "data": {"revoked": true}}
        401: missing/invalid auth
        404: not found
        409: already revoked
    """
    auth = await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        await _service.revoke_api_key(conn, key_id, actor_id=auth.get("key_id", "system"))

    return _resp.success_response({"revoked": True})
