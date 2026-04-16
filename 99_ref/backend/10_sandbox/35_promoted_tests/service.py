from __future__ import annotations

import hashlib
import json
import uuid
from importlib import import_module

from .repository import PromotedTestRepository
from .schemas import (
    ExecutePromotedTestResponse,
    PromotedTestListResponse,
    PromotedTestResponse,
    UpdatePromotedTestRequest,
)

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_engine_module = import_module("backend.10_sandbox.07_execution.engine")
_settings_module = import_module("backend.00_config.settings")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
SignalExecutionEngine = _engine_module.SignalExecutionEngine

logger = get_logger(__name__)


@instrument_class_methods(
    namespace="sandbox.promoted_tests.service",
    logger_name="backend.sandbox.promoted_tests.instrumentation",
)
class PromotedTestService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = PromotedTestRepository()
        self._logger = get_logger("backend.sandbox.promoted_tests")

    async def _require_test_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
        workspace_id: str | None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def list_tests(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        search: str | None = None,
        linked_asset_id: str | None = None,
        is_active: bool | None = True,
        limit: int = 100,
        offset: int = 0,
    ) -> PromotedTestListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
                workspace_id=workspace_id,
            )
            items, total = await self._repository.list(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                search=search,
                linked_asset_id=linked_asset_id,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
        return PromotedTestListResponse(
            items=[_to_response(r) for r in items],
            total=total,
        )

    async def get_test(
        self, *, user_id: str, tenant_key: str, test_id: str
    ) -> PromotedTestResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_by_id(conn, test_id, tenant_key)
            if record is None:
                raise NotFoundError(f"Promoted test '{test_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        return _to_response(record)

    async def get_version_history(
        self, *, user_id: str, tenant_key: str, test_id: str
    ) -> PromotedTestListResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_by_id(conn, test_id, tenant_key)
            if record is None:
                raise NotFoundError(f"Promoted test '{test_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
            items = await self._repository.get_version_history(
                conn,
                tenant_key=tenant_key,
                org_id=record.org_id,
                test_code=record.test_code,
            )
        return PromotedTestListResponse(
            items=[_to_response(r) for r in items],
            total=len(items),
        )

    async def update_test(
        self,
        *,
        user_id: str,
        tenant_key: str,
        test_id: str,
        request: UpdatePromotedTestRequest,
    ) -> PromotedTestResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_by_id(conn, test_id, tenant_key)
            if record is None:
                raise NotFoundError(f"Promoted test '{test_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )

            # Update fact table columns
            fact_fields: dict = {}
            if request.linked_asset_id is not None:
                fact_fields["linked_asset_id"] = request.linked_asset_id
            if fact_fields:
                await self._repository.update(
                    conn, test_id, tenant_key, fields=fact_fields, now=now
                )

            # Update EAV properties
            props: dict[str, str] = {}
            if request.name is not None:
                props["name"] = request.name
            if request.description is not None:
                props["description"] = request.description
            if props:
                await self._repository.upsert_properties(
                    conn, test_id, props, user_id, now
                )

            updated = await self._repository.get_by_id(conn, test_id, tenant_key)

        return _to_response(updated)

    async def delete_test(self, *, user_id: str, tenant_key: str, test_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._repository.get_by_id(conn, test_id, tenant_key)
            if record is None:
                raise NotFoundError(f"Promoted test '{test_id}' not found")
            await self._require_test_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
            await self._repository.soft_delete(conn, test_id, tenant_key, now)

    # ── execute promoted test ──────────────────────────────────────

    async def execute_test(
        self,
        *,
        user_id: str,
        tenant_key: str,
        test_id: str,
        dataset_id: str | None = None,
    ) -> ExecutePromotedTestResponse:
        """Execute a promoted test against its linked dataset/connector data."""
        now = utc_now_sql()
        engine = SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
        )

        async with self._database_pool.transaction() as conn:
            # 1. Load promoted test
            record = await self._repository.get_by_id(conn, test_id, tenant_key)
            if record is None:
                raise NotFoundError(f"Promoted test '{test_id}' not found")

            python_source = record.evaluation_rule
            if not python_source and record.source_signal_id:
                # Fallback: if property is missing, load from signal properties table
                self._logger.info(
                    f"Fallback loading evaluation_rule for test {test_id} from signal {record.source_signal_id}"
                )
                sig_source = await conn.fetchval(
                    'SELECT property_value FROM "15_sandbox"."45_dtl_signal_properties" WHERE signal_id = $1::uuid AND property_key = $2',
                    record.source_signal_id,
                    "python_source",
                )
                if sig_source:
                    python_source = sig_source
                else:
                    self._logger.warning(
                        f"No python_source found in 45_dtl_signal_properties for signal {record.source_signal_id}"
                    )

            if not python_source and record.source_library_id:
                # Global Library Fallback: load from the global test bundle
                self._logger.info(
                    f"Fallback loading evaluation_rule for test {test_id} from global {record.source_library_id}"
                )
                bundle_row = await conn.fetchval(
                    'SELECT bundle FROM "15_sandbox"."84_fct_global_control_tests" WHERE id = $1::uuid',
                    record.source_library_id,
                )
                if bundle_row:
                    bundle_data = (
                        json.loads(bundle_row)
                        if isinstance(bundle_row, str)
                        else bundle_row
                    )
                    g_signals = bundle_data.get("signals", [])
                    if g_signals:
                        python_source = g_signals[0].get("python_source")

            if not python_source:
                self._logger.error(
                    f"Execution failed: Promoted test {test_id} has no evaluation_rule (record={record.test_code})"
                )
                raise ValidationError(
                    "Promoted test has no evaluation_rule (python source)"
                )

            # 2. Find dataset to execute against
            actual_dataset_id = dataset_id
            if not actual_dataset_id and record.linked_asset_id:
                # Find the most recent dataset linked to this connector
                ds_row = await conn.fetchrow(
                    """
                    SELECT id FROM "15_sandbox"."21_fct_datasets"
                    WHERE org_id = $1 AND connector_instance_id = $2 AND is_deleted = FALSE
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    record.org_id,
                    record.linked_asset_id,
                )
                if ds_row:
                    actual_dataset_id = str(ds_row["id"])

            if not actual_dataset_id:
                # Try any dataset in the same org
                ds_row = await conn.fetchrow(
                    """
                    SELECT id FROM "15_sandbox"."21_fct_datasets"
                    WHERE org_id = $1 AND is_deleted = FALSE AND row_count > 0
                    ORDER BY created_at DESC LIMIT 1
                    """,
                    record.org_id,
                )
                if ds_row:
                    actual_dataset_id = str(ds_row["id"])

            if not actual_dataset_id:
                raise ValidationError(
                    "No dataset found to execute against. Link an asset or provide a dataset_id."
                )

            # 3. Load dataset records
            record_rows = await conn.fetch(
                """
                SELECT record_data FROM "15_sandbox"."43_dtl_dataset_records"
                WHERE dataset_id = $1 ORDER BY record_seq ASC
                """,
                actual_dataset_id,
            )
            if not record_rows:
                raise ValidationError("Dataset has no records")

            # Build dataset payload — group by _asset_type
            decoded_records = []
            for rr in record_rows:
                rd = rr["record_data"]
                if isinstance(rd, str):
                    try:
                        rd = json.loads(rd)
                    except (json.JSONDecodeError, TypeError):
                        continue
                if isinstance(rd, dict):
                    decoded_records.append(rd)
                elif isinstance(rd, list):
                    decoded_records.extend(rd)

            if not decoded_records:
                raise ValidationError("Dataset has no valid records")

            # Group by _asset_type for signal compatibility
            composed: dict[str, list[dict]] = {}
            for item in decoded_records:
                if not isinstance(item, dict):
                    continue
                asset_type = item.get("_asset_type")
                if isinstance(asset_type, str) and asset_type:
                    composed.setdefault(asset_type, []).append(item)

            if composed:
                dataset_payload: dict = dict(composed)
                dataset_payload["records"] = decoded_records
                dataset_payload["items"] = decoded_records
            else:
                dataset_payload = {"records": decoded_records, "items": decoded_records}

            # 4. Execute in sandbox
            result = await engine.execute(
                python_source=python_source,
                dataset=dataset_payload,
                timeout_ms=5000,
                max_memory_mb=128,
            )

            # 5. Map result
            if result.status == "completed":
                result_code = result.result_code or "pass"
                summary = result.result_summary or "Test completed"
            elif result.status == "timeout":
                result_code = "error"
                summary = "Test execution timed out"
            else:
                result_code = "error"
                summary = result.error_message or "Test execution failed"

            result_status_map = {
                "pass": "pass",
                "fail": "fail",
                "warning": "partial",
                "error": "error",
            }
            grc_result_status = result_status_map.get(result_code, "error")

            # 6. Record to GRC test_executions (if control_test_id exists)
            execution_id = None
            if record.control_test_id:
                execution_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."15_fct_test_executions"
                        (id, tenant_key, control_test_id, result_status, execution_type,
                         executed_by, executed_at, notes, evidence_summary,
                         is_active, created_by, updated_by)
                    VALUES ($1, $2, $3, $4, 'automated', $5, NOW(), $6, $7, TRUE, $5, $5)
                    """,
                    execution_id,
                    tenant_key,
                    record.control_test_id,
                    grc_result_status,
                    user_id,
                    f"Executed promoted test {record.test_code}",
                    json.dumps(
                        {
                            "result": result_code,
                            "summary": summary,
                            "details": result.result_details or [],
                        },
                        default=str,
                    )[:10000],
                )

            # 7. Auto-create issue on failure
            task_created = False
            task_id = None
            if result_code in ("fail", "error"):
                try:
                    _issue_service_module = import_module("backend.09_issues.service")
                    IssueService = _issue_service_module.IssueService
                    issue_service = IssueService(database_pool=self._database_pool)
                    issue_id = await issue_service.create_from_test_failure(
                        tenant_key=tenant_key,
                        org_id=record.org_id,
                        workspace_id=record.workspace_id,
                        promoted_test_id=test_id,
                        control_test_id=record.control_test_id,
                        execution_id=execution_id,
                        connector_id=record.linked_asset_id,
                        test_code=record.test_code,
                        test_name=record.name,
                        result_summary=summary,
                        result_details=result.result_details,
                        connector_type_code=record.connector_type_code,
                        severity_code="critical" if result_code == "error" else "high",
                        created_by=user_id,
                    )
                    task_created = (
                        True  # reuse field name for backward compat in response
                    )
                    task_id = issue_id
                except Exception as e:
                    logger.warning(f"Failed to auto-create issue for test failure: {e}")

        return ExecutePromotedTestResponse(
            test_id=test_id,
            test_code=record.test_code,
            result_status=result_code,
            summary=summary,
            details=result.result_details or [],
            metadata=result.metadata or {},
            execution_id=execution_id,
            executed_at=str(now),
            task_created=task_created,
            task_id=task_id,
        )


def _to_response(r) -> PromotedTestResponse:
    return PromotedTestResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        promotion_id=r.promotion_id,
        source_signal_id=r.source_signal_id,
        source_policy_id=r.source_policy_id,
        source_library_id=r.source_library_id,
        source_pack_id=r.source_pack_id,
        test_code=r.test_code,
        test_type_code=r.test_type_code,
        monitoring_frequency=r.monitoring_frequency,
        linked_asset_id=r.linked_asset_id,
        connector_type_code=r.connector_type_code,
        connector_name=r.connector_name,
        policy_container_code=r.policy_container_code,
        policy_container_name=r.policy_container_name,
        version_number=r.version_number,
        is_active=r.is_active,
        promoted_by=r.promoted_by,
        promoted_at=r.promoted_at,
        name=r.name,
        description=r.description,
        evaluation_rule=r.evaluation_rule,
        signal_type=r.signal_type,
        integration_guide=r.integration_guide,
        control_test_id=r.control_test_id,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
