from __future__ import annotations

import json
import uuid
from importlib import import_module

from .repository import VariableQueryRepository, validate_sql_template
from ..schemas import (
    BindParamDefinition,
    CreateVariableQueryRequest,
    PreviewQueryRequest,
    QueryPreviewResponse,
    ResultColumnDefinition,
    TestQueryRequest,
    UpdateVariableQueryRequest,
    VariableQueryListResponse,
    VariableQueryResponse,
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
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_QUERIES = "notif:variable_queries"
_CACHE_KEY_CONFIG = "notif:config"
_CACHE_TTL = 300  # 5 minutes

_AUDIT_ENTITY_TYPE = "variable_query"
_AUDIT_EVENT_CATEGORY = "notification"

# All allowed bind param keys
ALLOWED_BIND_PARAM_KEYS = frozenset({
    "$user_id", "$tenant_key", "$actor_id",
    "$org_id", "$workspace_id",
    "$framework_id", "$control_id", "$task_id", "$risk_id",
})


@instrument_class_methods(
    namespace="variable_queries.service",
    logger_name="backend.notifications.variable_queries.instrumentation",
)
class VariableQueryService:
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
        self._repository = VariableQueryRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.notifications.variable_queries")

    # ── List ───────────────────────────────────────────────────────────

    async def list_queries(
        self, *, user_id: str, tenant_key: str
    ) -> VariableQueryListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            queries, total = await self._repository.list_queries(conn, tenant_key)

        items = []
        for q in queries:
            variable_keys = _extract_variable_keys(q.code, q.result_columns)
            items.append(_query_response(q, variable_keys))
        return VariableQueryListResponse(items=items, total=total)

    # ── Create ─────────────────────────────────────────────────────────

    async def create_query(
        self, *, user_id: str, tenant_key: str, request: CreateVariableQueryRequest
    ) -> VariableQueryResponse:
        _validate_bind_params(request.bind_params)
        validate_sql_template(request.sql_template)
        now = utc_now_sql()
        query_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.create")

            # Check for duplicate code
            existing = await self._repository.get_by_code(conn, request.code, tenant_key)
            if existing:
                raise ConflictError(f"Variable query with code '{request.code}' already exists")

            record = await self._repository.create(
                conn,
                id=query_id,
                tenant_key=tenant_key,
                code=request.code,
                name=request.name,
                description=request.description,
                sql_template=request.sql_template,
                bind_params=[bp.model_dump() for bp in request.bind_params],
                result_columns=[rc.model_dump() for rc in request.result_columns],
                timeout_ms=request.timeout_ms,
                linked_event_type_codes=request.linked_event_type_codes,
                created_by=user_id,
                now=now,
            )

            # Sync variable keys in 08_dim_template_variable_keys
            variable_keys = await self._repository.sync_variable_keys(
                conn,
                query_id=query_id,
                query_code=request.code,
                result_columns=[rc.model_dump() for rc in request.result_columns],
                now=now,
            )

            # Audit
            await self._audit_writer.write(
                conn,
                AuditEntry(
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=query_id,
                    event_type="variable_query_created",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    actor_id=user_id,
                    tenant_key=tenant_key,
                    properties={"code": request.code, "sql_template": request.sql_template},
                ),
            )

        await self._invalidate_caches(tenant_key)
        return _query_response(record, variable_keys)

    # ── Update ─────────────────────────────────────────────────────────

    async def update_query(
        self, *, user_id: str, query_id: str, request: UpdateVariableQueryRequest
    ) -> VariableQueryResponse:
        if request.sql_template is not None:
            validate_sql_template(request.sql_template)
        if request.bind_params is not None:
            _validate_bind_params(request.bind_params)

        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.update")

            existing = await self._repository.get_by_id(conn, query_id)
            if not existing:
                raise NotFoundError("Variable query not found")

            # Guard: system queries only allow name/description/is_active changes
            if existing.is_system:
                _blocked = []
                if request.sql_template is not None:
                    _blocked.append("sql_template")
                if request.bind_params is not None:
                    _blocked.append("bind_params")
                if request.result_columns is not None:
                    _blocked.append("result_columns")
                if _blocked:
                    raise ValidationError(
                        f"System queries cannot modify: {', '.join(_blocked)}. "
                        "Clone the query to create a custom version."
                    )

            fields: dict = {}
            if request.name is not None:
                fields["name"] = request.name
            if request.description is not None:
                fields["description"] = request.description
            if request.sql_template is not None:
                fields["sql_template"] = request.sql_template
            if request.bind_params is not None:
                fields["bind_params"] = [bp.model_dump() for bp in request.bind_params]
            if request.result_columns is not None:
                fields["result_columns"] = [rc.model_dump() for rc in request.result_columns]
            if request.timeout_ms is not None:
                fields["timeout_ms"] = request.timeout_ms
            if request.is_active is not None:
                fields["is_active"] = request.is_active
            if request.linked_event_type_codes is not None:
                fields["linked_event_type_codes"] = request.linked_event_type_codes

            record = await self._repository.update(conn, query_id, now=now, **fields)
            if not record:
                raise NotFoundError("Variable query not found")

            # Re-sync variable keys if result_columns changed
            result_cols = (
                [rc.model_dump() for rc in request.result_columns]
                if request.result_columns is not None
                else json.loads(record.result_columns)
            )
            variable_keys = await self._repository.sync_variable_keys(
                conn,
                query_id=query_id,
                query_code=record.code,
                result_columns=result_cols,
                now=now,
            )

            await self._audit_writer.write(
                conn,
                AuditEntry(
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=query_id,
                    event_type="variable_query_updated",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    actor_id=user_id,
                    tenant_key=record.tenant_key,
                    properties={"code": record.code, "fields": list(fields.keys())},
                ),
            )

        await self._invalidate_caches(record.tenant_key)
        return _query_response(record, variable_keys)

    # ── Delete ─────────────────────────────────────────────────────────

    async def delete_query(
        self, *, user_id: str, query_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.update")

            existing = await self._repository.get_by_id(conn, query_id)
            if not existing:
                raise NotFoundError("Variable query not found")

            if existing.is_system:
                raise ValidationError("System queries cannot be deleted")

            # Deactivate variable keys first
            await self._repository.deactivate_variable_keys(conn, query_id)

            ok = await self._repository.soft_delete(conn, query_id, now)
            if not ok:
                raise NotFoundError("Variable query not found")

            await self._audit_writer.write(
                conn,
                AuditEntry(
                    entity_type=_AUDIT_ENTITY_TYPE,
                    entity_id=query_id,
                    event_type="variable_query_deleted",
                    event_category=_AUDIT_EVENT_CATEGORY,
                    actor_id=user_id,
                    tenant_key=existing.tenant_key,
                    properties={"code": existing.code},
                ),
            )

        await self._invalidate_caches(existing.tenant_key)

    # ── Preview (saved query) ──────────────────────────────────────────

    async def preview_query(
        self,
        *,
        user_id: str,
        tenant_key: str,
        query_id: str,
        request: PreviewQueryRequest,
    ) -> QueryPreviewResponse:
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.view")

            record = await self._repository.get_by_id(conn, query_id)
            if not record:
                raise NotFoundError("Variable query not found")

            bind_params = json.loads(record.bind_params)
            param_values = dict(request.param_values)

            # Auto-fill from profile
            if request.use_my_profile:
                param_values.setdefault("$user_id", user_id)
                param_values.setdefault("$tenant_key", tenant_key)

            # Pull context from audit event
            if request.audit_event_id:
                audit_ctx = await self._repository.fetch_audit_event_context(
                    conn, request.audit_event_id
                )
                for key in ("org_id", "workspace_id", "framework_id",
                            "control_id", "task_id", "risk_id", "actor_id"):
                    if key in audit_ctx:
                        param_values.setdefault(f"${key}", audit_ctx[key])

            return await self._execute_with_params(
                conn,
                sql_template=record.sql_template,
                bind_params=bind_params,
                param_values=param_values,
                timeout_ms=record.timeout_ms,
            )

    # ── Test (ad-hoc SQL) ──────────────────────────────────────────────

    async def test_query(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: TestQueryRequest,
    ) -> QueryPreviewResponse:
        validate_sql_template(request.sql_template)
        _validate_bind_params(request.bind_params)

        param_values = dict(request.param_values)
        if request.use_my_profile:
            param_values.setdefault("$user_id", user_id)
            param_values.setdefault("$tenant_key", tenant_key)

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "notification_system.view")
            return await self._execute_with_params(
                conn,
                sql_template=request.sql_template,
                bind_params=[bp.model_dump() for bp in request.bind_params],
                param_values=param_values,
                timeout_ms=3000,
            )

    # ── Internal helpers ───────────────────────────────────────────────

    async def _execute_with_params(
        self,
        conn,
        *,
        sql_template: str,
        bind_params: list[dict],
        param_values: dict[str, str],
        timeout_ms: int,
    ) -> QueryPreviewResponse:
        """Build ordered params and execute the query safely."""
        # Sort bind_params by position
        sorted_params = sorted(bind_params, key=lambda p: p["position"])

        ordered: list = []
        resolved: dict[str, str] = {}
        for bp in sorted_params:
            key = bp["key"]
            value = param_values.get(key)
            if value is None and bp.get("default_value"):
                value = bp["default_value"]
            if value is None and bp.get("required", False):
                return QueryPreviewResponse(
                    success=False,
                    error=f"Required bind parameter {key} is not available",
                    resolved_params=resolved,
                )
            ordered.append(value)
            resolved[f"${bp['position']} ({key})"] = value or "(null)"

        try:
            rows, elapsed_ms = await self._repository.execute_query(
                conn,
                sql_template=sql_template,
                ordered_params=ordered,
                timeout_ms=timeout_ms,
            )
            columns = list(rows[0].keys()) if rows else []
            return QueryPreviewResponse(
                success=True,
                columns=columns,
                rows=rows[:10],  # Limit preview to 10 rows
                resolved_params=resolved,
                execution_ms=elapsed_ms,
            )
        except Exception as exc:
            self._logger.warning("Variable query execution failed: %s", exc)
            return QueryPreviewResponse(
                success=False,
                error=str(exc),
                resolved_params=resolved,
            )

    async def _invalidate_caches(self, tenant_key: str) -> None:
        await self._cache.delete(f"{_CACHE_KEY_QUERIES}:{tenant_key}")
        await self._cache.delete(_CACHE_KEY_CONFIG)


def _validate_bind_params(params: list[BindParamDefinition]) -> None:
    """Validate bind param keys are from the allowed set."""
    for bp in params:
        if bp.key not in ALLOWED_BIND_PARAM_KEYS:
            raise ValidationError(
                f"Invalid bind parameter key: {bp.key}. "
                f"Allowed: {', '.join(sorted(ALLOWED_BIND_PARAM_KEYS))}"
            )
    # Ensure positions are unique and sequential
    positions = sorted(bp.position for bp in params)
    expected = list(range(1, len(params) + 1))
    if positions != expected:
        raise ValidationError(
            f"Bind param positions must be sequential starting from 1. Got: {positions}"
        )


def _extract_variable_keys(code: str, result_columns_json: str) -> list[str]:
    """Generate the variable key codes from a query's result_columns."""
    cols = json.loads(result_columns_json) if isinstance(result_columns_json, str) else result_columns_json
    return [f"custom.{code}.{col['name']}" for col in cols]


def _query_response(record, variable_keys: list[str]) -> VariableQueryResponse:
    bind_params = json.loads(record.bind_params) if isinstance(record.bind_params, str) else record.bind_params
    result_columns = json.loads(record.result_columns) if isinstance(record.result_columns, str) else record.result_columns
    return VariableQueryResponse(
        id=record.id,
        tenant_key=record.tenant_key,
        code=record.code,
        name=record.name,
        description=record.description,
        sql_template=record.sql_template,
        bind_params=[BindParamDefinition(**bp) for bp in bind_params],
        result_columns=[ResultColumnDefinition(**rc) for rc in result_columns],
        timeout_ms=record.timeout_ms,
        is_active=record.is_active,
        is_system=record.is_system,
        variable_keys=variable_keys,
        linked_event_type_codes=list(record.linked_event_type_codes or []),
        created_at=record.created_at,
        updated_at=record.updated_at,
    )
