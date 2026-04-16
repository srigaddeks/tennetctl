from __future__ import annotations

from datetime import timedelta
from importlib import import_module
from uuid import uuid4

from ..constants import AuditEventCategory, AuditEventType, BEARER_TOKEN_TYPE
from ..models import AccessTokenClaims
from ..repository import AuthRepository
from .schemas import (
    EndImpersonationResponse,
    ImpersonationStatusResponse,
    StartImpersonationRequest,
    StartImpersonationResponse,
)


_settings_module = import_module("backend.00_config.settings")
_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_jwt_module = import_module("backend.03_auth_manage.01_authlib.jwt_codec")
_refresh_module = import_module("backend.03_auth_manage.02_token_gen.refresh_tokens")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_permission_module = import_module("backend.03_auth_manage._permission_check")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
AuthorizationError = _errors_module.AuthorizationError
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
JWTCodec = _jwt_module.JWTCodec
KeyStore = _jwt_module.KeyStore
JTIBlocklist = _jwt_module.JTIBlocklist
RefreshTokenManager = _refresh_module.RefreshTokenManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
record_auth_event = _telemetry_module.record_auth_event
require_permission = _permission_module.require_permission
utc_now_sql = import_module("backend.01_core.time_utils").utc_now_sql


@instrument_class_methods(namespace="auth.impersonation", logger_name="backend.auth.impersonation.instrumentation")
class ImpersonationService:

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
        key_store = KeyStore.from_settings(settings)
        jti_blocklist = JTIBlocklist() if settings.access_token_jti_blocklist_enabled else None
        self._jwt_codec = JWTCodec(
            algorithm=settings.access_token_algorithm,
            issuer=settings.access_token_issuer,
            audience=settings.access_token_audience,
            ttl_seconds=settings.access_token_ttl_seconds,
            key_store=key_store,
            jti_blocklist=jti_blocklist,
            enable_jti=settings.access_token_jti_blocklist_enabled,
        )
        self._refresh_tokens = RefreshTokenManager()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.auth.impersonation")

    async def start_impersonation(
        self,
        payload: StartImpersonationRequest,
        *,
        admin_claims: AccessTokenClaims,
        client_ip: str | None,
        user_agent: str | None,
        request_id: str | None,
    ) -> StartImpersonationResponse:
        # Guard: impersonation feature must be enabled
        if not self._settings.impersonation_enabled:
            raise AuthorizationError("User impersonation is not enabled.")

        # Guard: cannot impersonate while already impersonating
        if admin_claims.is_impersonation:
            raise AuthorizationError("Cannot start impersonation while already impersonating.")

        now = utc_now_sql()
        tenant_key = admin_claims.tenant_key
        target_user_id = payload.target_user_id

        async with self._database_pool.transaction() as connection:
            # Permission check
            await require_permission(connection, admin_claims.subject, "user_impersonation.enable")

            # Validate target user exists and is active
            target_user = await self._repository.get_user_basic(connection, user_id=target_user_id)
            if target_user is None:
                raise NotFoundError("Target user not found.")
            if (
                not target_user["is_active"]
                or target_user["is_disabled"]
                or target_user["is_deleted"]
                or target_user["is_locked"]
            ):
                raise AuthorizationError("Cannot impersonate an inactive, disabled, or locked user.")

            # Guard: single active impersonation per admin
            if await self._repository.has_active_impersonation_session(
                connection, impersonator_user_id=admin_claims.subject,
            ):
                raise ConflictError("You already have an active impersonation session. End it first.")

            # Create impersonation session
            refresh_ttl = self._settings.impersonation_refresh_token_ttl_seconds
            refresh_expires_at = now + timedelta(seconds=refresh_ttl)
            session_id = await self._repository.create_impersonation_session(
                connection,
                target_user_id=target_user_id,
                impersonator_user_id=admin_claims.subject,
                tenant_key=tenant_key,
                refresh_token_hash="pending",
                refresh_expires_at=refresh_expires_at,
                impersonation_reason=payload.reason,
                client_ip=client_ip,
                user_agent=user_agent,
                now=now,
            )

            # Generate and rotate refresh token
            refresh_token = self._refresh_tokens.generate(session_id)
            refresh_parts = self._refresh_tokens.parse(refresh_token)
            await self._repository.rotate_session(
                connection,
                session_id=session_id,
                new_refresh_token_hash=self._refresh_tokens.hash_secret(refresh_parts.secret),
                now=now,
            )

            # Encode access token with impersonation claims
            access_ttl = self._settings.impersonation_access_token_ttl_seconds
            access_token = self._jwt_codec.encode_access_token(
                subject=target_user_id,
                session_id=session_id,
                tenant_key=tenant_key,
                extra_claims={
                    "imp": True,
                    "imp_sub": admin_claims.subject,
                    "imp_sid": admin_claims.session_id,
                },
                ttl_override=access_ttl,
            )

            # Get target user profile for response
            target_profile = await self._repository.read_user_profile(
                connection, tenant_key=tenant_key, user_id=target_user_id,
            )

            # Audit
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="session",
                    entity_id=session_id,
                    event_type=AuditEventType.IMPERSONATION_STARTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=admin_claims.subject,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=admin_claims.session_id,
                    properties={
                        "target_user_id": target_user_id,
                        "reason": payload.reason,
                        "impersonation_access_ttl_seconds": str(access_ttl),
                        "impersonation_refresh_ttl_seconds": str(refresh_ttl),
                    },
                ),
            )

        record_auth_event("impersonation_start", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "impersonation_started",
            extra={
                "request_id": request_id,
                "tenant_key": tenant_key,
                "impersonator_id": admin_claims.subject,
                "target_user_id": target_user_id,
                "impersonation_session_id": session_id,
                "reason": payload.reason,
                "outcome": "success",
            },
        )

        from ..schemas import AuthUserResponse
        return StartImpersonationResponse(
            access_token=access_token.token,
            token_type=BEARER_TOKEN_TYPE,
            expires_in=access_ttl,
            refresh_token=refresh_token,
            refresh_expires_in=refresh_ttl,
            target_user=AuthUserResponse(
                user_id=target_profile.user_id,
                tenant_key=target_profile.tenant_key,
                email=target_profile.email,
                username=target_profile.username,
                email_verified=target_profile.email_verified,
                account_status=target_profile.account_status,
            ),
            impersonation_session_id=session_id,
        )

    async def end_impersonation(
        self,
        *,
        claims: AccessTokenClaims,
        client_ip: str | None,
        request_id: str | None,
    ) -> EndImpersonationResponse:
        if not claims.is_impersonation:
            raise AuthorizationError("Current session is not an impersonation session.")

        now = utc_now_sql()

        async with self._database_pool.transaction() as connection:
            await self._repository.revoke_session(
                connection,
                session_id=claims.session_id,
                reason="impersonation_ended",
                now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=claims.tenant_key,
                    entity_type="session",
                    entity_id=claims.session_id,
                    event_type=AuditEventType.IMPERSONATION_ENDED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=claims.impersonator_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=claims.session_id,
                    properties={
                        "target_user_id": claims.subject,
                        "ended_by": "admin",
                    },
                ),
            )

        record_auth_event("impersonation_end", outcome="success", tenant_key=claims.tenant_key)
        self._logger.info(
            "impersonation_ended",
            extra={
                "request_id": request_id,
                "tenant_key": claims.tenant_key,
                "impersonator_id": claims.impersonator_id,
                "target_user_id": claims.subject,
                "session_id": claims.session_id,
                "outcome": "success",
            },
        )
        return EndImpersonationResponse(
            message="Impersonation session ended.",
            impersonator_user_id=claims.impersonator_id,
        )

    def get_impersonation_status(self, claims: AccessTokenClaims) -> ImpersonationStatusResponse:
        if not claims.is_impersonation:
            return ImpersonationStatusResponse(is_impersonating=False)
        return ImpersonationStatusResponse(
            is_impersonating=True,
            impersonator_id=claims.impersonator_id,
            target_user_id=claims.subject,
            session_id=claims.session_id,
            expires_at=claims.expires_at.isoformat(),
        )
