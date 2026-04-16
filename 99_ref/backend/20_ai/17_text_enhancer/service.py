"""
TextEnhancerService — single-call LLM text enhancement with SSE streaming.

Design invariants:
  - Single LLM call (no tool loop) — fast, low-latency enhancement
  - Resolves LLM config via AgentConfigResolver (org override → global → settings fallback)
  - Streams response content in ~5-word chunks with asyncio.sleep(0) between chunks
  - Full audit trail via unified AuditWriter
  - LangFuse tracing (optional — disabled when settings not configured)
  - OTEL counter ai.text_enhance.count (entity_type, field_name, outcome)
  - DB connection released before streaming begins — never held during SSE
"""

from __future__ import annotations

import asyncio
import uuid
from importlib import import_module
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    pass  # type-only imports — no runtime cost

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_audit_module = import_module("backend.01_core.audit")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_ai_constants_module = import_module("backend.20_ai.constants")
_resolver_module = import_module("backend.20_ai.12_agent_config.resolver")
_agent_config_repo_module = import_module("backend.20_ai.12_agent_config.repository")
_factory_module = import_module("backend.20_ai.14_llm_providers.factory")
_provider_module = import_module("backend.20_ai.14_llm_providers.provider")
_streaming_module = import_module("backend.20_ai.02_conversations.streaming")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
AuthorizationError = _errors_module.AuthorizationError
require_permission = _perm_check_module.require_permission
AIAuditEventType = _ai_constants_module.AIAuditEventType
AgentConfigResolver = _resolver_module.AgentConfigResolver
AgentConfigRepository = _agent_config_repo_module.AgentConfigRepository
get_provider = _factory_module.get_provider
StreamChunk = _provider_module.StreamChunk
sse_event = _streaming_module.sse_event

# ---------------------------------------------------------------------------
# System / user prompt templates
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Per-field system prompt registry
# ---------------------------------------------------------------------------
# Each entry is the FULL system prompt for that field_name.
# The common OUTPUT CONTRACT is injected at the end of every prompt so it
# never has to be repeated.
# Placeholders: {entity_display_name}, {entity_type}, {optional_context_block}
# ---------------------------------------------------------------------------

_OUTPUT_CONTRACT = """\

Respond with only the improved text — no explanations, no preamble, no markdown code fences.
Write specific, concrete language rather than generic placeholders.
Keep professional GRC terminology throughout.
Only include facts that are present in the original text or the context provided.\
"""

