from __future__ import annotations

import json
import uuid
from importlib import import_module

from .repository import WorkspaceRepository
from .schemas import (
    CreateWorkspaceRequest,
    UpdateWorkspaceRequest,
    UpdateWorkspaceMemberRequest,
    WorkspaceListResponse,
    WorkspaceMemberResponse,
    WorkspaceResponse,
    WorkspaceTypeResponse,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.03_auth_manage.constants")
_scoped_groups = import_module("backend.03_auth_manage._scoped_group_provisioning")
_grc_access = import_module("backend.03_auth_manage.18_grc_roles.access_check")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AuditEventType = _constants_module.AuditEventType
AuditEventCategory = _constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_WS_TYPES = "ws_types:list"
_CACHE_TTL_WS_TYPES = 3600  # 1 hour (static dimension data)
_CACHE_TTL_WORKSPACES = 300  # 5 minutes
_CACHE_TTL_WS_MEMBERS = 300  # 5 minutes


@instrument_class_methods(namespace="workspaces.service", logger_name="backend.workspaces.instrumentation")
class WorkspaceService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = WorkspaceRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.workspaces")

    async def list_workspace_types(self) -> list[WorkspaceTypeResponse]:
        cached = await self._cache.get(_CACHE_KEY_WS_TYPES)
        if cached is not None:
            items = json.loads(cached)
            return [WorkspaceTypeResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            types = await self._repository.list_workspace_types(conn)
        result = [
            WorkspaceTypeResponse(
                code=t.code,
                name=t.name,
                description=t.description,
                is_infrastructure_type=t.is_infrastructure_type,
            )
            for t in types
        ]
        await self._cache.set(_CACHE_KEY_WS_TYPES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_WS_TYPES)
        return result

    async def list_workspaces(
        self, *, user_id: str, org_id: str
    ) -> WorkspaceListResponse:
        # Check if user can manage workspaces at org scope (org admin) or just view their own.
        # Org admins (workspace_management.update at org scope) see all workspaces.
        # All other org members see only workspaces they're a member of.
        # GRC-role users with access grants always use membership-based listing.
        AuthorizationError = _errors_module.AuthorizationError
        async with self._database_pool.acquire() as conn:
            try:
                await require_permission(
                    conn, user_id, "workspace_management.update", scope_org_id=org_id
                )
                is_org_admin = True
            except AuthorizationError:
                # Still require they have at least view access at org scope
                try:
                    await require_permission(
                        conn, user_id, "workspace_management.view", scope_org_id=org_id
                    )
                    is_org_admin = False
                except AuthorizationError:
                    # No org-level access at all — return only workspaces they're directly a member of
                    is_org_admin = False

            # GRC-role users with access grants must use membership-based listing
            # even if they have workspace_management permissions via org_member role.
            if is_org_admin:
                has_grc_grants = await _grc_access.has_any_grants(conn, user_id=user_id, org_id=org_id)
                if has_grc_grants:
                    is_org_admin = False

        if is_org_admin:
            cache_key = f"workspaces:{org_id}"
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return WorkspaceListResponse.model_validate_json(cached)
            async with self._database_pool.acquire() as conn:
                workspaces = await self._repository.list_workspaces(conn, org_id=org_id)
            items = [_ws_response(w) for w in workspaces]
            result = WorkspaceListResponse(items=items, total=len(items))
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_WORKSPACES)
        else:
            cache_key = f"workspaces:user:{user_id}:{org_id}"
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return WorkspaceListResponse.model_validate_json(cached)
            async with self._database_pool.acquire() as conn:
                workspaces = await self._repository.list_workspaces_for_user(
                    conn, user_id=user_id, org_id=org_id
                )
            items = [_ws_response(w) for w in workspaces]
            result = WorkspaceListResponse(items=items, total=len(items))
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_WORKSPACES)
        return result

    async def create_workspace(
        self, *, user_id: str, org_id: str, request: CreateWorkspaceRequest
    ) -> WorkspaceResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(
                conn, user_id, "workspace_management.create", scope_org_id=org_id
            )
            workspace_type_exists = await self._repository.workspace_type_exists(
                conn, request.workspace_type_code
            )
            if not workspace_type_exists:
                raise ValidationError(
                    f"Invalid workspace_type_code '{request.workspace_type_code}'"
                )
            # Ensure name is unique within org — append random suffix if taken
            unique_name = await _unique_ws_name(self._repository, conn, request.name, org_id)
            request = request.model_copy(update={"name": unique_name})
            existing = await self._repository.get_workspace_by_slug(conn, request.slug, org_id)
            if existing:
                raise ConflictError(f"Workspace slug '{request.slug}' already exists in this org")
            workspace = await self._repository.create_workspace(
                conn,
                workspace_id=str(uuid.uuid4()),
                org_id=org_id,
                workspace_type_code=request.workspace_type_code,
                product_id=request.product_id,
                name=request.name,
                slug=request.slug,
                description=request.description,
                created_by=user_id,
                now=now,
            )
            # Provision workspace-level system groups (ws_admins, ws_contributors, ws_viewers).
            # For GRC workspaces, also provisions the 7 GRC role-specific groups.
            await _scoped_groups.provision_workspace_system_groups(
                conn, workspace_id=workspace.id, org_id=org_id,
                tenant_key=self._settings.default_tenant_key, created_by=user_id, now=now,
                workspace_type_code=request.workspace_type_code,
            )
            # Write creator to workspace_memberships table (owner) — required for list_workspaces_for_user
            await self._repository.add_workspace_member(
                conn,
                membership_id=str(uuid.uuid4()),
                workspace_id=workspace.id,
                user_id=user_id,
                role="owner",
                created_by=user_id,
                now=now,
            )
            # Add creator to workspace_admin scoped group
            await _scoped_groups.assign_workspace_member_to_scoped_group(
                conn, workspace_id=workspace.id, user_id=user_id,
                membership_type="owner", now=now, created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="workspace",
                    entity_id=workspace.id,
                    event_type=AuditEventType.WORKSPACE_CREATED.value,
                    event_category=AuditEventCategory.WORKSPACE.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "org_id": org_id,
                        "name": request.name,
                        "slug": request.slug,
                        "workspace_type_code": request.workspace_type_code,
                    },
                ),
            )
        await self._cache.delete(f"workspaces:{org_id}")
        await self._cache.delete(f"workspaces:user:{user_id}:{org_id}")
        return _ws_response(workspace)

    async def update_workspace(
        self, *, user_id: str, org_id: str, workspace_id: str, request: UpdateWorkspaceRequest
    ) -> WorkspaceResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(
                conn,
                user_id,
                "workspace_management.update",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            workspace = await self._repository.update_workspace(
                conn,
                workspace_id,
                name=request.name,
                description=request.description,
                product_id=request.product_id,
                is_disabled=request.is_disabled,
                updated_by=user_id,
                now=now,
            )
            if workspace is None:
                raise NotFoundError(f"Workspace '{workspace_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="workspace",
                    entity_id=workspace_id,
                    event_type=AuditEventType.WORKSPACE_UPDATED.value,
                    event_category=AuditEventCategory.WORKSPACE.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "org_id": org_id,
                        "name": request.name,
                        "description": request.description,
                        "is_disabled": str(request.is_disabled) if request.is_disabled is not None else None,
                    },
                ),
            )
        await self._cache.delete(f"workspaces:{org_id}")
        return _ws_response(workspace)

    async def list_members(
        self, *, user_id: str, org_id: str, workspace_id: str
    ) -> list[WorkspaceMemberResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "workspace_management.view",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )

        cache_key = f"ws_members:{workspace_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            items = json.loads(cached)
            return [WorkspaceMemberResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            members = await self._repository.list_workspace_members(conn, workspace_id)
        result = [_member_response(m) for m in members]
        await self._cache.set(cache_key, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_WS_MEMBERS)
        return result

    async def add_member(
        self, *, user_id: str, org_id: str, workspace_id: str, target_user_id: str, role: str
    ) -> WorkspaceMemberResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(
                conn,
                user_id,
                "workspace_management.assign",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            ws = await self._repository.get_workspace_by_id(conn, workspace_id)
            if ws is None:
                raise NotFoundError(f"Workspace '{workspace_id}' not found")
            member = await self._repository.add_workspace_member(
                conn,
                membership_id=str(uuid.uuid4()),
                workspace_id=workspace_id,
                user_id=target_user_id,
                role=role,
                created_by=user_id,
                now=now,
            )
            # Auto-assign to workspace-scoped system group based on membership_type
            await _scoped_groups.assign_workspace_member_to_scoped_group(
                conn, workspace_id=workspace_id, user_id=target_user_id,
                membership_type=role, now=now, created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="workspace",
                    entity_id=workspace_id,
                    event_type=AuditEventType.WORKSPACE_MEMBER_ADDED.value,
                    event_category=AuditEventCategory.WORKSPACE.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "org_id": org_id,
                        "target_user_id": target_user_id,
                        "role": role,
                    },
                ),
            )
        await self._cache.delete(f"ws_members:{workspace_id}")
        await self._cache.delete(f"workspaces:user:{target_user_id}:{org_id}")
        await self._cache.delete_pattern(f"access:{target_user_id}:*")
        return _member_response(member)

    async def remove_member(
        self, *, user_id: str, org_id: str, workspace_id: str, target_user_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(
                conn,
                user_id,
                "workspace_management.revoke",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            removed = await self._repository.remove_workspace_member(
                conn,
                workspace_id=workspace_id,
                user_id=target_user_id,
                deleted_by=user_id,
                now=now,
            )
            if not removed:
                raise NotFoundError(
                    f"Member '{target_user_id}' not found in workspace '{workspace_id}'"
                )
            # Remove from workspace-scoped system groups
            await _scoped_groups.remove_workspace_member_from_scoped_groups(
                conn, workspace_id=workspace_id, user_id=target_user_id, now=now, deleted_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="workspace",
                    entity_id=workspace_id,
                    event_type=AuditEventType.WORKSPACE_MEMBER_REMOVED.value,
                    event_category=AuditEventCategory.WORKSPACE.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "org_id": org_id,
                        "target_user_id": target_user_id,
                    },
                ),
            )
        await self._cache.delete(f"ws_members:{workspace_id}")
        await self._cache.delete(f"workspaces:user:{target_user_id}:{org_id}")
        await self._cache.delete_pattern(f"access:{target_user_id}:*")

    async def update_workspace_member(
        self,
        *,
        user_id: str,
        org_id: str,
        workspace_id: str,
        target_user_id: str,
        request: UpdateWorkspaceMemberRequest,
    ) -> WorkspaceMemberResponse:
        """Assign or remove a GRC workspace role for a member.

        Only valid for GRC workspaces (workspace_type_code='grc'). Assigning a new
        GRC role replaces any previous one — a member holds at most one GRC role.
        Setting grc_role_code=None removes all GRC role assignments.

        Args:
            user_id: UUID of the authenticated actor making the change.
            org_id: UUID of the owning org.
            workspace_id: UUID of the GRC workspace.
            target_user_id: UUID of the member whose GRC role is being updated.
            request: UpdateWorkspaceMemberRequest with the desired grc_role_code.

        Returns:
            Updated WorkspaceMemberResponse.

        Raises:
            NotFoundError: If the workspace or membership does not exist.
            ConflictError: If the workspace is not a GRC workspace.
            ValueError: If grc_role_code is not a recognised GRC role.
        """
        _validation_module = import_module("backend.01_core.errors")
        ValidationError = _validation_module.ValidationError if hasattr(_validation_module, "ValidationError") else ConflictError
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(
                conn,
                user_id,
                "workspace_management.assign",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            ws = await self._repository.get_workspace_by_id(conn, workspace_id)
            if ws is None:
                raise NotFoundError(f"Workspace '{workspace_id}' not found")
            member = await self._repository.get_workspace_member(conn, workspace_id, target_user_id)
            if member is None:
                raise NotFoundError(
                    f"User '{target_user_id}' is not a member of workspace '{workspace_id}'"
                )

            if request.grc_role_code is not None:
                await _scoped_groups.assign_workspace_member_grc_role(
                    conn,
                    workspace_id=workspace_id,
                    user_id=target_user_id,
                    grc_role_code=request.grc_role_code,
                    now=now,
                    created_by=user_id,
                )
            else:
                await _scoped_groups.remove_workspace_member_from_grc_groups(
                    conn,
                    workspace_id=workspace_id,
                    user_id=target_user_id,
                    now=now,
                    deleted_by=user_id,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="workspace",
                    entity_id=workspace_id,
                    event_type=AuditEventType.WORKSPACE_MEMBER_UPDATED.value,
                    event_category=AuditEventCategory.WORKSPACE.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "org_id": org_id,
                        "target_user_id": target_user_id,
                        "grc_role_code": request.grc_role_code,
                    },
                ),
            )
        await self._cache.delete(f"ws_members:{workspace_id}")
        await self._cache.delete_pattern(f"access:{target_user_id}:*")

        resp = _member_response(member)
        return resp.model_copy(update={"grc_role_code": request.grc_role_code})


async def _unique_ws_name(repo, conn, name: str, org_id: str) -> str:
    """Return `name` if unique within org, otherwise append a random 4-char suffix."""
    import random, string
    candidate = name
    for _ in range(10):
        existing = await repo.get_workspace_by_name(conn, candidate, org_id)
        if existing is None:
            return candidate
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        candidate = f"{name} {suffix}"
    return candidate


def _ws_response(w) -> WorkspaceResponse:
    return WorkspaceResponse(
        id=w.id,
        org_id=w.org_id,
        workspace_type_code=w.workspace_type_code,
        product_id=w.product_id,
        name=w.name,
        slug=w.slug,
        description=w.description,
        is_active=w.is_active,
        created_at=w.created_at,
        updated_at=w.updated_at,
    )


def _member_response(m) -> WorkspaceMemberResponse:
    return WorkspaceMemberResponse(
        id=m.id,
        workspace_id=m.workspace_id,
        user_id=m.user_id,
        role=m.role,
        is_active=m.is_active,
        joined_at=m.joined_at,
        email=m.email,
        display_name=m.display_name,
        grc_role_code=getattr(m, "grc_role_code", None),
    )
