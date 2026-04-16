"""
Response envelope helpers.

Every API response uses the standard envelope:
  {"ok": true, "data": {...}}
  {"ok": false, "error": {"code": "...", "message": "..."}}
"""

from __future__ import annotations

from typing import Any

from fastapi.responses import JSONResponse


def success(data: Any) -> dict:
    """Build success envelope dict."""
    return {"ok": True, "data": data}


def error(code: str, message: str) -> dict:
    """Build error envelope dict."""
    return {"ok": False, "error": {"code": code, "message": message}}


def paginated(data: list, total: int, limit: int, offset: int) -> dict:
    """Build success envelope with pagination metadata."""
    return {
        "ok": True,
        "data": data,
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
        },
    }


def success_response(data: Any, status_code: int = 200) -> JSONResponse:
    """Return a JSONResponse with success envelope."""
    return JSONResponse(content=success(data), status_code=status_code)


def error_response(code: str, message: str, status_code: int = 500) -> JSONResponse:
    """Return a JSONResponse with error envelope."""
    return JSONResponse(content=error(code, message), status_code=status_code)
