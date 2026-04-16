from __future__ import annotations

from importlib import import_module

from .repository import FeatureFlagRepository
from .schemas import (
    AddPermissionRequest,
    CreateFeatureCategoryRequest,
    CreateFeatureFlagRequest,
    FeatureCategoryResponse,
    FeatureFlagListResponse,
    FeatureFlagResponse,
    FeaturePermissionResponse,
    OrgAvailableFlagResponse,
    OrgAvailableFlagsResponse,
    PermissionActionTypeResponse,
    PermissionActionResponse,
    PermissionActionListResponse,
    UpdateFeatureFlagRequest,
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
require_permission = _perm_check_module.require_permission
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
utc_now_sql = _time_module.utc_now_sql

import asyncpg
from uuid import uuid4

SCHEMA = '"03_auth_manage"'

_CACHE_KEY_FLAGS = "features:list"
_CACHE_TTL_FLAGS = 600  # 10 minutes


@instrument_class_methods(namespace="feature_flags.service", logger_name="backend.feature_flags.instrumentation")
class FeatureFlagService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = FeatureFlagRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.feature_flags")

    async def list_flags(self, *, actor_id: str) -> FeatureFlagListResponse:
        async with self._database_pool.acquire() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.view")

        cached = await self._cache.get(_CACHE_KEY_FLAGS)
        if cached is not None:
            return FeatureFlagListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            categories = await self._repository.list_categories(connection)
            flags = await self._repository.list_feature_flags(connection)
            all_permissions = await self._repository.list_all_permissions(connection)
            # Batch-load org_visibility and required_license for all flags in 1 query
            flag_settings = await self._repository.list_flag_settings_batch(
                connection, ["org_visibility", "required_license"]
            )

        perms_by_flag: dict[str, list[FeaturePermissionResponse]] = {}
        for p in all_permissions:
            perms_by_flag.setdefault(p.feature_flag_code, []).append(
                FeaturePermissionResponse(
                    id=p.id, code=p.code, feature_flag_code=p.feature_flag_code,
                    permission_action_code=p.permission_action_code,
                    name=p.name, description=p.description,
                )
            )

        result = FeatureFlagListResponse(
            categories=[
                FeatureCategoryResponse(id=c.id, code=c.code, name=c.name,
                                        description=c.description, sort_order=c.sort_order)
                for c in categories
            ],
            flags=[
                FeatureFlagResponse(
                    id=f.id, code=f.code, name=f.name, description=f.description,
                    category_code=f.category_code, feature_scope=f.feature_scope,
                    access_mode=f.access_mode,
                    lifecycle_state=f.lifecycle_state, initial_audience=f.initial_audience,
                    env_dev=f.env_dev, env_staging=f.env_staging, env_prod=f.env_prod,
                    org_visibility=flag_settings.get(f.code, {}).get("org_visibility", "hidden")
                        if f.feature_scope == "org" else None,
                    required_license=flag_settings.get(f.code, {}).get("required_license"),
                    permissions=perms_by_flag.get(f.code, []),
                    created_at=f.created_at, updated_at=f.updated_at,
                )
                for f in flags
            ],
        )
        await self._cache.set(_CACHE_KEY_FLAGS, result.model_dump_json(), _CACHE_TTL_FLAGS)
        return result

    async def create_category(
        self,
        payload: CreateFeatureCategoryRequest,
        *,
        actor_id: str,
    ) -> FeatureCategoryResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.create")
            try:
                cat = await self._repository.create_category(
                    connection,
                    category_id=str(uuid4()),
                    code=payload.code,
                    name=payload.name,
                    description=payload.description,
                    sort_order=payload.sort_order,
                    now=now,
                )
            except asyncpg.UniqueViolationError:
                ConflictError = _errors_module.ConflictError
                raise ConflictError(f"Category code '{payload.code}' already exists")
        await self._cache.delete(_CACHE_KEY_FLAGS)
        return FeatureCategoryResponse(
            id=cat.id, code=cat.code, name=cat.name,
            description=cat.description, sort_order=cat.sort_order,
        )

    async def create_flag(
        self,
        payload: CreateFeatureFlagRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> FeatureFlagResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.create")
            try:
                flag = await self._repository.create_feature_flag(
                    connection,
                    code=payload.code,
                    name=payload.name,
                    description=payload.description,
                    category_code=payload.category_code,
                    feature_scope=payload.feature_scope,
                    access_mode=payload.access_mode,
                    lifecycle_state=payload.lifecycle_state,
                    initial_audience=payload.initial_audience,
                    env_dev=payload.env_dev,
                    env_staging=payload.env_staging,
                    env_prod=payload.env_prod,
                    now=now,
                )
            except asyncpg.UniqueViolationError:
                raise ConflictError(f"Feature flag '{payload.code}' already exists.")

            # Seed initial permissions if requested
            seeded_perms: list[FeaturePermissionResponse] = []
            if payload.permissions:
                valid_actions = await self._repository.list_permission_action_types(connection)
                valid_codes = {a["code"] for a in valid_actions}
                for action_code in payload.permissions:
                    if action_code not in valid_codes:
                        continue
                    existing = await self._repository.get_permission_by_flag_and_action(
                        connection, flag.code, action_code
                    )
                    if existing:
                        continue
                    perm = await self._repository.create_permission(
                        connection, flag_code=flag.code, action_code=action_code, now=now
                    )
                    await self._assign_permission_to_super_admin(connection, perm.id, now)
                    seeded_perms.append(FeaturePermissionResponse(
                        id=perm.id, code=perm.code, feature_flag_code=perm.feature_flag_code,
                        permission_action_code=perm.permission_action_code,
                        name=perm.name, description=perm.description,
                    ))

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="feature_flag",
                    entity_id=flag.id,
                    event_type="feature_flag_created",
                    event_category="access",
                    occurred_at=now,
                    actor_id=actor_id,
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={
                        "event_key": flag.code, "code": flag.code, "name": flag.name,
                        "permissions_seeded": str(len(seeded_perms)),
                    },
                ),
            )

            for perm_req in payload.permissions:
                await self._repository.create_feature_permission(
                    connection,
                    id=str(uuid4()),
                    code=f"{flag.code}.{perm_req.permission_action_code}",
                    feature_flag_code=flag.code,
                    permission_action_code=perm_req.permission_action_code,
                    name=perm_req.name,
                    description=perm_req.description,
                    now=now,
                )

        await self._cache.delete(_CACHE_KEY_FLAGS)
        permissions = await self._load_permissions_for(flag.code)
        return _flag_to_response(flag, permissions)

    async def update_flag(
        self,
        code: str,
        payload: UpdateFeatureFlagRequest,
        *,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
        request_id: str | None,
    ) -> FeatureFlagResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.update")
            existing = await self._repository.get_feature_flag_by_code(connection, code)
            if existing is None:
                raise NotFoundError(f"Feature flag '{code}' not found.")
            assert existing is not None

            flag = await self._repository.update_feature_flag(
                connection,
                code=code,
                name=payload.name,
                description=payload.description,
                category_code=payload.category_code,
                feature_scope=payload.feature_scope,
                access_mode=payload.access_mode,
                lifecycle_state=payload.lifecycle_state,
                env_dev=payload.env_dev,
                env_staging=payload.env_staging,
                env_prod=payload.env_prod,
                now=now,
            )

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=self._settings.default_tenant_key,
                    entity_type="feature_flag",
                    entity_id=existing.id,
                    event_type="feature_flag_updated",
                    event_category="access",
                    occurred_at=now,
                    actor_id=actor_id,
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={
                        "event_key": code,
                        "previous_lifecycle_state": existing.lifecycle_state,
                        "new_lifecycle_state": flag.lifecycle_state if flag else None,
                    },
                ),
            )

            if payload.permissions is not None:
                await self._repository.delete_permissions_by_flag_code(connection, code)
                for perm_req in payload.permissions:
                    await self._repository.create_feature_permission(
                        connection,
                        id=str(uuid4()),
                        code=f"{code}.{perm_req.permission_action_code}",
                        feature_flag_code=code,
                        permission_action_code=perm_req.permission_action_code,
                        name=perm_req.name,
                        description=perm_req.description,
                        now=now,
                    )

        assert flag is not None
        await self._cache.delete(_CACHE_KEY_FLAGS)
        permissions = await self._load_permissions_for(flag.code)
        return _flag_to_response(flag, permissions)

    async def list_permission_actions(self, actor_id: str) -> PermissionActionListResponse:
        async with self._database_pool.acquire() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.view")
            actions = await self._repository.list_permission_actions(connection)

        return PermissionActionListResponse(
            actions=[
                PermissionActionResponse(
                    id=a.id,
                    code=a.code,
                    name=a.name,
                    description=a.description,
                    sort_order=a.sort_order,
                )
                for a in actions
            ]
        )

    async def list_org_available_flags(self) -> OrgAvailableFlagsResponse:
        """List org-scoped flags visible to org admins. No platform permission required."""
        async with self._database_pool.acquire() as connection:
            categories = await self._repository.list_categories(connection)
            rows = await self._repository.list_org_available_flags(connection)
            all_permissions = await self._repository.list_all_permissions(connection)

        perms_by_flag: dict[str, list[FeaturePermissionResponse]] = {}
        for p in all_permissions:
            perms_by_flag.setdefault(p.feature_flag_code, []).append(
                FeaturePermissionResponse(
                    id=p.id, code=p.code, feature_flag_code=p.feature_flag_code,
                    permission_action_code=p.permission_action_code,
                    name=p.name, description=p.description,
                )
            )

        return OrgAvailableFlagsResponse(
            categories=[
                FeatureCategoryResponse(id=c.id, code=c.code, name=c.name,
                                        description=c.description, sort_order=c.sort_order)
                for c in categories
            ],
            flags=[
                OrgAvailableFlagResponse(
                    id=row["id"], code=row["code"], name=row["name"],
                    description=row["description"],
                    category_code=row["feature_flag_category_code"],
                    feature_scope=row["feature_scope"],
                    lifecycle_state=row["lifecycle_state"],
                    env_dev=row["env_dev"], env_staging=row["env_staging"], env_prod=row["env_prod"],
                    org_visibility=row["org_visibility"],
                    required_license=row.get("required_license"),
                    permissions=perms_by_flag.get(row["code"], []),
                )
                for row in rows
            ],
        )

    async def list_action_types(self) -> list[PermissionActionTypeResponse]:
        async with self._database_pool.acquire() as connection:
            rows = await self._repository.list_permission_action_types(connection)
        return [
            PermissionActionTypeResponse(
                code=r["code"], name=r["name"],
                description=r["description"], sort_order=r["sort_order"],
            )
            for r in rows
        ]

    async def add_permission(
        self,
        flag_code: str,
        payload: AddPermissionRequest,
        *,
        actor_id: str,
    ) -> FeaturePermissionResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.update")
            flag = await self._repository.get_feature_flag_by_code(connection, flag_code)
            if flag is None:
                raise NotFoundError(f"Feature flag '{flag_code}' not found.")
            # Validate action code exists
            valid_actions = await self._repository.list_permission_action_types(connection)
            valid_codes = {a["code"] for a in valid_actions}
            if payload.action_code not in valid_codes:
                _validation_error = _errors_module.ValidationError if hasattr(_errors_module, "ValidationError") else ValueError
                raise ValueError(f"Unknown action code '{payload.action_code}'. Valid: {sorted(valid_codes)}")
            existing = await self._repository.get_permission_by_flag_and_action(
                connection, flag_code, payload.action_code
            )
            if existing is not None:
                raise ConflictError(
                    f"Permission '{flag_code}.{payload.action_code}' already exists."
                )
            perm = await self._repository.create_permission(
                connection, flag_code=flag_code, action_code=payload.action_code, now=now
            )
            await self._assign_permission_to_super_admin(connection, perm.id, now)
        await self._cache.delete(_CACHE_KEY_FLAGS)
        # Also invalidate roles cache since platform_super_admin permissions changed
        await self._cache.delete_pattern("roles:list:*")
        await self._cache.delete_pattern("access:*")
        return FeaturePermissionResponse(
            id=perm.id, code=perm.code, feature_flag_code=perm.feature_flag_code,
            permission_action_code=perm.permission_action_code,
            name=perm.name, description=perm.description,
        )

    async def remove_permission(
        self,
        flag_code: str,
        action_code: str,
        *,
        actor_id: str,
    ) -> None:
        async with self._database_pool.transaction() as connection:
            await require_permission(connection, actor_id, "feature_flag_registry.update")
            perm = await self._repository.get_permission_by_flag_and_action(
                connection, flag_code, action_code
            )
            if perm is None:
                raise NotFoundError(
                    f"Permission '{flag_code}.{action_code}' not found."
                )
            await self._repository.delete_permission(connection, perm.id)
        await self._cache.delete(_CACHE_KEY_FLAGS)

    async def _assign_permission_to_super_admin(
        self, connection: asyncpg.Connection, permission_id: str, now: object
    ) -> None:
        """Auto-assign a new permission to the platform_super_admin role (idempotent)."""
        row = await connection.fetchrow(
            f"""
            SELECT id FROM {SCHEMA}."16_fct_roles"
            WHERE code = 'platform_super_admin' AND is_deleted = FALSE
            LIMIT 1
            """
        )
        if row is None:
            return
        role_id = str(row["id"])
        try:
            await connection.execute(
                f"""
                INSERT INTO {SCHEMA}."20_lnk_role_feature_permissions" (
                    id, role_id, feature_permission_id,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
                )
                VALUES ($1, $2, $3, TRUE, FALSE, FALSE, FALSE, TRUE, TRUE,
                        $4, $5, $6::uuid, $6::uuid, NULL, NULL)
                ON CONFLICT DO NOTHING
                """,
                str(uuid4()), role_id, permission_id, now, now, role_id,
            )
        except Exception:
            pass  # Already assigned or constraint — skip silently

    async def _load_permissions_for(self, flag_code: str) -> list[FeaturePermissionResponse]:
        async with self._database_pool.acquire() as connection:
            perms = await self._repository.list_permissions_for_flag(connection, flag_code)
        return [
            FeaturePermissionResponse(
                id=p.id, code=p.code, feature_flag_code=p.feature_flag_code,
                permission_action_code=p.permission_action_code,
                name=p.name, description=p.description,
            )
            for p in perms
        ]


def _flag_to_response(
    flag,
    permissions: list[FeaturePermissionResponse],
) -> FeatureFlagResponse:
    return FeatureFlagResponse(
        id=flag.id, code=flag.code, name=flag.name, description=flag.description,
        category_code=flag.category_code, feature_scope=flag.feature_scope,
        access_mode=flag.access_mode,
        lifecycle_state=flag.lifecycle_state, initial_audience=flag.initial_audience,
        env_dev=flag.env_dev, env_staging=flag.env_staging, env_prod=flag.env_prod,
        permissions=permissions,
        created_at=flag.created_at, updated_at=flag.updated_at,
    )