_FIELD_SYSTEM_PROMPTS: dict[str, str] = {

    # ── description ────────────────────────────────────────────────────────────
    "description": """\
You are an expert GRC technical writer helping improve documentation quality.

You are rewriting the description field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
A well-written GRC description:
- States what the {entity_type} is and why it exists in 1–3 concise sentences
- Uses active voice and precise domain language
- Avoids vague filler phrases (say specifically what is ensured or controlled)
- Focuses on the purpose, not implementation steps or evaluation criteria{OUTPUT_CONTRACT}""",

    # ── guidance ────────────────────────────────────────────────────────────────
    "guidance": """\
You are an expert GRC technical writer helping improve documentation quality.

You are rewriting the guidance field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
Good guidance provides high-level direction to practitioners:
- Explains the intent and scope — why this {entity_type} matters to the organisation
- References relevant frameworks or standards (NIST, ISO 27001, SOC 2, etc.) where applicable
- Written for a technical-but-business-aware audience, not as step-by-step procedures
- 1–4 paragraphs, well structured
- Avoids restating what is already in the description{OUTPUT_CONTRACT}""",

    # ── implementation_guidance ─────────────────────────────────────────────────
    "implementation_guidance": """\
You are an expert GRC practitioner and security engineer helping improve documentation quality.

You are rewriting the implementation guidance field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
Good implementation guidance is a structured, actionable list. Each item:
- Starts with a verb (Configure, Enable, Review, Document, Rotate, Enforce…)
- Describes one specific, concrete action a practitioner must take
- References specific tooling, settings, or configuration locations where relevant
- Is verifiable — someone can confirm it was completed
- Is scoped to this specific {entity_type}

Format: one action per line, no bullet prefix (the UI adds its own).
Order: most critical or foundational actions first.{OUTPUT_CONTRACT}""",

    # ── acceptance_criteria ─────────────────────────────────────────────────────
    "acceptance_criteria": """\
You are an expert GRC auditor and compliance engineer helping improve documentation quality.

You are rewriting the acceptance criteria field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
Good acceptance criteria define when the work is complete:
- Written as testable, verifiable statements rather than aspirations
- Follow patterns like: "Evidence of X exists", "System Y is configured to Z", "Report shows…"
- Cover both functional completion and audit evidence requirements
- Measurable enough that an auditor can confirm pass/fail without interpretation
- Reference specific artefacts: logs, reports, screenshots, config exports, sign-off records
- Avoid vague terms like "properly configured" or "adequately secured"

Format: one criterion per line.
Order: primary functional criteria first, audit evidence criteria last.{OUTPUT_CONTRACT}""",

    # ── remediation_plan ────────────────────────────────────────────────────────
    "remediation_plan": """\
You are an expert GRC project manager and security engineer helping improve documentation quality.

You are rewriting the remediation plan field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
A good remediation plan describes the steps to close a gap or fix a finding:
- Breaks work into clear, ordered phases or milestones
- Assigns ownership to a role rather than a specific person (unless one is already named)
- Includes timeframes or sequencing (immediate, within 30 days, prior to next audit)
- Calls out dependencies or pre-conditions explicitly
- Ends with a validation step explaining how completion will be confirmed
- Is actionable and practical, not aspirational

Keep it concise but complete — a reader should be able to act on it directly.{OUTPUT_CONTRACT}""",

    # ── notes ───────────────────────────────────────────────────────────────────
    "notes": """\
You are an expert GRC analyst helping improve documentation quality.

You are rewriting the notes field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
Good notes capture context, observations, and decisions that don't fit structured fields:
- Factual and specific — include dates, versions, decisions, exceptions, or open questions where relevant
- Flag risks, caveats, or known limitations clearly
- Use short paragraphs or bullet points for readability
- Written for a future reader who may not have context — be explicit and self-contained
- Avoid repeating what is already captured in structured fields (title, status, owner){OUTPUT_CONTRACT}""",

    # ── business_impact ─────────────────────────────────────────────────────────
    "business_impact": """\
You are an expert GRC risk analyst helping improve documentation quality.

You are rewriting the business impact field of a risk record titled "{entity_display_name}".
{optional_context_block}
Good business impact text describes the consequences if this risk materialises:
- Quantifies where possible (financial loss range, SLA breach %, regulatory fine scale)
- Covers multiple dimensions: financial, operational, reputational, regulatory/legal, customer
- Written to be understood by both executive and technical audiences
- Uses concrete scenarios rather than abstract statements
- Distinguishes direct impacts from secondary or cascading effects
- Focuses on consequences, not likelihood (likelihood belongs in risk scoring){OUTPUT_CONTRACT}""",

    # ── comment_body ────────────────────────────────────────────────────────────
    "comment_body": """\
You are a professional GRC practitioner helping improve documentation quality.

You are rewriting a comment on a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
A well-written GRC comment:
- States its point clearly in the first sentence
- Provides specific context, evidence, or references to support the point
- Is professional in tone — constructive and precise
- Uses markdown sparingly (bold for emphasis, bullet lists only for 3+ items)
- Ends with a clear next action, question, or decision point if one is needed
- Avoids restating what is already visible in the record title or status

Keep the voice natural and human — this is a comment, not a formal document.{OUTPUT_CONTRACT}""",

    # ── name / title ────────────────────────────────────────────────────────────
    "name": """\
You are an expert GRC technical writer helping improve documentation quality.

You are rewriting the name field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
A good {entity_type} name:
- Is concise (3–8 words), specific, and immediately meaningful
- Uses established GRC terminology
- Avoids redundant type prefixes (the type is already known from context)
- Is differentiable from sibling records
- Uses title case{OUTPUT_CONTRACT}""",

    "title": """\
You are an expert GRC technical writer helping improve documentation quality.

You are rewriting the title field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
A good {entity_type} title:
- Is concise (3–10 words), action-oriented, and self-explanatory
- For tasks: starts with a verb (Implement, Review, Document, Rotate, Remediate…)
- For risks: names the threat and its primary target
- Avoids unexplained acronyms
- Is differentiable from sibling records{OUTPUT_CONTRACT}""",
}

# Fallback for any field_name not explicitly registered above
_DEFAULT_SYSTEM_PROMPT = """\
You are an expert GRC (Governance, Risk & Compliance) technical writer and analyst helping improve documentation quality.

You are rewriting the {field_name} field of a {entity_type} record titled "{entity_display_name}".
{optional_context_block}
A well-written GRC text field:
- Is specific, accurate, and uses correct GRC terminology
- Avoids vague filler language and unnecessary passive voice
- Is appropriately concise — says what needs to be said, nothing more
- For list fields: one item per line; for prose: well-structured paragraphs{OUTPUT_CONTRACT}"""


