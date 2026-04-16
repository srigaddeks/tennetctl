"""
MCPToolDispatcher — routes GRC tool calls to Postgres views or the service layer.

Insight tools (5) query pre-aggregated views directly via asyncpg.
Navigation tools (9) delegate to existing service classes.

Token estimate: len(json.dumps(output)) // 4 — cheap, no external tokenizer.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import import_module
from typing import Any

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.mcp.dispatcher")

# Row caps enforced in the dispatcher regardless of what the agent requests
_INSIGHT_ROW_CAP = 50
_LIST_ROW_CAP = 50
_REQUIREMENT_ROW_CAP = 100


@dataclass
class ToolContext:
    pool: asyncpg.Pool
    user_id: str
    tenant_key: str
    org_id: str | None
    workspace_id: str | None
    # Services injected at construction time
    framework_service: Any
    requirement_service: Any
    control_service: Any
    risk_service: Any
    task_service: Any


@dataclass
class ToolResult:
    output: dict
    token_estimate: int
    error: str | None = None

    @classmethod
    def success(cls, output: dict) -> "ToolResult":
        estimate = len(json.dumps(output, default=str)) // 4
        return cls(output=output, token_estimate=estimate)

    @classmethod
    def failure(cls, message: str) -> "ToolResult":
        output = {"error": message}
        return cls(output=output, token_estimate=10, error=message)


# ---------------------------------------------------------------------------
# Insight handlers — query analytical views directly
# ---------------------------------------------------------------------------

async def _grc_framework_health(args: dict, ctx: ToolContext) -> ToolResult:
    framework_id = args.get("framework_id")
    scope_org_id = args.get("scope_org_id")
    # Scope by workspace unless a specific framework_id is already provided
    scope_workspace_id = args.get("scope_workspace_id") if args.get("scope_workspace_id") else (None if framework_id else ctx.workspace_id)

    conditions = ["tenant_key = $1"]
    params: list = [ctx.tenant_key]
    idx = 2

    if framework_id:
        conditions.append(f"framework_id = ${idx}::uuid"); params.append(framework_id); idx += 1
    if scope_org_id:
        conditions.append(f"scope_org_id = ${idx}::uuid"); params.append(scope_org_id); idx += 1
    if scope_workspace_id:
        conditions.append(f"scope_workspace_id = ${idx}::uuid"); params.append(scope_workspace_id); idx += 1

    where = " AND ".join(conditions)
    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT framework_id::text, framework_code, name, approval_status,
                   scope_org_id::text, total_controls, active_controls,
                   total_requirements, open_task_count, linked_risk_count, high_risk_count,
                   CASE WHEN total_controls > 0
                        THEN ROUND(active_controls::numeric / total_controls * 100, 1)
                        ELSE 0 END AS completion_pct
            FROM "05_grc_library"."80_vw_framework_summary"
            WHERE {where}
            ORDER BY name
            LIMIT {_INSIGHT_ROW_CAP}
            """,
            *params,
        )
    items = [dict(r) for r in rows]
    return ToolResult.success({"items": items, "total_count": len(items)})


async def _grc_requirement_gaps(args: dict, ctx: ToolContext) -> ToolResult:
    framework_id = args.get("framework_id")
    gaps_only = args.get("gaps_only", False)

    conditions = ["tenant_key = $1", "framework_id = $2::uuid"]
    params: list = [ctx.tenant_key, framework_id]
    if gaps_only:
        conditions.append("coverage_gap = TRUE")

    where = " AND ".join(conditions)
    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT requirement_id::text, framework_id::text, requirement_code, name,
                   control_count, open_task_count, high_risk_count,
                   has_no_controls, coverage_gap
            FROM "05_grc_library"."81_vw_requirement_summary"
            WHERE {where}
            ORDER BY coverage_gap DESC, requirement_code
            LIMIT {_INSIGHT_ROW_CAP}
            """,
            *params,
        )
    items = [dict(r) for r in rows]
    return ToolResult.success({"items": items, "total_count": len(items), "gaps_only": gaps_only})


async def _grc_risk_concentration(args: dict, ctx: ToolContext) -> ToolResult:
    org_id = args.get("org_id", ctx.org_id)
    workspace_id = args.get("workspace_id", ctx.workspace_id)
    framework_id = args.get("framework_id")
    top_n = min(int(args.get("top_n", 10)), _INSIGHT_ROW_CAP)

    conditions = ["tenant_key = $1", "org_id = $2::uuid", "workspace_id = $3::uuid"]
    params: list = [ctx.tenant_key, org_id, workspace_id]
    idx = 4

    if framework_id:
        conditions.append(f"framework_id = ${idx}::uuid"); params.append(framework_id); idx += 1

    where = " AND ".join(conditions)
    async with ctx.pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT control_id::text, control_code, framework_id::text,
                   critical_risk_count, high_risk_count, medium_risk_count,
                   unactioned_risk_count, active_treatment_count
            FROM "14_risk_registry"."80_vw_risk_concentration"
            WHERE {where}
            ORDER BY critical_risk_count DESC, high_risk_count DESC
            LIMIT {top_n}
            """,
            *params,
        )
    items = [dict(r) for r in rows]
    return ToolResult.success({"items": items, "total_count": len(items)})


