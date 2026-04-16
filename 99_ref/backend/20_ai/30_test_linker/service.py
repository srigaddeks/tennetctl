"""Service for AI-powered control test ↔ control linking."""
from __future__ import annotations

import json
import uuid
from importlib import import_module

from .prompts import (
    BULK_SUGGEST_TESTS_SYSTEM,
    BULK_SUGGEST_TESTS_USER,
    SUGGEST_CONTROLS_FOR_TEST_PROMPT,
)
from .repository import TestLinkerRepository
from .schemas import (
    ApplyResult,
    ApplySuggestionsForControlRequest,
    ApplySuggestionsForTestRequest,
    BulkDecisionRequest,
    BulkDecisionResponse,
    BulkLinkJobResponse,
    BulkLinkRequest,
    JobStatusResponse,
    ListPendingMappingsQuery,
    PendingTestControlMappingListResponse,
    PendingTestControlMappingSchema,
    SuggestControlsRequest,
    SuggestTestsRequest,
    TestSuggestionSchema,
)

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_llm_utils_mod = import_module("backend.20_ai._llm_utils")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
llm_complete = _llm_utils_mod.llm_complete
parse_json = _llm_utils_mod.parse_json
resolve_llm_config = _llm_utils_mod.resolve_llm_config

_JOBS = '"20_ai"."45_fct_job_queue"'
_TESTS = '"05_grc_library"."14_fct_control_tests"'
_TEST_PROPS = '"05_grc_library"."24_dtl_test_properties"'
_PROMOTED = '"15_sandbox"."35_fct_promoted_tests"'


