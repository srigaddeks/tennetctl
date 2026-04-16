from __future__ import annotations

from importlib import import_module

from fastapi import Request

_svc_module = import_module("backend.20_ai.28_pdf_templates.service")
PdfTemplateService = _svc_module.PdfTemplateService


def get_pdf_template_service(request: Request) -> PdfTemplateService:
    return PdfTemplateService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )
