from __future__ import annotations

from importlib import import_module
from uuid import uuid4

import asyncpg

from .repository import RoleRepository
from .schemas import (
    AssignPermissionRequest,
    CreateRoleRequest,
    RoleGroupListResponse,
    RoleGroupResponse,
    RoleLevelResponse,
    RoleListResponse,
    RolePermissionResponse,
    RoleResponse,
    UpdateRoleRequest,
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

_CACHE_TTL_ROLES = 600  # 10 minutes


def _cache_key_roles(tenant_key: str, scope_org_id: str | None = None) -> str:
    return f"roles:list:{tenant_key}:{scope_org_id or '_'}"


@instrument_class_methods(namespace="roles.service", logger_name="backend.roles.instrumentation")
class RoleService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = RoleRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.roles")

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
        await require_permission(connection, actor_id, "access_governance_console.view")

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

    async def list_roles(self, *, actor_id: str, scope_org_id: str | None = None) -> RoleListResponse:
        tenant_key = self._settings.default_tenant_key
        async with self._database_pool.acquire() as connection:
            await self._require_view_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=scope_org_id,
            )

        cache_key = _cache_key_roles(tenant_key, scope_org_id)
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return RoleListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            levels = await self._repository.list_role_levels(connection)
            roles = await self._repository.list_roles(
                connection,
                tenant_key=tenant_key,
                scope_org_id=scope_org_id,
            )
            all_perms = await self._repository.list_role_permissions_batch(
                connection, [role.id for role in roles]
            )

        result = RoleListResponse(
            levels=[
                RoleLevelResponse(id=l.id, code=l.code, name=l.name,
                                  description=l.description, sort_order=l.sort_order)
                for l in levels
            ],
            roles=[
                _role_to_response(r, all_perms.get(r.id, []))
                for r in roles
            ],
        )
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_ROLES)
        return result

    async def _invalidate_roles_cache(self) -> None:
        await self._cache.delete_pattern("roles:list:*")
        # Role permission changes affect all users' resolved access contexts
        await self._cache.delete_pattern("access:*")

    async def create_role(
        self,
        payload: CreateRoleRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> RoleResponse:
        now = utc_now_sql()
        tenant_key = payload.tenant_key or self._settings.default_tenant_key
        async with self._database_pool.transaction() as connection:
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=payload.scope_org_id,
            )
            try:
                role = await self._repository.create_role(
                    connection,
                    code=payload.code, name=payload.name, description=payload.description,
                    role_level_code=payload.role_level_code, tenant_key=tenant_key,
                    scope_org_id=payload.scope_org_id,
                    scope_workspace_id=payload.scope_workspace_id,
                    created_by=actor_id, now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError(f"Role '{payload.code}' already exists for this tenant.")

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=tenant_key, entity_type="role",
                    entity_id=role.id, event_type="role_created",
                    event_category="access", occurred_at=now,
                    actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={
                        "event_key": str(role.code),
                        "new_value": str({"code": role.code, "name": role.name}),
                    },
                ),
            )
        await self._invalidate_roles_cache()
        return _role_to_response(role, [])

    async def update_role(
        self,
        role_id: str,
        payload: UpdateRoleRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> RoleResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            existing = await self._repository.get_role_by_id(connection, role_id)
            if existing is None:
                raise NotFoundError(f"Role '{role_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=existing.scope_org_id,
            )
            if existing.is_system:
                raise AuthorizationError("System roles cannot be modified.")

            role = await self._repository.update_role(
                connection, role_id=role_id, name=payload.name,
                description=payload.description, is_disabled=payload.is_disabled,
                updated_by=actor_id, now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=existing.tenant_key, entity_type="role",
                    entity_id=role_id, event_type="role_updated",
                    event_category="access", occurred_at=now,
                    actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={
                        "event_key": str(existing.code),
                        "previous_value": str({"name": existing.name}),
                        "new_value": str({"name": role.name if role else None}),
                    },
                ),
            )

        assert role is not None
        await self._invalidate_roles_cache()
        async with self._database_pool.acquire() as connection:
            perms = await self._repository.list_role_permissions(connection, role_id)
        return _role_to_response(role, perms)

    async def list_groups_using_role(
        self,
        role_id: str,
        *,
        actor_id: str,
        scope_org_id: str | None = None,
    ) -> RoleGroupListResponse:
        async with self._database_pool.acquire() as connection:
            role = await self._repository.get_role_by_id(connection, role_id)
            if role is None:
                raise NotFoundError(f"Role '{role_id}' not found.")
            if scope_org_id is not None and role.scope_org_id is not None and role.scope_org_id != scope_org_id:
                raise NotFoundError(f"Role '{role_id}' not found.")
            effective_scope_org_id = role.scope_org_id or scope_org_id
            await self._require_view_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=effective_scope_org_id,
            )
            groups = await self._repository.list_groups_using_role(
                connection,
                role_id,
                scope_org_id=effective_scope_org_id,
            )
        return RoleGroupListResponse(
            groups=[
                RoleGroupResponse(
                    id=str(g["id"]),
                    code=g["code"],
                    name=g["name"],
                    role_level_code=g["role_level_code"],
                    is_system=g["is_system"],
                    is_active=g["is_active"],
                    member_count=g["member_count"],
                )
                for g in groups
            ]
        )

    async def delete_role(
        self,
        role_id: str,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            existing = await self._repository.get_role_by_id(connection, role_id)
            if existing is None:
                raise NotFoundError(f"Role '{role_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=existing.scope_org_id,
            )
            if existing.is_system:
                raise AuthorizationError("System roles cannot be deleted.")
            deleted = await self._repository.delete_role(
                connection, role_id=role_id, deleted_by=actor_id, now=now,
            )
            if not deleted:
                raise NotFoundError(f"Role '{role_id}' not found or already deleted.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=existing.tenant_key, entity_type="role",
                    entity_id=role_id, event_type="role_deleted",
                    event_category="access", occurred_at=now,
                    actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={"event_key": str(existing.code)},
                ),
            )
        await self._invalidate_roles_cache()

    async def assign_permission(
        self,
        role_id: str,
        payload: AssignPermissionRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> RoleResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            role = await self._repository.get_role_by_id(connection, role_id)
            if role is None:
                raise NotFoundError(f"Role '{role_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=role.scope_org_id,
            )
            try:
                await self._repository.assign_permission(
                    connection, role_id=role_id,
                    feature_permission_id=payload.feature_permission_id,
                    created_by=actor_id, now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError("Permission is already assigned to this role.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=role.tenant_key, entity_type="role",
                    entity_id=role_id, event_type="role_permission_assigned",
                    event_category="access", occurred_at=now,
                    actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={
                        "event_key": str(role.code),
                        "new_value": str({"feature_permission_id": payload.feature_permission_id}),
                    },
                ),
            )
        await self._invalidate_roles_cache()
        async with self._database_pool.acquire() as connection:
            role = await self._repository.get_role_by_id(connection, role_id)
            perms = await self._repository.list_role_permissions(connection, role_id)
        return _role_to_response(role, perms)  # type: ignore[arg-type]

    async def revoke_permission(
        self,
        role_id: str,
        feature_permission_id: str,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            role = await self._repository.get_role_by_id(connection, role_id)
            if role is None:
                raise NotFoundError(f"Role '{role_id}' not found.")
            await self._require_assign_permission(
                connection,
                actor_id=actor_id,
                scope_org_id=role.scope_org_id,
            )
            if role.code == "platform_super_admin":
                raise AuthorizationError("platform_super_admin permissions cannot be revoked.")
            revoked = await self._repository.revoke_permission(
                connection, role_id=role_id,
                feature_permission_id=feature_permission_id,
                deleted_by=actor_id, now=now,
            )
            if not revoked:
                raise NotFoundError("Permission assignment not found.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()), tenant_key=role.tenant_key, entity_type="role",
                    entity_id=role_id, event_type="role_permission_revoked",
                    event_category="access", occurred_at=now,
                    actor_id=actor_id, ip_address=client_ip, session_id=session_id,
                    properties={
                        "event_key": str(role.code),
                        "previous_value": str({"feature_permission_id": feature_permission_id}),
                    },
                ),
            )
        await self._invalidate_roles_cache()


def _role_to_response(role, perms) -> RoleResponse:
    return RoleResponse(
        id=role.id, code=role.code, name=role.name, description=role.description,
        role_level_code=role.role_level_code, tenant_key=role.tenant_key,
        scope_org_id=role.scope_org_id, scope_workspace_id=role.scope_workspace_id,
        is_active=role.is_active, is_disabled=role.is_disabled, is_system=role.is_system,
        permissions=[
            RolePermissionResponse(
                id=p.id, feature_permission_id=p.feature_permission_id,
                feature_permission_code=p.feature_permission_code,
                feature_flag_code=p.feature_flag_code,
                permission_action_code=p.permission_action_code,
                permission_name=p.permission_name,
            )
            for p in perms
        ],
        created_at=role.created_at, updated_at=role.updated_at,
    )
