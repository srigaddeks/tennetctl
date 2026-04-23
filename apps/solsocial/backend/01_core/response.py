"""Response envelope — {ok: true, data: ...} / {ok: false, error: {...}}."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any) -> dict:
    return {"ok": True, "data": data}


def error(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=success(data), status_code=status_code)


def error_response(code: str, message: str, status_code: int = 500) -> JSONResponse:
    return JSONResponse(content=error(code, message), status_code=status_code)


def success_list_response(
    items: list,
    *,
    total: int | None = None,
    limit: int | None = None,
    offset: int | None = None,
) -> dict:
    body: dict = {
        "ok": True,
        "data": {"items": items, "total": total if total is not None else len(items)},
    }
    if limit is not None and offset is not None:
        body["data"]["pagination"] = {
            "limit": limit, "offset": offset, "total": body["data"]["total"],
        }
    return body
