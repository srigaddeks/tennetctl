"""kbio signal catalog service."""
from __future__ import annotations
import importlib
from .repository import list_signals as _repo_list, get_signal_by_code
from .schemas import SignalDefResponse, SignalListResponse

_errors = importlib.import_module("01_core.errors")


async def list_signals(
    *, limit: int = 50, offset: int = 0,
    category: str | None = None, tag: str | None = None,
) -> SignalListResponse:
    if not (1 <= limit <= 200):
        raise _errors.AppError("VALIDATION_ERROR", "limit must be 1-200.", 422)
    items, total = _repo_list(limit=limit, offset=offset, category=category, tag=tag)
    return SignalListResponse(
        items=[SignalDefResponse(**s) for s in items],
        total=total, limit=limit, offset=offset,
    )


async def get_signal(code: str) -> SignalDefResponse:
    sig = get_signal_by_code(code)
    if sig is None:
        raise _errors.AppError("NOT_FOUND", f"Signal '{code}' not found.", 404)
    return SignalDefResponse(**sig)
