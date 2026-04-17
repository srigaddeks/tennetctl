"""Schemas for monitoring OTLP traces receiver."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PartialSuccessJSON(BaseModel):
    """JSON mirror of OTLP ExportTracePartialSuccess."""

    rejectedSpans: int = 0
    errorMessage: str = ""


class OTLPTracesResponseJSON(BaseModel):
    """JSON mirror of ExportTraceServiceResponse."""

    partialSuccess: PartialSuccessJSON = Field(default_factory=PartialSuccessJSON)
