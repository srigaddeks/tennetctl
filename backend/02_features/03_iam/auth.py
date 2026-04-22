"""Compat module: ``require_user`` / ``require_org`` helpers.

Plain functions that take a ``starlette.requests.Request`` directly.
Callers either invoke them inline inside a route handler that already
takes ``request: Request`` as a top-level parameter, or wrap them with
a local ``Depends`` that returns the Request. Avoiding the indirection
of a FastAPI sub-dep here dodges a version-sensitive quirk where
``request: Request`` on a sub-dep sometimes slips through as an
unintended query parameter.
"""

from importlib import import_module

from starlette.requests import Request

_errors = import_module("backend.01_core.errors")


def require_user(request: Request) -> str:
    state = request.state
    user_id = getattr(state, "user_id", None) or request.headers.get("x-user-id")
    if not user_id:
        raise _errors.AppError("UNAUTHORIZED", "user_id required", 401)
    return user_id


def require_org(request: Request) -> str:
    state = request.state
    org_id = getattr(state, "org_id", None) or request.headers.get("x-org-id")
    if not org_id:
        raise _errors.AppError("UNAUTHORIZED", "org_id required", 401)
    return org_id
