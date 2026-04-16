from __future__ import annotations

import uuid
from importlib import import_module

from .repository import BroadcastRepository
from ..schemas import (
    BroadcastListResponse,
    BroadcastResponse,
    CreateBroadcastRequest,
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
_constants_module = import_module("backend.04_notifications.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
BroadcastScope = _constants_module.BroadcastScope
NotificationChannel = _constants_module.NotificationChannel
NotificationStatus = _constants_module.NotificationStatus
NotificationType = _constants_module.NotificationType

_CACHE_TTL_BROADCASTS = 300  # 5 minutes

_AUDIT_ENTITY_TYPE = "broadcast"
_AUDIT_EVENT_CATEGORY = "notification"


@instrument_class_methods(namespace="broadcasts.service", logger_name="backend.notifications.broadcasts.instrumentation")
class BroadcastService:
    def __init__(
        self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = BroadcastRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.notifications.broadcasts")

    async def list_broadcasts(
        self, *, user_id: str, tenant_key: str, limit: int = 50, offset: int = 0
    ) -> BroadcastListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.view")
            broadcasts, total = await self._repository.list_broadcasts(conn, tenant_key, limit=limit, offset=offset)
        return BroadcastListResponse(items=[_broadcast_response(b) for b in broadcasts], total=total)

    async def create_broadcast(
        self, *, user_id: str, tenant_key: str, request: CreateBroadcastRequest
    ) -> BroadcastResponse:
        now = utc_now_sql()
        broadcast_id = str(uuid.uuid4())
        notification_type_code = request.notification_type_code or NotificationType.GLOBAL_BROADCAST
        priority_code = request.priority_code or "normal"

        # Critical broadcasts auto-escalate priority
        if request.is_critical and priority_code not in ("critical", "high"):
            priority_code = "high"

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.create")
            import json as _json
            broadcast = await self._repository.create_broadcast(
                conn,
                broadcast_id=broadcast_id,
                tenant_key=tenant_key,
                title=request.title,
                body_text=request.body_text,
                body_html=request.body_html,
                scope=request.scope,
                scope_org_id=request.scope_org_id,
                scope_workspace_id=request.scope_workspace_id,
                notification_type_code=notification_type_code,
                priority_code=priority_code,
                severity=request.severity,
                is_critical=request.is_critical,
                template_code=request.template_code,
                static_variables=_json.dumps(request.static_variables) if request.static_variables else None,
                scheduled_at=request.scheduled_at,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=broadcast_id,
                    event_type="broadcast_created",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "title": request.title,
                        "scope": request.scope,
                        "notification_type_code": notification_type_code,
                        "is_critical": str(request.is_critical),
                        "severity": request.severity or "",
                    },
                ),
            )
        await self._cache.delete_pattern("broadcasts:list:*")
        return _broadcast_response(broadcast)

    async def send_broadcast(
        self, *, user_id: str, broadcast_id: str
    ) -> BroadcastResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_broadcasts.create")

            broadcast = await self._repository.get_broadcast_by_id(conn, broadcast_id)
            if broadcast is None:
                raise NotFoundError(f"Broadcast '{broadcast_id}' not found")
            if broadcast.sent_at is not None:
                raise ConflictError(f"Broadcast '{broadcast_id}' has already been sent")

            # Resolve recipients based on scope
            recipients = await self._resolve_recipients(conn, broadcast)

            # Resolve available channels for this notification type (multi-channel)
            channels = await self._repository.resolve_channels_for_type(
                conn, broadcast.notification_type_code
            )
            if not channels:
                channels = [{"channel_code": NotificationChannel.EMAIL, "priority_code": broadcast.priority_code}]

            # Personalize and build queue entries per recipient per channel
            renderer = self._get_renderer()

            # --- Batch pre-fetch all recipient data to avoid N+1 queries ---
            all_user_ids = [str(r["user_id"]) for r in recipients]

            # Batch fetch user properties for all recipients
            prop_rows = await conn.fetch(
                """
                SELECT user_id::text, property_key, property_value
                FROM "03_auth_manage"."05_dtl_user_properties"
                WHERE user_id = ANY($1)
                  AND property_key = ANY($2)
                """,
                all_user_ids,
                ["display_name", "email", "first_name", "last_name", "username"],
            )
            user_props: dict[str, dict[str, str]] = {}
            for r in prop_rows:
                uid = r["user_id"]
                if uid not in user_props:
                    user_props[uid] = {}
                user_props[uid][f"user.{r['property_key']}"] = r["property_value"] or ""

            # Batch fetch emails for all recipients (needed for EMAIL channel)
            email_map: dict[str, str] = {}
            needs_email = any(ch["channel_code"] == NotificationChannel.EMAIL for ch in channels)
            if needs_email:
                email_rows = await conn.fetch(
                    """
                    SELECT user_id::text, property_value
                    FROM "03_auth_manage"."05_dtl_user_properties"
                    WHERE user_id = ANY($1)
                      AND property_key = 'email'
                      AND property_value IS NOT NULL
                    """,
                    all_user_ids,
                )
                email_map = {r["user_id"]: r["property_value"] for r in email_rows}

            # Resolve org name once (same for all recipients)
            org_name = None
            if broadcast.scope_org_id:
                org_row = await conn.fetchrow(
                    """SELECT name FROM "03_auth_manage"."29_fct_orgs" WHERE id = $1""",
                    broadcast.scope_org_id,
                )
                if org_row:
                    org_name = org_row["name"]

            # Base variables (shared across all recipients)
            base_variables: dict[str, str] = {
                "broadcast.title": broadcast.title,
                "broadcast.body": broadcast.body_text,
            }
            if org_name:
                base_variables["org.name"] = org_name
            if hasattr(self._settings, "notification_from_name"):
                base_variables["platform.name"] = self._settings.notification_from_name or "kcontrol"
            else:
                base_variables["platform.name"] = "kcontrol"
            static_vars = getattr(broadcast, "static_variables", None)
            if static_vars and isinstance(static_vars, dict):
                base_variables.update(static_vars)

            entries = []
            for recipient in recipients:
                recipient_user_id = str(recipient["user_id"])

                # Build per-recipient variables from pre-fetched data
                variables = {**base_variables}
                variables.update(user_props.get(recipient_user_id, {}))

                # Render personalized content
                rendered_subject = renderer.render(broadcast.title, variables)
                rendered_body = renderer.render(
                    broadcast.body_html or broadcast.body_text, variables
                )

                for ch in channels:
                    channel_code = ch["channel_code"]
                    channel_priority = ch["priority_code"] if not broadcast.is_critical else "critical"

                    # Resolve delivery address from pre-fetched maps
                    recipient_email = None
                    recipient_push = None
                    if channel_code == NotificationChannel.EMAIL:
                        recipient_email = email_map.get(recipient_user_id)
                        if not recipient_email:
                            continue
                    elif channel_code == NotificationChannel.WEB_PUSH:
                        recipient_push = await self._repository.resolve_recipient_push_endpoint(
                            conn, recipient_user_id
                        )
                        if not recipient_push:
                            continue

                    entries.append((
                        str(uuid.uuid4()),
                        broadcast.tenant_key,
                        recipient_user_id,
                        broadcast.notification_type_code,
                        channel_code,
                        NotificationStatus.QUEUED,
                        channel_priority,
                        broadcast_id,
                        rendered_subject,
                        rendered_body,
                        recipient_email,
                        recipient_push,
                        broadcast.scheduled_at or now,
                        now,
                        now,
                    ))

            total_recipients = len(entries)
            if entries:
                await self._repository.insert_queue_entries(conn, entries)

            await self._repository.update_broadcast_sent(
                conn, broadcast_id, total_recipients, now
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=broadcast.tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=broadcast_id,
                    event_type="broadcast_sent",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "total_recipients": str(total_recipients),
                        "scope": broadcast.scope,
                        "is_critical": str(broadcast.is_critical),
                    },
                ),
            )

        await self._cache.delete_pattern("broadcasts:list:*")

        # Re-fetch the updated broadcast
        async with self._database_pool.acquire() as conn:
            updated = await self._repository.get_broadcast_by_id(conn, broadcast_id)
        return _broadcast_response(updated)

    async def _resolve_recipients(self, conn, broadcast):
        """Resolve recipients based on broadcast scope."""
        scope = broadcast.scope
        if scope == BroadcastScope.GLOBAL:
            return await self._repository.resolve_global_recipients(conn, broadcast.tenant_key)
        elif scope == BroadcastScope.ORG:
            if broadcast.scope_org_id is None:
                raise NotFoundError("Broadcast scope is 'org' but scope_org_id is not set")
            return await self._repository.resolve_org_recipients(conn, broadcast.scope_org_id)
        elif scope == BroadcastScope.WORKSPACE:
            if broadcast.scope_workspace_id is None:
                raise NotFoundError("Broadcast scope is 'workspace' but scope_workspace_id is not set")
            return await self._repository.resolve_workspace_recipients(conn, broadcast.scope_workspace_id)
        return []

    async def _resolve_broadcast_variables(self, conn, broadcast, recipient_user_id: str) -> dict[str, str]:
        """Resolve per-recipient template variables for broadcast personalization.

        Priority: static_variables (admin-set) > per-recipient resolution > defaults.
        """
        variables: dict[str, str] = {
            "broadcast.title": broadcast.title,
            "broadcast.body": broadcast.body_text,
        }

        # Resolve recipient user properties
        rows = await conn.fetch(
            """
            SELECT property_key, property_value
            FROM "03_auth_manage"."05_dtl_user_properties"
            WHERE user_id = $1
              AND property_key = ANY($2)
            """,
            recipient_user_id,
            ["display_name", "email", "first_name", "last_name", "username"],
        )
        for r in rows:
            variables[f"user.{r['property_key']}"] = r["property_value"] or ""

        # Resolve org name if broadcast is org-scoped
        if broadcast.scope_org_id:
            org_row = await conn.fetchrow(
                """SELECT name FROM "03_auth_manage"."29_fct_orgs" WHERE id = $1""",
                broadcast.scope_org_id,
            )
            if org_row:
                variables["org.name"] = org_row["name"]

        # Platform name from settings
        if hasattr(self._settings, "notification_from_name"):
            variables["platform.name"] = self._settings.notification_from_name or "kcontrol"
        else:
            variables["platform.name"] = "kcontrol"

        # Apply static variables (admin-set) — these override per-recipient values
        static_vars = getattr(broadcast, "static_variables", None)
        if static_vars and isinstance(static_vars, dict):
            variables.update(static_vars)

        return variables

    @staticmethod
    def _get_renderer():
        """Lazy import template renderer."""
        _renderer_module = import_module("backend.04_notifications.01_templates.renderer")
        return _renderer_module.TemplateRenderer()

    # ------------------------------------------------------------------ #
    # Org-scoped broadcast operations (org membership auth, not platform perm)
    # ------------------------------------------------------------------ #

    async def _require_org_member(self, conn, user_id: str, org_id: str) -> None:
        """Assert the user is an active member of the given org."""
        AuthorizationError = import_module("backend.01_core.errors").AuthorizationError
        row = await conn.fetchrow(
            """
            SELECT 1
            FROM "03_auth_manage"."31_lnk_org_memberships"
            WHERE org_id = $1 AND user_id = $2
              AND is_active = TRUE AND is_deleted = FALSE
            LIMIT 1
            """,
            org_id, user_id,
        )
        if row is None:
            raise AuthorizationError("You are not a member of this organization")

    async def list_org_broadcasts(
        self, *, user_id: str, org_id: str, tenant_key: str
    ) -> list[BroadcastResponse]:
        """List broadcasts scoped to the given org (org member auth)."""
        async with self._database_pool.acquire() as conn:
            await self._require_org_member(conn, user_id, org_id)
            broadcasts = await self._repository.list_broadcasts_for_org(conn, tenant_key, org_id)
        return [_broadcast_response(b) for b in broadcasts]

    async def create_org_broadcast(
        self, *, user_id: str, org_id: str, tenant_key: str, request: "CreateBroadcastRequest"
    ) -> "BroadcastResponse":
        """Create a broadcast scoped to the given org (org member auth, owner/admin only)."""
        now = utc_now_sql()
        broadcast_id = str(uuid.uuid4())
        notification_type_code = request.notification_type_code or NotificationType.GLOBAL_BROADCAST
        priority_code = request.priority_code or "normal"
        if request.is_critical and priority_code not in ("critical", "high"):
            priority_code = "high"

        async with self._database_pool.transaction() as conn:
            await self._require_org_member(conn, user_id, org_id)
            # Force scope to org and pin scope_org_id
            broadcast = await self._repository.create_broadcast(
                conn,
                broadcast_id=broadcast_id,
                tenant_key=tenant_key,
                title=request.title,
                body_text=request.body_text,
                body_html=request.body_html,
                scope=BroadcastScope.ORG,
                scope_org_id=org_id,
                scope_workspace_id=None,
                notification_type_code=notification_type_code,
                priority_code=priority_code,
                severity=request.severity,
                is_critical=request.is_critical,
                template_code=request.template_code,
                scheduled_at=request.scheduled_at,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=broadcast_id,
                    event_type="broadcast_created",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "title": request.title,
                        "scope": BroadcastScope.ORG,
                        "scope_org_id": org_id,
                        "notification_type_code": notification_type_code,
                        "is_critical": str(request.is_critical),
                        "severity": request.severity or "",
                    },
                ),
            )
        await self._cache.delete_pattern("broadcasts:list:*")
        return _broadcast_response(broadcast)

    async def send_org_broadcast(
        self, *, user_id: str, org_id: str, broadcast_id: str
    ) -> "BroadcastResponse":
        """Send an org-scoped broadcast (org member auth)."""
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._require_org_member(conn, user_id, org_id)

            broadcast = await self._repository.get_broadcast_by_id(conn, broadcast_id)
            if broadcast is None:
                raise import_module("backend.01_core.errors").NotFoundError(
                    f"Broadcast '{broadcast_id}' not found"
                )
            if str(broadcast.scope_org_id) != str(org_id):
                raise import_module("backend.01_core.errors").AuthorizationError(
                    "Broadcast does not belong to this organization"
                )
            if broadcast.sent_at is not None:
                raise import_module("backend.01_core.errors").ConflictError(
                    f"Broadcast '{broadcast_id}' has already been sent"
                )

            recipients = await self._repository.resolve_org_recipients(conn, org_id)
            channels = await self._repository.resolve_channels_for_type(
                conn, broadcast.notification_type_code
            )
            if not channels:
                channels = [{"channel_code": NotificationChannel.EMAIL, "priority_code": broadcast.priority_code}]

            renderer = self._get_renderer()
            entries = []
            for recipient in recipients:
                recipient_user_id = str(recipient["user_id"])
                variables = await self._resolve_broadcast_variables(conn, broadcast, recipient_user_id)
                rendered_subject = renderer.render(broadcast.title, variables)
                rendered_body = renderer.render(broadcast.body_html or broadcast.body_text, variables)

                for ch in channels:
                    channel_code = ch["channel_code"]
                    channel_priority = ch["priority_code"] if not broadcast.is_critical else "critical"
                    recipient_email = None
                    recipient_push = None
                    if channel_code == NotificationChannel.EMAIL:
                        recipient_email = await self._repository.resolve_recipient_email(conn, recipient_user_id)
                        if not recipient_email:
                            continue
                    elif channel_code == NotificationChannel.WEB_PUSH:
                        recipient_push = await self._repository.resolve_recipient_push_endpoint(conn, recipient_user_id)
                        if not recipient_push:
                            continue
                    entries.append((
                        str(uuid.uuid4()), broadcast.tenant_key, recipient_user_id,
                        broadcast.notification_type_code, channel_code,
                        NotificationStatus.QUEUED, channel_priority, broadcast_id,
                        rendered_subject, rendered_body,
                        recipient_email, recipient_push,
                        broadcast.scheduled_at or now, now, now,
                    ))

            total_recipients = len(entries)
            if entries:
                await self._repository.insert_queue_entries(conn, entries)
            await self._repository.update_broadcast_sent(conn, broadcast_id, total_recipients, now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=broadcast.tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=broadcast_id,
                    event_type="broadcast_sent",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "total_recipients": str(total_recipients),
                        "scope": BroadcastScope.ORG,
                        "scope_org_id": org_id,
                        "is_critical": str(broadcast.is_critical),
                    },
                ),
            )

        await self._cache.delete_pattern("broadcasts:list:*")
        async with self._database_pool.acquire() as conn:
            updated = await self._repository.get_broadcast_by_id(conn, broadcast_id)
        return _broadcast_response(updated)


def _broadcast_response(b) -> BroadcastResponse:
    return BroadcastResponse(
        id=b.id,
        tenant_key=b.tenant_key,
        title=b.title,
        body_text=b.body_text,
        body_html=b.body_html,
        scope=b.scope,
        scope_org_id=b.scope_org_id,
        scope_workspace_id=b.scope_workspace_id,
        notification_type_code=b.notification_type_code,
        priority_code=b.priority_code,
        severity=b.severity,
        is_critical=b.is_critical,
        template_code=b.template_code,
        static_variables=b.static_variables or {},
        scheduled_at=b.scheduled_at,
        sent_at=b.sent_at,
        total_recipients=b.total_recipients,
        is_active=b.is_active,
        created_at=b.created_at,
        updated_at=b.updated_at,
        created_by=b.created_by,
    )