def _get_system_prompt(field_name: str) -> str:
    """Return the appropriate system prompt template for the given field name."""
    return _FIELD_SYSTEM_PROMPTS.get(field_name, _DEFAULT_SYSTEM_PROMPT)


_USER_MESSAGE_TEMPLATE = """\
Here is the current {field_name}:
---
{formatted_current_value}
---

Please apply the following improvement: {instruction}

Write only the improved text.\
"""

# Providers that natively support stream_chat_completion
_STREAMING_PROVIDERS = frozenset({"openai", "openai_compatible", "anthropic", "azure_openai"})


# ---------------------------------------------------------------------------
# LangFuse helpers (module-level so they can be shared across invocations)
# ---------------------------------------------------------------------------

def _init_langfuse(settings):
    """Initialise LangFuse client. Returns None when not configured (non-fatal)."""
    if not getattr(settings, "ai_langfuse_enabled", False):
        return None
    try:
        from langfuse import Langfuse  # dynamic import — optional dependency
        return Langfuse(
            public_key=settings.ai_langfuse_public_key,
            secret_key=settings.ai_langfuse_secret_key,
            host=settings.ai_langfuse_host or "https://cloud.langfuse.com",
        )
    except Exception as exc:
        get_logger("backend.ai.text_enhancer").warning(
            "LangFuse init failed (non-fatal): %s", exc
        )
        return None


def _lf_record_generation(lf_client, trace_id: str, response, system_prompt: str, user_message: str) -> None:
    """Record a single LLM generation on an existing LangFuse trace."""
    if not lf_client or not trace_id:
        return
    try:
        trace = lf_client.get_trace(trace_id)
        trace.generation(
            name="text_enhance/llm_call",
            model=response.model_id,
            input=[
                {"role": "system", "content": system_prompt[:500]},  # truncated for storage
                {"role": "user", "content": user_message[:500]},
            ],
            output=response.content or "",
            usage={"input": response.input_tokens, "output": response.output_tokens},
        )
    except Exception:
        pass  # LangFuse tracing is always best-effort


# ---------------------------------------------------------------------------
# OTEL metrics helper
# ---------------------------------------------------------------------------

def _get_enhance_counter():
    """Lazy-initialise the ai.text_enhance.count OTEL counter.

    We use opentelemetry.metrics.get_meter() directly so the counter is
    registered against whichever MeterProvider the app has configured (the
    same provider that the telemetry bootstrap sets up).  If no provider is
    active yet the call is a no-op (returns a noop meter).
    """
    try:
        from opentelemetry import metrics as otel_metrics
        meter = otel_metrics.get_meter("backend.ai.text_enhancer")
        return meter.create_counter(
            "ai.text_enhance.count",
            description="Number of text enhancement requests",
        )
    except Exception:
        return None


_enhance_counter = None  # lazily created on first use


def _record_enhance_metric(entity_type: str, field_name: str, outcome: str) -> None:
    """Increment the ai.text_enhance.count counter (best-effort)."""
    global _enhance_counter
    try:
        if _enhance_counter is None:
            _enhance_counter = _get_enhance_counter()
        if _enhance_counter is not None:
            _enhance_counter.add(1, {
                "entity_type": entity_type,
                "field_name": field_name,
                "outcome": outcome,
            })
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Prompt builders
# ---------------------------------------------------------------------------

def _build_context_block(entity_context: dict | None) -> str:
    """Format optional entity_context into a readable prompt block."""
    if not entity_context:
        return ""
    lines = ["Additional entity context:"]
    for key, value in entity_context.items():
        if value is None:
            continue
        if isinstance(value, list):
            value_str = ", ".join(str(v) for v in value)
        elif isinstance(value, dict):
            value_str = str(value)
        else:
            value_str = str(value)
        # Truncate very long values to avoid prompt bloat
        if len(value_str) > 300:
            value_str = value_str[:297] + "..."
        lines.append(f"  {key}: {value_str}")
    return "\n".join(lines) + "\n"


def _format_current_value(current_value: str | list[str]) -> str:
    """Format the current field value for inclusion in the user message prompt."""
    if isinstance(current_value, list):
        if not current_value:
            return "(empty list)"
        return "\n".join(f"- {item}" for item in current_value)
    return current_value if current_value else "(empty)"


def _derive_display_name(entity_context: dict | None, entity_type: str) -> str:
    """Extract a human-readable entity name from context, falling back gracefully."""
    if not entity_context:
        return entity_type
    # Common name fields across GRC entity types
    for key in ("name", "title", "code", "reference_code"):
        val = entity_context.get(key)
        if val and isinstance(val, str):
            return val
    return entity_type


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------

