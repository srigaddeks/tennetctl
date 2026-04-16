"""
FormFillService — single LLM call that returns a structured JSON object whose
keys match the form fields for a given entity type, streamed as SSE.

SSE event types:
  content_delta      — partial JSON text (for live preview, optional)
  fill_complete      — {"fill_id": "...", "fields": {...}, "usage": {...}}
  fill_error         — {"fill_id": "...", "error_code": "...", "message": "..."}

The LLM is instructed to return ONLY a valid JSON object — no markdown, no prose.
After the full text is collected the service JSON-parses it, validates the keys,
and emits fill_complete with the clean dict.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from importlib import import_module
from typing import AsyncIterator

_logging_module = import_module("backend.01_core.logging_utils")
_audit_module = import_module("backend.01_core.audit")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_resolver_module = import_module("backend.20_ai.12_agent_config.resolver")
_agent_config_repo_module = import_module("backend.20_ai.12_agent_config.repository")
_factory_module = import_module("backend.20_ai.14_llm_providers.factory")
_provider_module = import_module("backend.20_ai.14_llm_providers.provider")
_streaming_module = import_module("backend.20_ai.02_conversations.streaming")
_telemetry_module = import_module("backend.01_core.telemetry")

get_logger = _logging_module.get_logger
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AuthorizationError = _errors_module.AuthorizationError
require_permission = _perm_check_module.require_permission
AgentConfigResolver = _resolver_module.AgentConfigResolver
AgentConfigRepository = _agent_config_repo_module.AgentConfigRepository
get_provider = _factory_module.get_provider
sse_event = _streaming_module.sse_event
instrument_class_methods = _telemetry_module.instrument_class_methods

_STREAMING_PROVIDERS = frozenset({"openai", "openai_compatible", "anthropic", "azure_openai"})

# ---------------------------------------------------------------------------
# Field schema per entity type
# ---------------------------------------------------------------------------

_ENTITY_FIELD_SCHEMAS: dict[str, dict] = {
    "framework": {
        "name": "string — concise framework name (e.g. 'HIPAA Security Rule')",
        "description": "string — 1-3 sentence purpose description",
        "framework_type_code": "string — one code from available_types",
        "framework_category_code": "string — one code from available_categories",
    },
    "control": {
        "name": "string — concise control name (e.g. 'Multi-Factor Authentication Enforcement')",
        "description": "string — 1-3 sentence description of what this control does and why",
        "control_category_code": "string — one code from available_categories",
        "criticality_code": "string — one code from available_criticalities (critical/high/medium/low)",
        "control_type": "string — one of: preventive | detective | corrective | compensating",
        "automation_potential": "string — one of: full | partial | manual",
    },
    "risk": {
        "title": "string — concise risk title describing the threat and its target",
        "description": "string — 2-4 sentence scenario description",
        "risk_category_code": "string — one code from available_categories",
        "risk_level_code": "string — one code from available_criticalities (critical/high/medium/low)",
        "treatment_type_code": "string — one code from available_treatment_types",
    },
    "task": {
        "title": "string — action-oriented task title starting with a verb",
        "description": "string — 2-3 sentence task description explaining what needs to be done",
        "task_type_code": "string — one code from available_task_types",
        "priority_code": "string — one of: critical | high | medium | low",
    },
    "assessment": {
        "assessment_type": "string — one of: inherent | residual",
        "likelihood_score": "integer — 1 to 5 (1=Very Low, 2=Low, 3=Medium, 4=High, 5=Very High)",
        "impact_score": "integer — 1 to 5 (1=Very Low, 2=Low, 3=Medium, 4=High, 5=Very High)",
        "assessment_notes": "string — 2-4 sentences explaining the rationale for these scores",
    },
    "treatment_plan": {
        "plan_description": "string — 2-4 sentence description of how this risk will be treated",
        "action_items": "string — bullet-point list of specific actions to implement this plan",
        "plan_status": "string — one of: draft | in_progress | completed | on_hold | cancelled",
        "target_date": "string — ISO date (YYYY-MM-DD) for plan completion, or empty string",
        "review_frequency": "string — one of: monthly | quarterly | semi_annual | annual, or empty string",
    },
}

# ---------------------------------------------------------------------------
# System prompts per entity type
# ---------------------------------------------------------------------------

_SYSTEM_PROMPTS: dict[str, str] = {
    "framework": """\
