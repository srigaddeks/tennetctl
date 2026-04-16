"""featureflags.evaluations — FastAPI routes.

Single endpoint:
  POST /v1/evaluate { flag_key, environment, context } → EvaluateResponse
"""
from __future__ import annotations

from importlib import import_module
from typing import Any

from fastapi import APIRouter, Request

_response: Any = import_module("backend.01_core.response")

_schemas: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.05_evaluations.schemas"
)
_service: Any = import_module(
    "backend.02_features.09_featureflags.sub_features.05_evaluations.service"
)

EvaluateRequest = _schemas.EvaluateRequest
EvaluateResponse = _schemas.EvaluateResponse

router = APIRouter(prefix="/v1/evaluate", tags=["featureflags.evaluations"])


@router.post("", status_code=200)
async def evaluate_route(request: Request, body: EvaluateRequest) -> dict:
    pool = request.app.state.pool
    async with pool.acquire() as conn:
        result = await _service.evaluate(
            conn,
            flag_key=body.flag_key,
            environment=body.environment,
            context=body.context.model_dump(),
        )
    return _response.success(EvaluateResponse(**result).model_dump())
