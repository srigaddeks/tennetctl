from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_invitation_service
from .schemas import (
    AcceptInvitationRequest,
    BulkCreateInvitationRequest,
    BulkCreateInvitationResponse,
    CreateInvitationRequest,
    DeclineInvitationRequest,
    InvitationAcceptedResponse,
    InvitationCreatedResponse,
    InvitationListResponse,
    InvitationPreviewResponse,
    InvitationResponse,
    InvitationStatsResponse,
)
from .service import InvitationService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/am", tags=["invitations"])


@router.post("/invitations", response_model=InvitationCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    request: CreateInvitationRequest,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> InvitationCreatedResponse:
    return await service.create_invitation(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=request,
    )


@router.get("/invitations", response_model=InvitationListResponse)
async def list_invitations(
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
    scope: str | None = Query(None),
    org_id: str | None = Query(None),
    workspace_id: str | None = Query(None),
    invitation_status: str | None = Query(None, alias="status"),
    email: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> InvitationListResponse:
    return await service.list_invitations(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        scope=scope,
        org_id=org_id,
        workspace_id=workspace_id,
        status=invitation_status,
        email=email,
        page=page,
        page_size=page_size,
    )


@router.get("/invitations/stats", response_model=InvitationStatsResponse)
async def get_invitation_stats(
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> InvitationStatsResponse:
    return await service.get_stats(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
    )


@router.post("/invitations/bulk", response_model=BulkCreateInvitationResponse, status_code=status.HTTP_201_CREATED)
async def bulk_create_invitations(
    request: BulkCreateInvitationRequest,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> BulkCreateInvitationResponse:
    return await service.bulk_create_invitations(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=request,
    )


@router.get("/invitations/preview", response_model=InvitationPreviewResponse | None)
async def preview_invitation(
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    token: str = Query(..., min_length=10),
) -> InvitationPreviewResponse | None:
    """Return invite context (org, workspace, GRC role) without consuming the token. No auth required."""
    return await service.preview_invitation(invite_token=token)


@router.post("/invitations/accept", response_model=InvitationAcceptedResponse)
async def accept_invitation(
    request: AcceptInvitationRequest,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> InvitationAcceptedResponse:
    """Accept a pending invitation. Caller must be logged in as the invited email address."""
    return await service.accept_invitation(request=request, caller_user_id=claims.subject)


@router.post("/invitations/accept-public", response_model=InvitationAcceptedResponse)
async def accept_invitation_public(
    request: AcceptInvitationRequest,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> InvitationAcceptedResponse:
    """Accept a pending invitation using only the token (no auth required).

    Used when the invited email already has an account — token possession is the
    authorization. Returns 404 with detail "user_not_found" if no matching user exists,
    so the caller can route to /register instead.
    """
    return await service.accept_invitation_by_token(invite_token=request.invite_token)


@router.post("/invitations/decline", response_model=InvitationResponse)
async def decline_invitation(
    request: DeclineInvitationRequest,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
) -> InvitationResponse:
    return await service.decline_invitation(request=request)


@router.get("/invitations/{invitation_id}", response_model=InvitationResponse)
async def get_invitation(
    invitation_id: str,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> InvitationResponse:
    return await service.get_invitation(
        user_id=claims.subject,
        invitation_id=invitation_id,
    )


@router.post("/invitations/{invitation_id}/resend", response_model=InvitationCreatedResponse)
async def resend_invitation(
    invitation_id: str,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> InvitationCreatedResponse:
    return await service.resend_invitation(
        user_id=claims.subject,
        invitation_id=invitation_id,
        tenant_key=claims.tenant_key,
    )


@router.patch("/invitations/{invitation_id}/revoke", response_model=InvitationResponse)
async def revoke_invitation(
    invitation_id: str,
    service: Annotated[InvitationService, Depends(get_invitation_service)],
    claims=Depends(get_current_access_claims),
) -> InvitationResponse:
    return await service.revoke_invitation(
        user_id=claims.subject,
        invitation_id=invitation_id,
        tenant_key=claims.tenant_key,
    )
