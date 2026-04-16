"""FastAPI router for feedback & support tickets (prefix /api/v1/fb)."""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, status

from .dependencies import get_ticket_service
from .schemas import (
    AdminUpdateRequest,
    AssignTicketRequest,
    CreateTicketRequest,
    TicketDimensionsResponse,
    TicketEventsResponse,
    TicketListResponse,
    TicketResponse,
    UpdateTicketRequest,
    UpdateTicketStatusRequest,
)
from .service import TicketService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/fb", tags=["feedback"])


# ── Dimensions (no permission needed, just auth) ─────────────────────────────

@router.get("/dimensions", response_model=TicketDimensionsResponse)
async def list_dimensions(
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketDimensionsResponse:
    """Return ticket types, statuses, and priorities for form building."""
    return await service.list_dimensions()


# ── User-facing endpoints ─────────────────────────────────────────────────────

@router.get("/tickets", response_model=TicketListResponse)
async def list_my_tickets(
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
    status_code: str | None = Query(default=None, description="Filter by status"),
    ticket_type_code: str | None = Query(default=None, description="Filter by type"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TicketListResponse:
    """List the current user's own feedback tickets."""
    return await service.list_my_tickets(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        status_code=status_code,
        ticket_type_code=ticket_type_code,
        limit=limit,
        offset=offset,
    )


@router.post("/tickets", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    body: CreateTicketRequest,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Submit a new feedback or support ticket."""
    return await service.create_ticket(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=body,
    )


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Get ticket detail. Own tickets require feedback.view; others require feedback.manage."""
    return await service.get_ticket(user_id=claims.subject, ticket_id=ticket_id)


@router.patch("/tickets/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    body: UpdateTicketRequest,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Update a ticket's title, description, context, or priority."""
    return await service.update_ticket(
        user_id=claims.subject,
        ticket_id=ticket_id,
        request=body,
    )


@router.delete("/tickets/{ticket_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_ticket(
    ticket_id: str,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    """Soft-delete a ticket. Owner can delete open/in_review tickets; admin can delete any."""
    await service.delete_ticket(user_id=claims.subject, ticket_id=ticket_id)


@router.get("/tickets/{ticket_id}/events", response_model=TicketEventsResponse)
async def list_ticket_events(
    ticket_id: str,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> TicketEventsResponse:
    """Retrieve the audit event trail for a ticket."""
    return await service.list_events(
        user_id=claims.subject,
        ticket_id=ticket_id,
        limit=limit,
        offset=offset,
    )


# ── Admin endpoints ───────────────────────────────────────────────────────────

@router.get("/admin/tickets", response_model=TicketListResponse)
async def list_all_tickets(
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
    tenant_key: str | None = Query(default=None),
    status_code: str | None = Query(default=None),
    ticket_type_code: str | None = Query(default=None),
    priority_code: str | None = Query(default=None),
    submitted_by: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> TicketListResponse:
    """Admin: list all tickets across all users. Requires feedback.manage."""
    return await service.list_all_tickets(
        user_id=claims.subject,
        tenant_key=tenant_key,
        status_code=status_code,
        ticket_type_code=ticket_type_code,
        priority_code=priority_code,
        submitted_by_filter=submitted_by,
        limit=limit,
        offset=offset,
    )


@router.patch("/admin/tickets/{ticket_id}/status", response_model=TicketResponse)
async def change_ticket_status(
    ticket_id: str,
    body: UpdateTicketStatusRequest,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Admin: change ticket status. Validates allowed transitions."""
    return await service.change_status(
        user_id=claims.subject,
        ticket_id=ticket_id,
        request=body,
    )


@router.patch("/admin/tickets/{ticket_id}", response_model=TicketResponse)
async def admin_update_ticket(
    ticket_id: str,
    body: AdminUpdateRequest,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Admin: update status, priority, and/or internal admin note in one call."""
    return await service.admin_update(
        user_id=claims.subject,
        ticket_id=ticket_id,
        request=body,
    )


@router.post("/admin/tickets/{ticket_id}/assign", response_model=TicketResponse)
async def assign_ticket(
    ticket_id: str,
    body: AssignTicketRequest,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Admin: assign ticket to a team member."""
    return await service.assign_ticket(
        user_id=claims.subject,
        ticket_id=ticket_id,
        request=body,
    )


@router.delete("/admin/tickets/{ticket_id}/assign/{assigned_to_id}", response_model=TicketResponse)
async def unassign_ticket(
    ticket_id: str,
    assigned_to_id: str,
    service: Annotated[TicketService, Depends(get_ticket_service)],
    claims=Depends(get_current_access_claims),
) -> TicketResponse:
    """Admin: remove an assignment from a ticket."""
    return await service.unassign_ticket(
        user_id=claims.subject,
        ticket_id=ticket_id,
        assigned_to=assigned_to_id,
    )
