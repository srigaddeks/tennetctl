from __future__ import annotations

import json
import asyncpg
from importlib import import_module

from .models import TestScenarioRecord, TestCaseRecord

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

SCHEMA = '"25_agent_sandbox"'


@instrument_class_methods(namespace="agent_sandbox.test_scenarios.repository", logger_name="backend.agent_sandbox.test_scenarios.repository.instrumentation")
class TestScenarioRepository:

    async def list_scenarios(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        agent_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[TestScenarioRecord], int]:
        filters = ["s.org_id = $1", "s.is_deleted = FALSE"]
        values: list[object] = [org_id]
        idx = 2
        if agent_id:
            filters.append(f"s.agent_id = ${idx}")
            values.append(agent_id)
            idx += 1

        where = " AND ".join(filters)
        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."22_fct_test_scenarios" s WHERE {where}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT s.id, s.tenant_key, s.org_id, s.workspace_id, s.scenario_code,
                   s.scenario_type_code, s.agent_id, s.is_active,
                   s.created_at::text, s.updated_at::text,
                   pn.property_value AS name,
                   pd.property_value AS description
            FROM {SCHEMA}."22_fct_test_scenarios" s
            LEFT JOIN {SCHEMA}."42_dtl_scenario_properties" pn
                ON pn.scenario_id = s.id AND pn.property_key = 'name'
            LEFT JOIN {SCHEMA}."42_dtl_scenario_properties" pd
                ON pd.scenario_id = s.id AND pd.property_key = 'description'
            WHERE {where}
            ORDER BY s.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_scenario(r) for r in rows], total

    async def get_scenario_by_id(
        self, connection: asyncpg.Connection, scenario_id: str
    ) -> TestScenarioRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT s.id, s.tenant_key, s.org_id, s.workspace_id, s.scenario_code,
                   s.scenario_type_code, s.agent_id, s.is_active,
                   s.created_at::text, s.updated_at::text,
                   pn.property_value AS name,
                   pd.property_value AS description
            FROM {SCHEMA}."22_fct_test_scenarios" s
            LEFT JOIN {SCHEMA}."42_dtl_scenario_properties" pn
                ON pn.scenario_id = s.id AND pn.property_key = 'name'
            LEFT JOIN {SCHEMA}."42_dtl_scenario_properties" pd
                ON pd.scenario_id = s.id AND pd.property_key = 'description'
            WHERE s.id = $1 AND s.is_deleted = FALSE
            """,
            scenario_id,
        )
        return _row_to_scenario(row) if row else None

    async def create_scenario(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        scenario_code: str,
        scenario_type_code: str,
        agent_id: str | None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."22_fct_test_scenarios"
                (id, tenant_key, org_id, workspace_id, scenario_code,
                 scenario_type_code, agent_id,
                 is_active, is_deleted,
                 created_at, updated_at, created_by, updated_by,
                 deleted_at, deleted_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE, FALSE, $8, $9, $10, $11, NULL, NULL)
            """,
            id, tenant_key, org_id, workspace_id, scenario_code,
            scenario_type_code, agent_id,
            now, now, created_by, created_by,
        )
        return id

    async def upsert_properties(
        self,
        connection: asyncpg.Connection,
        scenario_id: str,
        properties: dict[str, str],
        *,
        created_by: str,
        now: object,
    ) -> None:
        if not properties:
            return
        rows = [
            (scenario_id, key, value, now, now, created_by, created_by)
            for key, value in properties.items()
        ]
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."42_dtl_scenario_properties"
                (id, scenario_id, property_key, property_value,
                 created_at, updated_at, created_by, updated_by)
            VALUES (gen_random_uuid(), $1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT (scenario_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            rows,
        )

    async def soft_delete_scenario(
        self, connection: asyncpg.Connection, scenario_id: str, *, deleted_by: str, now: object
    ) -> bool:
        result = await connection.execute(
            f"""
            UPDATE {SCHEMA}."22_fct_test_scenarios"
            SET is_deleted = TRUE, is_active = FALSE,
                deleted_at = $1, deleted_by = $2, updated_at = $3, updated_by = $4
            WHERE id = $5 AND is_deleted = FALSE
            """,
            now, deleted_by, now, deleted_by, scenario_id,
        )
        return result != "UPDATE 0"

    # ── test cases ────────────────────────────────────────────

    async def add_test_case(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        scenario_id: str,
        case_index: int,
        input_messages: list[dict],
        initial_context: dict,
        expected_behavior: dict,
        evaluation_method_code: str,
        evaluation_config: dict,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."23_fct_test_cases"
                (id, scenario_id, case_index, input_messages, initial_context,
                 expected_behavior, evaluation_method_code, evaluation_config,
                 is_active, created_at, updated_at, created_by)
            VALUES ($1, $2, $3, $4::jsonb, $5::jsonb, $6::jsonb, $7, $8::jsonb, TRUE, $9, $10, $11)
            """,
            id, scenario_id, case_index,
            json.dumps(input_messages), json.dumps(initial_context),
            json.dumps(expected_behavior), evaluation_method_code, json.dumps(evaluation_config),
            now, now, created_by,
        )
        return id

    async def get_next_case_index(
        self, connection: asyncpg.Connection, scenario_id: str
    ) -> int:
        row = await connection.fetchrow(
            f'SELECT COALESCE(MAX(case_index), -1) + 1 AS next FROM {SCHEMA}."23_fct_test_cases" WHERE scenario_id = $1',
            scenario_id,
        )
        return row["next"]

    async def list_test_cases(
        self, connection: asyncpg.Connection, scenario_id: str
    ) -> list[TestCaseRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, scenario_id, case_index, input_messages, initial_context,
                   expected_behavior, evaluation_method_code, evaluation_config,
                   is_active, created_at::text
            FROM {SCHEMA}."23_fct_test_cases"
            WHERE scenario_id = $1 AND is_active = TRUE
            ORDER BY case_index
            """,
            scenario_id,
        )
        return [
            TestCaseRecord(
                id=r["id"], scenario_id=r["scenario_id"],
                case_index=r["case_index"],
                input_messages=json.loads(r["input_messages"]) if isinstance(r["input_messages"], str) else r["input_messages"],
                initial_context=json.loads(r["initial_context"]) if isinstance(r["initial_context"], str) else r["initial_context"],
                expected_behavior=json.loads(r["expected_behavior"]) if isinstance(r["expected_behavior"], str) else r["expected_behavior"],
                evaluation_method_code=r["evaluation_method_code"],
                evaluation_config=json.loads(r["evaluation_config"]) if isinstance(r["evaluation_config"], str) else r["evaluation_config"],
                is_active=r["is_active"],
                created_at=r["created_at"],
            )
            for r in rows
        ]


def _row_to_scenario(r) -> TestScenarioRecord:
    return TestScenarioRecord(
        id=r["id"], tenant_key=r["tenant_key"], org_id=r["org_id"],
        workspace_id=r.get("workspace_id"), scenario_code=r["scenario_code"],
        scenario_type_code=r["scenario_type_code"], agent_id=r.get("agent_id"),
        is_active=r["is_active"], created_at=r["created_at"], updated_at=r["updated_at"],
        name=r.get("name"), description=r.get("description"),
    )
