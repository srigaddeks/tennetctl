from __future__ import annotations
from importlib import import_module
from typing import Annotated, AsyncIterator
from fastapi import Depends, Query
from fastapi.responses import StreamingResponse

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_service_module = import_module("backend.20_ai.02_conversations.service")
_schemas_module = import_module("backend.20_ai.02_conversations.schemas")
_deps_module = import_module("backend.20_ai.02_conversations.dependencies")
_streaming_module = import_module("backend.20_ai.02_conversations.streaming")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
ConversationService = _service_module.ConversationService
ConversationListResponse = _schemas_module.ConversationListResponse
ConversationResponse = _schemas_module.ConversationResponse
CreateConversationRequest = _schemas_module.CreateConversationRequest
SendMessageRequest = _schemas_module.SendMessageRequest
MessageResponse = _schemas_module.MessageResponse
get_conversation_service = _deps_module.get_conversation_service
stream_mock_response = _streaming_module.stream_mock_response  # kept for fallback/testing

router = InstrumentedAPIRouter(prefix="/api/v1/ai/conversations", tags=["ai-conversations"])

@router.get("", response_model=ConversationListResponse)
async def list_conversations(service: Annotated[ConversationService, Depends(get_conversation_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)],
        org_id: str = Query(...),
        workspace_id: str = Query(...),
        agent_type_code: str | None = Query(default=None),
        is_archived: bool = Query(default=False), limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0)) -> ConversationListResponse:
    return await service.list_conversations(user_id=claims.subject,
        tenant_key=claims.tenant_key, is_archived=is_archived, org_id=org_id,
        workspace_id=workspace_id, agent_type_code=agent_type_code, limit=limit, offset=offset)

@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(request: CreateConversationRequest,
        service: Annotated[ConversationService, Depends(get_conversation_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)]) -> ConversationResponse:
    return await service.create_conversation(user_id=claims.subject,
        tenant_key=claims.tenant_key, request=request)

@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str,
        service: Annotated[ConversationService, Depends(get_conversation_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)],
        org_id: str = Query(...),
        workspace_id: str = Query(...)) -> ConversationResponse:
    return await service.get_conversation(conversation_id=conversation_id,
        user_id=claims.subject, tenant_key=claims.tenant_key,
        org_id=org_id, workspace_id=workspace_id)

@router.post("/{conversation_id}/archive", status_code=204)
async def archive_conversation(conversation_id: str,
        service: Annotated[ConversationService, Depends(get_conversation_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)],
        org_id: str = Query(...),
        workspace_id: str = Query(...)) -> None:
    await service.archive_conversation(conversation_id=conversation_id,
        user_id=claims.subject, tenant_key=claims.tenant_key,
        org_id=org_id, workspace_id=workspace_id)

@router.get("/{conversation_id}/messages", response_model=list[MessageResponse])
async def list_messages(conversation_id: str,
        service: Annotated[ConversationService, Depends(get_conversation_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)],
        org_id: str = Query(...),
        workspace_id: str = Query(...),
        limit: int = Query(default=100, ge=1, le=500)) -> list[MessageResponse]:
    return await service.list_messages(
        conversation_id=conversation_id,
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        limit=limit,
    )

@router.post("/{conversation_id}/stream")
async def stream_message(conversation_id: str, request: SendMessageRequest,
        service: Annotated[ConversationService, Depends(get_conversation_service)],
        claims: Annotated[dict, Depends(get_current_access_claims)],
        org_id: str = Query(...),
        workspace_id: str = Query(...)) -> StreamingResponse:
    return StreamingResponse(
        service.stream_message(
            conversation_id=conversation_id,
            user_id=claims.subject,
            tenant_key=claims.tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            content=request.content,
            page_context=request.page_context,
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
