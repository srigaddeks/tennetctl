from __future__ import annotations

import asyncpg
from importlib import import_module

_errors_module = import_module("backend.01_core.errors")
ConflictError = _errors_module.ConflictError

from .models import AgentConfigRecord


class AgentConfigRepository:
    _SCHEMA = '"20_ai"'
    _TABLE = f'{_SCHEMA}."32_fct_agent_configs"'

    async def list_configs(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        agent_type_code: str | None = None,
        org_id: str | None = None,
    ) -> list[AgentConfigRecord]:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2
        if agent_type_code:
            conditions.append(f"agent_type_code = ${idx}")
            params.append(agent_type_code)
            idx += 1
        if org_id is not None:
            conditions.append(f"org_id = ${idx}")
            params.append(org_id)
            idx += 1
        where = " AND ".join(conditions)
        rows = await connection.fetch(
            f"""
            SELECT id::text, tenant_key, agent_type_code, org_id::text,
                   provider_base_url, provider_type, model_id, temperature, max_tokens,
                   is_active, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE {where}
            ORDER BY agent_type_code, org_id NULLS FIRST
            """,
            *params,
        )
        return [AgentConfigRecord(**dict(row)) for row in rows]

    async def get_config(
        self,
        connection: asyncpg.Connection,
        *,
        config_id: str,
        tenant_key: str,
    ) -> AgentConfigRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, agent_type_code, org_id::text,
                   provider_base_url, provider_type, model_id, temperature, max_tokens,
                   is_active, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE id = $1 AND tenant_key = $2
            """,
            config_id, tenant_key,
        )
        return AgentConfigRecord(**dict(row)) if row else None

    async def get_org_config(
        self,
        connection: asyncpg.Connection,
        *,
        agent_type_code: str,
        org_id: str,
    ) -> AgentConfigRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, agent_type_code, org_id::text,
                   provider_base_url, provider_type, model_id, temperature, max_tokens,
                   is_active, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE agent_type_code = $1 AND org_id = $2 AND is_active = TRUE
            """,
            agent_type_code, org_id,
        )
        return AgentConfigRecord(**dict(row)) if row else None

    async def get_global_config(
        self,
        connection: asyncpg.Connection,
        *,
        agent_type_code: str,
    ) -> AgentConfigRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, agent_type_code, org_id::text,
                   provider_base_url, provider_type, model_id, temperature, max_tokens,
                   is_active, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE agent_type_code = $1 AND org_id IS NULL AND is_active = TRUE
            """,
            agent_type_code,
        )
        return AgentConfigRecord(**dict(row)) if row else None

    async def get_encrypted_api_key(
        self,
        connection: asyncpg.Connection,
        *,
        config_id: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f"SELECT api_key_encrypted FROM {self._TABLE} WHERE id = $1",
            config_id,
        )
        return row["api_key_encrypted"] if row else None

    async def create_config(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        agent_type_code: str,
        org_id: str | None,
        provider_base_url: str | None,
        api_key_encrypted: str | None,
        provider_type: str = "openai_compatible",
        model_id: str,
        temperature: float,
        max_tokens: int,
        is_active: bool,
    ) -> AgentConfigRecord:
        try:
            row = await connection.fetchrow(
                f"""
                INSERT INTO {self._TABLE}
                    (tenant_key, agent_type_code, org_id, provider_base_url, api_key_encrypted,
                     provider_type, model_id, temperature, max_tokens, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                RETURNING id::text, tenant_key, agent_type_code, org_id::text,
                          provider_base_url, provider_type, model_id, temperature, max_tokens,
                          is_active, created_at::text, updated_at::text
                """,
                tenant_key, agent_type_code, org_id, provider_base_url, api_key_encrypted,
                provider_type, model_id, temperature, max_tokens, is_active,
            )
        except asyncpg.UniqueViolationError:
            scope = f"org {org_id}" if org_id else "global"
            raise ConflictError(f"Agent config for {agent_type_code} ({scope}) already exists")
        return AgentConfigRecord(**dict(row))

    async def update_config(
        self,
        connection: asyncpg.Connection,
        *,
        config_id: str,
        tenant_key: str,
        provider_base_url: str | None = None,
        api_key_encrypted: str | None = None,
        clear_api_key: bool = False,
        provider_type: str | None = None,
        model_id: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        is_active: bool | None = None,
    ) -> AgentConfigRecord | None:
        sets = ["updated_at = NOW()"]
        params: list = []
        idx = 1

        if provider_base_url is not None:
            sets.append(f"provider_base_url = ${idx}"); params.append(provider_base_url); idx += 1
        if api_key_encrypted is not None:
            sets.append(f"api_key_encrypted = ${idx}"); params.append(api_key_encrypted); idx += 1
        elif clear_api_key:
            sets.append("api_key_encrypted = NULL")
        if provider_type is not None:
            sets.append(f"provider_type = ${idx}"); params.append(provider_type); idx += 1
        if model_id is not None:
            sets.append(f"model_id = ${idx}"); params.append(model_id); idx += 1
        if temperature is not None:
            sets.append(f"temperature = ${idx}"); params.append(temperature); idx += 1
        if max_tokens is not None:
            sets.append(f"max_tokens = ${idx}"); params.append(max_tokens); idx += 1
        if is_active is not None:
            sets.append(f"is_active = ${idx}"); params.append(is_active); idx += 1

        params.extend([config_id, tenant_key])
        row = await connection.fetchrow(
            f"""
            UPDATE {self._TABLE}
            SET {', '.join(sets)}
            WHERE id = ${idx} AND tenant_key = ${idx + 1}
            RETURNING id::text, tenant_key, agent_type_code, org_id::text,
                      provider_base_url, provider_type, model_id, temperature, max_tokens,
                      is_active, created_at::text, updated_at::text
            """,
            *params,
        )
        return AgentConfigRecord(**dict(row)) if row else None

    async def delete_config(
        self,
        connection: asyncpg.Connection,
        *,
        config_id: str,
        tenant_key: str,
    ) -> bool:
        result = await connection.execute(
            f"DELETE FROM {self._TABLE} WHERE id = $1 AND tenant_key = $2",
            config_id, tenant_key,
        )
        return result == "DELETE 1"
