"""GRC access grant enforcement — reusable functions for filtering data by user's grants.

A user with a GRC role assignment has one of two access levels:
  1. **All access** — no grants exist (they see all frameworks + engagements in the org)
  2. **Scoped access** — one or more grants exist, limiting them to specific
     framework deployments and/or engagements

Usage in routers/services:
    allowed = await get_allowed_scope_ids(conn, user_id=..., org_id=..., scope_type="engagement")
    if allowed is not None:
        # Filter: only show engagements in `allowed`
        engagements = [e for e in engagements if e.id in allowed]
    # else: user sees everything (no grants = all access)
"""
from __future__ import annotations

from importlib import import_module

import asyncpg

_telemetry_module = import_module("backend.01_core.telemetry")
instrument_module_functions = _telemetry_module.instrument_module_functions

SCHEMA = '"03_auth_manage"'


async def get_grc_role_for_user(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
) -> str | None:
    """Return the active GRC role code for a user in an org, or None.

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.

    Returns:
        GRC role code string (e.g. 'grc_lead'), or None if not assigned.
    """
    return await conn.fetchval(
        f"""
        SELECT grc_role_code
        FROM {SCHEMA}."47_lnk_grc_role_assignments"
        WHERE user_id = $1::UUID AND org_id = $2::UUID AND revoked_at IS NULL
        LIMIT 1
        """,
        user_id, org_id,
    )


async def is_internal_role(
    conn: asyncpg.Connection,
    *,
    role_code: str | None,
) -> bool:
    """Return True if the role code belongs to an 'internal' GRC category.

    Internal roles (practitioner, engineer, ciso) bypass restrictive scoping.
    """
    INTERNAL_ROLES = {"grc_practitioner", "grc_engineer", "grc_ciso"}
    return role_code in INTERNAL_ROLES


async def has_any_grants(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
) -> bool:
    """Check whether the user has any active access grants (scoped access).

    If False, the user has "all access" (no narrowing grants).
    If True, the user's access is limited to their specific grants.

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.

    Returns:
        True if the user has at least one active grant, False otherwise.
    """
    result = await conn.fetchval(
        f"""
        SELECT EXISTS (
            SELECT 1
            FROM {SCHEMA}."48_lnk_grc_access_grants" g
            JOIN {SCHEMA}."47_lnk_grc_role_assignments" ra
              ON ra.id = g.grc_role_assignment_id
            WHERE ra.user_id = $1::UUID
              AND ra.org_id = $2::UUID
              AND ra.revoked_at IS NULL
              AND g.revoked_at IS NULL
        )
        """,
        user_id, org_id,
    )
    return bool(result)


async def get_allowed_scope_ids(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
    scope_type: str,
) -> set[str] | None:
    """Return the set of scope IDs the user has access to, or None for all access.

    Logic:
    - If the user has no GRC role assignment → None (no GRC filtering)
    - If the user has an INTERNAL GRC role (practitioner, engineer, ciso) → None (all access)
    - If the user has a GRC role but NO access grants → None (all access)
    - If the user has grants but none of the requested scope_type → empty set
    - If the user has grants of the requested scope_type → set of allowed IDs
    """
    # Check if user even has a GRC role
    role = await get_grc_role_for_user(conn, user_id=user_id, org_id=org_id)
    if not role:
        return None  # Not a GRC role holder

    # Exempt 'internal' roles from restrictive scoping
    if await is_internal_role(conn, role_code=role):
        return None

    # Check if user has any grants at all
    has_grants = await has_any_grants(conn, user_id=user_id, org_id=org_id)
    if not has_grants:
        return None  # All access — no narrowing

    # User has grants — return only the ones matching the requested scope type
    rows = await conn.fetch(
        f"""
        SELECT g.scope_id::text
        FROM {SCHEMA}."48_lnk_grc_access_grants" g
        JOIN {SCHEMA}."47_lnk_grc_role_assignments" ra
          ON ra.id = g.grc_role_assignment_id
        WHERE ra.user_id = $1::UUID
          AND ra.org_id = $2::UUID
          AND ra.revoked_at IS NULL
          AND g.revoked_at IS NULL
          AND g.scope_type = $3
        """,
        user_id, org_id, scope_type,
    )
    return {str(r["scope_id"]) for r in rows}



