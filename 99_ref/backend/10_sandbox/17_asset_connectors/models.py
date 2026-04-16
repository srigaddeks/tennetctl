from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssetConnector:
    """
    An asset inventory connector instance.
    Backed by 20_fct_connector_instances with asset-inventory-specific columns
    (provider_definition_code, provider_version_code, connection_config).
    """
    id: str
    tenant_key: str
    org_id: str
    instance_code: str
    # Asset-inventory fields
    provider_definition_code: str | None
    provider_version_code: str | None
    connection_config: dict | None          # Non-credential config (JSONB)
    # Schedule & health
    collection_schedule: str               # hourly | daily | weekly | manual
    last_collected_at: str | None
    health_status: str                     # unchecked | healthy | degraded | error | auth_failed
    consecutive_failures: int
    cooldown_until: str | None
    is_active: bool
    created_at: str
    updated_at: str
    # Display (from EAV properties)
    name: str | None
    description: str | None
