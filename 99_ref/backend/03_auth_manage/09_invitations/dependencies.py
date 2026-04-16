from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.09_invitations.service")
InvitationService = _service_module.InvitationService


def get_invitation_service(request: Request) -> InvitationService:
    return InvitationService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
