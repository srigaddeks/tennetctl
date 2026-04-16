from __future__ import annotations

import json
import uuid
from importlib import import_module

from .constants import NOTIFICATION_SCHEMA
from .models import (
    NotificationCategoryRecord,
    NotificationChannelRecord,
    NotificationQueueRecord,
    NotificationTypeRecord,
    UserNotificationPreferenceRecord,
    WebPushSubscriptionRecord,
)
from .schemas import (
    CategoryResponse,
    ChannelResponse,
    DeliveryFunnelResponse,
    DeliveryLogResponse,
    DeliveryReportResponse,
    DeliveryReportRow,
    NotificationConfigResponse,
    NotificationDetailResponse,
    NotificationHistoryItem,
    NotificationHistoryResponse,
    NotificationTypeResponse,
    PreferenceMatrixResponse,
    PreferenceResponse,
    QueueActionResponse,
    QueueAdminResponse,
    QueueItemAdminResponse,
    QueueStatsResponse,
    SendTestNotificationRequest,
    SendTestNotificationResponse,
    SetPreferenceRequest,
    SmtpConfigRequest,
    SmtpConfigResponse,
    SmtpTestRequest,
    SmtpTestResponse,
    TemplateVariableKeyResponse,
    TrackingEventResponse,
    WebPushSubscribeRequest,
    WebPushSubscriptionResponse,
)

