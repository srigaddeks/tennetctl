from __future__ import annotations

import uuid
from importlib import import_module

from .repository import ThreatTypeRepository
from .schemas import (
    EvaluationTraceEntry,
    SimulateThreatResponse,
    ThreatTypeListResponse,
    ThreatTypeResponse,
    CreateThreatTypeRequest,
    UpdateThreatTypeRequest,
    SimulateThreatRequest,
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

_CACHE_KEY_PREFIX = "sb:threats"
_CACHE_TTL = 300


@instrument_class_methods(namespace="sandbox.threat_types.service", logger_name="backend.sandbox.threat_types.instrumentation")
class ThreatTypeService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ThreatTypeRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.threat_types")

    async def _require_sandbox_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
        workspace_id: str | None = None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def _get_threat_type_or_not_found(self, conn, threat_type_id: str):
        record = await self._repository.get_threat_type_by_id(conn, threat_type_id)
        if record is None:
            raise NotFoundError(f"Threat type '{threat_type_id}' not found")
        return record

    async def list_threat_types(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        severity_code: str | None = None,
        search: str | None = None,
        sort_by: str = "threat_code",
        sort_dir: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> ThreatTypeListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{org_id}"
        if not any([workspace_id, severity_code, search]) and offset == 0 and limit == 100:
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return ThreatTypeListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
                workspace_id=workspace_id,
            )
            records, total = await self._repository.list_threat_types(
                conn,
                org_id,
                workspace_id=workspace_id,
                severity_code=severity_code,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
            # Batch-load properties for all records (avoids N+1)
            threat_type_ids = [r.id for r in records]
            all_props = await self._repository.list_threat_type_properties_batch(conn, threat_type_ids)

        items = [_threat_type_response(r, all_props.get(r.id, {})) for r in records]
        result = ThreatTypeListResponse(items=items, total=total)

        if not any([workspace_id, severity_code, search]) and offset == 0 and limit == 100:
            await self._cache.set_json(cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL)

        return result

    async def get_threat_type(
        self, *, user_id: str, threat_type_id: str
    ) -> ThreatTypeResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._get_threat_type_or_not_found(conn, threat_type_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
            properties = await self._repository.get_threat_type_properties(conn, threat_type_id)
        return _threat_type_response(record, properties)

    async def create_threat_type(
        self, *, user_id: str, tenant_key: str, org_id: str, request: CreateThreatTypeRequest
    ) -> ThreatTypeResponse:
        now = utc_now_sql()
        threat_type_id = str(uuid.uuid4())

        _validate_expression_tree(request.expression_tree)

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
                workspace_id=request.workspace_id,
            )
            version_number = await self._repository.get_next_version(
                conn, org_id, request.threat_code
            )
            await self._repository.create_threat_type(
                conn,
                id=threat_type_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                threat_code=request.threat_code,
                version_number=version_number,
                severity_code=request.severity_code,
                expression_tree=request.expression_tree,
                created_by=user_id,
                now=now,
            )
            props: dict[str, str] = {}
            if request.properties:
                props.update(request.properties)
            if props:
                await self._repository.upsert_properties(
                    conn, threat_type_id, props, created_by=user_id, now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="threat_type",
                    entity_id=threat_type_id,
                    event_type=SandboxAuditEventType.THREAT_TYPE_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "threat_code": request.threat_code,
                        "version_number": str(version_number),
                        "severity_code": request.severity_code,
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="threat_type",
                entity_id=threat_type_id,
                event_type="created",
                actor_id=user_id,
                properties={"threat_code": request.threat_code},
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_threat_type_by_id(conn, threat_type_id)
            properties = await self._repository.get_threat_type_properties(conn, threat_type_id)
        return _threat_type_response(record, properties)

    async def update_threat_type(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        threat_type_id: str,
        request: UpdateThreatTypeRequest,
    ) -> ThreatTypeResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._get_threat_type_or_not_found(conn, threat_type_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )

            expression_tree = request.expression_tree if request.expression_tree is not None else existing.expression_tree
            if request.expression_tree is not None:
                _validate_expression_tree(request.expression_tree)

            severity_code = request.severity_code if request.severity_code is not None else existing.severity_code

            # Create new version
            new_id = str(uuid.uuid4())
            version_number = await self._repository.get_next_version(
                conn, org_id, existing.threat_code
            )
            await self._repository.create_threat_type(
                conn,
                id=new_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=existing.workspace_id,
                threat_code=existing.threat_code,
                version_number=version_number,
                severity_code=severity_code,
                expression_tree=expression_tree,
                created_by=user_id,
                now=now,
            )

            # Copy existing properties and apply updates
            old_props = await self._repository.get_threat_type_properties(conn, threat_type_id)
            if request.properties:
                old_props.update(request.properties)
            if old_props:
                await self._repository.upsert_properties(
                    conn, new_id, old_props, created_by=user_id, now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="threat_type",
                    entity_id=new_id,
                    event_type=SandboxAuditEventType.THREAT_TYPE_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "threat_code": existing.threat_code,
                        "version_number": str(version_number),
                        "previous_version_id": threat_type_id,
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_threat_type_by_id(conn, new_id)
            properties = await self._repository.get_threat_type_properties(conn, new_id)
        return _threat_type_response(record, properties)

    async def delete_threat_type(
        self, *, user_id: str, tenant_key: str, org_id: str, threat_type_id: str
    ) -> None:
        SCHEMA = '"15_sandbox"'
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            existing = await self._get_threat_type_or_not_found(conn, threat_type_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            # Check for policies referencing this threat type
            ref_count = await conn.fetchval(
                f'''SELECT count(*) FROM {SCHEMA}."24_fct_policies"
                    WHERE threat_type_id = $1 AND is_deleted = FALSE''',
                threat_type_id,
            )
            if ref_count > 0:
                raise ConflictError(
                    f"Threat type referenced by {ref_count} policy(ies). "
                    "Remove policy references before deleting."
                )
            deleted = await self._repository.soft_delete(
                conn, threat_type_id, deleted_by=user_id, now=now,
            )
            if not deleted:
                raise NotFoundError(f"Threat type '{threat_type_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="threat_type",
                    entity_id=threat_type_id,
                    event_type=SandboxAuditEventType.THREAT_TYPE_DELETED.value,
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
                entity_type="threat_type",
                entity_id=threat_type_id,
                event_type="deleted",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def simulate_threat(
        self,
        *,
        user_id: str,
        threat_type_id: str,
        request: SimulateThreatRequest,
    ) -> SimulateThreatResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._get_threat_type_or_not_found(conn, threat_type_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.execute",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        expression_tree = _normalize_expression_tree(record.expression_tree)
        if expression_tree is None:
            raise ValidationError("Threat type has no expression tree defined")

        is_triggered, trace = _evaluate_expression(expression_tree, request.signal_results)
        return SimulateThreatResponse(
            is_triggered=is_triggered,
            evaluation_trace=trace,
        )

    async def list_versions(
        self,
        *,
        user_id: str,
        threat_type_id: str,
        org_id: str,
    ) -> list[ThreatTypeResponse]:
        async with self._database_pool.acquire() as conn:
            record = await self._get_threat_type_or_not_found(conn, threat_type_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
            records = await self._repository.list_versions(conn, org_id, record.threat_code)
        return [_threat_type_response(r) for r in records]

    async def _threat_type_response(self, record) -> ThreatTypeResponse:
        """Build response with properties loaded from DB."""
        async with self._database_pool.acquire() as conn:
            properties = await self._repository.get_threat_type_properties(conn, record.id)
        return _threat_type_response(record, properties)


def _validate_expression_tree(tree: dict) -> None:
    """Validate expression tree structure.

    Each node must have either:
    - {signal_code, expected_result} for leaf nodes
    - {operator: AND|OR|NOT, conditions: [...]} for composite nodes
    """
    if not isinstance(tree, dict):
        raise ValidationError("Expression tree must be a dictionary")

    if "signal_code" in tree:
        if "expected_result" not in tree:
            raise ValidationError(
                f"Leaf node with signal_code '{tree['signal_code']}' must have 'expected_result'"
            )
        return

    if "operator" in tree:
        operator = tree["operator"]
        if operator not in ("AND", "OR", "NOT"):
            raise ValidationError(
                f"Invalid operator '{operator}'. Must be AND, OR, or NOT"
            )
        if "conditions" not in tree or not isinstance(tree["conditions"], list):
            raise ValidationError(
                f"Operator node '{operator}' must have a 'conditions' list"
            )
        if operator == "NOT" and len(tree["conditions"]) != 1:
            raise ValidationError("NOT operator must have exactly one condition")
        if operator in ("AND", "OR") and len(tree["conditions"]) < 1:
            raise ValidationError(f"{operator} operator must have at least one condition")
        for condition in tree["conditions"]:
            _validate_expression_tree(condition)
        return

    raise ValidationError(
        "Each node must have either 'signal_code' (leaf) or 'operator' (composite)"
    )


def _evaluate_expression(tree: dict, signal_results: dict) -> tuple[bool, list]:
    """Recursively evaluate expression tree against signal results.

    Returns (result, trace) where trace is a list of EvaluationTraceEntry.
    """
    trace: list[EvaluationTraceEntry] = []

    if "signal_code" in tree:
        signal_code = tree["signal_code"]
        expected = tree["expected_result"]
        actual = signal_results.get(signal_code, "unknown")
        result = actual == expected
        trace.append(EvaluationTraceEntry(
            node_type="leaf",
            signal_code=signal_code,
            expected_result=expected,
            actual_result=actual,
            result=result,
        ))
        return result, trace

    operator = tree["operator"]
    conditions = tree["conditions"]

    if operator == "NOT":
        child_result, child_trace = _evaluate_expression(conditions[0], signal_results)
        trace.extend(child_trace)
        result = not child_result
        trace.append(EvaluationTraceEntry(
            node_type="operator",
            operator="NOT",
            result=result,
        ))
        return result, trace

    if operator == "AND":
        result = True
        for condition in conditions:
            child_result, child_trace = _evaluate_expression(condition, signal_results)
            trace.extend(child_trace)
            if not child_result:
                result = False
        trace.append(EvaluationTraceEntry(
            node_type="operator",
            operator="AND",
            result=result,
        ))
        return result, trace

    if operator == "OR":
        result = False
        for condition in conditions:
            child_result, child_trace = _evaluate_expression(condition, signal_results)
            trace.extend(child_trace)
            if child_result:
                result = True
        trace.append(EvaluationTraceEntry(
            node_type="operator",
            operator="OR",
            result=result,
        ))
        return result, trace

    return False, trace


def _threat_type_response(record, properties: dict[str, str] | None = None) -> ThreatTypeResponse:
    expression_tree = _normalize_expression_tree(record.expression_tree)

    return ThreatTypeResponse(
        id=record.id,
        tenant_key=record.tenant_key,
        org_id=record.org_id,
        workspace_id=record.workspace_id,
        threat_code=record.threat_code,
        version_number=record.version_number,
        severity_code=record.severity_code,
        severity_name=record.severity_name,
        expression_tree=expression_tree,
        is_active=record.is_active,
        created_at=record.created_at,
        updated_at=record.updated_at,
        name=record.name,
        description=record.description,
        properties=properties if properties else None,
    )


def _normalize_expression_tree(expression_tree):
    if isinstance(expression_tree, str):
        try:
            import json

            expression_tree = json.loads(expression_tree)
        except (json.JSONDecodeError, TypeError):
            return None
    if not isinstance(expression_tree, dict):
        return None

    normalized = dict(expression_tree)
    conditions = normalized.get("conditions")
    if isinstance(conditions, list):
        normalized["conditions"] = [
            child
            for child in (_normalize_expression_tree(condition) for condition in conditions)
            if child is not None
        ]
    return normalized
