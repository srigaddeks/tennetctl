"""IAM applications routes — CRUD, product links, tokens, resolve-access.

POST   /v1/applications                                    (201) create
GET    /v1/applications                                    list (?category_id=&limit=&offset=)
GET    /v1/applications/{id}                               get one
PATCH  /v1/applications/{id}                               update
DELETE /v1/applications/{id}                               (204) soft-delete

GET    /v1/applications/{id}/products                      list linked products
POST   /v1/applications/{id}/products                      (201) link product
DELETE /v1/applications/{id}/products/{product_id}         (204) unlink product

GET    /v1/applications/{id}/tokens                        list tokens
POST   /v1/applications/{id}/tokens                        (201) issue token
POST   /v1/applications/{id}/tokens/{token_id}/rotate      (201) rotate token
DELETE /v1/applications/{id}/tokens/{token_id}             (204) revoke token

POST   /v1/applications/{application_code}/resolve-access  resolve user access
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Depends, Header, Query

_db = importlib.import_module("04_backend.01_core.db")
_service = importlib.import_module("04_backend.02_features.iam.applications.service")
_resp = importlib.import_module("04_backend.01_core.response")
_auth = importlib.import_module("04_backend.01_core.auth")
_schemas = importlib.import_module("04_backend.02_features.iam.applications.schemas")

router = APIRouter(tags=["applications"])


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.post("/v1/applications", status_code=201)
async def create_application(
    body: _schemas.CreateApplicationRequest,  # type: ignore[name-defined]
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Create a new platform application."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.create_application(
            conn,
            code=body.code,
            name=body.name,
            category_id=body.category_id,
            description=body.description,
            slug=body.slug,
            icon_url=body.icon_url,
            redirect_uris=body.redirect_uris,
            owner_user_id=body.owner_user_id,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )
    return _resp.ok(result)


@router.get("/v1/applications")
async def list_applications(
    category_id: int | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """List applications with optional filtering."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_applications(
            conn,
            limit=limit,
            offset=offset,
            category_id=category_id,
        )
    return _resp.ok(result)


@router.get("/v1/applications/{application_id}")
async def get_application(
    application_id: str,
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Get a single application by ID."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.get_application(conn, application_id)
    return _resp.ok(result)


@router.patch("/v1/applications/{application_id}")
async def update_application(
    application_id: str,
    body: _schemas.UpdateApplicationRequest,  # type: ignore[name-defined]
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Update an application."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.update_application(
            conn,
            application_id,
            name=body.name,
            is_active=body.is_active,
            description=body.description,
            slug=body.slug,
            icon_url=body.icon_url,
            redirect_uris=body.redirect_uris,
            owner_user_id=body.owner_user_id,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )
    return _resp.ok(result)


@router.delete("/v1/applications/{application_id}", status_code=204)
async def delete_application(
    application_id: str,
    token: dict = Depends(_auth.require_auth),
) -> None:
    """Soft-delete an application."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        await _service.delete_application(
            conn,
            application_id,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )


# ---------------------------------------------------------------------------
# Product links
# ---------------------------------------------------------------------------

@router.get("/v1/applications/{application_id}/products")
async def list_linked_products(
    application_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """List products linked to an application."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_linked_products(
            conn, application_id, limit=limit, offset=offset
        )
    return _resp.ok(result)


@router.post("/v1/applications/{application_id}/products", status_code=201)
async def link_product(
    application_id: str,
    body: _schemas.LinkApplicationProductRequest,  # type: ignore[name-defined]
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Link a product to an application."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.link_product(
            conn,
            application_id,
            body.product_id,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )
    return _resp.ok(result)


@router.delete(
    "/v1/applications/{application_id}/products/{product_id}", status_code=204
)
async def unlink_product(
    application_id: str,
    product_id: str,
    token: dict = Depends(_auth.require_auth),
) -> None:
    """Unlink a product from an application."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        await _service.unlink_product(
            conn,
            application_id,
            product_id,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )


# ---------------------------------------------------------------------------
# Token management
# ---------------------------------------------------------------------------

@router.get("/v1/applications/{application_id}/tokens")
async def list_tokens(
    application_id: str,
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """List tokens for an application (no raw token values)."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_tokens(conn, application_id)
    return _resp.ok(result)


@router.post("/v1/applications/{application_id}/tokens", status_code=201)
async def issue_token(
    application_id: str,
    body: _schemas.CreateApplicationTokenRequest,  # type: ignore[name-defined]
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Issue a new application token. Raw token is returned ONCE."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.issue_token(
            conn,
            application_id,
            name=body.name,
            expires_at=body.expires_at,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )
    return _resp.ok(result)


@router.post(
    "/v1/applications/{application_id}/tokens/{token_id}/rotate", status_code=201
)
async def rotate_token(
    application_id: str,
    token_id: str,
    body: _schemas.RotateApplicationTokenRequest,  # type: ignore[name-defined]
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Rotate an application token. Old token is revoked; new raw token returned once."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.rotate_token(
            conn,
            application_id,
            token_id,
            name=body.name,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )
    return _resp.ok(result)


@router.delete(
    "/v1/applications/{application_id}/tokens/{token_id}", status_code=204
)
async def revoke_token(
    application_id: str,
    token_id: str,
    token: dict = Depends(_auth.require_auth),
) -> None:
    """Revoke an application token."""
    actor_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        await _service.revoke_token(
            conn,
            application_id,
            token_id,
            actor_id=actor_id,
            session_id=session_id,
            org_id_audit=org_id,
            workspace_id_audit=workspace_id,
        )


# ---------------------------------------------------------------------------
# Resolve-access
# ---------------------------------------------------------------------------

@router.post("/v1/applications/{application_code}/resolve-access")
async def resolve_access(
    application_code: str,
    body: _schemas.ResolveAccessRequest,  # type: ignore[name-defined]
    x_application_token: str = Header(..., alias="X-Application-Token"),
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Resolve a user's full access context within an application.

    The caller must supply a valid application token in X-Application-Token
    and a valid user JWT in Authorization: Bearer. Returns a JSON blob
    containing roles, groups, permissions, and evaluated products/features/flags.
    """
    user_id: str = token["sub"]
    session_id: str = token.get("sid", "")
    org_id: str | None = token.get("oid")
    workspace_id: str | None = token.get("wid")

    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.resolve_access(
            conn,
            application_code=application_code,
            user_id=user_id,
            org_id=org_id,
            workspace_id=workspace_id,
            environment=body.environment,
            application_token=x_application_token,
            actor_id=user_id,
            session_id=session_id,
        )
    return _resp.ok(result)
