from __future__ import annotations

from pydantic import BaseModel, Field


class CreateReviewEventRequest(BaseModel):
    event_type: str = Field(
        ...,
        pattern=r"^(status_changed|assessed|treatment_updated|control_linked|control_unlinked|comment_added|reviewed)$",
    )
    comment: str | None = None


class ReviewEventResponse(BaseModel):
    id: str
    risk_id: str
    event_type: str
    old_status: str | None = None
    new_status: str | None = None
    actor_id: str
    comment: str | None = None
    occurred_at: str
