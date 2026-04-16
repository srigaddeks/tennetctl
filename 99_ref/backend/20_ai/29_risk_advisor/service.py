from __future__ import annotations

import asyncio
import json
import uuid
from importlib import import_module

from .models import ControlCandidate, ControlSuggestion
from .repository import RiskAdvisorRepository
from .schemas import (
    BulkLinkJobResponse,
    BulkLinkRequest,
    ControlSuggestionSchema,
    JobStatusResponse,
    SuggestControlsRequest,
    SuggestControlsResponse,
)

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
require_permission = _perm_check_module.require_permission

_JOBS = '"20_ai"."45_fct_job_queue"'


@instrument_class_methods(
    namespace="ai.risk_advisor.service",
    logger_name="backend.ai.risk_advisor.instrumentation",
)
class RiskAdvisorService:
    def __init__(self, *, settings, database_pool: DatabasePool) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._repository = RiskAdvisorRepository()
        self._logger = get_logger("backend.ai.risk_advisor")

    # ── Suggest controls ───────────────────────────────────────────────────────

    async def suggest_controls(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: SuggestControlsRequest,
    ) -> SuggestControlsResponse:
        async with self._database_pool.acquire() as conn:
            risk = await self._repository.fetch_risk_detail(conn, request.risk_id)
            if not risk:
                raise NotFoundError(f"Risk '{request.risk_id}' not found")
            await require_permission(
                conn,
                user_id,
                "risks.view",
                scope_org_id=risk["org_id"],
                scope_workspace_id=risk["workspace_id"],
            )
            already_linked = await self._repository.fetch_already_linked_control_ids(
                conn, request.risk_id
            )
            candidates = await self._repository.fetch_candidate_controls(
                conn,
                tenant_key=tenant_key,
                org_id=request.org_id,
                framework_ids=request.framework_ids,
                limit=50,
            )

        try:
            provider, _ = await self._get_provider()
            suggestions = await self._call_llm_suggest(
                risk=risk,
                candidates=candidates,
                already_linked_ids=set(already_linked),
                top_n=request.top_n,
                provider=provider,
            )
            suggestion_error = None
        except Exception as exc:  # noqa: BLE001
            self._logger.warning("LLM suggest failed: %s", exc)
            suggestions = []
            suggestion_error = str(exc)

        return SuggestControlsResponse(
            risk_id=request.risk_id,
            risk_code=risk["risk_code"],
            risk_title=risk.get("title"),
            suggestions=[
                ControlSuggestionSchema(
                    control_id=s.control_id,
                    control_code=s.control_code,
                    control_name=s.control_name,
                    control_category_code=s.control_category_code,
                    criticality_code=s.criticality_code,
                    framework_id=s.framework_id,
                    framework_code=s.framework_code,
                    framework_name=s.framework_name,
                    suggested_link_type=s.suggested_link_type,
                    relevance_score=s.relevance_score,
                    rationale=s.rationale,
                    already_linked=s.already_linked,
                )
                for s in suggestions
            ],
            total_candidates_evaluated=len(candidates),
            suggestion_error=suggestion_error,
        )

    async def _call_llm_suggest(
        self,
        *,
        risk: dict,
        candidates: list[ControlCandidate],
        already_linked_ids: set[str],
        top_n: int,
        provider,
    ) -> list[ControlSuggestion]:
        from .prompts import SUGGEST_CONTROLS_SYSTEM, SUGGEST_CONTROLS_USER

        # Build candidate JSON (compact, under token limit)
        candidates_data = [
            {
                "control_id": c.control_id,
                "control_code": c.control_code,
                "control_name": c.control_name or "",
                "description": (c.description or "")[:300],
                "category": c.control_category_code or "",
                "tags": c.tags or "",
                "framework": c.framework_name or c.framework_code,
                "criticality": c.criticality_code or "",
            }
            for c in candidates[:200]
        ]

        already_section = ""
        if already_linked_ids:
            already_section = (
                f"ALREADY LINKED CONTROLS (do not suggest these):\n"
                + ", ".join(sorted(already_linked_ids))
            )

        system = SUGGEST_CONTROLS_SYSTEM.format(top_n=top_n)
        user = SUGGEST_CONTROLS_USER.format(
            risk_code=risk.get("risk_code", ""),
            risk_category_code=risk.get("risk_category_code", ""),
            risk_level_code=risk.get("risk_level_code", ""),
            title=risk.get("title") or "",
            description=(risk.get("description") or "")[:800],
            business_impact=(risk.get("business_impact") or "")[:400],
            already_linked_section=already_section,
            candidate_count=len(candidates_data),
            controls_json=json.dumps(candidates_data, indent=None),
            top_n=top_n,
        )

        raw = await self._llm_call(provider, system, user)
        parsed = _parse_json_array(raw)
        if not isinstance(parsed, list):
            return []

        # Build a lookup map for enrichment
        candidate_map = {c.control_id: c for c in candidates}

        results: list[ControlSuggestion] = []
        for item in parsed:
            cid = str(item.get("control_id", ""))
            if not cid or cid in already_linked_ids:
                continue
            c = candidate_map.get(cid)
            if not c:
                continue
            link_type = item.get("suggested_link_type", "related")
            if link_type not in {"mitigating", "compensating", "related"}:
                link_type = "related"
            score = int(item.get("relevance_score", 0))
            if score < 40:
                continue
            results.append(
                ControlSuggestion(
                    control_id=c.control_id,
                    control_code=c.control_code,
                    control_name=c.control_name,
                    control_category_code=c.control_category_code,
                    criticality_code=c.criticality_code,
                    framework_id=c.framework_id,
                    framework_code=c.framework_code,
                    framework_name=c.framework_name,
                    suggested_link_type=link_type,
                    relevance_score=min(100, max(0, score)),
                    rationale=str(item.get("rationale", ""))[:500],
                    already_linked=False,
                )
            )

        return sorted(results, key=lambda s: s.relevance_score, reverse=True)[:top_n]

    # ── Bulk link ──────────────────────────────────────────────────────────────

    async def enqueue_bulk_link(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: BulkLinkRequest,
    ) -> BulkLinkJobResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "risks.update",
                scope_org_id=request.org_id,
            )
            # Verify framework exists only if one was specified
            if request.framework_id:
                fw_row = await conn.fetchrow(
                    'SELECT framework_code FROM "05_grc_library"."10_fct_frameworks" '
                    "WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE",
                    request.framework_id,
                    tenant_key,
                )
                if not fw_row:
                    raise NotFoundError(f"Framework '{request.framework_id}' not found")

        job_id = await self._enqueue_job(
            job_type="risk_advisor_bulk_link",
            agent_type_code="risk_agent",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code=request.priority_code,
            scope_org_id=request.org_id,
            scope_workspace_id=request.workspace_id,
            input_json={
                "framework_id": request.framework_id,
                "risk_id": request.risk_id,
                "org_id": request.org_id,
                "workspace_id": request.workspace_id,
                "tenant_key": tenant_key,
                "user_id": user_id,
                "dry_run": request.dry_run,
            },
        )
        return BulkLinkJobResponse(
            job_id=job_id,
            status="queued",
            framework_id=request.framework_id,
            dry_run=request.dry_run,
        )

    async def delete_all_bulk_link_jobs(self, *, tenant_key: str) -> int:
        async with self._database_pool.acquire() as conn:
            return await self._repository.delete_all_bulk_link_jobs(conn, tenant_key)

    async def get_job_status(
        self, *, job_id: str, tenant_key: str
    ) -> JobStatusResponse:
        async with self._database_pool.acquire() as conn:
            row = await self._repository.get_job_status(conn, job_id, tenant_key)
        if not row:
            raise NotFoundError(f"Job '{job_id}' not found")
        return JobStatusResponse(
            job_id=row["job_id"],
            status_code=row["status_code"],
            job_type=row["job_type"],
            progress_pct=row.get("progress_pct"),
            output_json=json.loads(row["output_json"]) if isinstance(row.get("output_json"), str) else row.get("output_json"),
            error_message=row.get("error_message"),
            created_at=str(row["created_at"]),
            updated_at=str(row["updated_at"]),
        )

    # ── Shared helpers ─────────────────────────────────────────────────────────

    async def _get_provider(self):
        _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
        _factory_mod = import_module("backend.20_ai.14_llm_providers.factory")

        resolver = _resolver_mod.AgentConfigResolver(
            repository=_config_repo_mod.AgentConfigRepository(),
            database_pool=self._database_pool,
            settings=self._settings,
        )
        config = await resolver.resolve(agent_type_code="risk_agent", org_id=None)
        provider = _factory_mod.get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=config.api_key,
            model_id=config.model_id,
            temperature=1.0,
        )
        return provider, config

    async def _llm_call(self, provider, system: str, user: str, max_retries: int = 3) -> str:
        last_exc: Exception | None = None
        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    provider.chat_completion(
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": user},
                        ],
                        max_tokens=4096,
                    ),
                    timeout=90,
                )
                return response.content or ""
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                self._logger.warning(
                    "risk_advisor._llm_call attempt %d/%d failed: %s: %s",
                    attempt + 1, max_retries, type(exc).__name__, exc,
                )
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        raise RuntimeError(
            f"LLM call failed after {max_retries} attempts: {type(last_exc).__name__}: {last_exc}"
        ) from last_exc

    async def _enqueue_job(
        self,
        *,
        job_type: str,
        agent_type_code: str,
        user_id: str,
        tenant_key: str,
        priority_code: str,
        input_json: dict,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {_JOBS} (
                    id, tenant_key, user_id, org_id, workspace_id, agent_type_code, priority_code,
                    status_code, job_type, input_json,
                    scheduled_at, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid, $6, $7,
                    'queued', $8, $9::jsonb,
                    NOW(), NOW(), NOW()
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


def _parse_json_array(raw: str) -> list:
    """Parse a JSON array from LLM output, stripping markdown fences."""
    text = raw.strip()
    # Strip ```json ... ``` fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
    try:
        result = json.loads(text)
        return result if isinstance(result, list) else []
    except json.JSONDecodeError:
        return []