async def _grc_task_health(args: dict, ctx: ToolContext) -> ToolResult:
    org_id = args.get("org_id", ctx.org_id)
    workspace_id = args.get("workspace_id", ctx.workspace_id)

    async with ctx.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT total_open_tasks, overdue_count, unassigned_critical_count,
                   due_this_week_count, avg_days_overdue, open_by_priority
            FROM "08_tasks"."80_vw_task_health"
            WHERE tenant_key = $1 AND org_id = $2::uuid AND workspace_id = $3::uuid
            """,
            ctx.tenant_key, org_id, workspace_id,
        )
    if row is None:
        return ToolResult.success({
            "total_open_tasks": 0, "overdue_count": 0,
            "unassigned_critical_count": 0, "due_this_week_count": 0,
            "avg_days_overdue": 0.0, "open_by_priority": {},
        })
    data = dict(row)
    # asyncpg returns JSONB as str — parse if needed
    if isinstance(data.get("open_by_priority"), str):
        try:
            data["open_by_priority"] = json.loads(data["open_by_priority"])
        except (json.JSONDecodeError, TypeError):
            data["open_by_priority"] = {}
    return ToolResult.success(data)


async def _grc_control_health(args: dict, ctx: ToolContext) -> ToolResult:
    framework_id = args.get("framework_id")
    scope_workspace_id = args.get("scope_workspace_id", ctx.workspace_id)
    missing_owner = args.get("missing_owner")
    missing_tests = args.get("missing_tests")
    has_overdue_tasks = args.get("has_overdue_tasks")
    min_risk_severity = args.get("min_risk_severity")
    limit = min(int(args.get("limit", 20)), _INSIGHT_ROW_CAP)
    offset = int(args.get("offset", 0))

    _SEV_ORDER = {"low": 1, "medium": 2, "high": 3, "critical": 4}

    conditions = ["tenant_key = $1"]
    params: list = [ctx.tenant_key]
    idx = 2

    if framework_id:
        conditions.append(f"framework_id = ${idx}::uuid"); params.append(framework_id); idx += 1
    elif scope_workspace_id:
        # Scope to controls whose framework belongs to this workspace
        conditions.append(
            f"framework_id IN (SELECT id FROM \"05_grc_library\".\"10_fct_frameworks\" "
            f"WHERE scope_workspace_id = ${idx}::uuid AND NOT is_deleted)"
        )
        params.append(scope_workspace_id); idx += 1
    if missing_owner is True:
        conditions.append("has_owner = FALSE")
    if missing_tests is True:
        conditions.append("has_tests = FALSE")
    if has_overdue_tasks is True:
        conditions.append("overdue_task_count > 0")
    if min_risk_severity and min_risk_severity in _SEV_ORDER:
        sev_list = [s for s, v in _SEV_ORDER.items() if v >= _SEV_ORDER[min_risk_severity]]
        sev_literals = ", ".join(f"'{s}'" for s in sev_list)
        conditions.append(f"max_risk_severity IN ({sev_literals})")

    where = " AND ".join(conditions)
    async with ctx.pool.acquire() as conn:
        total_row = await conn.fetchrow(
            f"SELECT COUNT(*) FROM \"05_grc_library\".\"82_vw_control_health\" WHERE {where}",
            *params,
        )
        total = total_row[0] if total_row else 0
        rows = await conn.fetch(
            f"""
            SELECT control_id::text, framework_id::text, control_code, name,
                   criticality_code, open_task_count, overdue_task_count,
                   linked_risk_count, max_risk_severity, has_owner, has_tests, last_test_date::text
            FROM "05_grc_library"."82_vw_control_health"
            WHERE {where}
            ORDER BY overdue_task_count DESC, linked_risk_count DESC
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )
    items = [dict(r) for r in rows]
    return ToolResult.success({
        "items": items,
        "total_count": total,
        "returned_count": len(items),
        "has_more": (offset + len(items)) < total,
    })


# ---------------------------------------------------------------------------
# Navigation handlers — delegate to service layer
# ---------------------------------------------------------------------------

async def _grc_list_frameworks(args: dict, ctx: ToolContext) -> ToolResult:
    limit = min(int(args.get("limit", 20)), _LIST_ROW_CAP)
    offset = int(args.get("offset", 0))
    result = await ctx.framework_service.list_frameworks(
        user_id=ctx.user_id,
        tenant_key=ctx.tenant_key,
        category=args.get("category"),
        approval_status=args.get("approval_status"),
        search=args.get("search"),
        scope_org_id=args.get("scope_org_id"),
        scope_workspace_id=args.get("scope_workspace_id", ctx.workspace_id),
        limit=limit,
        offset=offset,
    )
    items = [i.model_dump() for i in result.items]
    total = result.total
    return ToolResult.success({
        "items": items,
        "total_count": total,
        "returned_count": len(items),
        "has_more": (offset + len(items)) < total,
    })


