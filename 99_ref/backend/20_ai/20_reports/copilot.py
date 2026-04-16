"""
Copilot Mixin for Report Service.
Contains AI streaming capabilities (enhance section, suggest assessment).
"""

from __future__ import annotations

import asyncio
import json
import uuid
from importlib import import_module
from typing import AsyncIterator, TYPE_CHECKING

if TYPE_CHECKING:
    from .schemas import EnhanceSectionRequest, SuggestAssessmentRequest

_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_streaming_module = import_module("backend.20_ai.02_conversations.streaming")
_factory_mod = import_module("backend.20_ai.14_llm_providers.factory")
_resolver_module = import_module("backend.20_ai.12_agent_config.resolver")
_agent_config_repo_module = import_module("backend.20_ai.12_agent_config.repository")
_cache_mod = import_module("backend.01_core.cache")
_dispatcher_mod = import_module("backend.20_ai.05_mcp.dispatcher")

require_permission = _perm_check_module.require_permission
sse_event = _streaming_module.sse_event
get_provider = _factory_mod.get_provider
AgentConfigResolver = _resolver_module.AgentConfigResolver
AgentConfigRepository = _agent_config_repo_module.AgentConfigRepository
NullCacheManager = _cache_mod.NullCacheManager
MCPToolDispatcher = _dispatcher_mod.MCPToolDispatcher
ToolContext = _dispatcher_mod.ToolContext

_STREAMING_PROVIDERS = frozenset({"openai", "openai_compatible", "anthropic", "azure_openai"})

_ENHANCE_SECTION_SYSTEM = """\
You are a senior GRC analyst and compliance report writer.
You are improving a specific section of an existing AI-generated {report_type} report.

The original report was generated using live data from the organisation's GRC platform.
The same data context is provided below — use it to write with specificity.

ORIGINAL CONTEXT DATA (live GRC data used to generate this report):
{context_data}

CURRENT SECTION TEXT:
{current_section}

USER INSTRUCTION:
{instruction}

Guidelines:
- Keep the same markdown heading level and section structure
- Cite specific numbers, control names, or risk names from the context data
- Do NOT invent metrics not present in the context
- Write for a compliance manager or external auditor audience
- Respond with only the improved section markdown — no preamble, no explanation
"""

_SUGGEST_ASSESSMENT_SYSTEM = """\
You are a senior GRC auditor reviewing an AI-generated compliance report.
Your job is to produce a structured assessment suggestion that a human reviewer can accept, edit, or reject.

REPORT TYPE: {report_type}
REPORT TITLE: {title}

REPORT CONTENT:
{content}

Analyse the report thoroughly and respond with a JSON object in this exact shape:
{{
  "verdict": "satisfactory" | "needs_revision" | "rejected",
  "verdict_rationale": "<1-2 sentence explanation>",
  "findings": [
    {{
      "severity": "critical" | "high" | "medium" | "low" | "informational",
      "section": "<section heading or empty string for whole-report finding>",
      "title": "<concise finding title>",
      "description": "<what the issue is, with evidence from the report>",
      "recommendation": "<what should be done to address it>"
    }}
  ]
}}

Rules:
- Produce 2–6 findings (zero is only acceptable if the report is genuinely perfect)
- Base every finding on content actually present in the report — never invent issues
- Severity guide: critical = regulatory breach risk, high = significant gap, medium = notable improvement needed, low = minor, informational = observation
- Verdict "rejected" only if the report contains material factual errors or is unusable
- Respond ONLY with the JSON — no markdown fences, no preamble
"""