You are an expert GRC architect helping a compliance team create a new framework record.

The user will describe what they want to create. You must return ONLY a valid JSON object \
(no markdown fences, no prose, no explanation) with exactly these fields:
{field_schema}

Rules:
- name: Use title case, 3-8 words, use the official framework name if recognised (e.g. "HIPAA Security Rule", "ISO 27001:2022", "SOC 2 Type II")
- description: State what the framework is and its primary compliance purpose in 1-3 sentences
- framework_type_code: Choose from: {available_types}
- framework_category_code: Choose from: {available_categories}

Return only the JSON object. No other text.\
""",
    "control": """\
You are an expert GRC practitioner helping a compliance team create a new control record.

The user will describe what they want to create. You must return ONLY a valid JSON object \
(no markdown fences, no prose, no explanation) with exactly these fields:
{field_schema}

Rules:
- name: Use title case, 3-8 words, action-oriented (e.g. "Multi-Factor Authentication Enforcement")
- description: Describe what the control does and why in 1-3 sentences. Use precise security language.
- control_category_code: Choose from: {available_categories}
- criticality_code: Choose from: {available_criticalities}
- control_type: preventive (blocks threats), detective (identifies them), corrective (fixes them), or compensating (alternative mitigations)
- automation_potential: full (fully automated), partial (partially automated), or manual
{context_block}
Return only the JSON object. No other text.\
""",
    "risk": """\
You are an expert GRC risk analyst helping a compliance team register a new risk.

The user will describe what they want to create. You must return ONLY a valid JSON object \
(no markdown fences, no prose, no explanation) with exactly these fields:
{field_schema}

Rules:
- title: Name the threat and its primary target (e.g. "Unauthorized ePHI Access via Compromised Credentials")
- description: Describe the risk scenario: what could happen, how, and the primary consequence. 2-4 sentences.
- risk_category_code: Choose from: {available_categories}
- risk_level_code: Choose from: {available_criticalities}
- treatment_type_code: Choose from: {available_treatment_types}
{context_block}
Return only the JSON object. No other text.\
""",
    "task": """\
You are an expert GRC project manager helping a compliance team create a new task.

The user will describe what they want to create. You must return ONLY a valid JSON object \
(no markdown fences, no prose, no explanation) with exactly these fields:
{field_schema}

Rules:
- title: Start with a verb (Implement, Review, Document, Remediate, Configure, Audit, Rotate, Enable…). 5-12 words.
- description: Explain what needs to be done and why in 2-3 sentences.
- task_type_code: Choose from: {available_task_types}
- priority_code: critical | high | medium | low — based on urgency implied in the description
{context_block}
Return only the JSON object. No other text.\
""",
    "assessment": """\
You are an expert GRC risk analyst helping a compliance team create a risk assessment.

The user will describe the risk scenario and context. You must return ONLY a valid JSON object \
(no markdown fences, no prose, no explanation) with exactly these fields:
{field_schema}

Rules:
- assessment_type: "inherent" for raw risk before controls, "residual" for risk after controls are applied
- likelihood_score: 1 (Very Low) to 5 (Very High) — how likely is this risk to materialise?
- impact_score: 1 (Very Low) to 5 (Very High) — how severe would the impact be if it occurred?
- assessment_notes: Explain the scoring rationale: what factors drive likelihood, what are the primary consequences
{context_block}
Return only the JSON object. No other text.\
""",
    "treatment_plan": """\
You are an expert GRC risk manager helping a compliance team define a risk treatment plan.

The user will describe how they want to treat the risk. You must return ONLY a valid JSON object \
(no markdown fences, no prose, no explanation) with exactly these fields:
{field_schema}

