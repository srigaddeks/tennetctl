"""
Shared LLM utility functions for AI agents.

Eliminates the duplicate _llm_complete / _post pattern that was copy-pasted
across signal_spec, test_dataset_gen, signal_codegen, and threat_composer.

All agents should call llm_complete() from here instead of maintaining their
own httpx boilerplate.

LangFuse integration is optional — pass tracer=None to skip tracing entirely.

Usage:
    from backend.20_ai._llm_utils import llm_complete, resolve_llm_config, strip_fences

    provider_url, api_key, model = resolve_llm_config(llm_config, settings)

    raw = await llm_complete(
        provider_url=provider_url,
        api_key=api_key,
        model=model,
        system=SYSTEM_PROMPT,
        user="Generate the signal code now.",
        max_tokens=4000,
        temperature=1.0,
        tracer=tracer,
        trace=trace,
        generation_name="generate_initial_code",
        generation_metadata={"iteration": 1, "signal_id": signal_id},
    )
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any

import httpx

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.llm_utils")


def resolve_llm_config(llm_config, settings) -> tuple[str, str, str]:
    """
    Resolve provider_url, api_key, model from llm_config object or settings fallback.

    llm_config can be an AgentConfigResult dataclass or any object with
    provider_base_url / api_key / model_id attributes.
    """
    provider_url = (
        getattr(llm_config, "provider_base_url", None)
        or getattr(settings, "ai_provider_url", None)
    )
    api_key = (
        getattr(llm_config, "api_key", None)
        or getattr(settings, "ai_api_key", None)
    )
    model = (
        getattr(llm_config, "model_id", None)
        or getattr(settings, "ai_model", "gpt-4o")
    )
    if not provider_url or not api_key:
        raise RuntimeError(
            "LLM not configured — set AI_API_KEY + AI_PROVIDER_URL in environment "
            "or configure an agent config in the database"
        )
    return provider_url, api_key, model


async def llm_complete(
    *,
    provider_url: str,
    api_key: str,
    model: str,
    system: str,
    user: str,
    max_tokens: int = 4000,
    temperature: float = 1.0,
    timeout: float = 120.0,
    # LangFuse tracing (all optional)
    tracer=None,
    trace=None,
    generation_name: str = "llm_call",
    generation_metadata: dict | None = None,
) -> str:
    """
    Make a single non-streaming chat completion call.

    Returns the raw string content from the LLM response.
    Strips leading/trailing whitespace.

    If tracer + trace are provided, wraps the call in a LangFuse generation span
    and records input tokens, output tokens, model, and latency.

    Raises httpx.HTTPStatusError on HTTP errors (already logged).
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    # Open LangFuse generation span
    gen = None
    if tracer is not None and trace is not None:
        gen = tracer.generation(
            trace,
            name=generation_name,
            model=model,
            input=messages,
            metadata=generation_metadata or {},
        )

    _logger.debug(
        "llm_utils.call",
        extra={"model": model, "max_tokens": max_tokens, "gen_name": generation_name},
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{provider_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            if not resp.is_success:
                _logger.error(
                    "llm_utils.http_error",
                    extra={"status": resp.status_code, "body": resp.text[:500]},
                )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        if gen is not None:
            gen.end(
                output=content,
                usage={"input": input_tokens, "output": output_tokens},
            )

        return content

    except Exception as exc:
        if gen is not None:
            gen.end(level="ERROR", status_message=str(exc)[:500])
        raise


async def llm_complete_with_history(
    *,
    provider_url: str,
    api_key: str,
    model: str,
    system: str,
    messages: list[dict],
    max_tokens: int = 4000,
    temperature: float = 1.0,
    timeout: float = 120.0,
    # LangFuse tracing (all optional)
    tracer=None,
    trace=None,
    generation_name: str = "llm_call_with_history",
    generation_metadata: dict | None = None,
) -> str:
    """
    Chat completion with a full conversation history.

    messages: list of {role, content} dicts (NOT including the system message).
    System message is prepended automatically.
    """
    full_messages = [{"role": "system", "content": system}] + messages

    gen = None
    if tracer is not None and trace is not None:
        gen = tracer.generation(
            trace,
            name=generation_name,
            model=model,
            input=full_messages,
            metadata=generation_metadata or {},
        )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(
                f"{provider_url.rstrip('/')}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": full_messages,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                },
            )
            if not resp.is_success:
                _logger.error(
                    "llm_utils.http_error",
                    extra={"status": resp.status_code, "body": resp.text[:500]},
                )
            resp.raise_for_status()
            data = resp.json()

        content = data["choices"][0]["message"]["content"].strip()
        usage = data.get("usage", {})

        if gen is not None:
            gen.end(
                output=content,
                usage={
                    "input": usage.get("prompt_tokens", 0),
                    "output": usage.get("completion_tokens", 0),
                },
            )

        return content

    except Exception as exc:
        if gen is not None:
            gen.end(level="ERROR", status_message=str(exc)[:500])
        raise


def strip_fences(raw: str) -> str:
    """Strip ```json / ``` markdown fences from LLM output."""
    text = raw.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        end = len(lines) - 1
        while end > 0 and lines[end].strip() in ("```", ""):
            end -= 1
        return "\n".join(lines[1:end + 1])
    return text


def parse_json(raw: str) -> Any:
    """Strip fences and parse JSON from LLM output.

    Falls back to repairing common LLM JSON errors:
    - Single-quoted strings  →  double-quoted
    - Trailing commas before } or ]
    - JavaScript-style comments
    """
    text = strip_fences(raw)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # Attempt repair: remove JS comments, fix trailing commas
    import re as _re
    repaired = _re.sub(r'//.*?$', '', text, flags=_re.MULTILINE)  # line comments
    repaired = _re.sub(r'/\*.*?\*/', '', repaired, flags=_re.DOTALL)  # block comments
    repaired = _re.sub(r',\s*([}\]])', r'\1', repaired)  # trailing commas
    try:
        return json.loads(repaired)
    except json.JSONDecodeError:
        pass
    # Last resort: try replacing single quotes with double quotes (risky but common)
    repaired2 = repaired.replace("'", '"')
    return json.loads(repaired2)


def parse_json_array(raw: str) -> list:
    """Strip fences and parse a JSON array from LLM output."""
    result = parse_json(raw)
    if not isinstance(result, list):
        raise ValueError(f"Expected JSON array, got {type(result).__name__}")
    return result