async def _grc_get_framework(args: dict, ctx: ToolContext) -> ToolResult:
    framework = await ctx.framework_service.get_framework(
        user_id=ctx.user_id,
        framework_id=args["framework_id"],
    )
    return ToolResult.success(framework.model_dump())


async def _grc_list_requirements(args: dict, ctx: ToolContext) -> ToolResult:
    limit = min(int(args.get("limit", 50)), _REQUIREMENT_ROW_CAP)
    offset = int(args.get("offset", 0))
    result = await ctx.requirement_service.list_requirements(
        user_id=ctx.user_id,
        framework_id=args["framework_id"],
    )
    # Slice manually since the service doesn't support pagination yet
    all_items = result.items
    sliced = all_items[offset: offset + limit]
    total = result.total
    return ToolResult.success({
        "items": [i.model_dump() for i in sliced],
        "total_count": total,
        "returned_count": len(sliced),
        "has_more": (offset + len(sliced)) < total,
    })


async def _grc_list_controls(args: dict, ctx: ToolContext) -> ToolResult:
    limit = min(int(args.get("limit", 20)), _LIST_ROW_CAP)
    offset = int(args.get("offset", 0))
    result = await ctx.control_service.list_all_controls(
        user_id=ctx.user_id,
        tenant_key=ctx.tenant_key,
        framework_id=args.get("framework_id"),
        control_category_code=args.get("criticality_code"),
        search=args.get("search"),
        scope_org_id=args.get("scope_org_id"),
        scope_workspace_id=args.get("scope_workspace_id", ctx.workspace_id),
        limit=limit,
        offset=offset,
    )
    items = result.items if hasattr(result, "items") else result
    total = result.total if hasattr(result, "total") else len(items)
    return ToolResult.success({
        "items": [i.model_dump() if hasattr(i, "model_dump") else i for i in items],
        "total_count": total,
        "returned_count": len(items),
        "has_more": (offset + len(items)) < total,
    })


async def _grc_get_control(args: dict, ctx: ToolContext) -> ToolResult:
    control_id = args["control_id"]
    # Look up framework_id from the DB first (service requires it for validation)
    async with ctx.pool.acquire() as conn:
        fw_row = await conn.fetchrow(
            "SELECT framework_id::text FROM \"05_grc_library\".\"13_fct_controls\" WHERE id = $1::uuid AND is_deleted = FALSE",
            control_id,
        )
    if fw_row is None:
        return ToolResult.failure(f"Control {control_id} not found")
    framework_id = fw_row["framework_id"]

    control = await ctx.control_service.get_control(
        user_id=ctx.user_id,
        framework_id=framework_id,
        control_id=control_id,
    )
    data = control.model_dump()
    # Enrich with health view data
    async with ctx.pool.acquire() as conn:
        health_row = await conn.fetchrow(
            """
            SELECT open_task_count, overdue_task_count, linked_risk_count,
                   max_risk_severity, has_owner, has_tests, last_test_date::text
            FROM "05_grc_library"."82_vw_control_health"
            WHERE control_id = $1::uuid
            """,
            control_id,
        )
    if health_row:
        data["health"] = dict(health_row)
    return ToolResult.success(data)


async def _grc_list_risks(args: dict, ctx: ToolContext) -> ToolResult:
    limit = min(int(args.get("limit", 20)), _LIST_ROW_CAP)
    offset = int(args.get("offset", 0))
    result = await ctx.risk_service.list_risks(
        user_id=ctx.user_id,
        tenant_key=ctx.tenant_key,
        org_id=args.get("org_id", ctx.org_id),
        workspace_id=args.get("workspace_id", ctx.workspace_id),
        category=args.get("category"),
        status=args.get("risk_status"),
        level=args.get("risk_level_code"),
        search=args.get("search"),
        limit=limit,
        offset=offset,
    )
    items = result.items if hasattr(result, "items") else result
    total = result.total if hasattr(result, "total") else len(items)
    return ToolResult.success({
        "items": [i.model_dump() if hasattr(i, "model_dump") else i for i in items],
        "total_count": total,
        "returned_count": len(items),
        "has_more": (offset + len(items)) < total,
    })


async def _grc_get_risk(args: dict, ctx: ToolContext) -> ToolResult:
    risk = await ctx.risk_service.get_risk(
        user_id=ctx.user_id,
        risk_id=args["risk_id"],
        org_id=args.get("org_id", ctx.org_id),
        workspace_id=args.get("workspace_id", ctx.workspace_id),
    )
    return ToolResult.success(risk.model_dump())