Rules:
- plan_description: Describe the treatment approach clearly (mitigate, transfer, accept, or avoid). 2-4 sentences.
- action_items: List the specific steps needed to implement this plan, one per line starting with "-"
- plan_status: draft (new plan), in_progress (being executed), completed, on_hold, or cancelled
- target_date: Realistic target date in YYYY-MM-DD format based on complexity; or empty string if not determinable
- review_frequency: How often to review progress: monthly, quarterly, semi_annual, or annual; or empty string
{context_block}
Return only the JSON object. No other text.\
""",
}


def _format_options(options: list) -> str:
    if not options:
        return "(none specified — use your best judgement)"
    return " | ".join(f"{o.code} ({o.name})" for o in options)


def _format_field_schema(entity_type: str) -> str:
    schema = _ENTITY_FIELD_SCHEMAS.get(entity_type, {})
    lines = []
    for k, v in schema.items():
        lines.append(f'  "{k}": {v}')
    return "{\n" + ",\n".join(lines) + "\n}"


def _build_context_block(entity_context: dict | None) -> str:
    if not entity_context:
        return ""
    lines = ["\nAdditional context about the parent entity:"]
    for k, v in entity_context.items():
        if v is not None:
            lines.append(f"  {k}: {v}")
    return "\n".join(lines) + "\n"


def _strip_json_fences(text: str) -> str:
    """Remove markdown code fences if the LLM added them despite instructions."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        # Remove opening fence line
        lines = lines[1:] if lines[0].startswith("```") else lines
        # Remove closing fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text


# ---------------------------------------------------------------------------
# Allowed keys per entity type — drop anything the LLM hallucinated
# ---------------------------------------------------------------------------

_ALLOWED_KEYS: dict[str, frozenset] = {
    entity: frozenset(_ENTITY_FIELD_SCHEMAS[entity].keys())
    for entity in _ENTITY_FIELD_SCHEMAS
}


