from __future__ import annotations

import json
from importlib import import_module
from typing import AsyncIterator

import httpx

from .provider import LLMResponse, StreamChunk, ToolCallResult

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.providers.azure")

_DEFAULT_API_VERSION = "2024-02-01"


class AzureOpenAIProvider:
    """
    Provider for Azure OpenAI.

    Differences from OpenAI:
    - URL shape: {base_url}/openai/deployments/{deployment}/chat/completions?api-version=...
    - Auth header: 'api-key' instead of 'Authorization: Bearer'
    - model_id maps to the Azure deployment name

    provider_base_url should be the Azure resource URL, e.g.:
        https://my-resource.openai.azure.com
    """

    def __init__(
        self,
        *,
        provider_base_url: str,
        api_key: str | None,
        model_id: str,
        temperature: float = 0.7,
        api_version: str = _DEFAULT_API_VERSION,
    ) -> None:
        self._base_url = provider_base_url.rstrip("/")
        self._api_key = api_key or ""
        self._deployment = model_id  # Azure uses deployment name as model
        self._api_version = api_version
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
        url = (
            f"{self._base_url}/openai/deployments/{self._deployment}"
            f"/chat/completions?api-version={self._api_version}"
        )

        payload: dict = {
            "messages": messages,
            "temperature": target_temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
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
        """Stream tokens from Azure OpenAI.

        Same SSE format as OpenAI, but with Azure URL + api-key auth.
        """
        target_temperature = temperature if temperature is not None else self._temperature
        url = (
            f"{self._base_url}/openai/deployments/{self._deployment}"
            f"/chat/completions?api-version={self._api_version}"
        )

        payload: dict = {
            "messages": messages,
            "temperature": target_temperature,
            "max_tokens": max_tokens,
            "stream": True,
            "stream_options": {"include_usage": True},
        }

        headers = {
            "api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            async with client.stream(
                "POST", url, headers=headers, json=payload
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
                    is_final = finish_reason is not None

                    if delta_content or is_final:
                        yield StreamChunk(
                            delta=delta_content,
                            is_final=is_final,
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                        )

    def _parse_response(self, data: dict) -> LLMResponse:
        choice = data["choices"][0]
        message = choice["message"]
        usage = data.get("usage", {})

        content = message.get("content")
        finish_reason = choice.get("finish_reason", "stop")

        tool_calls: list[ToolCallResult] = []
        for tc in message.get("tool_calls") or []:
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
            model_id=self._deployment,
            finish_reason=finish_reason,
        )
