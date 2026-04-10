"""kbio threat type catalog service."""
from __future__ import annotations

import importlib

from .repository import get_threat_type_by_code
from .repository import list_threat_types as _repo_list
from .schemas import ThreatTypeDefResponse, ThreatTypeListResponse

_errors = importlib.import_module("01_core.errors")


async def list_threat_types(
    *,
    limit: int = 50,
    offset: int = 0,
    category: str | None = None,
    tag: str | None = None,
) -> ThreatTypeListResponse:
    if not (1 <= limit <= 200):
        raise _errors.AppError("VALIDATION_ERROR", "limit must be 1-200.", 422)
    items, total = _repo_list(
        limit=limit, offset=offset, category=category, tag=tag,
    )
    return ThreatTypeListResponse(
        items=[ThreatTypeDefResponse(**t) for t in items],
        total=total,
        limit=limit,
        offset=offset,
    )


async def get_threat_type(code: str) -> ThreatTypeDefResponse:
    t = get_threat_type_by_code(code)
    if t is None:
        raise _errors.AppError(
            "NOT_FOUND", f"Threat type '{code}' not found.", 404,
        )
    return ThreatTypeDefResponse(**t)
