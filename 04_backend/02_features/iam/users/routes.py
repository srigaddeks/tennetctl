"""IAM users routes.

POST  /v1/users        — self-registration (public)
GET   /v1/users        — list users
GET   /v1/users/{id}   — get user by ID
PATCH /v1/users/{id}   — update email or is_active
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Depends, Query, Request

_db = importlib.import_module("04_backend.01_core.db")
_service = importlib.import_module("04_backend.02_features.iam.users.service")
_signup = importlib.import_module("04_backend.02_features.iam.users.signup_service")
_resp = importlib.import_module("04_backend.01_core.response")
_auth = importlib.import_module("04_backend.01_core.auth")
_schemas = importlib.import_module("04_backend.02_features.iam.users.schemas")

router = APIRouter(prefix="/v1/users", tags=["users"])


class SignupRequest(_schemas.BaseModel):  # type: ignore[name-defined]
    username: str
    password: str
    email: str | None = None
    display_name: str | None = None
    account_type: str = "personal"
    org_name: str | None = None
    default_workspace_name: str = "kbio"


@router.post("", status_code=201)
async def signup_user(body: SignupRequest, request: Request) -> dict:
    """Public self-registration — creates user, org, workspace, and returns tokens."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _signup.signup(
            conn,
            username=body.username,
            password=body.password,
            email=body.email,
            display_name=body.display_name,
            account_type=body.account_type,
            org_name=body.org_name,
            default_workspace_name=body.default_workspace_name,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get("user-agent"),
        )
    return _resp.ok(result)


@router.get("")
async def list_users(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    _token: dict = Depends(_auth.require_auth),
) -> dict:
    """List users (authenticated)."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        result = await _service.list_users(conn, limit=limit, offset=offset)
    return _resp.ok(result)


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    _token: dict = Depends(_auth.require_auth),
) -> dict:
    """Get a single user by ID."""
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        user = await _service.get_user(conn, user_id)
    return _resp.ok(user)


@router.patch("/{user_id}")
async def patch_user(
    user_id: str,
    body: _schemas.PatchUserRequest,  # type: ignore[name-defined]
    token: dict = Depends(_auth.require_auth),
) -> dict:
    """Update email or active status of a user."""
    actor_id: str = token["sub"]
    pool = _db.get_pool()
    async with pool.acquire() as conn:
        user = await _service.patch_user(
            conn,
            user_id,
            email=body.email,
            is_active=body.is_active,
            actor_id=actor_id,
        )
    return _resp.ok(user)
