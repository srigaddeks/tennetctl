"""
SolSocial authorization — delegated to tennetctl.

Identity comes from tennetctl via SessionProxyMiddleware. All RBAC
(roles, permissions, groups, feature flags) lives in tennetctl, scoped to the
'solsocial' application registered there (see the tennetctl applications
feature).

`require_scope(request, scope_code)` below is a placeholder that enforces
"user is authenticated and has a workspace" today and will call tennetctl's
scope-check endpoint once the applications feature lands. Route code stays
stable across that transition — only this module changes.
"""

from __future__ import annotations

from importlib import import_module

from fastapi import Request

_errors = import_module("apps.solsocial.backend.01_core.errors")
_middleware = import_module("apps.solsocial.backend.01_core.middleware")

APPLICATION_CODE = "solsocial"


async def require_scope(request: Request, scope_code: str) -> dict:
    """Require an authenticated user with a workspace.

    Once tennetctl exposes per-application scope checks, this will call
    `tennetctl.has_scope(token, application='solsocial', scope=scope_code)`.
    Today it only enforces identity + workspace presence.
    """
    identity = _middleware.require_user(request)
    if not identity["workspace_id"]:
        raise _errors.ForbiddenError("No workspace in session.")
    # TODO: call tennetctl /v1/applications/solsocial/scopes/check with scope_code
    _ = scope_code
    return identity