@instrument_class_methods(
    namespace="ai.form_fill.service",
    logger_name="backend.ai.form_fill.instrumentation",
)
class FormFillService:
    """
    Single LLM call to auto-fill a GRC create form from a natural-language intent.
    """

    def __init__(self, *, settings, database_pool) -> None:
        self._settings = settings
        self._pool = database_pool
        self._repository = AgentConfigRepository()
        self._resolver = AgentConfigResolver(
            repository=self._repository,
            database_pool=database_pool,
            settings=settings,
        )
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.form_fill")

    async def stream_fill(
        self,
        request,  # FormFillRequest
        user_id: str,
        tenant_key: str,
    ) -> AsyncIterator[str]:
        fill_id = str(uuid.uuid4())
        entity_type: str = request.entity_type
        self._logger.info(
            "form_fill start fill_id=%s entity_type=%s user=%s",
            fill_id, entity_type, user_id,
        )

        # 1. Permission check
        try:
            async with self._pool.acquire() as conn:
                await require_permission(conn, user_id, "ai_copilot.execute")
        except AuthorizationError:
            yield await sse_event("fill_error", {
                "fill_id": fill_id,
                "error_code": "FORBIDDEN",
                "message": "Permission denied: ai_copilot.execute required",
            })
            return
        except Exception as exc:
            self._logger.error("form_fill permission check failed fill_id=%s: %s", fill_id, exc)
            yield await sse_event("fill_error", {
                "fill_id": fill_id,
                "error_code": "PERMISSION_CHECK_FAILED",
                "message": "Could not verify permissions. Please try again.",
            })
            return

        # 2. Validate entity type
        if entity_type not in _ENTITY_FIELD_SCHEMAS:
            yield await sse_event("fill_error", {
                "fill_id": fill_id,
                "error_code": "UNSUPPORTED_ENTITY",
                "message": f"form_fill does not support entity type: {entity_type}",
            })
            return

        # 3. Resolve LLM config
        try:
            config = await self._resolver.resolve(
                agent_type_code="text_enhancer",  # reuse text_enhancer config
                org_id=request.org_id,
            )
        except Exception as exc:
            self._logger.error("form_fill config resolve failed fill_id=%s: %s", fill_id, exc)
            yield await sse_event("fill_error", {
                "fill_id": fill_id,
                "error_code": "CONFIG_ERROR",
                "message": "AI configuration error. Please contact your administrator.",
            })
            return

        effective_model_id = request.model_id or config.model_id

        # 4. Build prompts
        template = _SYSTEM_PROMPTS.get(entity_type, _SYSTEM_PROMPTS["framework"])
        field_schema = _format_field_schema(entity_type)
        context_block = _build_context_block(request.entity_context)
        system_prompt = template.format(
            field_schema=field_schema,
            available_types=_format_options(request.available_types),
            available_categories=_format_options(request.available_categories),
            available_criticalities=_format_options(request.available_criticalities),
            available_treatment_types=_format_options(request.available_treatment_types),
            available_task_types=_format_options(request.available_task_types),
            context_block=context_block,
        )
        user_message = f"Create a {entity_type}: {request.intent}"
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # 5. LLM call
        try:
            provider = get_provider(
                provider_type=config.provider_type,
                provider_base_url=config.provider_base_url,
                api_key=config.api_key,
                model_id=effective_model_id,
                temperature=1.0,
            )
        except Exception as exc:
            self._logger.error("form_fill provider init failed fill_id=%s: %s", fill_id, exc)
            yield await sse_event("fill_error", {
                "fill_id": fill_id,
                "error_code": "PROVIDER_ERROR",
                "message": "AI provider configuration error. Please contact your administrator.",
            })
            return

        use_streaming = (
            config.provider_type in _STREAMING_PROVIDERS
            and hasattr(provider, "stream_chat_completion")
        )

        full_text = ""
        input_tokens = 0
        output_tokens = 0

        if use_streaming:
            try:
                stream = provider.stream_chat_completion(
                    messages=messages,
                    temperature=1.0,
                    max_tokens=1024,
                )
                async for chunk in stream:
                    if chunk.delta:
                        full_text += chunk.delta
                        yield await sse_event("content_delta", {"delta": chunk.delta})
                    if chunk.is_final:
                        input_tokens = chunk.input_tokens
                        output_tokens = chunk.output_tokens
                    await asyncio.sleep(0)
            except Exception as exc:
                self._logger.error("form_fill streaming failed fill_id=%s: %s", fill_id, exc)
                yield await sse_event("fill_error", {
                    "fill_id": fill_id,
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
                    max_tokens=1024,
                )
            except Exception as exc:
                self._logger.error("form_fill llm call failed fill_id=%s: %s", fill_id, exc)
                yield await sse_event("fill_error", {
                    "fill_id": fill_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error. Please try again.",
                })
                return
            full_text = (response.content or "").strip()
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens

        # 6. Parse JSON
        clean_text = _strip_json_fences(full_text)
        try:
            raw_fields: dict = json.loads(clean_text)
        except json.JSONDecodeError as exc:
            self._logger.error(
                "form_fill json parse failed fill_id=%s text=%r err=%s",
                fill_id, clean_text[:200], exc,
            )
            yield await sse_event("fill_error", {
                "fill_id": fill_id,
                "error_code": "PARSE_ERROR",
                "message": "AI returned an invalid response. Please try again.",
            })
            return

        # Sanitise — keep only recognised fields, ensure string values
        allowed = _ALLOWED_KEYS.get(entity_type, frozenset())
        fields = {
            k: str(v) if not isinstance(v, (list, dict)) else v
            for k, v in raw_fields.items()
            if k in allowed
        }

        # 7. Emit fill_complete
        yield await sse_event("fill_complete", {
            "fill_id": fill_id,
            "entity_type": entity_type,
            "fields": fields,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        })

        self._logger.info(
            "form_fill complete fill_id=%s entity_type=%s fields=%s",
            fill_id, entity_type, list(fields.keys()),
        )

        # 8. Audit (best-effort)
        try:
            async with self._pool.acquire() as conn:
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=fill_id,
                        tenant_key=tenant_key,
                        entity_type=entity_type,
                        entity_id="new",
                        event_type="form_filled",
                        event_category="ai",
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "entity_type": entity_type,
                            "model_id": effective_model_id,
                            "input_tokens": str(input_tokens),
                            "output_tokens": str(output_tokens),
                            "org_id": request.org_id or "",
                            "fields_filled": ",".join(fields.keys()),
                        },
                        occurred_at=__import__("datetime").datetime.utcnow(),
                    ),
                )
        except Exception as audit_exc:
            self._logger.warning("form_fill audit write failed fill_id=%s: %s", fill_id, audit_exc)

    async def stream_agent_fill(
        self,
        *,
        entity_type: str,
        message: str,
        history: list[dict],
        page_context: dict,
        org_id: str | None,
        workspace_id: str | None,
        user_id: str,
        tenant_key: str,
        session_id: str,
    ) -> AsyncIterator[str]:
        """
        Agentic form-fill: runs the GRC agent loop with only read tools +
        grc_propose_form_fields. When the agent calls grc_propose_form_fields,
        emits a form_fill_proposed SSE event and the frontend fills the form.

        Unlike the main copilot, this does NOT persist messages to a DB conversation —
        the session is ephemeral (lives in frontend state only).
        """
        _agent_mod = import_module("backend.20_ai.18_form_fill.agent")
        _dispatcher_mod = import_module("backend.20_ai.05_mcp.dispatcher")
        _ac_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
        _ac_resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")

        _fw_svc_mod = import_module("backend.05_grc_library.02_frameworks.service")
        _req_svc_mod = import_module("backend.05_grc_library.04_requirements.service")
        _ctrl_svc_mod = import_module("backend.05_grc_library.05_controls.service")
        _risk_svc_mod = import_module("backend.06_risk_registry.02_risks.service")
        _task_svc_mod = import_module("backend.07_tasks.02_tasks.service")

        FormFillAgent = _agent_mod.FormFillAgent
        ToolContext = _dispatcher_mod.ToolContext
        AgentConfigRepository = _ac_repo_mod.AgentConfigRepository
        AgentConfigResolver = _ac_resolver_mod.AgentConfigResolver

        # Permission check
        try:
            async with self._pool.acquire() as conn:
                await require_permission(conn, user_id, "ai_copilot.execute")
        except AuthorizationError:
            yield await sse_event("fill_error", {
                "error_code": "FORBIDDEN",
                "message": "Permission denied: ai_copilot.execute required",
            })
            return

        # Resolve LLM config
        try:
            resolver = AgentConfigResolver(
                repository=AgentConfigRepository(),
                database_pool=self._pool,
                settings=self._settings,
            )
            config = await resolver.resolve(agent_type_code="grc_assistant", org_id=org_id)
        except Exception as exc:
            self._logger.error("agent_fill config resolve failed session=%s: %s", session_id, exc)
            yield await sse_event("fill_error", {
                "error_code": "CONFIG_ERROR",
                "message": "AI configuration error. Please contact your administrator.",
            })
            return

        # Build context note from page_context
        _ctx_lines = []
        if page_context:
            if page_context.get("control_id"):
                _ctrl_code = page_context.get("control_code", "")
                _ctrl_name = page_context.get("control_name", "")
                _fw_name = page_context.get("framework_name", "")
                _ctrl_label = f"{_ctrl_code} — {_ctrl_name}" if _ctrl_code and _ctrl_name else _ctrl_code or _ctrl_name or ""
                _ctx_lines.append(f"- The user is currently viewing control: {_ctrl_label}" + (f" in framework {_fw_name}" if _fw_name else ""))
                _ctx_lines.append(f"  [control_id for tool use: {page_context['control_id']}]")
            if page_context.get("risk_id"):
                _risk_title = page_context.get("risk_title", page_context.get("entity_title", ""))
                _ctx_lines.append(f"- The user is currently viewing risk: {_risk_title}")
                _ctx_lines.append(f"  [risk_id for tool use: {page_context['risk_id']}]")
            if page_context.get("framework_id"):
                _fw_name2 = page_context.get("framework_name", "")
                _ctx_lines.append(f"- The user is currently viewing framework: {_fw_name2}")
                _ctx_lines.append(f"  [framework_id for tool use: {page_context['framework_id']}]")
            if page_context.get("entity_type") and page_context.get("entity_id"):
                _etype = page_context["entity_type"]
                _etitle = page_context.get("entity_title", page_context.get("entity_id", ""))
                _ctx_lines.append(f"- The form is being opened in the context of {_etype}: {_etitle}")
                _ctx_lines.append(f"  [entity_id for tool use: {page_context['entity_id']}]")
            if page_context.get("org_id"):
                _ctx_lines.append(f"  [org_id: {page_context['org_id']}]")
            if page_context.get("workspace_id"):
                _ctx_lines.append(f"  [workspace_id: {page_context['workspace_id']}]")
            if page_context.get("current_form"):
                import json as _json
                _form_str = _json.dumps(page_context["current_form"], indent=2)
                _ctx_lines.append(f"- Current form state (enhance or fill missing fields):\n{_form_str}")

        _context_block = (
            "\n\nCURRENT PAGE CONTEXT (use these IDs in tool calls and field values):\n" +
            "\n".join(_ctx_lines)
        ) if _ctx_lines else ""

        # Detect if this is an edit context.
        # page_context may carry an explicit _is_edit flag (takes precedence);
        # otherwise infer from entity IDs that represent the entity being edited
        # (risk_id / framework_id / control_id are parent context IDs for
        # assessment/treatment_plan and should not trigger edit-mode for those types).
        if page_context and "_is_edit" in page_context:
            _is_edit = bool(page_context["_is_edit"])
        else:
            _is_edit = bool(
                page_context and (
                    page_context.get("framework_id") or page_context.get("control_id") or
                    page_context.get("entity_id")
                )
            )
        _mode_label = "editing an existing" if _is_edit else "creating a new"

        _FIELD_HINTS = {
            "framework": (
                "Framework fields for grc_propose_form_fields:\n"
                "  - name (string)\n"
                "  - description (string — 2-3 sentences on the framework's purpose and scope)\n"
                "  - framework_type_code: one of compliance_standard, security_framework, privacy_regulation, industry_standard, internal_policy, custom\n"
                "  - framework_category_code: one of compliance, security, privacy, industry, operational, custom\n"
                "\n"
                "When in form-fill mode: Propose ALL fields. If current_form has values, enhance/improve them rather than replacing wholesale."
            ),
            "control": (
                "Control fields for grc_propose_form_fields:\n"
                "  - name (string)\n"
                "  - description (string — 2-3 sentences explaining the control's purpose and scope)\n"
                "  - control_code (string — short uppercase code like CC6.1, AC-2, PR.AC-1; omit if editing)\n"
                "  - control_category_code: one of access_control, change_management, incident_response, data_protection, network_security, physical_security, risk_management, vendor_management, hr_security, business_continuity, cryptography, logging_monitoring, asset_management, compliance\n"
                "  - criticality_code: one of critical, high, medium, low\n"
                "  - automation_potential: one of full, partial, manual\n"
                "  - implementation_guidance (string — newline-separated actionable steps, 3-6 items)\n"
                "  - guidance (string — implementation guidance prose, for edit forms)\n"
                "  - tags (string — comma-separated relevant tags)\n"
                "\n"
                "When in form-fill mode: Propose ALL applicable fields. If current_form has values, enhance/improve them. "
                "Use framework context to choose appropriate codes."
            ),
            "risk": (
                "Risk fields for grc_propose_form_fields:\n"
                "  - title (string)\n"
                "  - description (string — 2-3 sentences describing the risk, its likelihood and impact)\n"
                "  - risk_category_code: one of operational, strategic, compliance, financial, reputational, technology, legal, vendor\n"
                "  - risk_level_code: one of critical, high, medium, low\n"
                "  - treatment_type_code: one of mitigate, accept, transfer, avoid\n"
                "  - notes (string — optional internal notes or context)\n"
                "  - business_impact (string — optional description of business impact if risk materialises)\n"
                "\n"
                "When in form-fill mode: Propose ALL applicable fields. If current_form has values, enhance/improve them."
            ),
            "requirement": (
                "Requirement fields for grc_propose_form_fields:\n"
                "  - name (string — clear title for this requirement group)\n"
                "  - description (string — 1-2 sentences explaining the requirement's scope)\n"
                "  - requirement_code (string — short uppercase code matching the framework, e.g. CC6, A.9, PR.AC)\n"
                "\n"
                "When in form-fill mode: Fill ALL fields. Use the framework context to pick a code that fits the framework's numbering style. "
                "Enhance existing values if already present."
            ),
            "task": (
                "Task fields for grc_propose_form_fields:\n"
                "  - title (string)\n"
                "  - description (string — clear description of what needs to be done)\n"
                "  - task_type_code: one of evidence_collection, control_remediation, risk_mitigation, general\n"
                "  - priority_code: one of critical, high, medium, low\n"
                "  - acceptance_criteria (string — newline-separated list of measurable criteria for task completion)\n"
                "  - remediation_plan (string — step-by-step remediation plan if applicable)\n"
                "\n"
                "When in form-fill mode: Propose ALL applicable fields. If current_form has values, enhance/improve them. "
                "entity_type and entity_id are OPTIONAL — only include if page context has entity_id."
            ),
            "assessment": (
                "Assessment fields for grc_propose_form_fields:\n"
                "  - assessment_type: one of inherent, residual\n"
                "    (inherent = raw risk before controls; residual = risk after controls are applied)\n"
                "  - likelihood_score: integer 1-5 (1=Very Low, 2=Low, 3=Medium, 4=High, 5=Very High)\n"
                "  - impact_score: integer 1-5 (1=Very Low, 2=Low, 3=Medium, 4=High, 5=Very High)\n"
                "  - assessment_notes (string — 2-4 sentences explaining the scoring rationale)\n"
                "\n"
                "When in form-fill mode: Propose ALL fields. The risk context is available in page_context. "
                "All score values must be string representations of integers (e.g. '4')."
            ),
            "treatment_plan": (
                "Treatment plan fields for grc_propose_form_fields:\n"
                "  - plan_description (string — 2-4 sentences describing the treatment approach)\n"
                "  - action_items (string — bullet-point list of specific actions, one per line starting with '-')\n"
                "  - plan_status: one of draft, in_progress, completed, on_hold, cancelled\n"
                "  - target_date (string — ISO date YYYY-MM-DD, or empty string)\n"
                "  - review_frequency: one of monthly, quarterly, semi_annual, annual (or empty string)\n"
                "\n"
                "When in form-fill mode: Propose ALL applicable fields. If current_form has values, enhance/improve them. "
                "The risk context is available in page_context."
            ),
        }
        _field_hint = _FIELD_HINTS.get(entity_type, "")

        system_prompt = f"""\
You are an AI assistant embedded in the "{entity_type}" form in K-Control GRC. \
The user is {_mode_label} {entity_type}.{_context_block}

You have TWO response modes:

MODE 1 — FORM FILL (when the user provides form-relevant content):
When the user describes what they want to create, asks you to fill the form, provides details \
for the {entity_type}, or asks you to change/update/improve specific fields, follow this process:
1. READ the page context and current_form above — current_form shows what the user has already filled in.
2. For each field: if current_form has a value, ENHANCE or IMPROVE it based on the user's instruction. \
If empty, generate an appropriate value.
3. If the form requires entity IDs (e.g. a task needs entity_id), use IDs from context directly — \
do NOT call extra tools if the ID is already provided.
4. Call `grc_propose_form_fields` with all field values once ready.

MODE 2 — CONVERSATION (when the user sends a generic message):
When the user sends a greeting (hello, hi, thanks), asks a question about your capabilities, \
asks clarifying questions, or sends any message that is NOT a form-fill instruction:
- Reply with a helpful, concise text response.
- Do NOT call grc_propose_form_fields.
- Do NOT change any form fields.
- If appropriate, explain what you can help with (e.g. "I can help you fill out this {entity_type} form. \
Describe what you want to create and I'll fill in the fields for you.").

FIELD NAMES AND ALLOWED VALUES:
{_field_hint}

CRITICAL RULES:
- Use EXACTLY the field names listed above — do NOT use generic names like "category" or "treatment_strategy".
- Only call grc_propose_form_fields when the user's message contains actionable form content.
- The "fields" parameter must be a JSON object mapping field_name → value string.
- NEVER guess UUIDs. Use IDs from context or look them up with tools.
- If current_form has existing values, enhance/improve them — do not ignore what the user already wrote.
- For tasks: ONLY include entity_type/entity_id if the page context contains an entity_id. \
  If no entity_id is in context, skip those fields and call grc_propose_form_fields immediately \
  with just title, description, task_type_code, and priority_code.
- Keep your messages short and focused. Ask only what you truly need.
- NEVER mention UUID strings in your responses to the user.
- Entity type for this form: {entity_type}
"""

        _raw_pool = self._pool.pool
        _cache_mod = import_module("backend.01_core.cache")
        _null_cache = _cache_mod.NullCacheManager()
        _svc_kwargs = dict(settings=self._settings, database_pool=self._pool, cache=_null_cache)

        tool_context = ToolContext(
            pool=_raw_pool,
            user_id=user_id,
            tenant_key=tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            framework_service=_fw_svc_mod.FrameworkService(**_svc_kwargs),
            requirement_service=_req_svc_mod.RequirementService(**_svc_kwargs),
            control_service=_ctrl_svc_mod.ControlService(**_svc_kwargs),
            risk_service=_risk_svc_mod.RiskService(**_svc_kwargs),
            task_service=_task_svc_mod.TaskService(**_svc_kwargs),
        )

        agent = FormFillAgent(config=config, settings=self._settings)

        async for chunk in agent.run(
            message=message,
            history=history,
            system_prompt=system_prompt,
            tool_context=tool_context,
        ):
            yield chunk