async def _grc_list_tasks(args: dict, ctx: ToolContext) -> ToolResult:
    limit = min(int(args.get("limit", 20)), _LIST_ROW_CAP)
    offset = int(args.get("offset", 0))
    entity_id = args.get("entity_id")
    framework_id = args.get("framework_id")

    # When filtering by a specific entity or framework, drop org/workspace scope —
    # tasks live in whatever workspace they were created in; entity_id is authoritative.
    scoped = bool(entity_id or framework_id)
    org_id = None if scoped else args.get("org_id", ctx.org_id)
    workspace_id = None if scoped else args.get("workspace_id", ctx.workspace_id)

    # framework_id filtering: query tasks whose entity_id is a control within that framework
    if framework_id and not entity_id:
        async with ctx.pool.acquire() as conn:
            # Build parameterized query — never interpolate user-supplied values directly
            conditions = [
                "c.framework_id = $1::uuid",
                "v.entity_type = 'control'",
                "NOT v.is_deleted",
                "v.tenant_key = $2",
            ]
            params: list = [framework_id, ctx.tenant_key]
            idx = 3

            if args.get("status_code"):
                conditions.append(f"v.status_code = ${idx}")
                params.append(str(args["status_code"]))
                idx += 1
            if args.get("priority_code"):
                conditions.append(f"v.priority_code = ${idx}")
                params.append(str(args["priority_code"]))
                idx += 1
            if args.get("assignee_user_id"):
                conditions.append(f"v.assignee_user_id = ${idx}::uuid")
                params.append(str(args["assignee_user_id"]))
                idx += 1
            if args.get("is_overdue"):
                conditions.append("v.due_date < NOW() AND NOT v.is_terminal")

            where = " AND ".join(conditions)
            rows = await conn.fetch(
                f"""
                SELECT v.id::text, v.task_type_code, v.task_type_name, v.priority_code,
                       v.status_code, v.status_name, v.is_terminal,
                       v.due_date::text, v.entity_type, v.entity_id::text,
                       v.assignee_user_id::text, v.title, v.description
                FROM "08_tasks"."40_vw_task_detail" v
                JOIN "05_grc_library"."13_fct_controls" c ON c.id = v.entity_id
                WHERE {where}
                ORDER BY v.due_date ASC NULLS LAST
                LIMIT {limit} OFFSET {offset}
                """,
                *params,
            )
        items = [dict(r) for r in rows]
        return ToolResult.success({
            "items": items,
            "total_count": len(items),
            "returned_count": len(items),
            "has_more": len(items) == limit,
            "note": "Tasks on controls within this framework. Risk tasks not included — use grc_get_framework_hierarchy for full picture.",
        })

    result = await ctx.task_service.list_tasks(
        user_id=ctx.user_id,
        tenant_key=ctx.tenant_key,
        org_id=org_id,
        workspace_id=workspace_id,
        status_code=args.get("status_code"),
        priority_code=args.get("priority_code"),
        entity_type=args.get("entity_type"),
        entity_id=entity_id,
        is_overdue=args.get("is_overdue"),
        assignee_user_id=args.get("assignee_user_id"),
        limit=limit,
        offset=offset,
    )
    items = result.items if hasattr(result, "items") else result
    total = result.total if hasattr(result, "total") else len(items)
    return ToolResult.success({
        "items": [i.model_dump() if hasattr(i, "model_dump") else i for i in items],
        "total_count": total,
        "returned_count": len(items),
        "has_more": (offset + len(items)) < total,
    })


async def _grc_get_task(args: dict, ctx: ToolContext) -> ToolResult:
    task = await ctx.task_service.get_task(
        user_id=ctx.user_id,
        task_id=args["task_id"],
    )
    return ToolResult.success(task.model_dump())


# ---------------------------------------------------------------------------
# Hierarchy handlers — traverse the GRC entity graph via dedicated views
# ---------------------------------------------------------------------------

