from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConnectorInstanceRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    instance_code: str
    connector_type_code: str
    connector_type_name: str | None
    connector_category_code: str | None
    connector_category_name: str | None
    asset_version_id: str | None
    collection_schedule: str
    last_collected_at: str | None
    health_status: str
    is_active: bool
    is_draft: bool
    created_at: str
    updated_at: str
    name: str | None
    description: str | None
