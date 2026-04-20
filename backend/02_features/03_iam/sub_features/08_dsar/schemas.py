"""
iam.dsar — Pydantic v2 schemas.

Data Subject Access Request (DSAR) schemas for operator-triggered requests.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class DsarExportRequest(BaseModel):
    """POST /v1/dsar/export-request"""
    subject_user_id: str = Field(..., description="Target user whose data is requested")
    org_id: str = Field(..., description="Org scope of the request")


class DsarDeleteRequest(BaseModel):
    """POST /v1/dsar/delete-request"""
    subject_user_id: str = Field(..., description="Target user whose data will be deleted")
    org_id: str = Field(..., description="Org scope of the request")


class DsarJobResponse(BaseModel):
    """DSAR job response with all fields."""
    id: str
    org_id: str
    subject_user_id: str
    actor_user_id: str
    actor_session_id: str | None
    job_type: str
    status: Literal["requested", "in_progress", "completed", "failed"]
    row_counts: dict | None = None
    result_location: str | None = None
    error_detail: str | None = None
    completed_at: datetime | None = None
    created_at: datetime
    download_url: str | None = None  # Added by service if export is complete


class DsarJobListResponse(BaseModel):
    """GET /v1/dsar/jobs — paginated list."""
    jobs: list[DsarJobResponse]
    total: int
    limit: int
    offset: int


class DsarStatusCode(BaseModel):
    """Status value for response."""
    status: Literal["requested", "in_progress", "completed", "failed"]
