from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ConversationRecord:
    id: str
    tenant_key: str
    user_id: str
    org_id: str | None
    workspace_id: str | None
    agent_type_code: str
    title: str | None
    page_context: dict | None
    is_archived: bool
    created_at: str
    updated_at: str

@dataclass(frozen=True)
class MessageRecord:
    id: str
    conversation_id: str
    role_code: str
    content: str
    token_count: int | None
    model_id: str | None
    parent_message_id: str | None
    created_at: str
