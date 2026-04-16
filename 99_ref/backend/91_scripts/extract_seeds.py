#!/usr/bin/env python3
"""
Seed Data Extractor — kcontrol
===============================
Extracts all system/dimension/config seed data from a live database
and writes idempotent SQL migration files.

Usage:
  # Extract all seed categories to stdout
  python extract_seeds.py --all

  # Extract specific category
  python extract_seeds.py --category notifications
  python extract_seeds.py --category auth
  python extract_seeds.py --category ai
  python extract_seeds.py --category sandbox
  python extract_seeds.py --category grc
  python extract_seeds.py --category agent_sandbox
  python extract_seeds.py --category tasks
  python extract_seeds.py --category issues
  python extract_seeds.py --category feedback
  python extract_seeds.py --category docs
  python extract_seeds.py --category engagements
  python extract_seeds.py --category risk_registry
  python extract_seeds.py --category steampipe
  python extract_seeds.py --category assessments

  # Write to migration file
  python extract_seeds.py --all --output ../01_sql_migrations/02_inprogress/YYYYMMDD_seed-system-data.sql

  # Use custom DB connection
  python extract_seeds.py --all --host myhost --port 5432 --dbname mydb --user myuser --password mypass

Environment variables (fallback to .env in backend/):
  DB_HOST, DB_PORT, DATABASE_NAME, ADMIN_USER, ADMIN_PASSWORD
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ─── Seed category definitions ─────────────────────────────────────────────
# Each category maps to a list of (schema, table, filter, conflict_columns) tuples.
# filter: SQL WHERE clause (None = all rows)
# conflict_columns: columns for ON CONFLICT (list), or None for (id)

SEED_CATEGORIES: dict[str, list[dict]] = {
    "auth": [
        # Dimension tables
        {"schema": "03_auth_manage", "table": "01_dim_identity_types"},
        {"schema": "03_auth_manage", "table": "02_dim_challenge_types"},
        {"schema": "03_auth_manage", "table": "04_dim_user_property_keys"},
        {"schema": "03_auth_manage", "table": "06_dim_account_types"},
        {"schema": "03_auth_manage", "table": "07_dim_account_property_keys"},
        {"schema": "03_auth_manage", "table": "11_dim_feature_flag_categories"},
        {"schema": "03_auth_manage", "table": "12_dim_feature_permission_actions"},
        {"schema": "03_auth_manage", "table": "13_dim_role_levels"},
        {"schema": "03_auth_manage", "table": "14_dim_feature_flags"},
        {"schema": "03_auth_manage", "table": "15_dim_feature_permissions"},
        {"schema": "03_auth_manage", "table": "21_dim_feature_flag_setting_keys"},
        {"schema": "03_auth_manage", "table": "22_dim_role_setting_keys"},
        {"schema": "03_auth_manage", "table": "23_dim_product_types"},
        {"schema": "03_auth_manage", "table": "26_dim_product_setting_keys"},
        {"schema": "03_auth_manage", "table": "27_dim_group_setting_keys"},
        {"schema": "03_auth_manage", "table": "28_dim_org_types"},
        {"schema": "03_auth_manage", "table": "31_dim_org_setting_keys"},
        {"schema": "03_auth_manage", "table": "33_dim_workspace_types"},
        {"schema": "03_auth_manage", "table": "36_dim_workspace_setting_keys"},
        {"schema": "03_auth_manage", "table": "43_dim_invite_statuses"},
        # Products
        {"schema": "03_auth_manage", "table": "24_fct_products"},
        # Feature flag settings (org_visibility, required_license etc.)
        {"schema": "03_auth_manage", "table": "21_dtl_feature_flag_settings",
         "conflict": ["feature_flag_id", "setting_key"]},
        # License profiles
        {"schema": "03_auth_manage", "table": "37_fct_license_profiles"},
        {"schema": "03_auth_manage", "table": "38_dtl_license_profile_settings",
         "conflict": ["license_profile_id", "setting_key"]},
        # System roles (is_system = true)
        {"schema": "03_auth_manage", "table": "16_fct_roles",
         "filter": "is_system = TRUE"},
        # System user groups (platform-level system groups only — no org/workspace scope)
        {"schema": "03_auth_manage", "table": "17_fct_user_groups",
         "filter": "is_system = TRUE AND scope_org_id IS NULL AND scope_workspace_id IS NULL"},
        # Group role assignments (system groups only)
        {"schema": "03_auth_manage", "table": "19_lnk_group_role_assignments",
         "filter": "group_id IN (SELECT id FROM \"03_auth_manage\".\"17_fct_user_groups\" WHERE is_system = TRUE AND scope_org_id IS NULL AND scope_workspace_id IS NULL)"},
        # Sentinel system org/workspace — required FK targets for global library frameworks.
        # Must be seeded before the library category runs.
        {"schema": "03_auth_manage", "table": "29_fct_orgs",
         "filter": "id = '00000000-0000-0000-0000-000000000010'"},
        {"schema": "03_auth_manage", "table": "34_fct_workspaces",
         "filter": "id = '00000000-0000-0000-0000-000000000011'"},
        # Platform admin@kreesalis.com seed user (is_system=true, super admin group member).
        {"schema": "03_auth_manage", "table": "03_fct_users",
         "filter": "id = '00000000-0000-0000-0000-000000000001'"},
        {"schema": "03_auth_manage", "table": "05_dtl_user_properties",
         "filter": "user_id = '00000000-0000-0000-0000-000000000001'"},
        {"schema": "03_auth_manage", "table": "08_dtl_user_accounts",
         "filter": "user_id = '00000000-0000-0000-0000-000000000001'"},
        {"schema": "03_auth_manage", "table": "09_dtl_user_account_properties",
         "filter": "user_account_id = '00000000-0000-0000-0000-000000000002'"},
        {"schema": "03_auth_manage", "table": "18_lnk_group_memberships",
         "filter": "user_id = '00000000-0000-0000-0000-000000000001' AND is_deleted = FALSE"},
        # Role feature permissions
        {"schema": "03_auth_manage", "table": "20_lnk_role_feature_permissions"},
        # Portal views
        {"schema": "03_auth_manage", "table": "50_dim_portal_views"},
        {"schema": "03_auth_manage", "table": "51_lnk_role_views",
         "filter": "role_id IN (SELECT id FROM \"03_auth_manage\".\"16_fct_roles\" WHERE is_system = TRUE)"},
        {"schema": "03_auth_manage", "table": "52_dtl_view_routes"},
    ],
    "notifications": [
        # Dimension tables
        {"schema": "03_notifications", "table": "02_dim_notification_channels"},
        {"schema": "03_notifications", "table": "03_dim_notification_categories"},
        {"schema": "03_notifications", "table": "04_dim_notification_types"},
        {"schema": "03_notifications", "table": "05_dim_notification_statuses"},
        {"schema": "03_notifications", "table": "06_dim_notification_priorities"},
        {"schema": "03_notifications", "table": "07_dim_notification_channel_types"},
        {"schema": "03_notifications", "table": "08_dim_template_variable_keys"},
        {"schema": "03_notifications", "table": "09_dim_tracking_event_types"},
        {"schema": "03_notifications", "table": "09_dim_variable_queries"},
        # Templates & rules
        {"schema": "03_notifications", "table": "10_fct_templates"},
        {"schema": "03_notifications", "table": "14_dtl_template_versions"},
        {"schema": "03_notifications", "table": "15_dtl_template_placeholders"},
        {"schema": "03_notifications", "table": "11_fct_notification_rules"},
        {"schema": "03_notifications", "table": "18_lnk_notification_rule_channels"},
        {"schema": "03_notifications", "table": "19_dtl_rule_conditions"},
        # Variable queries & SMTP
        {"schema": "03_notifications", "table": "31_fct_variable_queries"},
        {"schema": "03_notifications", "table": "30_fct_smtp_config"},
    ],
    "ai": [
        # Dimension tables
        {"schema": "20_ai", "table": "02_dim_agent_types"},
        {"schema": "20_ai", "table": "03_dim_message_roles"},
        {"schema": "20_ai", "table": "04_dim_approval_statuses"},
        {"schema": "20_ai", "table": "05_dim_tool_categories"},
        {"schema": "20_ai", "table": "06_dim_memory_types"},
        {"schema": "20_ai", "table": "07_dim_budget_periods"},
        {"schema": "20_ai", "table": "08_dim_guardrail_types"},
        {"schema": "20_ai", "table": "09_dim_prompt_scopes"},
        {"schema": "20_ai", "table": "10_dim_agent_relationships"},
        {"schema": "20_ai", "table": "11_dim_job_statuses"},
        {"schema": "20_ai", "table": "12_dim_job_priorities"},
        # System configs (guardrails, agent configs, agent definitions, rate limits, pdf templates)
        {"schema": "20_ai", "table": "30_fct_guardrail_configs"},
        {"schema": "20_ai", "table": "32_fct_agent_configs"},
        {"schema": "20_ai", "table": "33_fct_prompt_templates"},
        {"schema": "20_ai", "table": "34_dtl_prompt_template_properties"},
        {"schema": "20_ai", "table": "35_fct_agent_definitions"},
        {"schema": "20_ai", "table": "44_fct_agent_rate_limits"},
        {"schema": "20_ai", "table": "60_fct_pdf_templates"},
    ],
    "sandbox": [
        {"schema": "15_sandbox", "table": "02_dim_connector_categories"},
        {"schema": "15_sandbox", "table": "03_dim_connector_types"},
        {"schema": "15_sandbox", "table": "04_dim_signal_statuses"},
        {"schema": "15_sandbox", "table": "05_dim_dataset_sources"},
        {"schema": "15_sandbox", "table": "06_dim_execution_statuses"},
        {"schema": "15_sandbox", "table": "07_dim_dataset_templates"},
        {"schema": "15_sandbox", "table": "08_dim_threat_severities"},
        {"schema": "15_sandbox", "table": "09_dim_policy_action_types"},
        {"schema": "15_sandbox", "table": "10_dim_library_types"},
        {"schema": "15_sandbox", "table": "11_dim_asset_versions"},
        {"schema": "15_sandbox", "table": "14_dim_asset_types"},
        {"schema": "15_sandbox", "table": "15_dim_asset_statuses"},
        {"schema": "15_sandbox", "table": "16_dim_provider_definitions"},
        {"schema": "15_sandbox", "table": "18_dim_asset_access_roles"},
    ],
    "grc": [
        {"schema": "05_grc_library", "table": "02_dim_framework_types"},
        {"schema": "05_grc_library", "table": "03_dim_framework_categories"},
        {"schema": "05_grc_library", "table": "04_dim_control_categories"},
        {"schema": "05_grc_library", "table": "05_dim_control_criticalities"},
        {"schema": "05_grc_library", "table": "07_dim_test_types"},
        {"schema": "05_grc_library", "table": "08_dim_test_result_statuses"},
    ],
    "agent_sandbox": [
        {"schema": "25_agent_sandbox", "table": "02_dim_agent_statuses"},
        {"schema": "25_agent_sandbox", "table": "03_dim_tool_types"},
        {"schema": "25_agent_sandbox", "table": "04_dim_scenario_types"},
        {"schema": "25_agent_sandbox", "table": "05_dim_evaluation_methods"},
        {"schema": "25_agent_sandbox", "table": "06_dim_execution_statuses"},
    ],
    "tasks": [
        {"schema": "08_tasks", "table": "02_dim_task_types"},
        {"schema": "08_tasks", "table": "03_dim_task_priorities"},
        {"schema": "08_tasks", "table": "04_dim_task_statuses"},
    ],
    "issues": [
        {"schema": "09_issues", "table": "02_dim_issue_statuses"},
        {"schema": "09_issues", "table": "03_dim_issue_severities"},
    ],
    "feedback": [
        {"schema": "10_feedback", "table": "01_dim_ticket_types"},
        {"schema": "10_feedback", "table": "02_dim_ticket_statuses"},
        {"schema": "10_feedback", "table": "03_dim_ticket_priorities"},
    ],
    "docs": [
        {"schema": "11_docs", "table": "01_dim_doc_categories"},
    ],
    "engagements": [
        {"schema": "12_engagements", "table": "02_dim_engagement_statuses"},
        {"schema": "12_engagements", "table": "03_dim_engagement_property_keys"},
        {"schema": "12_engagements", "table": "04_dim_request_property_keys"},
    ],
    "risk_registry": [
        {"schema": "14_risk_registry", "table": "02_dim_risk_categories"},
        {"schema": "14_risk_registry", "table": "03_dim_risk_treatment_types"},
        {"schema": "14_risk_registry", "table": "04_dim_risk_levels"},
    ],
    "assessments": [
        {"schema": "09_assessments", "table": "02_dim_assessment_types"},
        {"schema": "09_assessments", "table": "03_dim_assessment_statuses"},
        {"schema": "09_assessments", "table": "04_dim_finding_severities"},
        {"schema": "09_assessments", "table": "05_dim_finding_statuses"},
        {"schema": "09_assessments", "table": "06_dim_assessment_property_keys"},
        {"schema": "09_assessments", "table": "07_dim_finding_property_keys"},
    ],
    "steampipe": [
        {"schema": "17_steampipe", "table": "02_dim_plugin_types"},
    ],
    # ── Global/published library content (frameworks, controls, risks, etc.) ──
    # Only extracts PUBLISHED frameworks visible in the Framework Library UI,
    # NOT workspace-scoped test/draft copies. Add framework IDs here when
    # publishing new frameworks to the global library.
    # Order matters: parents before children (FK chain).
    #
    # Published frameworks are always scoped to the sentinel org/workspace:
    #   scope_org_id      = 00000000-0000-0000-0000-000000000010
    #   scope_workspace_id = 00000000-0000-0000-0000-000000000011
    # The sentinel rows are seeded in the 'auth' category above.
    #
    # To find publishable framework IDs:
    #   SELECT id, framework_code, (SELECT property_value FROM "05_grc_library"."20_dtl_framework_properties"
    #     WHERE framework_id = f.id AND property_key = 'name') as name
    #   FROM "05_grc_library"."10_fct_frameworks" f
    #   WHERE scope_org_id = '00000000-0000-0000-0000-000000000010'
    #     AND approval_status = 'approved' AND is_marketplace_visible = TRUE
    #     AND is_deleted = FALSE ORDER BY framework_code;
    "library": [
        # ── Published framework IDs (update this list when publishing new ones) ──
        # ce7debe9... = ISO/IEC 27001:2022 (40 controls, 25 requirements)
        # 08b0e825... = SOC2 (36 controls, 24 requirements)
        # 1. Frameworks
        {"schema": "05_grc_library", "table": "10_fct_frameworks",
         "filter": "id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df')"},
        {"schema": "05_grc_library", "table": "20_dtl_framework_properties",
         "filter": "framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df')"},
        {"schema": "05_grc_library", "table": "25_dtl_framework_settings",
         "filter": "framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df')"},
        # 2. Framework versions
        {"schema": "05_grc_library", "table": "11_fct_framework_versions",
         "filter": "framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df')"},
        {"schema": "05_grc_library", "table": "21_dtl_version_properties",
         "filter": "framework_version_id IN (SELECT id FROM \"05_grc_library\".\"11_fct_framework_versions\" WHERE framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df'))"},
        # 3. Requirements
        {"schema": "05_grc_library", "table": "12_fct_requirements",
         "filter": "framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df') AND is_deleted = FALSE"},
        {"schema": "05_grc_library", "table": "22_dtl_requirement_properties",
         "filter": "requirement_id IN (SELECT id FROM \"05_grc_library\".\"12_fct_requirements\" WHERE framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df') AND is_deleted = FALSE)"},
        # 4. Controls
        {"schema": "05_grc_library", "table": "13_fct_controls",
         "filter": "framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df') AND is_deleted = FALSE"},
        {"schema": "05_grc_library", "table": "23_dtl_control_properties",
         "filter": "control_id IN (SELECT id FROM \"05_grc_library\".\"13_fct_controls\" WHERE framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df') AND is_deleted = FALSE)"},
        # 5. Version-control links
        {"schema": "05_grc_library", "table": "31_lnk_framework_version_controls",
         "filter": "framework_version_id IN (SELECT id FROM \"05_grc_library\".\"11_fct_framework_versions\" WHERE framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df'))"},
        # 6. Control tests (all global — scope_workspace_id IS NULL)
        {"schema": "05_grc_library", "table": "14_fct_control_tests",
         "filter": "scope_workspace_id IS NULL AND is_deleted = FALSE"},
        {"schema": "05_grc_library", "table": "24_dtl_test_properties",
         "filter": "test_id IN (SELECT id FROM \"05_grc_library\".\"14_fct_control_tests\" WHERE scope_workspace_id IS NULL AND is_deleted = FALSE)"},
        # 7. Test-control mappings (for published framework controls + global tests)
        {"schema": "05_grc_library", "table": "30_lnk_test_control_mappings",
         "filter": "control_test_id IN (SELECT id FROM \"05_grc_library\".\"14_fct_control_tests\" WHERE scope_workspace_id IS NULL AND is_deleted = FALSE) OR control_id IN (SELECT id FROM \"05_grc_library\".\"13_fct_controls\" WHERE framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df') AND is_deleted = FALSE)"},
        # 8. Global risks library (all — these are platform-level, not framework-specific)
        {"schema": "05_grc_library", "table": "50_fct_global_risks",
         "filter": "is_deleted = FALSE"},
        {"schema": "05_grc_library", "table": "56_dtl_global_risk_properties"},
        {"schema": "05_grc_library", "table": "61_lnk_global_risk_control_mappings",
         "filter": "control_id IN (SELECT id FROM \"05_grc_library\".\"13_fct_controls\" WHERE framework_id IN ('ce7debe9-796b-48df-a17c-f5e1c91cd012', '08b0e825-13d8-41e8-9456-ee6e8e60e2df') AND is_deleted = FALSE)"},
        # 9. Promoted control tests (sandbox → global library)
        {"schema": "15_sandbox", "table": "84_fct_global_control_tests"},
        {"schema": "15_sandbox", "table": "85_dtl_global_control_test_properties"},
        # 10. Risk questionnaires + versions
        {"schema": "14_risk_registry", "table": "37_fct_risk_questionnaires",
         "filter": "is_deleted = FALSE"},
        {"schema": "14_risk_registry", "table": "38_vrs_risk_questionnaire_versions"},
    ],
}


def load_env(backend_dir: Path) -> dict[str, str]:
    """Load .env file from backend directory."""
    env = {}
    env_file = backend_dir / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_db_params(args: argparse.Namespace) -> dict[str, str]:
    """Resolve DB connection parameters from args > env vars > .env file."""
    backend_dir = Path(__file__).resolve().parent.parent
    file_env = load_env(backend_dir)

    def resolve(arg_val: str | None, env_key: str, file_key: str) -> str:
        return arg_val or os.environ.get(env_key, "") or file_env.get(file_key, "")

    return {
        "host": resolve(args.host, "DB_HOST", "DB_HOST"),
        "port": resolve(args.port, "DB_PORT", "DB_PORT") or "5432",
        "dbname": resolve(args.dbname, "DATABASE_NAME", "DATABASE_NAME"),
        "user": resolve(args.user, "ADMIN_USER", "ADMIN_USER"),
        "password": resolve(args.password, "ADMIN_PASSWORD", "ADMIN_PASSWORD"),
    }


def run_query(db: dict[str, str], query: str) -> list[dict[str, Any]]:
    """Execute a query via psql and return rows as list of dicts (JSON output)."""
    wrapped = f"""
    SELECT json_agg(row_to_json(t))
    FROM ({query}) t;
    """
    env = os.environ.copy()
    env["PGPASSWORD"] = db["password"]
    result = subprocess.run(
        [
            "psql",
            "-h", db["host"],
            "-p", db["port"],
            "-U", db["user"],
            "-d", db["dbname"],
            "-t", "-A",
            "-c", wrapped,
        ],
        capture_output=True,
        text=True,
        env=env,
        timeout=30,
    )
    if result.returncode != 0:
        print(f"  ⚠ psql error: {result.stderr.strip()}", file=sys.stderr)
        return []
    raw = result.stdout.strip()
    if not raw or raw == "null" or raw == "":
        return []
    return json.loads(raw)


def get_columns(db: dict[str, str], schema: str, table: str) -> tuple[list[str], dict[str, str]]:
    """Get ordered column names and their data types for a table.

    Excludes GENERATED ALWAYS columns (computed columns) which cannot be
    inserted into.
    """
    q = f"""
    SELECT column_name, data_type, udt_name, is_generated
    FROM information_schema.columns
    WHERE table_schema = '{schema}' AND table_name = '{table}'
    ORDER BY ordinal_position
    """
    rows = run_query(db, q)
    names = [r["column_name"] for r in rows if r.get("is_generated", "NEVER") == "NEVER"]
    types = {r["column_name"]: r["data_type"] for r in rows if r.get("is_generated", "NEVER") == "NEVER"}
    return names, types


def get_unique_constraints(db: dict[str, str], schema: str, table: str) -> list[list[str]]:
    """Get all unique constraint column sets for a table."""
    q = f"""
    SELECT tc.constraint_name,
           array_agg(kcu.column_name ORDER BY kcu.ordinal_position) AS cols
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
        AND tc.table_schema = kcu.table_schema
    WHERE tc.constraint_type IN ('UNIQUE', 'PRIMARY KEY')
        AND tc.table_schema = '{schema}'
        AND tc.table_name = '{table}'
    GROUP BY tc.constraint_name
    ORDER BY tc.constraint_name
    """
    rows = run_query(db, q)
    return [r["cols"] for r in rows]


def best_conflict_columns(
    db: dict[str, str],
    schema: str,
    table: str,
    explicit: list[str] | None,
) -> list[str]:
    """Pick the best ON CONFLICT target for upsert.

    Priority:
    1. Explicit override from category definition
    2. Single-column 'code' unique constraint (most dim tables)
    3. Narrowest composite unique containing 'code'
    4. Narrowest non-PK unique constraint (link tables with natural keys)
    5. Fallback to 'id' (PK)
    """
    if explicit:
        return explicit
    constraints = get_unique_constraints(db, schema, table)
    # Prefer single-column 'code' constraint (most dim tables)
    for cols in constraints:
        if cols == ["code"]:
            return ["code"]
    # Next, prefer the narrowest unique constraint containing 'code'
    code_constraints = [c for c in constraints if "code" in c]
    if code_constraints:
        return min(code_constraints, key=len)
    # Next, prefer narrowest non-PK unique constraint (link tables)
    non_pk = [c for c in constraints if c != ["id"]]
    if non_pk:
        return min(non_pk, key=len)
    # Fallback to id (PK)
    return ["id"]


def sql_value(val: Any, col_type: str = "") -> str:
    """Convert a Python value to a SQL literal."""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, list):
        if col_type == "ARRAY":
            # PostgreSQL text[] array
            elements = ", ".join(
                f"'{str(v).replace(chr(39), chr(39)+chr(39))}'" for v in val
            )
            return f"ARRAY[{elements}]::text[]"
        # JSONB array
        escaped = json.dumps(val, ensure_ascii=False).replace("'", "''")
        return f"'{escaped}'::jsonb"
    if isinstance(val, dict):
        escaped = json.dumps(val, ensure_ascii=False).replace("'", "''")
        return f"'{escaped}'::jsonb"
    s = str(val)
    s = s.replace("'", "''")
    return f"'{s}'"


def extract_table(
    db: dict[str, str],
    schema: str,
    table: str,
    filter_clause: str | None = None,
    conflict_columns: list[str] | None = None,
) -> str:
    """Extract a table's data as idempotent INSERT SQL."""
    cols, col_types = get_columns(db, schema, table)
    if not cols:
        return f"-- Table \"{schema}\".\"{table}\" not found or has no columns\n"

    where = f" WHERE {filter_clause}" if filter_clause else ""
    q = f'SELECT * FROM "{schema}"."{table}"{where} ORDER BY 1'
    rows = run_query(db, q)

    if not rows:
        return f"-- \"{schema}\".\"{table}\": 0 rows (empty)\n"

    conflict = best_conflict_columns(db, schema, table, conflict_columns)
    conflict_str = ", ".join(conflict)

    col_list = ", ".join(cols)

    # Build the DO UPDATE SET clause for upsert (update all non-conflict, non-audit columns)
    skip_on_update = set(conflict) | {"id", "created_at", "created_by"}
    update_cols = [c for c in cols if c not in skip_on_update]
    if update_cols:
        update_set = ", ".join(f"{c} = EXCLUDED.{c}" for c in update_cols)
        conflict_action = f"DO UPDATE SET {update_set}"
    else:
        conflict_action = "DO NOTHING"

    # Wrap in DO $$ EXCEPTION block to skip gracefully if table/columns
    # don't exist on the target environment
    lines = [
        f"-- {schema}.{table} ({len(rows)} rows)",
        "DO $$ BEGIN",
        f'  INSERT INTO "{schema}"."{table}" ({col_list})',
        "  VALUES",
    ]
    value_rows = []
    for row in rows:
        vals = ", ".join(sql_value(row.get(c), col_types.get(c, "")) for c in cols)
        value_rows.append(f"      ({vals})")
    lines.append(",\n".join(value_rows))
    lines.append(f"  ON CONFLICT ({conflict_str}) {conflict_action};")
    lines.append("EXCEPTION WHEN undefined_table OR undefined_column OR foreign_key_violation OR unique_violation THEN NULL;")
    lines.append("END $$;\n")
    return "\n".join(lines)


