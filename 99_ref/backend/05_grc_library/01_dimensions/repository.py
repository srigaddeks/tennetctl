from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import DimensionRecord

SCHEMA = '"05_grc_library"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

_DIMENSION_TABLES = {
    "framework_types": "02_dim_framework_types",
    "framework_categories": "03_dim_framework_categories",
    "control_categories": "04_dim_control_categories",
    "control_criticalities": "05_dim_control_criticalities",
    "test_types": "07_dim_test_types",
    "test_result_statuses": "08_dim_test_result_statuses",
}


@instrument_class_methods(namespace="grc.dimensions.repository", logger_name="backend.grc.dimensions.repository.instrumentation")
class DimensionRepository:
    async def list_dimension(
        self, connection: asyncpg.Connection, *, dimension_name: str
    ) -> list[DimensionRecord]:
        table = _DIMENSION_TABLES[dimension_name]
        rows = await connection.fetch(
            f"""
            SELECT code, name, description, sort_order, is_active
            FROM {SCHEMA}."{table}"
            WHERE is_active = TRUE
            ORDER BY sort_order, name
            """
        )
        return [
            DimensionRecord(
                code=r["code"],
                name=r["name"],
                description=r["description"],
                sort_order=r["sort_order"],
                is_active=r["is_active"],
            )
            for r in rows
        ]
