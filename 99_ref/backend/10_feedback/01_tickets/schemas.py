from __future__ import annotations
from pydantic import BaseModel, Field


class CreateTicketRequest(BaseModel):
    ticket_type_code: str
    priority_code: str = "medium"
    title: str = Field(..., min_length=5, max_length=300)
    description: str = Field(..., min_length=3, max_length=10000)
    context_url: str | None = Field(None, max_length=2000)
    browser_info: str | None = Field(None, max_length=500)
    steps_to_reproduce: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    version_info: str | None = None
    org_id: str | None = None
    workspace_id: str | None = None


class UpdateTicketRequest(BaseModel):
    title: str | None = Field(None, min_length=5, max_length=300)
    description: str | None = None
    context_url: str | None = None
    browser_info: str | None = None
    priority_code: str | None = None


class UpdateTicketStatusRequest(BaseModel):
    status_code: str
    note: str | None = None


class AssignTicketRequest(BaseModel):
    assigned_to: str
    note: str | None = None


class AdminUpdateRequest(BaseModel):
    status_code: str | None = None
    priority_code: str | None = None
    admin_note: str | None = None


class AssignmentResponse(BaseModel):
    assigned_to: str
    assigned_by: str
    assigned_at: str


class TicketResponse(BaseModel):
    id: str
    tenant_key: str
    submitted_by: str
    ticket_type_code: str
    status_code: str
    priority_code: str
    org_id: str | None = None
    workspace_id: str | None = None
    title: str | None = None
    description: str | None = None
    context_url: str | None = None
    browser_info: str | None = None
    steps_to_reproduce: str | None = None
    expected_behavior: str | None = None
    actual_behavior: str | None = None
    version_info: str | None = None
    admin_note: str | None = None
    submitter_email: str | None = None
    submitter_display_name: str | None = None
    active_assignments: list[AssignmentResponse] = []
    created_at: str
    updated_at: str
    resolved_at: str | None = None


class TicketListResponse(BaseModel):
    items: list[TicketResponse]
    total: int


class TicketEventResponse(BaseModel):
    id: str
    ticket_id: str
    event_type: str
    actor_id: str
    occurred_at: str
    old_value: str | None = None
    new_value: str | None = None
    note: str | None = None


class TicketEventsResponse(BaseModel):
    items: list[TicketEventResponse]
    total: int


class TicketTypeDimResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    icon_name: str | None = None
    sort_order: int
    is_active: bool


class TicketStatusDimResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    is_terminal: bool
    sort_order: int


class TicketPriorityDimResponse(BaseModel):
    code: str
    name: str
    description: str | None = None
    numeric_level: int
    sort_order: int


class TicketDimensionsResponse(BaseModel):
    ticket_types: list[TicketTypeDimResponse]
    ticket_statuses: list[TicketStatusDimResponse]
    ticket_priorities: list[TicketPriorityDimResponse]
