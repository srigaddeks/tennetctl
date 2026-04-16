"""Dashboard API for control test execution statistics and monitoring."""

from __future__ import annotations

from importlib import import_module
from pydantic import BaseModel, Field

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger

SANDBOX_SCHEMA = '"15_sandbox"'
GRC_SCHEMA = '"05_grc_library"'


class TestExecutionSummary(BaseModel):
    total_executions: int = 0
    pass_count: int = 0
    fail_count: int = 0
    error_count: int = 0
    pass_rate: float = 0.0
    last_execution_at: str | None = None


class ConnectorHealthSummary(BaseModel):
    connector_id: str
    connector_name: str | None = None
    connector_type_code: str
    health_status: str
    test_count: int = 0
    last_pass_count: int = 0
    last_fail_count: int = 0
    last_execution_at: str | None = None
    collection_schedule: str = "manual"
    last_collected_at: str | None = None


class RecentExecution(BaseModel):
    execution_id: str
    test_code: str | None = None
    test_name: str | None = None
    result_status: str
    result_summary: str | None = None
    executed_at: str
    connector_type: str | None = None
    connector_id: str | None = None
    connector_name: str | None = None


class OpenIssue(BaseModel):
    task_id: str
    title: str | None = None
    priority_code: str
    entity_id: str | None = None
    created_at: str


class MonitoringDashboardResponse(BaseModel):
    execution_summary: TestExecutionSummary
    connector_health: list[ConnectorHealthSummary] = Field(default_factory=list)
    recent_executions: list[RecentExecution] = Field(default_factory=list)
    open_issues: list[OpenIssue] = Field(default_factory=list)
    total_promoted_tests: int = 0
    total_connectors: int = 0


