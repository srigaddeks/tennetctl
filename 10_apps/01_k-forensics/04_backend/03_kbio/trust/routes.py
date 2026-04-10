"""kbio trust routes.

Internal endpoints for managing trusted entities.
All endpoints require the X-Internal-Service-Token header.
"""
from __future__ import annotations

import importlib

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

_db = importlib.import_module("01_core.db")
_resp = importlib.import_module("01_core.response")
_errors = importlib.import_module("01_core.errors")
_auth = importlib.import_module("01_core.api_key_auth")

from .schemas import CreateTrustedEntityRequest
from .service import (
    create_trusted_entity_svc,
    get_trust_profile,
    revoke_trusted_entity,
)

router = APIRouter(prefix="/v1/internal", tags=["kbio-trust"])


@router.get(
    "/trust/{user_hash}",
    summary="Get full trust profile for a user",
)
async def get_trust_profile_endpoint(
    user_hash: str,
    request: Request,
) -> dict:
    """Return the complete trust profile for the given user_hash.

    The profile is grouped by entity type: trusted_devices, trusted_ips,
    trusted_locations, and trusted_networks.  An empty profile is valid.

    Fetched from Valkey cache (TTL 900 s) with DB fallback.

    Headers:
        X-Internal-Service-Token: shared service secret

    Returns:
        200: {"ok": true, "data": TrustProfileData}
        401: missing/invalid token
    """
    await _auth.validate_api_key(request)

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            profile = await get_trust_profile(conn, user_hash)
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(profile.model_dump())


@router.post(
    "/trust",
    status_code=201,
    summary="Create a new trusted entity",
)
async def create_trusted_entity_endpoint(
    body: CreateTrustedEntityRequest,
    request: Request,
) -> dict:
    """Add a new entity to the user's trust list.

    Valid entity_type values: device, ip_address, location, network.

    The actor_id is taken from the X-Actor-ID header if provided,
    otherwise defaults to the string literal 'service'.

    Headers:
        X-Internal-Service-Token: shared service secret
        X-Actor-ID (optional): who is creating the trusted entity

    Body:
        user_hash: str
        entity_type: str
        entity_value: str
        trust_reason: str
        expires_at: str | null

    Returns:
        201: {"ok": true, "data": TrustedEntityData}
        401: missing/invalid token
        422: unknown entity_type
        500: unexpected failure
    """
    await _auth.validate_api_key(request)

    actor_id = request.headers.get("X-Actor-ID", "service")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            entity = await create_trusted_entity_svc(
                conn,
                user_hash=body.user_hash,
                entity_type=body.entity_type,
                entity_value=body.entity_value,
                trust_reason=body.trust_reason,
                expires_at=body.expires_at,
                actor_id=actor_id,
            )
        except _errors.AppError as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )

    return _resp.success_response(entity.model_dump())


@router.delete(
    "/trust/{entity_id}",
    status_code=204,
    summary="Revoke a trusted entity",
)
async def revoke_trusted_entity_endpoint(
    entity_id: str,
    request: Request,
) -> None:
    """Soft-delete a trusted entity by setting deleted_at.

    Invalidates the user's Valkey trust cache so subsequent reads reflect
    the change immediately.

    The actor_id is taken from the X-Actor-ID header if provided,
    otherwise defaults to the string literal 'service'.

    Headers:
        X-Internal-Service-Token: shared service secret
        X-Actor-ID (optional): who is revoking the entity

    Returns:
        204: entity deleted (no body)
        401: missing/invalid token
        404: entity not found
    """
    await _auth.validate_api_key(request)

    actor_id = request.headers.get("X-Actor-ID", "service")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        try:
            await revoke_trusted_entity(conn, entity_id, actor_id=actor_id)
        except _errors.AppError as exc:
            # 204 routes cannot return a body, so we must re-raise for the
            # framework to handle, or return a JSONResponse directly.
            return JSONResponse(
                status_code=exc.status_code,
                content={"ok": False, "error": {"code": exc.code, "message": exc.message}},
            )
