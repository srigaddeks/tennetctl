"""POST /v1/media/upload — upload an image/video for a post."""

from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, File, Request, UploadFile

_authz = import_module("apps.solsocial.backend.01_core.authz")
_response = import_module("apps.solsocial.backend.01_core.response")
_errors = import_module("apps.solsocial.backend.01_core.errors")
_storage = import_module("apps.solsocial.backend.02_features.70_media.storage")

router = APIRouter(tags=["media"])

_MAX_BYTES = 20 * 1024 * 1024  # 20 MB


@router.post("/v1/media/upload")
async def upload_media(request: Request, file: UploadFile = File(...)) -> Any:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        identity = await _authz.require_scope(request, "posts.create")

    data = await file.read()
    if len(data) > _MAX_BYTES:
        raise _errors.ValidationError(
            f"File too large ({len(data)} bytes). Limit is 20 MB."
        )
    if len(data) == 0:
        raise _errors.ValidationError("File is empty.")

    content_type = file.content_type or "application/octet-stream"
    if not (content_type.startswith("image/") or content_type.startswith("video/")):
        raise _errors.ValidationError(
            f"Unsupported content type: {content_type}. Images and videos only."
        )

    result = _storage.upload(
        workspace_id=identity["workspace_id"],
        data=data, content_type=content_type,
        filename=file.filename or "file",
    )
    return _response.success(result)
