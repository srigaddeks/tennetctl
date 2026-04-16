from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CollectionRun:
    id: str
    tenant_key: str
    org_id: str
    connector_instance_id: str
    status: str
    trigger_type: str
    started_at: datetime | None
    completed_at: datetime | None
    assets_discovered: int
    assets_updated: int
    assets_deleted: int
    logs_ingested: int
    error_message: str | None
    triggered_by: str | None
    created_at: datetime
    updated_at: datetime
