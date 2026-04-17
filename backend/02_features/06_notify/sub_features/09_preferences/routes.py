"""FastAPI routes for notify.preferences."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_service: Any = import_module(
    "backend.02_features.06_notify.sub_features.09_preferences.service"
)
_schemas: Any = import_module(
    "backend.02_features.06_notify.sub_features.09_preferences.schemas"
)
_response: Any = import_module("backend.01_core.response")
_errors: Any = import_module("backend.01_core.errors")

router = APIRouter()

PreferencePatchBody = _schemas.PreferencePatchBody
PreferenceRow = _schemas.PreferenceRow


@router.get("/v1/notify/preferences", status_code=200)
async def list_preferences_route(request: Request) -> dict:
    """
    GET /v1/notify/preferences

    Returns all 16 (channel × category) combinations for the current user.
    Missing rows default to is_opted_in=True.

    Requires authentication.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    org_id = getattr(request.state, "org_id", None) or request.query_params.get("org_id")
    if not org_id:
        raise _errors.AppError("BAD_REQUEST", "org_id required.", 400)

    async with request.app.state.pool.acquire() as conn:
        prefs = await _service.list_preferences(conn, user_id=user_id, org_id=org_id)

    rows = [PreferenceRow(**p).model_dump() for p in prefs]
    return _response.success_response(rows)


@router.patch("/v1/notify/preferences", status_code=200)
async def patch_preferences_route(body: PreferencePatchBody, request: Request) -> dict:
    """
    PATCH /v1/notify/preferences

    Upsert one or more preference rows. Each item specifies channel_code,
    category_code, and is_opted_in. critical category is silently forced to True.

    Requires authentication.
    """
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "Authentication required.", 401)
    org_id = getattr(request.state, "org_id", None) or request.query_params.get("org_id")
    if not org_id:
        raise _errors.AppError("BAD_REQUEST", "org_id required.", 400)

    async with request.app.state.pool.acquire() as conn:
        updated = []
        for item in body.preferences:
            row = await _service.upsert_preference(
                conn,
                user_id=user_id,
                org_id=org_id,
                channel_code=item.channel_code,
                category_code=item.category_code,
                is_opted_in=item.is_opted_in,
                updated_by=user_id,
            )
            updated.append(PreferenceRow(**row).model_dump())

    return _response.success_response(updated)
