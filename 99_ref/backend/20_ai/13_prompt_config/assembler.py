from __future__ import annotations

"""
PromptAssembler — 3-level prompt chain composition.

Layer order:
  1. Agent base prompt   (scope=agent, agent_type_code)
  2. Feature guardrail   (scope=feature, feature_code)
  3. Org overlay         (scope=org, org_id)

Each layer is separated by a clear delimiter so the LLM sees them as
distinct instructions. Layers that have no configured template are silently
skipped — the system works with any combination.
"""

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger
_logger = get_logger("backend.ai.prompt_config.assembler")

_LAYER_SEPARATOR = "\n\n---\n\n"


class PromptAssembler:
    """Composes the 3-level system prompt chain from DB templates."""

    def __init__(self, *, repository, database_pool) -> None:
        self._repo = repository
        self._pool = database_pool

    async def compose(
        self,
        *,
        agent_type_code: str,
        feature_code: str | None = None,
        org_id: str | None = None,
    ) -> tuple[str, list[dict]]:
        """
        Returns:
            (composed_prompt: str, layers: list[dict])
            layers contains debug info for each layer: scope, template_id, prompt_text
        """
        layers: list[dict] = []
        parts: list[str] = []

        async with self._pool.acquire() as conn:
            # Layer 1: Agent base
            agent_tmpl = await self._repo.get_agent_prompt(conn, agent_type_code=agent_type_code)
            if agent_tmpl:
                parts.append(agent_tmpl.prompt_text.strip())
                layers.append({"scope": "agent", "template_id": agent_tmpl.id, "prompt_text": agent_tmpl.prompt_text})
            else:
                _logger.debug("No agent base prompt for %s", agent_type_code)

            # Layer 2: Feature guardrail
            if feature_code:
                feature_tmpl = await self._repo.get_feature_prompt(
                    conn, feature_code=feature_code, agent_type_code=agent_type_code
                )
                if feature_tmpl:
                    parts.append(feature_tmpl.prompt_text.strip())
                    layers.append({"scope": "feature", "template_id": feature_tmpl.id, "prompt_text": feature_tmpl.prompt_text})

            # Layer 3: Org overlay
            if org_id:
                org_tmpl = await self._repo.get_org_prompt(
                    conn, org_id=org_id, agent_type_code=agent_type_code
                )
                if org_tmpl:
                    parts.append(org_tmpl.prompt_text.strip())
                    layers.append({"scope": "org", "template_id": org_tmpl.id, "prompt_text": org_tmpl.prompt_text})

        composed = _LAYER_SEPARATOR.join(parts)
        return composed, layers
