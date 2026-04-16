from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


_service_module = import_module("backend.03_auth_manage.service")
_errors_module = import_module("backend.01_core.errors")
_logging_module = import_module("backend.01_core.logging_utils")

AuthService = _service_module.AuthService
AuthenticationError = _errors_module.AuthenticationError
AuthorizationError = _errors_module.AuthorizationError
bind_actor_context = _logging_module.bind_actor_context
bind_session_context = _logging_module.bind_session_context
bind_impersonator_context = _logging_module.bind_impersonator_context

_bearer_scheme = HTTPBearer(auto_error=False)


def get_auth_service(request: Request) -> AuthService:
    return AuthService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )


def get_client_ip(request: Request) -> str | None:
    settings = request.app.state.settings
    if settings.trust_proxy_headers:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        forwarded_chain = [item.strip() for item in forwarded_for.split(",") if item.strip()]
        if forwarded_chain:
            client_index = max(0, len(forwarded_chain) - settings.trusted_proxy_depth - 1)
            return forwarded_chain[client_index]
        real_ip = request.headers.get("x-real-ip", "").strip()
        if real_ip:
            return real_ip
    return request.client.host if request.client else None


async def get_current_access_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    request: Request,
    service: Annotated[AuthService, Depends(get_auth_service)],
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthenticationError("Bearer token is required.")

    token = credentials.credentials

    if token.startswith("kctl_"):
        # API key authentication path
        client_ip = get_client_ip(request)
        claims = await service.authenticate_api_key(token, client_ip=client_ip)
        bind_actor_context(claims.subject)
        bind_session_context(claims.session_id)
        request.state.is_api_key = True
        request.state.api_key_id = claims.api_key_id
        return claims

    # JWT authentication path (existing)
    claims = service.decode_access_token(token)
    active_claims = await service.require_active_access_claims(claims)
    bind_actor_context(active_claims.subject)
    bind_session_context(active_claims.session_id)
    if active_claims.is_impersonation:
        bind_impersonator_context(active_claims.impersonator_id)
        request.state.is_impersonation = True
        request.state.impersonator_id = active_claims.impersonator_id
    return active_claims


async def require_not_impersonating(
    claims=Depends(get_current_access_claims),
):
    """Reject requests made during impersonation sessions."""
    if claims.is_impersonation:
        raise AuthorizationError("This action is not allowed during impersonation.")
    return claims


async def require_not_api_key(
    claims=Depends(get_current_access_claims),
):
    """Reject requests made with API key authentication."""
    if claims.is_api_key:
        raise AuthorizationError("This action is not allowed with API key authentication.")
    return claims
