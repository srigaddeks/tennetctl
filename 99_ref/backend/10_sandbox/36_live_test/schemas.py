from __future__ import annotations

from pydantic import BaseModel, Field


class LiveTestRequest(BaseModel):
    connector_id: str = Field(..., min_length=1)
    signal_ids: list[str] = Field(..., min_length=1)


class LiveTestResultItem(BaseModel):
    asset_id: str
    asset_external_id: str
    asset_type: str
    signal_id: str
    signal_code: str
    signal_name: str | None = None
    result: str  # pass / fail / warning / error / timeout
    summary: str
    details: list[dict] = Field(default_factory=list)
    execution_time_ms: int = 0


class LiveTestResponse(BaseModel):
    connector_id: str
    total_assets: int
    total_signals: int
    total_tests: int
    passed: int
    failed: int
    warnings: int
    errors: int
    results: list[LiveTestResultItem]
