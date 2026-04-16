from __future__ import annotations

import json
import asyncpg
from importlib import import_module

from .models import AgentRunRecord, AgentRunStepRecord

instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods

SCHEMA = '"25_agent_sandbox"'


@instrument_class_methods(namespace="agent_sandbox.execution.repository", logger_name="backend.agent_sandbox.execution.repository.instrumentation")
class AgentRunRepository:

    # ── create run ────────────────────────────────────────────

    async def create_run(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None,
        agent_id: str,
        execution_status_code: str,
        input_messages: list[dict],
        initial_context: dict,
        graph_source_snapshot: str | None,
        agent_code_snapshot: str | None,
        version_snapshot: int | None,
        langfuse_trace_id: str | None,
        job_queue_id: str | None,
        test_run_id: str | None,
        created_by: str,
        now: object,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."70_fct_agent_runs"
                (id, tenant_key, org_id, workspace_id, agent_id,
                 execution_status_code, input_messages, initial_context,
                 graph_source_snapshot, agent_code_snapshot, version_snapshot,
                 langfuse_trace_id, job_queue_id, test_run_id,
                 started_at, created_at, created_by)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6, $7::jsonb, $8::jsonb,
                 $9, $10, $11,
                 $12, $13, $14,
                 $15, $16, $17)
            """,
            id, tenant_key, org_id, workspace_id, agent_id,
            execution_status_code, json.dumps(input_messages), json.dumps(initial_context),
            graph_source_snapshot, agent_code_snapshot, version_snapshot,
            langfuse_trace_id, job_queue_id, test_run_id,
            now, now, created_by,
        )
        return id

    # ── update run ────────────────────────────────────────────

    async def update_run_result(
        self,
        connection: asyncpg.Connection,
        run_id: str,
        *,
        execution_status_code: str,
        output_messages: list[dict] | None,
        final_state: dict | None,
        error_message: str | None,
        tokens_used: int,
        tool_calls_made: int,
        llm_calls_made: int,
        cost_usd: float,
        iterations_used: int,
        execution_time_ms: int,
        completed_at: object,
    ) -> None:
        await connection.execute(
            f"""
            UPDATE {SCHEMA}."70_fct_agent_runs"
            SET execution_status_code = $1,
                output_messages = $2::jsonb,
                final_state = $3::jsonb,
                error_message = $4,
                tokens_used = $5,
                tool_calls_made = $6,
                llm_calls_made = $7,
                cost_usd = $8,
                iterations_used = $9,
                execution_time_ms = $10,
                completed_at = $11
            WHERE id = $12
            """,
            execution_status_code,
            json.dumps(output_messages) if output_messages else None,
            json.dumps(final_state) if final_state else None,
            error_message,
            tokens_used, tool_calls_made, llm_calls_made,
            cost_usd, iterations_used, execution_time_ms,
            completed_at, run_id,
        )

    # ── insert step ───────────────────────────────────────────

    async def insert_step(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        agent_run_id: str,
        step_index: int,
        node_name: str,
        step_type: str,
        input_json: dict | None,
        output_json: dict | None,
        transition: str | None,
        tokens_used: int,
        cost_usd: float,
        duration_ms: int | None,
        error_message: str | None,
        started_at: object,
        completed_at: object | None,
    ) -> str:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."71_dtl_agent_run_steps"
                (id, agent_run_id, step_index, node_name, step_type,
                 input_json, output_json, transition,
                 tokens_used, cost_usd, duration_ms, error_message,
                 started_at, completed_at)
            VALUES
                ($1, $2, $3, $4, $5,
                 $6::jsonb, $7::jsonb, $8,
                 $9, $10, $11, $12,
                 $13, $14)
            """,
            id, agent_run_id, step_index, node_name, step_type,
            json.dumps(input_json) if input_json else None,
            json.dumps(output_json) if output_json else None,
            transition,
            tokens_used, cost_usd, duration_ms, error_message,
            started_at, completed_at,
        )
        return id

    # ── insert LLM call ──────────────────────────────────────

    async def insert_llm_call(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        run_step_id: str,
        model_id: str | None,
        system_prompt: str | None,
        user_prompt: str | None,
        response_text: str | None,
        input_tokens: int,
        output_tokens: int,
        total_tokens: int,
        cost_usd: float,
        duration_ms: int | None,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."73_dtl_agent_run_llm_calls"
                (id, run_step_id, model_id, system_prompt, user_prompt,
                 response_text, input_tokens, output_tokens, total_tokens,
                 cost_usd, duration_ms, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
            """,
            id, run_step_id, model_id, system_prompt, user_prompt,
            response_text, input_tokens, output_tokens, total_tokens,
            cost_usd, duration_ms,
        )

    # ── insert tool call ─────────────────────────────────────

    async def insert_tool_call(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        run_step_id: str,
        tool_code: str,
        tool_type_code: str,
        input_json: dict | None,
        output_json: dict | None,
        duration_ms: int | None,
        error_message: str | None,
        approval_status: str | None,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."72_dtl_agent_run_tool_calls"
                (id, run_step_id, tool_code, tool_type_code,
                 input_json, output_json, duration_ms,
                 error_message, approval_status, created_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, $9, NOW())
            """,
            id, run_step_id, tool_code, tool_type_code,
            json.dumps(input_json) if input_json else None,
            json.dumps(output_json) if output_json else None,
            duration_ms, error_message, approval_status,
        )

    # ── list runs ─────────────────────────────────────────────

    async def list_runs(
        self,
        connection: asyncpg.Connection,
        org_id: str,
        *,
        agent_id: str | None = None,
        execution_status_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[AgentRunRecord], int]:
        filters = ["r.org_id = $1"]
        values: list[object] = [org_id]
        idx = 2

        if agent_id is not None:
            filters.append(f"r.agent_id = ${idx}")
            values.append(agent_id)
            idx += 1
        if execution_status_code is not None:
            filters.append(f"r.execution_status_code = ${idx}")
            values.append(execution_status_code)
            idx += 1

        where = " AND ".join(filters)

        count_row = await connection.fetchrow(
            f'SELECT COUNT(*)::int AS total FROM {SCHEMA}."81_vw_agent_run_detail" r WHERE {where}',
            *values,
        )
        total = count_row["total"] if count_row else 0

        rows = await connection.fetch(
            f"""
            SELECT r.id, r.tenant_key, r.org_id, r.workspace_id, r.agent_id,
                   r.execution_status_code, r.execution_status_name,
                   r.tokens_used, r.tool_calls_made, r.llm_calls_made,
                   r.cost_usd::float, r.iterations_used,
                   r.error_message,
                   r.started_at::text, r.completed_at::text,
                   r.execution_time_ms, r.langfuse_trace_id, r.test_run_id,
                   r.agent_code_snapshot, r.version_snapshot, r.agent_name,
                   r.created_at::text, r.created_by
            FROM {SCHEMA}."81_vw_agent_run_detail" r
            WHERE {where}
            ORDER BY r.created_at DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *values,
        )
        return [_row_to_run(r) for r in rows], total

    # ── get run ───────────────────────────────────────────────

    async def get_run_by_id(
        self, connection: asyncpg.Connection, run_id: str
    ) -> AgentRunRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT r.id, r.tenant_key, r.org_id, r.workspace_id, r.agent_id,
                   r.execution_status_code, r.execution_status_name,
                   r.tokens_used, r.tool_calls_made, r.llm_calls_made,
                   r.cost_usd::float, r.iterations_used,
                   r.error_message,
                   r.started_at::text, r.completed_at::text,
                   r.execution_time_ms, r.langfuse_trace_id, r.test_run_id,
                   r.agent_code_snapshot, r.version_snapshot, r.agent_name,
                   r.created_at::text, r.created_by
            FROM {SCHEMA}."81_vw_agent_run_detail" r
            WHERE r.id = $1
            """,
            run_id,
        )
        return _row_to_run(row) if row else None

    # ── list steps ────────────────────────────────────────────

    async def list_steps(
        self, connection: asyncpg.Connection, run_id: str
    ) -> list[AgentRunStepRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, agent_run_id, step_index, node_name, step_type,
                   transition, tokens_used, cost_usd::float, duration_ms,
                   error_message, started_at::text, completed_at::text
            FROM {SCHEMA}."71_dtl_agent_run_steps"
            WHERE agent_run_id = $1
            ORDER BY step_index
            """,
            run_id,
        )
        return [
            AgentRunStepRecord(
                id=r["id"], agent_run_id=r["agent_run_id"],
                step_index=r["step_index"], node_name=r["node_name"],
                step_type=r["step_type"], transition=r.get("transition"),
                tokens_used=r["tokens_used"], cost_usd=float(r["cost_usd"]),
                duration_ms=r.get("duration_ms"), error_message=r.get("error_message"),
                started_at=r["started_at"], completed_at=r.get("completed_at"),
            )
            for r in rows
        ]


def _row_to_run(r) -> AgentRunRecord:
    return AgentRunRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        org_id=r["org_id"],
        workspace_id=r.get("workspace_id"),
        agent_id=r["agent_id"],
        execution_status_code=r["execution_status_code"],
        execution_status_name=r.get("execution_status_name"),
        tokens_used=r["tokens_used"],
        tool_calls_made=r["tool_calls_made"],
        llm_calls_made=r["llm_calls_made"],
        cost_usd=float(r["cost_usd"]),
        iterations_used=r["iterations_used"],
        error_message=r.get("error_message"),
        started_at=r.get("started_at"),
        completed_at=r.get("completed_at"),
        execution_time_ms=r.get("execution_time_ms"),
        langfuse_trace_id=r.get("langfuse_trace_id"),
        test_run_id=r.get("test_run_id"),
        agent_code_snapshot=r.get("agent_code_snapshot"),
        version_snapshot=r.get("version_snapshot"),
        agent_name=r.get("agent_name"),
        created_at=r["created_at"],
        created_by=r.get("created_by"),
    )
