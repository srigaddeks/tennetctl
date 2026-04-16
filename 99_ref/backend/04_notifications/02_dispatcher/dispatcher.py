from __future__ import annotations

import uuid
from importlib import import_module

import asyncpg

_constants_module = import_module("backend.04_notifications.constants")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_audit_module = import_module("backend.01_core.audit")
_time_module = import_module("backend.01_core.time_utils")

NOTIFICATION_SCHEMA = _constants_module.NOTIFICATION_SCHEMA
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
AuditEntry = _audit_module.AuditEntry
utc_now_sql = _time_module.utc_now_sql

from .preference_checker import PreferenceChecker
from .recipient_resolver import RecipientResolver
from .variable_resolver import VariableResolver

SCHEMA = f'"{NOTIFICATION_SCHEMA}"'
AUTH_SCHEMA = '"03_auth_manage"'

_LOGGER = get_logger("backend.notifications.dispatcher")


def _build_mention_fallback(
    audit_entry: "AuditEntry",
    author_display_name: str,
) -> tuple[str, str, str]:
    """Return (subject, body_html, body_text) for the legacy mention-style fallback."""
    entity_type = audit_entry.properties.get("entity_type", "item")
    subject = f"You were mentioned in a comment by {author_display_name}"
    body_html = (
        f"<p><strong>{author_display_name}</strong> mentioned you in a comment "
        f"on a {entity_type}.</p>"
        f"<p>View the full comment in the platform.</p>"
    )
    body_text = (
        f"{author_display_name} mentioned you in a comment on a {entity_type}.\n\n"
        f"View the full comment in the platform."
    )
    return subject, body_html, body_text


@instrument_class_methods(
    namespace="notifications.dispatcher",
    logger_name="backend.notifications.dispatcher.instrumentation",
)
class NotificationDispatcher:
    """Processes audit events into notification queue entries."""

    def __init__(
        self,
        *,
        schema_name: str = "03_notifications",
        settings: object | None = None,
        database_pool: object | None = None,
    ) -> None:
        self._schema = f'"{schema_name}"'
        self._settings = settings
        self._database_pool = database_pool
        self._preference_checker = PreferenceChecker()
        self._recipient_resolver = RecipientResolver()
        self._variable_resolver = VariableResolver()

        _renderer_module = import_module("backend.04_notifications.01_templates.renderer")
        self._renderer = _renderer_module.TemplateRenderer()

    async def process_audit_event(
        self,
        connection: asyncpg.Connection,
        audit_entry: AuditEntry,
    ) -> list[str]:
        """Process an audit event and create notification queue entries.

        Returns list of created notification IDs.
        """
        rules = await self._find_matching_rules(connection, audit_entry)
        if not rules:
            return []

        notification_ids: list[str] = []
        now = utc_now_sql()

        for rule in rules:
            recipients = await self._recipient_resolver.resolve(
                connection,
                strategy=rule["recipient_strategy"],
                audit_entry=audit_entry,
                filter_json=rule["recipient_filter_json"],
            )
            if not recipients:
                continue

            channels = await self._get_rule_channels(connection, rule)
            if not channels:
                continue

            # Look up the category_code and dispatch_immediately flag for this notification type
            category_code, dispatch_immediately = await self._get_type_meta(
                connection, rule["notification_type_code"]
            )

            # Check rule conditions (campaign conditions like inactivity, engagement)
            if not await self._evaluate_rule_conditions(connection, rule["id"]):
                continue

            for user_id in recipients:
                # Resolve template variables per-recipient for personalization
                variables = await self._variable_resolver.resolve_all(
                    connection,
                    audit_entry=audit_entry,
                    recipient_user_id=user_id,
                    settings=self._settings,
                    template_id=None,  # Resolved after template lookup
                )

                for channel_row in channels:
                    channel_code = channel_row["channel_code"]

                    # Check user preference
                    enabled = await self._preference_checker.is_enabled(
                        connection,
                        user_id=user_id,
                        tenant_key=audit_entry.tenant_key,
                        notification_type_code=rule["notification_type_code"],
                        channel_code=channel_code,
                        category_code=category_code or "",
                        org_id=audit_entry.properties.get("org_id"),
                        workspace_id=audit_entry.properties.get("workspace_id"),
                    )
                    if not enabled:
                        continue

                    # Check cooldown — skipped for dispatch_immediately types (transactional/OTP must always send)
                    if not dispatch_immediately and rule["delay_seconds"] and rule["delay_seconds"] > 0:
                        in_cooldown = await self._check_cooldown(
                            connection,
                            user_id=user_id,
                            notification_type_code=rule["notification_type_code"],
                            channel_code=channel_code,
                            cooldown_seconds=rule["delay_seconds"],
                        )
                        if in_cooldown:
                            continue

                    # Idempotency key prevents duplicate notifications
                    idempotency_key = (
                        f"{user_id}:{rule['notification_type_code']}"
                        f":{audit_entry.id}:{channel_code}"
                    )

                    # Resolve template and render
                    template_code = channel_row["template_code"]
                    rendered_subject: str | None = None
                    rendered_body: str | None = None
                    rendered_body_html: str | None = None
                    template_id: str | None = None
                    template_version_id: str | None = None

                    template_data = await self._resolve_template(
                        connection,
                        rule=rule,
                        channel_code=channel_code,
                        tenant_key=audit_entry.tenant_key,
                        template_code_override=template_code,
                    )
                    if template_data:
                        template_id = template_data["template_id"]
                        template_version_id = template_data["version_id"]

                        # Re-resolve variables scoped to this template's placeholders
                        template_variables = await self._variable_resolver.resolve_all(
                            connection,
                            audit_entry=audit_entry,
                            recipient_user_id=user_id,
                            settings=self._settings,
                            template_id=template_id,
                        )

                        # Merge template static_variables as lowest-priority defaults
                        # (dynamic resolution overrides statics)
                        import json as _json
                        _static_json = template_data.get("static_variables_json") or "{}"
                        try:
                            _static_vars: dict = _json.loads(_static_json) if isinstance(_static_json, str) else {}
                        except Exception:
                            _static_vars = {}
                        merged_variables = {**_static_vars, **template_variables}

                        # Inject one-click unsubscribe URL for email channel
                        if channel_code == "email" and category_code and user_id:
                            _unsub_mod = import_module("backend.04_notifications.11_unsubscribe.tokens")
                            _unsub_secret = getattr(self._settings, "notification_unsubscribe_secret", "")
                            _tracking_base = getattr(self._settings, "notification_tracking_base_url", "") or ""
                            if _unsub_secret and _tracking_base:
                                _unsub_token = _unsub_mod.generate_token(user_id, category_code, _unsub_secret)
                                merged_variables.setdefault(
                                    "unsubscribe_url",
                                    f"{_tracking_base}/api/v1/notifications/unsubscribe?token={_unsub_token}",
                                )

                        rendered = self._renderer.render_template_version(
                            subject_line=template_data.get("subject_line"),
                            body_html=template_data.get("body_html"),
                            body_text=template_data.get("body_text"),
                            body_short=template_data.get("body_short"),
                            variables=merged_variables,
                            base_body_html=template_data.get("base_body_html"),
                        )
                        rendered_subject = rendered.get("subject_line")
                        rendered_body_html = rendered.get("body_html")
                        rendered_body = rendered_body_html or rendered.get("body_text")

                    # Resolve recipient email for email channel
                    recipient_email: str | None = None
                    recipient_push_endpoint: str | None = None
                    if channel_code == "email":
                        recipient_email = await self._resolve_recipient_email(
                            connection, user_id
                        )
                    elif channel_code == "web_push":
                        recipient_push_endpoint = await self._resolve_push_endpoint(
                            connection, user_id, audit_entry.tenant_key
                        )

                    # Compute scheduled_at and effective priority
                    # dispatch_immediately (transactional/security types) overrides delay and forces critical priority
                    if dispatch_immediately:
                        scheduled_at = now
                        effective_priority_code = "critical"
                    else:
                        scheduled_at = now
                        if rule["delay_seconds"] and rule["delay_seconds"] > 0:
                            from datetime import timedelta

                            scheduled_at = now + timedelta(seconds=rule["delay_seconds"])
                        effective_priority_code = rule["priority_code"]

                    notification_id = str(uuid.uuid4())

                    _source_env = getattr(self._settings, "environment", "development") if self._settings else "development"
                    result = await connection.execute(
                        f"""
                        INSERT INTO {self._schema}."20_trx_notification_queue" (
                            id, tenant_key, user_id, notification_type_code, channel_code,
                            status_code, priority_code, template_id, template_version_id,
                            source_audit_event_id, source_rule_id,
                            rendered_subject, rendered_body, rendered_body_html,
                            recipient_email, recipient_push_endpoint,
                            scheduled_at,
                            attempt_count, max_attempts, idempotency_key,
                            source_env,
                            created_at, updated_at
                        ) VALUES (
                            $1, $2, $3, $4, $5,
                            'queued', $6, $7, $8,
                            $9, $10,
                            $11, $12, $21,
                            $13, $14,
                            $15,
                            0, $16, $17,
                            $18,
                            $19, $20
                        )
                        ON CONFLICT (idempotency_key)
                            WHERE idempotency_key IS NOT NULL
                            DO NOTHING
                        """,
                        notification_id,           # $1
                        audit_entry.tenant_key,    # $2
                        user_id,                   # $3
                        rule["notification_type_code"],  # $4
                        channel_code,              # $5
                        effective_priority_code,   # $6
                        template_id,               # $7
                        template_version_id,       # $8
                        audit_entry.id,            # $9
                        rule["id"],                # $10
                        rendered_subject,          # $11
                        rendered_body,             # $12
                        recipient_email,           # $13
                        recipient_push_endpoint,   # $14
                        scheduled_at,              # $15
                        5 if dispatch_immediately else 3,  # $16 max_attempts
                        idempotency_key,           # $17
                        _source_env,               # $18
                        now,                       # $19
                        now,                       # $20
                        rendered_body_html,        # $21
                    )

                    # ON CONFLICT DO NOTHING returns "INSERT 0 0" when skipped
                    if result != "INSERT 0 0":
                        notification_ids.append(notification_id)

        _LOGGER.info(
            "audit_event_processed",
            extra={
                "action": "process_audit_event",
                "outcome": "success",
                "audit_entry_id": audit_entry.id,
                "event_type": audit_entry.event_type,
                "rules_matched": len(rules),
                "notifications_created": len(notification_ids),
            },
        )
        return notification_ids

    async def dispatch_direct(
        self,
        audit_entry: AuditEntry,
        *,
        target_user_id: str,
        template_code: str | None = None,
        notification_type_code: str | None = None,
    ) -> list[str]:
        """Queue a notification directly for a specific user, bypassing rules.

        This is used for targeted notifications like @mention emails where the
        recipient is already known and rule-matching is not needed.  The method
        inserts one queue entry per available channel (currently email only) and
        returns the created notification IDs.

        When ``template_code`` is provided the named template is fetched and
        rendered via the variable resolver (same pipeline as
        ``dispatch_transactional``).  Without it the legacy mention-style
        subject/body is used as a fallback.

        Requires ``self._database_pool`` to be set.
        """
        if self._database_pool is None:
            _LOGGER.warning(
                "dispatch_direct_no_pool",
                extra={
                    "action": "dispatch_direct",
                    "outcome": "skipped",
                    "reason": "database_pool not provided",
                },
            )
            return []

        notification_ids: list[str] = []
        now = utc_now_sql()

        try:
            async with self._database_pool.transaction() as conn:
                # Resolve recipient email
                recipient_email = await self._resolve_recipient_email(conn, target_user_id)
                if not recipient_email:
                    _LOGGER.info(
                        "dispatch_direct_no_email",
                        extra={
                            "action": "dispatch_direct",
                            "outcome": "skipped",
                            "target_user_id": target_user_id,
                        },
                    )
                    return []

                # Resolve author display name (used by both template and legacy paths)
                author_display_name = await self._resolve_display_name(
                    conn, audit_entry.actor_id
                )

                if template_code:
                    # Template-aware path — fetch, resolve variables, render
                    template_row = await conn.fetchrow(
                        f"""
                        SELECT t.id AS template_id, v.id AS version_id,
                               v.subject_line, v.body_html, v.body_text, v.body_short,
                               bt_v.body_html AS base_body_html,
                               t.static_variables::text AS static_variables_json
                        FROM {self._schema}."10_fct_templates" t
                        JOIN {self._schema}."14_dtl_template_versions" v
                            ON v.id = t.active_version_id
                        LEFT JOIN {self._schema}."10_fct_templates" bt
                            ON bt.id = t.base_template_id
                            AND bt.is_active = TRUE AND bt.is_deleted = FALSE
                        LEFT JOIN {self._schema}."14_dtl_template_versions" bt_v
                            ON bt_v.id = bt.active_version_id
                        WHERE t.code = $1
                          AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                          AND t.is_active = TRUE AND t.is_deleted = FALSE
                        ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                        LIMIT 1
                        """,
                        template_code,
                        audit_entry.tenant_key,
                    )
                    variables = await self._variable_resolver.resolve_all(
                        conn,
                        audit_entry=audit_entry,
                        recipient_user_id=target_user_id,
                        settings=self._settings,
                        template_id=template_row["template_id"] if template_row else None,
                    )
                    if template_row:
                        import json as _json
                        _static_vars: dict = {}
                        if template_row.get("static_variables_json"):
                            try:
                                _static_vars = _json.loads(template_row["static_variables_json"]) or {}
                            except Exception:
                                pass
                        rendered = self._renderer.render_template_version(
                            subject_line=template_row.get("subject_line"),
                            body_html=template_row.get("body_html"),
                            body_text=template_row.get("body_text"),
                            body_short=template_row.get("body_short"),
                            variables={**_static_vars, **variables},
                            base_body_html=template_row.get("base_body_html"),
                        )
                        subject = rendered.get("subject_line") or ""
                        body_html = rendered.get("body_html") or ""
                        body_text = rendered.get("body_text") or ""
                    else:
                        _LOGGER.warning(
                            "dispatch_direct_template_not_found",
                            extra={
                                "template_code": template_code,
                                "event_type": audit_entry.event_type,
                            },
                        )
                        subject, body_html, body_text = _build_mention_fallback(
                            audit_entry, author_display_name
                        )
                else:
                    # Legacy mention-style fallback
                    subject, body_html, body_text = _build_mention_fallback(
                        audit_entry, author_display_name
                    )

                # Idempotency key to prevent duplicates
                idempotency_key = (
                    f"{target_user_id}:{audit_entry.event_type}"
                    f":{audit_entry.id}:email"
                )

                notification_id = str(uuid.uuid4())

                _source_env = getattr(self._settings, "environment", "development") if self._settings else "development"
                result = await conn.execute(
                    f"""
                    INSERT INTO {self._schema}."20_trx_notification_queue" (
                        id, tenant_key, user_id, notification_type_code, channel_code,
                        status_code, priority_code,
                        source_audit_event_id,
                        rendered_subject, rendered_body, rendered_body_html,
                        recipient_email,
                        scheduled_at,
                        attempt_count, max_attempts, idempotency_key,
                        source_env,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5,
                        'queued', 'normal',
                        $6,
                        $7, $8, $9,
                        $10,
                        $11,
                        0, 3, $12,
                        $13,
                        $14, $15
                    )
                    ON CONFLICT (idempotency_key)
                        WHERE idempotency_key IS NOT NULL
                        DO NOTHING
                    """,
                    notification_id,                              # $1
                    audit_entry.tenant_key,                       # $2
                    target_user_id,                               # $3
                    notification_type_code or audit_entry.event_type,  # $4
                    "email",                                      # $5
                    audit_entry.id,                               # $6
                    subject,                                      # $7
                    body_text,                                    # $8 rendered_body (plain text)
                    body_html,                                    # $9 rendered_body_html (HTML)
                    recipient_email,                              # $10
                    now,                                          # $11
                    idempotency_key,                              # $12
                    _source_env,                                  # $13
                    now,                                          # $14
                    now,                                          # $15
                )

                if result != "INSERT 0 0":
                    notification_ids.append(notification_id)

        except Exception as exc:
            _LOGGER.warning(
                "dispatch_direct_failed",
                extra={
                    "action": "dispatch_direct",
                    "outcome": "error",
                    "target_user_id": target_user_id,
                    "event_type": audit_entry.event_type,
                    "error": str(exc),
                },
            )

        return notification_ids

    async def dispatch_to_email(
        self,
        *,
        recipient_email: str,
        notification_type_code: str,
        subject: str,
        body_html: str,
        body_text: str,
        tenant_key: str,
        idempotency_key: str | None = None,
        priority_code: str = "high",
        source_audit_event_id: str | None = None,
    ) -> str | None:
        """Queue a notification directly to an email address (no user_id required).

        Used for transactional emails where the recipient may not yet have an account
        (e.g. magic link login for a new email address).

        Requires ``self._database_pool`` to be set.
        Returns the created notification ID, or None if skipped/failed.
        """
        if self._database_pool is None:
            _LOGGER.warning(
                "dispatch_to_email_no_pool",
                extra={"action": "dispatch_to_email", "outcome": "skipped"},
            )
            return None

        now = utc_now_sql()
        notification_id = str(uuid.uuid4())

        try:
            async with self._database_pool.transaction() as conn:
                _source_env = getattr(self._settings, "environment", "development") if self._settings else "development"
                result = await conn.execute(
                    f"""
                    INSERT INTO {self._schema}."20_trx_notification_queue" (
                        id, tenant_key, user_id, notification_type_code, channel_code,
                        status_code, priority_code,
                        source_audit_event_id,
                        rendered_subject, rendered_body, rendered_body_html,
                        recipient_email,
                        scheduled_at,
                        attempt_count, max_attempts, idempotency_key,
                        source_env,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, NULL, $3, 'email',
                        'queued', $4,
                        $5,
                        $6, $7, $8,
                        $9,
                        $10,
                        0, 3, $11,
                        $12,
                        $13, $14
                    )
                    ON CONFLICT (idempotency_key)
                        WHERE idempotency_key IS NOT NULL
                        DO NOTHING
                    """,
                    notification_id,        # $1
                    tenant_key,             # $2
                    notification_type_code, # $3
                    priority_code,          # $4
                    source_audit_event_id,  # $5
                    subject,                # $6
                    body_text,              # $7 rendered_body (plain text)
                    body_html,              # $8 rendered_body_html (HTML)
                    recipient_email,        # $9
                    now,                    # $10
                    idempotency_key,        # $11
                    _source_env,            # $12
                    now,                    # $13
                    now,                    # $14
                )
            if result == "INSERT 0 0":
                return None
            _LOGGER.info(
                "dispatch_to_email_queued",
                extra={
                    "action": "dispatch_to_email",
                    "outcome": "success",
                    "notification_type_code": notification_type_code,
                    "notification_id": notification_id,
                },
            )
            return notification_id
        except Exception as exc:
            _LOGGER.warning(
                "dispatch_to_email_failed",
                extra={
                    "action": "dispatch_to_email",
                    "outcome": "error",
                    "notification_type_code": notification_type_code,
                    "error": str(exc),
                },
            )
            return None

    async def dispatch_transactional(
        self,
        *,
        audit_entry: "AuditEntry",
        recipient_user_id: str,
        template_code: str,
        notification_type_code: str,
        tenant_key: str,
        idempotency_key: str | None = None,
        priority_code: str = "critical",
    ) -> str | None:
        """Queue a transactional notification (password reset, magic link, OTP) for a user.

        Renders the named template with fully-resolved variables derived from
        ``audit_entry.properties`` (which must include pre-computed action vars
        such as ``action.reset_url`` and ``action.expires_in``).

        Returns the created notification ID, or None if skipped/failed.
        """
        if self._database_pool is None:
            return None

        now = utc_now_sql()
        notification_id = str(uuid.uuid4())

        try:
            async with self._database_pool.transaction() as conn:
                # Resolve recipient email
                recipient_email = await self._resolve_recipient_email(conn, recipient_user_id)
                if not recipient_email:
                    _LOGGER.info(
                        "dispatch_transactional_no_email",
                        extra={"action": "dispatch_transactional", "outcome": "skipped",
                               "recipient_user_id": recipient_user_id},
                    )
                    return None

                # Fetch template by code
                template_row = await conn.fetchrow(
                    f"""
                    SELECT t.id AS template_id, v.id AS version_id,
                           v.subject_line, v.body_html, v.body_text, v.body_short,
                           bt_v.body_html AS base_body_html,
                           t.static_variables::text AS static_variables_json
                    FROM {self._schema}."10_fct_templates" t
                    JOIN {self._schema}."14_dtl_template_versions" v ON v.id = t.active_version_id
                    LEFT JOIN {self._schema}."10_fct_templates" bt
                        ON bt.id = t.base_template_id AND bt.is_active = TRUE AND bt.is_deleted = FALSE
                    LEFT JOIN {self._schema}."14_dtl_template_versions" bt_v ON bt_v.id = bt.active_version_id
                    WHERE t.code = $1
                      AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                      AND t.is_active = TRUE AND t.is_deleted = FALSE
                    ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                    LIMIT 1
                    """,
                    template_code,
                    tenant_key,
                )

                # Resolve template variables
                variables = await self._variable_resolver.resolve_all(
                    conn,
                    audit_entry=audit_entry,
                    recipient_user_id=recipient_user_id,
                    settings=self._settings,
                    template_id=template_row["template_id"] if template_row else None,
                )

                if template_row:
                    # Merge static variables from template with resolved variables
                    import json as _json
                    _static_vars: dict[str, str] = {}
                    if template_row.get("static_variables_json"):
                        try:
                            _static_vars = _json.loads(template_row["static_variables_json"]) or {}
                        except Exception:
                            pass
                    merged_variables = {**_static_vars, **variables}
                    # Render the template with resolved variables
                    rendered = self._renderer.render_template_version(
                        subject_line=template_row.get("subject_line"),
                        body_html=template_row.get("body_html"),
                        body_text=template_row.get("body_text"),
                        body_short=template_row.get("body_short"),
                        variables=merged_variables,
                        base_body_html=template_row.get("base_body_html"),
                    )
                    subject = rendered.get("subject_line") or ""
                    body_html = rendered.get("body_html") or ""
                    body_text = rendered.get("body_text") or ""
                else:
                    # No template — fall back to bare variables
                    subject = f"{notification_type_code} notification"
                    body_html = ""
                    body_text = ""

                _source_env = getattr(self._settings, "environment", "development") if self._settings else "development"
                result = await conn.execute(
                    f"""
                    INSERT INTO {self._schema}."20_trx_notification_queue" (
                        id, tenant_key, user_id, notification_type_code, channel_code,
                        status_code, priority_code,
                        source_audit_event_id,
                        rendered_subject, rendered_body, rendered_body_html,
                        recipient_email,
                        scheduled_at,
                        attempt_count, max_attempts, idempotency_key,
                        source_env,
                        created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, 'email',
                        'queued', $5,
                        $6,
                        $7, $8, $9,
                        $10,
                        $11,
                        0, 5, $12,
                        $13,
                        $14, $15
                    )
                    ON CONFLICT (idempotency_key)
                        WHERE idempotency_key IS NOT NULL
                        DO NOTHING
                    """,
                    notification_id,        # $1
                    tenant_key,             # $2
                    recipient_user_id,      # $3
                    notification_type_code, # $4
                    priority_code,          # $5
                    audit_entry.id,         # $6
                    subject,                # $7
                    body_text or "",        # $8 rendered_body (always plain text)
                    body_html or None,      # $9 rendered_body_html (always HTML)
                    recipient_email,        # $10
                    now,                    # $11
                    idempotency_key,        # $12
                    _source_env,            # $13
                    now,                    # $14
                    now,                    # $15
                )

                # Also queue web_push for each active subscription (best-effort, no idempotency block)
                push_subs = await conn.fetch(
                    f"""
                    SELECT id, endpoint, p256dh_key, auth_key
                    FROM {self._schema}."13_fct_web_push_subscriptions"
                    WHERE user_id = $1
                      AND tenant_key = $2
                      AND is_active = TRUE
                      AND is_deleted = FALSE
                    """,
                    recipient_user_id,
                    tenant_key,
                )
                if push_subs:
                    # Fetch the web_push template if available, else use email subject/body_short
                    push_template_row = await conn.fetchrow(
                        f"""
                        SELECT t.id AS template_id, v.id AS version_id,
                               v.subject_line, v.body_short, v.body_text
                        FROM {self._schema}."10_fct_templates" t
                        JOIN {self._schema}."14_dtl_template_versions" v ON v.id = t.active_version_id
                        WHERE t.code = $1
                          AND t.channel_code = 'web_push'
                          AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                          AND t.is_active = TRUE AND t.is_deleted = FALSE
                        ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                        LIMIT 1
                        """,
                        template_code,
                        tenant_key,
                    )
                    if push_template_row:
                        push_rendered = self._renderer.render_template_version(
                            subject_line=push_template_row.get("subject_line"),
                            body_html=None,
                            body_text=push_template_row.get("body_text"),
                            body_short=push_template_row.get("body_short"),
                            variables=variables,
                        )
                        push_subject = push_rendered.get("subject_line") or subject
                        push_body_short = push_rendered.get("body_short") or push_rendered.get("body_text") or ""
                    else:
                        push_subject = subject
                        push_body_short = body_text or ""

                    import json as _json
                    for sub in push_subs:
                        push_id = str(uuid.uuid4())
                        recipient_push = _json.dumps({
                            "endpoint": sub["endpoint"],
                            "keys": {"auth": sub["auth_key"], "p256dh": sub["p256dh_key"]},
                        })
                        push_idempotency = (
                            f"{idempotency_key}:push:{sub['id']}" if idempotency_key else None
                        )
                        await conn.execute(
                            f"""
                            INSERT INTO {self._schema}."20_trx_notification_queue" (
                                id, tenant_key, user_id, notification_type_code, channel_code,
                                status_code, priority_code,
                                source_audit_event_id,
                                rendered_subject, rendered_body,
                                recipient_push_endpoint,
                                scheduled_at,
                                attempt_count, max_attempts, idempotency_key,
                                source_env,
                                created_at, updated_at
                            ) VALUES (
                                $1, $2, $3, $4, 'web_push',
                                'queued', $5,
                                $6,
                                $7, $8,
                                $9,
                                $10,
                                0, 3, $11,
                                $12,
                                $13, $14
                            )
                            ON CONFLICT (idempotency_key)
                                WHERE idempotency_key IS NOT NULL
                                DO NOTHING
                            """,
                            push_id,
                            tenant_key,
                            recipient_user_id,
                            notification_type_code,
                            priority_code,
                            audit_entry.id,
                            push_subject,
                            push_body_short,
                            recipient_push,
                            now,
                            push_idempotency,
                            _source_env,
                            now,
                            now,
                        )

            if result == "INSERT 0 0":
                return None
            _LOGGER.info(
                "dispatch_transactional_queued",
                extra={
                    "action": "dispatch_transactional",
                    "outcome": "success",
                    "notification_type_code": notification_type_code,
                    "template_code": template_code,
                    "notification_id": notification_id,
                },
            )
            return notification_id

        except Exception as exc:
            _LOGGER.warning(
                "dispatch_transactional_failed",
                extra={
                    "action": "dispatch_transactional",
                    "outcome": "error",
                    "notification_type_code": notification_type_code,
                    "error": str(exc),
                },
            )
            return None

    async def _resolve_display_name(
        self,
        connection: asyncpg.Connection,
        user_id: str,
    ) -> str:
        """Resolve the display_name property for a user, falling back to 'Someone'."""
        row = await connection.fetchrow(
            f"""
            SELECT property_value
            FROM {AUTH_SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = 'display_name'
            LIMIT 1
            """,
            user_id,
        )
        return row["property_value"] if row else "Someone"

    async def _find_matching_rules(
        self,
        connection: asyncpg.Connection,
        audit_entry: AuditEntry,
    ) -> list[asyncpg.Record]:
        return await connection.fetch(
            f"""
            SELECT id, code, name, source_event_type, source_event_category,
                   notification_type_code, recipient_strategy, recipient_filter_json,
                   priority_code, delay_seconds
            FROM {self._schema}."11_fct_notification_rules"
            WHERE source_event_type = $1
              AND (source_event_category IS NULL OR source_event_category = $2)
              AND (tenant_key = $3 OR tenant_key = '__system__')
              AND is_active = TRUE AND is_disabled = FALSE AND is_deleted = FALSE
            ORDER BY is_system DESC, created_at ASC
            """,
            audit_entry.event_type,
            audit_entry.event_category,
            audit_entry.tenant_key,
        )

    async def _get_rule_channels(
        self,
        connection: asyncpg.Connection,
        rule: asyncpg.Record,
    ) -> list[asyncpg.Record]:
        """Get channels from rule link table, or fall back to defaults."""
        channels = await connection.fetch(
            f"""
            SELECT channel_code, template_code
            FROM {self._schema}."18_lnk_notification_rule_channels"
            WHERE rule_id = $1 AND is_active = TRUE
            """,
            rule["id"],
        )
        if channels:
            return channels

        # Fall back: all available channels for this notification type
        return await connection.fetch(
            f"""
            SELECT channel_code, NULL AS template_code
            FROM {self._schema}."07_dim_notification_channel_types"
            WHERE notification_type_code = $1 AND is_default = TRUE
            """,
            rule["notification_type_code"],
        )

    async def _resolve_template(
        self,
        connection: asyncpg.Connection,
        *,
        rule: asyncpg.Record,
        channel_code: str,
        tenant_key: str,
        template_code_override: str | None = None,
    ) -> dict[str, str | None] | None:
        """Find and return template data for rendering (includes static_variables)."""
        # Try template_code from rule channel first, then by notification_type + channel
        if template_code_override:
            row = await connection.fetchrow(
                f"""
                SELECT t.id AS template_id, v.id AS version_id,
                       v.subject_line, v.body_html, v.body_text, v.body_short,
                       bt_v.body_html AS base_body_html,
                       t.static_variables::text AS static_variables_json
                FROM {self._schema}."10_fct_templates" t
                JOIN {self._schema}."14_dtl_template_versions" v
                    ON v.id = t.active_version_id
                LEFT JOIN {self._schema}."10_fct_templates" bt
                    ON bt.id = t.base_template_id AND bt.is_active = TRUE AND bt.is_deleted = FALSE
                LEFT JOIN {self._schema}."14_dtl_template_versions" bt_v
                    ON bt_v.id = bt.active_version_id
                WHERE t.code = $1
                  AND (t.tenant_key = $2 OR t.tenant_key = '__system__')
                  AND t.is_active = TRUE AND t.is_deleted = FALSE
                ORDER BY CASE WHEN t.tenant_key = $2 THEN 0 ELSE 1 END
                LIMIT 1
                """,
                template_code_override,
                tenant_key,
            )
            if row:
                return dict(row)

        # Fall back to notification_type + channel lookup
        row = await connection.fetchrow(
            f"""
            SELECT t.id AS template_id, v.id AS version_id,
                   v.subject_line, v.body_html, v.body_text, v.body_short,
                   bt_v.body_html AS base_body_html,
                   t.static_variables::text AS static_variables_json
            FROM {self._schema}."10_fct_templates" t
            JOIN {self._schema}."14_dtl_template_versions" v
                ON v.id = t.active_version_id
            LEFT JOIN {self._schema}."10_fct_templates" bt
                ON bt.id = t.base_template_id AND bt.is_active = TRUE AND bt.is_deleted = FALSE
            LEFT JOIN {self._schema}."14_dtl_template_versions" bt_v
                ON bt_v.id = bt.active_version_id
            WHERE t.notification_type_code = $1
              AND t.channel_code = $2
              AND (t.tenant_key = $3 OR t.tenant_key = '__system__')
              AND t.is_active = TRUE AND t.is_deleted = FALSE
            ORDER BY CASE WHEN t.tenant_key = $3 THEN 0 ELSE 1 END
            LIMIT 1
            """,
            rule["notification_type_code"],
            channel_code,
            tenant_key,
        )
        if row:
            return dict(row)

        return None

    async def _resolve_recipient_email(
        self,
        connection: asyncpg.Connection,
        user_id: str,
    ) -> str | None:
        row = await connection.fetchrow(
            f"""
            SELECT property_value
            FROM {AUTH_SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = 'email'
            LIMIT 1
            """,
            user_id,
        )
        return row["property_value"] if row else None

    async def _resolve_push_endpoint(
        self,
        connection: asyncpg.Connection,
        user_id: str,
        tenant_key: str,
    ) -> str | None:
        """Return JSON-encoded subscription info for web push."""
        import json

        row = await connection.fetchrow(
            f"""
            SELECT endpoint, p256dh_key, auth_key
            FROM {self._schema}."13_fct_web_push_subscriptions"
            WHERE user_id = $1 AND tenant_key = $2
              AND is_active = TRUE
            ORDER BY last_used_at DESC NULLS LAST
            LIMIT 1
            """,
            user_id,
            tenant_key,
        )
        if not row:
            return None
        return json.dumps({
            "endpoint": row["endpoint"],
            "keys": {
                "p256dh": row["p256dh_key"],
                "auth": row["auth_key"],
            },
        })

    async def _get_type_meta(
        self,
        connection: asyncpg.Connection,
        notification_type_code: str,
    ) -> tuple[str | None, bool]:
        """Return (category_code, dispatch_immediately) for a notification type."""
        row = await connection.fetchrow(
            f"""
            SELECT category_code, COALESCE(dispatch_immediately, FALSE) AS dispatch_immediately
            FROM {self._schema}."04_dim_notification_types"
            WHERE code = $1
            """,
            notification_type_code,
        )
        if row:
            return row["category_code"], bool(row["dispatch_immediately"])
        return None, False

    async def _get_category_code(
        self,
        connection: asyncpg.Connection,
        notification_type_code: str,
    ) -> str | None:
        category_code, _ = await self._get_type_meta(connection, notification_type_code)
        return category_code

    async def _check_cooldown(
        self,
        connection: asyncpg.Connection,
        *,
        user_id: str,
        notification_type_code: str,
        channel_code: str,
        cooldown_seconds: int,
    ) -> bool:
        """Return True if a notification was sent within the cooldown window."""
        row = await connection.fetchrow(
            f"""
            SELECT 1 FROM {self._schema}."20_trx_notification_queue"
            WHERE user_id = $1
              AND notification_type_code = $2
              AND channel_code = $3
              AND status_code IN ('queued', 'processing', 'sent', 'delivered')
              AND created_at > NOW() - make_interval(secs => $4)
            LIMIT 1
            """,
            user_id,
            notification_type_code,
            channel_code,
            cooldown_seconds,
        )
        return row is not None

    async def _evaluate_rule_conditions(
        self,
        connection: asyncpg.Connection,
        rule_id: str,
    ) -> bool:
        """Evaluate all conditions attached to a rule. Returns True if all pass.

        Conditions within the same logical_group are OR'd together.
        Groups are AND'd with each other.
        If no conditions exist, the rule always matches.
        """
        conditions = await connection.fetch(
            f"""
            SELECT condition_type, field_key, operator, value, value_type, logical_group
            FROM {self._schema}."19_dtl_rule_conditions"
            WHERE rule_id = $1 AND is_active = TRUE
            ORDER BY logical_group, sort_order
            """,
            rule_id,
        )
        if not conditions:
            return True  # No conditions = always match

        # Group conditions by logical_group
        groups: dict[int, list[asyncpg.Record]] = {}
        for cond in conditions:
            groups.setdefault(cond["logical_group"], []).append(cond)

        # AND across groups, OR within each group
        for group_conditions in groups.values():
            group_passed = False
            for cond in group_conditions:
                if self._evaluate_single_condition(cond):
                    group_passed = True
                    break
            if not group_passed:
                return False

        return True

    @staticmethod
    def _evaluate_single_condition(cond: asyncpg.Record) -> bool:
        """Evaluate a single condition. For event-triggered rules, conditions
        of type 'inactivity' and 'engagement' are evaluated by the campaign
        runner, not here. This method handles 'property_check' and 'schedule'.
        """
        condition_type = cond["condition_type"]

        # Inactivity and engagement conditions are handled by the campaign
        # runner (periodic task), not by real-time event processing.
        # If we encounter them here, skip (they don't block event-based rules).
        if condition_type in ("inactivity", "engagement"):
            return True

        if condition_type == "schedule":
            # Schedule conditions check time-of-day / day-of-week
            # For now, always pass — the campaign runner handles scheduling
            return True

        # property_check: These are checked against audit event properties
        # at dispatch time by the campaign runner. For real-time rules,
        # the property is already implicitly matched via the audit event type.
        return True