async def _grc_get_control_hierarchy(args: dict, ctx: ToolContext) -> ToolResult:
    control_id = args["control_id"]
    async with ctx.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT control_id, framework_id, requirement_id, control_code,
                   framework_name, requirement_code, requirement_name,
                   direct_task_count, direct_open_task_count, direct_overdue_task_count,
                   evidence_task_count, remediation_task_count,
                   linked_risk_count, critical_risk_count, high_risk_count,
                   linked_risk_ids, linked_risk_codes, linked_risk_titles, linked_risk_levels,
                   risk_task_count, risk_open_task_count
            FROM "05_grc_library"."83_vw_control_hierarchy"
            WHERE control_id = $1
            """,
            control_id,
        )
    if row is None:
        return ToolResult.failure(f"Control {control_id} not found")
    data = dict(row)
    # Convert postgres arrays to plain lists
    for key in ("linked_risk_ids", "linked_risk_codes", "linked_risk_titles", "linked_risk_levels"):
        val = data.get(key)
        data[key] = list(val) if val else []
    return ToolResult.success(data)


async def _grc_get_risk_hierarchy(args: dict, ctx: ToolContext) -> ToolResult:
    risk_id = args["risk_id"]
    async with ctx.pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT risk_id, org_id, workspace_id, risk_code, risk_level_code,
                   risk_status, risk_category_code, title,
                   direct_task_count, direct_open_task_count, direct_overdue_task_count,
                   linked_control_count, linked_control_ids, linked_control_codes,
                   linked_framework_ids, linked_framework_names,
                   control_task_count, control_open_task_count
            FROM "05_grc_library"."84_vw_risk_hierarchy"
            WHERE risk_id = $1
            """,
            risk_id,
        )
    if row is None:
        return ToolResult.failure(f"Risk {risk_id} not found")
    data = dict(row)
    for key in ("linked_control_ids", "linked_control_codes", "linked_framework_ids", "linked_framework_names"):
        val = data.get(key)
        data[key] = list(val) if val else []
    return ToolResult.success(data)


async def _grc_get_framework_hierarchy(args: dict, ctx: ToolContext) -> ToolResult:
    framework_id = args["framework_id"]
    has_tasks = args.get("has_tasks")
    has_risks = args.get("has_risks")
    limit = min(int(args.get("limit", 50)), 100)
    offset = int(args.get("offset", 0))

    conditions = ["framework_id = $1"]
    params: list = [framework_id]
    idx = 2

    if has_tasks:
        conditions.append("(control_task_count > 0 OR risk_task_count > 0)")
    if has_risks:
        conditions.append("linked_risk_count > 0")

    where = " AND ".join(conditions)

    async with ctx.pool.acquire() as conn:
        total_row = await conn.fetchrow(
            f'SELECT COUNT(*) FROM "05_grc_library"."85_vw_framework_hierarchy" WHERE {where}',
            *params,
        )
        total = total_row[0] if total_row else 0

        rows = await conn.fetch(
            f"""
            SELECT control_id, control_code, criticality_code,
                   requirement_code, requirement_name,
                   control_task_count, control_open_tasks, control_overdue_tasks, evidence_task_count,
                   linked_risk_count, high_critical_risk_count, risk_codes, risk_levels,
                   risk_task_count, risk_open_tasks
            FROM "05_grc_library"."85_vw_framework_hierarchy"
            WHERE {where}
            ORDER BY control_overdue_tasks DESC, high_critical_risk_count DESC, control_code
            LIMIT {limit} OFFSET {offset}
            """,
            *params,
        )

    items = []
    for r in rows:
        item = dict(r)
        item["risk_codes"] = list(item["risk_codes"]) if item["risk_codes"] else []
        item["risk_levels"] = list(item["risk_levels"]) if item["risk_levels"] else []
        items.append(item)

    # Framework-level totals
    summary = {
        "total_controls_in_framework": total,
        "controls_returned": len(items),
        "total_control_tasks": sum(i["control_task_count"] for i in items),
        "total_open_control_tasks": sum(i["control_open_tasks"] for i in items),
        "total_evidence_tasks": sum(i["evidence_task_count"] for i in items),
        "total_risks": sum(i["linked_risk_count"] for i in items),
        "total_risk_tasks": sum(i["risk_task_count"] for i in items),
    }

    return ToolResult.success({
        "framework_id": framework_id,
        "summary": summary,
        "controls": items,
        "has_more": (offset + len(items)) < total,
    })


