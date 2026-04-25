"""Response envelope helpers."""

from __future__ import annotations

from typing import Any


def success(data: Any) -> dict:
    return {"ok": True, "data": data}


def error(code: str, message: str) -> dict:
    return {"ok": False, "error": {"code": code, "message": message}}
