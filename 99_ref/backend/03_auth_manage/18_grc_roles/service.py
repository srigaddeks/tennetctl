"""Business logic for GRC role management."""
from __future__ import annotations

from importlib import import_module
from uuid import uuid4

import asyncpg

from .repository import GrcRoleRepository, _ROLE_CATEGORIES
from .schemas import (
    AssignGrcRoleRequest,
    CreateAccessGrantRequest,
    GrcAccessGrantListResponse,
    GrcAccessGrantResponse,
    GrcRoleAssignmentListResponse,
    GrcRoleAssignmentResponse,
    GrcTeamMemberResponse,
    GrcTeamResponse,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_time_module = import_module("backend.01_core.time_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
require_permission = _perm_check_module.require_permission
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
utc_now_sql = _time_module.utc_now_sql

_CACHE_PREFIX = "grc_team"
_CACHE_TTL = 300

logger = get_logger("backend.grc_roles")


def _assignment_response(row: dict) -> GrcRoleAssignmentResponse:
    """Convert a DB row dict to GrcRoleAssignmentResponse.

    Args:
        row: Dict from v_grc_team view or repository query.

    Returns:
        Pydantic response model.
    """
    return GrcRoleAssignmentResponse(
        id=row["assignment_id"],
        org_id=row["org_id"],
        user_id=row["user_id"],
        grc_role_code=row["grc_role_code"],
        role_name=row.get("role_name", ""),
        role_description=row.get("role_description"),
        email=row.get("email"),
        display_name=row.get("display_name"),
        assigned_by=row.get("assigned_by"),
        assigned_at=row["assigned_at"],
        active_grant_count=row.get("active_grant_count", 0),
        created_at=row.get("created_at", row["assigned_at"]),
    )


def _grant_response(row: dict) -> GrcAccessGrantResponse:
    """Convert a DB row dict to GrcAccessGrantResponse.

    Args:
        row: Dict from grants query.

    Returns:
        Pydantic response model.
    """
    return GrcAccessGrantResponse(
        id=row["id"],
        grc_role_assignment_id=row["grc_role_assignment_id"],
        scope_type=row["scope_type"],
        scope_id=row["scope_id"],
        scope_name=row.get("scope_name"),
        granted_by=row.get("granted_by"),
        granted_at=row["granted_at"],
        created_at=row.get("created_at", row["granted_at"]),
    )


@instrument_class_methods(namespace="grc_roles.service", logger_name="backend.grc_roles")
class GrcRoleService:
    """Org-level GRC role assignment and access grant management."""

    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        """Initialize the GRC role service.

        Args:
            settings: Application settings.
            database_pool: Database connection pool.
            cache: Cache manager instance.
        """
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repo = GrcRoleRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")

    async def _invalidate_cache(self, org_id: str) -> None:
        """Clear cached GRC team data for an org.

        Args:
            org_id: Org whose cache to invalidate.
        """
        await self._cache.delete_pattern(f"{_CACHE_PREFIX}:{org_id}*")

    # ── Role assignments ───────────────────────────────────────────────────────

    async def list_assignments(
        self,
        *,
        actor_id: str,
        org_id: str,
        grc_role_code: str | None = None,
        user_id: str | None = None,
    ) -> GrcRoleAssignmentListResponse:
        """List GRC role assignments for an org.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org to query.
            grc_role_code: Optional filter by role code.
            user_id: Optional filter by user.

        Returns:
            List response with assignment items and total count.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "grc_role_management.view", scope_org_id=org_id)
            rows = await self._repo.list_assignments(
                conn, org_id=org_id, grc_role_code=grc_role_code, user_id=user_id,
            )
        items = [_assignment_response(r) for r in rows]
        return GrcRoleAssignmentListResponse(items=items, total=len(items))

    async def assign_role(
        self,
        *,
        actor_id: str,
        org_id: str,
        body: AssignGrcRoleRequest,
    ) -> GrcRoleAssignmentResponse:
        """Assign an org-level GRC role to a user.

        Idempotent: returns existing assignment if already active.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org to assign the role in.
            body: Assignment request with user_id and grc_role_code.

        Returns:
            The created or existing assignment response.

        Raises:
            ConflictError: If user already has this role (shouldn't happen with idempotent logic).
            NotFoundError: If user is not an org member.
        """
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "grc_role_management.assign", scope_org_id=org_id)

            # Verify user is an org member
            is_member = await conn.fetchval(
                """
                SELECT 1 FROM "03_auth_manage"."31_lnk_org_memberships"
                WHERE org_id = $1::UUID AND user_id = $2::UUID
                  AND is_active = TRUE AND is_deleted = FALSE
                LIMIT 1
                """,
                org_id, body.user_id,
            )
            if not is_member:
                raise NotFoundError(f"User {body.user_id} is not a member of org {org_id}.")

            # Check for existing active assignment (idempotent)
            existing = await self._repo.find_active_assignment(
                conn, org_id=org_id, user_id=body.user_id, grc_role_code=body.grc_role_code,
            )
            if existing:
                row = await self._repo.get_assignment_by_id(conn, existing["id"])
                return _assignment_response(row)

            assignment_id = str(uuid4())
            await self._repo.create_assignment(
                conn,
                assignment_id=assignment_id,
                org_id=org_id,
                user_id=body.user_id,
                grc_role_code=body.grc_role_code,
                assigned_by=actor_id,
                assigned_at=now,
            )

            # Audit
            await self._audit_writer.write(
                conn,
                AuditEntry(
                    entity_type="grc_role_assignment",
                    entity_id=assignment_id,
                    event_type="grc_role_assigned",
                    event_category="grc",
                    actor_id=actor_id,
                    properties={
                        "org_id": org_id,
                        "user_id": body.user_id,
                        "grc_role_code": body.grc_role_code,
                    },
                ),
            )

            row = await self._repo.get_assignment_by_id(conn, assignment_id)

        await self._invalidate_cache(org_id)
        return _assignment_response(row)

    async def revoke_role(
        self,
        *,
        actor_id: str,
        org_id: str,
        assignment_id: str,
    ) -> None:
        """Revoke a GRC role assignment and all its access grants.

        Also syncs backward by clearing grc_role_code on workspace memberships.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org context.
            assignment_id: UUID of the assignment to revoke.

        Raises:
            NotFoundError: If assignment not found or already revoked.
        """
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "grc_role_management.revoke", scope_org_id=org_id)

            assignment = await self._repo.get_assignment_by_id(conn, assignment_id)
            if not assignment or assignment["org_id"] != org_id:
                raise NotFoundError(f"GRC role assignment {assignment_id} not found.")

            # Get grants before revoking (for backward sync)
            grants = await self._repo.list_grants(conn, assignment_id=assignment_id)

            revoked = await self._repo.revoke_assignment(
                conn, assignment_id=assignment_id, revoked_by=actor_id, revoked_at=now,
            )
            if not revoked:
                raise NotFoundError(f"GRC role assignment {assignment_id} not found or already revoked.")

            # Backward sync: clear grc_role_code on workspace memberships
            for grant in grants:
                if grant["scope_type"] == "workspace":
                    await self._repo.sync_workspace_membership_grc_role(
                        conn,
                        user_id=assignment["user_id"],
                        workspace_id=grant["scope_id"],
                        grc_role_code=None,
                    )

            # Audit
            await self._audit_writer.write(
                conn,
                AuditEntry(
                    entity_type="grc_role_assignment",
                    entity_id=assignment_id,
                    event_type="grc_role_revoked",
                    event_category="grc",
                    actor_id=actor_id,
                    properties={
                        "org_id": org_id,
                        "user_id": assignment["user_id"],
                        "grc_role_code": assignment["grc_role_code"],
                    },
                ),
            )

        await self._invalidate_cache(org_id)

    # ── Access grants ──────────────────────────────────────────────────────────

    async def list_grants(
        self,
        *,
        actor_id: str,
        org_id: str,
        assignment_id: str,
    ) -> GrcAccessGrantListResponse:
        """List access grants for a role assignment.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org context.
            assignment_id: UUID of the role assignment.

        Returns:
            List response with grant items.

        Raises:
            NotFoundError: If assignment not found.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "grc_role_management.view", scope_org_id=org_id)

            assignment = await self._repo.get_assignment_by_id(conn, assignment_id)
            if not assignment or assignment["org_id"] != org_id:
                raise NotFoundError(f"GRC role assignment {assignment_id} not found.")

            rows = await self._repo.list_grants(conn, assignment_id=assignment_id)

        items = [_grant_response(r) for r in rows]
        return GrcAccessGrantListResponse(items=items, total=len(items))

    async def create_grant(
        self,
        *,
        actor_id: str,
        org_id: str,
        assignment_id: str,
        body: CreateAccessGrantRequest,
    ) -> GrcAccessGrantResponse:
        """Grant scope access to a role assignment.

        Idempotent: returns existing grant if already active.
        Also syncs backward by setting grc_role_code on workspace membership.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org context.
            assignment_id: UUID of the role assignment.
            body: Grant request with scope_type and scope_id.

        Returns:
            The created or existing grant response.

        Raises:
            NotFoundError: If assignment not found.
        """
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "grc_role_management.assign", scope_org_id=org_id)

            assignment = await self._repo.get_assignment_by_id(conn, assignment_id)
            if not assignment or assignment["org_id"] != org_id:
                raise NotFoundError(f"GRC role assignment {assignment_id} not found.")

            # Idempotent check
            existing = await self._repo.find_active_grant(
                conn,
                grc_role_assignment_id=assignment_id,
                scope_type=body.scope_type,
                scope_id=body.scope_id,
            )
            if existing:
                return _grant_response(existing)

            grant_id = str(uuid4())
            await self._repo.create_grant(
                conn,
                grant_id=grant_id,
                grc_role_assignment_id=assignment_id,
                scope_type=body.scope_type,
                scope_id=body.scope_id,
                granted_by=actor_id,
                granted_at=now,
            )

            # Backward sync: set grc_role_code on workspace membership
            if body.scope_type == "workspace":
                await self._repo.sync_workspace_membership_grc_role(
                    conn,
                    user_id=assignment["user_id"],
                    workspace_id=body.scope_id,
                    grc_role_code=assignment["grc_role_code"],
                )

            # Audit
            await self._audit_writer.write(
                conn,
                AuditEntry(
                    entity_type="grc_access_grant",
                    entity_id=grant_id,
                    event_type="grc_access_granted",
                    event_category="grc",
                    actor_id=actor_id,
                    properties={
                        "assignment_id": assignment_id,
                        "scope_type": body.scope_type,
                        "scope_id": body.scope_id,
                        "grc_role_code": assignment["grc_role_code"],
                    },
                ),
            )

            grants = await self._repo.list_grants(conn, assignment_id=assignment_id)
            grant_row = next((g for g in grants if g["id"] == grant_id), None)

        await self._invalidate_cache(org_id)
        if grant_row:
            return _grant_response(grant_row)
        return GrcAccessGrantResponse(
            id=grant_id,
            grc_role_assignment_id=assignment_id,
            scope_type=body.scope_type,
            scope_id=body.scope_id,
            granted_by=actor_id,
            granted_at=now,
            created_at=now,
        )

    async def revoke_grant(
        self,
        *,
        actor_id: str,
        org_id: str,
        assignment_id: str,
        grant_id: str,
    ) -> None:
        """Revoke an access grant.

        Also syncs backward by clearing grc_role_code on workspace membership
        if no other active assignment grants the same role for that workspace.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org context.
            assignment_id: UUID of the role assignment.
            grant_id: UUID of the grant to revoke.

        Raises:
            NotFoundError: If assignment or grant not found.
        """
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, "grc_role_management.revoke", scope_org_id=org_id)

            assignment = await self._repo.get_assignment_by_id(conn, assignment_id)
            if not assignment or assignment["org_id"] != org_id:
                raise NotFoundError(f"GRC role assignment {assignment_id} not found.")

            # Get grant details before revoking
            grants = await self._repo.list_grants(conn, assignment_id=assignment_id)
            grant_row = next((g for g in grants if g["id"] == grant_id), None)
            if not grant_row:
                raise NotFoundError(f"Access grant {grant_id} not found.")

            revoked = await self._repo.revoke_grant(
                conn, grant_id=grant_id, revoked_by=actor_id, revoked_at=now,
            )
            if not revoked:
                raise NotFoundError(f"Access grant {grant_id} not found or already revoked.")

            # Backward sync: clear workspace membership if this was a workspace grant
            if grant_row["scope_type"] == "workspace":
                await self._repo.sync_workspace_membership_grc_role(
                    conn,
                    user_id=assignment["user_id"],
                    workspace_id=grant_row["scope_id"],
                    grc_role_code=None,
                )

        await self._invalidate_cache(org_id)

    # ── Team view ──────────────────────────────────────────────────────────────

    async def get_team(
        self,
        *,
        actor_id: str,
        org_id: str,
        workspace_id: str | None = None,
        engagement_id: str | None = None,
    ) -> GrcTeamResponse:
        """Get the full GRC team for an org, grouped by role category.

        Args:
            actor_id: UUID of the requesting user.
            org_id: Org to query.
            workspace_id: Optional scope filter.
            engagement_id: Optional scope filter.

        Returns:
            Team response grouped into internal, auditors, vendors.
        """
        async with self._database_pool.acquire() as conn:
            # Allow access if user has explicit role management view permission OR general GRC view permission
            try:
                await require_permission(conn, actor_id, "grc_role_management.view", scope_org_id=org_id)
            except AuthorizationError:
                await require_permission(conn, actor_id, "controls.view", scope_org_id=org_id)

            members_rows = await self._repo.get_team(
                conn, org_id=org_id, workspace_id=workspace_id, engagement_id=engagement_id,
            )

            # Load grants for each member
            members = []
            for row in members_rows:
                grants_rows = await self._repo.list_grants(
                    conn, assignment_id=row["assignment_id"],
                )
                members.append(
                    GrcTeamMemberResponse(
                        assignment_id=row["assignment_id"],
                        org_id=row["org_id"],
                        user_id=row["user_id"],
                        grc_role_code=row["grc_role_code"],
                        role_name=row.get("role_name", ""),
                        email=row.get("email"),
                        display_name=row.get("display_name"),
                        assigned_at=row["assigned_at"],
                        grants=[_grant_response(g) for g in grants_rows],
                    )
                )

        internal = [m for m in members if _ROLE_CATEGORIES.get(m.grc_role_code) == "internal"]
        auditors = [m for m in members if _ROLE_CATEGORIES.get(m.grc_role_code) == "auditor"]
        vendors = [m for m in members if _ROLE_CATEGORIES.get(m.grc_role_code) == "vendor"]

        return GrcTeamResponse(
            internal=internal,
            auditors=auditors,
            vendors=vendors,
            total=len(members),
        )
