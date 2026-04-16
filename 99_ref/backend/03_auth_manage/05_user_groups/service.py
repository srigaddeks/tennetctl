from __future__ import annotations

from importlib import import_module
from uuid import uuid4

import asyncpg

from .repository import UserGroupRepository
from .schemas import (
    AddMemberRequest,
    AssignGroupRoleRequest,
    CreateGroupRequest,
    GroupChildListResponse,
    GroupListResponse,
    GroupMemberListResponse,
    GroupMemberResponse,
    GroupResponse,
    GroupRoleResponse,
    SetParentGroupRequest,
    UpdateGroupRequest,
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
AuthorizationError = _errors_module.AuthorizationError
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
require_permission = _perm_check_module.require_permission
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
utc_now_sql = _time_module.utc_now_sql

SCHEMA = '"03_auth_manage"'

_CACHE_TTL_GROUPS = 300  # 5 minutes


def _cache_key_groups(tenant_key: str, scope_org_id: str | None = None) -> str:
    return f"groups:list:{tenant_key}:{scope_org_id or '_'}"


@instrument_class_methods(namespace="user_groups.service", logger_name="backend.user_groups.instrumentation")
class UserGroupService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = UserGroupRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.user_groups")

    async def _require_view_permission(
        self,
        connection: asyncpg.Connection,
        *,
        actor_id: str,
        scope_org_id: str | None,
    ) -> None:
        if scope_org_id is not None:
            await require_permission(
                connection,
                actor_id,
                "org_management.view",
                scope_org_id=scope_org_id,
            )
            return
        await require_permission(connection, actor_id, "group_access_assignment.view")

    async def _require_assign_permission(
        self,
        connection: asyncpg.Connection,
        *,
        actor_id: str,
        scope_org_id: str | None,
    ) -> None:
        if scope_org_id is not None:
            await require_permission(
                connection,
                actor_id,
                "org_management.assign",
                scope_org_id=scope_org_id,
            )
            return
        await require_permission(connection, actor_id, "group_access_assignment.assign")

    async def _require_revoke_permission(
        self,
        connection: asyncpg.Connection,
        *,
        actor_id: str,
        scope_org_id: str | None,
    ) -> None:
        if scope_org_id is not None:
            await require_permission(
                connection,
                actor_id,
                "org_management.revoke",
                scope_org_id=scope_org_id,
            )
            return
        await require_permission(connection, actor_id, "group_access_assignment.revoke")

    async def get_group(self, group_id: str, *, actor_id: str) -> GroupResponse:
        async with self._database_pool.acquire() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_view_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            members = await self._repository.list_group_members(connection, group_id)
            roles = await self._repository.list_group_roles(connection, group_id)
            counts = await self._repository.count_group_members(connection, [group_id])
        return _group_to_response(group, members, roles, counts.get(group_id, 0))

    async def list_groups(self, *, actor_id: str, scope_org_id: str | None = None) -> GroupListResponse:
        tenant_key = self._settings.default_tenant_key
        async with self._database_pool.acquire() as connection:
            await self._require_view_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=scope_org_id,
            )

        cache_key = _cache_key_groups(tenant_key, scope_org_id)
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return GroupListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            groups = await self._repository.list_groups(
                connection,
                tenant_key=tenant_key,
                scope_org_id=scope_org_id,
            )
            group_ids = [g.id for g in groups]
            member_counts = await self._repository.count_group_members(connection, group_ids)
            group_roles = await self._repository.list_group_roles_batch(connection, group_ids)

        result = GroupListResponse(
            groups=[
                _group_to_response(g, [], group_roles[g.id], member_counts.get(g.id, 0))
                for g in groups
            ]
        )
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_GROUPS)
        return result

    async def _invalidate_groups_cache(self) -> None:
        await self._cache.delete_pattern("groups:list:*")

    async def _invalidate_access_cache_for_user(self, user_id: str) -> None:
        await self._cache.delete_pattern(f"access:{user_id}:*")

    async def _invalidate_all_access_cache(self) -> None:
        await self._cache.delete_pattern("access:*")

    async def list_group_members(
        self, group_id: str, *, actor_id: str, limit: int, offset: int
    ) -> GroupMemberListResponse:
        async with self._database_pool.acquire() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_view_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            members, total = await self._repository.list_group_members_paginated(
                connection, group_id, limit=limit, offset=offset
            )
        return GroupMemberListResponse(
            members=[
                GroupMemberResponse(
                    id=m.id, user_id=m.user_id, membership_status=m.membership_status,
                    effective_from=m.effective_from, effective_to=m.effective_to,
                    email=m.email, display_name=m.display_name,
                    scope_org_id=m.scope_org_id, scope_org_name=m.scope_org_name,
                    scope_workspace_id=m.scope_workspace_id, scope_workspace_name=m.scope_workspace_name,
                )
                for m in members
            ],
            total=total, limit=limit, offset=offset,
        )

    async def list_group_children(
        self, group_id: str, *, actor_id: str, limit: int, offset: int
    ) -> GroupChildListResponse:
        async with self._database_pool.acquire() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_view_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            children, total = await self._repository.list_group_children_paginated(
                connection, group_id, limit=limit, offset=offset
            )
            child_ids = [c.id for c in children]
            member_counts = await self._repository.count_group_members(connection, child_ids)
            child_roles = {
                c.id: await self._repository.list_group_roles(connection, c.id)
                for c in children
            }
        return GroupChildListResponse(
            children=[
                _group_to_response(c, [], child_roles[c.id], member_counts.get(c.id, 0))
                for c in children
            ],
            total=total, limit=limit, offset=offset,
        )

    async def create_group(
        self,
        payload: CreateGroupRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> GroupResponse:
        now = utc_now_sql()
        tenant_key = payload.tenant_key or self._settings.default_tenant_key
        async with self._database_pool.transaction() as connection:
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=payload.scope_org_id,
            )
            # Validate parent group exists (if given)
            if payload.parent_group_id:
                parent = await self._repository.get_group_by_id(connection, payload.parent_group_id)
                if parent is None:
                    raise NotFoundError(f"Parent group '{payload.parent_group_id}' not found.")
                if payload.scope_org_id is not None and parent.scope_org_id != payload.scope_org_id:
                    raise ConflictError("Parent group must belong to the same organization.")
                if parent.role_level_code != payload.role_level_code:
                    raise ConflictError("Parent group must have the same role level.")
            try:
                group = await self._repository.create_group(
                    connection, code=payload.code, name=payload.name,
                    description=payload.description, role_level_code=payload.role_level_code,
                    tenant_key=tenant_key, parent_group_id=payload.parent_group_id,
                    scope_org_id=payload.scope_org_id, created_by=actor_id, now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError(f"Group '{payload.code}' already exists for this tenant.")

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=tenant_key, entity_type="user_group",
                    entity_id=group.id, event_type="group_created", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": group.code,
                        "new_value": str({"code": group.code, "name": group.name, "parent_group_id": payload.parent_group_id}),
                    },
                ),
            )
        await self._invalidate_groups_cache()
        return _group_to_response(group, [], [], 0)

    async def update_group(
        self,
        group_id: str,
        payload: UpdateGroupRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> GroupResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            existing = await self._repository.get_group_by_id(connection, group_id)
            if existing is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=existing.scope_org_id,
            )
            if existing.is_system:
                raise AuthorizationError("System groups cannot be modified.")
            if existing.is_locked and payload.is_disabled:
                raise AuthorizationError("This group is mapped to a framework control and cannot be disabled. Remove it from all control assignments first.")
            # Validate parent (prevent cycles: can't set parent to self or own descendant)
            parent_arg = ...  # sentinel = don't change
            if payload.parent_group_id is not None:
                if payload.parent_group_id == group_id:
                    raise ConflictError("A group cannot be its own parent.")
                parent = await self._repository.get_group_by_id(connection, payload.parent_group_id)
                if parent is None:
                    raise NotFoundError(f"Parent group '{payload.parent_group_id}' not found.")
                if existing.scope_org_id is not None and parent.scope_org_id != existing.scope_org_id:
                    raise ConflictError("Parent group must belong to the same organization.")
                if parent.role_level_code != existing.role_level_code:
                    raise ConflictError("Parent group must have the same role level.")
                parent_arg = payload.parent_group_id
            elif "parent_group_id" in payload.model_fields_set:
                parent_arg = None  # explicitly clearing parent

            group = await self._repository.update_group(
                connection, group_id=group_id, name=payload.name,
                description=payload.description, parent_group_id=parent_arg,
                is_disabled=payload.is_disabled,
                updated_by=actor_id, now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=existing.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_updated", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": existing.code,
                        "previous_value": str({"name": existing.name, "parent_group_id": existing.parent_group_id}),
                        "new_value": str({"name": group.name if group else None}),
                    },
                ),
            )
        assert group is not None
        await self._invalidate_groups_cache()
        async with self._database_pool.acquire() as connection:
            members = await self._repository.list_group_members(connection, group_id)
            roles = await self._repository.list_group_roles(connection, group_id)
        return _group_to_response(group, members, roles, len(members))

    async def set_parent(
        self,
        group_id: str,
        payload: SetParentGroupRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> GroupResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            existing = await self._repository.get_group_by_id(connection, group_id)
            if existing is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=existing.scope_org_id,
            )
            if existing.is_system:
                raise AuthorizationError("System groups cannot be modified.")
            if payload.parent_group_id == group_id:
                raise ConflictError("A group cannot be its own parent.")
            if payload.parent_group_id is not None:
                parent = await self._repository.get_group_by_id(connection, payload.parent_group_id)
                if parent is None:
                    raise NotFoundError(f"Parent group '{payload.parent_group_id}' not found.")
                if existing.scope_org_id is not None and parent.scope_org_id != existing.scope_org_id:
                    raise ConflictError("Parent group must belong to the same organization.")
                if parent.role_level_code != existing.role_level_code:
                    raise ConflictError("Parent group must have the same role level.")
            group = await self._repository.update_group(
                connection, group_id=group_id, name=None, description=None,
                parent_group_id=payload.parent_group_id,
                updated_by=actor_id, now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=existing.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_parent_changed", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": existing.code,
                        "previous_value": str({"parent_group_id": existing.parent_group_id}),
                        "new_value": str({"parent_group_id": payload.parent_group_id}),
                    },
                ),
            )
        assert group is not None
        await self._invalidate_groups_cache()
        async with self._database_pool.acquire() as connection:
            members = await self._repository.list_group_members(connection, group_id)
            roles = await self._repository.list_group_roles(connection, group_id)
        return _group_to_response(group, members, roles, len(members))

    async def add_member(
        self,
        group_id: str,
        payload: AddMemberRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> GroupResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            try:
                await self._repository.add_member(
                    connection, group_id=group_id, user_id=payload.user_id,
                    created_by=actor_id, now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError("User is already a member of this group.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=group.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_member_added", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": group.code,
                        "new_value": str({"user_id": payload.user_id}),
                    },
                ),
            )
        await self._invalidate_groups_cache()
        await self._invalidate_access_cache_for_user(payload.user_id)
        async with self._database_pool.acquire() as connection:
            members = await self._repository.list_group_members(connection, group_id)
            roles = await self._repository.list_group_roles(connection, group_id)
        return _group_to_response(group, members, roles, len(members))

    async def remove_member(
        self,
        group_id: str,
        user_id: str,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_revoke_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            removed = await self._repository.remove_member(
                connection, group_id=group_id, user_id=user_id,
                deleted_by=actor_id, now=now,
            )
            if not removed:
                raise NotFoundError("Membership not found.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=group.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_member_removed", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": group.code,
                        "previous_value": str({"user_id": user_id}),
                    },
                ),
            )
        await self._invalidate_groups_cache()
        await self._invalidate_access_cache_for_user(user_id)

    async def delete_group(
        self,
        group_id: str,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> None:
        from fastapi import HTTPException
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            existing = await self._repository.get_group_by_id(connection, group_id)
            if existing is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=existing.scope_org_id,
            )
            if existing.is_system:
                raise AuthorizationError("System groups cannot be deleted.")
            if existing.is_locked:
                raise AuthorizationError("This group is mapped to a framework control and cannot be deleted. Remove it from all control assignments first.")
            deleted = await self._repository.delete_group(
                connection, group_id=group_id, deleted_by=actor_id, now=now,
            )
            if not deleted:
                raise NotFoundError(f"Group '{group_id}' not found or already deleted.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=existing.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_deleted", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={"event_key": existing.code},
                ),
            )
        await self._invalidate_groups_cache()
        await self._invalidate_all_access_cache()

    async def assign_role(
        self,
        group_id: str,
        payload: AssignGroupRoleRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> GroupResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            try:
                await self._repository.assign_role(
                    connection, group_id=group_id, role_id=payload.role_id,
                    created_by=actor_id, now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError("Role is already assigned to this group.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=group.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_role_assigned", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": group.code,
                        "new_value": str({"role_id": payload.role_id}),
                    },
                ),
            )
        await self._invalidate_groups_cache()
        await self._invalidate_all_access_cache()
        async with self._database_pool.acquire() as connection:
            members = await self._repository.list_group_members(connection, group_id)
            roles = await self._repository.list_group_roles(connection, group_id)
        return _group_to_response(group, members, roles, len(members))

    async def revoke_role(
        self,
        group_id: str,
        role_id: str,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            group = await self._repository.get_group_by_id(connection, group_id)
            if group is None:
                raise NotFoundError(f"Group '{group_id}' not found.")
            await self._require_revoke_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=group.scope_org_id,
            )
            revoked = await self._repository.revoke_role(
                connection, group_id=group_id, role_id=role_id,
                deleted_by=actor_id, now=now,
            )
            if not revoked:
                raise NotFoundError("Role assignment not found.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=group.tenant_key, entity_type="user_group",
                    entity_id=group_id, event_type="group_role_revoked", event_category="access",
                    occurred_at=now, actor_id=actor_id, ip_address=client_ip,
                    session_id=session_id, properties={
                        "event_key": group.code,
                        "previous_value": str({"role_id": role_id}),
                    },
                ),
            )
        await self._invalidate_groups_cache()
        await self._invalidate_all_access_cache()


