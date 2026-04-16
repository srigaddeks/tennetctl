from __future__ import annotations

import uuid
from importlib import import_module

from .repository import PolicyRepository
from .schemas import (
    CreatePolicyRequest,
    PolicyExecutionResponse,
    PolicyListResponse,
    PolicyResponse,
    PolicyTestResponse,
    UpdatePolicyRequest,
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
_constants_module = import_module("backend.10_sandbox.constants")
_lifecycle_module = import_module("backend.10_sandbox.lifecycle")
_policy_container_module = import_module("backend.10_sandbox.policy_container")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
write_lifecycle_event = _lifecycle_module.write_lifecycle_event
normalize_policy_container_properties = _policy_container_module.normalize_policy_container_properties

SCHEMA = '"15_sandbox"'
_CACHE_KEY_PREFIX = "sb:policies"
_CACHE_TTL = 300


@instrument_class_methods(namespace="sandbox.policies.service", logger_name="backend.sandbox.policies.instrumentation")
class PolicyService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = PolicyRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.policies")

    async def _require_sandbox_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
        )

    async def _validate_threat_type_reference(
        self,
        conn,
        *,
        org_id: str,
        threat_type_id: str,
    ) -> None:
        threat_row = await conn.fetchrow(
            f"""
            SELECT id
            FROM {SCHEMA}."23_fct_threat_types"
            WHERE id = $1::uuid
              AND org_id = $2::uuid
              AND is_deleted = FALSE
            """,
            threat_type_id,
            org_id,
        )
        if threat_row is None:
            raise ValidationError(f"Threat type '{threat_type_id}' not found")

    async def list_policies(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        threat_type_id: str | None = None,
        is_enabled: bool | None = None,
        sort_by: str = "policy_code",
        sort_dir: str = "ASC",
        limit: int = 100,
        offset: int = 0,
    ) -> PolicyListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{org_id}"
        if not any([workspace_id, threat_type_id, is_enabled is not None]) and offset == 0 and limit == 100:
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return PolicyListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records, total = await self._repository.list_policies(
                conn,
                org_id,
                workspace_id=workspace_id,
                threat_type_id=threat_type_id,
                is_enabled=is_enabled,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
            # Batch-load properties for all records (avoids N+1)
            policy_ids = [r.id for r in records]
            all_props = await self._repository.list_policy_properties_batch(conn, policy_ids)
            items = [_policy_response(r, all_props.get(r.id, {})) for r in records]

        result = PolicyListResponse(items=items, total=total)

        if not any([workspace_id, threat_type_id, is_enabled is not None]) and offset == 0 and limit == 100:
            await self._cache.set_json(cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL)

        return result

    async def get_policy(
        self, *, user_id: str, policy_id: str
    ) -> PolicyResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
            props = await self._repository.get_policy_properties(conn, policy_id)
        return _policy_response(record, props)

    async def create_policy(
        self, *, user_id: str, tenant_key: str, org_id: str, request: CreatePolicyRequest
    ) -> PolicyResponse:
        now = utc_now_sql()
        policy_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
            )

            await self._validate_threat_type_reference(
                conn,
                org_id=org_id,
                threat_type_id=request.threat_type_id,
            )

            # Validate actions
            await self._validate_actions(conn, request.actions)

            version_number = await self._repository.get_next_version(
                conn, org_id, request.policy_code
            )

            await self._repository.create_policy(
                conn,
                id=policy_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                policy_code=request.policy_code,
                version_number=version_number,
                threat_type_id=request.threat_type_id,
                actions=request.actions,
                is_enabled=request.is_enabled,
                cooldown_minutes=request.cooldown_minutes,
                created_by=user_id,
                now=now,
            )

            # Upsert properties (name, description, etc.)
            props = _normalize_policy_properties(
                request.properties,
                require_container=False,
            )
            if props:
                await self._repository.upsert_properties(
                    conn, policy_id, props, created_by=user_id, now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="policy",
                    entity_id=policy_id,
                    event_type=SandboxAuditEventType.POLICY_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "policy_code": request.policy_code,
                        "version_number": str(version_number),
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="policy",
                entity_id=policy_id,
                event_type="created",
                actor_id=user_id,
                properties={"policy_code": request.policy_code},
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            fetched_props = await self._repository.get_policy_properties(conn, policy_id)
        return _policy_response(record, fetched_props)

    async def update_policy(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        policy_id: str,
        request: UpdatePolicyRequest,
    ) -> PolicyResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._repository.get_policy_by_id(conn, policy_id)
            if existing is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=existing.org_id,
            )

            # Resolve fields — use existing values as defaults
            threat_type_id = request.threat_type_id or existing.threat_type_id
            actions = request.actions if request.actions is not None else existing.actions
            cooldown_minutes = request.cooldown_minutes if request.cooldown_minutes is not None else existing.cooldown_minutes

            # Validate if threat_type_id changed
            if request.threat_type_id is not None:
                await self._validate_threat_type_reference(
                    conn,
                    org_id=existing.org_id,
                    threat_type_id=request.threat_type_id,
                )

            # Validate if actions changed
            if request.actions is not None:
                await self._validate_actions(conn, request.actions)

            # Create new version
            new_version = await self._repository.get_next_version(
                conn, org_id, existing.policy_code
            )
            new_policy_id = str(uuid.uuid4())

            await self._repository.create_policy(
                conn,
                id=new_policy_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=existing.workspace_id,
                policy_code=existing.policy_code,
                version_number=new_version,
                threat_type_id=threat_type_id,
                actions=actions,
                is_enabled=existing.is_enabled,
                cooldown_minutes=cooldown_minutes,
                created_by=user_id,
                now=now,
            )

            # Copy existing properties and overlay new ones
            existing_props = await self._repository.get_policy_properties(conn, policy_id)
            merged_props = dict(existing_props)
            if request.properties:
                merged_props.update(request.properties)
                merged_props = _normalize_policy_properties(
                    merged_props,
                    require_container=False,
                )
            if merged_props:
                await self._repository.upsert_properties(
                    conn, new_policy_id, merged_props, created_by=user_id, now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="policy",
                    entity_id=new_policy_id,
                    event_type=SandboxAuditEventType.POLICY_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "policy_code": existing.policy_code,
                        "previous_version": str(existing.version_number),
                        "new_version": str(new_version),
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, new_policy_id)
            fetched_props = await self._repository.get_policy_properties(conn, new_policy_id)
        return _policy_response(record, fetched_props)

    async def delete_policy(
        self, *, user_id: str, tenant_key: str, org_id: str, policy_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=record.org_id,
            )
            deleted = await self._repository.soft_delete(conn, policy_id, deleted_by=user_id, now=now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="policy",
                    entity_id=policy_id,
                    event_type=SandboxAuditEventType.POLICY_DELETED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="policy",
                entity_id=policy_id,
                event_type="deleted",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def enable_policy(
        self, *, user_id: str, tenant_key: str, org_id: str, policy_id: str
    ) -> PolicyResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            updated = await self._repository.update_enabled(conn, policy_id, True, updated_by=user_id, now=now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="policy",
                    entity_id=policy_id,
                    event_type=SandboxAuditEventType.POLICY_ENABLED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="policy",
                entity_id=policy_id,
                event_type="enabled",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            props = await self._repository.get_policy_properties(conn, policy_id)
        return _policy_response(record, props)

    async def disable_policy(
        self, *, user_id: str, tenant_key: str, org_id: str, policy_id: str
    ) -> PolicyResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            updated = await self._repository.update_enabled(conn, policy_id, False, updated_by=user_id, now=now)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="policy",
                    entity_id=policy_id,
                    event_type=SandboxAuditEventType.POLICY_DISABLED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="policy",
                entity_id=policy_id,
                event_type="disabled",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            props = await self._repository.get_policy_properties(conn, policy_id)
        return _policy_response(record, props)

    async def test_policy(
        self, *, user_id: str, policy_id: str
    ) -> PolicyTestResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.execute",
                org_id=record.org_id,
            )

        # Dry-run simulation — stub: simulate each action would fire
        actions = _normalize_actions(record.actions)
        simulated = []
        for action in actions:
            simulated.append({
                "action_type": action.get("action_type", "unknown"),
                "config": action.get("config", {}),
                "result": "would_execute",
            })

        would_fire = record.is_enabled and len(actions) > 0

        return PolicyTestResponse(
            actions_simulated=simulated,
            would_fire=would_fire,
        )

    async def list_versions(
        self, *, user_id: str, org_id: str, policy_id: str
    ) -> list[PolicyResponse]:
        async with self._database_pool.acquire() as conn:
            # First get the policy to find its code
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
            versions = await self._repository.list_versions(conn, org_id, record.policy_code)
            version_ids = [v.id for v in versions]
            all_props = await self._repository.list_policy_properties_batch(conn, version_ids)
            results = [_policy_response(v, all_props.get(v.id, {})) for v in versions]
        return results

    async def list_executions(
        self, *, user_id: str, policy_id: str, limit: int = 100, offset: int = 0
    ) -> list[PolicyExecutionResponse]:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
            executions = await self._repository.list_policy_executions(
                conn, policy_id, limit=limit, offset=offset,
            )
        return [
            PolicyExecutionResponse(
                id=e.id,
                policy_id=e.policy_id,
                threat_evaluation_id=e.threat_evaluation_id,
                actions_executed=e.actions_executed,
                actions_failed=e.actions_failed,
                executed_at=e.created_at,
            )
            for e in executions
        ]

    async def execute_policy(
        self,
        *,
        tenant_key: str,
        org_id: str,
        policy_id: str,
        threat_evaluation_id: str | None = None,
        actor_id: str,
    ) -> PolicyExecutionResponse:
        """Internal method: execute a policy when a threat triggers.
        Not directly exposed via API.
        """
        now = utc_now_sql()
        execution_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_policy_by_id(conn, policy_id)
            if record is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")

            actions_executed = []
            actions_failed = []
            actions = _normalize_actions(record.actions)

            # Dispatch each action — stub implementation
            for action in actions:
                action_type = action.get("action_type", "unknown")
                try:
                    # Stub: in the future, dispatch to appropriate handler
                    actions_executed.append({
                        "action_type": action_type,
                        "config": action.get("config", {}),
                        "status": "executed",
                    })
                except Exception as exc:
                    actions_failed.append({
                        "action_type": action_type,
                        "config": action.get("config", {}),
                        "error": str(exc),
                    })

            await self._repository.insert_policy_execution(
                conn,
                id=execution_id,
                tenant_key=tenant_key,
                org_id=org_id,
                policy_id=policy_id,
                threat_evaluation_id=threat_evaluation_id,
                actions_executed=actions_executed,
                actions_failed=actions_failed,
                created_by=actor_id,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="policy_execution",
                    entity_id=execution_id,
                    event_type=SandboxAuditEventType.POLICY_EXECUTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=actor_id,
                    actor_type="system",
                    properties={
                        "policy_id": policy_id,
                        "actions_executed_count": str(len(actions_executed)),
                        "actions_failed_count": str(len(actions_failed)),
                    },
                ),
            )

        return PolicyExecutionResponse(
            id=execution_id,
            policy_id=policy_id,
            threat_evaluation_id=threat_evaluation_id,
            actions_executed=actions_executed,
            actions_failed=actions_failed,
            executed_at=str(now),
        )

    async def _validate_actions(
        self, conn, actions: list[dict]
    ) -> None:
        """Check each action_type exists in 09_dim_policy_action_types."""
        for action in actions:
            action_type = action.get("action_type")
            if not action_type:
                raise ValidationError("Each action must have an 'action_type' field")
            row = await conn.fetchrow(
                f'SELECT code FROM {SCHEMA}."09_dim_policy_action_types" WHERE code = $1 AND is_active = TRUE',
                action_type,
            )
            if row is None:
                raise ValidationError(f"Unknown action_type '{action_type}'")


def _policy_response(r, properties: dict[str, str] | None = None) -> PolicyResponse:
    actions = _normalize_actions(r.actions)

    return PolicyResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        policy_code=r.policy_code,
        version_number=r.version_number,
        threat_type_id=r.threat_type_id,
        threat_code=r.threat_code,
        actions=actions,
        is_enabled=r.is_enabled,
        cooldown_minutes=r.cooldown_minutes,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
        properties=properties if properties else None,
    )


def _normalize_policy_properties(
    properties: dict[str, str] | None,
    *,
    require_container: bool,
) -> dict[str, str]:
    try:
        return normalize_policy_container_properties(
            properties,
            required=require_container,
        )
    except ValueError as exc:
        raise ValidationError(str(exc)) from exc


def _normalize_actions(actions):
    if isinstance(actions, str):
        try:
            import json

            actions = json.loads(actions)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(actions, list):
        return []

    normalized: list[dict] = []
    for action in actions:
        if isinstance(action, str):
            try:
                import json

                action = json.loads(action)
            except (json.JSONDecodeError, TypeError):
                continue
        if isinstance(action, dict):
            normalized.append(action)
    return normalized
