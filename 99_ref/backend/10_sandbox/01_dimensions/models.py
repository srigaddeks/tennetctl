from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SandboxDimensionRecord:
    id: int
    code: str
    name: str
    description: str
    sort_order: int
    is_active: bool


@dataclass(frozen=True)
class AssetVersionRecord:
    id: str
    connector_type_code: str
    version_code: str
    version_label: str
    is_latest: bool
    is_active: bool
    sort_order: int


@dataclass(frozen=True)
class ConnectorConfigSchemaRecord:
    connector_type_code: str
    config_schema: dict  # parsed JSONB — {"fields": [...]}
    supports_steampipe: bool
    steampipe_plugin: str | None
