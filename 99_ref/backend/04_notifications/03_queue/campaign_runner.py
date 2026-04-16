from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timezone
from importlib import import_module

import asyncpg

_constants_module = import_module("backend.04_notifications.constants")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_database_module = import_module("backend.01_core.database")
_settings_module = import_module("backend.00_config.settings")
_audit_module = import_module("backend.01_core.audit")
_time_module = import_module("backend.01_core.time_utils")

NOTIFICATION_SCHEMA = _constants_module.NOTIFICATION_SCHEMA
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
DatabasePool = _database_module.DatabasePool
Settings = _settings_module.Settings
AuditEntry = _audit_module.AuditEntry
utc_now_sql = _time_module.utc_now_sql

SCHEMA = f'"{NOTIFICATION_SCHEMA}"'
AUTH_SCHEMA = '"03_auth_manage"'

_LOGGER = get_logger("backend.notifications.campaign_runner")

# Default: run campaigns every 15 minutes
_DEFAULT_CAMPAIGN_INTERVAL = 900.0


@instrument_class_methods(
    namespace="notifications.campaign_runner",
    logger_name="backend.notifications.campaign_runner.instrumentation",
)
class CampaignRunner:
    """Periodic task that evaluates notification rules with conditions.

    Handles condition types that can't be evaluated in real-time:
    - inactivity: "user hasn't logged in for N days"
    - engagement: "user hasn't opened notification X in N hours"
    - schedule: time-of-day / day-of-week restrictions

    Runs on a configurable interval (default 15 minutes).
    """

    def __init__(
        self,
        *,
        database_pool: DatabasePool,
        settings: Settings,
    ) -> None:
        self._database_pool = database_pool
        self._settings = settings
        self._running = False

    async def run_loop(self) -> None:
        """Main campaign evaluation loop."""
        self._running = True
        _LOGGER.info("campaign_runner_started", extra={"action": "start"})

        while self._running:
            try:
                await self._run_cycle()
            except asyncio.CancelledError:
                break
            except Exception:
                _LOGGER.exception(
                    "campaign_runner_error",
                    extra={"action": "run_cycle", "outcome": "error"},
                )

            await asyncio.sleep(_DEFAULT_CAMPAIGN_INTERVAL)

        _LOGGER.info("campaign_runner_stopped", extra={"action": "stop"})

    async def stop(self) -> None:
        self._running = False

    async def _run_cycle(self) -> None:
        """Evaluate all rules that have conditions (campaign-type rules)."""
        async with self._database_pool.acquire() as connection:
            # Find rules that have at least one condition (these are "campaigns")
            campaign_rules = await connection.fetch(
                f"""
                SELECT DISTINCT r.id, r.tenant_key, r.code, r.name,
                       r.notification_type_code, r.recipient_strategy,
                       r.recipient_filter_json, r.priority_code
                FROM {SCHEMA}."11_fct_notification_rules" r
                JOIN {SCHEMA}."19_dtl_rule_conditions" c
                    ON c.rule_id = r.id AND c.is_active = TRUE
                WHERE r.is_active = TRUE AND r.is_disabled = FALSE AND r.is_deleted = FALSE
                """
            )

            for rule in campaign_rules:
                try:
                    await self._evaluate_campaign_rule(connection, rule)
                except Exception:
                    _LOGGER.exception(
                        "campaign_rule_error",
                        extra={
                            "action": "evaluate_campaign_rule",
                            "outcome": "error",
                            "rule_id": rule["id"],
                            "rule_code": rule["code"],
                        },
                    )

    async def _evaluate_campaign_rule(
        self,
        connection: asyncpg.Connection,
        rule: asyncpg.Record,
    ) -> None:
        """Evaluate a single campaign rule against its conditions."""
        conditions = await connection.fetch(
            f"""
            SELECT condition_type, field_key, operator, value, value_type, logical_group
            FROM {SCHEMA}."19_dtl_rule_conditions"
            WHERE rule_id = $1 AND is_active = TRUE
            ORDER BY logical_group, sort_order
            """,
            rule["id"],
        )

        # Create a campaign run record
        run_id = str(uuid.uuid4())
        now = utc_now_sql()
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."24_trx_campaign_runs"
                (id, tenant_key, rule_id, run_type, started_at, status, created_at)
            VALUES ($1, $2, $3, 'periodic', $4, 'running', $5)
            """,
            run_id,
            rule["tenant_key"],
            rule["id"],
            now,
            now,
        )

        users_evaluated = 0
        users_matched = 0
        notifications_created = 0

        try:
            # Get candidate users based on condition types
            has_inactivity = any(c["condition_type"] == "inactivity" for c in conditions)
            has_engagement = any(c["condition_type"] == "engagement" for c in conditions)

            if has_inactivity:
                matched_users = await self._evaluate_inactivity_conditions(
                    connection, rule, conditions
                )
            elif has_engagement:
                matched_users = await self._evaluate_engagement_conditions(
                    connection, rule, conditions
                )
            else:
                matched_users = []

            users_evaluated = len(matched_users)
            users_matched = len(matched_users)

            # Queue notifications for matched users (batch)
            if matched_users:
                notifications_created = await self._queue_campaign_notifications_batch(
                    connection, rule=rule, user_ids=matched_users
                )

            # Update campaign run
            await connection.execute(
                f"""
                UPDATE {SCHEMA}."24_trx_campaign_runs"
                SET completed_at = $2, status = 'completed',
                    users_evaluated = $3, users_matched = $4,
                    notifications_created = $5
                WHERE id = $1
                """,
                run_id,
                utc_now_sql(),
                users_evaluated,
                users_matched,
                notifications_created,
            )

            _LOGGER.info(
                "campaign_rule_evaluated",
                extra={
                    "action": "evaluate_campaign_rule",
                    "outcome": "success",
                    "rule_id": rule["id"],
                    "rule_code": rule["code"],
                    "users_evaluated": users_evaluated,
                    "users_matched": users_matched,
                    "notifications_created": notifications_created,
                },
            )

        except Exception as e:
            await connection.execute(
                f"""
                UPDATE {SCHEMA}."24_trx_campaign_runs"
                SET completed_at = $2, status = 'failed', error_message = $3
                WHERE id = $1
                """,
                run_id,
                utc_now_sql(),
                str(e),
            )
            raise

    async def _evaluate_inactivity_conditions(
        self,
        connection: asyncpg.Connection,
        rule: asyncpg.Record,
        conditions: list[asyncpg.Record],
    ) -> list[str]:
        """Find users matching inactivity conditions.

        Example condition: field_key='inactivity_days', operator='gte', value='7'
        Means: users who haven't logged in for >= 7 days.
        """
        inactivity_conditions = [
            c for c in conditions if c["condition_type"] == "inactivity"
        ]
        if not inactivity_conditions:
            return []

        # Find the inactivity_days threshold
        days_threshold = 7  # default
        for cond in inactivity_conditions:
            if cond["field_key"] == "inactivity_days" and cond["value"]:
                try:
                    days_threshold = int(cond["value"])
                except ValueError:
                    pass

        # Update inactivity snapshots from latest login data
        await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."23_trx_inactivity_snapshots"
                (id, user_id, tenant_key, last_login_at, inactivity_days, created_at, updated_at)
            SELECT
                gen_random_uuid(),
                u.id,
                u.tenant_key,
                (SELECT MAX(s.created_at) FROM {AUTH_SCHEMA}."10_trx_auth_sessions" s WHERE s.user_id = u.id),
                COALESCE(
                    EXTRACT(DAY FROM NOW() -
                        (SELECT MAX(s.created_at) FROM {AUTH_SCHEMA}."10_trx_auth_sessions" s WHERE s.user_id = u.id)
                    )::INTEGER,
                    9999
                ),
                NOW(), NOW()
            FROM {AUTH_SCHEMA}."03_fct_users" u
            WHERE u.is_active = TRUE AND u.is_deleted = FALSE
              AND (u.tenant_key = $1 OR $1 = 'default')
            ON CONFLICT (user_id) DO UPDATE SET
                last_login_at = EXCLUDED.last_login_at,
                inactivity_days = EXCLUDED.inactivity_days,
                updated_at = NOW()
            """,
            rule["tenant_key"],
        )

        # Find users meeting the inactivity threshold who haven't been notified recently
        rows = await connection.fetch(
            f"""
            SELECT s.user_id
            FROM {SCHEMA}."23_trx_inactivity_snapshots" s
            WHERE s.inactivity_days >= $1
              AND (s.tenant_key = $2 OR $2 = 'default')
              AND (
                  s.last_notified_at IS NULL
                  OR s.last_notified_at < NOW() - INTERVAL '7 days'
              )
            """,
            days_threshold,
            rule["tenant_key"],
        )

        user_ids = [r["user_id"] for r in rows]

        # Mark these users as notified
        if user_ids:
            await connection.execute(
                f"""
                UPDATE {SCHEMA}."23_trx_inactivity_snapshots"
                SET last_notified_at = NOW(), notification_sent = TRUE, updated_at = NOW()
                WHERE user_id = ANY($1)
                """,
                user_ids,
            )

        return user_ids

    async def _evaluate_engagement_conditions(
        self,
        connection: asyncpg.Connection,
        rule: asyncpg.Record,
        conditions: list[asyncpg.Record],
    ) -> list[str]:
        """Find users matching engagement conditions.

        Example conditions:
        - field_key='notification_type:password_reset', operator='not_opened', value='48'
          (user didn't open password_reset notification in 48 hours)
        - field_key='notification_type:org_invite_received', operator='not_clicked', value='72'
          (user didn't click the invite link in 72 hours)
        """
        engagement_conditions = [
            c for c in conditions if c["condition_type"] == "engagement"
        ]
        if not engagement_conditions:
            return []

        all_matched: set[str] | None = None

        for cond in engagement_conditions:
            field_key = cond["field_key"]
            operator = cond["operator"]
            hours = int(cond["value"] or "48")

            # Parse field_key: "notification_type:code" or "channel:code"
            notification_type_code = None
            if field_key.startswith("notification_type:"):
                notification_type_code = field_key.split(":", 1)[1]

            if operator in ("eq", "not_opened"):
                # Find users who received a notification but didn't open it
                rows = await connection.fetch(
                    f"""
                    SELECT DISTINCT q.user_id
                    FROM {SCHEMA}."20_trx_notification_queue" q
                    WHERE q.notification_type_code = $1
                      AND q.status_code IN ('sent', 'delivered')
                      AND q.created_at < NOW() - make_interval(hours => $2)
                      AND q.tenant_key = $3
                      AND NOT EXISTS (
                          SELECT 1 FROM {SCHEMA}."22_trx_tracking_events" te
                          WHERE te.notification_id = q.id
                            AND te.tracking_event_type_code = 'opened'
                      )
                    """,
                    notification_type_code,
                    hours,
                    rule["tenant_key"],
                )
            elif operator in ("neq", "not_clicked"):
                # Find users who received but didn't click
                rows = await connection.fetch(
                    f"""
                    SELECT DISTINCT q.user_id
                    FROM {SCHEMA}."20_trx_notification_queue" q
                    WHERE q.notification_type_code = $1
                      AND q.status_code IN ('sent', 'delivered', 'opened')
                      AND q.created_at < NOW() - make_interval(hours => $2)
                      AND q.tenant_key = $3
                      AND NOT EXISTS (
                          SELECT 1 FROM {SCHEMA}."22_trx_tracking_events" te
                          WHERE te.notification_id = q.id
                            AND te.tracking_event_type_code = 'clicked'
                      )
                    """,
                    notification_type_code,
                    hours,
                    rule["tenant_key"],
                )
            else:
                continue

            matched = {r["user_id"] for r in rows}
            if all_matched is None:
                all_matched = matched
            else:
                all_matched &= matched  # AND across conditions

        return list(all_matched) if all_matched else []

    async def _queue_campaign_notification(
        self,
        connection: asyncpg.Connection,
        *,
        rule: asyncpg.Record,
        user_id: str,
    ) -> bool:
        """Queue a notification for a campaign-matched user.

        Uses idempotency key to prevent duplicate campaign notifications
        within a 24-hour window.
        """
        now = utc_now_sql()
        notification_id = str(uuid.uuid4())
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        idempotency_key = f"campaign:{user_id}:{rule['code']}:{today}"

        # Get recipient email
        email_row = await connection.fetchrow(
            f"""
            SELECT property_value FROM {AUTH_SCHEMA}."05_dtl_user_properties"
            WHERE user_id = $1 AND property_key = 'email'
            LIMIT 1
            """,
            user_id,
        )
        recipient_email = email_row["property_value"] if email_row else None

        result = await connection.execute(
            f"""
            INSERT INTO {SCHEMA}."20_trx_notification_queue" (
                id, tenant_key, user_id, notification_type_code, channel_code,
                status_code, priority_code, source_rule_id,
                recipient_email, scheduled_at,
                attempt_count, max_attempts, idempotency_key,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, 'email',
                'queued', $5, $6,
                $7, $8,
                0, 3, $9,
                $10, $11
            )
            ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL
            DO NOTHING
            """,
            notification_id,
            rule["tenant_key"],
            user_id,
            rule["notification_type_code"],
            rule["priority_code"],
            rule["id"],
            recipient_email,
            now,
            idempotency_key,
            now,
            now,
        )

        return result != "INSERT 0 0"

    async def _queue_campaign_notifications_batch(
        self,
        connection: asyncpg.Connection,
        *,
        rule: asyncpg.Record,
        user_ids: list[str],
    ) -> int:
        """Batch queue notifications for all matched users.

        Pre-fetches emails in one query, then batch-inserts queue entries.
        Uses idempotency keys to prevent duplicates within a 24-hour window.
        """
        if not user_ids:
            return 0

        now = utc_now_sql()
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Batch fetch all emails in one query
        email_rows = await connection.fetch(
            f"""
            SELECT user_id::text, property_value
            FROM {AUTH_SCHEMA}."05_dtl_user_properties"
            WHERE user_id = ANY($1) AND property_key = 'email'
            """,
            user_ids,
        )
        email_map = {r["user_id"]: r["property_value"] for r in email_rows}

        # Build batch rows
        rows = []
        for user_id in user_ids:
            notification_id = str(uuid.uuid4())
            idempotency_key = f"campaign:{user_id}:{rule['code']}:{today}"
            recipient_email = email_map.get(user_id)
            rows.append((
                notification_id,
                rule["tenant_key"],
                user_id,
                rule["notification_type_code"],
                rule["priority_code"],
                rule["id"],
                recipient_email,
                now,
                idempotency_key,
                now,
                now,
            ))

        # Batch insert with ON CONFLICT DO NOTHING for idempotency
        await connection.executemany(
            f"""
            INSERT INTO {SCHEMA}."20_trx_notification_queue" (
                id, tenant_key, user_id, notification_type_code, channel_code,
                status_code, priority_code, source_rule_id,
                recipient_email, scheduled_at,
                attempt_count, max_attempts, idempotency_key,
                created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, 'email',
                'queued', $5, $6,
                $7, $8,
                0, 3, $9,
                $10, $11
            )
            ON CONFLICT (idempotency_key) WHERE idempotency_key IS NOT NULL
            DO NOTHING
            """,
            rows,
        )
        return len(rows)
