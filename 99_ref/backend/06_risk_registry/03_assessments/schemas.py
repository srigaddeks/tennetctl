from __future__ import annotations

from pydantic import BaseModel, Field


class CreateAssessmentRequest(BaseModel):
    assessment_type: str = Field(default="inherent", pattern=r"^(inherent|residual)$")
    likelihood_score: int = Field(..., ge=1, le=5)
    impact_score: int = Field(..., ge=1, le=5)
    assessment_notes: str | None = None


class AssessmentResponse(BaseModel):
    id: str
    risk_id: str
    assessment_type: str
    likelihood_score: int
    impact_score: int
    risk_score: int
    assessed_by: str
    assessment_notes: str | None = None
    assessed_at: str
