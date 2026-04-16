from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Query, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .dispatcher import dispatch_playground_run

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/asb/playground", tags=["agent-sandbox-playground"])


class PlaygroundRunRequest(BaseModel):
    inputs: dict = Field(default_factory=dict, description="Agent-specific inputs")


@router.post("/{agent_code}/run")
async def run_agent_playground(
    agent_code: str,
    body: PlaygroundRunRequest,
    request: Request,
    claims=Depends(get_current_access_claims),
    org_id: str = Query(..., description="Organization ID"),
    workspace_id: str | None = Query(None, description="Workspace ID"),
) -> StreamingResponse:
    """Execute an agent in playground mode with SSE streaming."""

    async def event_stream():
        async for event in dispatch_playground_run(
            agent_code=agent_code,
            inputs=body.inputs,
            user_id=claims.subject,
            tenant_key=claims.tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            settings=request.app.state.settings,
            database_pool=request.app.state.database_pool,
        ):
            yield event

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
