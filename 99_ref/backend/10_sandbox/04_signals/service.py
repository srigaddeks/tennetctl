from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from importlib import import_module

from .repository import SignalRepository
from .schemas import (
    CreateSignalRequest,
    GenerateSignalRequest,
    GenerateSignalResponse,
    SignalListResponse,
    SignalResponse,
    SignalVersionResponse,
    UpdateSignalRequest,
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

_CACHE_KEY_PREFIX = "sb:signals"
_CACHE_TTL = 300


@instrument_class_methods(
    namespace="sandbox.signals.service",
    logger_name="backend.sandbox.signals.instrumentation",
)
class SignalService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = SignalRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.signals")

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

    async def _get_signal_or_not_found(self, conn, signal_id: str):
        record = await self._repository.get_signal_by_id(conn, signal_id)
        if record is None:
            raise NotFoundError(f"Signal '{signal_id}' not found")
        return record

    async def _get_test_dataset_or_not_found(
        self, conn, test_dataset_id: str
    ) -> dict[str, str | None]:
        row = await conn.fetchrow(
            """
            SELECT id::text AS id,
                   org_id::text AS org_id,
                   workspace_id::text AS workspace_id,
                   dataset_source_code
            FROM "15_sandbox"."21_fct_datasets"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            test_dataset_id,
        )
        if row is None:
            raise NotFoundError(f"Dataset '{test_dataset_id}' not found")
        return {
            "id": row["id"],
            "org_id": row["org_id"],
            "workspace_id": row["workspace_id"],
            "dataset_source_code": row["dataset_source_code"],
        }

    async def _load_test_cases_from_dataset(
        self,
        conn,
        *,
        test_dataset_id: str,
    ) -> tuple[list[dict], int]:
        rows = await self._fetch_dataset_case_rows(
            conn, test_dataset_id=test_dataset_id
        )
        test_cases: list[dict] = []
        invalid_records = 0

        for row in rows:
            extracted = _extract_test_cases(row["payload"])
            if extracted:
                test_cases.extend(extracted)
            else:
                invalid_records += 1

        return test_cases, invalid_records

    async def _fetch_dataset_case_rows(self, conn, *, test_dataset_id: str):
        query_variants = (
            (
                "dataset_records",
                """
                SELECT record_data::text AS payload
                FROM "15_sandbox"."43_dtl_dataset_records"
                WHERE dataset_id = $1::uuid
                ORDER BY record_seq ASC
                """,
            ),
            (
                "dataset_payloads_payload_data",
                """
                SELECT payload_data::text AS payload
                FROM "15_sandbox"."43_dtl_dataset_payloads"
                WHERE dataset_id = $1::uuid
                ORDER BY created_at ASC
                """,
            ),
            (
                "dataset_payloads_payload",
                """
                SELECT payload::text AS payload
                FROM "15_sandbox"."43_dtl_dataset_payloads"
                WHERE dataset_id = $1::uuid
                ORDER BY created_at ASC
                """,
            ),
        )

        last_exc: Exception | None = None
        for variant_name, sql in query_variants:
            try:
                return await conn.fetch(sql, test_dataset_id)
            except Exception as exc:
                if not _is_missing_dataset_storage_error(exc):
                    raise
                last_exc = exc
                self._logger.debug(
                    "signal_test_suite.dataset_storage_variant_unavailable",
                    extra={
                        "dataset_id": test_dataset_id,
                        "variant": variant_name,
                        "error": str(exc)[:200],
                    },
                )

        if last_exc is not None:
            raise ValidationError(
                "Selected dataset could not be loaded for test execution because its record storage layout is unsupported."
            ) from last_exc

        return []

    async def _resolve_live_connector_scope(
        self,
        conn,
        *,
        org_id: str,
        requested_connector_instance_id: str | None,
        signal_properties: dict[str, str],
    ) -> tuple[str | None, list[str]]:
        if requested_connector_instance_id:
            return requested_connector_instance_id, [requested_connector_instance_id]

        connector_type_codes = _parse_csv_codes(
            signal_properties.get("connector_types")
        )
        if not connector_type_codes:
            return None, []

        rows = await conn.fetch(
            """
            SELECT id::text AS id
            FROM "15_sandbox"."20_fct_connector_instances"
            WHERE org_id = $1::uuid
              AND provider_definition_code = ANY($2::text[])
              AND is_active = TRUE
              AND is_deleted = FALSE
            ORDER BY id ASC
            """,
            org_id,
            connector_type_codes,
        )
        connector_ids = [row["id"] for row in rows]
        if len(connector_ids) == 1:
            return connector_ids[0], connector_ids
        return None, connector_ids

    # ── list ──────────────────────────────────────────────────

    async def list_signals(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        signal_status_code: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> SignalListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
                workspace_id=workspace_id,
            )
            records, total = await self._repository.list_signals(
                conn,
                org_id,
                workspace_id=workspace_id,
                signal_status_code=signal_status_code,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_signal_response(r) for r in records]
        return SignalListResponse(items=items, total=total)

    # ── get ───────────────────────────────────────────────────

    async def get_signal(self, *, user_id: str, signal_id: str) -> SignalResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        async with self._database_pool.acquire() as conn:
            props = await self._repository.get_signal_properties(conn, signal_id)
        resp = _signal_response(record)
        resp.properties = props
        return resp

    # ── create ────────────────────────────────────────────────

    async def create_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: CreateSignalRequest,
    ) -> SignalResponse:
        if "name" not in request.properties:
            raise ValidationError("properties must include 'name'")
        if "python_source" not in request.properties:
            raise ValidationError("properties must include 'python_source'")

        python_source = request.properties["python_source"]
        python_hash = hashlib.sha256(python_source.encode("utf-8")).hexdigest()

        now = utc_now_sql()
        signal_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
                workspace_id=request.workspace_id,
            )
            version_number = await self._repository.get_next_version(
                conn, org_id, request.signal_code
            )
            if version_number > 1:
                raise ConflictError(
                    f"Signal code '{request.signal_code}' already exists."
                )
            await self._repository.create_signal(
                conn,
                id=signal_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                signal_code=request.signal_code,
                version_number=version_number,
                signal_status_code="draft",
                python_hash=python_hash,
                timeout_ms=request.timeout_ms,
                max_memory_mb=request.max_memory_mb,
                created_by=user_id,
                now=now,
            )
            await self._repository.upsert_properties(
                conn,
                signal_id,
                request.properties,
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="signal",
                    entity_id=signal_id,
                    event_type=SandboxAuditEventType.SIGNAL_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "signal_code": request.signal_code,
                        "version_number": str(version_number),
                        "name": request.properties.get("name", ""),
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="signal",
                entity_id=signal_id,
                event_type="created",
                actor_id=user_id,
                new_value="draft",
                properties={"signal_code": request.signal_code},
            )
        await self._invalidate_cache(org_id)
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_signal_by_id(conn, signal_id)
        return _signal_response(record)

    # ── update (new version) ──────────────────────────────────

    async def update_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        signal_id: str,
        request: UpdateSignalRequest,
    ) -> SignalResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )

            # Copy existing properties
            old_props = await self._repository.get_signal_properties(conn, signal_id)

            # Merge with new properties
            merged_props = dict(old_props)
            if request.properties:
                merged_props.update(request.properties)

            # Compute new hash if python_source changed
            python_source = merged_props.get("python_source", "")
            python_hash = hashlib.sha256(python_source.encode("utf-8")).hexdigest()

            # Create new version
            version_number = await self._repository.get_next_version(
                conn, org_id, existing.signal_code
            )
            new_signal_id = str(uuid.uuid4())

            await self._repository.create_signal(
                conn,
                id=new_signal_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=existing.workspace_id,
                signal_code=existing.signal_code,
                version_number=version_number,
                signal_status_code="draft",
                python_hash=python_hash,
                timeout_ms=request.timeout_ms or existing.timeout_ms,
                max_memory_mb=request.max_memory_mb or existing.max_memory_mb,
                created_by=user_id,
                now=now,
            )

            await self._repository.upsert_properties(
                conn,
                new_signal_id,
                merged_props,
                created_by=user_id,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="signal",
                    entity_id=new_signal_id,
                    event_type=SandboxAuditEventType.SIGNAL_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "signal_code": existing.signal_code,
                        "previous_version_id": signal_id,
                        "version_number": str(version_number),
                    },
                ),
            )

        await self._invalidate_cache(org_id)
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_signal_by_id(conn, new_signal_id)
        return _signal_response(record)

    # ── delete ────────────────────────────────────────────────

    async def delete_signal(
        self, *, user_id: str, tenant_key: str, org_id: str, signal_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            signal = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=signal.org_id,
                workspace_id=signal.workspace_id,
            )
            # Look up the signal to get its code for reference checking
            # Check for threat type references before deleting
            ref_count = await conn.fetchval(
                f"""SELECT count(*) FROM "15_sandbox"."23_fct_threat_types"
                    WHERE org_id = $1 AND is_deleted = FALSE
                    AND expression_tree::text LIKE '%' || $2 || '%' """,
                org_id,
                signal.signal_code,
            )
            if ref_count > 0:
                raise ConflictError(
                    f"Signal '{signal.signal_code}' is referenced by {ref_count} threat type(s). "
                    "Remove references before deleting."
                )
            deleted = await self._repository.soft_delete_signal(
                conn,
                signal_id,
                deleted_by=user_id,
                now=now,
            )
            if not deleted:
                raise NotFoundError(f"Signal '{signal_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="signal",
                    entity_id=signal_id,
                    event_type=SandboxAuditEventType.SIGNAL_DELETED.value,
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
                entity_type="signal",
                entity_id=signal_id,
                event_type="deleted",
                actor_id=user_id,
            )
        await self._invalidate_cache(org_id)

    # ── validate ──────────────────────────────────────────────

    async def validate_signal(
        self, *, user_id: str, tenant_key: str, signal_id: str
    ) -> SignalResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )

        test_results = await self.run_test_suite(
            user_id=user_id,
            tenant_key=tenant_key,
            org_id=record.org_id,
            signal_id=signal_id,
        )
        if test_results["total_cases"] <= 0:
            raise ValidationError(
                "Signal cannot be validated until it has at least one executable test case."
            )
        if test_results["failed"] > 0 or test_results["errored"] > 0:
            raise ValidationError(
                "Signal test suite must pass completely before validation."
            )

        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            current = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=current.org_id,
                workspace_id=current.workspace_id,
            )
            await self._repository.update_signal_status(
                conn,
                signal_id,
                "validated",
                updated_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="signal",
                    entity_id=signal_id,
                    event_type=SandboxAuditEventType.SIGNAL_VALIDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "cases_total": str(test_results["total_cases"]),
                        "passed": str(test_results["passed"]),
                        "failed": str(test_results["failed"]),
                        "errored": str(test_results["errored"]),
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=current.org_id,
                entity_type="signal",
                entity_id=signal_id,
                event_type="status_changed",
                actor_id=user_id,
                old_value="testing",
                new_value="validated",
            )

        await self._invalidate_cache(record.org_id)
        async with self._database_pool.acquire() as conn:
            updated = await self._repository.get_signal_by_id(conn, signal_id)
        return _signal_response(updated)

    # ── generate (AI agent) ──────────────────────────────────

    async def generate_signal(
        self, *, user_id: str, request: GenerateSignalRequest
    ) -> GenerateSignalResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")

        # Load sample dataset if provided
        sample_dataset: dict | None = None
        dataset_schema: dict = {}

        if request.sample_dataset_id:
            try:
                _dataset_module = import_module(
                    "backend.10_sandbox.03_datasets.repository"
                )
                DatasetRepository = _dataset_module.DatasetRepository  # noqa: N806
                dataset_repo = DatasetRepository()
                async with self._database_pool.acquire() as conn:
                    ds_record = await dataset_repo.get_dataset_by_id(
                        conn,
                        request.sample_dataset_id,
                    )
                if ds_record is not None:
                    ds_props: dict[str, str] = {}
                    async with self._database_pool.acquire() as conn:
                        ds_props = await dataset_repo.get_dataset_properties(
                            conn,
                            request.sample_dataset_id,
                        )
                    raw_json = ds_props.get("json_payload", "{}")
                    import json as _json

                    sample_dataset = _json.loads(raw_json)
            except Exception as exc:
                self._logger.warning(
                    "Failed to load sample dataset %s: %s",
                    request.sample_dataset_id,
                    exc,
                )

        # Infer schema from sample or use empty
        if sample_dataset:
            _agent_tools_mod = import_module("backend.10_sandbox.13_signal_agent.tools")
            dataset_schema = _agent_tools_mod.AgentTools.infer_dataset_schema(
                sample_dataset
            )

        # Build agent (lazy imports via import_module for numeric directory names)
        _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
        _agent_mod = import_module("backend.10_sandbox.13_signal_agent.agent")
        _agent_tools_mod = import_module("backend.10_sandbox.13_signal_agent.tools")

        SignalExecutionEngine = _engine_mod.SignalExecutionEngine  # noqa: N806
        SignalGenerationAgent = _agent_mod.SignalGenerationAgent  # noqa: N806
        AgentTools = _agent_tools_mod.AgentTools  # noqa: N806

        engine = SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
        )
        tools = AgentTools(execution_engine=engine)
        # Resolve LLM config via AgentConfigResolver
        _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
        _signal_llm_mod = import_module("backend.10_sandbox.13_signal_agent.llm_config")
        AgentConfigResolver = _resolver_mod.AgentConfigResolver  # noqa: N806
        AgentConfigRepository = _config_repo_mod.AgentConfigRepository  # noqa: N806
        get_effective_signal_generation_llm_config = (
            _signal_llm_mod.get_effective_signal_generation_llm_config
        )
        resolver = AgentConfigResolver(
            repository=AgentConfigRepository(),
            database_pool=self._database_pool,
            settings=self._settings,
        )
        llm_config = await resolver.resolve(
            agent_type_code="signal_generate", org_id=None
        )
        llm_config = get_effective_signal_generation_llm_config(
            llm_config=llm_config,
            settings=self._settings,
        )

        agent = SignalGenerationAgent(
            llm_config=llm_config,
            settings=self._settings,
            tools=tools,
        )

        # Build initial state
        state = {
            "prompt": request.prompt,
            "connector_type": request.connector_type_code,
            "dataset_schema": dataset_schema,
            "sample_dataset": sample_dataset,
            "asset_version_code": request.asset_version_code,
            "configurable_args": {},
            "max_iterations": 10,
        }

        # Run the agent
        result = await agent.run(state)

        compile_status = "success" if result.get("is_complete") else "failed"
        if result.get("compile_error"):
            compile_status = "compile_error"

        # Audit the generation event.
        # The audit table stores entity_id as a UUID, so use a synthetic id here
        # because this endpoint returns generated code and does not persist a signal yet.
        now = utc_now_sql()
        generation_entity_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key="system",
                    entity_type="signal",
                    entity_id=generation_entity_id,
                    event_type=SandboxAuditEventType.SIGNAL_GENERATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "prompt": request.prompt[:200],
                        "connector_type_code": request.connector_type_code or "",
                        "compile_status": compile_status,
                        "iterations_used": str(result.get("iteration", 0)),
                        "sample_dataset_id": request.sample_dataset_id or "",
                    },
                ),
            )

        return GenerateSignalResponse(
            generated_code=result.get("final_code") or result.get("generated_code", ""),
            compile_status=compile_status,
            test_result=result.get("test_result"),
            caep_event_type=result.get("caep_event_type"),
            risc_event_type=result.get("risc_event_type"),
            custom_event_type=result.get("custom_event_uri"),
            iterations_used=result.get("iterations_used", 0),
            signal_name_suggestion=result.get("signal_name_suggestion", ""),
            signal_description_suggestion=result.get(
                "signal_description_suggestion", ""
            ),
            signal_args_schema=result.get("signal_args_schema"),
            ssf_mapping=result.get("ssf_mapping"),
        )

    # ── execute signal ─────────────────────────────────────────

    async def execute_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        signal_id: str,
        dataset: dict | None = None,
        configurable_args: dict | None = None,
    ) -> dict:
        """Execute a signal against a dataset with optional configurable args.
        If dataset is not provided, loads the signal's test dataset.
        Returns execution result dict. SSF emission is fire-and-forget.
        """
        import asyncio as _asyncio
        import json as _json

        async with self._database_pool.acquire() as conn:
            record = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.execute",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )

        async with self._database_pool.acquire() as conn:
            props = await self._repository.get_signal_properties(conn, signal_id)

        python_source = props.get("python_source", "")
        if not python_source:
            raise ValidationError(
                "Signal has no python_source — generate or upload code first"
            )

        # Load test dataset if not provided
        if dataset is None:
            test_bundle_json = props.get("test_bundle_json")
            if test_bundle_json:
                try:
                    test_bundle = _json.loads(test_bundle_json)
                    test_cases = test_bundle.get("test_cases", [])
                    if test_cases:
                        first_case = test_cases[0]
                        dataset = first_case.get("dataset_input", {})
                except Exception:
                    pass

            if not dataset:
                resolved_test_dataset_id = props.get("test_dataset_id")
                if resolved_test_dataset_id:
                    async with self._database_pool.acquire() as conn:
                        await self._get_test_dataset_or_not_found(
                            conn, resolved_test_dataset_id
                        )
                        test_cases, _ = await self._load_test_cases_from_dataset(
                            conn, test_dataset_id=resolved_test_dataset_id
                        )
                        if test_cases:
                            dataset = test_cases[0].get("dataset_input", {})

            if not dataset:
                raise ValidationError(
                    "No dataset provided and signal has no test dataset"
                )

        # Run in sandbox
        _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
        SignalExecutionEngine = _engine_mod.SignalExecutionEngine  # noqa: N806
        engine = SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
        )
        result = await engine.execute(
            python_source=python_source,
            dataset=dataset,
            configurable_args=configurable_args or {},
        )

        now = utc_now_sql()

        # Audit
        async with self._database_pool.transaction() as conn:
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="signal",
                    entity_id=signal_id,
                    event_type=SandboxAuditEventType.SIGNAL_EXECUTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "status": result.status,
                        "result_code": result.result_code or "",
                        "execution_time_ms": str(result.execution_time_ms),
                        "has_configurable_args": str(bool(configurable_args)),
                    },
                ),
            )

        # SSF emission — fire-and-forget, never blocks, never fails the caller
        async def _emit_ssf() -> None:
            try:
                if not getattr(self._settings, "ssf_signing_key", None):
                    return
                ssf_mapping_raw = props.get("signal_ssf_mapping")
                if not ssf_mapping_raw:
                    return
                if result.result_code not in ("fail", "warning"):
                    return
                ssf_mapping = _json.loads(ssf_mapping_raw)
                _ssf_mod = import_module(
                    "backend.10_sandbox.12_ssf_transmitter.service"
                )
                _ssf_svc = _ssf_mod.SSFTransmitterService(
                    settings=self._settings,
                    database_pool=self._database_pool,
                    cache=self._cache,
                )
                await _ssf_svc.emit_set(
                    org_id=org_id,
                    tenant_key=tenant_key,
                    signal_code=record.signal_code,
                    signal_properties={
                        "signal_id": signal_id,
                        "result": result.result_code,
                    },
                    result={"summary": result.result_summary},
                    caep_event_type=ssf_mapping.get("event_type")
                    if ssf_mapping.get("standard") == "caep"
                    else None,
                    risc_event_type=ssf_mapping.get("event_type")
                    if ssf_mapping.get("standard") == "risc"
                    else None,
                )
            except Exception:
                self._logger.warning(
                    "signal_ssf.emit_failed", extra={"signal_id": signal_id}
                )

        _asyncio.create_task(_emit_ssf())

        return {
            "status": result.status,
            "result_code": result.result_code,
            "result_summary": result.result_summary,
            "result_details": result.result_details,
            "metadata": result.metadata,
            "stdout_capture": result.stdout_capture,
            "error_message": result.error_message,
            "execution_time_ms": result.execution_time_ms,
        }

    # ── versions ──────────────────────────────────────────────

    async def list_versions(
        self, *, user_id: str, org_id: str, signal_id: str
    ) -> list[SignalVersionResponse]:
        async with self._database_pool.acquire() as conn:
            record = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        async with self._database_pool.acquire() as conn:
            rows = await self._repository.list_versions(
                conn, org_id, record.signal_code
            )
        return [
            SignalVersionResponse(
                version_number=r["version_number"],
                signal_status_code=r["signal_status_code"],
                python_hash=r["python_hash"],
                created_at=r["created_at"],
                created_by=r["created_by"],
            )
            for r in rows
        ]

    # ── runs (stub) ───────────────────────────────────────────

    async def list_runs(self, *, user_id: str, signal_id: str) -> dict:
        async with self._database_pool.acquire() as conn:
            record = await self._get_signal_or_not_found(conn, signal_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        # Stub: will query runs module
        return {"items": [], "total": 0}

    # ── Bulk import ────────────────────────────────────────────

    async def bulk_import(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        signals: list[dict],
    ) -> dict:
        """
        Bulk-create or bulk-update signals from a list of definitions.
        Upserts by signal_code: if code exists, creates a new version; otherwise creates new.
        """
        import hashlib as _hashlib
        import json as _json

        results = []
        created = 0
        updated = 0
        failed = 0

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")

            for sig_def in signals:
                signal_code = sig_def.get("signal_code", "")
                try:
                    python_source = sig_def.get("python_source", "")
                    python_hash = _hashlib.sha256(python_source.encode()).hexdigest()

                    # Check if signal with this code already exists
                    existing = await conn.fetchrow(
                        """
                        SELECT id, version_number FROM "15_sandbox"."22_fct_signals"
                        WHERE org_id = $1::uuid AND signal_code = $2
                        ORDER BY version_number DESC LIMIT 1
                        """,
                        org_id,
                        signal_code,
                    )

                    if existing:
                        # Create new version
                        import uuid as _uuid

                        new_id = str(_uuid.uuid4())
                        new_version = existing["version_number"] + 1
                        await conn.execute(
                            """
                            INSERT INTO "15_sandbox"."22_fct_signals"
                                (id, tenant_key, org_id, workspace_id, signal_code,
                                 version_number, signal_status_code, python_hash,
                                 timeout_ms, max_memory_mb, is_active, created_by)
                            VALUES ($1::uuid, $2, $3::uuid, $4::uuid, $5,
                                    $6, 'draft', $7, $8, $9, true, $10::uuid)
                            """,
                            new_id,
                            tenant_key,
                            org_id,
                            workspace_id,
                            signal_code,
                            new_version,
                            python_hash,
                            sig_def.get("timeout_ms", 5000),
                            sig_def.get("max_memory_mb", 128),
                            user_id,
                        )
                        signal_id = new_id
                        updated += 1
                        action = "updated"
                    else:
                        # Create new signal
                        import uuid as _uuid

                        new_id = str(_uuid.uuid4())
                        await conn.execute(
                            """
                            INSERT INTO "15_sandbox"."22_fct_signals"
                                (id, tenant_key, org_id, workspace_id, signal_code,
                                 version_number, signal_status_code, python_hash,
                                 timeout_ms, max_memory_mb, is_active, created_by)
                            VALUES ($1::uuid, $2, $3::uuid, $4::uuid, $5,
                                    1, 'draft', $6, $7, $8, true, $9::uuid)
                            """,
                            new_id,
                            tenant_key,
                            org_id,
                            workspace_id,
                            signal_code,
                            python_hash,
                            sig_def.get("timeout_ms", 5000),
                            sig_def.get("max_memory_mb", 128),
                            user_id,
                        )
                        signal_id = new_id
                        created += 1
                        action = "created"

                    # Write EAV properties
                    props_to_write = {
                        "name": sig_def.get("name", signal_code),
                        "description": sig_def.get("description", ""),
                        "python_source": python_source,
                    }
                    connector_types = sig_def.get("connector_type_codes", [])
                    if connector_types:
                        props_to_write["connector_types"] = ",".join(connector_types)

                    for key, value in props_to_write.items():
                        if value:
                            prop_id = str(_uuid.uuid4())
                            await conn.execute(
                                """
                                INSERT INTO "15_sandbox"."45_dtl_signal_properties"
                                    (id, signal_id, property_key, property_value)
                                VALUES ($1::uuid, $2::uuid, $3, $4)
                                ON CONFLICT (signal_id, property_key)
                                    DO UPDATE SET property_value = EXCLUDED.property_value,
                                                  updated_at = now()
                                """,
                                prop_id,
                                signal_id,
                                key,
                                str(value),
                            )

                    results.append(
                        {
                            "signal_code": signal_code,
                            "status": action,
                            "signal_id": signal_id,
                        }
                    )
                except Exception as exc:
                    self._logger.warning(
                        "bulk_import: failed for %s: %s", signal_code, exc
                    )
                    failed += 1
                    results.append(
                        {
                            "signal_code": signal_code,
                            "status": "failed",
                            "error": str(exc),
                        }
                    )

        # Invalidate cache
        if hasattr(self, "_cache") and self._cache:
            await self._cache.delete(f"sb:signals:{org_id}")

        return {
            "total": len(signals),
            "created": created,
            "updated": updated,
            "failed": failed,
            "results": results,
        }

    # ── Test suite ─────────────────────────────────────────────

    async def run_test_suite(
        self,
        *,
        user_id: str,
        tenant_key: str,
        signal_id: str,
        org_id: str | None = None,
        test_dataset_id: str | None = None,
        configurable_args: dict | None = None,
    ) -> dict:
        """
        Run the signal's AI test dataset against the current code.
        Compares actual vs expected result_code per test case.
        """
        import time as _time
        from .schemas import TestCaseResult, TestSuiteResponse

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            record = await self._repository.get_signal_by_id(conn, signal_id)
            if record is None:
                raise NotFoundError(f"Signal '{signal_id}' not found")
            props = await self._repository.get_signal_properties(conn, signal_id)

        python_source = props.get("python_source", "")
        if not python_source:
            raise ValidationError("Signal has no python_source")

        resolved_test_dataset_id = test_dataset_id or props.get("test_dataset_id")
        test_bundle_json = None if test_dataset_id else props.get("test_bundle_json")

        test_cases: list[dict] = []
        invalid_dataset_records = 0
        selected_dataset_source_code: str | None = None

        if test_bundle_json:
            test_cases = _extract_test_cases(test_bundle_json)

        if not test_cases and resolved_test_dataset_id:
            async with self._database_pool.acquire() as conn:
                dataset = await self._get_test_dataset_or_not_found(
                    conn, resolved_test_dataset_id
                )
                await self._require_sandbox_permission(
                    conn,
                    user_id=user_id,
                    permission_code="sandbox.view",
                    org_id=dataset["org_id"] or "",
                    workspace_id=dataset["workspace_id"],
                )
                if dataset["org_id"] != record.org_id:
                    raise ValidationError(
                        "Test dataset must belong to the same organization as the signal"
                    )

                selected_dataset_source_code = dataset["dataset_source_code"]
                (
                    test_cases,
                    invalid_dataset_records,
                ) = await self._load_test_cases_from_dataset(
                    conn,
                    test_dataset_id=resolved_test_dataset_id,
                )

        if not test_cases and resolved_test_dataset_id and invalid_dataset_records > 0:
            if selected_dataset_source_code != "ai_generated_tests":
                raise ValidationError(
                    "Selected dataset is not a signal test dataset. Choose an AI-generated test dataset, or use Execute Live for real GitHub data."
                )
            raise ValidationError(
                "Selected test dataset contains no valid test cases. Each record must include 'dataset_input' and 'expected_output'."
            )

        if not test_cases:
            from .schemas import TestSuiteResponse

            return TestSuiteResponse(
                signal_id=signal_id,
                test_dataset_id=resolved_test_dataset_id,
                total_cases=0,
                passed=0,
                failed=0,
                errored=0,
                pass_rate=0.0,
                results=[],
            ).model_dump()

        _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
        SignalExecutionEngine = _engine_mod.SignalExecutionEngine
        engine = SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
        )

        results = []
        for case in test_cases:
            t0 = _time.monotonic()
            dataset_input = case.get("dataset_input", {})
            expected = case.get("expected_output", {})
            case_args = (
                configurable_args or case.get("configurable_args_override") or {}
            )

            try:
                exec_result = await engine.execute(
                    python_source=python_source,
                    dataset=dataset_input,
                    configurable_args=case_args,
                )
                actual_code = (
                    exec_result.result_code
                    if exec_result.status == "completed"
                    else "error"
                )
                error_msg = (
                    exec_result.error_message
                    if exec_result.status != "completed"
                    else None
                )
            except Exception as e:
                actual_code = "error"
                error_msg = str(e)[:500]
                exec_result = None

            expected_code = expected.get("result", "pass")
            passed = actual_code == expected_code
            elapsed_ms = int((_time.monotonic() - t0) * 1000)

            diff = {}
            if not passed and exec_result:
                diff = {
                    "expected_summary": expected.get("summary", ""),
                    "actual_summary": getattr(exec_result, "result_summary", ""),
                }

            results.append(
                {
                    "case_id": case.get("case_id"),
                    "scenario_name": case.get("scenario_name"),
                    "expected": expected_code,
                    "actual": actual_code,
                    "passed": passed,
                    "error": error_msg,
                    "execution_time_ms": elapsed_ms,
                    "diff": diff,
                }
            )

        passed_count = sum(1 for r in results if r["passed"])
        failed_count = sum(
            1 for r in results if not r["passed"] and r.get("actual") != "error"
        )
        errored_count = sum(1 for r in results if r.get("actual") == "error")
        total = len(results)
        pass_rate = round(passed_count / total, 3) if total else 0.0

        return {
            "signal_id": signal_id,
            "test_dataset_id": resolved_test_dataset_id,
            "total_cases": total,
            "passed": passed_count,
            "failed": failed_count,
            "errored": errored_count,
            "pass_rate": pass_rate,
            "results": results,
        }

    async def execute_live(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        signal_id: str,
        connector_instance_id: str | None = None,
        configurable_args: dict | None = None,
    ) -> dict:
        """
        Execute signal against the latest collected asset properties for the connector.
        Builds a dataset on-the-fly from current 54_dtl_asset_properties.
        """
        import time as _time

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            record = await self._repository.get_signal_by_id(conn, signal_id)
            if record is None:
                raise NotFoundError(f"Signal '{signal_id}' not found")
            props = await self._repository.get_signal_properties(conn, signal_id)

        python_source = props.get("python_source", "")
        if not python_source:
            raise ValidationError("Signal has no python_source")

        async with self._database_pool.acquire() as conn:
            (
                resolved_connector_instance_id,
                connector_scope_ids,
            ) = await self._resolve_live_connector_scope(
                conn,
                org_id=org_id,
                requested_connector_instance_id=connector_instance_id,
                signal_properties=props,
            )
            conditions = [
                "a.tenant_key = $1",
                "a.org_id = $2::uuid",
                "a.is_deleted = FALSE",
            ]
            params: list[object] = [tenant_key, org_id]
            idx = 3
            if resolved_connector_instance_id:
                conditions.append(f"a.connector_instance_id = ${idx}::uuid")
                params.append(resolved_connector_instance_id)
                idx += 1
            elif connector_scope_ids:
                conditions.append(f"a.connector_instance_id = ANY(${idx}::uuid[])")
                params.append(connector_scope_ids)
                idx += 1

            try:
                rows = await conn.fetch(
                    f"""
                    SELECT a.id::text AS asset_id,
                           a.connector_instance_id::text AS connector_instance_id,
                           a.asset_external_id,
                           a.asset_type_code,
                           jsonb_object_agg(p.property_key, p.property_value) AS properties
                    FROM "15_sandbox"."33_fct_assets" a
                    JOIN "15_sandbox"."54_dtl_asset_properties" p ON p.asset_id = a.id
                    WHERE {" AND ".join(conditions)}
                    GROUP BY a.id, a.asset_type_code
                    LIMIT 500
                    """,
                    *params,
                )
            except Exception as exc:
                raise ValidationError(
                    f"Unable to load live asset data for signal execution: {exc}"
                ) from exc

        # Compose dataset grouped by asset_type
        composed: dict[str, list[dict]] = {}
        for r in rows:
            asset_type = r["asset_type_code"] or "unknown"
            asset_props = _normalize_live_asset_payload(
                r["properties"],
                asset_id=r["asset_id"],
                asset_type=asset_type,
                asset_external_id=r["asset_external_id"],
                connector_instance_id=r["connector_instance_id"],
            )
            composed.setdefault(asset_type, []).append(asset_props)

        row_count = sum(len(v) for v in composed.values())
        if row_count <= 0:
            raise ValidationError(
                "No live asset rows were found for this signal. Collect connector data first, or choose a connector instance with collected assets."
            )

        execution_dataset = _augment_live_dataset_shape(composed)

        t0 = _time.monotonic()
        _engine_mod = import_module("backend.10_sandbox.07_execution.engine")
        SignalExecutionEngine = _engine_mod.SignalExecutionEngine
        engine = SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
        )
        exec_result = await engine.execute(
            python_source=python_source,
            dataset=execution_dataset,
            configurable_args=configurable_args or {},
        )
        elapsed_ms = int((_time.monotonic() - t0) * 1000)

        return {
            "signal_id": signal_id,
            "status": exec_result.status,
            "result_code": exec_result.result_code,
            "result_summary": exec_result.result_summary,
            "result_details": exec_result.result_details,
            "metadata": exec_result.metadata,
            "dataset_row_count": row_count,
            "execution_time_ms": elapsed_ms,
        }

    # ── cache ─────────────────────────────────────────────────

    async def _invalidate_cache(self, org_id: str) -> None:
        if not isinstance(self._cache, NullCacheManager):
            await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")


def _signal_response(r) -> SignalResponse:
    return SignalResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        signal_code=r.signal_code,
        version_number=r.version_number,
        signal_status_code=r.signal_status_code,
        signal_status_name=r.signal_status_name,
        python_hash=r.python_hash,
        timeout_ms=r.timeout_ms,
        max_memory_mb=r.max_memory_mb,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
        python_source=r.python_source,
        source_prompt=r.source_prompt,
        caep_event_type=r.caep_event_type,
        risc_event_type=r.risc_event_type,
    )


def _parse_csv_codes(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _normalize_live_asset_payload(
    payload: object,
    *,
    asset_id: str | None,
    asset_type: str | None,
    asset_external_id: str | None,
    connector_instance_id: str | None,
) -> dict:
    parsed = _decode_json_like(payload)
    normalized = dict(parsed) if isinstance(parsed, dict) else {}
    for key, value in list(normalized.items()):
        if isinstance(key, str) and key.endswith("_at"):
            normalized[key] = _normalize_signal_datetime_value(value)
    if asset_id and "_asset_id" not in normalized:
        normalized["_asset_id"] = asset_id
    if asset_type and "_asset_type" not in normalized:
        normalized["_asset_type"] = asset_type
    if asset_external_id and "_external_id" not in normalized:
        normalized["_external_id"] = asset_external_id
    if connector_instance_id and "_connector_instance_id" not in normalized:
        normalized["_connector_instance_id"] = connector_instance_id
    return normalized


def _normalize_signal_datetime_value(value: object) -> object:
    if not isinstance(value, str):
        return value
    candidate = value.strip()
    if not candidate:
        return value

    try:
        parsed = datetime.datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError:
        return value

    if parsed.tzinfo is None:
        return candidate
    return parsed.astimezone(datetime.timezone.utc).replace(tzinfo=None).isoformat()


def _infer_github_repo_full_name(repo_payload: dict) -> str | None:
    explicit = repo_payload.get("repository_full_name")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    owner = repo_payload.get("owner_login") or repo_payload.get("organization")
    name = repo_payload.get("name")
    if (
        isinstance(owner, str)
        and owner.strip()
        and isinstance(name, str)
        and name.strip()
    ):
        return f"{owner.strip()}/{name.strip()}"

    external_id = repo_payload.get("_external_id")
    if isinstance(external_id, str) and external_id.count("/") == 1:
        return external_id
    return None


def _infer_github_workflow_repo_name(workflow_payload: dict) -> str | None:
    explicit = workflow_payload.get("repository_full_name")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip()

    external_id = workflow_payload.get("_external_id")
    if isinstance(external_id, str) and "/" in external_id:
        repo_name, _, workflow_name = external_id.rpartition("/")
        if repo_name.count("/") >= 1 and workflow_name:
            return repo_name
    return None


def _build_github_repository_dataset(composed: dict[str, list[dict]]) -> list[dict]:
    repositories: dict[str, dict] = {}

    for repo_payload in composed.get("github_repo", []):
        repo_name = _infer_github_repo_full_name(repo_payload)
        if not repo_name:
            continue
        repo_entry = repositories.setdefault(
            repo_name,
            {"name": repo_name, "full_name": repo_name, "workflows": []},
        )
        for key, value in repo_payload.items():
            if key == "name":
                repo_entry.setdefault("repository_name", value)
                continue
            repo_entry.setdefault(key, value)

    for workflow_payload in composed.get("github_workflow", []):
        repo_name = _infer_github_workflow_repo_name(workflow_payload) or "unknown"
        repo_entry = repositories.setdefault(
            repo_name,
            {"name": repo_name, "full_name": repo_name, "workflows": []},
        )
        workflow = dict(workflow_payload)
        if "enabled" not in workflow:
            workflow["enabled"] = str(workflow.get("state", "")).lower() == "active"
        repo_entry["workflows"].append(workflow)

    ordered_repositories = []
    for repo_name in sorted(repositories):
        repo_entry = dict(repositories[repo_name])
        repo_entry["workflows"] = sorted(
            repo_entry.get("workflows", []),
            key=lambda item: str(item.get("name", "")),
        )
        ordered_repositories.append(repo_entry)
    return ordered_repositories


def _build_github_workflow_dataset(composed: dict[str, list[dict]]) -> list[dict]:
    workflows: list[dict] = []
    for workflow_payload in composed.get("github_workflow", []):
        workflow = dict(workflow_payload)
        workflow.setdefault(
            "repository",
            _infer_github_workflow_repo_name(workflow_payload) or "unknown",
        )
        workflow.setdefault(
            "active", str(workflow.get("state", "")).lower() == "active"
        )
        workflow.setdefault("inventory_collected", True)
        workflows.append(workflow)
    return sorted(
        workflows,
        key=lambda item: (
            str(item.get("repository", "")),
            str(item.get("name", "")),
        ),
    )


def _augment_live_dataset_shape(composed: dict[str, list[dict]]) -> dict[str, object]:
    normalized = {
        asset_type: [
            _normalize_live_asset_payload(
                item,
                asset_id=item.get("_asset_id") if isinstance(item, dict) else None,
                asset_type=asset_type,
                asset_external_id=item.get("_external_id")
                if isinstance(item, dict)
                else None,
                connector_instance_id=item.get("_connector_instance_id")
                if isinstance(item, dict)
                else None,
            )
            for item in records
        ]
        for asset_type, records in composed.items()
    }

    if "github_workflow" in normalized or "github_repo" in normalized:
        repositories = _build_github_repository_dataset(normalized)
        if repositories:
            normalized["repositories"] = repositories
        workflows = _build_github_workflow_dataset(normalized)
        if workflows:
            normalized["workflows"] = workflows

    return normalized


def _extract_test_cases(payload: object) -> list[dict]:
    parsed = _decode_json_like(payload)
    if isinstance(parsed, list):
        cases: list[dict] = []
        for item in parsed:
            normalized = _normalize_test_case(item)
            if normalized is not None:
                cases.append(normalized)
        return cases

    normalized = _normalize_test_case(parsed)
    return [normalized] if normalized is not None else []


def _normalize_test_case(payload: object) -> dict | None:
    parsed = _decode_json_like(payload)
    if not isinstance(parsed, dict):
        return None

    dataset_input = _decode_json_like(parsed.get("dataset_input"))
    if not isinstance(dataset_input, dict):
        return None

    expected_output_raw = parsed.get("expected_output", {})
    expected_output = _decode_json_like(expected_output_raw)
    if expected_output_raw is not None and not isinstance(expected_output, dict):
        return None

    normalized = dict(parsed)
    normalized["dataset_input"] = dataset_input
    normalized["expected_output"] = (
        expected_output if isinstance(expected_output, dict) else {}
    )
    return normalized


def _decode_json_like(payload: object) -> object:
    parsed = payload
    for _ in range(2):
        if not isinstance(parsed, str):
            break
        try:
            parsed = json.loads(parsed)
        except (TypeError, ValueError, json.JSONDecodeError):
            return None
    return parsed


def _is_missing_dataset_storage_error(exc: Exception) -> bool:
    error_name = exc.__class__.__name__
    if error_name in {"UndefinedTableError", "UndefinedColumnError"}:
        return True
    message = str(exc).lower()
    return "does not exist" in message or "undefined column" in message
