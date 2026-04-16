from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.09_attachments.01_attachments.service")
AttachmentService = _service_module.AttachmentService


def get_attachment_service(request: Request) -> AttachmentService:
    return AttachmentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
