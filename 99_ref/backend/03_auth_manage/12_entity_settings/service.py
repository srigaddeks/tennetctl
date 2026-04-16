"""Generic entity settings service — handles any entity type via registry config."""

from __future__ import annotations

from importlib import import_module
from uuid import uuid4

_errors = import_module("backend.01_core.errors")
_audit = import_module("backend.01_core.audit")
_perm_check = import_module("backend.03_auth_manage._permission_check")
_time = import_module("backend.01_core.time_utils")

NotFoundError = _errors.NotFoundError
AuditWriter = _audit.AuditWriter
AuditEntry = _audit.AuditEntry
require_permission = _perm_check.require_permission
utc_now_sql = _time.utc_now_sql

_registry_mod = import_module("backend.03_auth_manage.12_entity_settings.registry")
_repo_mod = import_module("backend.03_auth_manage.12_entity_settings.repository")
_schemas_mod = import_module("backend.03_auth_manage.12_entity_settings.schemas")

EntityConfig = _registry_mod.EntityConfig
ENTITY_REGISTRY = _registry_mod.ENTITY_REGISTRY
EntitySettingsRepository = _repo_mod.EntitySettingsRepository
SettingResponse = _schemas_mod.SettingResponse
SettingListResponse = _schemas_mod.SettingListResponse
BatchSetSettingsResponse = _schemas_mod.BatchSetSettingsResponse
SettingKeyResponse = _schemas_mod.SettingKeyResponse
SettingKeyListResponse = _schemas_mod.SettingKeyListResponse

_CACHE_TTL_SETTINGS = 300
_CACHE_TTL_SETTING_KEYS = 600

# Cache keys from other services that must be invalidated when their entity settings change
_CROSS_CACHE_INVALIDATION: dict[str, list[str]] = {
    "feature": ["features:list"],  # feature flag list includes org_visibility + required_license
}


