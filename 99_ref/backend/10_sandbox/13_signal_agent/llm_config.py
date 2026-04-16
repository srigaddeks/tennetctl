from __future__ import annotations

from importlib import import_module

_errors_module = import_module("backend.01_core.errors")
_models_module = import_module("backend.20_ai.12_agent_config.models")

ValidationError = _errors_module.ValidationError
ResolvedLLMConfig = _models_module.ResolvedLLMConfig


def get_effective_signal_generation_llm_config(*, llm_config, settings) -> ResolvedLLMConfig:
    """
    Resolve the effective LLM config for quick signal generation.

    Precedence:
    1. Sandbox-specific env override (`SANDBOX_AI_*`) when provider + API key are set
    2. Resolved agent config / platform AI config (`signal_generate` → `AI_*`)
    """
    sandbox_provider_url = getattr(settings, "sandbox_ai_provider_url", None)
    sandbox_api_key = getattr(settings, "sandbox_ai_api_key", None)
    sandbox_model = getattr(settings, "sandbox_ai_model", None)

    if sandbox_provider_url and sandbox_api_key:
        return ResolvedLLMConfig(
            agent_type_code=getattr(llm_config, "agent_type_code", "signal_generate"),
            provider_type=getattr(llm_config, "provider_type", None)
            or getattr(settings, "ai_provider_type", "openai_compatible"),
            provider_base_url=sandbox_provider_url,
            api_key=sandbox_api_key,
            model_id=sandbox_model
            or getattr(llm_config, "model_id", None)
            or getattr(settings, "ai_model", "gpt-4o"),
            temperature=float(
                getattr(llm_config, "temperature", getattr(settings, "ai_temperature", 0.2))
            ),
            max_tokens=int(
                getattr(llm_config, "max_tokens", getattr(settings, "ai_max_tokens", 4096))
            ),
            is_global=bool(getattr(llm_config, "is_global", True)),
        )

    if getattr(llm_config, "provider_base_url", None) and getattr(llm_config, "api_key", None):
        return llm_config

    raise ValidationError(
        "AI signal generation is not configured. Configure SANDBOX_AI_PROVIDER_URL + "
        "SANDBOX_AI_API_KEY, AI_PROVIDER_URL + AI_API_KEY, or a signal_generate agent config."
    )
