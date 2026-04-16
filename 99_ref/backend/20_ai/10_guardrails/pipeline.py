from __future__ import annotations

"""
GuardrailPipeline — ordered filter chain.

Input:   User input → [PII filter] → [Injection filter] → LLM
Output:  LLM output → [Content filter] → [Output filter] → Response

Each filter can: pass, redact (modify content and continue), block (raise GuardrailBlockedError), or warn (log and continue).
"""

import uuid
import datetime
from dataclasses import dataclass, field
from importlib import import_module

from .filters.base import FilterResult
from .filters.pii_filter import PIIFilter
from .filters.injection_filter import InjectionFilter
from .filters.content_filter import ContentFilter
from .filters.output_filter import OutputFilter

_logging_module = import_module("backend.01_core.logging_utils")
_errors_module = import_module("backend.01_core.errors")

get_logger = _logging_module.get_logger
_logger = get_logger("backend.ai.guardrails.pipeline")


class GuardrailBlockedError(Exception):
    def __init__(self, message: str, filter_name: str, matched_patterns: list[str]) -> None:
        super().__init__(message)
        self.filter_name = filter_name
        self.matched_patterns = matched_patterns


@dataclass
class PipelineResult:
    content: str
    blocked: bool = False
    block_reason: str | None = None
    filter_results: list[FilterResult] = field(default_factory=list)


_INPUT_FILTERS = [PIIFilter(), InjectionFilter()]
_OUTPUT_FILTERS = [ContentFilter(), OutputFilter()]


class GuardrailPipeline:
    """Applies the full filter chain around LLM I/O."""

    def __init__(self, *, repository, database_pool, settings) -> None:
        self._repo = repository
        self._pool = database_pool
        self._settings = settings
        self._logger = get_logger("backend.ai.guardrails")

    async def _get_configs(
        self,
        *,
        tenant_key: str,
        org_id: str | None,
    ) -> dict[str, dict]:
        """Load per-org guardrail configs. Falls back to empty config (uses filter defaults)."""
        try:
            async with self._pool.acquire() as conn:
                configs = await self._repo.get_org_configs(conn, tenant_key=tenant_key, org_id=org_id)
            return {c.guardrail_type_code: c.config_json for c in configs}
        except Exception:
            self._logger.warning("Failed to load guardrail configs, using defaults")
            return {}

    async def _log_event(
        self,
        *,
        conn,
        user_id: str,
        tenant_key: str,
        agent_run_id: str | None,
        result: FilterResult,
        direction: str,
    ) -> None:
        await self._repo.log_event(
            conn,
            id=str(uuid.uuid4()),
            agent_run_id=agent_run_id,
            user_id=user_id,
            tenant_key=tenant_key,
            guardrail_type_code=result.filter_name,
            direction=direction,
            action_taken=result.action,
            matched_pattern=", ".join(result.matched_patterns[:3]) if result.matched_patterns else None,
            severity=result.severity,
            original_content=result.original_content[:500] if result.original_content else None,
            sanitized_content=result.sanitized_content[:500] if result.sanitized_content else None,
        )

    async def filter_input(
        self,
        content: str,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        agent_run_id: str | None = None,
    ) -> PipelineResult:
        """Apply input filters before sending to LLM."""
        configs = await self._get_configs(tenant_key=tenant_key, org_id=org_id)
        current = content
        results: list[FilterResult] = []

        async with self._pool.acquire() as conn:
            for f in _INPUT_FILTERS:
                cfg = configs.get(f.guardrail_type_code, {})
                if cfg.get("disabled", False):
                    continue
                result = await f.apply(current, config=cfg)
                result.filter_name = f.filter_name
                results.append(result)

                if result.action in ("redact", "warn"):
                    await self._log_event(conn=conn, user_id=user_id, tenant_key=tenant_key,
                                          agent_run_id=agent_run_id, result=result, direction="input")
                    current = result.sanitized_content

                if not result.allowed:
                    await self._log_event(conn=conn, user_id=user_id, tenant_key=tenant_key,
                                          agent_run_id=agent_run_id, result=result, direction="input")
                    return PipelineResult(
                        content="",
                        blocked=True,
                        block_reason=f"Input blocked by {result.filter_name}: {', '.join(result.matched_patterns)}",
                        filter_results=results,
                    )

        return PipelineResult(content=current, blocked=False, filter_results=results)

    async def filter_output(
        self,
        content: str,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        agent_run_id: str | None = None,
    ) -> PipelineResult:
        """Apply output filters after LLM response."""
        configs = await self._get_configs(tenant_key=tenant_key, org_id=org_id)
        current = content
        results: list[FilterResult] = []

        async with self._pool.acquire() as conn:
            for f in _OUTPUT_FILTERS:
                cfg = configs.get(f.guardrail_type_code, {})
                if cfg.get("disabled", False):
                    continue
                result = await f.apply(current, config=cfg)
                result.filter_name = f.filter_name
                results.append(result)

                if result.action in ("redact", "warn"):
                    await self._log_event(conn=conn, user_id=user_id, tenant_key=tenant_key,
                                          agent_run_id=agent_run_id, result=result, direction="output")
                    current = result.sanitized_content

                if not result.allowed:
                    await self._log_event(conn=conn, user_id=user_id, tenant_key=tenant_key,
                                          agent_run_id=agent_run_id, result=result, direction="output")
                    return PipelineResult(
                        content="[Response blocked by content policy]",
                        blocked=True,
                        block_reason=f"Output blocked by {result.filter_name}",
                        filter_results=results,
                    )

        return PipelineResult(content=current, blocked=False, filter_results=results)
