"""
GRC Copilot tool definitions in OpenAI function-calling format.

14 read-only tools split into two categories:
  - Insight tools (5): read from pre-aggregated analytical views
  - Navigation tools (9): read from existing GRC service layer

All list tools return {items, total_count, returned_count, has_more}.
Row limits enforced here and in the dispatcher — the agent cannot bypass them.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Insight tools — read from analytical views
# ---------------------------------------------------------------------------

_GRC_FRAMEWORK_HEALTH = {
    "type": "function",
    "function": {
        "name": "grc_framework_health",
        "description": (
            "Get a health summary for one or all GRC frameworks. Returns control counts, "
            "risk counts (total + high), open task count, and completion percentage. "
            "Use this first to understand overall compliance posture before drilling down."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "UUID of a specific framework. Omit to get all frameworks for the org.",
                },
                "scope_org_id": {
                    "type": "string",
                    "description": "Filter by scope org ID.",
                },
            },
            "required": [],
        },
    },
}

_GRC_REQUIREMENT_GAPS = {
    "type": "function",
    "function": {
        "name": "grc_requirement_gaps",
        "description": (
            "List requirements within a framework showing coverage gaps. "
            "A gap means either no controls are mapped or all mapped controls lack tests. "
            "Use gaps_only=true to filter to requirements that need attention."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "UUID of the framework to inspect.",
                },
                "gaps_only": {
                    "type": "boolean",
                    "description": "If true, return only requirements with coverage_gap=true.",
                    "default": False,
                },
            },
            "required": ["framework_id"],
        },
    },
}

_GRC_RISK_CONCENTRATION = {
    "type": "function",
    "function": {
        "name": "grc_risk_concentration",
        "description": (
            "Find the controls with the highest risk concentration. "
            "Returns top N controls sorted by critical + high risk counts. "
            "Use this to identify the most risk-exposed parts of the control landscape. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "Limit to controls within a specific framework.",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top controls to return. Default 10, max 50.",
                    "default": 10,
                },
            },
            "required": [],
        },
    },
}

_GRC_TASK_HEALTH = {
    "type": "function",
    "function": {
        "name": "grc_task_health",
        "description": (
            "Get aggregate task health metrics for the current org/workspace. "
            "Returns: total open tasks, overdue count, unassigned critical count, "
            "due-this-week count, avg days overdue, and breakdown by priority and status. "
            "Single call — no pagination needed. No parameters required."
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
}

_GRC_CONTROL_HEALTH = {
    "type": "function",
    "function": {
        "name": "grc_control_health",
        "description": (
            "List controls filtered by health criteria. Use to find controls that are "
            "missing an owner, missing tests, have overdue tasks, or are linked to high-severity risks. "
            "Returns max 50 controls with health metadata."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "Limit to controls within this framework.",
                },
                "missing_owner": {
                    "type": "boolean",
                    "description": "Filter to controls with no assigned owner.",
                },
                "missing_tests": {
                    "type": "boolean",
                    "description": "Filter to controls that have no linked tests.",
                },
                "has_overdue_tasks": {
                    "type": "boolean",
                    "description": "Filter to controls with at least one overdue task.",
                },
                "min_risk_severity": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Filter to controls with max_risk_severity >= this level.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows to return. Default 20, max 50.",
                    "default": 20,
                },
                "offset": {
                    "type": "integer",
                    "description": "Pagination offset.",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
}

# ---------------------------------------------------------------------------
# Navigation tools — read from service layer
# ---------------------------------------------------------------------------

_GRC_LIST_FRAMEWORKS = {
    "type": "function",
    "function": {
        "name": "grc_list_frameworks",
        "description": (
            "List GRC frameworks. Use this to look up framework IDs before calling "
            "framework-specific tools. Returns name, code, approval status, and scope."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "search": {
                    "type": "string",
                    "description": "Text search across framework name and code.",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by framework category (e.g. 'security', 'privacy').",
                },
                "approval_status": {
                    "type": "string",
                    "enum": ["draft", "under_review", "approved", "retired"],
                    "description": "Filter by approval status.",
                },
                "scope_org_id": {
                    "type": "string",
                    "description": "Filter by scope org.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows. Default 20, max 50.",
                    "default": 20,
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
}

_GRC_GET_FRAMEWORK = {
    "type": "function",
    "function": {
        "name": "grc_get_framework",
        "description": (
            "Get full details of a single framework including its description, "
            "version, approval status, scope, and metadata."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "UUID of the framework.",
                },
            },
            "required": ["framework_id"],
        },
    },
}

_GRC_LIST_REQUIREMENTS = {
    "type": "function",
    "function": {
        "name": "grc_list_requirements",
        "description": (
            "List requirements within a framework. Returns requirement code, name, "
            "and control count. Use for navigating framework structure."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "UUID of the parent framework (required).",
                },
                "search": {
                    "type": "string",
                    "description": "Text search across requirement name and code.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows. Default 50, max 100.",
                    "default": 50,
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                },
            },
            "required": ["framework_id"],
        },
    },
}

_GRC_LIST_CONTROLS = {
    "type": "function",
    "function": {
        "name": "grc_list_controls",
        "description": (
            "List controls, optionally scoped to a framework. Use criticality_code "
            "to filter by severity (critical/high/medium/low). Returns control code, "
            "name, type, criticality, and current status."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "Limit to controls within this framework.",
                },
                "criticality_code": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter by control criticality.",
                },
                "control_type": {
                    "type": "string",
                    "description": "Filter by control type (e.g. 'preventive', 'detective').",
                },
                "search": {
                    "type": "string",
                    "description": "Text search across control name and code.",
                },
                "scope_org_id": {
                    "type": "string",
                    "description": "Filter by scope org.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows. Default 20, max 50.",
                    "default": 20,
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
}

_GRC_GET_CONTROL = {
    "type": "function",
    "function": {
        "name": "grc_get_control",
        "description": (
            "Get full detail of a single control including health metrics (open tasks, "
            "overdue tasks, linked risks, test status, owner). Use after grc_list_controls "
            "to get the complete picture for a specific control."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "UUID of the control.",
                },
            },
            "required": ["control_id"],
        },
    },
}

_GRC_LIST_RISKS = {
    "type": "function",
    "function": {
        "name": "grc_list_risks",
        "description": (
            "List risks for the current org/workspace. Filter by risk level (critical/high/medium/low), "
            "status (identified/mitigating/accepted/closed), or category. "
            "Returns risk name, level, status, and linked control count. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risk_level_code": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter by risk level.",
                },
                "risk_status": {
                    "type": "string",
                    "enum": ["identified", "mitigating", "accepted", "closed"],
                    "description": "Filter by risk status.",
                },
                "category": {
                    "type": "string",
                    "description": "Filter by risk category.",
                },
                "search": {
                    "type": "string",
                    "description": "Text search across risk name and description.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows. Default 20, max 50.",
                    "default": 20,
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
}

_GRC_GET_RISK = {
    "type": "function",
    "function": {
        "name": "grc_get_risk",
        "description": (
            "Get full detail of a single risk including its description, likelihood, "
            "impact, treatment plan, and linked controls. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risk_id": {
                    "type": "string",
                    "description": "UUID of the risk.",
                },
            },
            "required": ["risk_id"],
        },
    },
}

_GRC_LIST_TASKS = {
    "type": "function",
    "function": {
        "name": "grc_list_tasks",
        "description": (
            "List tasks for the current org/workspace. Filter by status, priority, entity type "
            "(control/risk/framework), overdue status, or assignee. "
            "Returns task title, priority, status, due date, and entity context. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "status_code": {
                    "type": "string",
                    "description": "Filter by task status (e.g. 'open', 'in_progress', 'completed').",
                },
                "priority_code": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter by priority.",
                },
                "framework_id": {
                    "type": "string",
                    "description": "Filter tasks linked to controls within a specific framework UUID.",
                },
                "entity_type": {
                    "type": "string",
                    "enum": ["control", "risk", "framework", "requirement"],
                    "description": "Filter tasks by the entity type they're linked to.",
                },
                "entity_id": {
                    "type": "string",
                    "description": "Filter tasks linked to a specific entity UUID.",
                },
                "is_overdue": {
                    "type": "boolean",
                    "description": "If true, return only overdue (past due date, not terminal) tasks.",
                },
                "assignee_user_id": {
                    "type": "string",
                    "description": "Filter tasks assigned to a specific user.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max rows. Default 20, max 50.",
                    "default": 20,
                },
                "offset": {
                    "type": "integer",
                    "default": 0,
                },
            },
            "required": [],
        },
    },
}

_GRC_GET_TASK = {
    "type": "function",
    "function": {
        "name": "grc_get_task",
        "description": (
            "Get full detail of a single task including its description, assignee, "
            "due date, priority, status history, and linked entity context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "UUID of the task.",
                },
            },
            "required": ["task_id"],
        },
    },
}


# ---------------------------------------------------------------------------
# Write tools
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Hierarchy tools — traverse GRC entity graph
# ---------------------------------------------------------------------------

_GRC_GET_CONTROL_HIERARCHY = {
    "type": "function",
    "function": {
        "name": "grc_get_control_hierarchy",
        "description": (
            "Get the full hierarchy for a control: framework, requirement, direct tasks "
            "(evidence + remediation), linked risks with their titles/levels, "
            "and tasks on those risks. "
            "Use this whenever the user asks about evidence, tasks, or risks on a control — "
            "it gives the complete picture in one call instead of multiple separate queries. "
            "Returns direct_task_count, evidence_task_count, risk_task_count, "
            "linked_risk_codes, linked_risk_titles, linked_risk_levels."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "control_id": {
                    "type": "string",
                    "description": "UUID of the control.",
                },
            },
            "required": ["control_id"],
        },
    },
}

_GRC_GET_RISK_HIERARCHY = {
    "type": "function",
    "function": {
        "name": "grc_get_risk_hierarchy",
        "description": (
            "Get the full hierarchy for a risk: direct tasks on the risk, "
            "all linked controls (with their codes and frameworks), "
            "and tasks on those linked controls. "
            "Use this when the user asks about a risk's controls, evidence, or tasks — "
            "gives full traversal in one call. "
            "Returns direct_task_count, linked_control_codes, linked_framework_names, "
            "control_task_count."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risk_id": {
                    "type": "string",
                    "description": "UUID of the risk.",
                },
            },
            "required": ["risk_id"],
        },
    },
}

_GRC_GET_FRAMEWORK_HIERARCHY = {
    "type": "function",
    "function": {
        "name": "grc_get_framework_hierarchy",
        "description": (
            "Get a full per-control breakdown of tasks and risks across an entire framework. "
            "Returns one row per control showing: requirement, direct task count, evidence task count, "
            "linked risks (codes + severity), and risk task count. "
            "This is the correct tool when the user asks about tasks/evidence/risks at framework level — "
            "it does NOT require iterating over controls one by one. "
            "Supports pagination (limit/offset) for frameworks with 100s of controls. "
            "Also returns a framework-level summary row with totals."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {
                    "type": "string",
                    "description": "UUID of the framework.",
                },
                "has_tasks": {
                    "type": "boolean",
                    "description": "If true, return only controls that have at least one task (direct or via risk).",
                },
                "has_risks": {
                    "type": "boolean",
                    "description": "If true, return only controls that have at least one linked risk.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max controls to return. Default 50, max 100.",
                    "default": 50,
                },
                "offset": {
                    "type": "integer",
                    "description": "Pagination offset for large frameworks.",
                    "default": 0,
                },
            },
            "required": ["framework_id"],
        },
    },
}

_GRC_LIST_TASKS_FOR_ENTITY = {
    "type": "function",
    "function": {
        "name": "grc_list_tasks_for_entity",
        "description": (
            "List all tasks (direct + via linked entities) for a GRC entity. "
            "For a control: returns tasks linked directly to the control PLUS tasks on all "
            "risks that are linked to that control. "
            "For a risk: returns tasks linked to the risk PLUS tasks on all controls linked "
            "to that risk. "
            "This is the correct tool to use when asking 'what tasks/evidence exist for this control/risk'. "
            "Returns tasks with title, status, priority, due_date, task_type, and source "
            "('direct' or 'via_risk'/'via_control')."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "enum": ["control", "risk"],
                    "description": "The entity type to fetch tasks for.",
                },
                "entity_id": {
                    "type": "string",
                    "description": "UUID of the control or risk.",
                },
                "include_indirect": {
                    "type": "boolean",
                    "description": "If true (default), also include tasks on linked entities (risks linked to control, or controls linked to risk).",
                    "default": True,
                },
                "limit": {
                    "type": "integer",
                    "description": "Max total tasks to return. Default 50.",
                    "default": 50,
                },
            },
            "required": ["entity_type", "entity_id"],
        },
    },
}


_GRC_NAVIGATE = {
    "type": "function",
    "function": {
        "name": "grc_navigate",
        "description": (
            "Navigate the user's browser to a specific GRC entity page. "
            "Use this when the user asks to 'go to', 'open', 'navigate to', 'show me', or 'take me to' "
            "a framework, control, risk, or task. Also use it when you've found an entity the user "
            "would clearly want to view in full detail. "
            "Supported entity types: 'framework', 'control', 'task'. "
            "For 'control', you MUST supply framework_id (look it up first with grc_get_control if needed). "
            "For 'risk', navigation opens the risks list filtered to that risk — use risk_id."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "entity_type": {
                    "type": "string",
                    "enum": ["framework", "control", "risk", "task"],
                    "description": "The type of entity to navigate to.",
                },
                "entity_id": {
                    "type": "string",
                    "description": "UUID of the entity to navigate to.",
                },
                "framework_id": {
                    "type": "string",
                    "description": "Required when entity_type is 'control'. The framework UUID that owns this control.",
                },
                "label": {
                    "type": "string",
                    "description": "Human-readable label for the entity (e.g. 'CC6-01 — User Access Provisioning'). Used in the navigation confirmation message.",
                },
            },
            "required": ["entity_type", "entity_id"],
        },
    },
}


_GRC_NAVIGATE_PAGE = {
    "type": "function",
    "function": {
        "name": "grc_navigate_page",
        "description": (
            "Navigate the user's browser to any page in the application. "
            "Use this when the user asks to 'go to', 'open', 'take me to', or 'show me' a section "
            "like reports, marketplace, frameworks, risks, tasks, settings, sandbox, copilot, admin, etc. "
            "Choose the most specific page that matches the user's intent."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "page": {
                    "type": "string",
                    "enum": [
                        "dashboard",
                        "frameworks",
                        "marketplace",
                        "risks",
                        "tasks",
                        "reports",
                        "copilot",
                        "sandbox",
                        "sandbox_connectors",
                        "sandbox_signals",
                        "sandbox_libraries",
                        "settings_profile",
                        "settings_security",
                        "settings_notifications",
                        "settings_api_keys",
                        "settings_features",
                        "admin_overview",
                        "admin_users",
                        "admin_roles",
                        "admin_orgs",
                        "admin_features",
                        "admin_library_frameworks",
                    ],
                    "description": "The page to navigate to.",
                },
                "label": {
                    "type": "string",
                    "description": "Human-readable label shown in the navigation confirmation (e.g. 'Reports', 'Marketplace'). Defaults to the page name.",
                },
            },
            "required": ["page"],
        },
    },
}


# ---------------------------------------------------------------------------
# Complete tool list — this is what the agent sees and MCP router returns
# ---------------------------------------------------------------------------

GRC_TOOL_DEFINITIONS: list[dict] = [
    # Insight tools (5)
    _GRC_FRAMEWORK_HEALTH,
    _GRC_REQUIREMENT_GAPS,
    _GRC_RISK_CONCENTRATION,
    _GRC_TASK_HEALTH,
    _GRC_CONTROL_HEALTH,
    # Navigation tools (9)
    _GRC_LIST_FRAMEWORKS,
    _GRC_GET_FRAMEWORK,
    _GRC_LIST_REQUIREMENTS,
    _GRC_LIST_CONTROLS,
    _GRC_GET_CONTROL,
    _GRC_LIST_RISKS,
    _GRC_GET_RISK,
    _GRC_LIST_TASKS,
    _GRC_GET_TASK,
    # Hierarchy tools (4) — traverse the entity graph
    _GRC_GET_CONTROL_HIERARCHY,
    _GRC_GET_RISK_HIERARCHY,
    _GRC_GET_FRAMEWORK_HIERARCHY,
    _GRC_LIST_TASKS_FOR_ENTITY,
    # Navigation actions (2) — trigger browser navigation
    _GRC_NAVIGATE,
    _GRC_NAVIGATE_PAGE,
]

# ---------------------------------------------------------------------------
# Write tool definitions — all require approval before execution
# ---------------------------------------------------------------------------

_GRC_CREATE_FRAMEWORK = {
    "type": "function",
    "function": {
        "name": "grc_create_framework",
        "description": (
            "Propose creating a new compliance framework. Requires approval before execution. "
            "Use when the user asks to add or create a framework."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_code": {"type": "string", "description": "Unique code, lowercase snake_case, e.g. 'iso_27001'"},
                "name": {"type": "string", "description": "Human-readable framework name"},
                "framework_type_code": {"type": "string", "description": "Type code, e.g. 'standard', 'regulation', 'internal'"},
                "framework_category_code": {"type": "string", "description": "Category code, e.g. 'security', 'compliance'"},
                "description": {"type": "string", "description": "Framework description"},
                "publisher_name": {"type": "string", "description": "Publisher, e.g. 'ISO', 'AICPA'"},
            },
            "required": ["framework_code", "name", "framework_type_code", "framework_category_code"],
        },
    },
}

_GRC_CREATE_REQUIREMENT = {
    "type": "function",
    "function": {
        "name": "grc_create_requirement",
        "description": (
            "Propose creating a single requirement under a framework. Requires approval. "
            "Use when adding one requirement/control group to a framework."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {"type": "string", "description": "Framework UUID to add requirement to"},
                "requirement_code": {"type": "string", "description": "Short code, e.g. 'CC6'"},
                "name": {"type": "string", "description": "Requirement name"},
                "description": {"type": "string", "description": "Requirement description"},
                "sort_order": {"type": "integer", "description": "Display sort order", "default": 0},
            },
            "required": ["framework_id", "requirement_code", "name"],
        },
    },
}

_GRC_BULK_CREATE_REQUIREMENTS = {
    "type": "function",
    "function": {
        "name": "grc_bulk_create_requirements",
        "description": (
            "Propose creating multiple requirements under a single framework in one approval. "
            "Use when adding several requirements at once to a framework."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {"type": "string", "description": "Framework UUID to add requirements to"},
                "requirements": {
                    "type": "array",
                    "description": "List of requirements to create",
                    "items": {
                        "type": "object",
                        "properties": {
                            "requirement_code": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "sort_order": {"type": "integer"},
                        },
                        "required": ["requirement_code", "name"],
                    },
                    "maxItems": 20,
                },
            },
            "required": ["framework_id", "requirements"],
        },
    },
}

_GRC_CREATE_CONTROL = {
    "type": "function",
    "function": {
        "name": "grc_create_control",
        "description": (
            "Propose creating a single control under a framework. Requires approval. "
            "You can only create controls for one framework at a time."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {"type": "string", "description": "Framework UUID the control belongs to"},
                "control_code": {"type": "string", "description": "Control code, e.g. 'CC6-01'"},
                "name": {"type": "string", "description": "Control name"},
                "control_category_code": {"type": "string", "description": "Category, e.g. 'access_control', 'change_management'"},
                "criticality_code": {"type": "string", "description": "Criticality: 'critical', 'high', 'medium', 'low'", "default": "medium"},
                "control_type": {"type": "string", "enum": ["preventive", "detective", "corrective", "compensating"], "default": "preventive"},
                "automation_potential": {"type": "string", "enum": ["full", "partial", "manual"], "default": "manual"},
                "requirement_id": {"type": "string", "description": "Optional requirement UUID to link control to"},
                "description": {"type": "string"},
                "guidance": {"type": "string", "description": "Implementation guidance"},
            },
            "required": ["framework_id", "control_code", "name", "control_category_code"],
        },
    },
}

_GRC_BULK_CREATE_CONTROLS = {
    "type": "function",
    "function": {
        "name": "grc_bulk_create_controls",
        "description": (
            "Propose creating multiple controls under a single framework in one approval. "
            "Only one framework allowed per bulk call."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "framework_id": {"type": "string", "description": "Framework UUID — all controls belong to this framework"},
                "controls": {
                    "type": "array",
                    "description": "List of controls to create",
                    "items": {
                        "type": "object",
                        "properties": {
                            "control_code": {"type": "string"},
                            "name": {"type": "string"},
                            "control_category_code": {"type": "string"},
                            "criticality_code": {"type": "string", "default": "medium"},
                            "control_type": {"type": "string", "default": "preventive"},
                            "automation_potential": {"type": "string", "default": "manual"},
                            "requirement_id": {"type": "string"},
                            "description": {"type": "string"},
                            "guidance": {"type": "string"},
                        },
                        "required": ["control_code", "name", "control_category_code"],
                    },
                    "maxItems": 30,
                },
            },
            "required": ["framework_id", "controls"],
        },
    },
}

_GRC_CREATE_RISK = {
    "type": "function",
    "function": {
        "name": "grc_create_risk",
        "description": (
            "Propose creating a single risk in the risk registry. Requires approval. "
            "org_id and workspace_id are injected automatically from session context — do NOT ask the user for them."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risk_code": {"type": "string", "description": "Short unique code, e.g. 'RISK-001'. If not provided, one will be auto-generated."},
                "title": {"type": "string", "description": "Risk title"},
                "risk_category_code": {"type": "string", "description": "Category code. Valid values: 'operational', 'strategic', 'compliance', 'financial', 'reputational', 'technology', 'legal', 'vendor'. Use 'technology' for security/cyber risks."},
                "risk_level_code": {"type": "string", "description": "Level: 'critical', 'high', 'medium', 'low'", "default": "medium"},
                "treatment_type_code": {"type": "string", "description": "Treatment: 'mitigate', 'accept', 'transfer', 'avoid'", "default": "mitigate"},
                "description": {"type": "string"},
                "business_impact": {"type": "string"},
            },
            "required": ["title", "risk_category_code"],
        },
    },
}

_GRC_BULK_CREATE_RISKS = {
    "type": "function",
    "function": {
        "name": "grc_bulk_create_risks",
        "description": (
            "Propose creating multiple risks in one approval. "
            "All risks go into the same org and workspace. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risks": {
                    "type": "array",
                    "description": "List of risks to create",
                    "items": {
                        "type": "object",
                        "properties": {
                            "risk_code": {"type": "string"},
                            "title": {"type": "string"},
                            "risk_category_code": {"type": "string"},
                            "risk_level_code": {"type": "string", "default": "medium"},
                            "treatment_type_code": {"type": "string", "default": "mitigate"},
                            "description": {"type": "string"},
                            "business_impact": {"type": "string"},
                        },
                        "required": ["risk_code", "title", "risk_category_code"],
                    },
                    "maxItems": 20,
                },
            },
            "required": ["risks"],
        },
    },
}

_GRC_CREATE_TASK = {
    "type": "function",
    "function": {
        "name": "grc_create_task",
        "description": (
            "Propose creating a single task linked to a control or risk. Requires approval. "
            "Tasks for one control or one risk only per call. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Task title"},
                "task_type_code": {"type": "string", "description": "Type: 'evidence_collection' (for controls), 'control_remediation' (for controls), 'risk_mitigation' (for risks), 'general'"},
                "priority_code": {"type": "string", "description": "Priority: 'critical', 'high', 'medium', 'low'", "default": "medium"},
                "entity_type": {"type": "string", "description": "Linked entity type: 'control' or 'risk'. Required when linking to an entity."},
                "entity_id": {"type": "string", "description": "UUID of the linked control or risk"},
                "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD format"},
                "assignee_user_id": {"type": "string", "description": "User UUID to assign to"},
                "description": {"type": "string"},
                "acceptance_criteria": {"type": "string"},
            },
            "required": ["title", "task_type_code"],
        },
    },
}

_GRC_BULK_CREATE_TASKS = {
    "type": "function",
    "function": {
        "name": "grc_bulk_create_tasks",
        "description": (
            "Propose creating multiple tasks all linked to a single control or risk. "
            "Only one parent entity (control or risk) per bulk call. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "entity_type": {"type": "string", "description": "Parent entity type: 'control' or 'risk'"},
                "entity_id": {"type": "string", "description": "UUID of the parent control or risk"},
                "tasks": {
                    "type": "array",
                    "description": "List of tasks to create",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "task_type_code": {"type": "string", "description": "'evidence_collection', 'control_remediation', 'risk_mitigation', or 'general'"},
                            "priority_code": {"type": "string", "default": "medium"},
                            "due_date": {"type": "string"},
                            "assignee_user_id": {"type": "string"},
                            "description": {"type": "string"},
                            "acceptance_criteria": {"type": "string"},
                        },
                        "required": ["title", "task_type_code"],
                    },
                    "maxItems": 20,
                },
            },
            "required": ["entity_type", "entity_id", "tasks"],
        },
    },
}

_GRC_MAP_CONTROL_TO_RISK = {
    "type": "function",
    "function": {
        "name": "grc_map_control_to_risk",
        "description": (
            "Propose mapping a control to a risk to establish their relationship. Requires approval. "
            "Use when the user asks to link, associate, or map controls to risks. "
            "org_id and workspace_id are injected automatically from session context."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "risk_id": {"type": "string", "description": "Risk UUID"},
                "control_id": {"type": "string", "description": "Control UUID"},
                "effectiveness_rating": {"type": "string", "description": "How effective: 'high', 'medium', 'low'", "default": "medium"},
                "notes": {"type": "string", "description": "Notes about this mapping"},
            },
            "required": ["risk_id", "control_id"],
        },
    },
}

_GRC_PROPOSE_FORM_FIELDS = {
    "type": "function",
    "function": {
        "name": "grc_propose_form_fields",
        "description": (
            "Propose field values for the currently open create/edit form. "
            "Call this ONLY when you have gathered enough context to confidently fill "
            "all required fields. This does NOT create any entity — it just pre-fills "
            "the form for the user to review and submit. "
            "After proposing, write a brief explanation of your choices."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "fields": {
                    "type": "object",
                    "description": (
                        "Map of field_name → value. "
                        "Framework fields: name, description, framework_type_code, framework_category_code. "
                        "Control fields: name, description, control_category_code, criticality_code, automation_potential. "
                        "Risk fields: title, description, risk_category_code, risk_level_code, treatment_type_code. "
                        "Task fields: title, description, task_type_code, priority_code, entity_type, entity_id. "
                        "Only include fields you are confident about."
                    ),
                    "additionalProperties": {"type": "string"},
                },
                "explanation": {
                    "type": "string",
                    "description": "Brief explanation of why you chose these values (1-2 sentences).",
                },
            },
            "required": ["fields"],
        },
    },
}

_GRC_GENERATE_REPORT = {
    "type": "function",
    "function": {
        "name": "grc_generate_report",
        "description": (
            "Queue an AI-generated GRC report. Call this when the user asks to generate, create, or run any compliance "
            "or risk report. The report is generated asynchronously — the tool returns immediately with a report_id "
            "and initial status.\n\n"
            "IMPORTANT SCOPING RULES — always clarify scope with the user before calling:\n"
            "- framework_compliance, framework_readiness, framework_gap_analysis: "
            "MUST have a framework. Call grc_list_frameworks and ask the user to confirm which one. Pass as framework_id.\n"
            "- control_status: ask if they want a single control (pass control_id), "
            "all controls in a framework (pass framework_id), or org-wide (no scope).\n"
            "- evidence_report: ask if they want evidence for a single control (pass control_id) "
            "or a whole framework (pass framework_id).\n"
            "- risk_summary: ask if they want a deep-dive on one risk (pass risk_id), "
            "risks for a framework (pass framework_id), or org-wide. "
            "Also ask if they want to filter by risk level (critical/high/medium/low) or status (identified/mitigating/accepted/closed).\n"
            "- task_health: ask if they want tasks filtered by framework, priority, or status.\n"
            "- remediation_plan: ask if scoped to a framework, a risk level, or org-wide.\n"
            "- executive_summary, compliance_posture, board_risk_report, vendor_risk, audit_trail: "
            "org-wide — no scoping needed, proceed directly.\n\n"
            "Available report types:\n"
            "  framework_compliance — compliance status for one framework\n"
            "  framework_readiness — readiness assessment for one framework\n"
            "  framework_gap_analysis — gap analysis for one framework\n"
            "  control_status — control health (org-wide or per-framework)\n"
            "  risk_summary — risk landscape (org-wide or per-framework)\n"
            "  executive_summary — high-level org-wide summary\n"
            "  compliance_posture — cross-framework posture overview\n"
            "  board_risk_report — board-level risk narrative\n"
            "  remediation_plan — prioritized remediation roadmap\n"
            "  vendor_risk — third-party risk assessment\n"
            "  task_health — task backlog health\n"
            "  audit_trail — audit event timeline\n"
            "  evidence_report — evidence collection status"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "report_type": {
                    "type": "string",
                    "enum": [
                        "executive_summary", "compliance_posture",
                        "framework_compliance", "framework_readiness", "framework_gap_analysis",
                        "control_status", "risk_summary", "board_risk_report",
                        "vendor_risk", "remediation_plan", "task_health",
                        "audit_trail", "evidence_report",
                    ],
                    "description": "Type of report to generate.",
                },
                "title": {
                    "type": "string",
                    "description": "Optional human-readable title. If omitted, one is auto-generated.",
                },
                "framework_id": {
                    "type": "string",
                    "description": (
                        "UUID of the framework to scope this report to. "
                        "REQUIRED for: framework_compliance, framework_readiness, framework_gap_analysis. "
                        "OPTIONAL for: control_status, risk_summary, remediation_plan (scopes to that framework). "
                        "OMIT for: executive_summary, compliance_posture, board_risk_report, vendor_risk, task_health, audit_trail, evidence_report."
                    ),
                },
                "risk_id": {
                    "type": "string",
                    "description": (
                        "UUID of a specific risk to focus on. "
                        "Use for: risk_summary (generates a deep-dive report on one risk including all linked controls and tasks). "
                        "Mutually exclusive with framework_id for risk_summary."
                    ),
                },
                "control_id": {
                    "type": "string",
                    "description": (
                        "UUID of a specific control to focus on. "
                        "Use for: control_status, evidence_report (generates a focused report on one control "
                        "including its tasks, evidence, linked risks, and test history). "
                        "Mutually exclusive with framework_id for control_status."
                    ),
                },
                "risk_level": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter risk_summary or board_risk_report to risks at this level or above.",
                },
                "risk_status": {
                    "type": "string",
                    "enum": ["identified", "mitigating", "accepted", "closed"],
                    "description": "Filter risk_summary to risks in this treatment status.",
                },
                "task_status": {
                    "type": "string",
                    "description": "Filter task_health report to tasks with this status (e.g. 'open', 'in_progress').",
                },
                "task_priority": {
                    "type": "string",
                    "enum": ["critical", "high", "medium", "low"],
                    "description": "Filter task_health or remediation_plan to tasks at this priority.",
                },
            },
            "required": ["report_type"],
        },
    },
}

GRC_WRITE_TOOL_DEFINITIONS: list[dict] = [
    _GRC_GENERATE_REPORT,
    _GRC_CREATE_FRAMEWORK,
    _GRC_CREATE_REQUIREMENT,
    _GRC_BULK_CREATE_REQUIREMENTS,
    _GRC_CREATE_CONTROL,
    _GRC_BULK_CREATE_CONTROLS,
    _GRC_CREATE_RISK,
    _GRC_BULK_CREATE_RISKS,
    _GRC_CREATE_TASK,
    _GRC_BULK_CREATE_TASKS,
    _GRC_MAP_CONTROL_TO_RISK,
]

# Form fill tool — included in form-fill agent but NOT the main copilot
GRC_FORM_FILL_TOOL_DEFINITIONS: list[dict] = GRC_TOOL_DEFINITIONS + [_GRC_PROPOSE_FORM_FIELDS]

# Full combined tool list (read + write) — used by the main copilot
GRC_ALL_TOOL_DEFINITIONS: list[dict] = GRC_TOOL_DEFINITIONS + GRC_WRITE_TOOL_DEFINITIONS

# Quick lookup: tool name → category for SSE events
GRC_TOOL_CATEGORIES: dict[str, str] = {
    "grc_framework_health": "insight",
    "grc_requirement_gaps": "insight",
    "grc_risk_concentration": "insight",
    "grc_task_health": "insight",
    "grc_control_health": "insight",
    "grc_list_frameworks": "navigation",
    "grc_get_framework": "navigation",
    "grc_list_requirements": "navigation",
    "grc_list_controls": "navigation",
    "grc_get_control": "navigation",
    "grc_list_risks": "navigation",
    "grc_get_risk": "navigation",
    "grc_list_tasks": "navigation",
    "grc_get_task": "navigation",
    "grc_get_control_hierarchy": "hierarchy",
    "grc_get_risk_hierarchy": "hierarchy",
    "grc_get_framework_hierarchy": "hierarchy",
    "grc_list_tasks_for_entity": "hierarchy",
    "grc_navigate": "action",
    "grc_navigate_page": "action",
    "grc_generate_report": "action",
    # Write tools
    "grc_create_framework": "write",
    "grc_create_requirement": "write",
    "grc_bulk_create_requirements": "write",
    "grc_create_control": "write",
    "grc_bulk_create_controls": "write",
    "grc_create_risk": "write",
    "grc_bulk_create_risks": "write",
    "grc_create_task": "write",
    "grc_bulk_create_tasks": "write",
    "grc_map_control_to_risk": "write",
    # Form fill
    "grc_propose_form_fields": "form_fill",
}
