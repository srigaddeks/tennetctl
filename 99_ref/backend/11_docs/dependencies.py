from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.11_docs.service")
DocumentService = _service_module.DocumentService


def get_document_service(request: Request) -> DocumentService:
    return DocumentService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
