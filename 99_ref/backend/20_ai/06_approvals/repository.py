from __future__ import annotations
import asyncpg
from .models import ApprovalRecord

class ApprovalRepository:
    _SCHEMA = '"20_ai"'
    _TABLE = f'{_SCHEMA}."23_fct_approval_requests"'
    _VIEW  = f'{_SCHEMA}."61_vw_approval_queue"'

    async def create_approval(self, conn: asyncpg.Connection, *, tenant_key: str, requester_id: str,
            org_id: str | None, tool_name: str, tool_category: str, entity_type: str | None,
            operation: str | None, payload_json: dict, diff_json: dict | None,
            expires_at) -> ApprovalRecord:
        row = await conn.fetchrow(f"""
            INSERT INTO {self._TABLE} (tenant_key, requester_id, org_id, tool_name, tool_category,
                entity_type, operation, payload_json, diff_json, expires_at)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::TIMESTAMPTZ)
            RETURNING id::text, tenant_key, requester_id::text, org_id::text, approver_id::text,
                status_code, tool_name, tool_category, entity_type, operation, payload_json, diff_json,
                rejection_reason, expires_at::text, approved_at::text, executed_at::text,
                created_at::text, updated_at::text
        """, tenant_key, requester_id, org_id, tool_name, tool_category,
             entity_type, operation, payload_json, diff_json, expires_at)
        return ApprovalRecord(**dict(row))

    async def get_approval(self, conn: asyncpg.Connection, *, approval_id: str, tenant_key: str) -> ApprovalRecord | None:
        row = await conn.fetchrow(f"""
            SELECT id::text, tenant_key, requester_id::text, org_id::text, approver_id::text,
                status_code, tool_name, tool_category, entity_type, operation, payload_json, diff_json,
                rejection_reason, expires_at::text, approved_at::text, executed_at::text,
                created_at::text, updated_at::text
            FROM {self._TABLE} WHERE id=$1 AND tenant_key=$2
        """, approval_id, tenant_key)
        return ApprovalRecord(**dict(row)) if row else None

    async def list_approvals(self, conn: asyncpg.Connection, *, tenant_key: str,
            requester_id: str | None, status_code: str | None,
            limit: int = 50, offset: int = 0) -> list[dict]:
        conditions = ["tenant_key = $1"]
        params: list = [tenant_key]
        idx = 2
        if requester_id:
            conditions.append(f"requester_id = ${idx}"); params.append(requester_id); idx += 1
        if status_code:
            conditions.append(f"status_code = ${idx}"); params.append(status_code); idx += 1
        params.extend([limit, offset])
        rows = await conn.fetch(f"""
            SELECT id::text, tenant_key, requester_id::text, org_id::text, approver_id::text,
                status_code, status_name, tool_name, tool_category, entity_type, operation,
                payload_json, diff_json, rejection_reason, expires_at::text, approved_at::text,
                executed_at::text, created_at::text, updated_at::text, is_overdue
            FROM {self._VIEW}
            WHERE {" AND ".join(conditions)}
            ORDER BY created_at DESC LIMIT ${idx} OFFSET ${idx+1}
        """, *params)
        return [dict(r) for r in rows]

    async def transition_status(self, conn: asyncpg.Connection, *, approval_id: str,
            new_status: str, approver_id: str | None, rejection_reason: str | None) -> ApprovalRecord | None:
        sets = ["status_code=$2", "updated_at=NOW()"]
        params: list = [approval_id, new_status]
        idx = 3
        if approver_id:
            sets.append(f"approver_id=${idx}"); params.append(approver_id); idx += 1
        if rejection_reason:
            sets.append(f"rejection_reason=${idx}"); params.append(rejection_reason); idx += 1
        if new_status == "approved":
            sets.append("approved_at=NOW()")
        elif new_status == "executed":
            sets.append("executed_at=NOW()")
        row = await conn.fetchrow(f"""
            UPDATE {self._TABLE} SET {', '.join(sets)} WHERE id=$1
            RETURNING id::text, tenant_key, requester_id::text, org_id::text, approver_id::text,
                status_code, tool_name, tool_category, entity_type, operation, payload_json, diff_json,
                rejection_reason, expires_at::text, approved_at::text, executed_at::text,
                created_at::text, updated_at::text
        """, *params)
        return ApprovalRecord(**dict(row)) if row else None

    async def expire_pending(self, conn: asyncpg.Connection) -> int:
        result = await conn.execute(f"""
            UPDATE {self._TABLE} SET status_code='expired', updated_at=NOW()
            WHERE status_code='pending' AND expires_at < NOW()
        """)
        return int(result.split()[-1])
