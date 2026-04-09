"""kprotect library routes — proxy to kbio policy catalog.

GET /v1/kprotect/library              — list predefined policies (paginated, filterable)
GET /v1/kprotect/library/{code}       — get one predefined policy by code
"""

from __future__ import annotations

import importlib

from fastapi import APIRouter, Query

_service = importlib.import_module("02_features.library.service")
_resp = importlib.import_module("01_core.response")

router = APIRouter(prefix="/v1/kprotect/library", tags=["library"])


@router.get("")
async def list_library_policies(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    category: str | None = Query(default=None),
    tag: str | None = Query(default=None),
) -> dict:
    result = await _service.list_policies(
        limit=limit,
        offset=offset,
        category=category,
        tag=tag,
    )
    return _resp.success_list_response(
        result["items"],
        total=result["total"],
        limit=result["limit"],
        offset=result["offset"],
    )


@router.get("/{code}")
async def get_library_policy(code: str) -> dict:
    policy = await _service.get_policy(code)
    return _resp.success_response(policy)
