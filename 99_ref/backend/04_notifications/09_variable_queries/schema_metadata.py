"""Whitelist of schemas and tables safe for variable query SQL editor autocomplete.

Only tables and views relevant to notification template variable resolution are exposed.
Sensitive tables (credentials, sessions, audit events) are excluded.
"""

from __future__ import annotations

# Schema → list of safe table/view names (no credentials, sessions, or secret tables)
QUERYABLE_TABLES: dict[str, list[str]] = {
    "03_auth_manage": [
        # Views (recommended for queries)
        "50_vw_user_profile",
        "51_vw_org_detail",
        "52_vw_workspace_detail",
        "42_vw_auth_users",
        # Fact tables
        "03_fct_users",
        "29_fct_orgs",
        "34_fct_workspaces",
        "16_fct_roles",
        "17_fct_user_groups",
        # Detail / EAV tables
        "04_dim_user_property_keys",
        "05_dtl_user_properties",
        "30_dtl_org_settings",
        "35_dtl_workspace_settings",
        # Link tables
        "18_lnk_group_memberships",
        "19_lnk_group_role_assignments",
        "31_lnk_org_memberships",
        "36_lnk_workspace_memberships",
    ],
    "05_grc_library": [
        # Views (recommended)
        "50_vw_control_notification",
        "50_vw_framework_notification",
        "40_vw_framework_catalog",
        "41_vw_control_detail",
        # Fact tables
        "10_fct_frameworks",
        "13_fct_controls",
        "12_fct_requirements",
        # Detail / EAV tables
        "20_dtl_framework_properties",
        "22_dtl_requirement_properties",
        "23_dtl_control_properties",
        # Dimensions
        "04_dim_control_categories",
        "05_dim_control_criticalities",
    ],
    "08_tasks": [
        # Views (recommended)
        "50_vw_task_notification",
        "40_vw_task_detail",
        # Fact tables
        "10_fct_tasks",
        # Detail / EAV tables
        "20_dtl_task_properties",
        # Dimensions
        "02_dim_task_types",
        "03_dim_task_priorities",
        "04_dim_task_statuses",
    ],
    "14_risk_registry": [
        # Views (recommended)
        "50_vw_risk_notification",
        "40_vw_risk_detail",
        # Fact tables
        "10_fct_risks",
        # Detail / EAV tables
        "20_dtl_risk_properties",
        # Dimensions
        "02_dim_risk_categories",
        "04_dim_risk_levels",
        # Link tables
        "30_lnk_risk_control_mappings",
    ],
}