def extract_category(db: dict[str, str], category: str) -> str:
    """Extract all tables for a seed category."""
    tables = SEED_CATEGORIES.get(category, [])
    if not tables:
        return f"-- Unknown category: {category}\n"

    parts = [
        f"-- {'═' * 77}",
        f"-- SEED: {category.upper()}",
        f"-- Extracted: {datetime.now().isoformat()}",
        f"-- {'═' * 77}\n",
    ]
    for tbl in tables:
        print(f"  Extracting {tbl['schema']}.{tbl['table']}...", file=sys.stderr)
        sql = extract_table(
            db,
            tbl["schema"],
            tbl["table"],
            tbl.get("filter"),
            tbl.get("conflict"),
        )
        parts.append(sql)
    return "\n".join(parts)


def main():
    parser = argparse.ArgumentParser(description="Extract seed data from kcontrol DB")
    parser.add_argument("--all", action="store_true", help="Extract all categories")
    parser.add_argument("--category", type=str, help="Extract a specific category")
    parser.add_argument("--list", action="store_true", help="List available categories")
    parser.add_argument("--output", type=str, help="Write to file instead of stdout")
    parser.add_argument("--host", type=str)
    parser.add_argument("--port", type=str)
    parser.add_argument("--dbname", type=str)
    parser.add_argument("--user", type=str)
    parser.add_argument("--password", type=str)
    args = parser.parse_args()

    if args.list:
        for cat, tables in SEED_CATEGORIES.items():
            schemas = sorted(set(t["schema"] for t in tables))
            print(f"  {cat:20s}  ({len(tables)} tables)  [{', '.join(schemas)}]")
        return

    if not args.all and not args.category:
        parser.print_help()
        return

    db = get_db_params(args)
    if not db["host"] or not db["dbname"]:
        print("ERROR: Missing DB connection params. Set DB_HOST/DATABASE_NAME in .env or pass --host/--dbname", file=sys.stderr)
        sys.exit(1)

    # --all extracts config/dimension seed data only (not library content).
    # Use --category library separately for published frameworks/controls.
    _ALL_EXCLUDES = {"library"}
    categories = [k for k in SEED_CATEGORIES if k not in _ALL_EXCLUDES] if args.all else [args.category]

    header = [
        "-- ═══════════════════════════════════════════════════════════════════════════",
        "-- KCONTROL SYSTEM SEED DATA",
        f"-- Generated: {datetime.now().isoformat()}",
        f"-- Source DB: {db['dbname']} @ {db['host']}",
        f"-- Categories: {', '.join(categories)}",
        "-- ",
        "-- Idempotent: all INSERTs use ON CONFLICT DO UPDATE SET (upsert).",
        "-- Safe to re-run in any environment.",
        "-- ═══════════════════════════════════════════════════════════════════════════\n",
    ]

    parts = header.copy()
    for cat in categories:
        print(f"Extracting category: {cat}...", file=sys.stderr)
        parts.append(extract_category(db, cat))

    parts.append("-- ═══════════════════════════════════════════════════════════════════════════")
    parts.append("-- END OF SEED DATA")
    parts.append("-- ═══════════════════════════════════════════════════════════════════════════\n")
    output = "\n".join(parts)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"\n✓ Written to {args.output} ({len(output)} bytes)", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
