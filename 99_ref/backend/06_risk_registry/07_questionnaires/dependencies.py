from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.06_risk_registry.07_questionnaires.service")
QuestionnairesService = _service_module.QuestionnairesService


def get_questionnaires_service(request: Request) -> QuestionnairesService:
    return QuestionnairesService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
    )
