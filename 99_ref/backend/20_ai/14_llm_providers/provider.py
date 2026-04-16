from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator, Protocol, runtime_checkable


@dataclass
class ToolCallResult:
    """A single tool call requested by the LLM."""
    id: str           # tool_call id from LLM
    name: str         # tool name
    arguments: dict   # parsed JSON arguments


@dataclass
class LLMResponse:
    """Normalized response from any LLM provider.

    All provider implementations convert their wire format to this.
    The agent loop only ever sees LLMResponse — never raw provider responses.
    """
    content: str | None               # Text content (None if tool calls only)
    tool_calls: list[ToolCallResult]  # Empty list if no tool calls
    input_tokens: int
    output_tokens: int
    model_id: str
    finish_reason: str                # "stop" | "tool_calls" | "length" | "error"


@dataclass
class StreamChunk:
    """A single streaming text chunk from a provider."""
    delta: str         # incremental text (may be empty string)
    is_final: bool     # True on the last chunk carrying usage stats
    input_tokens: int = 0
    output_tokens: int = 0


@runtime_checkable
class LLMProvider(Protocol):
    """Protocol all provider implementations must satisfy."""

    async def chat_completion(
        self,
        *,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """
        Send a chat completion request.

        messages: OpenAI-format message list
            [{"role": "system"|"user"|"assistant"|"tool", "content": "..."}]
            Tool results use: {"role": "tool", "tool_call_id": "...", "content": "..."}

        tools: OpenAI function-calling format
            [{"type": "function", "function": {"name": "...", "description": "...", "parameters": {...}}}]

        Returns LLMResponse with normalized content + tool_calls.
        """
        ...

    async def stream_chat_completion(
        self,
        *,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream a chat completion, yielding StreamChunk deltas as they arrive.

        The final chunk has is_final=True and carries token usage stats.
        No tool calls — streaming is only used for text-only generation.
        """
        ...
