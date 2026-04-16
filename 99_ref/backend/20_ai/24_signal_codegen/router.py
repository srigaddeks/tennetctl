"""
FastAPI router for interactive signal code generation.
Prefix: /api/v1/ai/signal-codegen

Routes:
  POST /generate    Generate signal Python code from spec + test data (iterative compile+test loop)
"""
from __future__ import annotations

from importlib import import_module
from typing import Annotated

from fastapi import Depends, Request
from pydantic import BaseModel, Field

from .service import SignalCodegenService

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_deps_module = import_module("backend.03_auth_manage.dependencies")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_deps_module.get_current_access_claims

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/signal-codegen",
    tags=["ai-signal-codegen"],
)


class GenerateCodeRequest(BaseModel):
    signal_spec: dict = Field(..., description="Signal specification JSON")
    test_records: list[dict] = Field(..., min_length=1, description="Test dataset records")
    signal_id: str | None = Field(None, description="Signal to save generated code to")
    org_id: str | None = None


class ArgSchema(BaseModel):
    key: str
    label: str
    type: str  # integer | string | boolean | select
    default: object = None
    description: str = ""
    min: object = None
    max: object = None
    options: list[str] = Field(default_factory=list)
    required: bool = False
    group: str = "general"


class TestResult(BaseModel):
    scenario: str
    expected_anomalous: bool | None = None
    actual_anomalous: bool | None = None
    actual_result_code: str | None = None
    passed: bool
    summary: str = ""
    error: str | None = None


class GenerateCodeResponse(BaseModel):
    status: str  # success | partial | failed
    iterations_used: int
    all_tests_passed: bool
    test_pass_rate: float
    test_results: list[dict] = Field(default_factory=list)
    generated_code: str = ""
    args_schema: list[dict] = Field(default_factory=list)
    saved_to_signal: bool = False
    signal_id: str | None = None
    elapsed_seconds: float = 0
    workspace: str = ""
    trace_log: list[dict] = Field(default_factory=list)


def _get_codegen_service(request: Request) -> SignalCodegenService:
    return SignalCodegenService(
        database_pool=request.app.state.database_pool,
        settings=request.app.state.settings,
    )


@router.post("/generate", response_model=GenerateCodeResponse)
async def generate_code(
    body: GenerateCodeRequest,
    service: Annotated[SignalCodegenService, Depends(_get_codegen_service)],
    claims=Depends(get_current_access_claims),
) -> GenerateCodeResponse:
    """
    Generate Python signal code from spec + test data.
    Iterative loop: generate → compile → test → fix (up to 8 iterations).
    Saves to signal EAV if signal_id provided.
    """
    result = await service.generate_signal_code(
        user_id=claims.subject,
        signal_spec=body.signal_spec,
        test_records=body.test_records,
        signal_id=body.signal_id,
        org_id=body.org_id,
    )
    return GenerateCodeResponse(**result)


class RetryCodegenRequest(BaseModel):
    signal_id: str = Field(..., description="Signal to retry codegen for")
    signal_spec: dict = Field(..., description="Signal specification")
    test_records: list[dict] = Field(..., min_length=1, description="Test records")
    org_id: str | None = None


@router.post("/retry", response_model=GenerateCodeResponse)
async def retry_codegen(
    body: RetryCodegenRequest,
    service: Annotated[SignalCodegenService, Depends(_get_codegen_service)],
    claims=Depends(get_current_access_claims),
) -> GenerateCodeResponse:
    """
    Retry a failed codegen run. Loads prior fix_history so LLM can learn
    from past failures and avoid repeating the same mistakes.
    """
    result = await service.generate_signal_code(
        user_id=claims.subject,
        signal_spec=body.signal_spec,
        test_records=body.test_records,
        signal_id=body.signal_id,
        org_id=body.org_id,
        is_retry=True,
    )
    return GenerateCodeResponse(**result)
