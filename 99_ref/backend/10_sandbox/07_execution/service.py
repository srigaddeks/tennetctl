from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from importlib import import_module

from .engine import SignalExecutionEngine
from .repository import ExecutionRepository
from .schemas import (
    BatchExecuteResponse,
    PolicyExecutionResponse,
    RunListResponse,
    RunResponse,
    ThreatEvaluationListResponse,
    ThreatEvaluationResponse,
    PolicyExecutionListResponse,
)
from .threat_evaluator import evaluate_threat

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
_signal_repo_module = import_module("backend.10_sandbox.04_signals.repository")
_signal_service_module = import_module("backend.10_sandbox.04_signals.service")
_dataset_repo_module = import_module("backend.10_sandbox.03_datasets.repository")
_threat_repo_module = import_module("backend.10_sandbox.05_threat_types.repository")
_policy_repo_module = import_module("backend.10_sandbox.06_policies.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
SignalRepository = _signal_repo_module.SignalRepository
DatasetRepository = _dataset_repo_module.DatasetRepository
ThreatTypeRepository = _threat_repo_module.ThreatTypeRepository
PolicyRepository = _policy_repo_module.PolicyRepository
augment_live_dataset_shape = _signal_service_module._augment_live_dataset_shape

_CACHE_KEY_PREFIX = "sb:runs"
_CACHE_TTL = 60


@instrument_class_methods(
    namespace="sandbox.execution.service",
    logger_name="backend.sandbox.execution.instrumentation",
)
class ExecutionService:
    def __init__(self, *, settings, database_pool, cache, clickhouse) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._clickhouse = clickhouse
        self._repository = ExecutionRepository()
        self._signal_repository = SignalRepository()
        self._dataset_repository = DatasetRepository()
        self._threat_repository = ThreatTypeRepository()
        self._policy_repository = PolicyRepository()
        self._engine = SignalExecutionEngine()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.execution")

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

    @staticmethod
    def _decode_dataset_record(payload: object) -> object:
        parsed = payload
        for _ in range(3):
            if not isinstance(parsed, str):
                return parsed
            stripped = parsed.strip()
            if not stripped:
                return {}
            try:
                parsed = json.loads(stripped)
            except (TypeError, ValueError, json.JSONDecodeError):
                return parsed
        return parsed

    def _build_execution_dataset(
        self,
        *,
        dataset_source_code: str,
        records,
    ) -> dict[str, object]:
        decoded_records: list[object] = []
        for record in records:
            parsed = self._decode_dataset_record(record.record_data)
            if parsed is None:
                continue
            if isinstance(parsed, list):
                decoded_records.extend(parsed)
            else:
                decoded_records.append(parsed)

        if not decoded_records:
            raise ValidationError("Dataset has no executable records.")

        composed: dict[str, list[dict]] = {}
        for item in decoded_records:
            if not isinstance(item, dict):
                continue
            asset_type = item.get("_asset_type")
            if isinstance(asset_type, str) and asset_type:
                composed.setdefault(asset_type, []).append(item)

        if composed:
            dataset_payload = augment_live_dataset_shape(composed)
            dataset_payload["records"] = decoded_records
            dataset_payload["items"] = decoded_records
            return dataset_payload

        if len(decoded_records) == 1:
            first_record = decoded_records[0]
            if isinstance(first_record, dict):
                result = dict(first_record)
                result.setdefault("records", decoded_records)
                result.setdefault("items", decoded_records)
                return result
            if dataset_source_code != "connector_pull":
                return {
                    "records": [first_record],
                    "items": [first_record],
                    "value": first_record,
                }

        return {"records": decoded_records, "items": decoded_records}

    @classmethod
    def _normalize_expression_tree(cls, expression_tree: object) -> dict | None:
        parsed = cls._decode_dataset_record(expression_tree)
        if not isinstance(parsed, dict):
            return None

        normalized = dict(parsed)
        conditions = normalized.get("conditions")
        if isinstance(conditions, list):
            normalized["conditions"] = [
                child
                for child in (
                    cls._normalize_expression_tree(condition)
                    for condition in conditions
                )
                if child is not None
            ]
        return normalized

    @classmethod
    def _normalize_policy_actions(cls, actions: object) -> list[dict]:
        parsed_actions = cls._decode_dataset_record(actions)
        if not isinstance(parsed_actions, list):
            return []

        normalized: list[dict] = []
        for action in parsed_actions:
            parsed_action = cls._decode_dataset_record(action)
            if isinstance(parsed_action, dict):
                normalized.append(parsed_action)
        return normalized

    async def _load_dataset_payload(
        self,
        conn,
        *,
        dataset_id: str,
        org_id: str,
    ) -> tuple[dict[str, object], str]:
        dataset = await self._dataset_repository.get_dataset_by_id(conn, dataset_id)
        if dataset is None or dataset.org_id != org_id:
            raise NotFoundError(f"Dataset '{dataset_id}' not found")

        records = []
        offset = 0
        page_size = 500
        total = 0
        while True:
            page, total = await self._dataset_repository.list_records(
                conn,
                dataset_id,
                limit=page_size,
                offset=offset,
            )
            if not page:
                break
            records.extend(page)
            offset += len(page)
            if offset >= total:
                break

        if not records:
            raise ValidationError("Dataset has no records to execute.")

        dataset_payload = self._build_execution_dataset(
            dataset_source_code=dataset.dataset_source_code,
            records=records,
        )
        dataset_hash = hashlib.sha256(
            json.dumps(dataset_payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        return dataset_payload, dataset_hash

    # ── execute single signal ──────────────────────────────────────

    async def execute_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        signal_id: str,
        dataset_id: str,
    ) -> RunResponse:
        now = utc_now_sql()
        run_id = str(uuid.uuid4())

        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
            )

            # Load signal
            signal = await self._signal_repository.get_signal_by_id(conn, signal_id)
            if signal is None:
                raise NotFoundError(f"Signal '{signal_id}' not found")

            # Load signal python_source
            python_source = signal.python_source
            if not python_source:
                props = await self._signal_repository.get_signal_properties(
                    conn, signal_id
                )
                python_source = props.get("python_source", "")
            if not python_source:
                raise ValidationError("Signal has no python_source defined")

            dataset_payload, dataset_hash = await self._load_dataset_payload(
                conn,
                dataset_id=dataset_id,
                org_id=org_id,
            )

        # Execute in sandbox subprocess
        result = await self._engine.execute(
            python_source=python_source,
            dataset=dataset_payload,
            timeout_ms=signal.timeout_ms,
            max_memory_mb=signal.max_memory_mb,
        )

        # Map engine status to execution_status_code
        status_map = {
            "completed": "completed",
            "failed": "failed",
            "timeout": "timeout",
        }
        execution_status_code = status_map.get(result.status, "failed")

        completed_at = utc_now_sql()

        # Write to PG (fail/warning only) and ClickHouse (all)
        should_persist_pg = (
            result.result_code in ("fail", "warning", "error")
            or result.status != "completed"
        )

        if should_persist_pg:
            async with self._database_pool.transaction() as conn:
                await self._repository.insert_run(
                    conn,
                    id=run_id,
                    tenant_key=tenant_key,
                    org_id=org_id,
                    workspace_id=signal.workspace_id,
                    signal_id=signal_id,
                    dataset_id=dataset_id,
                    live_session_id=None,
                    execution_status_code=execution_status_code,
                    result_code=result.result_code
                    if result.status == "completed"
                    else None,
                    result_summary=result.result_summary or result.error_message,
                    result_details=result.result_details
                    if result.result_details
                    else None,
                    execution_time_ms=result.execution_time_ms,
                    error_message=result.error_message,
                    stdout_capture=result.stdout_capture or None,
                    python_source_snapshot=python_source,
                    dataset_snapshot_hash=dataset_hash,
                    started_at=now,
                    completed_at=completed_at,
                    created_by=user_id,
                )

                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="sandbox_run",
                        entity_id=run_id,
                        event_type=SandboxAuditEventType.SANDBOX_RUN_EXECUTED.value,
                        event_category="sandbox",
                        occurred_at=completed_at,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "signal_id": signal_id,
                            "signal_code": signal.signal_code,
                            "dataset_id": dataset_id,
                            "result_code": result.result_code or "",
                            "execution_status": execution_status_code,
                            "execution_time_ms": str(result.execution_time_ms),
                        },
                    ),
                )

        # Write to ClickHouse (all results including pass)
        try:
            await self._clickhouse.insert_signal_result(
                {
                    "run_id": run_id,
                    "tenant_key": tenant_key,
                    "org_id": org_id,
                    "signal_id": signal_id,
                    "signal_code": signal.signal_code,
                    "dataset_id": dataset_id,
                    "execution_status": execution_status_code,
                    "result_code": result.result_code,
                    "result_summary": result.result_summary,
                    "execution_time_ms": result.execution_time_ms,
                    "started_at": str(now),
                    "completed_at": str(completed_at),
                }
            )
        except Exception:
            self._logger.warning("clickhouse_insert_failed", extra={"run_id": run_id})

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        return RunResponse(
            id=run_id,
            tenant_key=tenant_key,
            org_id=org_id,
            signal_id=signal_id,
            signal_code=signal.signal_code,
            dataset_id=dataset_id,
            live_session_id=None,
            execution_status_code=execution_status_code,
            execution_status_name=None,
            result_code=result.result_code,
            result_summary=result.result_summary or result.error_message,
            result_details=result.result_details if result.result_details else None,
            execution_time_ms=result.execution_time_ms,
            error_message=result.error_message,
            stdout_capture=result.stdout_capture or None,
            started_at=str(now),
            completed_at=str(completed_at),
            created_at=str(completed_at),
            signal_name=signal.name,
        )

    # ── batch execute ──────────────────────────────────────────────

    async def batch_execute(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        signal_ids: list[str],
        dataset_id: str,
    ) -> BatchExecuteResponse:
        # 1. Execute signals concurrently (bounded by engine semaphore)
        signal_results: dict[str, RunResponse] = {}
        signal_result_codes: dict[str, str] = {}  # signal_code -> result_code
        signal_errors: list[str] = []

        async def _exec_one(sid: str) -> tuple[str, RunResponse]:
            resp = await self.execute_signal(
                user_id=user_id,
                tenant_key=tenant_key,
                org_id=org_id,
                signal_id=sid,
                dataset_id=dataset_id,
            )
            return sid, resp

        results = await asyncio.gather(
            *[_exec_one(sid) for sid in signal_ids],
            return_exceptions=True,
        )
        for item in results:
            if isinstance(item, Exception):
                signal_errors.append(str(item))
                self._logger.warning(
                    "batch_signal_exec_failed", extra={"error": str(item)}
                )
                continue
            sid, run_response = item
            signal_results[sid] = run_response
            if run_response.signal_code and run_response.result_code:
                signal_result_codes[run_response.signal_code] = run_response.result_code

        if not signal_results and signal_errors:
            raise ValidationError(
                f"No signals executed successfully in this batch run. First error: {signal_errors[0]}"
            )

        # 2. Find threat types that reference these signal_codes
        threat_evaluations: list[ThreatEvaluationResponse] = []
        policy_executions: list[PolicyExecutionResponse] = []

        if signal_result_codes:
            async with self._database_pool.acquire() as conn:
                threat_types, _ = await self._threat_repository.list_threat_types(
                    conn,
                    org_id,
                    limit=500,
                )

            # 3. Evaluate each threat type's expression tree
            # Pre-filter relevant threat types using set intersection
            signal_code_set = set(signal_result_codes.keys())
            relevant_threats: list[tuple[object, dict]] = []
            for threat_type in threat_types:
                normalized_expression = self._normalize_expression_tree(
                    threat_type.expression_tree
                )
                if not normalized_expression:
                    continue
                tree_json = json.dumps(normalized_expression)
                if any(code in tree_json for code in signal_code_set):
                    relevant_threats.append((threat_type, normalized_expression))

            # Evaluate and batch-write all threat evaluations in one transaction
            eval_data: list[
                tuple
            ] = []  # (eval_id, threat_type, expression, is_triggered, trace)
            for threat_type, normalized_expression in relevant_threats:
                is_triggered, trace = evaluate_threat(
                    normalized_expression,
                    signal_result_codes,
                )
                eval_data.append(
                    (
                        str(uuid.uuid4()),
                        threat_type,
                        normalized_expression,
                        is_triggered,
                        trace,
                    )
                )

            if eval_data:
                async with self._database_pool.transaction() as conn:
                    for (
                        eval_id,
                        threat_type,
                        normalized_expression,
                        is_triggered,
                        trace,
                    ) in eval_data:
                        await self._repository.insert_threat_evaluation(
                            conn,
                            id=eval_id,
                            tenant_key=tenant_key,
                            org_id=org_id,
                            threat_type_id=threat_type.id,
                            is_triggered=is_triggered,
                            signal_results=signal_result_codes,
                            expression_snapshot=normalized_expression,
                            live_session_id=None,
                            created_by=user_id,
                        )
                        await self._audit_writer.write_entry(
                            conn,
                            AuditEntry(
                                id=str(uuid.uuid4()),
                                tenant_key=tenant_key,
                                entity_type="threat_evaluation",
                                entity_id=eval_id,
                                event_type=SandboxAuditEventType.THREAT_EVALUATED.value,
                                event_category="sandbox",
                                occurred_at=utc_now_sql(),
                                actor_id=user_id,
                                actor_type="user",
                                properties={
                                    "threat_type_id": threat_type.id,
                                    "threat_code": threat_type.threat_code,
                                    "is_triggered": str(is_triggered),
                                },
                            ),
                        )

            for (
                eval_id,
                threat_type,
                normalized_expression,
                is_triggered,
                trace,
            ) in eval_data:
                # Write to ClickHouse (best-effort, outside transaction)
                try:
                    await self._clickhouse.insert_threat_evaluation(
                        {
                            "evaluation_id": eval_id,
                            "tenant_key": tenant_key,
                            "org_id": org_id,
                            "threat_type_id": threat_type.id,
                            "threat_code": threat_type.threat_code,
                            "is_triggered": is_triggered,
                            "signal_results": signal_result_codes,
                        }
                    )
                except Exception:
                    self._logger.warning(
                        "clickhouse_threat_eval_failed", extra={"eval_id": eval_id}
                    )

                threat_evaluations.append(
                    ThreatEvaluationResponse(
                        id=eval_id,
                        tenant_key=tenant_key,
                        org_id=org_id,
                        threat_type_id=threat_type.id,
                        is_triggered=is_triggered,
                        signal_results=signal_result_codes,
                        expression_snapshot=normalized_expression,
                        evaluation_trace=trace,
                        live_session_id=None,
                        evaluated_at=str(utc_now_sql()),
                        created_by=user_id,
                    )
                )

                # 4. If triggered, execute associated policies
                if is_triggered:
                    async with self._database_pool.acquire() as conn:
                        policies, _ = await self._policy_repository.list_policies(
                            conn,
                            org_id,
                            threat_type_id=threat_type.id,
                            is_enabled=True,
                        )

                    for policy in policies:
                        exec_id = str(uuid.uuid4())
                        actions_executed: list[dict] = []
                        actions_failed: list[dict] = []

                        for action in self._normalize_policy_actions(policy.actions):
                            # Actions are recorded but not yet executed (placeholder)
                            actions_executed.append(
                                {
                                    "action_type": action.get("action_type", "unknown"),
                                    "status": "recorded",
                                    "message": "Action recorded for future execution",
                                }
                            )

                        async with self._database_pool.transaction() as conn:
                            await self._repository.insert_policy_execution(
                                conn,
                                id=exec_id,
                                tenant_key=tenant_key,
                                org_id=org_id,
                                policy_id=policy.id,
                                threat_evaluation_id=eval_id,
                                actions_executed=actions_executed,
                                actions_failed=actions_failed
                                if actions_failed
                                else None,
                                created_by=user_id,
                            )

                            await self._audit_writer.write_entry(
                                conn,
                                AuditEntry(
                                    id=str(uuid.uuid4()),
                                    tenant_key=tenant_key,
                                    entity_type="policy_execution",
                                    entity_id=exec_id,
                                    event_type=SandboxAuditEventType.POLICY_EXECUTED.value,
                                    event_category="sandbox",
                                    occurred_at=utc_now_sql(),
                                    actor_id=user_id,
                                    actor_type="user",
                                    properties={
                                        "policy_id": policy.id,
                                        "policy_code": policy.policy_code,
                                        "threat_evaluation_id": eval_id,
                                        "actions_count": str(len(actions_executed)),
                                    },
                                ),
                            )

                        policy_executions.append(
                            PolicyExecutionResponse(
                                id=exec_id,
                                tenant_key=tenant_key,
                                org_id=org_id,
                                policy_id=policy.id,
                                threat_evaluation_id=eval_id,
                                actions_executed=actions_executed,
                                actions_failed=actions_failed
                                if actions_failed
                                else None,
                                executed_at=str(utc_now_sql()),
                                created_by=user_id,
                            )
                        )

        return BatchExecuteResponse(
            signal_results=signal_results,
            threat_evaluations=threat_evaluations,
            policy_executions=policy_executions,
        )

    # ── list runs ──────────────────────────────────────────────────

    async def list_runs(
        self,
        *,
        user_id: str,
        org_id: str,
        signal_id: str | None = None,
        dataset_id: str | None = None,
        execution_status_code: str | None = None,
        result_code: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> RunListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records, total = await self._repository.list_runs(
                conn,
                org_id,
                signal_id=signal_id,
                dataset_id=dataset_id,
                execution_status_code=execution_status_code,
                result_code=result_code,
                limit=limit,
                offset=offset,
            )

        items = [_run_record_to_response(r) for r in records]
        return RunListResponse(items=items, total=total)

    # ── get run ────────────────────────────────────────────────────

    async def get_run(
        self,
        *,
        user_id: str,
        run_id: str,
    ) -> RunResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_run_by_id(conn, run_id)
            if record is None:
                raise NotFoundError(f"Run '{run_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return _run_detail_to_response(record)

    # ── query history (ClickHouse) ─────────────────────────────────

    async def query_history(
        self,
        *,
        user_id: str,
        org_id: str,
        signal_code: str | None = None,
        days: int = 30,
        limit: int = 500,
    ) -> list[dict]:
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )

        if signal_code:
            return await self._clickhouse.query_signal_history(
                signal_code,
                days,
                limit,
            )
        return []

    # ── threat evaluations ─────────────────────────────────────────

    async def list_threat_evaluations(
        self,
        *,
        user_id: str,
        org_id: str,
        threat_type_id: str | None = None,
        is_triggered: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> ThreatEvaluationListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records, total = await self._repository.list_threat_evaluations(
                conn,
                org_id,
                threat_type_id=threat_type_id,
                is_triggered=is_triggered,
                limit=limit,
                offset=offset,
            )

        items = [_threat_eval_to_response(r) for r in records]
        return ThreatEvaluationListResponse(items=items, total=total)

    async def get_threat_evaluation(
        self,
        *,
        user_id: str,
        eval_id: str,
    ) -> ThreatEvaluationResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_threat_evaluation(conn, eval_id)
            if record is None:
                raise NotFoundError(f"Threat evaluation '{eval_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return _threat_eval_to_response(record)

    # ── policy executions ──────────────────────────────────────────

    async def list_policy_executions(
        self,
        *,
        user_id: str,
        org_id: str,
        policy_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> PolicyExecutionListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records, total = await self._repository.list_policy_executions(
                conn,
                org_id,
                policy_id=policy_id,
                limit=limit,
                offset=offset,
            )

        items = [_policy_exec_to_response(r) for r in records]
        return PolicyExecutionListResponse(items=items, total=total)

    async def get_policy_execution(
        self,
        *,
        user_id: str,
        exec_id: str,
    ) -> PolicyExecutionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_policy_execution(conn, exec_id)
            if record is None:
                raise NotFoundError(f"Policy execution '{exec_id}' not found")
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return _policy_exec_to_response(record)


# ── response mappers ──────────────────────────────────────────────


def _run_record_to_response(r) -> RunResponse:
    details = r.result_details
    # Handle double-serialized JSONB (stored as json.dumps(string))
    import json as _json

    for _ in range(3):  # up to 3 rounds of unwrapping
        if isinstance(details, str):
            try:
                details = _json.loads(details)
            except Exception:
                details = None
                break
        else:
            break
    return RunResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        signal_id=r.signal_id,
        signal_code=r.signal_code,
        dataset_id=r.dataset_id,
        live_session_id=r.live_session_id,
        execution_status_code=r.execution_status_code,
        execution_status_name=r.execution_status_name,
        result_code=r.result_code,
        result_summary=r.result_summary,
        result_details=details if isinstance(details, list) else None,
        execution_time_ms=r.execution_time_ms,
        started_at=r.started_at,
        completed_at=r.completed_at,
        created_at=r.created_at,
        signal_name=r.signal_name,
    )


def _run_detail_to_response(r) -> RunResponse:
    details = r.result_details
    # Handle double-serialized JSONB (stored as json.dumps(string))
    import json as _json

    for _ in range(3):  # up to 3 rounds of unwrapping
        if isinstance(details, str):
            try:
                details = _json.loads(details)
            except Exception:
                details = None
                break
        else:
            break
    return RunResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        signal_id=r.signal_id,
        signal_code=r.signal_code,
        dataset_id=r.dataset_id,
        live_session_id=r.live_session_id,
        execution_status_code=r.execution_status_code,
        execution_status_name=r.execution_status_name,
        result_code=r.result_code,
        result_summary=r.result_summary,
        result_details=details if isinstance(details, list) else None,
        execution_time_ms=r.execution_time_ms,
        error_message=r.error_message,
        stdout_capture=r.stdout_capture,
        started_at=r.started_at,
        completed_at=r.completed_at,
        created_at=r.created_at,
        signal_name=r.signal_name,
    )


def _threat_eval_to_response(r) -> ThreatEvaluationResponse:
    return ThreatEvaluationResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        threat_type_id=r.threat_type_id,
        is_triggered=r.is_triggered,
        signal_results=r.signal_results,
        expression_snapshot=r.expression_snapshot,
        live_session_id=r.live_session_id,
        evaluated_at=r.evaluated_at,
        created_by=r.created_by,
    )


def _policy_exec_to_response(r) -> PolicyExecutionResponse:
    return PolicyExecutionResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        policy_id=r.policy_id,
        threat_evaluation_id=r.threat_evaluation_id,
        actions_executed=r.actions_executed,
        actions_failed=r.actions_failed,
        executed_at=r.executed_at,
        created_by=r.created_by,
    )
