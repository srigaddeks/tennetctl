from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request, status
from fastapi.responses import Response

from ..dependencies import get_client_ip, get_current_access_claims
from .dependencies import get_admin_service
from .schemas import (
    AuditEventListResponse,
    FeatureEvaluationResponse,
    ImpersonationHistoryResponse,
    SessionListResponse,
    UserAuditEventListResponse,
    UserDetailResponse,
    UserDisableResponse,
    UserListResponse,
)
from .service import AdminService

_telemetry_module = import_module("backend.01_core.telemetry")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter

router = InstrumentedAPIRouter(prefix="/api/v1/am/admin", tags=["admin"])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query(max_length=200)] = None,
    is_active: Annotated[bool | None, Query()] = None,
    is_disabled: Annotated[bool | None, Query()] = None,
    account_status: Annotated[str | None, Query(max_length=100)] = None,
    org_id: Annotated[str | None, Query(max_length=36)] = None,
    group_id: Annotated[str | None, Query(max_length=36)] = None,
    user_category: Annotated[str | None, Query(max_length=50)] = None,
) -> UserListResponse:
    return await service.list_users(
        actor_id=claims.subject,
        tenant_key=claims.tenant_key,
        limit=limit,
        offset=offset,
        search=search,
        is_active=is_active,
        is_disabled=is_disabled,
        account_status=account_status,
        org_id=org_id,
        group_id=group_id,
        user_category=user_category,
    )


@router.get("/users/{user_id}", response_model=UserDetailResponse)
async def get_user_detail(
    user_id: str,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
) -> UserDetailResponse:
    return await service.get_user_detail(
        actor_id=claims.subject,
        user_id=user_id,
    )


@router.patch("/users/{user_id}/disable", response_model=UserDisableResponse)
async def disable_user(
    user_id: str,
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> UserDisableResponse:
    return await service.disable_user(
        actor_id=claims.subject,
        user_id=user_id,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.patch("/users/{user_id}/enable", response_model=UserDisableResponse)
async def enable_user(
    user_id: str,
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> UserDisableResponse:
    return await service.enable_user(
        actor_id=claims.subject,
        user_id=user_id,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )


@router.get("/users/{user_id}/audit", response_model=UserAuditEventListResponse)
async def get_user_audit_events(
    user_id: str,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> UserAuditEventListResponse:
    return await service.get_user_audit_events(
        actor_id=claims.subject,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )


@router.get("/users/{user_id}/sessions", response_model=SessionListResponse)
async def list_user_sessions(
    user_id: str,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    include_revoked: Annotated[bool, Query()] = False,
) -> SessionListResponse:
    return await service.list_user_sessions(
        actor_id=claims.subject,
        user_id=user_id,
        include_revoked=include_revoked,
    )


@router.delete("/users/{user_id}/sessions/{session_id}", status_code=204)
async def revoke_user_session(
    user_id: str,
    session_id: str,
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> Response:
    await service.revoke_user_session(
        actor_id=claims.subject,
        user_id=user_id,
        session_id=session_id,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return Response(status_code=204)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: str,
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    client_ip: Annotated[str | None, Depends(get_client_ip)] = None,
) -> Response:
    await service.delete_user(
        actor_id=claims.subject,
        user_id=user_id,
        client_ip=client_ip,
        request_id=getattr(request.state, "request_id", None),
    )
    return Response(status_code=204)


@router.get("/audit", response_model=AuditEventListResponse)
async def list_audit_events(
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    entity_type: Annotated[str | None, Query(max_length=100)] = None,
    entity_id: Annotated[str | None, Query(max_length=100)] = None,
    actor_id: Annotated[str | None, Query(max_length=100)] = None,
    event_type: Annotated[str | None, Query(max_length=100)] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> AuditEventListResponse:
    return await service.list_audit_events(
        actor_id=claims.subject,
        tenant_key=claims.tenant_key,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id_filter=actor_id,
        event_type=event_type,
        limit=limit,
        offset=offset,
    )


@router.get("/impersonation/history", response_model=ImpersonationHistoryResponse)
async def list_impersonation_history(
    request: Request,
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ImpersonationHistoryResponse:
    return await service.list_impersonation_history(
        actor_id=claims.subject,
        tenant_key=claims.tenant_key,
        limit=limit,
        offset=offset,
    )


@router.get("/me/features", response_model=FeatureEvaluationResponse)
async def evaluate_features(
    service: Annotated[AdminService, Depends(get_admin_service)],
    claims=Depends(get_current_access_claims),
) -> FeatureEvaluationResponse:
    return await service.evaluate_features(user_id=claims.subject)