def _group_to_response(group, members, roles, member_count: int = 0) -> GroupResponse:
    return GroupResponse(
        id=group.id, code=group.code, name=group.name, description=group.description,
        role_level_code=group.role_level_code, tenant_key=group.tenant_key,
        parent_group_id=group.parent_group_id,
        scope_org_id=group.scope_org_id,
        scope_workspace_id=group.scope_workspace_id,
        is_active=group.is_active, is_system=group.is_system, is_locked=group.is_locked,
        member_count=member_count,
        members=[
            GroupMemberResponse(
                id=m.id, user_id=m.user_id, membership_status=m.membership_status,
                effective_from=m.effective_from, effective_to=m.effective_to,
                email=m.email, display_name=m.display_name,
                scope_org_id=getattr(m, 'scope_org_id', None), scope_org_name=getattr(m, 'scope_org_name', None),
                scope_workspace_id=getattr(m, 'scope_workspace_id', None), scope_workspace_name=getattr(m, 'scope_workspace_name', None),
            )
            for m in members
        ],
        roles=[
            GroupRoleResponse(
                id=r.id, role_id=r.role_id, role_code=r.role_code,
                role_name=r.role_name, role_level_code=r.role_level_code,
                assignment_status=r.assignment_status,
            )
            for r in roles
        ],
        created_at=group.created_at, updated_at=group.updated_at,
    )