async def get_monitoring_dashboard(
    pool: DatabasePool, org_id: str, workspace_id: str | None = None
) -> MonitoringDashboardResponse:
    """Aggregate monitoring data for the dashboard, scoped to org and optionally workspace."""
    ws_filter = (
        "AND pt.workspace_id = $2::UUID" if workspace_id else ""
    )  # queries with pt alias
    ws_filter_bare = (
        "AND workspace_id = $2::UUID" if workspace_id else ""
    )  # queries without alias
    ws_filter_fallback = (
        "AND pt.workspace_id = $2::UUID" if workspace_id else ""
    )  # fallback for org_tests CTEs
    ws_args_pt = (org_id, workspace_id) if workspace_id else (org_id,)

    async with pool.acquire() as conn:
        # 1. Execution summary — sandbox runs scoped to workspace
        exec_row = await conn.fetchrow(
            f"""
            WITH all_runs AS (
                SELECT result_code AS result_status, completed_at AS executed_at
                FROM {SANDBOX_SCHEMA}."25_trx_sandbox_runs" r
                JOIN {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt ON pt.source_signal_id = r.signal_id
                WHERE pt.org_id = $1 {ws_filter}
                  AND r.completed_at >= NOW() - INTERVAL '30 days'
            )
            SELECT
                COUNT(*)::int AS total,
                COUNT(*) FILTER (WHERE result_status = 'pass')::int AS pass_count,
                COUNT(*) FILTER (WHERE result_status = 'fail')::int AS fail_count,
                COUNT(*) FILTER (WHERE result_status IN ('error', 'partial', 'warning'))::int AS error_count,
                MAX(executed_at) AS last_execution_at
            FROM all_runs
        """,
            *ws_args_pt,
        )

        total_exec = exec_row["total"] if exec_row else 0
        pass_count = exec_row["pass_count"] if exec_row else 0
        fail_count = exec_row["fail_count"] if exec_row else 0
        error_count = exec_row["error_count"] if exec_row else 0
        pass_rate = round((pass_count / total_exec * 100), 1) if total_exec > 0 else 0.0

        execution_summary = TestExecutionSummary(
            total_executions=total_exec,
            pass_count=pass_count,
            fail_count=fail_count,
            error_count=error_count,
            pass_rate=pass_rate,
            last_execution_at=str(exec_row["last_execution_at"])
            if exec_row and exec_row["last_execution_at"]
            else None,
        )

        # 2. Connector health — workspace-scoped tests, fallback to org-scoped
        connector_rows = await conn.fetch(
            f"""
            WITH ws_tests AS (
                SELECT pt.id, pt.linked_asset_id, pt.source_signal_id
                FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt
                WHERE pt.org_id = $1 {ws_filter}
                  AND pt.is_active = TRUE AND pt.is_deleted = FALSE
            ),
            org_tests AS (
                SELECT pt.id, pt.linked_asset_id, pt.source_signal_id
                FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt
                WHERE pt.org_id = $1 {ws_filter_fallback}
                  AND pt.is_active = TRUE AND pt.is_deleted = FALSE
                  AND NOT EXISTS (SELECT 1 FROM ws_tests)
            ),
            all_tests AS (
                SELECT * FROM ws_tests UNION ALL SELECT * FROM org_tests
            )
            SELECT
                ci.id AS connector_id,
                ci.connector_type_code,
                ci.health_status,
                ci.collection_schedule,
                ci.last_collected_at,
                MAX(CASE WHEN p.property_key = 'name' THEN p.property_value END) AS connector_name,
                COUNT(DISTINCT at2.id)::int AS test_count,
                COUNT(DISTINCT CASE WHEN sr.result_code = 'pass' THEN sr.id END)::int AS last_pass_count,
                COUNT(DISTINCT CASE WHEN sr.result_code = 'fail' THEN sr.id END)::int AS last_fail_count,
                MAX(sr.completed_at) AS last_execution_at
            FROM all_tests at2
            JOIN {SANDBOX_SCHEMA}."20_fct_connector_instances" ci
                ON ci.id = at2.linked_asset_id AND ci.is_deleted = FALSE AND ci.is_draft = FALSE
            LEFT JOIN {SANDBOX_SCHEMA}."40_dtl_connector_instance_properties" p
                ON p.connector_instance_id = ci.id
            LEFT JOIN {SANDBOX_SCHEMA}."25_trx_sandbox_runs" sr
                ON sr.signal_id = at2.source_signal_id
                AND sr.completed_at >= NOW() - INTERVAL '7 days'
            GROUP BY ci.id
            ORDER BY ci.id
        """,
            org_id,
            workspace_id,
        )

        connector_health = [
            ConnectorHealthSummary(
                connector_id=str(r["connector_id"]),
                connector_name=r["connector_name"],
                connector_type_code=r["connector_type_code"],
                health_status=r["health_status"] or "unknown",
                test_count=r["test_count"],
                last_pass_count=r["last_pass_count"],
                last_fail_count=r["last_fail_count"],
                last_execution_at=str(r["last_execution_at"])
                if r["last_execution_at"]
                else None,
                collection_schedule=r["collection_schedule"] or "manual",
                last_collected_at=str(r["last_collected_at"])
                if r["last_collected_at"]
                else None,
            )
            for r in connector_rows
        ]

        # 3. Recent executions — combine GRC + sandbox auto-runs
        # Build test_code lookup with fallback logic
        test_code_map: dict[str, dict] = {}
        pt_rows = await conn.fetch(
            f"""
            WITH ws_tests AS (
                SELECT pt.id, pt.test_code, pt.source_signal_id, pt.linked_asset_id
                FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt
                WHERE pt.org_id = $1 {ws_filter}
                  AND pt.is_active = TRUE AND pt.is_deleted = FALSE
            ),
            org_tests AS (
                SELECT pt.id, pt.test_code, pt.source_signal_id, pt.linked_asset_id
                FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt
                WHERE pt.org_id = $1 {ws_filter_fallback}
                  AND pt.is_active = TRUE AND pt.is_deleted = FALSE
                  AND NOT EXISTS (SELECT 1 FROM ws_tests)
            ),
            all_tests AS (
                SELECT * FROM ws_tests UNION ALL SELECT * FROM org_tests
            )
            SELECT at2.id::text AS pt_id, at2.test_code, at2.source_signal_id::text,
                   at2.linked_asset_id, ci.connector_type_code,
                   MAX(CASE WHEN pp.property_key = 'name' THEN pp.property_value END) AS test_name,
                   MAX(CASE WHEN cp.property_key = 'name' THEN cp.property_value END) AS connector_name
            FROM all_tests at2
            LEFT JOIN {SANDBOX_SCHEMA}."36_dtl_promoted_test_properties" pp ON pp.test_id = at2.id
            LEFT JOIN {SANDBOX_SCHEMA}."20_fct_connector_instances" ci ON ci.id = at2.linked_asset_id
            LEFT JOIN {SANDBOX_SCHEMA}."40_dtl_connector_instance_properties" cp ON cp.connector_instance_id = ci.id
            GROUP BY at2.id, at2.test_code, at2.source_signal_id, at2.linked_asset_id, ci.connector_type_code
        """,
            *ws_args_pt,
        )
        signal_to_test: dict[str, dict] = {}
        for pr in pt_rows:
            info = {
                "test_code": pr["test_code"],
                "test_name": pr["test_name"],
                "connector_type": pr["connector_type_code"],
                "connector_id": str(pr["linked_asset_id"])
                if pr["linked_asset_id"]
                else None,
                "connector_name": pr["connector_name"],
            }
            test_code_map[pr["test_code"]] = info
            if pr["source_signal_id"]:
                signal_to_test[pr["source_signal_id"]] = info

        # Get sandbox auto-run results with fallback logic
        recent_rows = await conn.fetch(
            f"""
            WITH ws_tests AS (
                SELECT pt.id, pt.source_signal_id
                FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt
                WHERE pt.org_id = $1 {ws_filter}
                  AND pt.is_active = TRUE AND pt.is_deleted = FALSE
            ),
            org_tests AS (
                SELECT pt.id, pt.source_signal_id
                FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests" pt
                WHERE pt.org_id = $1 {ws_filter_fallback}
                  AND pt.is_active = TRUE AND pt.is_deleted = FALSE
                  AND NOT EXISTS (SELECT 1 FROM ws_tests)
            ),
            all_tests AS (
                SELECT * FROM ws_tests UNION ALL SELECT * FROM org_tests
            )
            SELECT r.id::text, r.result_code, r.result_summary,
                   r.completed_at, r.signal_id::text
            FROM {SANDBOX_SCHEMA}."25_trx_sandbox_runs" r
            JOIN all_tests at2 ON at2.source_signal_id = r.signal_id
            WHERE r.completed_at IS NOT NULL
            ORDER BY r.completed_at DESC LIMIT 20
        """,
            *ws_args_pt,
        )

        grc_rows: list = []

        recent_executions = []
        seen_ids: set[str] = set()

        # Sandbox runs first (most recent)
        for r in recent_rows:
            info = signal_to_test.get(r["signal_id"], {})
            recent_executions.append(
                RecentExecution(
                    execution_id=r["id"],
                    test_code=info.get("test_code"),
                    test_name=info.get("test_name") or info.get("test_code"),
                    result_status=r["result_code"] or "unknown",
                    result_summary=r["result_summary"],
                    executed_at=str(r["completed_at"]),
                    connector_type=info.get("connector_type"),
                    connector_id=info.get("connector_id"),
                    connector_name=info.get("connector_name"),
                )
            )
            seen_ids.add(r["id"])

        # GRC executions (scoped to org/workspace)
        for r in grc_rows:
            if r["id"] in seen_ids:
                continue
            notes = r.get("notes") or ""
            test_code = (
                notes.replace("Executed promoted test ", "").strip()
                if notes.startswith("Executed promoted test ")
                else None
            )
            info = test_code_map.get(test_code, {}) if test_code else {}
            recent_executions.append(
                RecentExecution(
                    execution_id=r["id"],
                    test_code=test_code,
                    test_name=info.get("test_name") or test_code,
                    result_status=r["result_status"],
                    executed_at=str(r["executed_at"]),
                    connector_type=info.get("connector_type"),
                    connector_id=info.get("connector_id"),
                    connector_name=info.get("connector_name"),
                )
            )

        # Sort by most recent
        recent_executions.sort(key=lambda x: x.executed_at, reverse=True)
        recent_executions = recent_executions[:20]

        # 4. Open issues (from 09_issues schema)
        issue_rows = await conn.fetch(
            f"""
            SELECT id, issue_code, test_name, test_code, severity_code, result_summary, status_code, created_at
            FROM "09_issues"."10_fct_issues"
            WHERE org_id = $1 {ws_filter_bare}
              AND status_code NOT IN ('closed', 'accepted', 'verified')
              AND is_active = TRUE AND is_deleted = FALSE
            ORDER BY created_at DESC LIMIT 20
        """,
            *ws_args_pt,
        )

        open_issues = [
            OpenIssue(
                task_id=str(r["id"]),
                title=r["test_name"] or r["test_code"] or r["issue_code"],
                priority_code=r["severity_code"],
                entity_id=r["issue_code"],
                created_at=str(r["created_at"]),
            )
            for r in issue_rows
        ]

        # 5. Counts
        test_count_row = await conn.fetchrow(
            f"""
            SELECT COUNT(*)::int AS cnt
            FROM {SANDBOX_SCHEMA}."35_fct_promoted_tests"
            WHERE org_id = $1 {ws_filter_bare} AND is_active = TRUE AND is_deleted = FALSE
        """,
            *ws_args_pt,
        )

        connector_count_row = await conn.fetchrow(
            f"""
            SELECT COUNT(*)::int AS cnt
            FROM {SANDBOX_SCHEMA}."20_fct_connector_instances"
            WHERE org_id = $1 AND is_deleted = FALSE AND is_draft = FALSE
        """,
            org_id,
        )

        return MonitoringDashboardResponse(
            execution_summary=execution_summary,
            connector_health=connector_health,
            recent_executions=recent_executions,
            open_issues=open_issues,
            total_promoted_tests=test_count_row["cnt"] if test_count_row else 0,
            total_connectors=connector_count_row["cnt"] if connector_count_row else 0,
        )
