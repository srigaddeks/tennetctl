from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import timedelta
from importlib import import_module

from .schemas import (
    ApiKeyCreatedResponse,
    ApiKeyListResponse,
    ApiKeyResponse,
    CreateApiKeyRequest,
    RevokeApiKeyRequest,
)

_settings_module = import_module("backend.00_config.settings")
_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.03_auth_manage.constants")
_repository_module = import_module("backend.03_auth_manage.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuthorizationError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AuditEventType = _constants_module.AuditEventType
AuditEventCategory = _constants_module.AuditEventCategory
AuthRepository = _repository_module.AuthRepository
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_PREFIX = "apikeys"
_CACHE_TTL_LIST = 300  # 5 min
_CACHE_TTL_HASH = 60  # 60 sec


@instrument_class_methods(
    namespace="api_keys.service", logger_name="backend.api_keys.instrumentation"
)
class ApiKeyService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AuthRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.api_keys")

    @staticmethod
    def _generate_api_key() -> tuple[str, str, str, str]:
        """Returns (full_key, key_id, key_prefix, key_hash)."""
        import uuid

        key_id = str(uuid.uuid4())
        id_prefix = key_id.replace("-", "")[:8]
        random_part = secrets.token_urlsafe(40)
        prefix = f"kctl_{id_prefix}"
        full_key = f"{prefix}_{random_part}"
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()
        return full_key, key_id, prefix, key_hash

    @staticmethod
    def _format_dt(dt) -> str | None:
        if dt is None:
            return None
        return dt.isoformat()

    async def create_api_key(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateApiKeyRequest,
    ) -> ApiKeyCreatedResponse:
        now = utc_now_sql()

        if not self._settings.api_key_enabled:
            raise ValidationError("API key management is disabled.")

        expires_at = None
        ttl_days = request.expires_in_days or self._settings.api_key_default_ttl_days
        if ttl_days:
            expires_at = now + timedelta(days=ttl_days)

        full_key, key_id, prefix, key_hash = self._generate_api_key()

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "api_key_management.create")

            active_count = await self._repository.count_active_api_keys(
                conn,
                user_id=user_id,
                tenant_key=tenant_key,
            )
            if active_count >= self._settings.api_key_max_per_user:
                raise ValidationError(
                    f"Maximum of {self._settings.api_key_max_per_user} active API keys per user."
                )

            status_id = await self._repository.get_api_key_status_id(
                conn, status_code="active"
            )
            if not status_id:
                raise ValidationError("API key status configuration not found.")

            await self._repository.create_api_key(
                conn,
                key_id=key_id,
                user_id=user_id,
                tenant_key=tenant_key,
                name=request.name.strip(),
                key_prefix=prefix,
                key_hash=key_hash,
                status_id=status_id,
                scopes=request.scopes,
                expires_at=expires_at,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    entity_type="api_key",
                    entity_id=key_id,
                    event_type=AuditEventType.API_KEY_CREATED,
                    event_category=AuditEventCategory.ACCESS,
                    actor_id=user_id,
                    tenant_key=tenant_key,
                    occurred_at=now,
                    properties={
                        "name": request.name.strip(),
                        "key_prefix": prefix,
                        "scopes": ",".join(request.scopes) if request.scopes else "",
                        "expires_at": self._format_dt(expires_at) or "never",
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:list:{user_id}")

        return ApiKeyCreatedResponse(
            id=key_id,
            name=request.name.strip(),
            key_prefix=prefix,
            api_key=full_key,
            scopes=request.scopes,
            expires_at=self._format_dt(expires_at),
            created_at=self._format_dt(now),
        )

    async def list_api_keys(
        self,
        *,
        user_id: str,
        tenant_key: str,
    ) -> ApiKeyListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:list:{user_id}"
        cached = await self._cache.get_json(cache_key)
        if cached:
            return ApiKeyListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "api_key_management.view")
            rows = await self._repository.list_api_keys(
                conn,
                user_id=user_id,
                tenant_key=tenant_key,
            )

        items = [
            ApiKeyResponse(
                id=str(r["id"]),
                name=r["name"],
                key_prefix=r["key_prefix"],
                status=r["status_code"],
                scopes=list(r["scopes"]) if r["scopes"] else None,
                expires_at=self._format_dt(r["expires_at"]),
                last_used_at=self._format_dt(r["last_used_at"]),
                last_used_ip=r.get("last_used_ip"),
                revoked_at=self._format_dt(r.get("revoked_at")),
                created_at=self._format_dt(r["created_at"]),
            )
            for r in rows
        ]
        result = ApiKeyListResponse(items=items, total=len(items))
        await self._cache.set_json(
            cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL_LIST
        )
        return result

    async def get_api_key(
        self,
        *,
        user_id: str,
        key_id: str,
    ) -> ApiKeyResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "api_key_management.view")
            row = await self._repository.get_api_key_by_id(
                conn,
                key_id=key_id,
                user_id=user_id,
            )

        if not row:
            raise NotFoundError("API key not found.")

        return ApiKeyResponse(
            id=str(row["id"]),
            name=row["name"],
            key_prefix=row["key_prefix"],
            status=row["status_code"],
            scopes=list(row["scopes"]) if row["scopes"] else None,
            expires_at=self._format_dt(row["expires_at"]),
            last_used_at=self._format_dt(row["last_used_at"]),
            last_used_ip=row.get("last_used_ip"),
            revoked_at=self._format_dt(row.get("revoked_at")),
            revoke_reason=row.get("revoke_reason"),
            created_at=self._format_dt(row["created_at"]),
        )

    async def rotate_api_key(
        self,
        *,
        user_id: str,
        tenant_key: str,
        key_id: str,
    ) -> ApiKeyCreatedResponse:
        now = utc_now_sql()

        if not self._settings.api_key_enabled:
            raise ValidationError("API key management is disabled.")

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "api_key_management.update")

            old_key = await self._repository.get_api_key_by_id(
                conn,
                key_id=key_id,
                user_id=user_id,
            )
            if not old_key:
                raise NotFoundError("API key not found.")
            if old_key["status_code"] != "active":
                raise ValidationError("Only active API keys can be rotated.")

            revoked_status_id = await self._repository.get_api_key_status_id(
                conn, status_code="revoked"
            )
            await self._repository.revoke_api_key(
                conn,
                key_id=key_id,
                revoked_by=user_id,
                revoke_reason="Rotated",
                revoked_status_id=revoked_status_id,
                now=now,
            )

            full_key, new_key_id, prefix, key_hash = self._generate_api_key()
            active_status_id = await self._repository.get_api_key_status_id(
                conn, status_code="active"
            )

            old_scopes = list(old_key["scopes"]) if old_key["scopes"] else None
            old_expires = old_key["expires_at"]

            await self._repository.create_api_key(
                conn,
                key_id=new_key_id,
                user_id=user_id,
                tenant_key=tenant_key,
                name=old_key["name"],
                key_prefix=prefix,
                key_hash=key_hash,
                status_id=active_status_id,
                scopes=old_scopes,
                expires_at=old_expires,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    entity_type="api_key",
                    entity_id=new_key_id,
                    event_type=AuditEventType.API_KEY_ROTATED,
                    event_category=AuditEventCategory.ACCESS,
                    actor_id=user_id,
                    tenant_key=tenant_key,
                    occurred_at=now,
                    properties={
                        "old_key_id": key_id,
                        "old_key_prefix": old_key["key_prefix"],
                        "new_key_prefix": prefix,
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:list:{user_id}")

        return ApiKeyCreatedResponse(
            id=new_key_id,
            name=old_key["name"],
            key_prefix=prefix,
            api_key=full_key,
            scopes=old_scopes,
            expires_at=self._format_dt(old_expires),
            created_at=self._format_dt(now),
        )

    async def revoke_api_key(
        self,
        *,
        user_id: str,
        tenant_key: str,
        key_id: str,
        request: RevokeApiKeyRequest,
    ) -> ApiKeyResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "api_key_management.revoke")

            key_row = await self._repository.get_api_key_by_id(
                conn,
                key_id=key_id,
                user_id=user_id,
            )
            if not key_row:
                raise NotFoundError("API key not found.")
            if key_row["status_code"] != "active":
                raise ValidationError("Only active API keys can be revoked.")

            revoked_status_id = await self._repository.get_api_key_status_id(
                conn, status_code="revoked"
            )
            await self._repository.revoke_api_key(
                conn,
                key_id=key_id,
                revoked_by=user_id,
                revoke_reason=request.reason,
                revoked_status_id=revoked_status_id,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    entity_type="api_key",
                    entity_id=key_id,
                    event_type=AuditEventType.API_KEY_REVOKED,
                    event_category=AuditEventCategory.ACCESS,
                    actor_id=user_id,
                    tenant_key=tenant_key,
                    occurred_at=now,
                    properties={
                        "key_prefix": key_row["key_prefix"],
                        "reason": request.reason or "",
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:list:{user_id}")

        return ApiKeyResponse(
            id=str(key_row["id"]),
            name=key_row["name"],
            key_prefix=key_row["key_prefix"],
            status="revoked",
            scopes=list(key_row["scopes"]) if key_row["scopes"] else None,
            expires_at=self._format_dt(key_row["expires_at"]),
            last_used_at=self._format_dt(key_row["last_used_at"]),
            last_used_ip=key_row.get("last_used_ip"),
            revoked_at=self._format_dt(now),
            revoke_reason=request.reason,
            created_at=self._format_dt(key_row["created_at"]),
        )

    async def delete_api_key(
        self,
        *,
        user_id: str,
        tenant_key: str,
        key_id: str,
    ) -> None:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "api_key_management.revoke")

            deleted = await self._repository.soft_delete_api_key(
                conn,
                key_id=key_id,
                user_id=user_id,
                now=now,
            )
            if not deleted:
                raise NotFoundError("API key not found.")

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    entity_type="api_key",
                    entity_id=key_id,
                    event_type=AuditEventType.API_KEY_DELETED,
                    event_category=AuditEventCategory.ACCESS,
                    actor_id=user_id,
                    tenant_key=tenant_key,
                    occurred_at=now,
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:list:{user_id}")
