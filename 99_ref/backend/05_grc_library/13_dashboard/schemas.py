from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class TestStats(BaseModel):
    pass_rate: float
    total_tests: int
    failing_tests: int


class TaskForecast(BaseModel):
    overdue: int
    due_this_week: int
    total_pending: int


class FrameworkStatus(BaseModel):
    id: str
    name: str
    completion_percentage: float


class GrcDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trust_score: float
    test_stats: TestStats
    task_forecast: TaskForecast
    framework_status: list[FrameworkStatus]
    recent_activity: list[dict]  # Simplified for now


class Milestone(BaseModel):
    id: str
    title: str
    date: str
    status: str


class PortfolioEngagement(BaseModel):
    id: str
    name: str
    progress: float
    risk_level: str
    status: str


class ExecutiveDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    trust_score: float
    controls_verified_percentage: float
    pending_findings_count: int
    audit_status: str
    portfolio: list[PortfolioEngagement]
    milestones: list[Milestone]


class EngineerDashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    owned_controls_count: int
    pending_tasks_count: int
    tasks_by_status: dict[str, int]
    upcoming_deadlines: list[dict]