_crypto_module = import_module("backend.04_notifications.04_channels.crypto")
_encrypt_value = _crypto_module.encrypt_value
_decrypt_value = _crypto_module.decrypt_value
_parse_encryption_key = _crypto_module.parse_encryption_key

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_time_module = import_module("backend.01_core.time_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_audit_module = import_module("backend.01_core.audit")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
utc_now_sql = _time_module.utc_now_sql
require_permission = _perm_check_module.require_permission
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter

SCHEMA = f'"{NOTIFICATION_SCHEMA}"'

_CACHE_KEY_CONFIG = "notif:config"
_CACHE_TTL_DIMENSION = 3600  # 1 hour (static dimension data)
_CACHE_TTL_PREFERENCES = 300  # 5 minutes
_CACHE_TTL_HISTORY = 60  # 1 minute


@instrument_class_methods(
    namespace="notifications.service",
    logger_name="backend.notifications.service.instrumentation",
)
class NotificationService:
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
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.notifications")
        # Parse encryption key once at init time (None if not configured)
        self._smtp_enc_key: bytes | None = (
            _parse_encryption_key(settings.notification_encryption_key)
            if settings.notification_encryption_key
            else None
        )

    def _encrypt_smtp_password(self, password: str) -> str:
        """Encrypt SMTP password if key is configured, else store as-is."""
        if self._smtp_enc_key:
            return _encrypt_value(password, self._smtp_enc_key)
        return password

    def _decrypt_smtp_password(self, stored: str) -> str:
        """Decrypt SMTP password if key is configured, else return as-is."""
        if self._smtp_enc_key:
            try:
                return _decrypt_value(stored, self._smtp_enc_key)
            except Exception:
                # Legacy plaintext — return as-is (first migration grace period)
                return stored
        return stored

    # ------------------------------------------------------------------ #
    # Config (all dimension data in one call)
    # ------------------------------------------------------------------ #

    async def get_config(self) -> NotificationConfigResponse:
        cached = await self._cache.get(_CACHE_KEY_CONFIG)
        if cached is not None:
            return NotificationConfigResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            ch_rows = await conn.fetch(
                f'SELECT id, code, name, description, is_available, sort_order '
                f'FROM {SCHEMA}."02_dim_notification_channels" '
                f'WHERE is_available = TRUE ORDER BY sort_order'
            )
            cat_rows = await conn.fetch(
                f'SELECT id, code, name, description, is_mandatory, sort_order '
                f'FROM {SCHEMA}."03_dim_notification_categories" ORDER BY sort_order'
            )
            type_rows = await conn.fetch(
                f'SELECT id, code, name, description, category_code, '
                f'is_mandatory, is_user_triggered, default_enabled, '
                f'cooldown_seconds, sort_order '
                f'FROM {SCHEMA}."04_dim_notification_types" ORDER BY sort_order'
            )
            var_rows = await conn.fetch(
                f'SELECT id, code, name, description, data_type, '
                f'example_value, preview_default, resolution_source, resolution_key, '
                f'static_value, query_id, is_user_defined, sort_order '
                f'FROM {SCHEMA}."08_dim_template_variable_keys" ORDER BY sort_order'
            )

        result = NotificationConfigResponse(
            channels=[
                ChannelResponse(
                    id=str(r["id"]), code=r["code"], name=r["name"],
                    description=r["description"], is_available=r["is_available"],
                    sort_order=r["sort_order"],
                )
                for r in ch_rows
            ],
            categories=[
                CategoryResponse(
                    id=str(r["id"]), code=r["code"], name=r["name"],
                    description=r["description"], is_mandatory=r["is_mandatory"],
                    sort_order=r["sort_order"],
                )
                for r in cat_rows
            ],
            types=[
                NotificationTypeResponse(
                    id=str(r["id"]), code=r["code"], name=r["name"],
                    description=r["description"], category_code=r["category_code"],
                    is_mandatory=r["is_mandatory"],
                    is_user_triggered=r["is_user_triggered"],
                    default_enabled=r["default_enabled"],
                    cooldown_seconds=r["cooldown_seconds"],
                    sort_order=r["sort_order"],
                )
                for r in type_rows
            ],
            variable_keys=[
                TemplateVariableKeyResponse(
                    id=str(r["id"]), code=r["code"], name=r["name"],
                    description=r["description"], data_type=r["data_type"],
                    example_value=r["example_value"],
                    preview_default=r["preview_default"],
                    resolution_source=r["resolution_source"],
                    resolution_key=r["resolution_key"],
                    static_value=r.get("static_value"),
                    query_id=str(r["query_id"]) if r.get("query_id") else None,
                    is_user_defined=r.get("is_user_defined", False),
                    sort_order=r["sort_order"],
                )
                for r in var_rows
            ],
        )
        await self._cache.set(_CACHE_KEY_CONFIG, result.model_dump_json(), _CACHE_TTL_DIMENSION)
        return result

    # ------------------------------------------------------------------ #
    # Preferences
    # ------------------------------------------------------------------ #

    async def list_preferences(
        self, *, user_id: str, tenant_key: str
    ) -> PreferenceMatrixResponse:
        cache_key = f"notif:prefs:{user_id}:{tenant_key}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return PreferenceMatrixResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, user_id, tenant_key, scope_level,
                       channel_code, category_code, notification_type_code,
                       scope_org_id, scope_workspace_id, is_enabled,
                       created_at::text, updated_at::text
                FROM {SCHEMA}."17_lnk_user_notification_preferences"
                WHERE user_id = $1 AND tenant_key = $2
                ORDER BY
                    CASE scope_level
                        WHEN 'global' THEN 1
                        WHEN 'channel' THEN 2
                        WHEN 'category' THEN 3
                        WHEN 'type' THEN 4
                    END,
                    created_at
                """,
                user_id,
                tenant_key,
            )
        items = [_preference_response(r) for r in rows]
        result = PreferenceMatrixResponse(items=items)
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_PREFERENCES)
        return result

    async def set_preference(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: SetPreferenceRequest,
    ) -> PreferenceResponse:
        now = utc_now_sql()
        pref_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            # Upsert: match on user + tenant + scope_level + channel + category + type + org + ws
            row = await conn.fetchrow(
                f"""
                INSERT INTO {SCHEMA}."17_lnk_user_notification_preferences" (
                    id, user_id, tenant_key, scope_level,
                    channel_code, category_code, notification_type_code,
                    scope_org_id, scope_workspace_id, is_enabled,
                    created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
                ON CONFLICT (user_id, tenant_key, scope_level,
                             COALESCE(channel_code, ''),
                             COALESCE(category_code, ''),
                             COALESCE(notification_type_code, ''),
                             COALESCE(scope_org_id, '00000000-0000-0000-0000-000000000000'),
                             COALESCE(scope_workspace_id, '00000000-0000-0000-0000-000000000000'))
                DO UPDATE SET is_enabled = EXCLUDED.is_enabled, updated_at = EXCLUDED.updated_at
                RETURNING id, user_id, tenant_key, scope_level,
                          channel_code, category_code, notification_type_code,
                          scope_org_id, scope_workspace_id, is_enabled,
                          created_at::text, updated_at::text
                """,
                pref_id,
                user_id,
                tenant_key,
                request.scope_level,
                request.channel_code,
                request.category_code,
                request.notification_type_code,
                request.scope_org_id,
                request.scope_workspace_id,
                request.is_enabled,
                now,
                now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="notification_preference",
                    entity_id=str(row["id"]),
                    event_type="preference_set",
                    event_category="notification",
                    occurred_at=now,
                    actor_id=user_id,
                    properties={
                        "scope_level": request.scope_level,
                        "channel_code": request.channel_code or "",
                        "is_enabled": str(request.is_enabled),
                    },
                ),
            )

        await self._cache.delete(f"notif:prefs:{user_id}:{tenant_key}")
        return _preference_response(row)

    async def delete_preference(
        self, *, user_id: str, tenant_key: str, preference_id: str
    ) -> None:
        async with self._database_pool.transaction() as conn:
            result = await conn.execute(
                f"""
                DELETE FROM {SCHEMA}."17_lnk_user_notification_preferences"
                WHERE id = $1 AND user_id = $2 AND tenant_key = $3
                """,
                preference_id,
                user_id,
                tenant_key,
            )
            if result == "DELETE 0":
                raise NotFoundError(f"Preference '{preference_id}' not found")

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="notification_preference",
                    entity_id=preference_id,
                    event_type="preference_deleted",
                    event_category="notification",
                    occurred_at=utc_now_sql(),
                    actor_id=user_id,
                ),
            )

        await self._cache.delete(f"notif:prefs:{user_id}:{tenant_key}")

    # ------------------------------------------------------------------ #
    # Web push subscriptions
    # ------------------------------------------------------------------ #

    def get_vapid_public_key(self) -> str | None:
        """Return the VAPID app server key (applicationServerKey) for the frontend.

        This is the URL-safe base64 uncompressed EC public key point,
        as returned by VAPID.generate_keys() (third return value).
        """
        return (
            getattr(self._settings, "notification_vapid_app_server_key", None)
            or getattr(self._settings, "notification_vapid_public_key", None)
        )

    async def list_web_push_subscriptions(
        self,
        *,
        user_id: str,
        tenant_key: str,
    ) -> list[WebPushSubscriptionResponse]:
        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, user_id, tenant_key, endpoint, is_active,
                       last_used_at::text, created_at::text, updated_at::text
                FROM {SCHEMA}."13_fct_web_push_subscriptions"
                WHERE user_id = $1 AND tenant_key = $2
                  AND is_active = TRUE AND is_deleted = FALSE
                ORDER BY created_at DESC
                """,
                user_id,
                tenant_key,
            )
        return [_subscription_response(r) for r in rows]

    async def subscribe_web_push(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: WebPushSubscribeRequest,
    ) -> WebPushSubscriptionResponse:
        now = utc_now_sql()
        sub_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            row = await conn.fetchrow(
                f"""
                INSERT INTO {SCHEMA}."13_fct_web_push_subscriptions" (
                    id, user_id, tenant_key, endpoint, p256dh_key, auth_key,
                    user_agent, is_active, last_used_at, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, TRUE, NULL, $8, $9)
                ON CONFLICT (user_id, endpoint)
                DO UPDATE SET
                    p256dh_key = EXCLUDED.p256dh_key,
                    auth_key = EXCLUDED.auth_key,
                    user_agent = EXCLUDED.user_agent,
                    is_active = TRUE,
                    updated_at = EXCLUDED.updated_at
                RETURNING id, user_id, tenant_key, endpoint, is_active,
                          last_used_at::text, created_at::text, updated_at::text
                """,
                sub_id,
                user_id,
                tenant_key,
                request.endpoint,
                request.p256dh_key,
                request.auth_key,
                request.user_agent,
                now,
                now,
            )
        return _subscription_response(row)

    async def unsubscribe_web_push(
        self, *, user_id: str, tenant_key: str, subscription_id: str
    ) -> None:
        async with self._database_pool.transaction() as conn:
            result = await conn.execute(
                f"""
                UPDATE {SCHEMA}."13_fct_web_push_subscriptions"
                SET is_active = FALSE, updated_at = NOW()
                WHERE id = $1 AND user_id = $2 AND tenant_key = $3
                """,
                subscription_id,
                user_id,
                tenant_key,
            )
            if result == "UPDATE 0":
                raise NotFoundError(f"Subscription '{subscription_id}' not found")

    async def send_test_web_push(
        self,
        *,
        user_id: str,
        tenant_key: str,
        title: str | None = None,
        body: str | None = None,
        deep_link: str = "/notifications",
    ) -> dict:
        """Send a test push notification to all active subscriptions of the user."""
        _webpush_module = import_module("backend.04_notifications.04_channels.webpush_provider")

        priv = getattr(self._settings, "notification_vapid_private_key", None)
        pub = getattr(self._settings, "notification_vapid_public_key", None)
        email = getattr(self._settings, "notification_vapid_claims_email", None)

        if not (priv and pub and email):
            return {"success": False, "message": "Web push not configured (VAPID keys missing)", "sent": 0}

        provider = _webpush_module.WebPushProvider(
            vapid_private_key=priv,
            vapid_public_key=pub,
            vapid_claims_email=email,
        )

        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT endpoint, p256dh_key, auth_key
                FROM {SCHEMA}."13_fct_web_push_subscriptions"
                WHERE user_id = $1 AND tenant_key = $2
                  AND is_active = TRUE AND is_deleted = FALSE
                """,
                user_id,
                tenant_key,
            )

        if not rows:
            return {"success": False, "message": "No active push subscriptions found", "sent": 0}

        import json as _json
        sent = 0
        errors = []
        for row in rows:
            recipient = _json.dumps({
                "endpoint": row["endpoint"],
                "keys": {"auth": row["auth_key"], "p256dh": row["p256dh_key"]},
            })
            result = await provider.send(
                recipient=recipient,
                subject=title or "K-Control",
                body_short=body or "Desktop notifications are active. Click to open your inbox.",
                metadata={"url": deep_link, "tag": "kcontrol-test"},
            )
            if result.success:
                sent += 1
            else:
                errors.append(result.error_message or result.error_code or "unknown")

        await provider.close()

        if sent > 0:
            return {"success": True, "message": f"Test push sent to {sent} subscription(s)", "sent": sent}
        return {"success": False, "message": f"Failed to send: {'; '.join(errors)}", "sent": 0}

    # ------------------------------------------------------------------ #
    # Notification history
    # ------------------------------------------------------------------ #

    async def get_history(
        self,
        *,
        user_id: str,
        tenant_key: str,
        limit: int = 50,
        offset: int = 0,
    ) -> NotificationHistoryResponse:
        _queue_repo_module = import_module("backend.04_notifications.03_queue.repository")
        repo = _queue_repo_module.QueueRepository()

        async with self._database_pool.acquire() as conn:
            records, total = await repo.get_user_notification_history(
                conn, user_id, tenant_key=tenant_key, limit=limit, offset=offset
            )

        items = [
            NotificationHistoryItem(
                id=r.id,
                notification_type_code=r.notification_type_code,
                channel_code=r.channel_code,
                status_code=r.status_code,
                priority_code=r.priority_code,
                rendered_subject=r.rendered_subject,
                rendered_body=r.rendered_body,
                scheduled_at=r.scheduled_at,
                attempt_count=r.attempt_count,
                created_at=r.created_at,
                completed_at=r.completed_at,
            )
            for r in records
        ]
        return NotificationHistoryResponse(items=items, total=total)


    # ------------------------------------------------------------------ #
    # Admin queue monitor
    # ------------------------------------------------------------------ #

    async def get_queue_admin(
        self,
        *,
        user_id: str,
        tenant_key: str,
        status_code: str | None = None,
        channel_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> QueueAdminResponse:
        _queue_repo_module = import_module("backend.04_notifications.03_queue.repository")
        repo = _queue_repo_module.QueueRepository()

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            rows, total = await repo.list_queue_admin(
                conn,
                tenant_key=tenant_key,
                status_code=status_code,
                channel_code=channel_code,
                limit=limit,
                offset=offset,
            )
            stats_row = await repo.get_queue_stats(conn, tenant_key=tenant_key)

        stats = QueueStatsResponse(
            queued=stats_row["queued"] if stats_row else 0,
            processing=stats_row["processing"] if stats_row else 0,
            sent=stats_row["sent"] if stats_row else 0,
            delivered=stats_row["delivered"] if stats_row else 0,
            failed=stats_row["failed"] if stats_row else 0,
            dead_letter=stats_row["dead_letter"] if stats_row else 0,
            suppressed=stats_row["suppressed"] if stats_row else 0,
        )
        items = [
            QueueItemAdminResponse(
                id=str(r["id"]),
                tenant_key=r["tenant_key"],
                user_id=str(r["user_id"]) if r["user_id"] else None,
                notification_type_code=r["notification_type_code"],
                channel_code=r["channel_code"],
                status_code=r["status_code"],
                priority_code=r["priority_code"],
                template_id=str(r["template_id"]) if r["template_id"] else None,
                source_rule_id=str(r["source_rule_id"]) if r["source_rule_id"] else None,
                broadcast_id=str(r["broadcast_id"]) if r["broadcast_id"] else None,
                rendered_subject=r["rendered_subject"],
                recipient_email=r["recipient_email"],
                scheduled_at=r["scheduled_at"],
                attempt_count=r["attempt_count"],
                max_attempts=r["max_attempts"],
                next_retry_at=r["next_retry_at"],
                last_error=r["last_error"],
                created_at=r["created_at"],
                updated_at=r["updated_at"],
                completed_at=r["completed_at"],
            )
            for r in rows
        ]
        return QueueAdminResponse(stats=stats, items=items, total=total)


    # ------------------------------------------------------------------ #
    # SMTP configuration
    # ------------------------------------------------------------------ #

    async def get_smtp_config(self, *, user_id: str) -> SmtpConfigResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            row = await conn.fetchrow(
                f'SELECT host, port, username, from_email, from_name, use_tls, start_tls'
                f' FROM "{NOTIFICATION_SCHEMA}"."30_fct_smtp_config"'
                f' WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1',
                'default',
            )

        if row:
            return SmtpConfigResponse(
                host=row['host'],
                port=row['port'],
                username=row['username'],
                from_email=row['from_email'],
                from_name=row['from_name'],
                use_tls=row['use_tls'],
                start_tls=row['start_tls'],
                is_configured=True,
                source='db',
            )

        # Fall back to env vars
        s = self._settings
        return SmtpConfigResponse(
            host=s.notification_smtp_host,
            port=s.notification_smtp_port,
            username=s.notification_smtp_user,
            from_email=s.notification_from_email,
            from_name=s.notification_from_name,
            use_tls=s.notification_smtp_use_tls,
            start_tls=s.notification_smtp_start_tls,
            is_configured=bool(s.notification_smtp_host and s.notification_from_email),
            source='env',
        )

    async def save_smtp_config(self, *, user_id: str, request: SmtpConfigRequest) -> SmtpConfigResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.update")
            # If password not provided, fetch existing to preserve it
            password_to_save: str | None
            if request.password is not None:
                password_to_save = self._encrypt_smtp_password(request.password)
            else:
                existing = await conn.fetchval(
                    f'SELECT password FROM "{NOTIFICATION_SCHEMA}"."30_fct_smtp_config"'
                    f' WHERE tenant_key = $1 LIMIT 1',
                    'default',
                )
                password_to_save = existing  # already encrypted (or None on first insert)

            await conn.execute(
                f'''INSERT INTO "{NOTIFICATION_SCHEMA}"."30_fct_smtp_config"
                    (tenant_key, host, port, username, password, from_email, from_name, use_tls, start_tls, is_active, created_at, updated_at, created_by, updated_by)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, NOW(), NOW(), $10, $10)
                    ON CONFLICT (tenant_key) DO UPDATE SET
                        host = EXCLUDED.host,
                        port = EXCLUDED.port,
                        username = EXCLUDED.username,
                        password = EXCLUDED.password,
                        from_email = EXCLUDED.from_email,
                        from_name = EXCLUDED.from_name,
                        use_tls = EXCLUDED.use_tls,
                        start_tls = EXCLUDED.start_tls,
                        updated_at = NOW(),
                        updated_by = $10
                ''',
                'default',
                request.host,
                request.port,
                request.username,
                password_to_save,
                request.from_email,
                request.from_name,
                request.use_tls,
                request.start_tls,
                uuid.UUID(user_id),
            )
        return await self.get_smtp_config(user_id=user_id)

    async def test_smtp(
        self, *, user_id: str, request: SmtpTestRequest
    ) -> SmtpTestResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            db_row = await conn.fetchrow(
                f'SELECT host, port, username, password, from_email, from_name, use_tls, start_tls'
                f' FROM "{NOTIFICATION_SCHEMA}"."30_fct_smtp_config"'
                f' WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1',
                'default',
            )

        s = self._settings
        # DB config takes precedence over env vars; request overrides take highest priority
        db_host = db_row['host'] if db_row else None
        db_port = db_row['port'] if db_row else None
        db_user = db_row['username'] if db_row else None
        _db_pass_raw = db_row['password'] if db_row else None
        db_pass = self._decrypt_smtp_password(_db_pass_raw) if _db_pass_raw else None
        db_from_email = db_row['from_email'] if db_row else None
        db_from_name = db_row['from_name'] if db_row else None
        db_use_tls = db_row['use_tls'] if db_row else None
        db_start_tls = db_row['start_tls'] if db_row else None

        host = request.host or db_host or s.notification_smtp_host
        port = request.port or db_port or s.notification_smtp_port
        username = request.username or db_user or s.notification_smtp_user
        password = request.password or db_pass or s.notification_smtp_password
        from_email = request.from_email or db_from_email or s.notification_from_email
        from_name = request.from_name or db_from_name or s.notification_from_name
        use_tls = request.use_tls if request.use_tls is not None else (db_use_tls if db_use_tls is not None else s.notification_smtp_use_tls)
        start_tls = request.start_tls if request.start_tls is not None else (db_start_tls if db_start_tls is not None else s.notification_smtp_start_tls)

        if not host or not from_email:
            return SmtpTestResponse(
                success=False,
                message="SMTP not configured",
                detail="host and from_email are required",
            )

        _email_module = import_module("backend.04_notifications.04_channels.email_provider")
        EmailProvider = _email_module.EmailProvider
        provider = EmailProvider(
            host=host,
            port=port,
            username=username,
            password=password,
            from_email=from_email,
            from_name=from_name,
            use_tls=use_tls,
            start_tls=start_tls,
        )
        result = await provider.send(
            recipient=request.to_email,
            subject="[K-Control] SMTP Test",
            body_html="<p>This is a test email from K-Control to verify your SMTP configuration is working correctly.</p>",
            body_text="This is a test email from K-Control to verify your SMTP configuration is working correctly.",
        )
        if result.success:
            return SmtpTestResponse(
                success=True,
                message=f"Test email delivered to {request.to_email}",
                detail=result.provider_response,
            )
        return SmtpTestResponse(
            success=False,
            message="SMTP delivery failed",
            detail=result.error_message,
        )

    # ------------------------------------------------------------------ #
    # Send test notification
    # ------------------------------------------------------------------ #

    async def send_test_notification(
        self, *, user_id: str, tenant_key: str, request: SendTestNotificationRequest
    ) -> SendTestNotificationResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            # Load SMTP config from DB (same as test_smtp — DB takes precedence over env)
            db_row = await conn.fetchrow(
                f'SELECT host, port, username, password, from_email, from_name, use_tls, start_tls'
                f' FROM "{NOTIFICATION_SCHEMA}"."30_fct_smtp_config"'
                f' WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1',
                'default',
            )

        if request.channel_code == "email":
            async with self._database_pool.acquire() as conn:
                db_row = await conn.fetchrow(
                    f'SELECT host, port, username, password, from_email, from_name, use_tls, start_tls'
                    f' FROM "{NOTIFICATION_SCHEMA}"."30_fct_smtp_config"'
                    f' WHERE tenant_key = $1 AND is_active = TRUE LIMIT 1',
                    'default',
                )

                # Attempt to find a template for this type
                _template_repo_module = import_module("backend.04_notifications.01_templates.repository")
                template_repo = _template_repo_module.TemplateRepository()
                template = await template_repo.get_template_for_type_channel(
                    conn, request.notification_type_code, request.channel_code, tenant_key
                )
                
                rendered_subject = None
                rendered_html = None
                rendered_text = None
                
                if template and template.active_version_id:
                    version = await template_repo.get_version(conn, template.active_version_id)
                    if version:
                        base_body_html = None
                        if template.base_template_id:
                            base_template = await template_repo.get_template_by_id(conn, template.base_template_id)
                            if base_template and base_template.active_version_id:
                                base_version = await template_repo.get_version(conn, base_template.active_version_id)
                                if base_version:
                                    base_body_html = base_version.body_html
                        
                        _renderer_module = import_module("backend.04_notifications.01_templates.renderer")
                        renderer = _renderer_module.TemplateRenderer()
                        
                        # Merge provided variables with some defaults if useful
                        test_vars = {
                            "user.display_name": "Test User",
                            "user.email": request.to_email,
                            "app.name": self._settings.app_name,
                            **request.variables
                        }
                        
                        rendered = renderer.render_template_version(
                            subject_line=version.subject_line,
                            body_html=version.body_html,
                            body_text=version.body_text,
                            body_short=version.body_short,
                            variables=test_vars,
                            base_body_html=base_body_html
                        )
                        rendered_subject = rendered["subject_line"]
                        rendered_html = rendered["body_html"]
                        rendered_text = rendered["body_text"]

            s = self._settings
            host = (db_row['host'] if db_row else None) or s.notification_smtp_host
            port = (db_row['port'] if db_row else None) or s.notification_smtp_port
            username = (db_row['username'] if db_row else None) or s.notification_smtp_user
            _raw_pass = (db_row['password'] if db_row else None)
            password = (self._decrypt_smtp_password(_raw_pass) if _raw_pass else None) or s.notification_smtp_password
            from_email = (db_row['from_email'] if db_row else None) or s.notification_from_email
            from_name = (db_row['from_name'] if db_row else None) or s.notification_from_name
            use_tls = (db_row['use_tls'] if db_row else None) if db_row else s.notification_smtp_use_tls
            start_tls = (db_row['start_tls'] if db_row else None) if db_row else s.notification_smtp_start_tls

            if not host or not from_email:
                return SendTestNotificationResponse(
                    success=False,
                    message="SMTP not configured — cannot send test email",
                )

            _email_module = import_module("backend.04_notifications.04_channels.email_provider")
            EmailProvider = _email_module.EmailProvider
            provider = EmailProvider(
                host=host,
                port=port,
                username=username,
                password=password,
                from_email=from_email,
                from_name=from_name or "K-Control",
                use_tls=use_tls or False,
                start_tls=start_tls if start_tls is not None else True,
            )
            
            # Use rendered content if available, else fall back to basic test message
            subject = rendered_subject or request.subject or f"[K-Control Test] {request.notification_type_code}"
            body_html = rendered_html or request.body or (
                f"<p>This is a test notification for type <strong>{request.notification_type_code}</strong>.</p>"
                f"<p>Sent from K-Control admin console.</p>"
            )
            body_text = rendered_text or request.body or (
                f"This is a test notification for type {request.notification_type_code}.\n"
                f"Sent from K-Control admin console."
            )

            result = await provider.send(
                recipient=request.to_email,
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
            if result.success:
                return SendTestNotificationResponse(
                    success=True,
                    message=f"Test notification sent to {request.to_email}",
                )
            return SendTestNotificationResponse(
                success=False,
                message=f"Delivery failed: {result.error_message}",
            )

        return SendTestNotificationResponse(
            success=False,
            message=f"Channel '{request.channel_code}' test not supported via this endpoint",
        )

    # ------------------------------------------------------------------ #
    # Reports / analytics
    # ------------------------------------------------------------------ #

    async def get_delivery_report(
        self,
        *,
        user_id: str,
        tenant_key: str,
        period_hours: int = 24,
    ) -> DeliveryReportResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")

            rows = await conn.fetch(
                f"""
                SELECT notification_type_code, channel_code, status_code,
                       total_count::int, hour_bucket::text
                FROM {SCHEMA}.\"40_vw_notification_delivery_summary\"
                WHERE tenant_key = $1
                  AND hour_bucket >= NOW() - ($2 || ' hours')::interval
                ORDER BY hour_bucket DESC, total_count DESC
                """,
                tenant_key,
                str(period_hours),
            )

            funnel_row = await conn.fetchrow(
                f"""
                SELECT
                    COUNT(*) FILTER (WHERE status_code = 'queued') AS queued,
                    COUNT(*) FILTER (WHERE status_code = 'processing') AS processing,
                    COUNT(*) FILTER (WHERE status_code = 'sent') AS sent,
                    COUNT(*) FILTER (WHERE status_code = 'delivered') AS delivered,
                    COUNT(*) FILTER (WHERE status_code = 'opened') AS opened,
                    COUNT(*) FILTER (WHERE status_code = 'clicked') AS clicked,
                    COUNT(*) FILTER (WHERE status_code = 'failed') AS failed,
                    COUNT(*) FILTER (WHERE status_code = 'dead_letter') AS dead_letter,
                    COUNT(*) FILTER (WHERE status_code = 'suppressed') AS suppressed
                FROM {SCHEMA}.\"20_trx_notification_queue\"
                WHERE tenant_key = $1
                  AND created_at >= NOW() - ($2 || ' hours')::interval
                """,
                tenant_key,
                str(period_hours),
            )

        sent = funnel_row["sent"] or 0
        delivered = funnel_row["delivered"] or 0
        opened = funnel_row["opened"] or 0
        clicked = funnel_row["clicked"] or 0
        total_attempted = sent + delivered + opened + clicked + (funnel_row["failed"] or 0) + (funnel_row["dead_letter"] or 0)
        delivery_rate = round(delivered / total_attempted * 100, 1) if total_attempted else 0.0
        open_rate = round(opened / delivered * 100, 1) if delivered else 0.0
        click_rate = round(clicked / opened * 100, 1) if opened else 0.0

        funnel = DeliveryFunnelResponse(
            queued=funnel_row["queued"] or 0,
            processing=funnel_row["processing"] or 0,
            sent=sent,
            delivered=delivered,
            opened=opened,
            clicked=clicked,
            failed=funnel_row["failed"] or 0,
            dead_letter=funnel_row["dead_letter"] or 0,
            suppressed=funnel_row["suppressed"] or 0,
            delivery_rate=delivery_rate,
            open_rate=open_rate,
            click_rate=click_rate,
        )
        report_rows = [
            DeliveryReportRow(
                notification_type_code=r["notification_type_code"],
                channel_code=r["channel_code"],
                status_code=r["status_code"],
                total_count=r["total_count"],
                hour_bucket=r["hour_bucket"],
            )
            for r in rows
        ]
        return DeliveryReportResponse(funnel=funnel, rows=report_rows, period_hours=period_hours)

    # ------------------------------------------------------------------ #
    # Queue management (retry, dead-letter, detail)
    # ------------------------------------------------------------------ #

    async def retry_queue_item(
        self, *, user_id: str, tenant_key: str, notification_id: str
    ) -> QueueActionResponse:
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            _queue_repo_module = import_module("backend.04_notifications.03_queue.repository")
            repo = _queue_repo_module.QueueRepository()
            ok = await repo.retry_notification(conn, notification_id)
            if ok:
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="notification_queue",
                        entity_id=notification_id,
                        event_type="queue_item_retried",
                        event_category="notification",
                        occurred_at=utc_now_sql(),
                        actor_id=user_id,
                    ),
                )
        if ok:
            return QueueActionResponse(success=True, message=f"Notification {notification_id} requeued for retry")
        return QueueActionResponse(success=False, message="Notification not found or not in a retryable state")

    async def dead_letter_queue_item(
        self, *, user_id: str, tenant_key: str, notification_id: str, reason: str | None = None
    ) -> QueueActionResponse:
        effective_reason = reason or "Manually dead-lettered by admin"
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            _queue_repo_module = import_module("backend.04_notifications.03_queue.repository")
            repo = _queue_repo_module.QueueRepository()
            ok = await repo.dead_letter_notification(conn, notification_id, effective_reason)
            if ok:
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="notification_queue",
                        entity_id=notification_id,
                        event_type="queue_item_dead_lettered",
                        event_category="notification",
                        occurred_at=utc_now_sql(),
                        actor_id=user_id,
                        properties={"reason": effective_reason},
                    ),
                )
        if ok:
            return QueueActionResponse(success=True, message=f"Notification {notification_id} moved to dead_letter")
        return QueueActionResponse(success=False, message="Notification not found or already in terminal state")

    async def get_notification_detail(
        self, *, user_id: str, notification_id: str, tenant_key: str
    ) -> NotificationDetailResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            _queue_repo_module = import_module("backend.04_notifications.03_queue.repository")
            repo = _queue_repo_module.QueueRepository()

            row = await conn.fetchrow(
                f"""
                SELECT id, tenant_key, user_id, notification_type_code, channel_code,
                       status_code, priority_code, template_id,
                       source_rule_id, broadcast_id,
                       rendered_subject, recipient_email,
                       scheduled_at::text, attempt_count, max_attempts,
                       next_retry_at::text, last_error,
                       created_at::text, updated_at::text, completed_at::text
                FROM {SCHEMA}.\"20_trx_notification_queue\"
                WHERE id = $1
                """,
                notification_id,
            )
            if not row:
                raise NotFoundError(f"Notification '{notification_id}' not found")

            notification = QueueItemAdminResponse(
                id=str(row["id"]),
                tenant_key=row["tenant_key"],
                user_id=str(row["user_id"]) if row["user_id"] else None,
                notification_type_code=row["notification_type_code"],
                channel_code=row["channel_code"],
                status_code=row["status_code"],
                priority_code=row["priority_code"],
                template_id=str(row["template_id"]) if row["template_id"] else None,
                source_rule_id=str(row["source_rule_id"]) if row["source_rule_id"] else None,
                broadcast_id=str(row["broadcast_id"]) if row["broadcast_id"] else None,
                rendered_subject=row["rendered_subject"],
                recipient_email=row["recipient_email"],
                scheduled_at=row["scheduled_at"],
                attempt_count=row["attempt_count"],
                max_attempts=row["max_attempts"],
                next_retry_at=row["next_retry_at"],
                last_error=row["last_error"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
                completed_at=row["completed_at"],
            )

            log_rows = await repo.get_delivery_logs(conn, notification_id)
            logs = [
                DeliveryLogResponse(
                    id=str(lr["id"]),
                    notification_id=str(lr["notification_id"]),
                    channel_code=lr["channel_code"],
                    attempt_number=lr["attempt_number"],
                    status=lr["status"],
                    provider_response=lr["provider_response"],
                    provider_message_id=lr["provider_message_id"],
                    error_code=lr["error_code"],
                    error_message=lr["error_message"],
                    duration_ms=lr["duration_ms"],
                    occurred_at=lr["occurred_at"],
                    created_at=lr["created_at"],
                )
                for lr in log_rows
            ]

            event_rows = await repo.get_tracking_events(conn, notification_id)
            events = [
                TrackingEventResponse(
                    id=str(er["id"]),
                    notification_id=str(er["notification_id"]),
                    tracking_event_type_code=er["tracking_event_type_code"],
                    channel_code=er["channel_code"],
                    click_url=er["click_url"],
                    user_agent=er["user_agent"],
                    ip_address=er["ip_address"],
                    occurred_at=er["occurred_at"],
                    created_at=er["created_at"],
                )
                for er in event_rows
            ]

        return NotificationDetailResponse(
            notification=notification,
            delivery_logs=logs,
            tracking_events=events,
        )

    # ------------------------------------------------------------------ #
    # User notification inbox
    # ------------------------------------------------------------------ #

    async def get_inbox(
        self,
        *,
        user_id: str,
        tenant_key: str,
        is_read: bool | None = None,
        category_code: str | None = None,
        channel_code: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ):
        _inbox_schemas = import_module("backend.04_notifications.schemas")
        InboxResponse = _inbox_schemas.InboxResponse
        InboxNotificationItem = _inbox_schemas.InboxNotificationItem

        filters = ["user_id = $1", "tenant_key = $2", "status_code IN ('sent', 'delivered', 'opened', 'clicked')"]
        params: list = [user_id, tenant_key]
        p = 3

        if is_read is not None:
            filters.append(f"is_read = ${p}")
            params.append(is_read)
            p += 1
        if category_code:
            filters.append(f"nt.category_code = ${p}")
            params.append(category_code)
            p += 1
        if channel_code:
            filters.append(f"q.channel_code = ${p}")
            params.append(channel_code)
            p += 1

        where = " AND ".join(filters)

        async with self._database_pool.acquire() as conn:
            total_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*) AS cnt
                FROM {SCHEMA}."20_trx_notification_queue" q
                LEFT JOIN {SCHEMA}."04_dim_notification_types" nt
                    ON nt.code = q.notification_type_code
                WHERE {where}
                """,
                *params,
            )
            total = int(total_row["cnt"])

            unread_row = await conn.fetchrow(
                f"""
                SELECT COUNT(*) AS cnt
                FROM {SCHEMA}."20_trx_notification_queue"
                WHERE user_id = $1 AND tenant_key = $2
                  AND status_code IN ('sent', 'delivered', 'opened', 'clicked')
                  AND is_read = FALSE
                """,
                user_id,
                tenant_key,
            )
            unread_count = int(unread_row["cnt"])

            rows = await conn.fetch(
                f"""
                SELECT q.id, q.notification_type_code, nt.category_code,
                       q.channel_code, q.status_code, q.priority_code,
                       q.rendered_subject, q.rendered_body, q.rendered_body_html,
                       q.is_read, q.read_at::text,
                       q.scheduled_at::text, q.completed_at::text,
                       q.created_at::text
                FROM {SCHEMA}."20_trx_notification_queue" q
                LEFT JOIN {SCHEMA}."04_dim_notification_types" nt
                    ON nt.code = q.notification_type_code
                WHERE {where}
                ORDER BY q.created_at DESC
                LIMIT ${p} OFFSET ${p + 1}
                """,
                *params,
                limit,
                offset,
            )

        items = [
            InboxNotificationItem(
                id=str(r["id"]),
                notification_type_code=r["notification_type_code"],
                category_code=r["category_code"],
                channel_code=r["channel_code"],
                status_code=r["status_code"],
                priority_code=r["priority_code"],
                rendered_subject=r["rendered_subject"],
                rendered_body=r["rendered_body"],
                rendered_body_html=r["rendered_body_html"],
                is_read=r["is_read"],
                read_at=r["read_at"],
                scheduled_at=r["scheduled_at"],
                completed_at=r["completed_at"],
                created_at=r["created_at"],
            )
            for r in rows
        ]
        return InboxResponse(items=items, total=total, unread_count=unread_count)

    async def get_unread_count(self, *, user_id: str, tenant_key: str) -> int:
        async with self._database_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT COUNT(*) AS cnt
                FROM {SCHEMA}."20_trx_notification_queue"
                WHERE user_id = $1 AND tenant_key = $2
                  AND status_code IN ('sent', 'delivered', 'opened', 'clicked')
                  AND is_read = FALSE
                """,
                user_id,
                tenant_key,
            )
        return int(row["cnt"])

    async def bulk_retry_queue(
        self,
        *,
        user_id: str,
        tenant_key: str,
        status_filter: str = "failed,dead_letter",
    ) -> QueueActionResponse:
        """Reset all failed/dead_letter notifications back to queued for retry."""
        statuses = [s.strip() for s in status_filter.split(",") if s.strip() in ("failed", "dead_letter")]
        if not statuses:
            return QueueActionResponse(success=False, message="No valid statuses specified")

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            result = await conn.execute(
                f"""
                UPDATE {SCHEMA}."20_trx_notification_queue"
                SET status_code = 'queued',
                    next_retry_at = NULL,
                    last_error = NULL,
                    updated_at = NOW()
                WHERE tenant_key = $1
                  AND status_code = ANY($2::text[])
                """,
                tenant_key,
                statuses,
            )
            # Extract count from "UPDATE N"
            count = int(result.split()[-1]) if result.startswith("UPDATE") else 0

        return QueueActionResponse(
            success=True,
            message=f"Requeued {count} notification(s) for retry",
        )

    async def mark_inbox_read(
        self,
        *,
        user_id: str,
        tenant_key: str,
        notification_ids: list[str],
    ) -> dict:
        """Mark specific notifications (or all if empty list) as read for this user."""
        async with self._database_pool.transaction() as conn:
            if notification_ids:
                await conn.execute(
                    f"""
                    UPDATE {SCHEMA}."20_trx_notification_queue"
                    SET is_read = TRUE, read_at = NOW(), updated_at = NOW()
                    WHERE user_id = $1 AND tenant_key = $2
                      AND id = ANY($3::uuid[])
                      AND is_read = FALSE
                    """,
                    user_id,
                    tenant_key,
                    notification_ids,
                )
            else:
                # Mark all unread as read
                await conn.execute(
                    f"""
                    UPDATE {SCHEMA}."20_trx_notification_queue"
                    SET is_read = TRUE, read_at = NOW(), updated_at = NOW()
                    WHERE user_id = $1 AND tenant_key = $2 AND is_read = FALSE
                    """,
                    user_id,
                    tenant_key,
                )
        return {"success": True}


def _preference_response(r) -> PreferenceResponse:
    return PreferenceResponse(
        id=r["id"],
        user_id=r["user_id"],
        tenant_key=r["tenant_key"],
        scope_level=r["scope_level"],
        channel_code=r["channel_code"],
        category_code=r["category_code"],
        notification_type_code=r["notification_type_code"],
        scope_org_id=r["scope_org_id"],
        scope_workspace_id=r["scope_workspace_id"],
        is_enabled=r["is_enabled"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _subscription_response(r) -> WebPushSubscriptionResponse:
    return WebPushSubscriptionResponse(
        id=r["id"],
        user_id=r["user_id"],
        tenant_key=r["tenant_key"],
        endpoint=r["endpoint"],
        is_active=r["is_active"],
        last_used_at=r["last_used_at"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


