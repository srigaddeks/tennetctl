from __future__ import annotations

import asyncpg
from dataclasses import dataclass


@dataclass(frozen=True)
class GuardrailConfigRecord:
    id: str
    tenant_key: str
    org_id: str | None
    guardrail_type_code: str
    is_enabled: bool
    config_json: dict


class GuardrailRepository:
    _SCHEMA = '"20_ai"'
    _CONFIGS = f'{_SCHEMA}."30_fct_guardrail_configs"'
    _EVENTS = f'{_SCHEMA}."31_trx_guardrail_events"'

    async def get_org_configs(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None,
    ) -> list[GuardrailConfigRecord]:
        # Get org-specific configs; fall back to tenant-level (org_id IS NULL)
        rows = await connection.fetch(
            f"""
            SELECT id::text, tenant_key, org_id::text, guardrail_type_code,
                   is_enabled, config_json
            FROM {self._CONFIGS}
            WHERE tenant_key = $1
              AND (org_id = $2 OR org_id IS NULL)
            ORDER BY org_id NULLS LAST
            """,
            tenant_key, org_id,
        )
        # Org-specific overrides take precedence (org_id IS NOT NULL first)
        seen: set[str] = set()
        result: list[GuardrailConfigRecord] = []
        for row in rows:
            if row["guardrail_type_code"] not in seen:
                seen.add(row["guardrail_type_code"])
                result.append(GuardrailConfigRecord(
                    id=row["id"], tenant_key=row["tenant_key"], org_id=row["org_id"],
                    guardrail_type_code=row["guardrail_type_code"],
                    is_enabled=row["is_enabled"], config_json=dict(row["config_json"]),
                ))
        return result

    async def upsert_config(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        org_id: str | None,
        guardrail_type_code: str,
        is_enabled: bool,
        config_json: dict,
    ) -> GuardrailConfigRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {self._CONFIGS}
                (tenant_key, org_id, guardrail_type_code, is_enabled, config_json)
            VALUES ($1, $2, $3, $4, $5)
            ON CONFLICT (tenant_key, COALESCE(org_id::text, ''), guardrail_type_code)
            DO UPDATE SET
                is_enabled = EXCLUDED.is_enabled,
                config_json = EXCLUDED.config_json,
                updated_at = NOW()
            RETURNING id::text, tenant_key, org_id::text, guardrail_type_code,
                      is_enabled, config_json
            """,
            tenant_key, org_id, guardrail_type_code, is_enabled, config_json,
        )
        return GuardrailConfigRecord(
            id=row["id"], tenant_key=row["tenant_key"], org_id=row["org_id"],
            guardrail_type_code=row["guardrail_type_code"],
            is_enabled=row["is_enabled"], config_json=dict(row["config_json"]),
        )

    async def log_event(
        self,
        connection: asyncpg.Connection,
        *,
        id: str,
        agent_run_id: str | None,
        user_id: str,
        tenant_key: str,
        guardrail_type_code: str,
        direction: str,
        action_taken: str,
        matched_pattern: str | None,
        severity: str,
        original_content: str | None,
        sanitized_content: str | None,
    ) -> None:
        await connection.execute(
            f"""
            INSERT INTO {self._EVENTS}
                (id, agent_run_id, user_id, tenant_key, guardrail_type_code,
                 direction, action_taken, matched_pattern, severity,
                 original_content, sanitized_content)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """,
            id, agent_run_id, user_id, tenant_key, guardrail_type_code,
            direction, action_taken, matched_pattern, severity,
            original_content, sanitized_content,
        )

    async def list_events(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        user_id: str | None = None,
        guardrail_type_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict]:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2
        if user_id:
            conditions.append(f"user_id = ${idx}"); params.append(user_id); idx += 1
        if guardrail_type_code:
            conditions.append(f"guardrail_type_code = ${idx}"); params.append(guardrail_type_code); idx += 1
        params.extend([limit, offset])
        rows = await connection.fetch(
            f"""
            SELECT id::text, agent_run_id::text, user_id::text, tenant_key,
                   guardrail_type_code, direction, action_taken, matched_pattern,
                   severity, occurred_at::text
            FROM {self._EVENTS}
            WHERE {" AND ".join(conditions)}
            ORDER BY occurred_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
            """,
            *params,
        )
        return [dict(r) for r in rows]