async def get_allowed_framework_template_ids(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
) -> set[str] | None:
    """Return allowed framework template IDs from both framework and engagement grants.

    Resolves the grant chain bidirectionally:
    - Framework grants (deployment IDs) → deployment.framework_id
    - Engagement grants → engagement.framework_deployment_id → deployment.framework_id

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.

    Returns:
        None if no filtering needed (no GRC role or no grants = all access).
        Set of framework template IDs if scoped.
    """
    role = await get_grc_role_for_user(conn, user_id=user_id, org_id=org_id)
    if not role:
        return None
    if await is_internal_role(conn, role_code=role):
        return None
    if not await has_any_grants(conn, user_id=user_id, org_id=org_id):
        return None

    # Collect deployment IDs from both grant types
    all_deployment_ids: set[str] = set()

    # 1. Direct framework grants → deployment IDs
    fw_rows = await conn.fetch(
        f"""
        SELECT g.scope_id::text
        FROM {SCHEMA}."48_lnk_grc_access_grants" g
        JOIN {SCHEMA}."47_lnk_grc_role_assignments" ra
          ON ra.id = g.grc_role_assignment_id
        WHERE ra.user_id = $1::UUID AND ra.org_id = $2::UUID
          AND ra.revoked_at IS NULL AND g.revoked_at IS NULL
          AND g.scope_type = 'framework'
        """,
        user_id, org_id,
    )
    all_deployment_ids.update(str(r["scope_id"]) for r in fw_rows)

    # 2. Engagement grants → resolve to framework_deployment_ids
    eng_rows = await conn.fetch(
        f"""
        SELECT g.scope_id::text
        FROM {SCHEMA}."48_lnk_grc_access_grants" g
        JOIN {SCHEMA}."47_lnk_grc_role_assignments" ra
          ON ra.id = g.grc_role_assignment_id
        WHERE ra.user_id = $1::UUID AND ra.org_id = $2::UUID
          AND ra.revoked_at IS NULL AND g.revoked_at IS NULL
          AND g.scope_type = 'engagement'
        """,
        user_id, org_id,
    )
    eng_ids = [str(r["scope_id"]) for r in eng_rows]
    if eng_ids:
        dep_rows = await conn.fetch(
            """
            SELECT DISTINCT framework_deployment_id::text
            FROM "12_engagements"."10_fct_audit_engagements"
            WHERE id = ANY($1::UUID[])
            """,
            eng_ids,
        )
        all_deployment_ids.update(
            str(r["framework_deployment_id"]) for r in dep_rows if r["framework_deployment_id"]
        )

    if not all_deployment_ids:
        return set()

    # 3. Resolve deployment IDs → framework template IDs
    tmpl_rows = await conn.fetch(
        """
        SELECT DISTINCT framework_id::text
        FROM "05_grc_library"."16_fct_framework_deployments"
        WHERE id = ANY($1::UUID[])
        """,
        list(all_deployment_ids),
    )
    return {str(r["framework_id"]) for r in tmpl_rows}


async def get_allowed_control_ids(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
) -> set[str] | None:
    """Return allowed control IDs based on framework grants, or None for all access.

    Resolves: framework grants → framework template IDs → control IDs.

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.

    Returns:
        None if no filtering needed. Set of control IDs if scoped.
    """
    fw_ids = await get_allowed_framework_template_ids(conn, user_id=user_id, org_id=org_id)
    if fw_ids is None:
        return None
    if not fw_ids:
        return set()
    rows = await conn.fetch(
        """
        SELECT id::text FROM "05_grc_library"."13_fct_controls"
        WHERE framework_id = ANY($1::UUID[])
        """,
        list(fw_ids),
    )
    return {str(r["id"]) for r in rows}


async def get_allowed_test_ids(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
) -> set[str] | None:
    """Return allowed test IDs based on framework grants, or None for all access.

    Resolves: framework grants → control IDs → test IDs via test-control mappings.

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.

    Returns:
        None if no filtering needed. Set of test IDs if scoped.
    """
    control_ids = await get_allowed_control_ids(conn, user_id=user_id, org_id=org_id)
    if control_ids is None:
        return None
    if not control_ids:
        return set()
    rows = await conn.fetch(
        """
        SELECT DISTINCT control_test_id::text
        FROM "05_grc_library"."30_lnk_test_control_mappings"
        WHERE control_id = ANY($1::UUID[])
        """,
        list(control_ids),
    )
    return {str(r["control_test_id"]) for r in rows}