async def _grc_list_tasks_for_entity(args: dict, ctx: ToolContext) -> ToolResult:
    """
    Returns all tasks for a control or risk, including indirect tasks via linked entities.
    For control: direct control tasks + tasks on linked risks.
    For risk: direct risk tasks + tasks on linked controls.
    """
    entity_type = args["entity_type"]
    entity_id = args["entity_id"]
    include_indirect = args.get("include_indirect", True)
    limit = min(int(args.get("limit", 50)), _LIST_ROW_CAP)

    async with ctx.pool.acquire() as conn:
        # Direct tasks
        direct_rows = await conn.fetch(
            """
            SELECT t.id::text, t.task_type_code, t.task_type_name, t.priority_code,
                   t.status_code, t.status_name, t.is_terminal,
                   t.due_date::text, t.entity_type, t.entity_id::text,
                   t.assignee_user_id::text,
                   t.title, t.description
            FROM "08_tasks"."40_vw_task_detail" t
            WHERE t.entity_id = $1::uuid AND t.entity_type = $2 AND NOT t.is_deleted
            ORDER BY t.due_date ASC NULLS LAST
            LIMIT $3
            """,
            entity_id, entity_type, limit,
        )
        direct_items = [
            {**dict(r), "source": "direct"} for r in direct_rows
        ]

        indirect_items = []
        if include_indirect and len(direct_items) < limit:
            remaining = limit - len(direct_items)
            if entity_type == "control":
                # Get tasks on risks linked to this control
                indirect_rows = await conn.fetch(
                    """
                    SELECT t.id::text, t.task_type_code, t.task_type_name, t.priority_code,
                           t.status_code, t.status_name, t.is_terminal,
                           t.due_date::text, t.entity_type, t.entity_id::text,
                           t.assignee_user_id::text,
                           t.title, t.description,
                           r.risk_code, rp.property_value AS risk_title
                    FROM "08_tasks"."40_vw_task_detail" t
                    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm
                        ON rcm.risk_id = t.entity_id
                    JOIN "14_risk_registry"."10_fct_risks" r ON r.id = rcm.risk_id
                    LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" rp
                        ON rp.risk_id = r.id AND rp.property_key = 'title'
                    WHERE rcm.control_id = $1::uuid AND t.entity_type = 'risk' AND NOT t.is_deleted
                    ORDER BY t.due_date ASC NULLS LAST
                    LIMIT $2
                    """,
                    entity_id, remaining,
                )
                indirect_items = [
                    {**dict(r), "source": f"via_risk:{r['risk_code']} — {r['risk_title'] or ''}"}
                    for r in indirect_rows
                ]
            elif entity_type == "risk":
                # Get tasks on controls linked to this risk
                indirect_rows = await conn.fetch(
                    """
                    SELECT t.id::text, t.task_type_code, t.task_type_name, t.priority_code,
                           t.status_code, t.status_name, t.is_terminal,
                           t.due_date::text, t.entity_type, t.entity_id::text,
                           t.assignee_user_id::text,
                           t.title, t.description,
                           c.control_code
                    FROM "08_tasks"."40_vw_task_detail" t
                    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm
                        ON rcm.control_id = t.entity_id
                    JOIN "05_grc_library"."13_fct_controls" c ON c.id = rcm.control_id
                    WHERE rcm.risk_id = $1::uuid AND t.entity_type = 'control' AND NOT t.is_deleted
                    ORDER BY t.due_date ASC NULLS LAST
                    LIMIT $2
                    """,
                    entity_id, remaining,
                )
                indirect_items = [
                    {**dict(r), "source": f"via_control:{r['control_code']}"}
                    for r in indirect_rows
                ]

    all_items = direct_items + indirect_items
    return ToolResult.success({
        "items": all_items,
        "total_count": len(all_items),
        "direct_count": len(direct_items),
        "indirect_count": len(indirect_items),
        "has_more": len(all_items) >= limit,
    })


async def _grc_navigate(args: dict, ctx: ToolContext) -> ToolResult:
    """Navigation action — returns a special marker so the agent emits a navigate SSE event."""
    entity_type = args.get("entity_type", "")
    entity_id = args.get("entity_id", "")
    framework_id = args.get("framework_id")
    label = args.get("label") or entity_type

    if not entity_type or not entity_id:
        return ToolResult.failure("entity_type and entity_id are required")

    return ToolResult(
        output={
            "_navigate": True,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "framework_id": framework_id,
            "label": label,
            "message": f"Navigating to {label}",
        },
        token_estimate=20,
        error=None,
    )


async def _grc_navigate_page(args: dict, ctx: ToolContext) -> ToolResult:
    """Page navigation action — returns a special marker so the agent emits a navigate_page SSE event."""
    page = args.get("page", "")
    label = args.get("label") or page.replace("_", " ").title()

    if not page:
        return ToolResult.failure("page is required")

    return ToolResult(
        output={
            "_navigate_page": True,
            "page": page,
            "label": label,
            "message": f"Navigating to {label}",
        },
        token_estimate=20,
        error=None,
    )


# ---------------------------------------------------------------------------
# Write tool handlers — each creates an approval record, never executes directly
# ---------------------------------------------------------------------------

import datetime as _dt
import uuid as _uuid_mod


async def _create_approval(args: dict, ctx: ToolContext, *, tool_name: str, entity_type: str, operation: str, label: str) -> ToolResult:
    """Common helper: persist an approval request and return _approval sentinel."""
    _approval_repo_mod = import_module("backend.20_ai.06_approvals.repository")
    repo = _approval_repo_mod.ApprovalRepository()
    expires_at = _dt.datetime.utcnow() + _dt.timedelta(hours=72)
    async with ctx.pool.acquire() as conn:
        record = await repo.create_approval(
            conn,
            tenant_key=ctx.tenant_key,
            requester_id=ctx.user_id,
            org_id=ctx.org_id,
            tool_name=tool_name,
            tool_category="write",
            entity_type=entity_type,
            operation=operation,
            payload_json=args,
            diff_json={"after": args},
            expires_at=expires_at,
        )
    return ToolResult(
        output={
            "_approval": True,
            "approval_id": record.id,
            "tool_name": tool_name,
            "entity_type": entity_type,
            "operation": operation,
            "label": label,
            "message": f"Approval request created for {label}. Waiting for user confirmation.",
        },
        token_estimate=30,
    )


