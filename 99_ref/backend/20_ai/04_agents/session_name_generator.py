"""
SessionNameGenerator — fire-and-forget micro-agent for conversation titles.

Fires once as asyncio.create_task() on the first message of a new conversation.
Makes a single non-streaming LLM call, updates the conversations table, and
optionally emits a session_named SSE event if a queue is provided.

Never raises — silent failure means the title stays NULL and the UI shows
"New conversation" as a fallback.
"""

from __future__ import annotations

import asyncio
from importlib import import_module
from typing import TYPE_CHECKING

import asyncpg

if TYPE_CHECKING:
    from typing import Any  # noqa: F401

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.agents.session_namer")

_PROMPT = (
    "Generate a concise 3-7 word title for a GRC (Governance, Risk & Compliance) "
    "conversation that starts with the following user message. "
    "Reply with only the title — no quotes, no punctuation at the end, no explanation.\n\n"
    "User message: {message}"
)

_MAX_TITLE_LENGTH = 120


async def generate_session_name(
    *,
    conversation_id: str,
    first_message: str,
    pool: asyncpg.Pool,
    config: "ResolvedLLMConfig",
    sse_queue: asyncio.Queue | None = None,
) -> None:
    """
    Async task — designed to be launched with asyncio.create_task().
    Updates conversations.title in Postgres.
    If sse_queue is provided, puts a session_named SSE string into it.
    """
    try:
        get_provider = import_module("backend.20_ai.14_llm_providers.factory").get_provider

        provider = get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=config.api_key,
            model_id=config.model_id,
        )

        response = await provider.chat_completion(
            messages=[
                {"role": "user", "content": _PROMPT.format(message=first_message[:500])},
            ],
            tools=None,
            temperature=1.0,
            max_tokens=40,
        )

        title = (response.content or "").strip()
        if not title:
            return

        # Sanitize
        title = title.strip('"\'').strip()[:_MAX_TITLE_LENGTH]
        if not title:
            return

        async with pool.acquire() as conn:
            updated = await conn.execute(
                """
                UPDATE "20_ai"."20_fct_conversations"
                SET title = $1, updated_at = NOW()
                WHERE id = $2::uuid AND title IS NULL
                """,
                title, conversation_id,
            )

        if updated == "UPDATE 0":
            # Title was already set (race), nothing to do
            return

        _logger.debug("Session %s named: %s", conversation_id, title)

        if sse_queue is not None:
            sse_session_named = import_module("backend.20_ai.02_conversations.streaming").sse_session_named
            try:
                sse_str = await sse_session_named(conversation_id, title)
                sse_queue.put_nowait(sse_str)
            except Exception:
                pass

    except Exception as exc:
        # Non-fatal — title stays NULL
        _logger.debug("Session naming failed for %s: %s", conversation_id, exc)
