from __future__ import annotations

from importlib import import_module

from .models import ResolvedLLMConfig

_logging_module = import_module("backend.01_core.logging_utils")
_settings_module = import_module("backend.00_config.settings")

get_logger = _logging_module.get_logger
_logger = get_logger("backend.ai.agent_config.resolver")


class AgentConfigResolver:
    """
    Resolves LLM config for a given agent type and org.
    Resolution order: org override → global config → settings fallback.
    """

    def __init__(self, *, repository, database_pool, settings) -> None:
        self._repo = repository
        self._pool = database_pool
        self._settings = settings

    async def resolve(
        self,
        *,
        agent_type_code: str,
        org_id: str | None = None,
    ) -> ResolvedLLMConfig:
        from .crypto import decrypt_value, parse_encryption_key

        async with self._pool.acquire() as conn:
            # 1. Try org-specific override
            record = None
            if org_id:
                record = await self._repo.get_org_config(conn, agent_type_code=agent_type_code, org_id=org_id)

            is_global = record is None

            # 2. Fall back to global config
            if record is None:
                record = await self._repo.get_global_config(conn, agent_type_code=agent_type_code)

            # 3. Resolve API key
            api_key: str | None = None
            if record is not None:
                raw_key = await self._repo.get_encrypted_api_key(conn, config_id=record.id)
                if raw_key and self._settings.ai_encryption_key:
                    try:
                        enc_key = parse_encryption_key(self._settings.ai_encryption_key)
                        api_key = decrypt_value(raw_key, enc_key)
                    except Exception:
                        _logger.warning("Failed to decrypt API key for agent config %s", record.id)

        # 4. Settings fallback if no DB config
        if record is None:
            return ResolvedLLMConfig(
                agent_type_code=agent_type_code,
                provider_type=self._settings.ai_provider_type,
                provider_base_url=self._settings.ai_provider_url,
                api_key=self._settings.ai_api_key,
                model_id=self._settings.ai_model,
                temperature=getattr(self._settings, "ai_temperature", 1.0),
                max_tokens=self._settings.ai_max_tokens,
                is_global=True,
            )

        return ResolvedLLMConfig(
            agent_type_code=agent_type_code,
            provider_type=record.provider_type or self._settings.ai_provider_type,
            provider_base_url=record.provider_base_url or self._settings.ai_provider_url,
            api_key=api_key or self._settings.ai_api_key,
            model_id=record.model_id,
            temperature=float(record.temperature),
            max_tokens=record.max_tokens,
            is_global=is_global,
        )