async def _grc_create_framework(args: dict, ctx: ToolContext) -> ToolResult:
    name = args.get("name", args.get("framework_code", "framework"))
    return await _create_approval(args, ctx, tool_name="grc_create_framework", entity_type="framework", operation="create", label=f"Create framework: {name}")


async def _grc_create_requirement(args: dict, ctx: ToolContext) -> ToolResult:
    name = args.get("name", args.get("requirement_code", "requirement"))
    return await _create_approval(args, ctx, tool_name="grc_create_requirement", entity_type="requirement", operation="create", label=f"Create requirement: {name}")


async def _grc_bulk_create_requirements(args: dict, ctx: ToolContext) -> ToolResult:
    count = len(args.get("requirements", []))
    return await _create_approval(args, ctx, tool_name="grc_bulk_create_requirements", entity_type="requirement", operation="bulk_create", label=f"Bulk create {count} requirements")


async def _grc_create_control(args: dict, ctx: ToolContext) -> ToolResult:
    name = args.get("name", args.get("control_code", "control"))
    return await _create_approval(args, ctx, tool_name="grc_create_control", entity_type="control", operation="create", label=f"Create control: {name}")


async def _grc_bulk_create_controls(args: dict, ctx: ToolContext) -> ToolResult:
    count = len(args.get("controls", []))
    return await _create_approval(args, ctx, tool_name="grc_bulk_create_controls", entity_type="control", operation="bulk_create", label=f"Bulk create {count} controls")


async def _grc_create_risk(args: dict, ctx: ToolContext) -> ToolResult:
    # Inject org_id/workspace_id from session context; auto-generate risk_code if absent
    merged = {"org_id": ctx.org_id, "workspace_id": ctx.workspace_id, **args}
    if not merged.get("risk_code"):
        merged["risk_code"] = f"RISK-{str(_uuid_mod.uuid4())[:8].upper()}"
    title = merged.get("title", merged.get("risk_code", "risk"))
    return await _create_approval(merged, ctx, tool_name="grc_create_risk", entity_type="risk", operation="create", label=f"Create risk: {title}")


async def _grc_bulk_create_risks(args: dict, ctx: ToolContext) -> ToolResult:
    merged = {"org_id": ctx.org_id, "workspace_id": ctx.workspace_id, **args}
    count = len(merged.get("risks", []))
    return await _create_approval(merged, ctx, tool_name="grc_bulk_create_risks", entity_type="risk", operation="bulk_create", label=f"Bulk create {count} risks")


async def _grc_create_task(args: dict, ctx: ToolContext) -> ToolResult:
    merged = {"org_id": ctx.org_id, "workspace_id": ctx.workspace_id, **args}
    title = merged.get("title", "task")
    return await _create_approval(merged, ctx, tool_name="grc_create_task", entity_type="task", operation="create", label=f"Create task: {title}")


async def _grc_bulk_create_tasks(args: dict, ctx: ToolContext) -> ToolResult:
    merged = {"org_id": ctx.org_id, "workspace_id": ctx.workspace_id, **args}
    count = len(merged.get("tasks", []))
    entity = merged.get("entity_type", "entity")
    return await _create_approval(merged, ctx, tool_name="grc_bulk_create_tasks", entity_type="task", operation="bulk_create", label=f"Bulk create {count} tasks for {entity}")


async def _grc_map_control_to_risk(args: dict, ctx: ToolContext) -> ToolResult:
    merged = {"org_id": ctx.org_id, "workspace_id": ctx.workspace_id, **args}
    return await _create_approval(merged, ctx, tool_name="grc_map_control_to_risk", entity_type="control_risk_mapping", operation="create", label="Map control to risk")


