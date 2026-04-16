from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssessmentRecord:
    id: str
    risk_id: str
    assessment_type: str
    likelihood_score: int
    impact_score: int
    risk_score: int
    assessed_by: str
    assessment_notes: str | None
    assessed_at: str
