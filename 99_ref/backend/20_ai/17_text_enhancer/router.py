"""
FastAPI router for inline AI text enhancement.

Mounts under /api/v1/ai/enhance-text/ in the main 20_ai router.

Endpoint:
  POST /api/v1/ai/enhance-text/stream
    - Auth: Bearer JWT via get_current_access_claims
    - Permission: ai_copilot.execute (checked inside service before streaming)
    - Returns: text/event-stream SSE response
    - SSE events: content_delta, enhance_complete, enhance_error
"""

from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request
from fastapi.responses import StreamingResponse

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.17_text_enhancer.service")
_schemas_module = import_module("backend.20_ai.17_text_enhancer.schemas")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
TextEnhancerService = _service_module.TextEnhancerService
EnhanceTextRequest = _schemas_module.EnhanceTextRequest

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/enhance-text",
    tags=["ai-text-enhancer"],
)


def _get_text_enhancer_service(request: Request) -> TextEnhancerService:
    """Construct a TextEnhancerService from app.state on each request."""
    return TextEnhancerService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )


@router.post("/stream")
async def stream_enhance_text(
    body: EnhanceTextRequest,
    claims: Annotated[object, Depends(get_current_access_claims)],
    request: Request,
) -> StreamingResponse:
    """
    Stream inline text enhancement for a GRC entity field.

    SSE event types:
      - content_delta:     {"delta": "<partial text>"}
      - enhance_complete:  {"enhance_id": "...", "enhanced_value": "...", "usage": {...}}
      - enhance_error:     {"enhance_id": "...", "error_code": "...", "message": "..."}
    """
    user_id: str = claims.subject
    service = _get_text_enhancer_service(request)

    return StreamingResponse(
        service.stream_enhance(
            body,
            user_id=user_id,
            tenant_key=claims.tenant_key,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