class EntitySettingsService:
    """Unified EAV settings CRUD for any registered entity type."""

    def __init__(self, *, settings, database_pool, cache):
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repo = EntitySettingsRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")

    async def _invalidate_cross_caches(self, entity_type: str) -> None:
        """Invalidate caches in other services affected by entity setting changes."""
        for key in _CROSS_CACHE_INVALIDATION.get(entity_type, []):
            await self._cache.delete(key)

    def _get_config(self, entity_type: str) -> EntityConfig:
        cfg = ENTITY_REGISTRY.get(entity_type)
        if cfg is None:
            raise NotFoundError(f"Unknown entity type '{entity_type}'")
        return cfg

    async def _resolve_scope(
        self, connection, entity_type: str, entity_id: str
    ) -> tuple[str | None, str | None]:
        """Return (scope_org_id, scope_workspace_id) for permission checks.

        - org entity → (entity_id, None)
        - workspace entity → (workspace.org_id, entity_id)
        - all others → (None, None) — platform-scope check
        """
        if entity_type == "org":
            return entity_id, None
        if entity_type == "workspace":
            row = await connection.fetchrow(
                'SELECT org_id FROM "03_auth_manage"."34_fct_workspaces" WHERE id = $1',
                entity_id,
            )
            if row:
                return row["org_id"], entity_id
        return None, None

    async def _resolve_entity_id(
        self, connection, cfg: EntityConfig, entity_id_or_code: str
    ) -> tuple[str, str]:
        """Return (resolved_entity_id, tenant_key).

        For code-based entities (feature flags), resolves code → UUID first.
        """
        if cfg.resolve_from_code:
            resolved_id = await self._repo.resolve_code_to_id(
                connection,
                code_lookup_table=cfg.code_lookup_table,
                code_lookup_column=cfg.code_lookup_column,
                code=entity_id_or_code,
            )
            if resolved_id is None:
                raise NotFoundError(
                    f"{cfg.entity_type} '{entity_id_or_code}' not found"
                )
            tenant_key = await self._repo.entity_exists(
                connection,
                fact_table=cfg.fact_table,
                fact_id_column=cfg.fact_id_column,
                entity_id=resolved_id,
                tenant_key_column=cfg.tenant_key_column,
            )
            return resolved_id, tenant_key or "default"

        tenant_key = await self._repo.entity_exists(
            connection,
            fact_table=cfg.fact_table,
            fact_id_column=cfg.fact_id_column,
            entity_id=entity_id_or_code,
            tenant_key_column=cfg.tenant_key_column,
        )
        if tenant_key is None:
            raise NotFoundError(
                f"{cfg.entity_type} '{entity_id_or_code}' not found"
            )
        return entity_id_or_code, tenant_key

    # ── list settings ──────────────────────────────────────────────────

    async def list_settings(
        self,
        *,
        entity_type: str,
        entity_id: str,
        actor_id: str,
    ) -> SettingListResponse:
        cfg = self._get_config(entity_type)

        async with self._database_pool.acquire() as conn:
            scope_org_id, scope_workspace_id = await self._resolve_scope(
                conn, entity_type, entity_id
            )
            await require_permission(
                conn, actor_id, f"{cfg.permission_prefix}.view",
                scope_org_id=scope_org_id, scope_workspace_id=scope_workspace_id,
            )

        cache_key = f"{cfg.cache_prefix}:{entity_id}:settings"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return SettingListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            resolved_id, _ = await self._resolve_entity_id(conn, cfg, entity_id)
            pairs = await self._repo.list_settings(
                conn,
                detail_table=cfg.detail_table,
                entity_id_column=cfg.entity_id_column,
                entity_id=resolved_id,
            )
        result = SettingListResponse(
            settings=[SettingResponse(key=k, value=v) for k, v in pairs]
        )
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_SETTINGS)
        return result

    # ── set single setting ─────────────────────────────────────────────

    async def set_setting(
        self,
        *,
        entity_type: str,
        entity_id: str,
        setting_key: str,
        setting_value: str,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
    ) -> SettingResponse:
        cfg = self._get_config(entity_type)
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            scope_org_id, scope_workspace_id = await self._resolve_scope(
                conn, entity_type, entity_id
            )
            await require_permission(
                conn, actor_id, f"{cfg.permission_prefix}.update",
                scope_org_id=scope_org_id, scope_workspace_id=scope_workspace_id,
            )
            resolved_id, tenant_key = await self._resolve_entity_id(
                conn, cfg, entity_id
            )
            if not await self._repo.setting_key_exists(
                conn, dimension_table=cfg.dimension_table, setting_key=setting_key
            ):
                raise NotFoundError(f"Setting key '{setting_key}' is not valid")
            await self._repo.upsert_setting(
                conn,
                detail_table=cfg.detail_table,
                entity_id_column=cfg.entity_id_column,
                entity_id=resolved_id,
                setting_key=setting_key,
                setting_value=setting_value,
                updated_by=actor_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type=cfg.audit_entity_type,
                    entity_id=resolved_id,
                    event_type=cfg.audit_event_type,
                    event_category="settings",
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={
                        "setting_key": setting_key,
                        "setting_value": setting_value,
                    },
                ),
            )
        await self._cache.delete(f"{cfg.cache_prefix}:{entity_id}:settings")
        await self._invalidate_cross_caches(entity_type)
        return SettingResponse(key=setting_key, value=setting_value)

    # ── batch set settings ─────────────────────────────────────────────

    async def batch_set_settings(
        self,
        *,
        entity_type: str,
        entity_id: str,
        settings: dict[str, str],
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
    ) -> BatchSetSettingsResponse:
        cfg = self._get_config(entity_type)
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            scope_org_id, scope_workspace_id = await self._resolve_scope(
                conn, entity_type, entity_id
            )
            await require_permission(
                conn, actor_id, f"{cfg.permission_prefix}.update",
                scope_org_id=scope_org_id, scope_workspace_id=scope_workspace_id,
            )
            resolved_id, tenant_key = await self._resolve_entity_id(
                conn, cfg, entity_id
            )
            for key in settings:
                if not await self._repo.setting_key_exists(
                    conn, dimension_table=cfg.dimension_table, setting_key=key
                ):
                    raise NotFoundError(f"Setting key '{key}' is not valid")
            for key, value in settings.items():
                await self._repo.upsert_setting(
                    conn,
                    detail_table=cfg.detail_table,
                    entity_id_column=cfg.entity_id_column,
                    entity_id=resolved_id,
                    setting_key=key,
                    setting_value=value,
                    updated_by=actor_id,
                    now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type=cfg.audit_entity_type,
                    entity_id=resolved_id,
                    event_type=cfg.audit_event_type,
                    event_category="settings",
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={
                        "setting_keys": ",".join(settings.keys()),
                        "setting_count": str(len(settings)),
                    },
                ),
            )
        await self._cache.delete(f"{cfg.cache_prefix}:{entity_id}:settings")
        await self._invalidate_cross_caches(entity_type)
        return BatchSetSettingsResponse(
            settings=[SettingResponse(key=k, value=v) for k, v in settings.items()]
        )

    # ── delete setting ─────────────────────────────────────────────────

    async def delete_setting(
        self,
        *,
        entity_type: str,
        entity_id: str,
        setting_key: str,
        actor_id: str,
        client_ip: str | None,
        session_id: str | None,
    ) -> None:
        cfg = self._get_config(entity_type)
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            scope_org_id, scope_workspace_id = await self._resolve_scope(
                conn, entity_type, entity_id
            )
            await require_permission(
                conn, actor_id, f"{cfg.permission_prefix}.update",
                scope_org_id=scope_org_id, scope_workspace_id=scope_workspace_id,
            )
            resolved_id, tenant_key = await self._resolve_entity_id(
                conn, cfg, entity_id
            )
            deleted = await self._repo.delete_setting(
                conn,
                detail_table=cfg.detail_table,
                entity_id_column=cfg.entity_id_column,
                entity_id=resolved_id,
                setting_key=setting_key,
            )
            if not deleted:
                raise NotFoundError(
                    f"Setting '{setting_key}' not found for {cfg.entity_type} '{entity_id}'"
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type=cfg.audit_entity_type,
                    entity_id=resolved_id,
                    event_type=cfg.audit_event_type,
                    event_category="settings",
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={"setting_key_deleted": setting_key},
                ),
            )
        await self._cache.delete(f"{cfg.cache_prefix}:{entity_id}:settings")
        await self._invalidate_cross_caches(entity_type)

    # ── list setting keys (dimension table) ────────────────────────────

    async def list_setting_keys(
        self,
        *,
        entity_type: str,
        actor_id: str,
    ) -> SettingKeyListResponse:
        cfg = self._get_config(entity_type)

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, actor_id, f"{cfg.permission_prefix}.view")

        cache_key = f"{cfg.cache_prefix}_setting_keys:list"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return SettingKeyListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            keys = await self._repo.list_setting_keys(
                conn, dimension_table=cfg.dimension_table
            )
        result = SettingKeyListResponse(
            keys=[SettingKeyResponse(**k) for k in keys]
        )
        await self._cache.set(
            cache_key, result.model_dump_json(), _CACHE_TTL_SETTING_KEYS
        )
        return result
