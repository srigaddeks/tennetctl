from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_review_event_service
from .schemas import CreateReviewEventRequest, ReviewEventResponse
from .service import ReviewEventService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(tags=["risk-review-events"])


@router.get("/risks/{risk_id}/events", response_model=list[ReviewEventResponse])
async def list_review_events(
    risk_id: str,
    service: Annotated[ReviewEventService, Depends(get_review_event_service)],
    claims=Depends(get_current_access_claims),
) -> list[ReviewEventResponse]:
    return await service.list_review_events(user_id=claims.subject, risk_id=risk_id)


@router.post(
    "/risks/{risk_id}/events",
    response_model=ReviewEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_review_event(
    risk_id: str,
    body: CreateReviewEventRequest,
    service: Annotated[ReviewEventService, Depends(get_review_event_service)],
    claims=Depends(get_current_access_claims),
) -> ReviewEventResponse:
    return await service.create_review_event(
        user_id=claims.subject, risk_id=risk_id, request=body
    )
