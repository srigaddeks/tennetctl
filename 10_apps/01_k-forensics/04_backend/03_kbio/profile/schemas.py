"""kbio profile schemas."""
from __future__ import annotations

from pydantic import BaseModel


class ProfileSummary(BaseModel):
    user_hash: str
    status: str = "active"
    baseline_quality: str = "insufficient"
    profile_maturity: float = 0.0
    total_sessions: int = 0
    centroid_count: int = 0
    last_genuine_session_at: str | None = None
    baseline_age_days: int = 0
    credential_profile_count: int = 0
    encoder_version: str = "v1"
