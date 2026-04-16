"""
FastAPI middleware — error handling and request ID.

Registers:
  - AppError exception handler → standard error envelope
  - Request ID middleware → X-Request-ID on every response
"""

from __future__ import annotations

from importlib import import_module

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

_errors = import_module("backend.01_core.errors")
_response = import_module("backend.01_core.response")
_id = import_module("backend.01_core.id")


async def _app_error_handler(_request: Request, exc: _errors.AppError) -> JSONResponse:
    """Convert AppError into standard error envelope response."""
    return _response.error_response(exc.code, exc.message, exc.status_code)


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Add X-Request-ID header to every response."""

    async def dispatch(self, request: Request, call_next):
        request_id = _id.uuid7()
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


def register_middleware(app: FastAPI) -> None:
    """Register all middleware and exception handlers on the app."""
    app.add_exception_handler(_errors.AppError, _app_error_handler)
    app.add_middleware(RequestIdMiddleware)
