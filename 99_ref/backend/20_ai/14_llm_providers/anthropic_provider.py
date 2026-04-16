from __future__ import annotations

import json
from importlib import import_module
from typing import AsyncIterator

import httpx

from .provider import LLMProvider, LLMResponse, StreamChunk, ToolCallResult

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.providers.anthropic")

_ANTHROPIC_VERSION = "2023-06-01"
_DEFAULT_BASE_URL = "https://api.anthropic.com"


class AnthropicProvider:
    """
    Provider for Anthropic Claude API.

    Key differences from OpenAI format (handled here, invisible to the agent):
    - system prompt is a top-level field, not a message
    - tool definitions use 'input_schema' not 'parameters'
    - tool use in response is content blocks of type 'tool_use'
    - tool results go back as content blocks of type 'tool_result'

    All differences are normalized to OpenAI format before returning LLMResponse.
    """

    def __init__(self, *, provider_base_url: str | None, api_key: str | None, model_id: str, temperature: float = 0.7) -> None:
        self._base_url = (provider_base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._api_key = api_key or ""
        self._model_id = model_id
        self._temperature = temperature

    async def chat_completion(
        self,
        *,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        target_temperature = temperature if temperature is not None else self._temperature
        system_content, anthropic_messages = self._convert_messages(messages)

        payload: dict = {
            "model": self._model_id,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": target_temperature,
        }
        if system_content:
            payload["system"] = system_content
        if tools:
            payload["tools"] = self._convert_tools(tools)

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(
                f"{self._base_url}/v1/messages",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()

        return self._parse_response(data)

    async def stream_chat_completion(
        self,
        *,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int = 4096,
    ) -> AsyncIterator[StreamChunk]:
        """Stream tokens from Anthropic Messages API.

        Anthropic SSE events:
          message_start          — carries input_tokens
          content_block_delta    — carries text delta
          message_delta          — carries output_tokens + stop_reason
          message_stop           — end of stream
        """
        target_temperature = temperature if temperature is not None else self._temperature
        system_content, anthropic_messages = self._convert_messages(messages)

        payload: dict = {
            "model": self._model_id,
            "messages": anthropic_messages,
            "max_tokens": max_tokens,
            "temperature": target_temperature,
            "stream": True,
        }
        if system_content:
            payload["system"] = system_content

        headers = {
            "x-api-key": self._api_key,
            "anthropic-version": _ANTHROPIC_VERSION,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        input_tokens = 0
        output_tokens = 0

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/v1/messages",
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                event_type = ""
                async for raw_line in resp.aiter_lines():
                    if raw_line.startswith("event:"):
                        event_type = raw_line[6:].strip()
                    elif raw_line.startswith("data:"):
                        data_str = raw_line[5:].strip()
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            continue

                        if event_type == "message_start":
                            usage = (data.get("message") or {}).get("usage") or {}
                            input_tokens = usage.get("input_tokens", 0)

                        elif event_type == "content_block_delta":
                            delta = data.get("delta") or {}
                            text = delta.get("text") or ""
                            if text:
                                yield StreamChunk(delta=text, is_final=False)

                        elif event_type == "message_delta":
                            usage = data.get("usage") or {}
                            output_tokens = usage.get("output_tokens", 0)

                        elif event_type == "message_stop":
                            yield StreamChunk(
                                delta="",
                                is_final=True,
                                input_tokens=input_tokens,
                                output_tokens=output_tokens,
                            )

    def _convert_messages(self, messages: list[dict]) -> tuple[str, list[dict]]:
        """Extract system prompt; convert tool messages to Anthropic format."""
        system_parts: list[str] = []
        result: list[dict] = []

        for msg in messages:
            role = msg["role"]
            if role == "system":
                system_parts.append(msg["content"])
            elif role == "tool":
                # OpenAI tool result → Anthropic tool_result content block
                result.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.get("tool_call_id", ""),
                        "content": msg["content"],
                    }],
                })
            elif role == "assistant" and msg.get("tool_calls"):
                # OpenAI assistant tool_calls → Anthropic tool_use content blocks
                content_blocks = []
                if msg.get("content"):
                    content_blocks.append({"type": "text", "text": msg["content"]})
                for tc in msg["tool_calls"]:
                    content_blocks.append({
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["function"]["name"],
                        "input": json.loads(tc["function"]["arguments"]),
                    })
                result.append({"role": "assistant", "content": content_blocks})
            else:
                result.append({"role": role, "content": msg["content"]})

        return "\n\n".join(system_parts), result

    def _convert_tools(self, tools: list[dict]) -> list[dict]:
        """Convert OpenAI tool format to Anthropic format."""
        anthropic_tools = []
        for t in tools:
            fn = t.get("function", t)
            anthropic_tools.append({
                "name": fn["name"],
                "description": fn.get("description", ""),
                "input_schema": fn.get("parameters", {"type": "object", "properties": {}}),
            })
        return anthropic_tools

    def _parse_response(self, data: dict) -> LLMResponse:
        content_text: list[str] = []
        tool_calls: list[ToolCallResult] = []

        for block in data.get("content", []):
            if block["type"] == "text":
                content_text.append(block["text"])
            elif block["type"] == "tool_use":
                tool_calls.append(ToolCallResult(
                    id=block["id"],
                    name=block["name"],
                    arguments=block.get("input", {}),
                ))

        usage = data.get("usage", {})
        stop_reason = data.get("stop_reason", "end_turn")
        finish_reason = "tool_calls" if tool_calls else ("stop" if stop_reason == "end_turn" else stop_reason)

        return LLMResponse(
            content="\n".join(content_text) or None,
            tool_calls=tool_calls,
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            model_id=data.get("model", self._model_id),
            finish_reason=finish_reason,
        )
