from __future__ import annotations
import asyncpg
from .models import ConversationRecord, MessageRecord

class ConversationRepository:
    _SCHEMA = '"20_ai"'
    _CONV = f'{_SCHEMA}."20_fct_conversations"'
    _MSG  = f'{_SCHEMA}."21_fct_messages"'

    async def create_conversation(self, conn: asyncpg.Connection, *, tenant_key: str, user_id: str,
            org_id: str | None, workspace_id: str | None, agent_type_code: str,
            title: str | None, page_context: dict | None) -> ConversationRecord:
        row = await conn.fetchrow(f"""
            INSERT INTO {self._CONV} (tenant_key, user_id, org_id, workspace_id, agent_type_code, title, page_context)
            VALUES ($1,$2,$3,$4,$5,$6,$7)
            RETURNING id::text, tenant_key, user_id::text, org_id::text, workspace_id::text,
                      agent_type_code, title, page_context, is_archived, created_at::text, updated_at::text
        """, tenant_key, user_id, org_id, workspace_id, agent_type_code, title, page_context)
        return ConversationRecord(**dict(row))

    async def get_conversation(
        self,
        conn: asyncpg.Connection,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
    ) -> ConversationRecord | None:
        row = await conn.fetchrow(f"""
            SELECT id::text, tenant_key, user_id::text, org_id::text, workspace_id::text,
                   agent_type_code, title, page_context, is_archived, created_at::text, updated_at::text
            FROM {self._CONV}
            WHERE id = $1::uuid
              AND user_id = $2::uuid
              AND tenant_key = $3
        """, conversation_id, user_id, tenant_key)
        return ConversationRecord(**dict(row)) if row else None

    async def list_conversations(
        self,
        conn: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        is_archived: bool = False,
        org_id: str | None = None,
        workspace_id: str | None = None,
        agent_type_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[ConversationRecord]:
        where = [
            "user_id = $1::uuid",
            "tenant_key = $2",
            "is_archived = $3",
        ]
        args: list[object] = [user_id, tenant_key, is_archived]
        idx = 4
        if org_id is not None:
            where.append(f"org_id = ${idx}::uuid")
            args.append(org_id)
            idx += 1
        if workspace_id is not None:
            where.append(f"workspace_id = ${idx}::uuid")
            args.append(workspace_id)
            idx += 1
        if agent_type_code is not None:
            where.append(f"agent_type_code = ${idx}")
            args.append(agent_type_code)
            idx += 1

        where_sql = " AND ".join(where)
        rows = await conn.fetch(f"""
            SELECT id::text, tenant_key, user_id::text, org_id::text, workspace_id::text,
                   agent_type_code, title, page_context, is_archived, created_at::text, updated_at::text
            FROM {self._CONV}
            WHERE {where_sql}
            ORDER BY updated_at DESC
            LIMIT ${idx} OFFSET ${idx + 1}
        """, *args, limit, offset)
        return [ConversationRecord(**dict(r)) for r in rows]

    async def archive_conversation(
        self,
        conn: asyncpg.Connection,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
    ) -> bool:
        result = await conn.execute(f"""
            UPDATE {self._CONV} SET is_archived=TRUE, updated_at=NOW()
            WHERE id = $1::uuid
              AND user_id = $2::uuid
              AND tenant_key = $3
        """, conversation_id, user_id, tenant_key)
        return result == "UPDATE 1"

    async def add_message(self, conn: asyncpg.Connection, *, conversation_id: str, role_code: str,
            content: str, token_count: int | None, model_id: str | None) -> MessageRecord:
        row = await conn.fetchrow(f"""
            INSERT INTO {self._MSG} (conversation_id, role_code, content, token_count, model_id)
            VALUES ($1,$2,$3,$4,$5)
            RETURNING id::text, conversation_id::text, role_code, content, token_count,
                      model_id, parent_message_id::text, created_at::text
        """, conversation_id, role_code, content, token_count, model_id)
        # Touch conversation updated_at
        await conn.execute(f"UPDATE {self._CONV} SET updated_at=NOW() WHERE id=$1", conversation_id)
        return MessageRecord(**dict(row))

    async def list_messages(
        self,
        conn: asyncpg.Connection,
        *,
        conversation_id: str,
        user_id: str,
        tenant_key: str,
        limit: int = 100,
    ) -> list[MessageRecord]:
        rows = await conn.fetch(f"""
            SELECT id::text, conversation_id::text, role_code, content, token_count,
                   model_id, parent_message_id::text, created_at::text
            FROM {self._MSG} m
            WHERE m.conversation_id = $1::uuid
              AND EXISTS (
                  SELECT 1
                  FROM {self._CONV} c
                  WHERE c.id = m.conversation_id
                    AND c.user_id = $2::uuid
                    AND c.tenant_key = $3
              )
            ORDER BY created_at ASC
            LIMIT $4
        """, conversation_id, user_id, tenant_key, limit)
        return [MessageRecord(**dict(r)) for r in rows]
