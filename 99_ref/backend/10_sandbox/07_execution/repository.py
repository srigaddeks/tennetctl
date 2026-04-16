from __future__ import annotations

import json

import asyncpg
from importlib import import_module

from .models import (
    SandboxRunRecord,
    SandboxRunDetailRecord,
    ThreatEvaluationRecord,
    PolicyExecutionRecord,
)

SCHEMA = '"15_sandbox"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="sandbox.execution.repository", logger_name="backend.sandbox.execution.repository.instrumentation")
class ExecutionRepository:

    # ── sandbox runs ──────────────────────────────────────────────

    async def insert_run(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        signal_id: str,
        dataset_id: str | None,
        live_session_id: str | None,
        execution_status_code: str,
        result_code: str | None,
        result_summary: str | None,
        result_details: list[dict] | None,
        execution_time_ms: int | None,
        error_message: str | None,
        stdout_capture: str | None,
        python_source_snapshot: str,
        dataset_snapshot_hash: str | None,
        started_at: object | None,
        completed_at: object | None,
        created_by: str | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."25_trx_sandbox_runs"
                (id, tenant_key, org_id, workspace_id, signal_id,
                 dataset_id, live_session_id,
                 execution_status_code, result_code, result_summary,
                 result_details, execution_time_ms, error_message, stdout_capture,
                 python_source_snapshot, dataset_snapshot_hash,
                 started_at, completed_at, created_at, created_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7,
                 $8, $9, $10,
                 $11::jsonb, $12, $13, $14,
                 $15, $16,
                 $17, $18, NOW(), $19)
            """,
            id,
            tenant_key,
            org_id,
            workspace_id,
            signal_id,
            dataset_id,
            live_session_id,
            execution_status_code,
            result_code,
            result_summary,
            json.dumps(result_details) if result_details else None,
            execution_time_ms,
            error_message,
            stdout_capture,
            python_source_snapshot,
            dataset_snapshot_hash,
            started_at,
            completed_at,
            created_by,
        )
        return id

    async def list_runs(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        signal_id: str | None = None,
        dataset_id: str | None = None,
        execution_status_code: str | None = None,
        result_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[SandboxRunRecord], int]:
        """Returns (records, total_count) using a window function to avoid a separate COUNT query."""
        filters = ["v.org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if signal_id is not None:
            filters.append(f"v.signal_id = ${idx}")
            values.append(signal_id)
            idx += 1
        if dataset_id is not None:
            filters.append(f"v.dataset_id = ${idx}")
            values.append(dataset_id)
            idx += 1
        if execution_status_code is not None:
            filters.append(f"v.execution_status_code = ${idx}")
            values.append(execution_status_code)
            idx += 1
        if result_code is not None:
            filters.append(f"v.result_code = ${idx}")
            values.append(result_code)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT v.id, v.tenant_key, v.org_id, v.signal_id, v.signal_code,
                   v.dataset_id, v.live_session_id,
                   v.execution_status_code, v.execution_status_name,
                   v.result_code, v.result_summary, v.execution_time_ms,
                   v.started_at::text, v.completed_at::text, v.created_at::text,
                   v.signal_name,
                   r.result_details,
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."65_vw_run_detail" v
            JOIN {SCHEMA}."25_trx_sandbox_runs" r ON r.id = v.id
            WHERE {where_clause}
            ORDER BY v.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_run(r) for r in rows], total

    async def get_run_by_id(
        self, connection: asyncpg.Connection, run_id: str,
    ) -> SandboxRunDetailRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT r.id, r.tenant_key, r.org_id, r.workspace_id,
                   r.signal_id, s.signal_code,
                   r.dataset_id, r.live_session_id,
                   r.execution_status_code,
                   es.name AS execution_status_name,
                   r.result_code, r.result_summary,
                   r.result_details::text, r.execution_time_ms,
                   r.error_message, r.stdout_capture,
                   r.started_at::text, r.completed_at::text, r.created_at::text,
                   (SELECT p.property_value FROM {SCHEMA}."45_dtl_signal_properties" p
                    WHERE p.signal_id = s.id AND p.property_key = 'name') AS signal_name
            FROM {SCHEMA}."25_trx_sandbox_runs" r
            JOIN {SCHEMA}."22_fct_signals" s ON s.id = r.signal_id
            JOIN {SCHEMA}."06_dim_execution_statuses" es ON es.code = r.execution_status_code
            WHERE r.id = $1
            """,
            run_id,
        )
        if row is None:
            return None
        return _row_to_run_detail(row)

    # ── threat evaluations ────────────────────────────────────────

    async def insert_threat_evaluation(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        threat_type_id: str,
        is_triggered: bool,
        signal_results: dict,
        expression_snapshot: dict,
        live_session_id: str | None,
        created_by: str | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."26_trx_threat_evaluations"
                (id, tenant_key, org_id, threat_type_id,
                 is_triggered, signal_results, expression_snapshot,
                 live_session_id, evaluated_at, created_by)
            VALUES
                ($1, $2, $3, $4,
                 $5, $6::jsonb, $7::jsonb,
                 $8, NOW(), $9)
            """,
            id,
            tenant_key,
            org_id,
            threat_type_id,
            is_triggered,
            json.dumps(signal_results),
            json.dumps(expression_snapshot),
            live_session_id,
            created_by,
        )
        return id

    async def list_threat_evaluations(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        threat_type_id: str | None = None,
        is_triggered: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[ThreatEvaluationRecord], int]:
        """Returns (records, total_count) using a window function."""
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if threat_type_id is not None:
            filters.append(f"threat_type_id = ${idx}")
            values.append(threat_type_id)
            idx += 1
        if is_triggered is not None:
            filters.append(f"is_triggered = ${idx}")
            values.append(is_triggered)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, threat_type_id,
                   is_triggered, signal_results::text, expression_snapshot::text,
                   live_session_id, evaluated_at::text, created_by,
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."26_trx_threat_evaluations"
            WHERE {where_clause}
            ORDER BY evaluated_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_threat_evaluation(r) for r in rows], total

    async def get_threat_evaluation(
        self, connection: asyncpg.Connection, eval_id: str,
    ) -> ThreatEvaluationRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, threat_type_id,
                   is_triggered, signal_results::text, expression_snapshot::text,
                   live_session_id, evaluated_at::text, created_by
            FROM {SCHEMA}."26_trx_threat_evaluations"
            WHERE id = $1
            """,
            eval_id,
        )
        return _row_to_threat_evaluation(row) if row else None

    # ── policy executions ─────────────────────────────────────────

    async def insert_policy_execution(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        policy_id: str,
        threat_evaluation_id: str,
        actions_executed: list[dict],
        actions_failed: list[dict] | None,
        created_by: str | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."27_trx_policy_executions"
                (id, tenant_key, org_id, policy_id, threat_evaluation_id,
                 actions_executed, actions_failed,
                 executed_at, created_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6::jsonb, $7::jsonb,
                 NOW(), $8)
            """,
            id,
            tenant_key,
            org_id,
            policy_id,
            threat_evaluation_id,
            json.dumps(actions_executed),
            json.dumps(actions_failed) if actions_failed else None,
            created_by,
        )
        return id

    async def list_policy_executions(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        policy_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[PolicyExecutionRecord], int]:
        """Returns (records, total_count) using a window function."""
        filters = ["org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if policy_id is not None:
            filters.append(f"policy_id = ${idx}")
            values.append(policy_id)
            idx += 1

        where_clause = " AND ".join(filters)

        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, org_id, policy_id, threat_evaluation_id,
                   actions_executed::text, actions_failed::text,
                   executed_at::text, created_by,
                   COUNT(*) OVER() AS _total
            FROM {SCHEMA}."27_trx_policy_executions"
            WHERE {where_clause}
            ORDER BY executed_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        total = rows[0]["_total"] if rows else 0
        return [_row_to_policy_execution(r) for r in rows], total

    async def get_policy_execution(
        self, connection: asyncpg.Connection, exec_id: str,
    ) -> PolicyExecutionRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, org_id, policy_id, threat_evaluation_id,
                   actions_executed::text, actions_failed::text,
                   executed_at::text, created_by
            FROM {SCHEMA}."27_trx_policy_executions"
            WHERE id = $1
            """,
            exec_id,
        )
        return _row_to_policy_execution(row) if row else None

    # ── lifecycle events ──────────────────────────────────────────

    async def insert_lifecycle_event(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        entity_type: str,
        entity_id: str,
        event_type: str,
        old_value: str | None,
        new_value: str | None,
        actor_id: str,
        comment: str | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."31_trx_entity_lifecycle_events"
                (id, tenant_key, org_id, entity_type, entity_id,
                 event_type, old_value, new_value, actor_id, comment,
                 occurred_at)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7, $8, $9, $10,
                 NOW())
            """,
            id,
            tenant_key,
            org_id,
            entity_type,
            entity_id,
            event_type,
            old_value,
            new_value,
            actor_id,
            comment,
        )
        return id


# ── row mappers ───────────────────────────────────────────────────

def _row_to_run(r) -> SandboxRunRecord:
    try:
        result_details_raw = r["result_details"]
    except (KeyError, IndexError):
        result_details_raw = None
    if isinstance(result_details_raw, str):
        try:
            result_details = json.loads(result_details_raw)
        except (json.JSONDecodeError, TypeError):
            result_details = None
    else:
        result_details = result_details_raw

    return SandboxRunRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        signal_id=r["signal_id"],
        signal_code=r["signal_code"],
        dataset_id=r["dataset_id"],
        live_session_id=r["live_session_id"],
        execution_status_code=r["execution_status_code"],
        execution_status_name=r["execution_status_name"],
        result_code=r["result_code"],
        result_summary=r["result_summary"],
        execution_time_ms=r["execution_time_ms"],
        started_at=r["started_at"],
        completed_at=r["completed_at"],
        created_at=r["created_at"],
        signal_name=r["signal_name"],
        result_details=result_details,
    )


def _row_to_run_detail(r) -> SandboxRunDetailRecord:
    result_details_raw = r["result_details"]
    if isinstance(result_details_raw, str):
        try:
            result_details = json.loads(result_details_raw)
        except (json.JSONDecodeError, TypeError):
            result_details = None
    else:
        result_details = result_details_raw

    return SandboxRunDetailRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r["workspace_id"],
        signal_id=r["signal_id"],
        signal_code=r.get("signal_code"),
        dataset_id=r["dataset_id"],
        live_session_id=r["live_session_id"],
        execution_status_code=r["execution_status_code"],
        execution_status_name=r.get("execution_status_name"),
        result_code=r["result_code"],
        result_summary=r["result_summary"],
        result_details=result_details,
        execution_time_ms=r["execution_time_ms"],
        error_message=r["error_message"],
        stdout_capture=r["stdout_capture"],
        started_at=r["started_at"],
        completed_at=r["completed_at"],
        created_at=r["created_at"],
        signal_name=r.get("signal_name"),
    )


def _decode_json_recursive(val):
    current = val
    for _ in range(3):
        if not isinstance(current, str):
            break
        try:
            current = json.loads(current)
        except (json.JSONDecodeError, TypeError):
            break
    return current


def _parse_json(val):
    decoded = _decode_json_recursive(val)
    return decoded if isinstance(decoded, dict) else {}


def _parse_json_list(val):
    decoded = _decode_json_recursive(val)
    return decoded if isinstance(decoded, list) else []


def _row_to_threat_evaluation(r) -> ThreatEvaluationRecord:
    return ThreatEvaluationRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        threat_type_id=r["threat_type_id"],
        is_triggered=r["is_triggered"],
        signal_results=_parse_json(r["signal_results"]),
        expression_snapshot=_parse_json(r["expression_snapshot"]),
        live_session_id=r["live_session_id"],
        evaluated_at=r["evaluated_at"],
        created_by=r["created_by"],
    )


def _row_to_policy_execution(r) -> PolicyExecutionRecord:
    return PolicyExecutionRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        policy_id=r["policy_id"],
        threat_evaluation_id=r["threat_evaluation_id"],
        actions_executed=_parse_json_list(r["actions_executed"]),
        actions_failed=_parse_json_list(r["actions_failed"]),
        executed_at=r["executed_at"],
        created_by=r["created_by"],
    )
