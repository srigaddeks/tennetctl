from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import RiskCategoryRecord, RiskLevelRecord, RiskTreatmentTypeRecord

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="risk.dimensions.repository", logger_name="backend.risk.dimensions.repository.instrumentation")
class DimensionsRepository:
    async def list_risk_categories(self, connection: asyncpg.Connection) -> list[RiskCategoryRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, sort_order, is_active FROM {SCHEMA}."02_dim_risk_categories" ORDER BY sort_order'
        )
        return [RiskCategoryRecord(
            code=r["code"], name=r["name"], description=r["description"],
            sort_order=r["sort_order"], is_active=r["is_active"],
        ) for r in rows]

    async def list_treatment_types(self, connection: asyncpg.Connection) -> list[RiskTreatmentTypeRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, sort_order, is_active FROM {SCHEMA}."03_dim_risk_treatment_types" ORDER BY sort_order'
        )
        return [RiskTreatmentTypeRecord(
            code=r["code"], name=r["name"], description=r["description"],
            sort_order=r["sort_order"], is_active=r["is_active"],
        ) for r in rows]

    async def list_risk_levels(self, connection: asyncpg.Connection) -> list[RiskLevelRecord]:
        rows = await connection.fetch(
            f'SELECT code, name, description, score_min, score_max, color_hex, sort_order, is_active FROM {SCHEMA}."04_dim_risk_levels" ORDER BY sort_order'
        )
        return [RiskLevelRecord(
            code=r["code"], name=r["name"], description=r["description"],
            score_min=r["score_min"], score_max=r["score_max"], color_hex=r["color_hex"],
            sort_order=r["sort_order"], is_active=r["is_active"],
        ) for r in rows]
