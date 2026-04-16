from __future__ import annotations

import asyncio
from importlib import import_module
from uuid import UUID
from .schemas import AuditorDashboardResponse, EngagementSummary, ReviewQueueItem

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_engagements_repo_module = import_module("backend.12_engagements.repository")
_models_module = import_module("backend.12_engagements.models")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
EngagementDetailRecord = _models_module.EngagementDetailRecord
EngagementRepository = _engagements_repo_module.EngagementRepository

_LOGGER = get_logger("backend.engagements.dashboard")

@instrument_class_methods(namespace="engagements.dashboard.service", logger_name="backend.engagements.dashboard.instrumentation")
class AuditorDashboardService:
    def __init__(self, *, database_pool) -> None:
        self._database_pool = database_pool
        self._repo = EngagementRepository()

    async def is_user_globally_active(self, *, user_id: str) -> bool:
        async with self._database_pool.acquire() as conn:
            return await self._repo.is_user_globally_active(
                conn,
                user_id=user_id,
            )

    async def get_dashboard(
        self,
        *,
        user_id: str,
        email: str,
        org_id: str | None = None,
    ) -> AuditorDashboardResponse:
        async with self._database_pool.acquire() as conn:
            engagements = await self._repo.list_my_engagements(
                conn,
                user_id=user_id,
                email=email,
                org_id=org_id,
            )
            engagement_summaries = [
                EngagementSummary(
                    id=r.id,
                    code=r.engagement_code or "N/A",
                    name=r.engagement_name or r.engagement_code or "Untitled",
                    org_name=r.org_name or "N/A",
                    status=r.status_name or "Draft",
                    progress_percentage=(
                        (r.verified_controls_count * 100.0 / r.total_controls_count)
                        if r.total_controls_count > 0 else 0
                    ),
                    open_requests_count=r.open_requests_count,
                    verified_controls_count=r.verified_controls_count,
                    total_controls_count=r.total_controls_count,
                    target_date=r.target_completion_date,
                ) for r in engagements
            ]

            review_rows = await self._repo.list_review_queue_for_user(
                conn,
                user_id=user_id,
                email=email,
                org_id=org_id,
                limit=20,
            )
            review_queue = [
                ReviewQueueItem(
                    task_id=r["task_id"],
                    title=r["title"],
                    control_code=r["control_code"],
                    framework_name=r["framework_name"],
                    due_date=r["due_date"],
                    status=r["status_code"]
                ) for r in review_rows
            ]

            return AuditorDashboardResponse(
                active_engagements_count=len(engagement_summaries),
                pending_reviews_count=len(review_queue),
                total_pending_requests=sum(e.open_requests_count for e in engagement_summaries),
                total_verified_controls=sum(e.verified_controls_count for e in engagement_summaries),
                engagements=engagement_summaries,
                review_queue=review_queue
            )
