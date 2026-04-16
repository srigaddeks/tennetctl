from __future__ import annotations
from importlib import import_module
from fastapi import Request


def get_attachment_service(request: Request):
    _svc_mod = import_module("backend.20_ai.19_attachments.service")
    return _svc_mod.AttachmentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )
