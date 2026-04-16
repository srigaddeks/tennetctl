"""Scoped group provisioning and GRC role assignment.

Permission scoping model:
  - Org/workspace access is enforced via DIRECT membership tables
    (31_lnk_org_memberships, 36_lnk_workspace_memberships) with CASE
    mapping in _permission_check.py (e.g. owner → org_admin role).
  - GRC roles are stored as `grc_role_code` on workspace membership
    records and/or via 47_lnk_grc_role_assignments (org-level identity).

The 17 global system groups (org_admins, workspace_admins, grc_leads, etc.)
are TEMPLATE definitions with no scope_org_id/scope_workspace_id.  They exist
for admin UI display and group-based reporting only.

IMPORTANT: Users must NOT be added to these unscoped global groups for
org/workspace roles, because _permission_check.py Branch 1 treats unscoped
group permissions as PLATFORM-level.  Adding a user to the global `org_admins`
group would grant them org_admin permissions across ALL orgs (super admin),
not just their own org.

Org/workspace member → group assignment is therefore a no-op.  GRC role
assignment sets the `grc_role_code` column on workspace membership directly.
"""
from __future__ import annotations

import asyncpg

SCHEMA = '"03_auth_manage"'

# ── GRC role codes (shared with invitation flow) ─────────────────────────

_GRC_ROLE_CODES: frozenset[str] = frozenset({
    "grc_lead",
    "grc_sme",
    "grc_practitioner",
    "grc_engineer",
    "grc_ciso",
    "grc_lead_auditor",
    "grc_staff_auditor",
    "grc_vendor",
})


# ── Org group provisioning (no-op) ──────────────────────────────────────

async def provision_org_system_groups(
    conn: asyncpg.Connection,
    *,
    org_id: str,
    tenant_key: str,
    created_by: str | None,
    now,
) -> None:
    """No-op.  Org access is resolved via direct membership + CASE mapping.

    Args:
        conn: Active asyncpg database connection.
        org_id: UUID of the newly created org.
        tenant_key: Tenant key for the org.
        created_by: UUID of the actor creating the org.
        now: Current timestamp.
    """


# ── Workspace group provisioning (no-op) ────────────────────────────────

async def provision_workspace_system_groups(
    conn: asyncpg.Connection,
    *,
    workspace_id: str,
    org_id: str,
    tenant_key: str,
    created_by: str | None,
    now,
    workspace_type_code: str | None = None,
) -> None:
    """No-op.  Workspace access is resolved via direct membership + CASE mapping.

    Args:
        conn: Active asyncpg database connection.
        workspace_id: UUID of the newly created workspace.
        org_id: UUID of the owning org.
        tenant_key: Tenant key.
        created_by: UUID of the actor creating the workspace.
        now: Current timestamp.
        workspace_type_code: Workspace type (e.g. 'grc', 'project', 'sandbox').
    """


# ── Org member group assignment (no-op) ─────────────────────────────────

async def assign_org_member_to_scoped_group(
    conn: asyncpg.Connection,
    *,
    org_id: str,
    user_id: str,
    membership_type: str,
    now,
    created_by: str | None,
) -> None:
    """No-op.  Org permissions resolve via direct membership in
    31_lnk_org_memberships (membership_type → role via CASE in
    _permission_check.py).  Do NOT add to global org_admins group —
    that would grant platform-wide org_admin permissions.

    Args:
        conn: Active asyncpg database connection.
        org_id: UUID of the org.
        user_id: UUID of the user.
        membership_type: Org membership role.
        now: Current timestamp.
        created_by: UUID of the actor.
    """


async def remove_org_member_from_scoped_groups(
    conn: asyncpg.Connection,
    *,
    org_id: str,
    user_id: str,
    now,
    deleted_by: str | None,
) -> None:
    """No-op.  Org access is enforced via direct membership checks."""


# ── Workspace member group assignment (no-op) ───────────────────────────

async def assign_workspace_member_to_scoped_group(
    conn: asyncpg.Connection,
    *,
    workspace_id: str,
    user_id: str,
    membership_type: str,
    now,
    created_by: str | None,
) -> None:
    """No-op.  Workspace permissions resolve via direct membership in
    36_lnk_workspace_memberships (membership_type → role via CASE in
    _permission_check.py).  Do NOT add to global workspace_admins group.

    Args:
        conn: Active asyncpg database connection.
        workspace_id: UUID of the workspace.
        user_id: UUID of the user.
        membership_type: Workspace membership role.
        now: Current timestamp.
        created_by: UUID of the actor.
    """


async def remove_workspace_member_from_scoped_groups(
    conn: asyncpg.Connection,
    *,
    workspace_id: str,
    user_id: str,
    now,
    deleted_by: str | None,
) -> None:
    """No-op.  Workspace access is enforced via direct membership checks."""


# ── GRC role on workspace membership ─────────────────────────────────────

async def assign_workspace_member_grc_role(
    conn: asyncpg.Connection,
    *,
    workspace_id: str,
    user_id: str,
    grc_role_code: str,
    now,
    created_by: str | None,
) -> None:
    """Set the GRC role for a workspace member.

    Updates `grc_role_code` on the active workspace membership record.
    Permission check reads this column directly via Branch 5 in
    _permission_check.py.

    Args:
        conn: Active asyncpg database connection.
        workspace_id: UUID of the GRC workspace.
        user_id: UUID of the user.
        grc_role_code: One of the GRC role codes (e.g. 'grc_practitioner', 'grc_engineer').
        now: Current timestamp.
        created_by: UUID of the actor.

    Raises:
        ValueError: If grc_role_code is not a recognised GRC workspace role.
    """
    if grc_role_code not in _GRC_ROLE_CODES:
        raise ValueError(
            f"Unknown GRC role code: {grc_role_code!r}. "
            f"Must be one of {sorted(_GRC_ROLE_CODES)}."
        )

    await conn.execute(
        f"""
        UPDATE {SCHEMA}."36_lnk_workspace_memberships"
        SET grc_role_code = $1, updated_at = NOW()
        WHERE workspace_id = $2::UUID
          AND user_id = $3::UUID
          AND is_deleted = FALSE
          AND is_active = TRUE
        """,
        grc_role_code, workspace_id, user_id,
    )


async def remove_workspace_member_from_grc_groups(
    conn: asyncpg.Connection,
    *,
    workspace_id: str,
    user_id: str,
    now,
    deleted_by: str | None,
) -> None:
    """Clear the GRC role for a workspace member.

    Sets `grc_role_code` to NULL on the active workspace membership record.

    Args:
        conn: Active asyncpg database connection.
        workspace_id: UUID of the GRC workspace.
        user_id: UUID of the user.
        now: Current timestamp.
        deleted_by: UUID of the actor.
    """
    await conn.execute(
        f"""
        UPDATE {SCHEMA}."36_lnk_workspace_memberships"
        SET grc_role_code = NULL, updated_at = NOW()
        WHERE workspace_id = $1::UUID
          AND user_id = $2::UUID
          AND is_deleted = FALSE
        """,
        workspace_id, user_id,
    )


async def get_workspace_member_grc_role(
    conn: asyncpg.Connection,
    *,
    workspace_id: str,
    user_id: str,
) -> str | None:
    """Return the active GRC role code for a user in a workspace, or None.

    Args:
        conn: Active asyncpg database connection.
        workspace_id: UUID of the workspace.
        user_id: UUID of the user.

    Returns:
        GRC role code string (e.g. 'grc_practitioner'), or None if not set.
    """
    return await conn.fetchval(
        f"""
        SELECT grc_role_code
        FROM {SCHEMA}."36_lnk_workspace_memberships"
        WHERE workspace_id = $1::UUID
          AND user_id = $2::UUID
          AND is_deleted = FALSE
          AND is_active = TRUE
        LIMIT 1
        """,
        workspace_id, user_id,
    )