async def _grc_generate_report(args: dict, ctx: ToolContext) -> ToolResult:
    """
    Queue a GRC report for AI generation. Returns immediately with report_id + status.
    Emits _report_queued sentinel so the agent loop can emit a report_queued SSE event.
    """
    if not ctx.org_id:
        return ToolResult.failure("org_id is required to generate a report (not set in session context)")

    _report_svc_mod = import_module("backend.20_ai.20_reports.service")
    _report_schemas_mod = import_module("backend.20_ai.20_reports.schemas")
    _settings_mod = import_module("backend.00_config.settings")
    _cache_mod = import_module("backend.01_core.cache")

    settings = _settings_mod.load_settings()
    cache = _cache_mod.NullCacheManager()

    report_type = args["report_type"]
    framework_id = args.get("framework_id")
    risk_id = args.get("risk_id")
    control_id = args.get("control_id")
    title = args.get("title")

    _FRAMEWORK_REQUIRED_TYPES = {"framework_compliance", "framework_readiness", "framework_gap_analysis"}
    if report_type in _FRAMEWORK_REQUIRED_TYPES and not framework_id:
        return ToolResult.failure(
            f"report_type '{report_type}' requires a framework_id. "
            "Use grc_list_frameworks to list available frameworks, then ask the user to confirm which one before calling grc_generate_report again."
        )

    # Build scoped parameters — only include keys that were provided
    parameters: dict = {}
    if framework_id:
        parameters["framework_id"] = framework_id
    if risk_id:
        parameters["risk_id"] = risk_id
    if control_id:
        parameters["control_id"] = control_id
    for key in ("risk_level", "risk_status", "task_status", "task_priority"):
        if args.get(key):
            parameters[key] = args[key]

    request = _report_schemas_mod.GenerateReportRequest(
        report_type=report_type,
        title=title,
        org_id=ctx.org_id,
        workspace_id=ctx.workspace_id,
        parameters=parameters,
    )

    svc = _report_svc_mod.ReportService(database_pool=ctx.pool, settings=settings, cache=cache)
    report = await svc.generate_report(
        user_id=ctx.user_id,
        tenant_key=ctx.tenant_key,
        request=request,
    )

    return ToolResult(
        output={
            "_report_queued": True,
            "report_id": report.id,
            "report_type": report.report_type,
            "title": report.title,
            "status": report.status_code,
            "message": f"Report queued — ID: {report.id}",
        },
        token_estimate=20,
        error=None,
    )


async def _grc_propose_form_fields(args: dict, ctx: ToolContext) -> ToolResult:
    """
    Form-fill terminal action: emits _form_fill_proposed sentinel so the agent loop
    can forward a form_fill_proposed SSE event. No DB write, no approval required.
    """
    fields = args.get("fields") or {}
    explanation = args.get("explanation", "")
    if not fields:
        return ToolResult.failure("fields must be a non-empty object")
    return ToolResult(
        output={
            "_form_fill_proposed": True,
            "fields": fields,
            "explanation": explanation,
        },
        token_estimate=20,
        error=None,
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_DISPATCH_TABLE: dict[str, Any] = {
    # Insight
    "grc_framework_health": _grc_framework_health,
    "grc_requirement_gaps": _grc_requirement_gaps,
    "grc_risk_concentration": _grc_risk_concentration,
    "grc_task_health": _grc_task_health,
    "grc_control_health": _grc_control_health,
    # Navigation
    "grc_list_frameworks": _grc_list_frameworks,
    "grc_get_framework": _grc_get_framework,
    "grc_list_requirements": _grc_list_requirements,
    "grc_list_controls": _grc_list_controls,
    "grc_get_control": _grc_get_control,
    "grc_list_risks": _grc_list_risks,
    "grc_get_risk": _grc_get_risk,
    "grc_list_tasks": _grc_list_tasks,
    "grc_get_task": _grc_get_task,
    # Hierarchy
    "grc_get_control_hierarchy": _grc_get_control_hierarchy,
    "grc_get_risk_hierarchy": _grc_get_risk_hierarchy,
    "grc_get_framework_hierarchy": _grc_get_framework_hierarchy,
    "grc_list_tasks_for_entity": _grc_list_tasks_for_entity,
    # Action
    "grc_navigate": _grc_navigate,
    "grc_navigate_page": _grc_navigate_page,
    # Report generation (sentinel — queues async job)
    "grc_generate_report": _grc_generate_report,
    # Form fill (sentinel — no approval)
    "grc_propose_form_fields": _grc_propose_form_fields,
    # Write (approval-gated)
    "grc_create_framework": _grc_create_framework,
    "grc_create_requirement": _grc_create_requirement,
    "grc_bulk_create_requirements": _grc_bulk_create_requirements,
    "grc_create_control": _grc_create_control,
    "grc_bulk_create_controls": _grc_bulk_create_controls,
    "grc_create_risk": _grc_create_risk,
    "grc_bulk_create_risks": _grc_bulk_create_risks,
    "grc_create_task": _grc_create_task,
    "grc_bulk_create_tasks": _grc_bulk_create_tasks,
    "grc_map_control_to_risk": _grc_map_control_to_risk,
}


class MCPToolDispatcher:
    """
    Routes tool calls from the GRC agent to the appropriate handler.

    Usage:
        dispatcher = MCPToolDispatcher()
        result = await dispatcher.dispatch("grc_task_health", args, ctx)
    """

    async def dispatch(
        self,
        tool_name: str,
        tool_input: dict,
        context: ToolContext,
    ) -> ToolResult:
        handler = _DISPATCH_TABLE.get(tool_name)
        if handler is None:
            return ToolResult.failure(f"Unknown tool: {tool_name}")

        try:
            return await handler(tool_input, context)
        except Exception as exc:
            _logger.exception("Tool %s failed: %s", tool_name, exc)
            return ToolResult.failure(f"Tool {tool_name} failed: {exc!s}")
