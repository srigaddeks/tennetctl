from __future__ import annotations

import json
from importlib import import_module
from typing import AsyncIterator

import httpx

from .provider import LLMProvider, LLMResponse, StreamChunk, ToolCallResult

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.providers.openai")

_VALID_PROVIDER_TYPES = ("openai", "openai_compatible")


class OpenAIProvider:
    """
    Provider for OpenAI API and any OpenAI-compatible endpoint.

    Compatible with:
      - OpenAI (api.openai.com)
      - Custom endpoints (https://llm.kreesalis.com/v1, Ollama, Together, Groq, etc.)
      - Azure OpenAI is handled by AzureOpenAIProvider instead

    The /chat/completions endpoint is used. The provider URL should end with /v1
    or whatever prefix the endpoint uses (e.g. https://llm.kreesalis.com/v1).
    """

    def __init__(self, *, provider_base_url: str, api_key: str | None, model_id: str, temperature: float = 0.7) -> None:
        self._base_url = provider_base_url.rstrip("/")
        self._api_key = api_key or ""
        self._model_id = model_id
        self._temperature = temperature

    async def chat_completion(
        self,
        *,
        messages: list[dict],
        tools: list[dict] | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResponse:
        payload: dict = {
            "model": self._model_id,
            "messages": messages,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if tools:
            payload["tools"] = tools

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as exc:
                _logger.error(
                    "LLM HTTP error %s: %s",
                    resp.status_code,
                    resp.text[:500],
                )
                raise exc
            data = resp.json()

        return self._parse_response(data)

    def _parse_response(self, data: dict) -> LLMResponse:
        choice = data["choices"][0]
        message = choice["message"]
        usage = data.get("usage", {})

        content = message.get("content")
        finish_reason = choice.get("finish_reason", "stop")

        tool_calls: list[ToolCallResult] = []
        raw_tool_calls = message.get("tool_calls") or []
        for tc in raw_tool_calls:
            try:
                args = json.loads(tc["function"]["arguments"])
            except (json.JSONDecodeError, KeyError):
                args = {}
            tool_calls.append(ToolCallResult(
                id=tc.get("id", ""),
                name=tc["function"]["name"],
                arguments=args,
            ))

        return LLMResponse(
            content=content,
            tool_calls=tool_calls,
            input_tokens=usage.get("prompt_tokens", 0),
            output_tokens=usage.get("completion_tokens", 0),
            model_id=data.get("model", self._model_id),
            finish_reason=finish_reason,
        )

    async def stream_chat_completion(
        self,
        *,
        messages: list[dict],
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncIterator[StreamChunk]:
        """Stream tokens from the OpenAI /chat/completions endpoint.

        Uses SSE with stream=true. Yields StreamChunk deltas; the final chunk
        carries usage stats and is_final=True.
        """
        payload: dict = {
            "model": self._model_id,
            "messages": messages,
            "stream": True,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                headers=headers,
                json=payload,
            ) as resp:
                resp.raise_for_status()
                input_tokens = 0
                output_tokens = 0
                async for raw_line in resp.aiter_lines():
                    if not raw_line.startswith("data:"):
                        continue
                    data_str = raw_line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                    except json.JSONDecodeError:
                        continue

                    usage = chunk.get("usage") or {}
                    if usage:
                        input_tokens = usage.get("prompt_tokens", 0)
                        output_tokens = usage.get("completion_tokens", 0)

                    choices = chunk.get("choices") or []
                    if not choices:
                        continue

                    delta_content = (choices[0].get("delta") or {}).get("content") or ""
                    finish_reason = choices[0].get("finish_reason")

                    if delta_content:
                        yield StreamChunk(delta=delta_content, is_final=False)

                # Always emit a final chunk to carry token counts
                yield StreamChunk(delta="", is_final=True, input_tokens=input_tokens, output_tokens=output_tokens)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Fetch embeddings for a list of texts."""
        payload = {
            "input": texts,
            "model": "text-embedding-3-small",  # Usually standard for openai compatibility
        }
        
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self._base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
            
        vectors = []
        for d in data.get("data", []):
            vectors.append(d["embedding"])
        return vectors
