"""
FastAPI router for AI-powered form auto-fill.

Mounts under /api/v1/ai/form-fill/ in the main 20_ai router.

Endpoints:
  POST /api/v1/ai/form-fill/stream        — single LLM call (v1)
  POST /api/v1/ai/form-fill/agent/stream  — agentic multi-turn form fill (v2)
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.18_form_fill.service")
_schemas_module = import_module("backend.20_ai.18_form_fill.schemas")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
FormFillService = _service_module.FormFillService
FormFillRequest = _schemas_module.FormFillRequest

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/form-fill",
    tags=["ai-form-fill"],
)

_SSE_HEADERS = {
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}


def _get_service(request: Request) -> FormFillService:
    return FormFillService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )


@router.post("/stream")
async def stream_form_fill(
    body: FormFillRequest,
    claims: Annotated[object, Depends(get_current_access_claims)],
    request: Request,
) -> StreamingResponse:
    """
    Stream AI-generated form field values for a GRC entity create dialog.

    SSE event types:
      - content_delta:  {"delta": "<partial JSON text>"} — live preview
      - fill_complete:  {"fill_id": "...", "entity_type": "...", "fields": {...}, "usage": {...}}
      - fill_error:     {"fill_id": "...", "error_code": "...", "message": "..."}
    """
    user_id: str = claims.subject
    service = _get_service(request)
    return StreamingResponse(
        service.stream_fill(body, user_id=user_id, tenant_key=claims.tenant_key),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


class AgentFillRequest(BaseModel):
    entity_type: str = Field(..., min_length=1, max_length=50)
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str = Field(..., min_length=1, max_length=100)
    history: list[dict] = Field(default_factory=list)
    org_id: str | None = Field(None, max_length=100)
    workspace_id: str | None = Field(None, max_length=100)
    page_context: dict = Field(default_factory=dict)


@router.post("/agent/stream")
async def stream_agent_form_fill(
    body: AgentFillRequest,
    claims: Annotated[object, Depends(get_current_access_claims)],
    request: Request,
) -> StreamingResponse:
    """
    Agentic form fill: runs the GRC agent with read-only tools + grc_propose_form_fields.
    Conversations are ephemeral (not persisted to a DB conversation thread).

    SSE event types:
      - message_start:        {"message_id": "..."}
      - content_delta:        {"delta": "..."}  — agent thinking/asking
      - tool_call_start:      {"tool_name": "...", "tool_category": "...", "input_summary": "..."}
      - tool_call_result:     {"tool_name": "...", "is_successful": bool, "output_summary": "..."}
      - form_fill_proposed:   {"fields": {...}, "explanation": "..."}  — fills the form
      - message_end:          {"usage": {...}}
      - fill_error:           {"error_code": "...", "message": "..."}
    """
    user_id: str = claims.subject
    service = _get_service(request)
    return StreamingResponse(
        service.stream_agent_fill(
            entity_type=body.entity_type,
            message=body.message,
            history=body.history,
            page_context=body.page_context,
            org_id=body.org_id,
            workspace_id=body.workspace_id,
            user_id=user_id,
            tenant_key=claims.tenant_key,
            session_id=body.session_id,
        ),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )
