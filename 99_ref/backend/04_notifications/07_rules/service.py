from __future__ import annotations

import uuid
from importlib import import_module

from .repository import RuleRepository
from ..schemas import (
    CampaignRunResponse,
    CreateRuleConditionRequest,
    CreateRuleRequest,
    RuleChannelResponse,
    RuleConditionResponse,
    RuleDetailResponse,
    RuleResponse,
    SetRuleChannelRequest,
    UpdateRuleRequest,
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

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_RULES = "notification_rules:list"
_CACHE_TTL_RULES = 300  # 5 minutes

_AUDIT_ENTITY_TYPE = "notification_rule"
_AUDIT_EVENT_CATEGORY = "notification"


@instrument_class_methods(namespace="rules.service", logger_name="backend.notifications.rules.instrumentation")
class RuleService:
    def __init__(
        self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = RuleRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.notifications.rules")

    async def list_rules(
        self, *, user_id: str, tenant_key: str
    ) -> list[RuleResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")

        cache_key = f"{_CACHE_KEY_RULES}:{tenant_key}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            import json
            items = json.loads(cached)
            return [RuleResponse(**item) for item in items]

        async with self._database_pool.acquire() as conn:
            rules = await self._repository.list_rules(conn, tenant_key)
        result = [_rule_response(r) for r in rules]
        import json
        await self._cache.set(
            cache_key, json.dumps([r.model_dump() for r in result]), _CACHE_TTL_RULES
        )
        return result

    async def create_rule(
        self, *, user_id: str, tenant_key: str, request: CreateRuleRequest
    ) -> RuleResponse:
        now = utc_now_sql()
        rule_id = str(uuid.uuid4())
        priority_code = request.priority_code or "normal"

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.create")
            existing = await self._repository.get_rule_by_code(conn, request.code, tenant_key)
            if existing:
                raise ConflictError(f"Rule code '{request.code}' already exists")
            rule = await self._repository.create_rule(
                conn,
                rule_id=rule_id,
                tenant_key=tenant_key,
                code=request.code,
                name=request.name,
                description=request.description,
                source_event_type=request.source_event_type,
                source_event_category=request.source_event_category,
                notification_type_code=request.notification_type_code,
                recipient_strategy=request.recipient_strategy,
                recipient_filter_json=request.recipient_filter_json,
                priority_code=priority_code,
                delay_seconds=request.delay_seconds,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=rule_id,
                    event_type="notification_rule_created",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "code": request.code,
                        "name": request.name,
                        "source_event_type": request.source_event_type,
                        "notification_type_code": request.notification_type_code,
                        "recipient_strategy": request.recipient_strategy,
                    },
                ),
            )
        await self._cache.delete_pattern(f"{_CACHE_KEY_RULES}:*")
        return _rule_response(rule)

    async def update_rule(
        self, *, user_id: str, rule_id: str, request: UpdateRuleRequest
    ) -> RuleResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.update")
            rule = await self._repository.update_rule(
                conn,
                rule_id,
                name=request.name,
                description=request.description,
                is_disabled=request.is_disabled,
                priority_code=request.priority_code,
                delay_seconds=request.delay_seconds,
                updated_by=user_id,
                now=now,
            )
            if rule is None:
                raise NotFoundError(f"Rule '{rule_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=rule.tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=rule_id,
                    event_type="notification_rule_updated",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "name": request.name,
                        "description": request.description,
                        "is_disabled": str(request.is_disabled) if request.is_disabled is not None else None,
                        "priority_code": request.priority_code,
                        "delay_seconds": str(request.delay_seconds) if request.delay_seconds is not None else None,
                    },
                ),
            )
        await self._cache.delete_pattern(f"{_CACHE_KEY_RULES}:*")
        return _rule_response(rule)

    async def get_rule_detail(
        self, *, user_id: str, rule_id: str
    ) -> RuleDetailResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            rule = await self._repository.get_rule_by_id(conn, rule_id)
            if rule is None:
                raise NotFoundError(f"Rule '{rule_id}' not found")
            channels = await self._repository.list_rule_channels(conn, rule_id)
            conditions = await self._repository.list_rule_conditions(conn, rule_id)
            runs = await self._repository.list_campaign_runs(conn, rule_id)
        return RuleDetailResponse(
            id=rule.id,
            tenant_key=rule.tenant_key,
            code=rule.code,
            name=rule.name,
            description=rule.description,
            source_event_type=rule.source_event_type,
            source_event_category=rule.source_event_category,
            notification_type_code=rule.notification_type_code,
            recipient_strategy=rule.recipient_strategy,
            recipient_filter_json=rule.recipient_filter_json,
            priority_code=rule.priority_code,
            delay_seconds=rule.delay_seconds,
            is_active=rule.is_active,
            is_system=rule.is_system,
            created_at=rule.created_at,
            updated_at=rule.updated_at,
            channels=[_rule_channel_response(c) for c in channels],
            conditions=[_rule_condition_response(c) for c in conditions],
            recent_runs=[_campaign_run_response(r) for r in runs],
        )

    async def set_rule_channel(
        self, *, user_id: str, rule_id: str, channel_code: str, request: SetRuleChannelRequest
    ) -> RuleChannelResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.update")
            rule = await self._repository.get_rule_by_id(conn, rule_id)
            if rule is None:
                raise NotFoundError(f"Rule '{rule_id}' not found")
            channel = await self._repository.set_rule_channel(
                conn,
                channel_id=str(uuid.uuid4()),
                rule_id=rule_id,
                channel_code=channel_code,
                template_code=request.template_code,
                is_active=request.is_active,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=rule.tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=rule_id,
                    event_type="notification_rule_updated",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "channel_code": channel_code,
                        "template_code": request.template_code,
                        "is_active": str(request.is_active),
                    },
                ),
            )
        await self._cache.delete_pattern(f"{_CACHE_KEY_RULES}:*")
        return _rule_channel_response(channel)


    async def create_rule_condition(
        self, *, user_id: str, rule_id: str, request: CreateRuleConditionRequest
    ) -> RuleConditionResponse:
        now = utc_now_sql()
        condition_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.update")
            rule = await self._repository.get_rule_by_id(conn, rule_id)
            if rule is None:
                raise NotFoundError(f"Rule '{rule_id}' not found")
            condition = await self._repository.create_rule_condition(
                conn,
                condition_id=condition_id,
                rule_id=rule_id,
                condition_type=request.condition_type,
                field_key=request.field_key,
                operator=request.operator,
                value=request.value,
                value_type=request.value_type,
                logical_group=request.logical_group,
                sort_order=request.sort_order,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=rule.tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=rule_id,
                    event_type="notification_rule_updated",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "action": "condition_added",
                        "condition_type": request.condition_type,
                        "field_key": request.field_key,
                        "operator": request.operator,
                    },
                ),
            )
        await self._cache.delete_pattern(f"{_CACHE_KEY_RULES}:*")
        return _rule_condition_response(condition)

    async def delete_rule_condition(
        self, *, user_id: str, rule_id: str, condition_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.update")
            rule = await self._repository.get_rule_by_id(conn, rule_id)
            if rule is None:
                raise NotFoundError(f"Rule '{rule_id}' not found")
            deleted = await self._repository.delete_rule_condition(
                conn, condition_id=condition_id, rule_id=rule_id
            )
            if not deleted:
                raise NotFoundError(f"Condition '{condition_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=rule.tenant_key,
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=rule_id,
                    event_type="notification_rule_updated",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"action": "condition_removed", "condition_id": condition_id},
                ),
            )
        await self._cache.delete_pattern(f"{_CACHE_KEY_RULES}:*")

