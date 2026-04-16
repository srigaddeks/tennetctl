from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .azure_provider import AzureOpenAIProvider
from .openai_provider import OpenAIProvider
from .provider import LLMProvider


def get_provider(
    *,
    provider_type: str,
    provider_base_url: str | None,
    api_key: str | None,
    model_id: str,
    temperature: float = 0.7,
    api_version: str = "2024-02-01",
) -> LLMProvider:
    """
    Return the correct LLMProvider implementation based on provider_type.

    provider_type values:
      "anthropic"        → AnthropicProvider  (Anthropic Messages API)
      "azure_openai"     → AzureOpenAIProvider (Azure deployment URL + api-version)
      "openai"           → OpenAIProvider      (api.openai.com)
      "openai_compatible"→ OpenAIProvider      (any OpenAI-compatible endpoint)
    """
    match provider_type:
        case "anthropic":
            return AnthropicProvider(
                provider_base_url=provider_base_url,
                api_key=api_key,
                model_id=model_id,
                temperature=temperature,
            )
        case "azure_openai":
            if not provider_base_url:
                raise ValueError("provider_base_url is required for azure_openai provider")
            return AzureOpenAIProvider(
                provider_base_url=provider_base_url,
                api_key=api_key,
                model_id=model_id,
                temperature=temperature,
                api_version=api_version,
            )
        case _:
            # "openai" and "openai_compatible" both use OpenAIProvider
            if not provider_base_url:
                raise ValueError("provider_base_url is required for openai/openai_compatible provider")
            return OpenAIProvider(
                provider_base_url=provider_base_url,
                api_key=api_key,
                model_id=model_id,
                temperature=temperature,
            )
