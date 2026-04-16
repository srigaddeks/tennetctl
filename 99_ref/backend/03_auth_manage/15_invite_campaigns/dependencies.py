from __future__ import annotations

from importlib import import_module

from fastapi import Request

_service_module = import_module("backend.03_auth_manage.15_invite_campaigns.service")
CampaignService = _service_module.CampaignService


def get_campaign_service(request: Request) -> CampaignService:
    return CampaignService(
        settings=request.app.state.settings,
        database_pool=request.app.state.database_pool,
        cache=request.app.state.cache,
    )
