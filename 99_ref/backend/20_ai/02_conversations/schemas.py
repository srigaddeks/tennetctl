from __future__ import annotations
from pydantic import BaseModel, Field

class CreateConversationRequest(BaseModel):
    agent_type_code: str = Field(default="copilot", max_length=50)
    title: str | None = Field(None, max_length=500)
    page_context: dict | None = None
    org_id: str | None = None
    workspace_id: str | None = None

class SendMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=32000)
    page_context: dict | None = None

class ConversationResponse(BaseModel):
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None = None
    workspace_id: str | None = None
    agent_type_code: str
    title: str | None = None
    page_context: dict | None = None
    is_archived: bool
    created_at: str
    updated_at: str

class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int

class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    role_code: str
    content: str
    token_count: int | None = None
    model_id: str | None = None
    created_at: str
