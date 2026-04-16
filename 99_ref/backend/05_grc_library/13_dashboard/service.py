from __future__ import annotations

import asyncio
from importlib import import_module
from .schemas import (
    GrcDashboardResponse, TestStats, TaskForecast, FrameworkStatus, 
    EngineerDashboardResponse, ExecutiveDashboardResponse,
    PortfolioEngagement, Milestone
)

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
require_permission = _perm_check_module.require_permission

_LOGGER = get_logger("backend.grc.dashboard")

@instrument_class_methods(namespace="grc.dashboard.service", logger_name="backend.grc.dashboard.instrumentation")
class DashboardService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache

    async def get_dashboard(self, *, user_id: str, tenant_key: str, org_id: str | None = None, engagement_id: str | None = None) -> GrcDashboardResponse:
        async with self._database_pool.acquire() as conn:
            # 1. Permission check (scoped to org if provided)
            await require_permission(conn, user_id, "controls.view", scope_org_id=org_id)

            # 2. Execute aggregator queries sequentially
            test_stats = await self._get_test_stats(conn, tenant_key, org_id, engagement_id)
            task_forecast = await self._get_task_forecast(conn, tenant_key, org_id, engagement_id)
            framework_status = await self._get_framework_status(conn, tenant_key, org_id, engagement_id)
            trust_score = await self._calculate_trust_score(conn, tenant_key, org_id, engagement_id)

            # 3. Fetch recent activity from audit events
            # If scoped to engagement, we filter for events related to that engagement's framework, tasks, or the engagement itself
            activity_query = """
                SELECT 
                    e.event_type, e.entity_type, e.occurred_at::text as occurred_at,
                    COALESCE(u.email, 'System') as actor_name
                FROM "03_auth_manage"."40_aud_events" e
                LEFT JOIN "03_auth_manage"."42_vw_auth_users" u ON e.actor_id = u.user_id
            """
            
            args = [tenant_key]
            where_clauses = ["e.tenant_key = $1"]
            
            if engagement_id:
                activity_query += """
                LEFT JOIN "12_engagements"."10_fct_audit_engagements" eng ON eng.id = $2::uuid
                """
                where_clauses.append("""
                    (e.entity_id = $2::uuid OR 
                     EXISTS (SELECT 1 FROM "03_auth_manage"."41_dtl_audit_event_properties" p WHERE p.event_id = e.id AND p.meta_key = 'engagement_id' AND p.meta_value = $2::text) OR
                     (e.entity_type = 'framework' AND e.entity_id = eng.framework_id) OR
                     (e.entity_type = 'task' AND EXISTS (SELECT 1 FROM "03_auth_manage"."41_dtl_audit_event_properties" p WHERE p.event_id = e.id AND p.meta_key = 'engagement_id' AND p.meta_value = $2::text)))
                """)
                args.append(engagement_id)
            elif org_id:
                # Security Fix: Scope activity stream to the selected organization (Lead Dashboard)
                where_clauses.append("""
                    (
                        (e.entity_type = 'org' AND e.entity_id = $2::uuid)
                        OR EXISTS (
                            SELECT 1 FROM "03_auth_manage"."41_dtl_audit_event_properties" p
                            WHERE p.event_id = e.id AND p.meta_key = 'org_id' AND p.meta_value = $2::text
                        )
                        OR EXISTS (
                            SELECT 1 FROM "12_engagements"."10_fct_audit_engagements" sub_eng
                            WHERE sub_eng.org_id = $2::uuid AND (
                                (e.entity_type = 'engagement' AND e.entity_id = sub_eng.id) OR
                                (e.entity_type = 'framework' AND e.entity_id = sub_eng.framework_id) OR
                                EXISTS (
                                    SELECT 1 FROM "03_auth_manage"."41_dtl_audit_event_properties" p2
                                    WHERE p2.event_id = e.id AND p2.meta_key = 'engagement_id' AND p2.meta_value = sub_eng.id::text
                                )
                            )
                        )
                    )
                """)
                args.append(org_id)


            
            activity_query += " WHERE " + " AND ".join(where_clauses)
            activity_query += " ORDER BY e.occurred_at DESC LIMIT 15"
            
            activity_rows = await conn.fetch(activity_query, *args)
            recent_activity = [dict(r) for r in activity_rows]

            return GrcDashboardResponse(
                trust_score=trust_score,
                test_stats=test_stats,
                task_forecast=task_forecast,
                framework_status=framework_status,
                recent_activity=recent_activity,
            )

    async def _get_test_stats(self, conn, tenant_key: str, org_id: str | None = None, engagement_id: str | None = None) -> TestStats:
        query = """
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE result_status = 'pass') as passing,
                COUNT(*) FILTER (WHERE result_status = 'fail') as failing
            FROM "05_grc_library"."15_fct_test_executions" e
            JOIN "05_grc_library"."13_fct_controls" c ON c.id = e.control_id
            JOIN "05_grc_library"."10_fct_frameworks" f ON f.id = c.framework_id
        """
        args = [tenant_key]
        where_clauses = ["e.tenant_key = $1", "e.is_deleted = FALSE"]
        
        if engagement_id:
            query += " JOIN \"12_engagements\".\"10_fct_audit_engagements\" eng ON eng.framework_id = f.id"
            where_clauses.append(f"eng.id = ${len(args) + 1}::uuid")
            args.append(engagement_id)
        else:
            # Enforce engagement-linked frameworks only
            query += """
                JOIN "12_engagements"."10_fct_audit_engagements" e_link ON e_link.framework_id = f.id
            """
            if org_id:
                where_clauses.append(f"e_link.org_id = ${len(args) + 1}::uuid")
                args.append(org_id)
            
        if org_id:
            where_clauses.append(f"(f.scope_org_id = ${len(args) + 1}::uuid OR f.scope_org_id IS NULL)")
            args.append(org_id)
            
        query += " WHERE " + " AND ".join(where_clauses)
            
        row = await conn.fetchrow(query, *args)
        if not row:
            return TestStats(pass_rate=0.0, total_tests=0, failing_tests=0)

        total = row["total"] or 0
        passing = row["passing"] or 0
        failing = row["failing"] or 0
        
        pass_rate = (passing / total * 100) if total > 0 else 0
        return TestStats(pass_rate=pass_rate, total_tests=total, failing_tests=failing)

    async def _get_task_forecast(self, conn, tenant_key: str, org_id: str | None = None, engagement_id: str | None = None) -> TaskForecast:
        query = """
            SELECT
                COUNT(*) FILTER (WHERE due_date < NOW() AND status_code NOT IN ('resolved', 'cancelled')) as overdue,
                COUNT(*) FILTER (WHERE due_date BETWEEN NOW() AND NOW() + INTERVAL '7 days' AND status_code NOT IN ('resolved', 'cancelled')) as due_week,
                COUNT(*) FILTER (WHERE status_code NOT IN ('resolved', 'cancelled')) as total_pending
            FROM "08_tasks"."10_fct_tasks" t
        """
        args = [tenant_key]
        where_clauses = ["t.tenant_key = $1", "t.is_deleted = FALSE"]
        
        if engagement_id:
            where_clauses.append(f"(t.entity_id = ${len(args) + 1}::uuid AND t.entity_type = 'engagement')")
            args.append(engagement_id)
        else:
            # Enforce: only show tasks that belong to an engagement
            where_clauses.append("(t.entity_type = 'engagement' AND t.entity_id IS NOT NULL)")
            if org_id:
                where_clauses.append(f"t.org_id = ${len(args) + 1}::uuid")
                args.append(org_id)
            
        query += " WHERE " + " AND ".join(where_clauses)
            
        row = await conn.fetchrow(query, *args)
        if not row:
            return TaskForecast(overdue=0, due_this_week=0, total_pending=0)

        return TaskForecast(
            overdue=row["overdue"] or 0,
            due_this_week=row["due_week"] or 0,
            total_pending=row["total_pending"] or 0
        )

    async def _get_framework_status(self, conn, tenant_key: str, org_id: str | None = None, engagement_id: str | None = None) -> list[FrameworkStatus]:
        """Derive framework readiness from actual audit engagement verification data."""
        query = """
            SELECT
                e.id::text,
                COALESCE(name_prop.property_value, e.engagement_code) AS name,
                (SELECT count(*)::int
                 FROM "05_grc_library"."31_lnk_framework_version_controls" lvc
                 JOIN "05_grc_library"."16_fct_framework_deployments" fd
                   ON fd.id = e.framework_deployment_id
                 WHERE lvc.framework_version_id = fd.deployed_version_id
                ) AS total_controls,
                (SELECT count(*)::int
                 FROM "12_engagements"."21_trx_auditor_verifications" v
                 WHERE v.engagement_id = e.id
                ) AS verified_controls
            FROM "12_engagements"."10_fct_audit_engagements" e
            LEFT JOIN "12_engagements"."22_dtl_engagement_properties" name_prop
                ON name_prop.engagement_id = e.id AND name_prop.property_key = 'engagement_name'
        """
        args = [tenant_key]
        where_clauses = ["e.tenant_key = $1", "e.is_deleted = FALSE", "e.is_active = TRUE"]
        
        if engagement_id:
            where_clauses.append(f"e.id = ${len(args) + 1}::uuid")
            args.append(engagement_id)
            
        if org_id:
            where_clauses.append(f"e.org_id = ${len(args) + 1}::uuid")
            args.append(org_id)
            
        query += " WHERE " + " AND ".join(where_clauses)
        query += " ORDER BY e.created_at DESC LIMIT 10"
        
        rows = await conn.fetch(query, *args)
        return [
            FrameworkStatus(
                id=r["id"],
                name=r["name"],
                completion_percentage=(
                    float(r["verified_controls"]) / float(r["total_controls"]) * 100.0
                    if r["total_controls"] and r["total_controls"] > 0
                    else 0.0
                )
            ) for r in rows
        ]

    async def _calculate_trust_score(self, conn, tenant_key: str, org_id: str | None = None, engagement_id: str | None = None) -> float:
        # Weighted average of controls that have at least one PASSED test in the last 30 days
        query = """
            WITH control_status AS (
                SELECT 
                    c.id,
                    EXISTS (
                        SELECT 1 FROM "05_grc_library"."15_fct_test_executions" e
                        WHERE e.control_id = c.id 
                          AND e.result_status = 'pass' 
                          AND e.executed_at > NOW() - INTERVAL '30 days'
                          AND e.is_deleted = FALSE
                    ) as is_compliant
                FROM "05_grc_library"."13_fct_controls" c
                JOIN "05_grc_library"."10_fct_frameworks" f ON f.id = c.framework_id
        """
        args = [tenant_key]
        where_clauses = ["c.tenant_key = $1", "c.is_deleted = FALSE"]
        
        if engagement_id:
            query += " JOIN \"12_engagements\".\"10_fct_audit_engagements\" eng ON eng.framework_id = f.id"
            where_clauses.append(f"eng.id = ${len(args) + 1}::uuid")
            args.append(engagement_id)
        else:
            # Enforce engagement-linked frameworks only
            query += """
                JOIN "12_engagements"."10_fct_audit_engagements" e_link ON e_link.framework_id = f.id
            """
            if org_id:
                where_clauses.append(f"e_link.org_id = ${len(args) + 1}::uuid")
                args.append(org_id)
            
        if org_id:
            where_clauses.append(f"(f.scope_org_id = ${len(args) + 1}::uuid OR f.scope_org_id IS NULL)")
            args.append(org_id)
            
        query += " WHERE " + " AND ".join(where_clauses)
        query += """
            )
            SELECT 
                (COUNT(*) FILTER (WHERE is_compliant = TRUE) * 100.0 / NULLIF(COUNT(*), 0)) as score
            FROM control_status
        """
        
        row = await conn.fetchrow(query, *args)
        if not row or row["score"] is None:
            return 0.0
        return float(row["score"])

    async def get_engineer_dashboard(self, *, user_id: str, tenant_key: str, org_id: str | None = None) -> EngineerDashboardResponse:
        async with self._database_pool.acquire() as conn:
            # 1. Permission check (scoped to org if provided)
            await require_permission(conn, user_id, "controls.view", scope_org_id=org_id)

            # Fetch count of controls where user is owner
            owned_count = await conn.fetchval(
                """
                SELECT COUNT(*) 
                FROM "05_grc_library"."13_fct_controls" c
                LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp ON cp.control_id = c.id
                WHERE cp.property_key = 'owner_user_id' AND cp.property_value = $1
                  AND c.tenant_key = $2 AND c.is_deleted = FALSE
                """,
                user_id, tenant_key
            )

            # 2. Fetch evidence task breakdown for the user
            conditions = ["tenant_key = $1", "is_deleted = FALSE", "assignee_user_id = $2::uuid"]
            args = [tenant_key, user_id]
            if org_id:
                conditions.append("org_id = $3::uuid")
                args.append(org_id)
            
            where_clause = " AND ".join(conditions)

            task_rows = await conn.fetch(
                f"""
                SELECT status_code, COUNT(*) as count
                FROM "08_tasks"."10_fct_tasks"
                WHERE {where_clause}
                GROUP BY status_code
                """,
                *args
            )
            tasks_by_status = {r["status_code"]: r["count"] for r in task_rows} if task_rows else {}
            
            # 3. Sum of 'pending' tasks
            pending_count = sum(count for sc, count in tasks_by_status.items() if sc not in ('resolved', 'cancelled'))

            return EngineerDashboardResponse(
                owned_controls_count=owned_count or 0,
                pending_tasks_count=pending_count,
                tasks_by_status=tasks_by_status,
                upcoming_deadlines=[]
            )

    async def get_executive_dashboard(self, *, user_id: str, tenant_key: str, org_id: str | None = None) -> ExecutiveDashboardResponse:
        async with self._database_pool.acquire() as conn:
            # 1. Permission (wider than engineer)
            await require_permission(conn, user_id, "controls.view", scope_org_id=org_id)

            # 2. Portfolio query (active engagements)
            # This handles audit progress across frameworks
            portfolio_query = """
                SELECT
                    e.id::text,
                    COALESCE(name_prop.property_value, e.engagement_code) AS engagement_name,
                    COALESCE(e.status_code, 'active') as status_code,
                    (SELECT count(*)::int
                     FROM "05_grc_library"."31_lnk_framework_version_controls" lvc
                     JOIN "05_grc_library"."16_fct_framework_deployments" fd
                       ON fd.id = e.framework_deployment_id
                     WHERE lvc.framework_version_id = fd.deployed_version_id
                    ) AS total_controls,
                    (SELECT count(*)::int
                     FROM "12_engagements"."21_trx_auditor_verifications" v
                     WHERE v.engagement_id = e.id
                    ) AS verified_controls
                FROM "12_engagements"."10_fct_audit_engagements" e
                LEFT JOIN "12_engagements"."22_dtl_engagement_properties" name_prop
                    ON name_prop.engagement_id = e.id AND name_prop.property_key = 'engagement_name'
                WHERE e.tenant_key = $1 AND e.is_deleted = FALSE AND e.is_active = TRUE
            """
            args = [tenant_key]
            if org_id:
                portfolio_query += " AND e.org_id = $2::uuid"
                args.append(org_id)

            rows = await conn.fetch(portfolio_query, *args)
            
            portfolio = []
            total_ctrl = 0
            total_verified = 0
            audit_status = "On Track"

            for r in rows:
                t_ctrl = r["total_controls"] or 0
                v_ctrl = r["verified_controls"] or 0
                total_ctrl += t_ctrl
                total_verified += v_ctrl
                
                progress = (float(v_ctrl) / float(t_ctrl) * 100.0) if t_ctrl > 0 else 0.0
                status = "On Track"
                if r["status_code"] in ('delayed', 'blocked'):
                    status = "Delayed"
                    audit_status = "At Risk"
                elif r["status_code"] == 'completed':
                    status = "Completed"
                
                portfolio.append(PortfolioEngagement(
                    id=r["id"],
                    name=r["engagement_name"],
                    progress=progress,
                    risk_level="Low" if progress > 50 else "Medium",
                    status=status
                ))

            # 3. Quick Stats
            controls_verified_pct = (float(total_verified) / float(total_ctrl) * 100.0) if total_ctrl > 0 else 0.0
            trust_score = await self._calculate_trust_score(conn, tenant_key, org_id)

            # 4. Findings (pending tasks of type 'finding' or similar)
            # Defaulting to open/in_progress tasks
            findings_count = await conn.fetchval(
                f"""
                SELECT COUNT(*)
                FROM "08_tasks"."40_vw_task_detail"
                WHERE tenant_key = $1 AND is_deleted = FALSE 
                  AND status_code NOT IN ('resolved', 'cancelled')
                  {f"AND org_id = $2::uuid" if org_id else ""}
                """,
                *args
            )

            # 5. Milestones (Upcoming task deadlines)
            milestones_query = f"""
                SELECT 
                    t.id::text, 
                    COALESCE(p.property_value, t.task_type_code) as title, 
                    t.due_date::text as date, 
                    t.status_code as status
                FROM "08_tasks"."10_fct_tasks" t
                LEFT JOIN "08_tasks"."20_dtl_task_properties" p 
                    ON p.task_id = t.id AND p.property_key = 'title'
                WHERE t.tenant_key = $1 AND t.is_deleted = FALSE AND t.due_date IS NOT NULL
                  AND t.status_code NOT IN ('resolved', 'cancelled')
                  {f"AND t.org_id = $2::uuid" if org_id else ""}
                ORDER BY t.due_date ASC LIMIT 5
            """
            m_rows = await conn.fetch(milestones_query, *args)
            milestones = [
                Milestone(
                    id=r["id"],
                    title=r["title"],
                    date=r["date"],
                    status="active" if i == 0 else "setup"
                ) for i, r in enumerate(m_rows)
            ]

            return ExecutiveDashboardResponse(
                trust_score=trust_score,
                controls_verified_percentage=controls_verified_pct,
                pending_findings_count=findings_count or 0,
                audit_status=audit_status,
                portfolio=portfolio,
                milestones=milestones
            )

