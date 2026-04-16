from __future__ import annotations
from importlib import import_module
from fastapi import Request

_service_module = import_module("backend.10_feedback.01_tickets.service")
TicketService = _service_module.TicketService


def get_ticket_service(request: Request) -> TicketService:
    return TicketService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
