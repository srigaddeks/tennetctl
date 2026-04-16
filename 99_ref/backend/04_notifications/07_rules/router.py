from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, status

from .dependencies import get_rule_service
from .service import RuleService
from ..schemas import (
    CreateRuleConditionRequest,
    CreateRuleRequest,
    RuleChannelResponse,
    RuleConditionResponse,
    RuleDetailResponse,
    RuleResponse,
    SetRuleChannelRequest,
    UpdateRuleRequest,
)

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(prefix="/api/v1/notifications", tags=["notification-rules"])


@router.get("/rules", response_model=list[RuleResponse])
async def list_rules(
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> list[RuleResponse]:
    return await service.list_rules(
        user_id=claims.subject, tenant_key=claims.tenant_key
    )


@router.post(
    "/rules",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule(
    body: CreateRuleRequest,
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> RuleResponse:
    return await service.create_rule(
        user_id=claims.subject, tenant_key=claims.tenant_key, request=body
    )


@router.get("/rules/{rule_id}", response_model=RuleDetailResponse)
async def get_rule(
    rule_id: str,
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> RuleDetailResponse:
    return await service.get_rule_detail(
        user_id=claims.subject, rule_id=rule_id
    )


@router.patch("/rules/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: str,
    body: UpdateRuleRequest,
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> RuleResponse:
    return await service.update_rule(
        user_id=claims.subject, rule_id=rule_id, request=body
    )


@router.put("/rules/{rule_id}/channels/{channel_code}", response_model=RuleChannelResponse)
async def set_rule_channel(
    rule_id: str,
    channel_code: str,
    body: SetRuleChannelRequest,
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> RuleChannelResponse:
    return await service.set_rule_channel(
        user_id=claims.subject,
        rule_id=rule_id,
        channel_code=channel_code,
        request=body,
    )


@router.post(
    "/rules/{rule_id}/conditions",
    response_model=RuleConditionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rule_condition(
    rule_id: str,
    body: CreateRuleConditionRequest,
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> RuleConditionResponse:
    return await service.create_rule_condition(
        user_id=claims.subject, rule_id=rule_id, request=body
    )


@router.delete(
    "/rules/{rule_id}/conditions/{condition_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_rule_condition(
    rule_id: str,
    condition_id: str,
    service: Annotated[RuleService, Depends(get_rule_service)],
    claims=Depends(get_current_access_claims),
) -> None:
    await service.delete_rule_condition(
        user_id=claims.subject, rule_id=rule_id, condition_id=condition_id
    )