async def get_allowed_risk_ids(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
) -> set[str] | None:
    """Return allowed risk IDs based on framework grants, or None for all access.

    Resolves: framework grants → control IDs → risk IDs via risk-control mappings.

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.

    Returns:
        None if no filtering needed. Set of risk IDs if scoped.
    """
    control_ids = await get_allowed_control_ids(conn, user_id=user_id, org_id=org_id)
    if control_ids is None:
        return None
    if not control_ids:
        return set()
    rows = await conn.fetch(
        """
        SELECT DISTINCT risk_id::text
        FROM "14_risk_registry"."30_lnk_risk_control_mappings"
        WHERE control_id = ANY($1::UUID[])
        """,
        list(control_ids),
    )
    return {str(r["risk_id"]) for r in rows}


async def check_engagement_access(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
    engagement_id: str,
) -> bool:
    """Check whether the user has access to a specific engagement.

    Returns True if:
    - User has no GRC role (standard permissions apply — no GRC filtering)
    - User has GRC role with no grants (all access)
    - User has a grant for this specific engagement
    - User has a framework grant that matches the engagement's framework deployment

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.
        engagement_id: UUID of the engagement to check.

    Returns:
        True if access is allowed.
    """
    allowed = await get_allowed_scope_ids(conn, user_id=user_id, org_id=org_id, scope_type="engagement")
    if allowed is None:
        return True  # All access
    if engagement_id in allowed:
        return True  # Direct engagement grant

    # Also check if user has a framework grant matching the engagement's framework_deployment_id
    fw_allowed = await get_allowed_scope_ids(conn, user_id=user_id, org_id=org_id, scope_type="framework")
    if fw_allowed is None:
        return True  # Already handled above, but safety check

    if fw_allowed:
        # Check if the engagement's framework_deployment_id is in the allowed frameworks
        eng_fw_id = await conn.fetchval(
            """
            SELECT framework_deployment_id::text
            FROM "12_engagements"."10_fct_audit_engagements"
            WHERE id = $1::UUID
            """,
            engagement_id,
        )
        if eng_fw_id and eng_fw_id in fw_allowed:
            return True

    return False


async def filter_engagement_ids(
    conn: asyncpg.Connection,
    *,
    user_id: str,
    org_id: str,
    engagement_ids: list[str],
) -> list[str]:
    """Filter a list of engagement IDs to only those the user can access.

    Args:
        conn: Active asyncpg database connection.
        user_id: UUID of the user.
        org_id: UUID of the org.
        engagement_ids: List of engagement IDs to filter.

    Returns:
        Filtered list of engagement IDs.
    """
    if not engagement_ids:
        return []

    # Check engagement grants
    eng_allowed = await get_allowed_scope_ids(conn, user_id=user_id, org_id=org_id, scope_type="engagement")
    if eng_allowed is None:
        return engagement_ids  # All access

    # Also check framework grants
    fw_allowed = await get_allowed_scope_ids(conn, user_id=user_id, org_id=org_id, scope_type="framework")

    # Direct engagement grants
    result = [eid for eid in engagement_ids if eid in eng_allowed]

    # Framework-based access: check engagements whose framework_deployment_id is allowed
    if fw_allowed:
        remaining = [eid for eid in engagement_ids if eid not in eng_allowed]
        if remaining:
            placeholders = ", ".join(f"${i+1}::UUID" for i in range(len(remaining)))
            rows = await conn.fetch(
                f"""
                SELECT id::text, framework_deployment_id::text
                FROM "12_engagements"."10_fct_audit_engagements"
                WHERE id IN ({placeholders})
                """,
                *remaining,
            )
            for row in rows:
                fw_dep_id = str(row["framework_deployment_id"]) if row["framework_deployment_id"] else None
                if fw_dep_id and fw_dep_id in fw_allowed:
                    result.append(str(row["id"]))

    return result


instrument_module_functions(
    globals(),
    namespace="grc_roles.access_check",
    logger_name="backend.grc_roles.access_check.instrumentation",
)
