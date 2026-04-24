"""Response envelope helpers — {ok: true, data} / {ok: false, error}."""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any) -> dict:
    return {"ok": True, "data": data}


def error(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}


def ok_response(data: Any, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=ok(data), status_code=status_code)


def error_response(code: str, message: str, status_code: int = 500) -> JSONResponse:
    return JSONResponse(content=error(code, message), status_code=status_code)
