"""kbio drift schemas."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DriftState(BaseModel):
    session_id: str
    user_hash: str
    current_drift_score: float = -1.0
    confidence: float = 0.0
    session_trust: str = "trusted"
    drift_trend: dict[str, Any] = Field(default_factory=dict)
    signal_scores: dict[str, float] = Field(default_factory=dict)
    pulse_count: int = 0
    baseline_quality: str = "insufficient"
    active: bool = True