@instrument_class_methods(
    namespace="ai.text_enhancer.service",
    logger_name="backend.ai.text_enhancer.instrumentation",
)
class TextEnhancerService:
    """
    Inline text enhancement powered by a single LLM call.

    Usage:
        service = TextEnhancerService(
            settings=app.state.settings,
            database_pool=app.state.database_pool,
        )
        async for chunk in service.stream_enhance(request, user_id, tenant_key):
            yield chunk
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
        self._logger = get_logger("backend.ai.text_enhancer")

    # ------------------------------------------------------------------
    # Public streaming entry point
    # ------------------------------------------------------------------

    async def stream_enhance(
        self,
        request,  # EnhanceTextRequest — avoid circular import by typing as Any
        user_id: str,
        tenant_key: str,
    ) -> AsyncIterator[str]:
        """
        Yield SSE-formatted strings for the text enhancement stream.

        Flow:
          1. Permission check + release DB connection
          2. Resolve LLM config
          3. Build prompts
          4. Call LLM (single call, no tool loop)
          5. Stream response in word chunks
          6. Emit enhance_complete + write audit entry
        """
        enhance_id = str(uuid.uuid4())
        entity_type: str = request.entity_type
        field_name: str = request.field_name
        org_id: str | None = request.org_id

        self._logger.info(
            "text_enhance start enhance_id=%s entity_type=%s field=%s user=%s",
            enhance_id, entity_type, field_name, user_id,
        )

        # --- 1. Permission check (acquire + release before streaming) ---
        try:
            async with self._pool.acquire() as conn:
                await require_permission(conn, user_id, "ai_copilot.execute")
        except AuthorizationError:
            _record_enhance_metric(entity_type, field_name, "forbidden")
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "FORBIDDEN",
                "message": "Permission denied: ai_copilot.execute required",
            })
            return
        except Exception as exc:
            self._logger.error(
                "text_enhance permission check failed enhance_id=%s: %s", enhance_id, exc
            )
            _record_enhance_metric(entity_type, field_name, "error")
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "PERMISSION_CHECK_FAILED",
                "message": "Could not verify permissions. Please try again.",
            })
            return

        # --- 2. Resolve LLM config ---
        try:
            config = await self._resolver.resolve(
                agent_type_code="text_enhancer",
                org_id=org_id,
            )
        except Exception as exc:
            self._logger.error(
                "text_enhance config resolve failed enhance_id=%s: %s", enhance_id, exc
            )
            _record_enhance_metric(entity_type, field_name, "error")
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "CONFIG_ERROR",
                "message": "AI configuration error. Please contact your administrator.",
            })
            return

        # Apply model override if provided
        effective_model_id = request.model_id or config.model_id

        # --- 3. Build prompts (per-field specialised system prompt) ---
        entity_display_name = _derive_display_name(request.entity_context, entity_type)
        context_block = _build_context_block(request.entity_context)
        optional_context_block = context_block if context_block else ""

        prompt_template = _get_system_prompt(field_name)
        system_prompt = prompt_template.format(
            entity_type=entity_type,
            field_name=field_name,
            entity_display_name=entity_display_name,
            optional_context_block=optional_context_block,
            OUTPUT_CONTRACT=_OUTPUT_CONTRACT,
        )

        formatted_value = _format_current_value(request.current_value)
        user_message = _USER_MESSAGE_TEMPLATE.format(
            field_name=field_name,
            formatted_current_value=formatted_value,
            instruction=request.instruction,
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        # --- 4. LLM call (real streaming where supported, batch fallback) ---
        try:
            provider = get_provider(
                provider_type=config.provider_type,
                provider_base_url=config.provider_base_url,
                api_key=config.api_key,
                model_id=effective_model_id,
                temperature=config.temperature,  # use config temperature (avoids model-specific rejections)
            )
        except Exception as exc:
            self._logger.error(
                "text_enhance provider init failed enhance_id=%s model=%s: %s",
                enhance_id, effective_model_id, exc,
            )
            _record_enhance_metric(entity_type, field_name, "error")
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "PROVIDER_ERROR",
                "message": "AI provider configuration error. Please contact your administrator.",
            })
            return

        use_streaming = config.provider_type in _STREAMING_PROVIDERS and hasattr(provider, "stream_chat_completion")

        enhanced_text = ""
        input_tokens = 0
        output_tokens = 0

        if use_streaming:
            # --- 5a. Real token-by-token streaming ---
            try:
                stream = provider.stream_chat_completion(
                    messages=messages,
                    temperature=config.temperature,
                    max_tokens=2048,
                )
                async for chunk in stream:
                    if chunk.delta:
                        enhanced_text += chunk.delta
                        yield await sse_event("content_delta", {"delta": chunk.delta})
                    if chunk.is_final:
                        input_tokens = chunk.input_tokens
                        output_tokens = chunk.output_tokens
                    await asyncio.sleep(0)  # yield to event loop
            except Exception as exc:
                self._logger.error(
                    "text_enhance streaming failed enhance_id=%s: %s", enhance_id, exc
                )
                _record_enhance_metric(entity_type, field_name, "error")
                yield await sse_event("enhance_error", {
                    "enhance_id": enhance_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error. Please try again.",
                })
                return
        else:
            # --- 5b. Batch fallback (no streaming support) ---
            try:
                response = await provider.chat_completion(
                    messages=messages,
                    tools=None,
                    temperature=config.temperature,
                    max_tokens=2048,
                )
            except Exception as exc:
                self._logger.error(
                    "text_enhance llm call failed enhance_id=%s: %s", enhance_id, exc
                )
                _record_enhance_metric(entity_type, field_name, "error")
                yield await sse_event("enhance_error", {
                    "enhance_id": enhance_id,
                    "error_code": "LLM_ERROR",
                    "message": "The AI service encountered an error. Please try again.",
                })
                return
            enhanced_text = (response.content or "").strip()
            input_tokens = response.input_tokens
            output_tokens = response.output_tokens
            # Emit the full text as a single delta so the frontend still sees content_delta
            if enhanced_text:
                yield await sse_event("content_delta", {"delta": enhanced_text})
                await asyncio.sleep(0)

        enhanced_text = enhanced_text.strip()

        if not enhanced_text:
            self._logger.warning(
                "text_enhance empty response enhance_id=%s model=%s", enhance_id, effective_model_id
            )
            _record_enhance_metric(entity_type, field_name, "error")
            yield await sse_event("enhance_error", {
                "enhance_id": enhance_id,
                "error_code": "EMPTY_RESPONSE",
                "message": "The AI returned an empty response. Please try again.",
            })
            return

        # --- 6. Emit completion event ---
        yield await sse_event("enhance_complete", {
            "enhance_id": enhance_id,
            "enhanced_value": enhanced_text,
            "usage": {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        })

        _record_enhance_metric(entity_type, field_name, "success")

        # --- LangFuse trace (best-effort, non-blocking) ---
        lf_client = _init_langfuse(self._settings)
        if lf_client:
            try:
                trace = lf_client.trace(
                    name=f"text_enhancer/{entity_type}/{field_name}",
                    user_id=user_id,
                    metadata={
                        "enhance_id": enhance_id,
                        "entity_type": entity_type,
                        "field_name": field_name,
                        "org_id": org_id,
                        "model_id": effective_model_id,
                        "streamed": use_streaming,
                    },
                )
                trace.generation(
                    name="text_enhance/llm_call",
                    model=effective_model_id,
                    input=[
                        {"role": "system", "content": system_prompt[:500]},
                        {"role": "user", "content": user_message[:500]},
                    ],
                    output=enhanced_text[:500],
                    usage={
                        "input": input_tokens,
                        "output": output_tokens,
                    },
                )
                # Flush asynchronously — never block the SSE stream
                asyncio.create_task(asyncio.to_thread(lf_client.flush))
            except Exception as lf_exc:
                self._logger.debug("LangFuse trace failed (non-fatal): %s", lf_exc)

        # --- Audit trail ---
        try:
            async with self._pool.acquire() as conn:
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=enhance_id,
                        tenant_key=tenant_key,
                        entity_type=entity_type,
                        entity_id=request.entity_id or "unknown",
                        event_type="text_enhanced",
                        event_category="ai",
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "field_name": field_name,
                            "model_id": effective_model_id,
                            "input_tokens": str(input_tokens),
                            "output_tokens": str(output_tokens),
                            "org_id": org_id or "",
                            "workspace_id": request.workspace_id or "",
                            "streamed": "true" if use_streaming else "false",
                        },
                        occurred_at=__import__("datetime").datetime.utcnow(),
                    ),
                )
        except Exception as audit_exc:
            # Audit failures must never surface to the caller
            self._logger.warning(
                "text_enhance audit write failed enhance_id=%s: %s", enhance_id, audit_exc
            )

        self._logger.info(
            "text_enhance complete enhance_id=%s entity_type=%s field=%s "
            "input_tokens=%d output_tokens=%d streamed=%s",
            enhance_id, entity_type, field_name,
            input_tokens, output_tokens, use_streaming,
        )
