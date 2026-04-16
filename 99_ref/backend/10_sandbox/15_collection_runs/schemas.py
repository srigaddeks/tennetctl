from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CollectionRunResponse(BaseModel):
    id: str
    tenant_key: str
    org_id: str
    connector_instance_id: str
    status: str
    trigger_type: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    assets_discovered: int
    assets_updated: int
    assets_deleted: int
    logs_ingested: int
    error_message: str | None = None
    triggered_by: str | None = None
    created_at: datetime
    updated_at: datetime
    duration_seconds: int | None = None

    @model_validator(mode="before")
    @classmethod
    def compute_duration(cls, data: Any) -> Any:
        if isinstance(data, dict):
            started = data.get("started_at")
            completed = data.get("completed_at")
            if started and completed:
                if isinstance(started, datetime) and isinstance(completed, datetime):
                    data["duration_seconds"] = max(
                        0, int((completed - started).total_seconds())
                    )
                else:
                    data["duration_seconds"] = None
            else:
                data["duration_seconds"] = None
        return data


class CollectionRunListResponse(BaseModel):
    items: list[CollectionRunResponse]
    total: int


class TriggerCollectionRequest(BaseModel):
    connector_instance_id: UUID
    asset_types: list[str] | None = Field(default=None)
