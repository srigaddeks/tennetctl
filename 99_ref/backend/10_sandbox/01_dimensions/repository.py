from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import SandboxDimensionRecord, AssetVersionRecord, ConnectorConfigSchemaRecord

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_DIMENSION_TABLES = {
    "connector_categories": "02_dim_connector_categories",
    "connector_types": "03_dim_connector_types",
    "signal_statuses": "04_dim_signal_statuses",
    "dataset_sources": "05_dim_dataset_sources",
    "execution_statuses": "06_dim_execution_statuses",
    "dataset_templates": "07_dim_dataset_templates",
    "threat_severities": "08_dim_threat_severities",
    "policy_action_types": "09_dim_policy_action_types",
    "library_types": "10_dim_library_types",
    "asset_versions": "11_dim_asset_versions",
}

# Tables that support optional filtering by a parent code
_FILTERABLE_TABLES = {
    "connector_types": "category_code",
    "dataset_templates": "connector_type_code",
    "asset_versions": "connector_type_code",
}

# Tables with non-standard column names — maps to (code_col, name_col, description_col)
_COLUMN_ALIASES = {
    "asset_versions": ("version_code", "version_label", None),
    "threat_severities": ("code", "name", None),
    "execution_statuses": ("code", "name", None),
}

# Tables that do NOT have an is_active column (no active flag — all rows are "active")
_NO_IS_ACTIVE = {
    "signal_statuses",
    "execution_statuses",
    "dataset_sources",
    "threat_severities",
    "library_types",
}


@instrument_class_methods(namespace="sandbox.dimensions.repository", logger_name="backend.sandbox.dimensions.repository.instrumentation")
class SandboxDimensionRepository:
    async def list_dimension(
        self,
        connection: asyncpg.Connection,
        *,
        dimension_name: str,
        filter_code: str | None = None,
    ) -> list[SandboxDimensionRecord]:
        table = _DIMENSION_TABLES[dimension_name]
        filter_column = _FILTERABLE_TABLES.get(dimension_name)
        aliases = _COLUMN_ALIASES.get(dimension_name)

        has_active = dimension_name not in _NO_IS_ACTIVE

        if aliases:
            code_col, name_col, desc_col = aliases
            active_sel = ", is_active" if has_active else ", TRUE AS is_active"
            select_cols = f"id, {code_col} AS code, {name_col} AS name, {f'{desc_col} AS description' if desc_col else 'NULL AS description'}, sort_order{active_sel}"
        else:
            active_sel = ", is_active" if has_active else ", TRUE AS is_active"
            select_cols = f"id, code, name, description, sort_order{active_sel}"

        if filter_code and filter_column:
            where = f"WHERE {'is_active = TRUE AND ' if has_active else ''}{filter_column} = $1"
            rows = await connection.fetch(
                f"SELECT {select_cols} FROM {SCHEMA}.\"{table}\" {where} ORDER BY sort_order, name",
                filter_code,
            )
        else:
            where = "WHERE is_active = TRUE" if has_active else ""
            rows = await connection.fetch(
                f"SELECT {select_cols} FROM {SCHEMA}.\"{table}\" {where} ORDER BY sort_order, name"
            )
        return [
            SandboxDimensionRecord(
                id=r["id"],
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]

    async def list_asset_versions(
        self,
        connection: asyncpg.Connection,
        *,
        connector_type_code: str | None = None,
    ) -> list[AssetVersionRecord]:
        if connector_type_code:
            rows = await connection.fetch(
                f"""
                SELECT id, connector_type_code, version_code, version_label, is_latest, is_active, sort_order
                FROM {SCHEMA}."11_dim_asset_versions"
                WHERE is_active = TRUE AND connector_type_code = $1
                ORDER BY sort_order, version_label
                """,
                connector_type_code,
            )
        else:
            rows = await connection.fetch(
                f"""
                SELECT id, connector_type_code, version_code, version_label, is_latest, is_active, sort_order
                FROM {SCHEMA}."11_dim_asset_versions"
                WHERE is_active = TRUE
                ORDER BY sort_order, version_label
                """
            )
        return [
            AssetVersionRecord(
                id=str(r["id"]),
                connector_type_code=r["connector_type_code"],
                version_code=r["version_code"],
                version_label=r["version_label"],
                is_latest=r["is_latest"],
                is_active=r["is_active"],
                sort_order=r["sort_order"],
            )
            for r in rows
        ]

    async def get_connector_config_schema(
        self,
        connection: asyncpg.Connection,
        *,
        connector_type_code: str,
    ) -> ConnectorConfigSchemaRecord | None:
        import json as _json
        row = await connection.fetchrow(
            f"""
            SELECT code, config_schema, supports_steampipe, steampipe_plugin
            FROM {SCHEMA}."16_dim_provider_definitions"
            WHERE code = $1 AND is_active = TRUE
            """,
            connector_type_code,
        )
        if not row:
            return None
        raw = row["config_schema"]
        schema = _json.loads(raw) if isinstance(raw, str) else dict(raw)
        return ConnectorConfigSchemaRecord(
            connector_type_code=row["code"],
            config_schema=schema,
            supports_steampipe=row["supports_steampipe"],
            steampipe_plugin=row["steampipe_plugin"],
        )
