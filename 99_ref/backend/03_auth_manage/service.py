from __future__ import annotations

from datetime import UTC, datetime, timedelta
from importlib import import_module
import hashlib
import hmac
import secrets
from uuid import uuid4

import asyncpg
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .constants import AccountType, AuditEventCategory, AuditEventType, BEARER_TOKEN_TYPE
from .models import AccessTokenClaims, AuthenticatedUser
from .repository import AuthRepository
from .schemas import (
    AuthUserResponse,
    BatchSetUserPropertiesResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginRequest,
    LogoutRequest,
    PropertyKeyListResponse,
    PropertyKeyResponse,
    RefreshRequest,
    RegisterResponse,
    RegistrationRequest,
    RequestEmailVerificationResponse,
    RequestOTPResponse,
    ResetPasswordRequest,
    TokenPairResponse,
    UserAccountListResponse,
    UserAccountResponse,
    UserPropertyListResponse,
    UserPropertyResponse,
    VerifyEmailRequest,
    VerifyOTPRequest,
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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
AuthenticationError = _errors_module.AuthenticationError
AuthorizationError = _errors_module.AuthorizationError
AuthFeatureDisabledError = _errors_module.AuthFeatureDisabledError
ConflictError = _errors_module.ConflictError
RateLimitError = _errors_module.RateLimitError
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
JWTCodec = _jwt_module.JWTCodec
KeyStore = _jwt_module.KeyStore
JTIBlocklist = _jwt_module.JTIBlocklist
RefreshTokenManager = _refresh_module.RefreshTokenManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
record_auth_event = _telemetry_module.record_auth_event
utc_now_sql = import_module("backend.01_core.time_utils").utc_now_sql


@instrument_class_methods(namespace="auth.service", logger_name="backend.auth.instrumentation")
class AuthService:
    _CACHE_TTL_PROFILE = 300  # 5 minutes
    _CACHE_TTL_PROPERTIES = 300
    _CACHE_TTL_ACCOUNTS = 600  # 10 minutes
    _CACHE_TTL_PROPERTY_KEYS = 600  # 10 minutes

    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AuthRepository()
        self._password_hasher = PasswordHasher()
        self._dummy_password_hash = self._password_hasher.hash("kcontrol-auth-dummy-password")
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
        self._logger = get_logger("backend.auth")

    @staticmethod
    def _normalize_portal_mode(value: str | None) -> str | None:
        if not value:
            return None
        normalized = value.strip().lower()
        return normalized or None

    async def _invalidate_user_cache(self, user_id: str) -> None:
        await self._cache.delete_pattern(f"user:{user_id}:*")

    # ── Registration ─────────────────────────────────────────────────────

    async def register_user(
        self,
        payload: RegistrationRequest,
        *,
        client_ip: str | None,
        user_agent: str | None,
        request_id: str | None,
    ) -> RegisterResponse:
        del user_agent
        self._ensure_feature_enabled()
        now = utc_now_sql()
        tenant_key = self._settings.default_tenant_key
        email = payload.email.strip().lower()
        username = payload.username.strip().lower() if payload.username else None
        password_hash = self._password_hasher.hash(payload.password)

        try:
            async with self._database_pool.transaction() as connection:
                user_id, _ = await self._repository.create_user(
                    connection,
                    tenant_key=tenant_key,
                    now=now,
                    created_by=None,
                )
                # User properties (EAV)
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="email",
                    property_value=email, created_by=user_id, now=now,
                )
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="email_verified",
                    property_value="false", created_by=user_id, now=now,
                )
                if username is not None:
                    await self._repository.create_user_property(
                        connection, user_id=user_id, property_key="username",
                        property_value=username, created_by=user_id, now=now,
                    )
                # Account (local_password)
                account_id = await self._repository.create_user_account(
                    connection,
                    user_id=user_id,
                    tenant_key=tenant_key,
                    account_type_code=AccountType.LOCAL_PASSWORD.value,
                    is_primary=True,
                    created_by=user_id,
                    now=now,
                )
                await self._repository.create_user_account_property(
                    connection, user_account_id=account_id,
                    property_key="password_hash", property_value=password_hash, now=now,
                )
                await self._repository.create_user_account_property(
                    connection, user_account_id=account_id,
                    property_key="password_version", property_value="1", now=now,
                )
                await self._repository.create_user_account_property(
                    connection, user_account_id=account_id,
                    property_key="password_changed_at", property_value=str(now), now=now,
                )
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="user",
                        entity_id=user_id,
                        event_type=AuditEventType.REGISTERED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        ip_address=client_ip,
                        properties={
                            "email": email,
                            "username": username,
                            "account_status": "pending_verification",
                            "account_type": AccountType.LOCAL_PASSWORD.value,
                        },
                    ),
                )
                # Auto-enroll in default_users group (grants basic onboarding permissions)
                await self._repository.add_user_to_default_group(
                    connection, user_id=user_id, tenant_key=tenant_key, now=now,
                )
                # Auto-accept pending invitations for this email
                await self._process_registration_invites(
                    connection, email=email, user_id=user_id,
                    tenant_key=tenant_key, now=now,
                )
        except asyncpg.UniqueViolationError as exc:
            raise ConflictError("Email or username is already in use.") from exc

        record_auth_event("register", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_registration_succeeded",
            extra={"request_id": request_id, "tenant_key": tenant_key, "user_id": user_id, "outcome": "success"},
        )
        return RegisterResponse(
            user_id=user_id,
            email=email,
            username=username,
            tenant_key=tenant_key,
            email_verified=False,
        )

    # ── Authentication ───────────────────────────────────────────────────

    async def authenticate_user(
        self,
        payload: LoginRequest,
        *,
        client_ip: str | None,
        user_agent: str | None,
        request_id: str | None,
    ) -> TokenPairResponse:
        self._ensure_feature_enabled()
        now = utc_now_sql()
        tenant_key = self._settings.default_tenant_key
        identity_type, normalized_login = self._classify_login(payload.login)
        failure_message: str | None = None
        user_record = None
        refresh_token = ""
        access_token = None
        session_id = ""

        async with self._database_pool.transaction() as connection:
            failed_attempts = await self._repository.count_recent_failed_attempts(
                connection,
                tenant_key=tenant_key,
                normalized_identifier=normalized_login,
                window_seconds=self._settings.brute_force_window_seconds,
                now=now,
            )
            if failed_attempts >= self._settings.brute_force_max_attempts:
                raise RateLimitError()

            user_record = await self._repository.find_user_by_identity(
                connection,
                tenant_key=tenant_key,
                normalized_value=normalized_login,
                identity_type_code=identity_type,
            )
            if user_record is None:
                self._verify_dummy_password(payload.password)
                await self._record_failure(
                    connection,
                    tenant_key=tenant_key,
                    normalized_login=normalized_login,
                    identity_type=identity_type,
                    user_id=None,
                    client_ip=client_ip,
                    now=now,
                )
                failure_message = "Invalid credentials."

            if user_record is not None and failure_message is None:
                try:
                    self._password_hasher.verify(user_record.password_hash, payload.password)
                except VerifyMismatchError:
                    await self._record_failure(
                        connection,
                        tenant_key=tenant_key,
                        normalized_login=normalized_login,
                        identity_type=identity_type,
                        user_id=user_record.user_id,
                        client_ip=client_ip,
                        now=now,
                    )
                    failure_message = "Invalid credentials."

            if failure_message is None and user_record is not None:
                refresh_expires_at = now + timedelta(seconds=self._settings.refresh_token_ttl_seconds)
                session_id = await self._repository.create_session(
                    connection,
                    user_id=user_record.user_id,
                    tenant_key=tenant_key,
                    refresh_token_hash="pending",
                    refresh_expires_at=refresh_expires_at,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    now=now,
                )
                refresh_token = self._refresh_tokens.generate(session_id)
                refresh_parts = self._refresh_tokens.parse(refresh_token)
                await self._repository.rotate_session(
                    connection,
                    session_id=session_id,
                    new_refresh_token_hash=self._refresh_tokens.hash_secret(refresh_parts.secret),
                    now=now,
                )
                await self._repository.record_login_attempt(
                    connection,
                    tenant_key=tenant_key,
                    normalized_identifier=normalized_login,
                    identity_type_code=identity_type,
                    user_id=user_record.user_id,
                    outcome="success",
                    failure_reason=None,
                    client_ip=client_ip,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="session",
                        entity_id=session_id,
                        event_type=AuditEventType.LOGIN_SUCCEEDED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=user_record.user_id,
                        actor_type="user",
                        ip_address=client_ip,
                        session_id=session_id,
                        properties={"rotation_counter": "1"},
                    ),
                )
                access_token = self._jwt_codec.encode_access_token(
                    subject=user_record.user_id,
                    session_id=session_id,
                    tenant_key=tenant_key,
                )

        if failure_message is not None:
            raise AuthenticationError(failure_message)

        record_auth_event("login", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_login_succeeded",
            extra={"request_id": request_id, "tenant_key": tenant_key, "user_id": user_record.user_id, "session_id": session_id, "outcome": "success"},
        )
        return TokenPairResponse(
            access_token=access_token.token,
            token_type=BEARER_TOKEN_TYPE,
            expires_in=self._settings.access_token_ttl_seconds,
            refresh_token=refresh_token,
            refresh_expires_in=self._settings.refresh_token_ttl_seconds,
            user=AuthUserResponse(
                user_id=user_record.user_id,
                tenant_key=user_record.tenant_key,
                email=user_record.email,
                username=user_record.username,
                email_verified=user_record.email_verified,
                account_status=user_record.account_status,
            ),
        )

    # ── Google OAuth ────────────────────────────────────────────────────

    async def authenticate_google(
        self,
        *,
        id_token: str,
        client_ip: str | None,
        user_agent: str | None,
        request_id: str | None,
    ) -> TokenPairResponse:
        """Authenticate via Google ID token. Links to existing user by email or creates new user."""
        from google.oauth2 import id_token as google_id_token_module
        from google.auth.transport import requests as google_requests

        client_id = self._settings.google_oauth_client_id
        if not client_id:
            raise AuthFeatureDisabledError("Google OAuth is not configured.")

        # Verify the Google ID token
        try:
            idinfo = google_id_token_module.verify_oauth2_token(
                id_token,
                google_requests.Request(),
                client_id,
            )
        except Exception as exc:
            self._logger.warning(
                "google_token_verification_failed",
                extra={"request_id": request_id, "error": str(exc)},
            )
            raise AuthenticationError("Invalid Google token.") from exc

        google_id = idinfo.get("sub")
        email = (idinfo.get("email") or "").strip().lower()
        if not google_id or not email:
            raise AuthenticationError("Google token missing required claims.")

        if not idinfo.get("email_verified", False):
            raise AuthenticationError("Google email is not verified.")

        now = utc_now_sql()
        tenant_key = self._settings.default_tenant_key

        async with self._database_pool.transaction() as connection:
            # 1. Try to find existing user by google_id
            existing_user = await self._repository.find_user_by_google_id(
                connection, tenant_key=tenant_key, google_id=google_id,
            )
            if existing_user is not None:
                return await self._create_google_session(
                    connection,
                    user_id=existing_user.user_id,
                    tenant_key=existing_user.tenant_key,
                    email=existing_user.email,
                    username=existing_user.username,
                    email_verified=existing_user.email_verified,
                    account_status=existing_user.account_status,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    request_id=request_id,
                    now=now,
                )

            # 2. Try to find existing user by email and link the google account
            email_user = await self._repository.find_user_by_email_for_magic_link(
                connection, tenant_key=tenant_key, email=email,
            )
            if email_user is not None:
                if not email_user.is_active or email_user.is_disabled or email_user.is_locked:
                    raise AuthenticationError("Account is inactive or locked.")
                # Link Google account to this existing user
                google_acct_id = await self._repository.find_google_account_for_user(
                    connection, user_id=email_user.user_id,
                )
                if google_acct_id is None:
                    google_acct_id = await self._repository.create_user_account(
                        connection,
                        user_id=email_user.user_id,
                        tenant_key=tenant_key,
                        account_type_code=AccountType.GOOGLE.value,
                        is_primary=False,
                        created_by=email_user.user_id,
                        now=now,
                    )
                    await self._repository.create_user_account_property(
                        connection, user_account_id=google_acct_id,
                        property_key="google_id", property_value=google_id, now=now,
                    )
                    await self._repository.create_user_account_property(
                        connection, user_account_id=google_acct_id,
                        property_key="google_email", property_value=email, now=now,
                    )
                    await self._audit_writer.write_entry(
                        connection,
                        AuditEntry(
                            id=str(uuid4()),
                            tenant_key=tenant_key,
                            entity_type="user",
                            entity_id=email_user.user_id,
                            event_type=AuditEventType.ACCOUNT_LINKED.value,
                            event_category=AuditEventCategory.AUTH.value,
                            occurred_at=now,
                            actor_id=email_user.user_id,
                            actor_type="user",
                            ip_address=client_ip,
                            properties={
                                "account_type": AccountType.GOOGLE.value,
                                "google_id": google_id,
                            },
                        ),
                    )
                # Mark email as verified if it wasn't already
                if not email_user.email_verified:
                    await self._repository.upsert_user_property(
                        connection, user_id=email_user.user_id,
                        property_key="email_verified", property_value="true",
                        updated_by=email_user.user_id, now=now,
                    )
                return await self._create_google_session(
                    connection,
                    user_id=email_user.user_id,
                    tenant_key=email_user.tenant_key,
                    email=email_user.email,
                    username=email_user.username,
                    email_verified=True,
                    account_status=email_user.account_status,
                    client_ip=client_ip,
                    user_agent=user_agent,
                    request_id=request_id,
                    now=now,
                )

            # 3. No existing user — create a new one
            user_id, _ = await self._repository.create_user(
                connection, tenant_key=tenant_key, now=now, created_by=None,
            )
            await self._repository.create_user_property(
                connection, user_id=user_id, property_key="email",
                property_value=email, created_by=user_id, now=now,
            )
            await self._repository.create_user_property(
                connection, user_id=user_id, property_key="email_verified",
                property_value="true", created_by=user_id, now=now,
            )
            # Set display_name from Google profile if available
            display_name = idinfo.get("name", "")
            if display_name:
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="display_name",
                    property_value=display_name, created_by=user_id, now=now,
                )
            avatar_url = idinfo.get("picture", "")
            if avatar_url:
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="avatar_url",
                    property_value=avatar_url, created_by=user_id, now=now,
                )
            # Create Google account
            google_acct_id = await self._repository.create_user_account(
                connection,
                user_id=user_id,
                tenant_key=tenant_key,
                account_type_code=AccountType.GOOGLE.value,
                is_primary=True,
                created_by=user_id,
                now=now,
            )
            await self._repository.create_user_account_property(
                connection, user_account_id=google_acct_id,
                property_key="google_id", property_value=google_id, now=now,
            )
            await self._repository.create_user_account_property(
                connection, user_account_id=google_acct_id,
                property_key="google_email", property_value=email, now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="user",
                    entity_id=user_id,
                    event_type=AuditEventType.REGISTERED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={
                        "email": email,
                        "account_type": AccountType.GOOGLE.value,
                        "account_status": "pending_verification",
                    },
                ),
            )
            await self._repository.add_user_to_default_group(
                connection, user_id=user_id, tenant_key=tenant_key, now=now,
            )
            await self._process_registration_invites(
                connection, email=email, user_id=user_id,
                tenant_key=tenant_key, now=now,
            )
            return await self._create_google_session(
                connection,
                user_id=user_id,
                tenant_key=tenant_key,
                email=email,
                username=None,
                email_verified=True,
                account_status="pending_verification",
                client_ip=client_ip,
                user_agent=user_agent,
                request_id=request_id,
                now=now,
                is_new_user=True,
            )

    async def _create_google_session(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        tenant_key: str,
        email: str,
        username: str | None,
        email_verified: bool,
        account_status: str,
        client_ip: str | None,
        user_agent: str | None,
        request_id: str | None,
        now: datetime,
        is_new_user: bool = False,
    ) -> TokenPairResponse:
        """Create a session + JWT for a Google-authenticated user (shared helper)."""
        refresh_expires_at = now + timedelta(seconds=self._settings.refresh_token_ttl_seconds)
        session_id = await self._repository.create_session(
            connection,
            user_id=user_id,
            tenant_key=tenant_key,
            refresh_token_hash="pending",
            refresh_expires_at=refresh_expires_at,
            client_ip=client_ip,
            user_agent=user_agent,
            now=now,
        )
        refresh_token = self._refresh_tokens.generate(session_id)
        refresh_parts = self._refresh_tokens.parse(refresh_token)
        await self._repository.rotate_session(
            connection,
            session_id=session_id,
            new_refresh_token_hash=self._refresh_tokens.hash_secret(refresh_parts.secret),
            now=now,
        )
        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="session",
                entity_id=session_id,
                event_type=AuditEventType.LOGIN_SUCCEEDED.value,
                event_category=AuditEventCategory.AUTH.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                ip_address=client_ip,
                session_id=session_id,
                properties={"auth_method": "google", "rotation_counter": "1"},
            ),
        )
        access_token = self._jwt_codec.encode_access_token(
            subject=user_id,
            session_id=session_id,
            tenant_key=tenant_key,
        )

        record_auth_event("login", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_google_login_succeeded",
            extra={
                "request_id": request_id,
                "tenant_key": tenant_key,
                "user_id": user_id,
                "session_id": session_id,
                "auth_method": "google",
                "is_new_user": is_new_user,
            },
        )
        return TokenPairResponse(
            access_token=access_token.token,
            token_type=BEARER_TOKEN_TYPE,
            expires_in=self._settings.access_token_ttl_seconds,
            refresh_token=refresh_token,
            refresh_expires_in=self._settings.refresh_token_ttl_seconds,
            user=AuthUserResponse(
                user_id=user_id,
                tenant_key=tenant_key,
                email=email,
                username=username,
                email_verified=email_verified,
                account_status=account_status,
                is_new_user=is_new_user,
            ),
        )

    # ── Password reset ───────────────────────────────────────────────────

    async def request_password_reset(
        self,
        payload: ForgotPasswordRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> ForgotPasswordResponse:
        self._ensure_feature_enabled()
        now = utc_now_sql()
        tenant_key = self._settings.default_tenant_key
        identity_type, normalized_login = self._classify_login(payload.login)
        reset_token: str | None = None
        user_record = None

        async with self._database_pool.transaction() as connection:
            user_record = await self._repository.find_user_by_identity(
                connection,
                tenant_key=tenant_key,
                normalized_value=normalized_login,
                identity_type_code=identity_type,
            )
            if user_record is not None:
                await self._repository.expire_active_password_reset_challenges(
                    connection,
                    user_id=user_record.user_id,
                    tenant_key=tenant_key,
                    now=now,
                )
                reset_token = self._refresh_tokens.generate(str(uuid4()))
                reset_parts = self._refresh_tokens.parse(reset_token)
                challenge_id = await self._repository.create_password_reset_challenge(
                    connection,
                    user_id=user_record.user_id,
                    tenant_key=tenant_key,
                    target_value=user_record.email,
                    secret_hash=self._refresh_tokens.hash_secret(reset_parts.secret),
                    expires_at=now + timedelta(minutes=self._settings.password_reset_expiry_minutes),
                    client_ip=client_ip,
                    now=now,
                )
                reset_token = f"{challenge_id}.{reset_parts.secret}"
                # Build reset URL the same way magic-link does (_build_magic_link_url):
                # prefer the dedicated setting, otherwise construct {platform_base_url}/reset-password.
                _reset_base = getattr(self._settings, "password_reset_frontend_url", "").rstrip("/")
                if not _reset_base:
                    _platform = getattr(self._settings, "platform_base_url", "").rstrip("/")
                    if _platform:
                        _reset_base = f"{_platform}/reset-password"
                _reset_url = f"{_reset_base}?token={reset_token}" if _reset_base else ""
                _expiry_label = f"{self._settings.password_reset_expiry_minutes} minutes"
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="challenge",
                        entity_id=challenge_id,
                        event_type=AuditEventType.PASSWORD_RESET_REQUESTED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=user_record.user_id,
                        actor_type="user",
                        ip_address=client_ip,
                        properties={
                            "target": user_record.email,
                            "reset.url": _reset_url,
                            "reset.expires_in": _expiry_label,
                            "event.ip_address": client_ip or "",
                        },
                    ),
                )

        record_auth_event("password_reset_request", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_password_reset_requested",
            extra={"request_id": request_id, "tenant_key": tenant_key, "outcome": "accepted"},
        )

        # Send password reset email via notification system (best-effort — never blocks auth flow)
        if reset_token is not None and user_record is not None and getattr(self._settings, "notification_enabled", False):
            try:
                _dispatcher_module = import_module("backend.04_notifications.02_dispatcher.dispatcher")
                NotificationDispatcher = _dispatcher_module.NotificationDispatcher
                dispatcher = NotificationDispatcher(
                    database_pool=self._database_pool,
                    settings=self._settings,
                )
                challenge_id_for_key = reset_token.split(".")[0] if reset_token else "unknown"
                _reset_audit_entry = AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="challenge",
                    entity_id=challenge_id_for_key,
                    event_type=AuditEventType.PASSWORD_RESET_REQUESTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_record.user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={
                        "target": user_record.email,
                        "reset.url": _reset_url,
                        "reset.expires_in": _expiry_label,
                        "event.ip_address": client_ip or "",
                    },
                )
                import asyncio as _asyncio
                _asyncio.create_task(dispatcher.dispatch_transactional(
                    audit_entry=_reset_audit_entry,
                    recipient_user_id=user_record.user_id,
                    template_code="password_reset_email",
                    notification_type_code="password_reset",
                    tenant_key=tenant_key,
                    idempotency_key=f"password_reset:{challenge_id_for_key}:email",
                    priority_code="critical",
                ))
            except Exception as _exc:
                self._logger.warning(
                    "auth_password_reset_email_failed",
                    extra={"reason": str(_exc)},
                )

        if self._settings.environment in {"local", "test", "development", "dev"}:
            return ForgotPasswordResponse(
                message="If the account exists, password reset instructions have been created.",
                reset_token=reset_token,
            )
        return ForgotPasswordResponse(
            message="If the account exists, password reset instructions have been created.",
            reset_token=None,
        )

    async def reset_password(
        self,
        payload: ResetPasswordRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> dict[str, str]:
        self._ensure_feature_enabled()
        now = utc_now_sql()
        now_aware = now.replace(tzinfo=UTC)
        reset_parts = self._refresh_tokens.parse(payload.reset_token)
        provided_hash = self._refresh_tokens.hash_secret(reset_parts.secret)
        new_password_hash = self._password_hasher.hash(payload.new_password)

        async with self._database_pool.transaction() as connection:
            challenge = await self._repository.get_password_reset_challenge(connection, challenge_id=reset_parts.session_id)
            if challenge is None or challenge.user_id is None or challenge.consumed_at is not None:
                raise AuthenticationError("Reset token is invalid.")
            if challenge.expires_at <= now_aware:
                raise AuthenticationError("Reset token is invalid.")
            if not hmac.compare_digest(challenge.secret_hash, provided_hash):
                raise AuthenticationError("Reset token is invalid.")
            await self._repository.update_password_credential(
                connection,
                user_id=challenge.user_id,
                tenant_key=challenge.tenant_key,
                new_password_hash=new_password_hash,
                now=now,
            )
            await self._repository.consume_password_reset_challenge(
                connection,
                challenge_id=challenge.challenge_id,
                now=now,
            )
            await self._repository.revoke_active_sessions_for_user(
                connection,
                user_id=challenge.user_id,
                reason="password_reset",
                now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=challenge.tenant_key,
                    entity_type="user",
                    entity_id=challenge.user_id,
                    event_type=AuditEventType.PASSWORD_RESET_COMPLETED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=challenge.user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={"password_reset": "true"},
                ),
            )

        record_auth_event("password_reset_complete", outcome="success", tenant_key=challenge.tenant_key)
        self._logger.info(
            "auth_password_reset_completed",
            extra={"request_id": request_id, "tenant_key": challenge.tenant_key, "user_id": challenge.user_id, "outcome": "success"},
        )
        return {"message": "Password reset completed."}

    # ── Email verification ─────────────────────────────────────────────

    async def request_email_verification(
        self,
        claims: AccessTokenClaims,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> RequestEmailVerificationResponse:
        self._ensure_feature_enabled()
        if claims.is_impersonation:
            raise AuthorizationError("Cannot request email verification during impersonation.")

        now = utc_now_sql()
        tenant_key = claims.tenant_key
        user_id = claims.subject
        verification_token: str | None = None

        async with self._database_pool.transaction() as connection:
            email_prop = await self._repository.get_user_property(
                connection, user_id=user_id, property_key="email",
            )
            if email_prop is None:
                raise NotFoundError("No email address found for this account.")

            ev_prop = await self._repository.get_user_property(
                connection, user_id=user_id, property_key="email_verified",
            )
            if ev_prop is not None and ev_prop.property_value == "true":
                return RequestEmailVerificationResponse(
                    message="Email is already verified.",
                )

            await self._repository.expire_active_email_verification_challenges(
                connection,
                user_id=user_id,
                tenant_key=tenant_key,
                now=now,
            )

            raw_token = self._refresh_tokens.generate(str(uuid4()))
            token_parts = self._refresh_tokens.parse(raw_token)
            challenge_id = await self._repository.create_email_verification_challenge(
                connection,
                user_id=user_id,
                tenant_key=tenant_key,
                target_value=email_prop.property_value,
                secret_hash=self._refresh_tokens.hash_secret(token_parts.secret),
                expires_at=now + timedelta(minutes=30),
                client_ip=client_ip,
                now=now,
            )
            verification_token = f"{challenge_id}.{token_parts.secret}"

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="challenge",
                    entity_id=challenge_id,
                    event_type=AuditEventType.EMAIL_VERIFICATION_REQUESTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={"target": email_prop.property_value},
                ),
            )

        record_auth_event("email_verification_request", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_email_verification_requested",
            extra={"request_id": request_id, "tenant_key": tenant_key, "user_id": user_id, "outcome": "accepted"},
        )
        if self._settings.environment in {"local", "test", "development", "dev"}:
            return RequestEmailVerificationResponse(
                message="Verification email has been sent.",
                verification_token=verification_token,
            )
        return RequestEmailVerificationResponse(
            message="Verification email has been sent.",
            verification_token=None,
        )

    async def verify_email(
        self,
        payload: VerifyEmailRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> dict[str, str]:
        self._ensure_feature_enabled()
        now = utc_now_sql()
        now_aware = now.replace(tzinfo=UTC)
        token_parts = self._refresh_tokens.parse(payload.verification_token)
        provided_hash = self._refresh_tokens.hash_secret(token_parts.secret)

        async with self._database_pool.transaction() as connection:
            challenge = await self._repository.get_email_verification_challenge(
                connection, challenge_id=token_parts.session_id,
            )
            if challenge is None or challenge.user_id is None or challenge.consumed_at is not None:
                raise AuthenticationError("Verification token is invalid.")
            if challenge.expires_at <= now_aware:
                raise AuthenticationError("Verification token is invalid.")
            if not hmac.compare_digest(challenge.secret_hash, provided_hash):
                raise AuthenticationError("Verification token is invalid.")

            await self._repository.consume_password_reset_challenge(
                connection,
                challenge_id=challenge.challenge_id,
                now=now,
            )

            await self._repository.upsert_user_property(
                connection,
                user_id=challenge.user_id,
                property_key="email_verified",
                property_value="true",
                updated_by=challenge.user_id,
                now=now,
            )

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=challenge.tenant_key,
                    entity_type="user",
                    entity_id=challenge.user_id,
                    event_type=AuditEventType.EMAIL_VERIFICATION_COMPLETED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=challenge.user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={"email_verified": "true"},
                ),
            )

        await self._invalidate_user_cache(challenge.user_id)
        record_auth_event("email_verification_complete", outcome="success", tenant_key=challenge.tenant_key)
        self._logger.info(
            "auth_email_verification_completed",
            extra={"request_id": request_id, "tenant_key": challenge.tenant_key, "user_id": challenge.user_id, "outcome": "success"},
        )
        return {"message": "Email verified."}

    # ── OTP verification ────────────────────────────────────────────────

    @staticmethod
    def _generate_otp(length: int = 6) -> str:
        """Generate a cryptographically secure numeric OTP."""
        return "".join(str(secrets.randbelow(10)) for _ in range(length))

    @staticmethod
    def _hash_otp(otp: str) -> str:
        return hashlib.sha256(otp.encode()).hexdigest()

    async def request_otp(
        self,
        claims: AccessTokenClaims,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> RequestOTPResponse:
        """Generate a 6-digit OTP, store it as a challenge, and dispatch notification."""
        self._ensure_feature_enabled()
        if claims.is_impersonation:
            raise AuthorizationError("Cannot request OTP during impersonation.")

        now = utc_now_sql()
        tenant_key = claims.tenant_key
        user_id = claims.subject
        otp_code = self._generate_otp()
        otp_hash = self._hash_otp(otp_code)
        expiry_minutes = self._settings.otp_expiry_minutes

        async with self._database_pool.transaction() as connection:
            email_prop = await self._repository.get_user_property(
                connection, user_id=user_id, property_key="email",
            )
            if email_prop is None:
                raise NotFoundError("No email address found for this account.")

            # Check if already verified
            ev_prop = await self._repository.get_user_property(
                connection, user_id=user_id, property_key="email_verified",
            )
            if ev_prop is not None and ev_prop.property_value == "true":
                otp_prop = await self._repository.get_user_property(
                    connection, user_id=user_id, property_key="otp_verified",
                )
                if otp_prop is not None and otp_prop.property_value == "true":
                    return RequestOTPResponse(message="Email is already verified.")

            # Enforce 10 OTP requests per user per day
            _otp_count_today = await connection.fetchval(
                f"""
                SELECT COUNT(*) FROM "03_auth_manage"."12_trx_auth_challenges"
                WHERE user_id = $1
                  AND tenant_key = $2
                  AND challenge_type_code = 'email_verification'
                  AND created_at >= NOW() - INTERVAL '24 hours'
                """,
                user_id,
                tenant_key,
            )
            if _otp_count_today >= 10:
                raise RateLimitError("Too many OTP requests. Please try again later.")

            # Expire any active email_verification challenges
            await self._repository.expire_active_email_verification_challenges(
                connection, user_id=user_id, tenant_key=tenant_key, now=now,
            )

            # Store OTP hash as secret_hash in the challenge table
            challenge_id = await self._repository.create_email_verification_challenge(
                connection,
                user_id=user_id,
                tenant_key=tenant_key,
                target_value=email_prop.property_value,
                secret_hash=otp_hash,
                expires_at=now + timedelta(minutes=expiry_minutes),
                client_ip=client_ip,
                now=now,
            )

            # Build audit entry once — reused for both audit log and notification dispatch
            _otp_audit_entry = AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="challenge",
                entity_id=challenge_id,
                event_type=AuditEventType.EMAIL_VERIFICATION_REQUESTED.value,
                event_category=AuditEventCategory.AUTH.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                ip_address=client_ip,
                properties={
                    "target": email_prop.property_value,
                    "otp_code": otp_code,
                    "method": "otp",
                },
            )
            await self._audit_writer.write_entry(connection, _otp_audit_entry)

        record_auth_event("otp_request", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_otp_requested",
            extra={"request_id": request_id, "tenant_key": tenant_key, "user_id": user_id},
        )

        # Dispatch OTP email via notification system (best-effort, never blocks auth flow)
        if self._settings.notification_enabled:
            try:
                _dispatcher_module = import_module("backend.04_notifications.02_dispatcher.dispatcher")
                dispatcher = _dispatcher_module.NotificationDispatcher(
                    database_pool=self._database_pool, settings=self._settings,
                )

                async def _dispatch_otp() -> None:
                    try:
                        nid = await dispatcher.dispatch_transactional(
                            audit_entry=_otp_audit_entry,
                            recipient_user_id=user_id,
                            template_code="otp_verification_email",
                            notification_type_code="email_verification",
                            tenant_key=tenant_key,
                            idempotency_key=f"otp:{challenge_id}:email",
                            priority_code="critical",
                        )
                        self._logger.info("otp_notification_queued", extra={"notification_id": nid})
                    except Exception:
                        self._logger.warning("otp_notification_dispatch_failed_async", exc_info=True)

                import asyncio as _asyncio
                _asyncio.create_task(_dispatch_otp())
            except Exception:
                self._logger.warning("otp_notification_dispatch_setup_failed", exc_info=True)

        # In dev environments, return the OTP for testing convenience
        if self._settings.environment in {"local", "test", "development", "dev"}:
            return RequestOTPResponse(
                message="OTP has been sent to your email.",
                otp_code=otp_code,
            )
        return RequestOTPResponse(message="OTP has been sent to your email.")

    async def verify_otp(
        self,
        claims: AccessTokenClaims,
        payload: VerifyOTPRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> dict[str, str]:
        """Verify a 6-digit OTP code against the stored challenge."""
        self._ensure_feature_enabled()
        now = utc_now_sql()
        now_aware = now.replace(tzinfo=UTC)
        user_id = claims.subject
        tenant_key = claims.tenant_key
        otp_hash = self._hash_otp(payload.otp_code)

        async with self._database_pool.transaction() as connection:
            # Find the latest unconsumed email_verification challenge for this user
            row = await connection.fetchrow(
                f"""
                SELECT id, user_id, tenant_key, target_value, secret_hash, expires_at, consumed_at
                FROM "03_auth_manage"."12_trx_auth_challenges"
                WHERE user_id = $1
                  AND tenant_key = $2
                  AND challenge_type_code = 'email_verification'
                  AND consumed_at IS NULL
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id,
                tenant_key,
            )
            if row is None:
                raise AuthenticationError("No active OTP found. Please request a new one.")

            from_ts = import_module("backend.01_core.time_utils").from_sql_timestamp
            expires_at = from_ts(row["expires_at"])
            if expires_at <= now_aware:
                raise AuthenticationError("OTP has expired. Please request a new one.")

            if not hmac.compare_digest(row["secret_hash"], otp_hash):
                # Track failed attempt — lock after 5 failures
                _fail_count = await connection.fetchval(
                    f"""
                    SELECT COUNT(*) FROM "03_auth_manage"."40_aud_events"
                    WHERE entity_id = $1
                      AND event_type = 'otp_verify_failed'
                      AND occurred_at >= NOW() - INTERVAL '30 minutes'
                    """,
                    str(row["id"]),
                )
                if _fail_count >= 4:
                    # Consume the challenge so it can't be tried again
                    await self._repository.consume_password_reset_challenge(
                        connection, challenge_id=str(row["id"]), now=now,
                    )
                    raise AuthenticationError("Too many failed attempts. Please request a new OTP.")
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()), tenant_key=tenant_key,
                        entity_type="challenge", entity_id=str(row["id"]),
                        event_type="otp_verify_failed",
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now, actor_id=user_id, actor_type="user",
                        ip_address=client_ip, properties={"attempt": str(_fail_count + 1)},
                    ),
                )
                raise AuthenticationError("Invalid OTP code.")

            # Consume the challenge
            await self._repository.consume_password_reset_challenge(
                connection, challenge_id=str(row["id"]), now=now,
            )

            # Mark email as verified
            await self._repository.upsert_user_property(
                connection, user_id=user_id, property_key="email_verified",
                property_value="true", updated_by=user_id, now=now,
            )
            # Mark OTP as verified
            await self._repository.upsert_user_property(
                connection, user_id=user_id, property_key="otp_verified",
                property_value="true", updated_by=user_id, now=now,
            )

            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="user",
                    entity_id=user_id,
                    event_type=AuditEventType.EMAIL_VERIFICATION_COMPLETED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={"email_verified": "true", "otp_verified": "true", "method": "otp"},
                ),
            )

        await self._invalidate_user_cache(user_id)
        record_auth_event("otp_verify", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_otp_verified",
            extra={"request_id": request_id, "tenant_key": tenant_key, "user_id": user_id},
        )
        return {"message": "OTP verified. Email confirmed."}

    # ── Refresh ──────────────────────────────────────────────────────────

    async def refresh_session(
        self,
        payload: RefreshRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> TokenPairResponse:
        self._ensure_feature_enabled()
        now = utc_now_sql()
        now_aware = now.replace(tzinfo=UTC)
        refresh_parts = self._refresh_tokens.parse(payload.refresh_token)
        provided_hash = self._refresh_tokens.hash_secret(refresh_parts.secret)
        invalid_refresh = False
        session_record = None
        new_refresh_token = ""
        access_token = None

        async with self._database_pool.transaction() as connection:
            session_record = await self._repository.get_session_by_id(connection, session_id=refresh_parts.session_id)
            if session_record is None or session_record.revoked_at is not None:
                raise AuthenticationError("Refresh token is invalid.")
            if session_record.refresh_token_expires_at <= now_aware:
                await self._repository.revoke_session(connection, session_id=session_record.session_id, reason="expired", now=now)
                invalid_refresh = True
            if not hmac.compare_digest(session_record.refresh_token_hash, provided_hash):
                await self._repository.revoke_session(
                    connection,
                    session_id=session_record.session_id,
                    reason="refresh_reuse_detected",
                    now=now,
                )
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=session_record.tenant_key,
                        entity_type="session",
                        entity_id=session_record.session_id,
                        event_type=AuditEventType.REFRESH_REPLAY_DETECTED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        ip_address=client_ip,
                        session_id=session_record.session_id,
                        properties={"revoked": "true"},
                    ),
                )
                record_auth_event("refresh", outcome="replay_detected", tenant_key=session_record.tenant_key)
                invalid_refresh = True

            if not invalid_refresh:
                new_refresh_token = self._refresh_tokens.generate(session_record.session_id)
                new_parts = self._refresh_tokens.parse(new_refresh_token)
                await self._repository.rotate_session(
                    connection,
                    session_id=session_record.session_id,
                    new_refresh_token_hash=self._refresh_tokens.hash_secret(new_parts.secret),
                    now=now,
                )
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=session_record.tenant_key,
                        entity_type="session",
                        entity_id=session_record.session_id,
                        event_type=AuditEventType.REFRESH_SUCCEEDED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=session_record.user_id,
                        actor_type="user",
                        ip_address=client_ip,
                        session_id=session_record.session_id,
                        properties={
                            "previous_rotation_counter": str(session_record.rotation_counter),
                            "new_rotation_counter": str(session_record.rotation_counter + 1),
                        },
                    ),
                )
                record_auth_event("refresh", outcome="success", tenant_key=session_record.tenant_key)
                # Carry impersonation claims through token rotation
                extra_claims: dict[str, object] | None = None
                if session_record.is_impersonation and session_record.impersonator_user_id:
                    extra_claims = {
                        "imp": True,
                        "imp_sub": session_record.impersonator_user_id,
                        "imp_sid": session_record.session_id,
                    }
                if session_record.portal_mode:
                    if extra_claims is None:
                        extra_claims = {}
                    extra_claims["portal_mode"] = session_record.portal_mode
                access_token = self._jwt_codec.encode_access_token(
                    subject=session_record.user_id,
                    session_id=session_record.session_id,
                    tenant_key=session_record.tenant_key,
                    extra_claims=extra_claims,
                )

        if invalid_refresh:
            raise AuthenticationError("Refresh token is invalid.")

        self._logger.info(
            "auth_refresh_succeeded",
            extra={"request_id": request_id, "tenant_key": session_record.tenant_key, "user_id": session_record.user_id, "session_id": session_record.session_id, "outcome": "success"},
        )
        return TokenPairResponse(
            access_token=access_token.token,
            token_type=BEARER_TOKEN_TYPE,
            expires_in=self._settings.access_token_ttl_seconds,
            refresh_token=new_refresh_token,
            refresh_expires_in=self._settings.refresh_token_ttl_seconds,
            user=None,
        )

    # ── Logout ───────────────────────────────────────────────────────────

    async def logout_session(
        self,
        payload: LogoutRequest,
        *,
        claims: AccessTokenClaims,
        client_ip: str | None,
        request_id: str | None,
    ) -> dict[str, str]:
        self._ensure_feature_enabled()
        now = utc_now_sql()
        refresh_parts = self._refresh_tokens.parse(payload.refresh_token)
        if refresh_parts.session_id != claims.session_id:
            raise AuthenticationError("Refresh token does not match the current session.")
        refresh_hash = self._refresh_tokens.hash_secret(refresh_parts.secret)

        async with self._database_pool.transaction() as connection:
            session_record = await self._repository.get_session_by_id(connection, session_id=claims.session_id)
            if session_record is None or session_record.revoked_at is not None:
                raise AuthenticationError("Session is not active.")
            if session_record.user_id != claims.subject or session_record.tenant_key != claims.tenant_key:
                raise AuthorizationError()
            if not hmac.compare_digest(session_record.refresh_token_hash, refresh_hash):
                raise AuthenticationError("Refresh token does not match the current session.")
            await self._repository.revoke_session(connection, session_id=session_record.session_id, reason="logout", now=now)
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=session_record.tenant_key,
                    entity_type="session",
                    entity_id=session_record.session_id,
                    event_type=AuditEventType.LOGOUT_SUCCEEDED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=claims.subject,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=session_record.session_id,
                    properties={"revoked": "true"},
                ),
            )

        record_auth_event("logout", outcome="success", tenant_key=claims.tenant_key)
        self._logger.info(
            "auth_logout_succeeded",
            extra={"request_id": request_id, "tenant_key": claims.tenant_key, "user_id": claims.subject, "session_id": claims.session_id, "outcome": "success"},
        )
        return {"message": "Session revoked."}

    # ── User profile ─────────────────────────────────────────────────────

    async def get_authenticated_user(self, claims: AccessTokenClaims) -> AuthenticatedUser:
        import json as _json
        cache_key = f"user:{claims.subject}:profile"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            data = _json.loads(cached)
            return AuthenticatedUser(**data)

        async with self._database_pool.acquire() as connection:
            user = await self._repository.read_user_profile(
                connection,
                tenant_key=claims.tenant_key,
                user_id=claims.subject,
            )
        if user is None:
            raise AuthenticationError("Authenticated user is unavailable.")
        from dataclasses import asdict
        await self._cache.set(cache_key, _json.dumps(asdict(user), default=str), self._CACHE_TTL_PROFILE)
        return user

    # ── User properties ──────────────────────────────────────────────────

    async def get_user_properties(self, claims: AccessTokenClaims) -> UserPropertyListResponse:
        cache_key = f"user:{claims.subject}:properties"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return UserPropertyListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            props = await self._repository.list_user_properties(connection, user_id=claims.subject)
        result = UserPropertyListResponse(
            properties=[
                UserPropertyResponse(key=p.property_key, value=p.property_value)
                for p in props
            ]
        )
        await self._cache.set(cache_key, result.model_dump_json(), self._CACHE_TTL_PROPERTIES)
        return result

    _IMPERSONATION_BLOCKED_PROPERTIES = frozenset({"email", "username"})

    async def set_user_property(
        self,
        claims: AccessTokenClaims,
        *,
        property_key: str,
        property_value: str,
        client_ip: str | None,
    ) -> UserPropertyResponse:
        if claims.is_impersonation and property_key in self._IMPERSONATION_BLOCKED_PROPERTIES:
            raise AuthorizationError(
                f"Cannot modify '{property_key}' during impersonation."
            )
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            if not await self._repository.property_key_exists(connection, property_key=property_key):
                raise NotFoundError(f"Property key '{property_key}' is not defined.")
            old_prop = await self._repository.get_user_property(
                connection, user_id=claims.subject, property_key=property_key,
            )
            await self._repository.upsert_user_property(
                connection,
                user_id=claims.subject,
                property_key=property_key,
                property_value=property_value,
                updated_by=claims.subject,
                now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=claims.tenant_key,
                    entity_type="user",
                    entity_id=claims.subject,
                    event_type=AuditEventType.PROPERTY_CHANGED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=claims.subject,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={
                        "property_key": property_key,
                        "previous_value": old_prop.property_value if old_prop else None,
                        "new_value": property_value,
                    },
                ),
            )
        await self._invalidate_user_cache(claims.subject)
        return UserPropertyResponse(key=property_key, value=property_value)

    async def delete_user_property(
        self,
        claims: AccessTokenClaims,
        *,
        property_key: str,
        client_ip: str | None,
    ) -> None:
        if claims.is_impersonation and property_key in self._IMPERSONATION_BLOCKED_PROPERTIES:
            raise AuthorizationError(
                f"Cannot delete '{property_key}' during impersonation."
            )
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            old_prop = await self._repository.get_user_property(
                connection, user_id=claims.subject, property_key=property_key,
            )
            if old_prop is None:
                raise NotFoundError(f"Property '{property_key}' not found.")
            deleted = await self._repository.delete_user_property(
                connection, user_id=claims.subject, property_key=property_key,
            )
            if not deleted:
                raise NotFoundError(f"Property '{property_key}' not found.")
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=claims.tenant_key,
                    entity_type="user",
                    entity_id=claims.subject,
                    event_type=AuditEventType.PROPERTY_REMOVED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=claims.subject,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={
                        "property_key": property_key,
                        "previous_value": old_prop.property_value,
                    },
                ),
            )
        await self._invalidate_user_cache(claims.subject)

    # ── Batch set user properties ────────────────────────────────────────

    async def batch_set_user_properties(
        self,
        claims: AccessTokenClaims,
        *,
        properties: dict[str, str],
        client_ip: str | None,
    ) -> BatchSetUserPropertiesResponse:
        blocked = self._IMPERSONATION_BLOCKED_PROPERTIES & properties.keys()
        if claims.is_impersonation and blocked:
            raise AuthorizationError(
                f"Cannot modify {', '.join(sorted(blocked))} during impersonation."
            )
        now = utc_now_sql()
        async with self._database_pool.transaction() as connection:
            invalid_keys = await self._repository.validate_all_property_keys(
                connection, keys=list(properties.keys()),
            )
            if invalid_keys:
                raise NotFoundError(
                    f"Property key(s) not defined: {', '.join(sorted(invalid_keys))}"
                )
            for key, value in properties.items():
                old_prop = await self._repository.get_user_property(
                    connection, user_id=claims.subject, property_key=key,
                )
                await self._repository.upsert_user_property(
                    connection,
                    user_id=claims.subject,
                    property_key=key,
                    property_value=value,
                    updated_by=claims.subject,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=claims.tenant_key,
                        entity_type="user",
                        entity_id=claims.subject,
                        event_type=AuditEventType.PROPERTY_CHANGED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=claims.subject,
                        actor_type="user",
                        ip_address=client_ip,
                        properties={
                            "property_key": key,
                            "previous_value": old_prop.property_value if old_prop else None,
                            "new_value": value,
                        },
                    ),
                )
        await self._invalidate_user_cache(claims.subject)
        return BatchSetUserPropertiesResponse(
            properties=[
                UserPropertyResponse(key=k, value=v)
                for k, v in properties.items()
            ]
        )

    # ── Property keys discovery ──────────────────────────────────────────

    async def list_property_keys(self) -> PropertyKeyListResponse:
        cache_key = "property_keys:user"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return PropertyKeyListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            rows = await self._repository.list_property_keys(connection)
        result = PropertyKeyListResponse(
            keys=[PropertyKeyResponse(**row) for row in rows]
        )
        await self._cache.set(cache_key, result.model_dump_json(), self._CACHE_TTL_PROPERTY_KEYS)
        return result

    # ── Password change ──────────────────────────────────────────────────

    async def change_password(
        self,
        claims: AccessTokenClaims,
        *,
        payload,
        client_ip: str | None,
        request_id: str | None,
    ) -> dict[str, str]:
        if claims.is_impersonation:
            raise AuthorizationError("Cannot change password during impersonation.")
        self._ensure_feature_enabled()
        now = utc_now_sql()

        async with self._database_pool.transaction() as connection:
            account = await self._repository.get_user_account_by_type(
                connection,
                user_id=claims.subject,
                account_type_code=AccountType.LOCAL_PASSWORD.value,
            )
            if account is None:
                raise NotFoundError("No local password account found.")
            props = await connection.fetch(
                f"""
                SELECT property_key, property_value
                FROM "03_auth_manage"."09_dtl_user_account_properties"
                WHERE user_account_id = $1 AND property_key = 'password_hash'
                LIMIT 1
                """,
                account.id,
            )
            if not props:
                raise AuthenticationError("Password credential not found.")
            stored_hash = props[0]["property_value"]
            try:
                self._password_hasher.verify(stored_hash, payload.current_password)
            except VerifyMismatchError:
                raise AuthenticationError("Current password is incorrect.")
            new_password_hash = self._password_hasher.hash(payload.new_password)
            await self._repository.update_password_credential(
                connection,
                user_id=claims.subject,
                tenant_key=claims.tenant_key,
                new_password_hash=new_password_hash,
                now=now,
            )
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=claims.tenant_key,
                    entity_type="user",
                    entity_id=claims.subject,
                    event_type=AuditEventType.PASSWORD_CHANGED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=claims.subject,
                    actor_type="user",
                    ip_address=client_ip,
                    properties={"password_changed": "true"},
                ),
            )

        record_auth_event("password_change", outcome="success", tenant_key=claims.tenant_key)
        self._logger.info(
            "auth_password_changed",
            extra={"request_id": request_id, "tenant_key": claims.tenant_key, "user_id": claims.subject, "outcome": "success"},
        )
        return {"message": "Password changed."}

    # ── User accounts ────────────────────────────────────────────────────

    async def list_user_accounts(self, claims: AccessTokenClaims) -> UserAccountListResponse:
        cache_key = f"user:{claims.subject}:accounts"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return UserAccountListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as connection:
            accounts = await self._repository.list_user_accounts(connection, user_id=claims.subject)
            acct_responses = []
            for acct in accounts:
                props = await self._repository.list_account_properties_non_secret(
                    connection, user_account_id=acct.id,
                )
                acct_responses.append(UserAccountResponse(
                    account_type=acct.account_type_code,
                    is_primary=acct.is_primary,
                    is_active=acct.is_active,
                    properties={k: v for k, v in props},
                ))
        result = UserAccountListResponse(accounts=acct_responses)
        await self._cache.set(cache_key, result.model_dump_json(), self._CACHE_TTL_ACCOUNTS)
        return result

    # ── Token decode / session validation ────────────────────────────────

    def decode_access_token(self, token: str) -> AccessTokenClaims:
        try:
            payload = self._jwt_codec.decode_access_token(token)
        except ValueError as exc:
            raise AuthenticationError("Access token is invalid.") from exc
        return AccessTokenClaims(
            subject=str(payload["sub"]),
            session_id=str(payload["sid"]),
            tenant_key=str(payload["tid"]),
            expires_at=datetime.fromtimestamp(int(payload["exp"]), tz=UTC),
            portal_mode=str(payload["portal_mode"]) if payload.get("portal_mode") else None,
            is_impersonation=bool(payload.get("imp", False)),
            impersonator_id=str(payload["imp_sub"]) if payload.get("imp_sub") else None,
            impersonator_session_id=str(payload["imp_sid"]) if payload.get("imp_sid") else None,
        )

    async def require_active_access_claims(self, claims: AccessTokenClaims) -> AccessTokenClaims:
        self._ensure_feature_enabled()
        now = datetime.now(tz=UTC)
        async with self._database_pool.acquire() as connection:
            session_state = await self._repository.get_access_session_state(
                connection,
                session_id=claims.session_id,
            )
        if session_state is None:
            raise AuthenticationError("Access token is invalid.")
        if session_state.user_id != claims.subject or session_state.tenant_key != claims.tenant_key:
            raise AuthenticationError("Access token is invalid.")
        if self._normalize_portal_mode(session_state.portal_mode) != self._normalize_portal_mode(claims.portal_mode):
            raise AuthenticationError("Access token is invalid.")
        if session_state.revoked_at is not None or session_state.refresh_token_expires_at <= now:
            raise AuthenticationError("Access token is invalid.")
        if (
            not session_state.user_is_active
            or session_state.user_is_disabled
            or session_state.user_is_deleted
            or session_state.user_is_locked
        ):
            raise AuthenticationError("Access token is invalid.")
        return claims

    # ── API key authentication ───────────────────────────────────────────

    async def authenticate_api_key(
        self, token: str, *, client_ip: str | None = None,
    ) -> AccessTokenClaims:
        import hashlib as _hashlib

        if not self._settings.api_key_enabled:
            raise AuthenticationError("API key authentication is disabled.")

        key_hash = _hashlib.sha256(token.encode()).hexdigest()

        async with self._database_pool.acquire() as connection:
            row = await self._repository.get_api_key_by_hash(connection, key_hash=key_hash)

        if not row:
            raise AuthenticationError("Invalid API key.")

        if row["status_code"] != "active":
            raise AuthenticationError("API key is not active.")

        if row["expires_at"] is not None:
            now = datetime.now(tz=UTC)
            if row["expires_at"].replace(tzinfo=UTC) <= now:
                raise AuthenticationError("API key has expired.")

        if (
            not row["user_is_active"]
            or row["user_is_disabled"]
            or row["user_is_deleted"]
            or row["user_is_locked"]
        ):
            raise AuthenticationError("User account is not active.")

        # Fire-and-forget: update last_used_at
        try:
            async with self._database_pool.acquire() as connection:
                await self._repository.update_api_key_last_used(
                    connection,
                    key_id=str(row["id"]),
                    client_ip=client_ip,
                    now=datetime.now(tz=UTC),
                )
        except Exception:
            self._logger.debug("api_key_last_used_update_failed", exc_info=True)

        scopes = tuple(row["scopes"]) if row["scopes"] else None

        return AccessTokenClaims(
            subject=str(row["user_id"]),
            session_id=f"apikey:{row['id']}",
            tenant_key=row["tenant_key"],
            expires_at=row["expires_at"] or datetime.max.replace(tzinfo=UTC),
            is_api_key=True,
            api_key_id=str(row["id"]),
            api_key_scopes=scopes,
        )

    # ── Private helpers ──────────────────────────────────────────────────

    async def _process_registration_invites(
        self, connection, *, email: str, user_id: str, tenant_key: str, now
    ) -> None:
        try:
            _invite_service_module = import_module(
                "backend.03_auth_manage.09_invitations.service"
            )
            invite_service = _invite_service_module.InvitationService(
                settings=self._settings,
                database_pool=self._database_pool,
                cache=self._cache,
            )
            await invite_service.process_registration_invites(
                connection, email=email, user_id=user_id,
                tenant_key=tenant_key, now=now,
            )
        except Exception:
            self._logger.warning(
                "invitation_auto_accept_failed",
                extra={"email": email, "user_id": user_id},
                exc_info=True,
            )

    def _ensure_feature_enabled(self) -> None:
        if not self._settings.auth_local_core_enabled:
            raise AuthFeatureDisabledError()

    def _classify_login(self, raw_login: str) -> tuple[str, str]:
        normalized = raw_login.strip().lower()
        if "@" in normalized:
            return "email", normalized
        return "username", normalized

    def _verify_dummy_password(self, password: str) -> None:
        try:
            self._password_hasher.verify(self._dummy_password_hash, password)
        except VerifyMismatchError:
            return

    async def _record_failure(
        self,
        connection: asyncpg.Connection,
        *,
        tenant_key: str,
        normalized_login: str,
        identity_type: str,
        user_id: str | None,
        client_ip: str | None,
        now: datetime,
    ) -> None:
        attempt_id = await self._repository.record_login_attempt(
            connection,
            tenant_key=tenant_key,
            normalized_identifier=normalized_login,
            identity_type_code=identity_type,
            user_id=user_id,
            outcome="failure",
            failure_reason="invalid_credentials",
            client_ip=client_ip,
            now=now,
        )
        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid4()),
                tenant_key=tenant_key,
                entity_type="login_attempt",
                entity_id=attempt_id,
                event_type=AuditEventType.LOGIN_FAILED.value,
                event_category=AuditEventCategory.AUTH.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                ip_address=client_ip,
                properties={"reason": "invalid_credentials"},
            ),
        )
        record_auth_event("login", outcome="failure", tenant_key=tenant_key)