@instrument_class_methods(
    namespace="ai.test_linker.service",
    logger_name="backend.ai.test_linker.instrumentation",
)
class TestLinkerService:
    def __init__(self, *, settings, database_pool) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._repo = TestLinkerRepository()
        self._logger = get_logger("backend.ai.test_linker")
        self._llm_runtime_cache: tuple[str | None, str | None, str] | None = None

    async def _load_test_info(self, conn, *, test_id: str, tenant_key: str) -> dict:
        """Load test info from control_tests table or promoted_tests table."""
        row = await conn.fetchrow(
            f"""
            SELECT
                t.id::text,
                t.test_code,
                t.test_type_code,
                t.integration_type,
                t.scope_org_id::text AS scope_org_id,
                t.scope_workspace_id::text AS scope_workspace_id,
                (SELECT property_value FROM {_TEST_PROPS} WHERE test_id = t.id AND property_key = 'name') AS name,
                (SELECT property_value FROM {_TEST_PROPS} WHERE test_id = t.id AND property_key = 'description') AS description,
                (SELECT property_value FROM {_TEST_PROPS} WHERE test_id = t.id AND property_key = 'signal_type') AS signal_type,
                (SELECT LEFT(property_value, 500) FROM {_TEST_PROPS} WHERE test_id = t.id AND property_key = 'evaluation_rule') AS evaluation_rule_summary
            FROM {_TESTS} t
            WHERE t.id = $1::uuid
              AND t.tenant_key = $2
              AND t.is_active = TRUE
              AND t.is_deleted = FALSE
            """,
            test_id,
            tenant_key,
        )
        if row:
            return dict(row)

        row = await conn.fetchrow(
            f"""
            SELECT
                id::text,
                test_code,
                test_type_code,
                NULL AS integration_type,
                org_id::text AS scope_org_id,
                workspace_id::text AS scope_workspace_id,
                name,
                description,
                signal_type,
                LEFT(evaluation_rule, 500) AS evaluation_rule_summary
            FROM {_PROMOTED}
            WHERE id = $1::uuid
              AND tenant_key = $2
              AND is_active = TRUE
              AND is_deleted = FALSE
            """,
            test_id,
            tenant_key,
        )
        if row:
            return dict(row)

        raise NotFoundError(f"Control test {test_id} not found")

    async def _resolve_llm_runtime(self) -> tuple[str | None, str | None, str]:
        if self._llm_runtime_cache is not None:
            return self._llm_runtime_cache

        _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")

        config_repo = _config_repo_mod.AgentConfigRepository()
        resolver = _resolver_mod.AgentConfigResolver(
            repository=config_repo,
            database_pool=self._database_pool,
            settings=self._settings,
        )
        llm_config = await resolver.resolve(agent_type_code="test_linker", org_id=None)
        self._llm_runtime_cache = resolve_llm_config(llm_config, self._settings)
        return self._llm_runtime_cache

    async def _complete_json_prompt(self, *, system: str, user: str, max_tokens: int = 4000) -> object:
        provider_url, api_key, model = await self._resolve_llm_runtime()
        raw = await llm_complete(
            provider_url=provider_url,
            api_key=api_key,
            model=model,
            system=system,
            user=user,
            max_tokens=min(max_tokens, self._settings.ai_max_tokens),
            temperature=1.0,
        )
        return parse_json(raw)

    async def _suggest_tests_for_control_candidates(
        self,
        *,
        control: dict,
        tests: list[dict],
        existing_test_ids: set[str],
        max_matches: int = 20,
        chunk_size: int = 40,
    ) -> list[TestSuggestionSchema]:
        candidate_map = {str(test["id"]): test for test in tests}
        merged: dict[str, TestSuggestionSchema] = {}

        for idx in range(0, len(tests), chunk_size):
            batch = tests[idx : idx + chunk_size]
            tests_json = json.dumps(
                [
                    {
                        "test_id": test["id"],
                        "test_code": test["test_code"],
                        "name": test.get("name") or "",
                        "description": (test.get("description") or "")[:240],
                        "test_type_code": test.get("test_type_code") or "",
                        "signal_type": test.get("signal_type") or "",
                        "integration_type": test.get("integration_type") or "",
                        "monitoring_frequency": test.get("monitoring_frequency") or "",
                    }
                    for test in batch
                ],
                separators=(",", ":"),
            )
            already_linked = ""
            if existing_test_ids:
                already_linked = ", ".join(sorted(existing_test_ids))

            parsed = await self._complete_json_prompt(
                system=BULK_SUGGEST_TESTS_SYSTEM,
                user=BULK_SUGGEST_TESTS_USER.format(
                    control_code=control.get("control_code") or "",
                    control_name=control.get("name") or control.get("control_code") or "",
                    control_description=(control.get("description") or "")[:600],
                    framework_code=control.get("framework_code") or "",
                    control_category=control.get("control_category_code") or "",
                    control_type=control.get("control_type") or "",
                    candidate_count=len(batch),
                    already_linked=already_linked or "None",
                    tests_json=tests_json,
                ),
            )

            if not isinstance(parsed, list):
                continue

            for item in parsed:
                if not isinstance(item, dict):
                    continue
                test_id = str(item.get("test_id") or "").strip()
                if not test_id or test_id in existing_test_ids:
                    continue
                candidate = candidate_map.get(test_id)
                if not candidate:
                    continue

                confidence = float(item.get("confidence") or 0)
                if confidence < 0.3:
                    continue

                link_type = str(item.get("link_type") or "related").strip().lower()
                if link_type not in {"covers", "partially_covers", "related"}:
                    link_type = "related"

                suggestion = TestSuggestionSchema(
                    test_id=test_id,
                    test_code=str(candidate.get("test_code") or ""),
                    confidence=min(max(confidence, 0.0), 1.0),
                    link_type=link_type,
                    rationale=str(item.get("rationale") or "")[:500],
                )
                current = merged.get(test_id)
                if current is None or suggestion.confidence > current.confidence:
                    merged[test_id] = suggestion

        return sorted(merged.values(), key=lambda item: item.confidence, reverse=True)[:max_matches]

    async def suggest_controls_for_test(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: SuggestControlsRequest,
    ) -> list[dict]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            test = await self._load_test_info(conn, test_id=request.test_id, tenant_key=tenant_key)
            controls = await self._repo.list_all_controls(
                conn,
                tenant_key=tenant_key,
                framework_id=request.framework_id,
                deployed_org_id=request.org_id or test.get("scope_org_id"),
                deployed_workspace_id=request.workspace_id or test.get("scope_workspace_id"),
            )
            if not controls:
                return []
            existing = await self._repo.get_existing_mappings(conn, test_id=request.test_id)

        controls_text = "\n".join(
            f"- ID: {c['id']} | Code: {c['control_code']} | Framework: {c.get('framework_code', '')} | "
            f"Name: {c.get('name', 'N/A')} | Category: {c.get('control_category_code', '')} | "
            f"Type: {c.get('control_type', '')} | Description: {(c.get('description', '') or '')[:200]}"
            for c in controls
        )

        parsed = await self._complete_json_prompt(
            system=SUGGEST_CONTROLS_FOR_TEST_PROMPT.format(
                test_name=test.get("name") or test["test_code"],
                test_description=test.get("description") or "N/A",
                test_type=test.get("test_type_code") or "automated",
                signal_type=test.get("signal_type") or "N/A",
                evaluation_rule_summary=test.get("evaluation_rule_summary") or "N/A",
                controls_list=controls_text,
            ),
            user="Suggest control mappings for this test now.",
        )

        if not isinstance(parsed, list):
            return []
        return [item for item in parsed if isinstance(item, dict) and item.get("control_id") not in existing]

    async def suggest_tests_for_control(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: SuggestTestsRequest,
    ) -> list[dict]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            control = await self._repo.get_control_detail(
                conn,
                control_id=request.control_id,
                tenant_key=tenant_key,
            )
            if not control:
                raise NotFoundError(f"Control {request.control_id} not found")

            tests = await self._repo.list_tests(
                conn,
                tenant_key=tenant_key,
                scope_org_id=request.org_id,
                scope_workspace_id=request.workspace_id,
            )
            if not tests:
                return []

            existing = await self._repo.get_existing_mappings_for_control(
                conn,
                control_id=request.control_id,
            )

        suggestions = await self._suggest_tests_for_control_candidates(
            control=control,
            tests=tests,
            existing_test_ids=existing,
        )
        return [item.model_dump() for item in suggestions]

    async def apply_suggestions(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: ApplySuggestionsForTestRequest,
    ) -> ApplyResult:
        created = 0
        skipped = 0
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            for suggestion in request.suggestions:
                mapping_id = await self._repo.create_mapping_if_not_exists(
                    conn,
                    test_id=request.test_id,
                    control_id=suggestion.control_id,
                    link_type=suggestion.link_type,
                    ai_confidence=suggestion.confidence,
                    ai_rationale=suggestion.rationale,
                    created_by=user_id,
                )
                if mapping_id:
                    created += 1
                else:
                    skipped += 1
        return ApplyResult(created=created, skipped=skipped)

    async def apply_suggestions_for_control(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: ApplySuggestionsForControlRequest,
    ) -> ApplyResult:
        created = 0
        skipped = 0
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            for suggestion in request.suggestions:
                mapping_id = await self._repo.create_mapping_if_not_exists(
                    conn,
                    test_id=suggestion.test_id,
                    control_id=request.control_id,
                    link_type=suggestion.link_type,
                    ai_confidence=suggestion.confidence,
                    ai_rationale=suggestion.rationale,
                    created_by=user_id,
                )
                if mapping_id:
                    created += 1
                else:
                    skipped += 1
        return ApplyResult(created=created, skipped=skipped)

    async def approve_mapping(self, *, user_id: str, tenant_key: str, mapping_id: str) -> None:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            await self._repo.approve_mapping(conn, mapping_id=mapping_id)

    async def reject_mapping(self, *, user_id: str, tenant_key: str, mapping_id: str) -> None:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            await self._repo.reject_mapping(conn, mapping_id=mapping_id)

    async def bulk_approve_mappings(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: BulkDecisionRequest,
    ) -> BulkDecisionResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            updated = await self._repo.bulk_set_approval_status(
                conn,
                mapping_ids=request.mapping_ids,
                status="approved",
            )
        return BulkDecisionResponse(updated=updated)

    async def bulk_reject_mappings(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: BulkDecisionRequest,
    ) -> BulkDecisionResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            updated = await self._repo.bulk_set_approval_status(
                conn,
                mapping_ids=request.mapping_ids,
                status="rejected",
            )
        return BulkDecisionResponse(updated=updated)

    async def list_pending(
        self,
        *,
        user_id: str,
        tenant_key: str,
        query: ListPendingMappingsQuery,
    ) -> PendingTestControlMappingListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            items, total = await self._repo.list_pending_mappings(
                conn,
                tenant_key=tenant_key,
                org_id=query.org_id,
                workspace_id=query.workspace_id,
                framework_id=query.framework_id,
                test_ids=query.test_ids,
                control_ids=query.control_ids,
                created_after=query.created_after,
                created_by=user_id if query.mine_only else None,
                limit=query.limit,
                offset=query.offset,
            )
        return PendingTestControlMappingListResponse(
            items=[PendingTestControlMappingSchema(**item) for item in items],
            total=total,
        )

    async def enqueue_bulk_link(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: BulkLinkRequest,
    ) -> BulkLinkJobResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            controls = await self._repo.list_all_controls(
                conn,
                tenant_key=tenant_key,
                framework_id=request.framework_id,
                deployed_org_id=request.org_id,
                deployed_workspace_id=request.workspace_id,
                control_ids=request.control_ids,
                limit=1000,
            )
            tests = await self._repo.list_tests(
                conn,
                tenant_key=tenant_key,
                scope_org_id=request.org_id,
                scope_workspace_id=request.workspace_id,
                test_ids=request.test_ids,
                limit=1000,
            )

        if not controls:
            raise ValidationError("No eligible controls found for the selected scope.")
        if not tests:
            raise ValidationError("No eligible control tests found for the selected scope.")

        job_id = await self._enqueue_job(
            job_type="test_linker_bulk_link",
            agent_type_code="test_linker",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code=request.priority_code,
            scope_org_id=request.org_id,
            scope_workspace_id=request.workspace_id,
            input_json={
                "org_id": request.org_id,
                "workspace_id": request.workspace_id,
                "framework_id": request.framework_id,
                "control_ids": request.control_ids,
                "test_ids": request.test_ids,
                "tenant_key": tenant_key,
                "user_id": user_id,
                "dry_run": request.dry_run,
            },
        )
        return BulkLinkJobResponse(
            job_id=job_id,
            status="queued",
            framework_id=request.framework_id,
            control_count=len(controls),
            test_count=len(tests),
            dry_run=request.dry_run,
        )

    async def get_job_status(self, *, job_id: str, tenant_key: str) -> JobStatusResponse:
        async with self._database_pool.acquire() as conn:
            row = await self._repo.get_job_status(conn, job_id, tenant_key)
        if not row:
            raise NotFoundError(f"Job '{job_id}' not found")
        return JobStatusResponse(**row)

    async def _enqueue_job(
        self,
        *,
        job_type: str,
        agent_type_code: str,
        user_id: str,
        tenant_key: str,
        priority_code: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
        input_json: dict,
    ) -> str:
        job_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {_JOBS} (
                    id, tenant_key, user_id, org_id, workspace_id,
                    agent_type_code, priority_code, status_code, job_type,
                    input_json, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid,
                    $6, $7, 'queued', $8, $9::jsonb, NOW(), NOW()
                )
                """,
                job_id,
                tenant_key,
                user_id,
                scope_org_id,
                scope_workspace_id,
                agent_type_code,
                priority_code,
                job_type,
                json.dumps(input_json),
            )
        return job_id
