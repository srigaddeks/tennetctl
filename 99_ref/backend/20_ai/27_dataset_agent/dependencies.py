"""FastAPI dependencies for Dataset AI Agent."""
from __future__ import annotations

from fastapi import Request

from .service import DatasetAgentService


def get_dataset_agent_service(request: Request) -> DatasetAgentService:
    return DatasetAgentService(
        database_pool=request.app.state.database_pool,
        settings=request.app.state.settings,
    )
