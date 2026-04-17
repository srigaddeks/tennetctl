"""Schemas for monitoring OTLP logs receiver.

OTLP spec returns protobuf ExportLogsServiceResponse. We also support a JSON
form. No tennetctl envelope — OTel clients expect raw spec responses.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PartialSuccessJSON(BaseModel):
    """JSON mirror of OTLP ExportLogsPartialSuccess."""

    rejectedLogRecords: int = 0
    errorMessage: str = ""


class OTLPLogsResponseJSON(BaseModel):
    """JSON mirror of ExportLogsServiceResponse."""

    partialSuccess: PartialSuccessJSON = Field(default_factory=PartialSuccessJSON)
