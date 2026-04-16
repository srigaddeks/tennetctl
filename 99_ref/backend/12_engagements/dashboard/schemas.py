from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class EngagementSummary(BaseModel):
    id: str
    code: str
    name: str
    org_name: str
    status: str
    progress_percentage: float
    open_requests_count: int
    verified_controls_count: int
    total_controls_count: int
    target_date: Optional[str]


class ReviewQueueItem(BaseModel):
    task_id: str
    title: str
    control_code: str
    framework_name: str
    due_date: Optional[str]
    status: str


class AuditorDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    active_engagements_count: int
    pending_reviews_count: int
    total_pending_requests: int
    total_verified_controls: int
    engagements: List[EngagementSummary]
    review_queue: List[ReviewQueueItem]