def _rule_response(r) -> RuleResponse:
    return RuleResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        code=r.code,
        name=r.name,
        description=r.description,
        source_event_type=r.source_event_type,
        source_event_category=r.source_event_category,
        notification_type_code=r.notification_type_code,
        recipient_strategy=r.recipient_strategy,
        recipient_filter_json=r.recipient_filter_json,
        priority_code=r.priority_code,
        delay_seconds=r.delay_seconds,
        is_active=r.is_active,
        is_system=r.is_system,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


def _rule_channel_response(c) -> RuleChannelResponse:
    return RuleChannelResponse(
        id=c.id,
        rule_id=c.rule_id,
        channel_code=c.channel_code,
        template_code=c.template_code,
        is_active=c.is_active,
    )


def _rule_condition_response(c) -> RuleConditionResponse:
    return RuleConditionResponse(
        id=c.id,
        rule_id=c.rule_id,
        condition_type=c.condition_type,
        field_key=c.field_key,
        operator=c.operator,
        value=c.value,
        value_type=c.value_type,
        logical_group=c.logical_group,
        sort_order=c.sort_order,
        is_active=c.is_active,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _campaign_run_response(r) -> CampaignRunResponse:
    return CampaignRunResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        rule_id=r.rule_id,
        run_type=r.run_type,
        started_at=r.started_at,
        completed_at=r.completed_at,
        users_evaluated=r.users_evaluated,
        users_matched=r.users_matched,
        notifications_created=r.notifications_created,
        status=r.status,
        error_message=r.error_message,
        created_at=r.created_at,
    )
