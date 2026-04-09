"""kprotect evaluate schemas."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field


class EvaluateRequest(BaseModel):
    """Main evaluation request from SDK (via kprotect API)."""
    session_id: str
    user_hash: str
    device_uuid: str | None = None
    event_type: str = "behavioral"  # behavioral | login | critical_action
    batch: dict[str, Any] = Field(default_factory=dict)  # the raw behavioral batch to forward to kbio
    policy_set_code: str | None = None  # optional; falls back to org's default set
    metadata: dict[str, Any] = Field(default_factory=dict)


class PolicyResult(BaseModel):
    """Result of evaluating a single predefined policy."""
    policy_code: str
    action: str
    reason: str | None = None
    execution_ms: float = 0.0


class EvaluateResponse(BaseModel):
    """Full evaluation response returned to SDK."""
    decision_id: str
    action: str  # allow | challenge | block | monitor | flag | throttle
    reason: str | None = None
    policies_evaluated: int = 0
    policies_triggered: int = 0
    latency_ms: dict[str, float] = Field(default_factory=dict)
    details: list[PolicyResult] = Field(default_factory=list)
    context_summary: dict[str, Any] = Field(default_factory=dict)
    # Pass through kbio score data
    drift_score: float = -1.0
    confidence: float = 0.0
    bot_score: float = 0.0
    signal_scores: dict[str, float] = Field(default_factory=dict)
    auth_state: dict[str, Any] = Field(default_factory=dict)
    drift_trend: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