class ReportCopilotMixin:
    """
    Mixin for AI operations on reports.
    Expects self._pool, self._settings, self._logger, and self._repo to be present.
    """

    async def stream_enhance_section(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
        request: "EnhanceSectionRequest",
    ) -> AsyncIterator[str]:
        """
        Stream an AI-improved version of a single report section.

        Reuses the same GRC context that was used to generate the original report,
        ensuring the enhancement agent has full data fidelity.

        SSE events: content_delta, enhance_complete, enhance_error
        """
        enhance_id = str(uuid.uuid4())

        # 1. Permission check — release connection before streaming
        try:
            async with self._pool.acquire() as conn:
                await require_permission(conn, user_id, "ai_copilot.execute")
        except Exception as exc:
            self._logger.error("report.enhance_section perm check failed %s: %s", enhance_id, exc)
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "PERMISSION_CHECK_FAILED",
                "message": "Could not verify permissions. Please try again.",
            })
            return

        # 2. Fetch report record to get original parameters and type
        try:
            async with self._pool.acquire() as conn:
                report = await self._repo.get_report(conn, report_id, tenant_key)
        except Exception as exc:
            self._logger.error("report.enhance_section fetch failed %s: %s", enhance_id, exc)
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "NOT_FOUND",
                "message": "Report not found.",
            })
            return

        if not report:
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "NOT_FOUND",
                "message": "Report not found.",
            })
            return

        if report.status_code != "completed":
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "NOT_READY",
                "message": "Report is not yet completed.",
            })
            return

        # 3. Resolve LLM config
        try:
            _repo = AgentConfigRepository()
            _resolver = AgentConfigResolver(
                repository=_repo,
                database_pool=self._pool,
                settings=self._settings,
            )
            config = await _resolver.resolve(
                agent_type_code="text_enhancer",
                org_id=request.org_id,
            )
        except Exception as exc:
            self._logger.error("report.enhance_section config resolve failed %s: %s", enhance_id, exc)
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "CONFIG_ERROR",
                "message": "AI configuration error. Please contact your administrator.",
            })
            return

        # 4. Re-collect original context data using same parameters
        from .agent import _build_collection_plan  # noqa: PLC0415
        try:
            # Build tool context from report's original scope
            orig_params = {
                "org_id": report.org_id,
                "workspace_id": report.workspace_id,
                **(report.parameters_json or {}),
            }
            plan = _build_collection_plan(report.report_type, orig_params)

            # Import services lazily (same pattern as agent._build_tool_context)
            _fw_svc_mod = import_module("backend.05_grc_library.02_frameworks.service")
            _req_svc_mod = import_module("backend.05_grc_library.04_requirements.service")
            _ctrl_svc_mod = import_module("backend.05_grc_library.05_controls.service")
            _risk_svc_mod = import_module("backend.06_risk_registry.02_risks.service")
            _task_svc_mod = import_module("backend.07_tasks.02_tasks.service")
            _null_cache = NullCacheManager()

            fw_svc = _fw_svc_mod.FrameworkService(settings=self._settings, database_pool=self._pool, cache=_null_cache)
            req_svc = _req_svc_mod.RequirementService(settings=self._settings, database_pool=self._pool, cache=_null_cache)
            ctrl_svc = _ctrl_svc_mod.ControlService(settings=self._settings, database_pool=self._pool, cache=_null_cache)
            risk_svc = _risk_svc_mod.RiskService(settings=self._settings, database_pool=self._pool, cache=_null_cache)
            task_svc = _task_svc_mod.TaskService(settings=self._settings, database_pool=self._pool, cache=_null_cache)

            ctx = ToolContext(
                pool=self._pool,
                user_id=user_id,
                tenant_key=tenant_key,
                org_id=report.org_id,
                workspace_id=report.workspace_id,
                framework_service=fw_svc,
                requirement_service=req_svc,
                control_service=ctrl_svc,
                risk_service=risk_svc,
                task_service=task_svc,
            )

            dispatcher = MCPToolDispatcher()
            collected: dict = {}
            for call in plan[:20]:
                try:
                    result = await dispatcher.dispatch(call["tool"], call.get("args", {}), ctx)
                    key = f"{call['tool']}__{json.dumps(call.get('args', {}), sort_keys=True, default=str)[:40]}"
                    collected[key] = result.output
                except Exception as tool_exc:
                    self._logger.warning("report.enhance_section tool %s: %s", call["tool"], tool_exc)

            context_data = json.dumps(collected, indent=2, default=str)[:6000]
        except Exception as exc:
            self._logger.warning("report.enhance_section context collection failed %s: %s", enhance_id, exc)
            # Fallback: use empty context — still useful with existing section text
            context_data = "(context unavailable)"

        # 5. Build prompt and stream LLM response
        system_prompt = _ENHANCE_SECTION_SYSTEM.format(
            report_type=report.report_type.replace("_", " ").title(),
            context_data=context_data,
            current_section=request.current_section_markdown[:3000],
            instruction=request.instruction,
        )
        if request.section_title:
            user_msg = f"Improve the \"{request.section_title}\" section per the instruction above."
        else:
            user_msg = "Apply the instruction to the full report content above."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
        ]

        try:
            provider = get_provider(
                provider_type=config.provider_type,
                provider_base_url=config.provider_base_url,
                api_key=config.api_key,
                model_id=config.model_id,
            )
        except Exception as exc:
            self._logger.error("report.enhance_section provider init failed %s: %s", enhance_id, exc)
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "PROVIDER_ERROR",
                "message": "AI provider configuration error.",
            })
            return

        use_streaming = config.provider_type in _STREAMING_PROVIDERS and hasattr(provider, "stream_chat_completion")
        enhanced_text = ""
        input_tokens = 0
        output_tokens = 0

        if use_streaming:
            try:
                stream = provider.stream_chat_completion(
                    messages=messages,
                    temperature=1.0,
                    max_tokens=1500,
                )
                async for chunk in stream:
                    if chunk.delta:
                        enhanced_text += chunk.delta
                        yield await sse_event("content_delta", {"delta": chunk.delta})
                    if chunk.is_final:
                        input_tokens = chunk.input_tokens
                        output_tokens = chunk.output_tokens
                    await asyncio.sleep(0)
            except Exception as exc:
                self._logger.error("report.enhance_section streaming failed %s: %s", enhance_id, exc)
                yield await sse_event("enhance_error", {
                    "enhance_id": enhance_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error. Please try again.",
                })
                return
        else:
            try:
                response = await provider.chat_completion(
                    messages=messages,
                    tools=None,
                    temperature=1.0,
                    max_tokens=1500,
                )
                enhanced_text = (response.content or "").strip()
                input_tokens = response.input_tokens
                output_tokens = response.output_tokens
                if enhanced_text:
                    yield await sse_event("content_delta", {"delta": enhanced_text})
                    await asyncio.sleep(0)
            except Exception as exc:
                self._logger.error("report.enhance_section llm failed %s: %s", enhance_id, exc)
                yield await sse_event("enhance_error", {
                    "enhance_id": enhance_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error. Please try again.",
                })
                return

        enhanced_text = enhanced_text.strip()
        if not enhanced_text:
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "EMPTY_RESPONSE",
                "message": "The AI returned an empty response. Please try again.",
            })
            return

        yield await sse_event("enhance_complete", {
            "enhance_id": enhance_id,
            "section_title": request.section_title,
            "enhanced_section": enhanced_text,
            "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
        })

        self._logger.info(
            "report.enhance_section completed enhance_id=%s report=%s section=%s",
            enhance_id, report_id, request.section_title,
        )

    async def stream_suggest_assessment(
        self,
        *,
        user_id: str,
        tenant_key: str,
        report_id: str,
        request: "SuggestAssessmentRequest",
    ) -> AsyncIterator[bytes]:
        """
        Stream an AI-generated assessment suggestion for a completed report.

        SSE events:
          - content_delta:        {"delta": "<partial JSON token>"}
          - suggestion_complete:  {"verdict": "...", "verdict_rationale": "...", "findings": [...]}
          - suggestion_error:     {"error_code": "...", "message": "..."}
        """
        suggest_id = str(uuid.uuid4())

        await require_permission(
            pool=self._pool,
            user_id=user_id,
            tenant_key=tenant_key,
            org_id=request.org_id,
            workspace_id=request.workspace_id,
            permission_code="ai_copilot.execute",
        )

        # 1. Fetch report
        async with self._pool.acquire() as conn:
            report = await self._repo.get_report(conn, report_id, tenant_key)
        if not report:
            yield await sse_event("suggestion_error", {
                "suggest_id": suggest_id,
                "error_code": "NOT_FOUND",
                "message": "Report not found.",
            })
            return

        if report.status_code != "completed" or not report.content_markdown:
            yield await sse_event("suggestion_error", {
                "suggest_id": suggest_id,
                "error_code": "NOT_READY",
                "message": "Report is not yet completed.",
            })
            return

        # 2. Resolve LLM config
        try:
            _repo = AgentConfigRepository()
            _resolver = AgentConfigResolver(
                repository=_repo,
                database_pool=self._pool,
                settings=self._settings,
            )
            config = await _resolver.resolve(
                agent_type_code="text_enhancer",
                org_id=request.org_id,
            )
        except Exception as exc:
            self._logger.error("report.suggest_assessment config resolve failed %s: %s", suggest_id, exc)
            yield await sse_event("suggestion_error", {
                "suggest_id": suggest_id,
                "error_code": "CONFIG_ERROR",
                "message": "AI configuration error.",
            })
            return

        # 3. Build prompt — truncate content to avoid exceeding context window
        content_snippet = report.content_markdown[:8000]
        system_prompt = _SUGGEST_ASSESSMENT_SYSTEM.format(
            report_type=report.report_type.replace("_", " ").title(),
            title=report.title or report.report_type.replace("_", " ").title(),
            content=content_snippet,
        )
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Please analyse this report and provide your assessment suggestion as JSON."},
        ]

        # 4. Stream LLM response
        try:
            provider = get_provider(
                provider_type=config.provider_type,
                provider_base_url=config.provider_base_url,
                api_key=config.api_key,
                model_id=config.model_id,
            )
        except Exception as exc:
            self._logger.error("report.suggest_assessment provider init failed %s: %s", suggest_id, exc)
            yield await sse_event("suggestion_error", {
                "suggest_id": suggest_id,
                "error_code": "PROVIDER_ERROR",
                "message": "AI provider configuration error.",
            })
            return

        use_streaming = config.provider_type in _STREAMING_PROVIDERS and hasattr(provider, "stream_chat_completion")
        raw_text = ""

        if use_streaming:
            try:
                stream = provider.stream_chat_completion(
                    messages=messages,
                    temperature=1.0,
                    max_tokens=2000,
                )
                async for chunk in stream:
                    if chunk.delta:
                        raw_text += chunk.delta
                        yield await sse_event("content_delta", {"delta": chunk.delta})
                    await asyncio.sleep(0)
            except Exception as exc:
                self._logger.error("report.suggest_assessment streaming failed %s: %s", suggest_id, exc)
                yield await sse_event("suggestion_error", {
                    "suggest_id": suggest_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error.",
                })
                return
        else:
            try:
                response = await provider.chat_completion(
                    messages=messages,
                    tools=None,
                    temperature=1.0,
                    max_tokens=2000,
                )
                raw_text = (response.content or "").strip()
                if raw_text:
                    yield await sse_event("content_delta", {"delta": raw_text})
                    await asyncio.sleep(0)
            except Exception as exc:
                self._logger.error("report.suggest_assessment llm failed %s: %s", suggest_id, exc)
                yield await sse_event("suggestion_error", {
                    "suggest_id": suggest_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error.",
                })
                return

        raw_text = raw_text.strip()
        if not raw_text:
            yield await sse_event("suggestion_error", {
                "suggest_id": suggest_id,
                "error_code": "EMPTY_RESPONSE",
                "message": "The AI returned an empty response.",
            })
            return

        # 5. Parse JSON and emit final event
        try:
            # Strip any accidental markdown fences
            clean = raw_text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(clean)
        except json.JSONDecodeError:
            self._logger.warning("report.suggest_assessment JSON parse failed %s: %r", suggest_id, raw_text[:200])
            yield await sse_event("suggestion_error", {
                "suggest_id": suggest_id,
                "error_code": "PARSE_ERROR",
                "message": "AI response was not valid JSON. Please try again.",
            })
            return

        yield await sse_event("suggestion_complete", {
            "suggest_id": suggest_id,
            "verdict": parsed.get("verdict", "satisfactory"),
            "verdict_rationale": parsed.get("verdict_rationale", ""),
            "findings": parsed.get("findings", []),
        })
        self._logger.info("report.suggest_assessment completed suggest_id=%s report=%s", suggest_id, report_id)
