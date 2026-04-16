from __future__ import annotations

import uuid
from importlib import import_module

from .repository import OrgRepository
from .schemas import (
    CreateOrgRequest,
    OrgListResponse,
    OrgMemberResponse,
    OrgResponse,
    OrgTypeResponse,
    UpdateOrgRequest,
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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AuditEventType = _constants_module.AuditEventType
AuditEventCategory = _constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_ORG_TYPES = "org_types:list"
_CACHE_TTL_ORG_TYPES = 3600  # 1 hour (static dimension data)
_CACHE_TTL_ORGS = 300  # 5 minutes
_CACHE_TTL_ORG_MEMBERS = 300  # 5 minutes


@instrument_class_methods(namespace="orgs.service", logger_name="backend.orgs.instrumentation")
class OrgService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = OrgRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.orgs")

    async def list_org_types(self) -> list[OrgTypeResponse]:
        cached = await self._cache.get(_CACHE_KEY_ORG_TYPES)
        if cached is not None:
            import json
            items = json.loads(cached)
            return [OrgTypeResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            types = await self._repository.list_org_types(conn)
        result = [OrgTypeResponse(code=t.code, name=t.name, description=t.description) for t in types]
        import json
        await self._cache.set(_CACHE_KEY_ORG_TYPES, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_ORG_TYPES)
        return result

    async def list_orgs(self, *, user_id: str, tenant_key: str) -> OrgListResponse:
        # Super admins (platform-level org_management.view) see all orgs.
        # All other users see only the orgs they are a member of.
        AuthorizationError = _errors_module.AuthorizationError
        async with self._database_pool.acquire() as conn:
            try:
                await require_permission(conn, user_id, "org_management.view")
                is_super_admin = True
            except AuthorizationError:
                is_super_admin = False

        if is_super_admin:
            cache_key = f"orgs:list:{tenant_key}"
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return OrgListResponse.model_validate_json(cached)
            async with self._database_pool.acquire() as conn:
                orgs = await self._repository.list_orgs(conn, tenant_key=tenant_key)
            items = [_org_response(o) for o in orgs]
            result = OrgListResponse(items=items, total=len(items))
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_ORGS)
        else:
            # Per-user cache — not shared, intentionally short-lived
            cache_key = f"orgs:user:{user_id}"
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return OrgListResponse.model_validate_json(cached)
            async with self._database_pool.acquire() as conn:
                orgs = await self._repository.list_orgs_for_user(
                    conn, user_id=user_id, tenant_key=tenant_key
                )
            items = [_org_response(o) for o in orgs]
            result = OrgListResponse(items=items, total=len(items))
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_ORGS)
        return result

    async def create_org(
        self, *, user_id: str, tenant_key: str, request: CreateOrgRequest
    ) -> OrgResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            # Any authenticated user may create an org (onboarding flow).
            # No platform permission required — quota/license enforcement handled separately.
            # Ensure name is unique within tenant — append random suffix if taken
            unique_name = await _unique_org_name(self._repository, conn, request.name, tenant_key)
            request = request.model_copy(update={"name": unique_name})
            existing = await self._repository.get_org_by_slug(conn, request.slug, tenant_key)
            if existing:
                raise ConflictError(f"Org slug '{request.slug}' already exists")
            org = await self._repository.create_org(
                conn,
                org_id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                org_type_code=request.org_type_code,
                name=request.name,
                slug=request.slug,
                description=request.description,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="org",
                    entity_id=org.id,
                    event_type=AuditEventType.ORG_CREATED.value,
                    event_category=AuditEventCategory.ORG.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "name": request.name,
                        "slug": request.slug,
                        "org_type_code": request.org_type_code,
                    },
                ),
            )
            # Write creator to org_memberships table (owner) — required for list_orgs_for_user
            await self._repository.add_org_member(
                conn,
                membership_id=str(uuid.uuid4()),
                org_id=org.id,
                user_id=user_id,
                role="owner",
                created_by=user_id,
                now=now,
            )
        await self._cache.delete_pattern("orgs:list:*")
        await self._cache.delete(f"orgs:user:{user_id}")
        return _org_response(org)

    async def update_org(
        self, *, user_id: str, org_id: str, request: UpdateOrgRequest
    ) -> OrgResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "org_management.update", scope_org_id=org_id)
            org = await self._repository.update_org(
                conn,
                org_id,
                name=request.name,
                description=request.description,
                is_disabled=request.is_disabled,
                updated_by=user_id,
                now=now,
            )
            if org is None:
                raise NotFoundError(f"Org '{org_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=org.tenant_key,
                    entity_type="org",
                    entity_id=org_id,
                    event_type=AuditEventType.ORG_UPDATED.value,
                    event_category=AuditEventCategory.ORG.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "name": request.name,
                        "description": request.description,
                        "is_disabled": str(request.is_disabled) if request.is_disabled is not None else None,
                    },
                ),
            )
        await self._cache.delete_pattern("orgs:list:*")
        return _org_response(org)

    async def list_members(self, *, user_id: str, org_id: str) -> list[OrgMemberResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "org_management.view", scope_org_id=org_id)

        cache_key = f"org_members:{org_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            import json
            items = json.loads(cached)
            return [OrgMemberResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            members = await self._repository.list_org_members(conn, org_id)
        result = [_member_response(m) for m in members]
        import json
        await self._cache.set(cache_key, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_ORG_MEMBERS)
        return result

    async def add_member(
        self, *, user_id: str, org_id: str, target_user_id: str, role: str
    ) -> OrgMemberResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "org_management.assign", scope_org_id=org_id)
            org = await self._repository.get_org_by_id(conn, org_id)
            if org is None:
                raise NotFoundError(f"Org '{org_id}' not found")
            member = await self._repository.add_org_member(
                conn,
                membership_id=str(uuid.uuid4()),
                org_id=org_id,
                user_id=target_user_id,
                role=role,
                created_by=user_id,
                now=now,
            )
            # Auto-assign to org-scoped system group based on membership_type
            await _scoped_groups.assign_org_member_to_scoped_group(
                conn, org_id=org_id, user_id=target_user_id, membership_type=role, now=now, created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=org.tenant_key,
                    entity_type="org",
                    entity_id=org_id,
                    event_type=AuditEventType.ORG_MEMBER_ADDED.value,
                    event_category=AuditEventCategory.ORG.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "target_user_id": target_user_id,
                        "role": role,
                    },
                ),
            )
        await self._cache.delete(f"org_members:{org_id}")
        await self._cache.delete_pattern("orgs:list:*")
        await self._cache.delete(f"orgs:user:{target_user_id}")
        await self._cache.delete_pattern(f"access:{target_user_id}:*")
        return _member_response(member)

    async def remove_member(self, *, user_id: str, org_id: str, target_user_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "org_management.revoke", scope_org_id=org_id)
            org = await self._repository.get_org_by_id(conn, org_id)
            if org is None:
                raise NotFoundError(f"Org '{org_id}' not found")
            removed = await self._repository.remove_org_member(
                conn,
                org_id=org_id,
                user_id=target_user_id,
                deleted_by=user_id,
                now=now,
            )
            if not removed:
                raise NotFoundError(f"Member '{target_user_id}' not found in org '{org_id}'")
            # Remove from org-scoped system groups
            await _scoped_groups.remove_org_member_from_scoped_groups(
                conn, org_id=org_id, user_id=target_user_id, now=now, deleted_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=org.tenant_key,
                    entity_type="org",
                    entity_id=org_id,
                    event_type=AuditEventType.ORG_MEMBER_REMOVED.value,
                    event_category=AuditEventCategory.ORG.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "target_user_id": target_user_id,
                    },
                ),
            )
        await self._cache.delete(f"org_members:{org_id}")
        await self._cache.delete_pattern("orgs:list:*")
        await self._cache.delete(f"orgs:user:{target_user_id}")
        await self._cache.delete_pattern(f"access:{target_user_id}:*")

    async def update_member_role(
        self, *, user_id: str, org_id: str, target_user_id: str, role: str
    ) -> OrgMemberResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "org_management.assign", scope_org_id=org_id)
            org = await self._repository.get_org_by_id(conn, org_id)
            if org is None:
                raise NotFoundError(f"Org '{org_id}' not found")
            member = await self._repository.update_org_member_role(
                conn,
                org_id=org_id,
                user_id=target_user_id,
                role=role,
                updated_by=user_id,
                now=now,
            )
            if member is None:
                raise NotFoundError(f"Member '{target_user_id}' not found in org '{org_id}'")
            # Swap scoped system group: remove from old, add to new
            await _scoped_groups.remove_org_member_from_scoped_groups(
                conn, org_id=org_id, user_id=target_user_id, now=now, deleted_by=user_id,
            )
            await _scoped_groups.assign_org_member_to_scoped_group(
                conn, org_id=org_id, user_id=target_user_id, membership_type=role, now=now, created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=org.tenant_key,
                    entity_type="org",
                    entity_id=org_id,
                    event_type=AuditEventType.ORG_MEMBER_ROLE_CHANGED.value,
                    event_category=AuditEventCategory.ORG.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "target_user_id": target_user_id,
                        "new_role": role,
                    },
                ),
            )
        await self._cache.delete(f"org_members:{org_id}")
        await self._cache.delete(f"orgs:user:{target_user_id}")
        await self._cache.delete_pattern(f"access:{target_user_id}:*")
        return _member_response(member)


SCHEMA = '"03_auth_manage"'


async def _unique_org_name(repo, conn, name: str, tenant_key: str) -> str:
    """Return `name` if unique within tenant, otherwise append a random 4-char suffix."""
    import random, string
    candidate = name
    for _ in range(10):
        existing = await repo.get_org_by_name(conn, candidate, tenant_key)
        if existing is None:
            return candidate
        suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=4))
        candidate = f"{name} {suffix}"
    # Extremely unlikely to still collide — return last candidate and let DB enforce
    return candidate


def _org_response(o) -> OrgResponse:
    return OrgResponse(
        id=o.id,
        tenant_key=o.tenant_key,
        org_type_code=o.org_type_code,
        name=o.name,
        slug=o.slug,
        description=o.description,
        is_active=o.is_active,
        created_at=o.created_at,
        updated_at=o.updated_at,
    )


def _member_response(m) -> OrgMemberResponse:
    return OrgMemberResponse(
        id=m.id,
        org_id=m.org_id,
        user_id=m.user_id,
        role=m.role,
        is_active=m.is_active,
        joined_at=m.joined_at,
        email=m.email,
        display_name=m.display_name,
    )
