from __future__ import annotations
import asyncpg

class ReportingRepository:
    _SCHEMA = '"20_ai"'

    async def get_summary(self, conn: asyncpg.Connection, *, tenant_key: str) -> dict:
        row = await conn.fetchrow(f"""
            SELECT
                (SELECT COUNT(*) FROM {self._SCHEMA}."20_fct_conversations" WHERE tenant_key=$1) AS total_conversations,
                (SELECT COUNT(*) FROM {self._SCHEMA}."21_fct_messages" m
                 JOIN {self._SCHEMA}."20_fct_conversations" c ON c.id=m.conversation_id WHERE c.tenant_key=$1) AS total_messages,
                (SELECT COUNT(*) FROM {self._SCHEMA}."24_fct_agent_runs" r
                 JOIN {self._SCHEMA}."20_fct_conversations" c ON c.id=r.conversation_id WHERE c.tenant_key=$1) AS total_agent_runs,
                (SELECT COALESCE(SUM(tokens_used),0) FROM {self._SCHEMA}."29_trx_token_usage" WHERE tenant_key=$1) AS total_tokens_used,
                (SELECT COALESCE(SUM(cost_usd),0) FROM {self._SCHEMA}."29_trx_token_usage" WHERE tenant_key=$1) AS total_cost_usd,
                (SELECT COUNT(*) FROM {self._SCHEMA}."23_fct_approval_requests" WHERE tenant_key=$1 AND status_code='pending') AS active_approvals,
                (SELECT COUNT(*) FROM {self._SCHEMA}."31_trx_guardrail_events" WHERE tenant_key=$1 AND occurred_at>=NOW()-INTERVAL '24 hours') AS guardrail_events_today,
                (SELECT COUNT(*) FROM {self._SCHEMA}."45_fct_job_queue" WHERE tenant_key=$1 AND status_code='queued') AS jobs_queued,
                (SELECT COUNT(*) FROM {self._SCHEMA}."45_fct_job_queue" WHERE tenant_key=$1 AND status_code='running') AS jobs_running
        """, tenant_key)
        return dict(row)

    async def get_agent_run_stats(self, conn: asyncpg.Connection, *, tenant_key: str) -> list[dict]:
        rows = await conn.fetch(f"""
            SELECT r.agent_type_code, at.name AS agent_type_name,
                   COUNT(*) AS run_count,
                   SUM(r.total_tokens)::bigint AS total_tokens,
                   SUM(r.cost_usd)::float AS total_cost_usd,
                   AVG(EXTRACT(EPOCH FROM (r.completed_at - r.started_at))*1000)::float AS avg_duration_ms,
                   ROUND(COUNT(*) FILTER(WHERE r.status='failed') * 100.0 / NULLIF(COUNT(*),0), 2)::float AS error_rate_pct
            FROM {self._SCHEMA}."24_fct_agent_runs" r
            JOIN {self._SCHEMA}."20_fct_conversations" c ON c.id=r.conversation_id
            LEFT JOIN {self._SCHEMA}."02_dim_agent_types" at ON at.code=r.agent_type_code
            WHERE c.tenant_key=$1
            GROUP BY r.agent_type_code, at.name
            ORDER BY run_count DESC
        """, tenant_key)
        return [dict(r) for r in rows]
