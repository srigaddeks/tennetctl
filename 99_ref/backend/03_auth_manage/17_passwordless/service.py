from __future__ import annotations

import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta
from importlib import import_module
from uuid import uuid4

import asyncpg

from ..constants import AccountType, AuditEventCategory, AuditEventType, BEARER_TOKEN_TYPE
from ..repository import AuthRepository
from ..schemas import AuthUserResponse, TokenPairResponse
from .constants import (
    ASSIGNEE_PORTAL_MODE,
    MAGIC_LINK_ASSIGNEE_CHALLENGE_TYPE,
    MAGIC_LINK_CHALLENGE_TYPE,
    MAGIC_LINK_DEFAULT_TTL_HOURS,
    MAGIC_LINK_MAX_TTL_HOURS,
)
from .schemas import RequestMagicLinkRequest, RequestMagicLinkResponse

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


@instrument_class_methods(namespace="auth.passwordless", logger_name="backend.auth.passwordless")
class PasswordlessService:
    _RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour window for rate limiting
    _RATE_LIMIT_MAX_REQUESTS = 5       # max 5 magic link requests per email per hour

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
        self._refresh_tokens = RefreshTokenManager()
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
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.auth.passwordless")

    @staticmethod
    def _generate_magic_link_token() -> tuple[str, str]:
        """Generate a one-time magic link token. Returns (token_string, secret_hash)."""
        secret = secrets.token_urlsafe(32)
        secret_hash = hashlib.sha256(secret.encode()).hexdigest()
        return secret, secret_hash

    @staticmethod
    def _parse_magic_link_token(token: str) -> tuple[str, str]:
        """Parse token string into (challenge_id, secret). Raises ValueError on bad format."""
        parts = token.split(".", 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("Invalid magic link token format.")
        return parts[0], parts[1]

    @staticmethod
    def _hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()

    async def _check_rate_limit(self, email: str) -> None:
        """Raise RateLimitError if email has exceeded magic link request rate."""
        cache_key = f"passwordless:rate:{hashlib.sha256(email.encode()).hexdigest()}"
        count_raw = await self._cache.get(cache_key)
        count = int(count_raw) if count_raw else 0
        if count >= self._RATE_LIMIT_MAX_REQUESTS:
            raise RateLimitError()
        # Increment counter, set TTL on first request
        await self._cache.set(cache_key, str(count + 1), ttl_seconds=self._RATE_LIMIT_WINDOW_SECONDS)

    def _get_ttl_hours(self) -> int:
        configured = getattr(self._settings, "magic_link_default_ttl_hours", MAGIC_LINK_DEFAULT_TTL_HOURS)
        return min(max(configured, 1), MAGIC_LINK_MAX_TTL_HOURS)

    def _build_magic_link_url(
        self,
        challenge_id: str,
        secret: str,
        *,
        challenge_type_code: str,
    ) -> str:
        if challenge_type_code == MAGIC_LINK_ASSIGNEE_CHALLENGE_TYPE:
            base = getattr(self._settings, "magic_link_assignee_frontend_verify_url", "").rstrip("/")
            if not base:
                base = getattr(self._settings, "magic_link_frontend_verify_url", "").rstrip("/")
        else:
            base = getattr(self._settings, "magic_link_frontend_verify_url", "").rstrip("/")
        # Fallback to platform_base_url if specific URL not configured
        if not base:
            _platform = getattr(self._settings, "platform_base_url", "").rstrip("/")
            if _platform:
                if challenge_type_code == MAGIC_LINK_ASSIGNEE_CHALLENGE_TYPE:
                    base = f"{_platform}/assignee/login"
                else:
                    base = f"{_platform}/magic-link/verify"
        token = f"{challenge_id}.{secret}"
        if base:
            return f"{base}?token={token}"
        return token

    # ── Request magic link ────────────────────────────────────────────────

    async def request_magic_link(
        self,
        payload: RequestMagicLinkRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> RequestMagicLinkResponse:
        return await self._request_magic_link_for_channel(
            payload=payload,
            challenge_type_code=MAGIC_LINK_CHALLENGE_TYPE,
            assignee_only=False,
            client_ip=client_ip,
            request_id=request_id,
        )

    async def request_assignee_magic_link(
        self,
        payload: RequestMagicLinkRequest,
        *,
        client_ip: str | None,
        request_id: str | None,
    ) -> RequestMagicLinkResponse:
        return await self._request_magic_link_for_channel(
            payload=payload,
            challenge_type_code=MAGIC_LINK_ASSIGNEE_CHALLENGE_TYPE,
            assignee_only=True,
            client_ip=client_ip,
            request_id=request_id,
        )

    async def _request_magic_link_for_channel(
        self,
        *,
        payload: RequestMagicLinkRequest,
        challenge_type_code: str,
        assignee_only: bool,
        client_ip: str | None,
        request_id: str | None,
    ) -> RequestMagicLinkResponse:
        if not getattr(self._settings, "magic_link_enabled", True):
            raise AuthorizationError("Passwordless authentication is not enabled.")

        now = utc_now_sql()
        tenant_key = self._settings.default_tenant_key
        email = payload.email.strip().lower()
        ttl_hours = self._get_ttl_hours()
        magic_link_token: str | None = None
        magic_link_url: str | None = None
        challenge_id: str | None = None
        eligible_user_id: str | None = None

        # Rate limiting (best-effort via cache — NullCache skips this safely)
        await self._check_rate_limit(email)

        async with self._database_pool.transaction() as connection:
            user = await self._repository.find_user_by_email_for_magic_link(
                connection, tenant_key=tenant_key, email=email,
            )
            is_blocked_existing_user = False
            if user is not None and not (user.is_active and not user.is_disabled and not user.is_deleted and not user.is_locked):
                is_blocked_existing_user = True

            if user is not None:
                eligible_user_id = user.user_id
                if assignee_only:
                    eligible = await self._repository.has_any_task_assignment(
                        connection,
                        tenant_key=tenant_key,
                        user_id=user.user_id,
                    )
                    if not eligible:
                        eligible_user_id = None

            should_issue_challenge = not is_blocked_existing_user and (
                not assignee_only or eligible_user_id is not None
            )

            if not should_issue_challenge:
                if assignee_only:
                    await self._repository.expire_active_magic_link_challenges(
                        connection,
                        target_value=email,
                        tenant_key=tenant_key,
                        challenge_type_code=challenge_type_code,
                        now=now,
                    )
            else:
                await self._repository.expire_active_magic_link_challenges(
                    connection,
                    target_value=email,
                    tenant_key=tenant_key,
                    challenge_type_code=challenge_type_code,
                    now=now,
                )

                secret, secret_hash = self._generate_magic_link_token()
                challenge_id = await self._repository.create_magic_link_challenge(
                    connection,
                    user_id=eligible_user_id,
                    tenant_key=tenant_key,
                    target_value=email,
                    secret_hash=secret_hash,
                    expires_at=now + timedelta(hours=ttl_hours),
                    client_ip=client_ip,
                    challenge_type_code=challenge_type_code,
                    now=now,
                )
                magic_link_token = f"{challenge_id}.{secret}"
                magic_link_url = self._build_magic_link_url(
                    challenge_id,
                    secret,
                    challenge_type_code=challenge_type_code,
                )

                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="challenge",
                        entity_id=challenge_id,
                        event_type=AuditEventType.MAGIC_LINK_REQUESTED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=eligible_user_id or "anonymous",
                        actor_type="user",
                        ip_address=client_ip,
                        properties={
                            "target": email,
                            "ttl_hours": str(ttl_hours),
                            "challenge_type": challenge_type_code,
                        },
                    ),
                )

        # Send magic link email via notification system (best-effort — never blocks auth flow)
        if self._settings.notification_enabled and magic_link_url and challenge_id:
            try:
                _dispatcher_module = import_module("backend.04_notifications.02_dispatcher.dispatcher")
                dispatcher = _dispatcher_module.NotificationDispatcher(
                    database_pool=self._database_pool, settings=self._settings,
                )
                _expiry_label = f"{ttl_hours} hour{'s' if ttl_hours != 1 else ''}"
                _ml_audit_entry = AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="challenge",
                    entity_id=challenge_id,
                    event_type=AuditEventType.MAGIC_LINK_REQUESTED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=eligible_user_id or "anonymous",
                    actor_type="user",
                    ip_address=client_ip,
                    properties={
                        "target": email,
                        "magic_link_url": magic_link_url,
                        "magic_link.url": magic_link_url,
                        "magic_link.expires_in": _expiry_label,
                        "expires_in": _expiry_label,
                        "method": "magic_link_assignee" if assignee_only else "magic_link",
                    },
                )

                async def _dispatch_magic_link() -> None:
                    try:
                        if eligible_user_id:
                            # Existing user — use template-based dispatch
                            nid = await dispatcher.dispatch_transactional(
                                audit_entry=_ml_audit_entry,
                                recipient_user_id=eligible_user_id,
                                template_code="magic_link_login_email",
                                notification_type_code="magic_link_login",
                                tenant_key=tenant_key,
                                idempotency_key=f"magic_link:{challenge_id}:email",
                                priority_code="critical",
                            )
                        else:
                            # No user yet — use raw email dispatch with rendered template
                            nid = await dispatcher.dispatch_to_email(
                                recipient_email=email,
                                notification_type_code="magic_link_login",
                                subject="Your Magic Link — K-Control",
                                body_html=(
                                    f"<p>Hello,</p>"
                                    f"<p>Click the link below to sign in. "
                                    f"This link expires in {_expiry_label}.</p>"
                                    f'<p><a href="{magic_link_url}" style="background:#295cf6;color:#fff;padding:14px 36px;'
                                    f'border-radius:6px;text-decoration:none;font-weight:600;">Sign In with Magic Link</a></p>'
                                    f"<p>If you didn't request this, you can safely ignore this email.</p>"
                                ),
                                body_text=(
                                    f"Sign in to K-Control:\n\n{magic_link_url}\n\n"
                                    f"This link expires in {_expiry_label} and can only be used once."
                                ),
                                tenant_key=tenant_key,
                                idempotency_key=f"magic_link:{challenge_id}:email",
                                priority_code="critical",
                            )
                        self._logger.info("magic_link_notification_queued", extra={"notification_id": nid})
                    except Exception:
                        self._logger.warning("magic_link_notification_dispatch_failed", exc_info=True)

                import asyncio as _asyncio
                _asyncio.create_task(_dispatch_magic_link())
            except Exception as _exc:
                self._logger.warning(
                    "auth_magic_link_email_failed",
                    extra={"reason": str(_exc)},
                )

        self._logger.info(
            "auth_magic_link_requested",
            extra={
                "request_id": request_id,
                "tenant_key": tenant_key,
                "challenge_type": challenge_type_code,
                "issued": challenge_id is not None,
                "magic_link_url": magic_link_url if (magic_link_url and self._settings.environment in {"local", "test", "development", "dev"}) else "[REDACTED]",
                "outcome": "sent",
            },
        )

        record_auth_event("magic_link_request", outcome="success", tenant_key=tenant_key)

        if self._settings.environment in {"local", "test", "development", "dev"}:
            return RequestMagicLinkResponse(
                message="If this email is registered or eligible, a login link has been sent.",
                magic_link_token=magic_link_token,
            )
        return RequestMagicLinkResponse(
            message="If this email is registered or eligible, a login link has been sent.",
        )

    # ── Verify magic link ─────────────────────────────────────────────────

    async def verify_magic_link(
        self,
        token: str,
        *,
        client_ip: str | None,
        user_agent: str | None,
        request_id: str | None,
    ) -> TokenPairResponse:
        if not getattr(self._settings, "magic_link_enabled", True):
            raise AuthorizationError("Passwordless authentication is not enabled.")

        now = utc_now_sql()
        now_aware = now.replace(tzinfo=UTC)
        tenant_key = self._settings.default_tenant_key

        try:
            challenge_id, secret = self._parse_magic_link_token(token)
        except ValueError as exc:
            raise AuthenticationError("Magic link token is invalid.") from exc

        provided_hash = self._hash_secret(secret)

        async with self._database_pool.transaction() as connection:
            challenge = await self._repository.get_magic_link_challenge(
                connection, challenge_id=challenge_id,
            )
            if challenge is None or challenge.consumed_at is not None:
                raise AuthenticationError("Magic link token is invalid or already used.")
            if challenge.expires_at <= now_aware:
                raise AuthenticationError("Magic link token has expired.")
            if not hmac.compare_digest(challenge.secret_hash, provided_hash):
                raise AuthenticationError("Magic link token is invalid.")

            is_assignee_challenge = challenge.challenge_type_code == MAGIC_LINK_ASSIGNEE_CHALLENGE_TYPE
            email = challenge.target_value
            is_new_user = False
            portal_mode: str | None = ASSIGNEE_PORTAL_MODE if is_assignee_challenge else None

            # Look up existing user
            user = await self._repository.find_user_by_email_for_magic_link(
                connection, tenant_key=tenant_key, email=email,
            )

            if user is not None:
                # Existing user — check they're not blocked
                if user.is_deleted:
                    raise AuthenticationError("Account not found.")
                if not user.is_active or user.is_disabled or user.is_locked:
                    raise AuthorizationError("Account is not accessible.")

                # Ensure magic_link account exists (for full users doing first passwordless)
                await self._repository.ensure_magic_link_account(
                    connection, user_id=user.user_id, tenant_key=tenant_key, now=now,
                )
                user_id = user.user_id
                user_email = user.email
                user_username = user.username
                user_email_verified = user.email_verified
                user_account_status = user.account_status
                user_category = user.user_category

            else:
                if is_assignee_challenge:
                    raise AuthenticationError("Magic link token is invalid.")
                # New external collaborator — check license limit
                # Get max_external_users from license profile (simplified: check count vs default 10)
                ext_count = await self._repository.count_users_by_category(
                    connection, tenant_key=tenant_key, user_category="external_collaborator",
                )
                # Use a generous default of 9999 if we can't resolve from license profile
                max_ext = 9999
                if ext_count >= max_ext:
                    raise ConflictError("External user license limit reached.")

                # Create the user
                user_id, _ = await self._repository.create_external_user(
                    connection, tenant_key=tenant_key, now=now,
                )
                # Set properties
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="email",
                    property_value=email, created_by=user_id, now=now,
                )
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="email_verified",
                    property_value="true", created_by=user_id, now=now,
                )
                await self._repository.create_user_property(
                    connection, user_id=user_id, property_key="user_category_source",
                    property_value="magic_link_auto_created", created_by=user_id, now=now,
                )
                # Create magic_link account
                await self._repository.create_user_account(
                    connection, user_id=user_id, tenant_key=tenant_key,
                    account_type_code=AccountType.MAGIC_LINK.value,
                    is_primary=True, created_by=user_id, now=now,
                )
                # Enroll in external_collaborators group
                await self._repository.add_user_to_external_collaborators_group(
                    connection, user_id=user_id, tenant_key=tenant_key, now=now,
                )
                # Audit: external user created
                await self._audit_writer.write_entry(
                    connection,
                    AuditEntry(
                        id=str(uuid4()),
                        tenant_key=tenant_key,
                        entity_type="user",
                        entity_id=user_id,
                        event_type=AuditEventType.MAGIC_LINK_EXTERNAL_USER_CREATED.value,
                        event_category=AuditEventCategory.AUTH.value,
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        ip_address=client_ip,
                        properties={"email": email, "user_category": "external_collaborator"},
                    ),
                )
                user_email = email
                user_username = None
                user_email_verified = True
                user_account_status = "active"
                user_category = "external_collaborator"
                is_new_user = True

            if is_assignee_challenge:
                has_assignment = await self._repository.has_any_task_assignment(
                    connection,
                    tenant_key=tenant_key,
                    user_id=user_id,
                )
                if not has_assignment:
                    raise AuthenticationError("Magic link token is invalid.")

            # Create session
            refresh_expires_at = now + timedelta(seconds=self._settings.refresh_token_ttl_seconds)
            session_id = await self._repository.create_session(
                connection,
                user_id=user_id,
                tenant_key=tenant_key,
                refresh_token_hash="pending",
                refresh_expires_at=refresh_expires_at,
                client_ip=client_ip,
                user_agent=user_agent,
                portal_mode=portal_mode,
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

            # Consume challenge
            await self._repository.consume_magic_link_challenge(
                connection, challenge_id=challenge_id, now=now,
            )

            # Audit: magic link verified
            await self._audit_writer.write_entry(
                connection,
                AuditEntry(
                    id=str(uuid4()),
                    tenant_key=tenant_key,
                    entity_type="session",
                    entity_id=session_id,
                    event_type=AuditEventType.MAGIC_LINK_VERIFIED.value,
                    event_category=AuditEventCategory.AUTH.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    ip_address=client_ip,
                    session_id=session_id,
                    properties={
                        "user_category": user_category,
                        "is_new_user": str(is_new_user),
                        "challenge_type": challenge.challenge_type_code,
                        "portal_mode": portal_mode or "",
                    },
                ),
            )

            extra_claims: dict[str, object] | None = None
            if portal_mode:
                extra_claims = {"portal_mode": portal_mode}
            access_token = self._jwt_codec.encode_access_token(
                subject=user_id,
                session_id=session_id,
                tenant_key=tenant_key,
                extra_claims=extra_claims,
            )

        record_auth_event("magic_link_verify", outcome="success", tenant_key=tenant_key)
        self._logger.info(
            "auth_magic_link_verified",
            extra={
                "request_id": request_id,
                "tenant_key": tenant_key,
                "user_id": user_id,
                "session_id": session_id,
                "user_category": user_category,
                "is_new_user": is_new_user,
                "challenge_type": challenge.challenge_type_code,
                "portal_mode": portal_mode,
                "outcome": "success",
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
                email=user_email,
                username=user_username,
                email_verified=user_email_verified,
                account_status=user_account_status,
                user_category=user_category,
                is_new_user=is_new_user,
            ),
        )
