"""kprotect response envelope helpers."""

from __future__ import annotations

from typing import Any


def success_response(data: Any) -> dict:
    return {"ok": True, "data": data}


def success_list_response(
    items: list, *, total: int, limit: int, offset: int
) -> dict:
    return {
        "ok": True,
        "data": {
            "items": items,
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }
