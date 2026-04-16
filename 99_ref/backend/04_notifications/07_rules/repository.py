from __future__ import annotations

import asyncpg
from importlib import import_module

from ..models import CampaignRunRecord, NotificationRuleRecord, RuleChannelRecord, RuleConditionRecord

SCHEMA = '"03_notifications"'
instrument_class_methods = import_module("backend.01_core.telemetry").instrument_class_methods


@instrument_class_methods(namespace="rules.repository", logger_name="backend.notifications.rules.repository.instrumentation")
class RuleRepository:
    async def list_rules(
        self, connection: asyncpg.Connection, tenant_key: str
    ) -> list[NotificationRuleRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, code, name, description,
                   source_event_type, source_event_category,
                   notification_type_code, recipient_strategy,
                   recipient_filter_json, priority_code, delay_seconds,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."11_fct_notification_rules"
            WHERE tenant_key = $1 AND is_deleted = FALSE
            ORDER BY name
            """,
            tenant_key,
        )
        return [_row_to_rule(r) for r in rows]

    async def get_rule_by_id(
        self, connection: asyncpg.Connection, rule_id: str
    ) -> NotificationRuleRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, code, name, description,
                   source_event_type, source_event_category,
                   notification_type_code, recipient_strategy,
                   recipient_filter_json, priority_code, delay_seconds,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."11_fct_notification_rules"
            WHERE id = $1 AND is_deleted = FALSE
            """,
            rule_id,
        )
        return _row_to_rule(row) if row else None

    async def get_rule_by_code(
        self, connection: asyncpg.Connection, code: str, tenant_key: str
    ) -> NotificationRuleRecord | None:
        row = await connection.fetchrow(
            f"""
            SELECT id, tenant_key, code, name, description,
                   source_event_type, source_event_category,
                   notification_type_code, recipient_strategy,
                   recipient_filter_json, priority_code, delay_seconds,
                   is_active, is_disabled, is_deleted, is_system,
                   created_at::text, updated_at::text
            FROM {SCHEMA}."11_fct_notification_rules"
            WHERE code = $1 AND tenant_key = $2 AND is_deleted = FALSE
            """,
            code,
            tenant_key,
        )
        return _row_to_rule(row) if row else None

    async def create_rule(
        self,
        connection: asyncpg.Connection,
        *,
        rule_id: str,
        tenant_key: str,
        code: str,
        name: str,
        description: str,
        source_event_type: str,
        source_event_category: str | None,
        notification_type_code: str,
        recipient_strategy: str,
        recipient_filter_json: str | None,
        priority_code: str,
        delay_seconds: int,
        created_by: str,
        now: datetime,
    ) -> NotificationRuleRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."11_fct_notification_rules"
                (id, tenant_key, code, name, description,
                 source_event_type, source_event_category,
                 notification_type_code, recipient_strategy,
                 recipient_filter_json, priority_code, delay_seconds,
                 is_active, is_disabled, is_deleted, is_system,
                 created_at, updated_at, created_by, updated_by)
            VALUES ($1, $2, $3, $4, $5,
                    $6, $7,
                    $8, $9,
                    $10, $11, $12,
                    TRUE, FALSE, FALSE, FALSE,
                    $13, $14, $15, $16)
            RETURNING id, tenant_key, code, name, description,
                      source_event_type, source_event_category,
                      notification_type_code, recipient_strategy,
                      recipient_filter_json, priority_code, delay_seconds,
                      is_active, is_disabled, is_deleted, is_system,
                      created_at::text, updated_at::text
            """,
            rule_id,
            tenant_key,
            code,
            name,
            description,
            source_event_type,
            source_event_category,
            notification_type_code,
            recipient_strategy,
            recipient_filter_json,
            priority_code,
            delay_seconds,
            now,
            now,
            created_by,
            created_by,
        )
        return _row_to_rule(row)

    async def update_rule(
        self,
        connection: asyncpg.Connection,
        rule_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        is_disabled: bool | None = None,
        priority_code: str | None = None,
        delay_seconds: int | None = None,
        updated_by: str,
        now: datetime,
    ) -> NotificationRuleRecord | None:
        fields: list[str] = ["updated_at = $1", "updated_by = $2"]
        values: list[object] = [now, updated_by]
        idx = 3

        if name is not None:
            fields.append(f"name = ${idx}")
            values.append(name)
            idx += 1
        if description is not None:
            fields.append(f"description = ${idx}")
            values.append(description)
            idx += 1
        if is_disabled is not None:
            fields.append(f"is_disabled = ${idx}")
            values.append(is_disabled)
            idx += 1
            fields.append(f"is_active = ${idx}")
            values.append(not is_disabled)
            idx += 1
        if priority_code is not None:
            fields.append(f"priority_code = ${idx}")
            values.append(priority_code)
            idx += 1
        if delay_seconds is not None:
            fields.append(f"delay_seconds = ${idx}")
            values.append(delay_seconds)
            idx += 1

        values.append(rule_id)
        set_clause = ", ".join(fields)

        row = await connection.fetchrow(
            f"""
            UPDATE {SCHEMA}."11_fct_notification_rules"
            SET {set_clause}
            WHERE id = ${idx} AND is_deleted = FALSE
            RETURNING id, tenant_key, code, name, description,
                      source_event_type, source_event_category,
                      notification_type_code, recipient_strategy,
                      recipient_filter_json, priority_code, delay_seconds,
                      is_active, is_disabled, is_deleted, is_system,
                      created_at::text, updated_at::text
            """,
            *values,
        )
        return _row_to_rule(row) if row else None

    async def list_rule_channels(
        self, connection: asyncpg.Connection, rule_id: str
    ) -> list[RuleChannelRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, rule_id, channel_code, template_code, is_active
            FROM {SCHEMA}."18_lnk_notification_rule_channels"
            WHERE rule_id = $1
            ORDER BY channel_code
            """,
            rule_id,
        )
        return [_row_to_rule_channel(r) for r in rows]

    async def set_rule_channel(
        self,
        connection: asyncpg.Connection,
        *,
        channel_id: str,
        rule_id: str,
        channel_code: str,
        template_code: str | None,
        is_active: bool,
    ) -> RuleChannelRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."18_lnk_notification_rule_channels"
                (id, rule_id, channel_code, template_code, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
            ON CONFLICT (rule_id, channel_code)
            DO UPDATE SET
                template_code = EXCLUDED.template_code,
                is_active = EXCLUDED.is_active,
                updated_at = NOW()
            RETURNING id, rule_id, channel_code, template_code, is_active
            """,
            channel_id,
            rule_id,
            channel_code,
            template_code,
            is_active,
        )
        return _row_to_rule_channel(row)


    async def list_rule_conditions(
        self, connection: asyncpg.Connection, rule_id: str
    ) -> list[RuleConditionRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, rule_id, condition_type, field_key, operator,
                   value, value_type, logical_group, sort_order,
                   is_active, created_at::text, updated_at::text
            FROM {SCHEMA}."19_dtl_rule_conditions"
            WHERE rule_id = $1
            ORDER BY logical_group, sort_order
            """,
            rule_id,
        )
        return [_row_to_rule_condition(r) for r in rows]

    async def create_rule_condition(
        self,
        connection: asyncpg.Connection,
        *,
        condition_id: str,
        rule_id: str,
        condition_type: str,
        field_key: str,
        operator: str,
        value: str | None,
        value_type: str,
        logical_group: int,
        sort_order: int,
        now: object,
    ) -> RuleConditionRecord:
        row = await connection.fetchrow(
            f"""
            INSERT INTO {SCHEMA}."19_dtl_rule_conditions"
                (id, rule_id, condition_type, field_key, operator,
                 value, value_type, logical_group, sort_order,
                 is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE, $10, $11)
            RETURNING id, rule_id, condition_type, field_key, operator,
                      value, value_type, logical_group, sort_order,
                      is_active, created_at::text, updated_at::text
            """,
            condition_id,
            rule_id,
            condition_type,
            field_key,
            operator,
            value,
            value_type,
            logical_group,
            sort_order,
            now,
            now,
        )
        return _row_to_rule_condition(row)

    async def delete_rule_condition(
        self, connection: asyncpg.Connection, *, condition_id: str, rule_id: str
    ) -> bool:
        result = await connection.execute(
            f"""
            DELETE FROM {SCHEMA}."19_dtl_rule_conditions"
            WHERE id = $1 AND rule_id = $2
            """,
            condition_id,
            rule_id,
        )
        return result != "DELETE 0"

    async def list_campaign_runs(
        self, connection: asyncpg.Connection, rule_id: str
    ) -> list[CampaignRunRecord]:
        rows = await connection.fetch(
            f"""
            SELECT id, tenant_key, rule_id, run_type,
                   started_at::text, completed_at::text,
                   users_evaluated, users_matched, notifications_created,
                   status, error_message, created_at::text
            FROM {SCHEMA}."24_trx_campaign_runs"
            WHERE rule_id = $1
            ORDER BY created_at DESC
            LIMIT 50
            """,
            rule_id,
        )
        return [_row_to_campaign_run(r) for r in rows]


def _row_to_rule(r) -> NotificationRuleRecord:
    return NotificationRuleRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        code=r["code"],
        name=r["name"],
        description=r["description"],
        source_event_type=r["source_event_type"],
        source_event_category=r["source_event_category"],
        notification_type_code=r["notification_type_code"],
        recipient_strategy=r["recipient_strategy"],
        recipient_filter_json=r["recipient_filter_json"],
        priority_code=r["priority_code"],
        delay_seconds=r["delay_seconds"],
        is_active=r["is_active"],
        is_disabled=r["is_disabled"],
        is_deleted=r["is_deleted"],
        is_system=r["is_system"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_rule_channel(r) -> RuleChannelRecord:
    return RuleChannelRecord(
        id=r["id"],
        rule_id=r["rule_id"],
        channel_code=r["channel_code"],
        template_code=r["template_code"],
        is_active=r["is_active"],
    )


def _row_to_rule_condition(r) -> RuleConditionRecord:
    return RuleConditionRecord(
        id=r["id"],
        rule_id=r["rule_id"],
        condition_type=r["condition_type"],
        field_key=r["field_key"],
        operator=r["operator"],
        value=r["value"],
        value_type=r["value_type"],
        logical_group=r["logical_group"],
        sort_order=r["sort_order"],
        is_active=r["is_active"],
        created_at=r["created_at"],
        updated_at=r["updated_at"],
    )


def _row_to_campaign_run(r) -> CampaignRunRecord:
    return CampaignRunRecord(
        id=r["id"],
        tenant_key=r["tenant_key"],
        rule_id=r["rule_id"],
        run_type=r["run_type"],
        started_at=r["started_at"],
        completed_at=r["completed_at"],
        users_evaluated=r["users_evaluated"],
        users_matched=r["users_matched"],
        notifications_created=r["notifications_created"],
        status=r["status"],
        error_message=r["error_message"],
        created_at=r["created_at"],
    )
