from __future__ import annotations

import asyncpg

from .models import PromptTemplateRecord


class PromptTemplateRepository:
    _SCHEMA = '"20_ai"'
    _TABLE = f'{_SCHEMA}."33_fct_prompt_templates"'

    async def list_templates(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        scope_code: str | None = None,
        agent_type_code: str | None = None,
        feature_code: str | None = None,
        org_id: str | None = None,
        active_only: bool = True,
    ) -> list[PromptTemplateRecord]:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2
        if scope_code:
            conditions.append(f"scope_code = ${idx}"); params.append(scope_code); idx += 1
        if agent_type_code:
            conditions.append(f"agent_type_code = ${idx}"); params.append(agent_type_code); idx += 1
        if feature_code:
            conditions.append(f"feature_code = ${idx}"); params.append(feature_code); idx += 1
        if org_id:
            conditions.append(f"org_id = ${idx}"); params.append(org_id); idx += 1
        if active_only:
            conditions.append("is_active = TRUE")
        where = " AND ".join(conditions)
        rows = await connection.fetch(
            f"""
            SELECT id::text, tenant_key, scope_code, agent_type_code,
                   feature_code, org_id::text, prompt_text, version, is_active,
                   created_by::text, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE {where}
            ORDER BY scope_code, agent_type_code, feature_code
            """,
            *params,
        )
        return [PromptTemplateRecord(**dict(r)) for r in rows]

    async def get_template(
        self,
        connection: asyncpg.Connection,
        *,
        template_id: str,
        tenant_key: str,
    ) -> PromptTemplateRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, scope_code, agent_type_code,
                   feature_code, org_id::text, prompt_text, version, is_active,
                   created_by::text, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE id = $1 AND tenant_key = $2
            """,
            template_id, tenant_key,
        )
        return PromptTemplateRecord(**dict(row)) if row else None

    async def get_agent_prompt(
        self,
        connection: asyncpg.Connection,
        *,
        agent_type_code: str,
    ) -> PromptTemplateRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, scope_code, agent_type_code,
                   feature_code, org_id::text, prompt_text, version, is_active,
                   created_by::text, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE scope_code = 'agent' AND agent_type_code = $1 AND is_active = TRUE
            ORDER BY version DESC LIMIT 1
            """,
            agent_type_code,
        )
        return PromptTemplateRecord(**dict(row)) if row else None

    async def get_feature_prompt(
        self,
        connection: asyncpg.Connection,
        *,
        feature_code: str,
        agent_type_code: str | None = None,
    ) -> PromptTemplateRecord | None:
        params: list = [feature_code]
        extra = ""
        if agent_type_code:
            extra = " AND (agent_type_code = $2 OR agent_type_code IS NULL)"
            params.append(agent_type_code)
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, scope_code, agent_type_code,
                   feature_code, org_id::text, prompt_text, version, is_active,
                   created_by::text, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE scope_code = 'feature' AND feature_code = $1{extra} AND is_active = TRUE
            ORDER BY agent_type_code NULLS LAST, version DESC LIMIT 1
            """,
            *params,
        )
        return PromptTemplateRecord(**dict(row)) if row else None

    async def get_org_prompt(
        self,
        connection: asyncpg.Connection,
        *,
        org_id: str,
        agent_type_code: str | None = None,
    ) -> PromptTemplateRecord | None:
        params: list = [org_id]
        extra = ""
        if agent_type_code:
            extra = " AND (agent_type_code = $2 OR agent_type_code IS NULL)"
            params.append(agent_type_code)
        row = await connection.fetchrow(
            f"""
            SELECT id::text, tenant_key, scope_code, agent_type_code,
                   feature_code, org_id::text, prompt_text, version, is_active,
                   created_by::text, created_at::text, updated_at::text
            FROM {self._TABLE}
            WHERE scope_code = 'org' AND org_id = $1{extra} AND is_active = TRUE
            ORDER BY agent_type_code NULLS LAST, version DESC LIMIT 1
            """,
            *params,
        )
        return PromptTemplateRecord(**dict(row)) if row else None

    async def create_template(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        scope_code: str,
        agent_type_code: str | None,
        feature_code: str | None,
        org_id: str | None,
        prompt_text: str,
        is_active: bool,
        created_by: str | None,
    ) -> PromptTemplateRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {self._TABLE}
                (tenant_key, scope_code, agent_type_code, feature_code, org_id,
                 prompt_text, is_active, created_by)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING id::text, tenant_key, scope_code, agent_type_code,
                      feature_code, org_id::text, prompt_text, version, is_active,
                      created_by::text, created_at::text, updated_at::text
            """,
            tenant_key, scope_code, agent_type_code, feature_code, org_id,
            prompt_text, is_active, created_by,
        )
        return PromptTemplateRecord(**dict(row))

    async def update_template(
        self,
        connection: asyncpg.Connection,
        *,
        template_id: str,
        tenant_key: str,
        prompt_text: str | None = None,
        is_active: bool | None = None,
    ) -> PromptTemplateRecord | None:
        sets = ["updated_at = NOW()", "version = version + 1"]
        params: list = []
        idx = 1
        if prompt_text is not None:
            sets.append(f"prompt_text = ${idx}"); params.append(prompt_text); idx += 1
        if is_active is not None:
            sets.append(f"is_active = ${idx}"); params.append(is_active); idx += 1
        params.extend([template_id, tenant_key])
        row = await connection.fetchrow(
            f"""
            UPDATE {self._TABLE}
            SET {', '.join(sets)}
            WHERE id = ${idx} AND tenant_key = ${idx + 1}
            RETURNING id::text, tenant_key, scope_code, agent_type_code,
                      feature_code, org_id::text, prompt_text, version, is_active,
                      created_by::text, created_at::text, updated_at::text
            """,
            *params,
        )
        return PromptTemplateRecord(**dict(row)) if row else None

    async def delete_template(
        self,
        connection: asyncpg.Connection,
        *,
        template_id: str,
        tenant_key: str,
    ) -> bool:
        result = await connection.execute(
            f"DELETE FROM {self._TABLE} WHERE id = $1 AND tenant_key = $2",
            template_id, tenant_key,
        )
        return result == "DELETE 1"
