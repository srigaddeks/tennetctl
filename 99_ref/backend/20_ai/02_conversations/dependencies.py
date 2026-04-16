from __future__ import annotations
from importlib import import_module
from fastapi import Request
_service_module = import_module("backend.20_ai.02_conversations.service")
ConversationService = _service_module.ConversationService

def get_conversation_service(request: Request) -> ConversationService:
    return ConversationService(settings=request.app.state.settings,
        database_pool=request.app.state.database_pool, cache=request.app.state.cache)
