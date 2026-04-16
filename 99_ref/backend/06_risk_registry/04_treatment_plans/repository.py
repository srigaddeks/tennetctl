from __future__ import annotations

import asyncpg
from importlib import import_module

from .models import TreatmentPlanRecord

SCHEMA = '"14_risk_registry"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="risk.treatment_plans.repository", logger_name="backend.risk.treatment_plans.repository.instrumentation")
class TreatmentPlanRepository:
    async def get_treatment_plan(
        self, connection: asyncpg.Connection, risk_id: str
    ) -> TreatmentPlanRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, risk_id::text, tenant_key, plan_status,
                   target_date::text, completed_at::text, is_active,
                   created_at::text, updated_at::text, created_by::text
            FROM {SCHEMA}."11_fct_risk_treatment_plans"
            WHERE risk_id = $1::uuid AND is_deleted = FALSE
            """,
            risk_id,
        )
        return _row_to_plan(row) if row else None

    async def create_treatment_plan(
        self,
        connection: asyncpg.Connection,
        *,
        plan_id: str,
        risk_id: str,
        tenant_key: str,
        plan_status: str,
        target_date: str | None,
        created_by: str,
        now: datetime,
    ) -> TreatmentPlanRecord:
        target_ts = None
        if target_date is not None:
            from datetime import datetime as dt
            target_ts = dt.fromisoformat(target_date)

        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."11_fct_risk_treatment_plans" (
                id, risk_id, tenant_key, plan_status, target_date, completed_at,
                is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            )
            VALUES (
                $1::uuid, $2::uuid, $3, $4, $5, NULL,
                TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                $6, $7, $8::uuid, $9::uuid, NULL, NULL
            )
            RETURNING id::text, risk_id::text, tenant_key, plan_status,
                      target_date::text, completed_at::text, is_active,
                      created_at::text, updated_at::text, created_by::text
            """,
            plan_id,
            risk_id,
            tenant_key,
            plan_status,
            target_ts,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_plan(row)

    async def update_treatment_plan(
        self,
        connection: asyncpg.Connection,
        risk_id: str,
        *,
        plan_status: str | None = None,
        target_date: str | None = None,
        updated_by: str,
        now: datetime,
    ) -> TreatmentPlanRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2::uuid"]
        values: list[object] = [now, updated_by]
        idx = 3

        if plan_status is not None:
            fields.append(f"plan_status = ${idx}")
            values.append(plan_status)
            idx += 1
            if plan_status == "completed":
                fields.append(f"completed_at = ${idx}")
                values.append(now)
                idx += 1
        if target_date is not None:
            from datetime import datetime as dt
            fields.append(f"target_date = ${idx}")
            values.append(dt.fromisoformat(target_date))
            idx += 1

        values.append(risk_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."11_fct_risk_treatment_plans"
            SET {set_clause}
            WHERE risk_id = ${idx}::uuid AND is_deleted = FALSE
            RETURNING id::text, risk_id::text, tenant_key, plan_status,
                      target_date::text, completed_at::text, is_active,
                      created_at::text, updated_at::text, created_by::text
            """,
            *values,
        )
        return _row_to_plan(row) if row else None

    async def list_treatment_plan_properties(
        self, connection: asyncpg.Connection, plan_id: str
    ) -> dict[str, str]:
        rows = await connection.fetch(
            f"""
            SELECT property_key, property_value
            FROM {SCHEMA}."21_dtl_treatment_plan_properties"
            WHERE treatment_plan_id = $1::uuid
            ORDER BY property_key
            """,
            plan_id,
        )
        return {r["property_key"]: r["property_value"] for r in rows}

    async def upsert_treatment_plan_property(
        self,
        connection: asyncpg.Connection,
        *,
        prop_id: str,
        treatment_plan_id: str,
        property_key: str,
        property_value: str,
        actor_id: str,
        now: datetime,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."21_dtl_treatment_plan_properties" (
                id, treatment_plan_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            )
            VALUES ($1::uuid, $2::uuid, $3, $4, $5, $6, $7::uuid, $8::uuid)
            ON CONFLICT (treatment_plan_id, property_key)
            DO UPDATE SET
                property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            prop_id,
            treatment_plan_id,
            property_key,
            property_value,
            now,
            now,
            actor_id,
            actor_id,
        )


def _row_to_plan(r) -> TreatmentPlanRecord:
    return TreatmentPlanRecord(
        id=r["id"],
        risk_id=r["risk_id"],
        tenant_key=r["tenant_key"],
        plan_status=r["plan_status"],
        target_date=r["target_date"],
        completed_at=r["completed_at"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
        created_by=r["created_by"],
    )
