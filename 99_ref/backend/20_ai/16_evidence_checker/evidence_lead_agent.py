"""
EvidenceLeadAgent — orchestrates evidence evaluation for all acceptance criteria
of a single task.

Responsibilities:
  1. Load acceptance criteria from DB
  2. Load system prompt from DB via PromptAssembler (scope=agent, agent_type_code='evidence_lead')
  3. Resolve LLM config for evidence_checker_agent (org → global → settings)
  4. Build EvidenceCheckerAgent and fan out per-criterion evaluations
     (bounded concurrency via EVIDENCE_CHECKER_CRITERION_CONCURRENCY env var)
  5. Compute overall verdict
  6. Return EvidenceReport

Progress callbacks fire after each criterion completes so the job handler can
update DB + emit SSE events without waiting for the full batch.
"""

from __future__ import annotations

import asyncio
import os
import time
import uuid
from importlib import import_module
from typing import Callable

import asyncpg

from .evidence_checker_agent import EvidenceCheckerAgent, _EVIDENCE_CHECKER_SYSTEM_FALLBACK
from .models import Criterion, EvidenceReport

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.evidence_checker.lead")

_CRITERION_CONCURRENCY = int(os.getenv("EVIDENCE_CHECKER_CRITERION_CONCURRENCY", "5"))

_EVIDENCE_LEAD_SYSTEM_FALLBACK = """\
You are the Evidence Lead AI. You orchestrate evidence evaluation across all acceptance criteria.
"""

# ── Verdict roll-up ──────────────────────────────────────────────────────────

_VERDICT_RANK = {
    "NOT_MET": 0,
    "INSUFFICIENT_EVIDENCE": 1,
    "PARTIALLY_MET": 2,
    "MET": 3,
}


def _overall_verdict(results) -> str:
    if not results:
        return "INCONCLUSIVE"
    verdicts = [r.verdict for r in results]
    if all(v == "MET" for v in verdicts):
        return "ALL_MET"
    if all(v in ("NOT_MET", "INSUFFICIENT_EVIDENCE") for v in verdicts):
        return "NOT_MET"
    if any(v == "INSUFFICIENT_EVIDENCE" for v in verdicts) and not any(v in ("MET", "PARTIALLY_MET") for v in verdicts):
        return "INCONCLUSIVE"
    return "PARTIALLY_MET"


# ── Criteria loader ──────────────────────────────────────────────────────────

async def _load_criteria(pool: asyncpg.Pool, task_id: str) -> list[Criterion]:
    """
    Load the task's acceptance criteria.

    Priority:
    1. Structured rows in "08_tasks"."12_fct_task_criteria" (future)
    2. EAV property `acceptance_criteria` in "08_tasks"."20_dtl_task_properties"
       — stored as newline-delimited text; each non-empty line is one criterion.
    """
    try:
        async with pool.acquire() as conn:
            # Try structured criteria table first
            rows = await conn.fetch(
                """
                SELECT id::text, criterion_text, threshold
                FROM "08_tasks"."12_fct_task_criteria"
                WHERE task_id = $1::uuid
                  AND is_deleted = FALSE
                ORDER BY sort_order, created_at
                """,
                task_id,
            )
            if rows:
                return [
                    Criterion(
                        id=str(r["id"]),
                        text=r["criterion_text"],
                        threshold=r.get("threshold"),
                    )
                    for r in rows
                ]

            # Fallback: EAV property acceptance_criteria (newline-delimited)
            row = await conn.fetchrow(
                """
                SELECT property_value
                FROM "08_tasks"."20_dtl_task_properties"
                WHERE task_id = $1::uuid AND property_key = 'acceptance_criteria'
                """,
                task_id,
            )
            if not row or not row["property_value"]:
                return []

            lines = [line.strip() for line in row["property_value"].splitlines() if line.strip()]
            import uuid as _uuid
            return [
                Criterion(id=str(_uuid.uuid5(_uuid.NAMESPACE_URL, f"{task_id}::{i}")), text=line, threshold=None)
                for i, line in enumerate(lines)
            ]
    except Exception as exc:
        _logger.warning("Could not load criteria for task %s: %s", task_id, exc)
        return []


# ── Attachment list loader ───────────────────────────────────────────────────

async def _load_attachment_count(pool: asyncpg.Pool, task_id: str) -> int:
    try:
        async with pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT COUNT(*) AS cnt
                FROM "09_attachments"."01_fct_attachments"
                WHERE entity_type = 'task' AND entity_id = $1::uuid AND is_deleted = FALSE
                """,
                task_id,
            )
            return int(row["cnt"]) if row else 0
    except Exception:
        return 0


# ── Config + prompt resolution ───────────────────────────────────────────────

async def _resolve_checker_config(pool: asyncpg.Pool, org_id: str, settings):
    """
    Resolve LLM config for evidence_checker_agent using existing AgentConfigRepository.
    Falls back to settings-level env vars if no DB config.
    """
    _agent_config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    _agent_config_crypto_mod = import_module("backend.20_ai.12_agent_config.crypto")
    _llm_factory_mod = import_module("backend.20_ai.14_llm_providers.factory")
    AgentConfigRepository = _agent_config_repo_mod.AgentConfigRepository
    decrypt_value = _agent_config_crypto_mod.decrypt_value
    parse_encryption_key = _agent_config_crypto_mod.parse_encryption_key
    get_provider = _llm_factory_mod.get_provider

    repo = AgentConfigRepository()
    async with pool.acquire() as conn:
        config = await repo.get_org_config(conn, agent_type_code="evidence_checker_agent", org_id=org_id)
        if not config:
            config = await repo.get_global_config(conn, agent_type_code="evidence_checker_agent")

    if config:
        api_key: str | None = None
        async with pool.acquire() as conn:
            enc_key_str = await repo.get_encrypted_api_key(conn, config_id=config.id)
        if enc_key_str:
            try:
                enc_key_bytes = parse_encryption_key(settings.ai_encryption_key)
                api_key = decrypt_value(enc_key_str, enc_key_bytes)
            except Exception:
                pass
        provider = get_provider(
            provider_type=config.provider_type,
            provider_base_url=config.provider_base_url,
            api_key=api_key,
            model_id=config.model_id,
            temperature=1.0,
        )
        return provider

    # Fallback to grc_assistant config (same provider, different model is fine)
    async with pool.acquire() as conn:
        fallback = await repo.get_global_config(conn, agent_type_code="grc_assistant")
    if fallback:
        api_key = None
        async with pool.acquire() as conn:
            enc_key_str = await repo.get_encrypted_api_key(conn, config_id=fallback.id)
        if enc_key_str:
            try:
                enc_key_bytes = parse_encryption_key(settings.ai_encryption_key)
                api_key = decrypt_value(enc_key_str, enc_key_bytes)
            except Exception:
                pass
        provider = get_provider(
            provider_type=fallback.provider_type,
            provider_base_url=fallback.provider_base_url,
            api_key=api_key,
            model_id=fallback.model_id,
            temperature=1.0,
        )
        return provider

    raise RuntimeError("No LLM config available for evidence_checker_agent — configure one via Agent Config admin")


async def _resolve_prompts(pool: asyncpg.Pool, org_id: str) -> tuple[str, str]:
    """
    Returns (lead_prompt, checker_prompt).
    Uses existing PromptAssembler for both agent types.
    Falls back to hardcoded defaults if DB has no templates.
    """
    try:
        _pt_repo_mod = import_module("backend.20_ai.13_prompt_config.repository")
        _assembler_mod = import_module("backend.20_ai.13_prompt_config.assembler")
        PromptTemplateRepository = _pt_repo_mod.PromptTemplateRepository
        PromptAssembler = _assembler_mod.PromptAssembler

        repo = PromptTemplateRepository()
        assembler = PromptAssembler(repository=repo, database_pool=pool)

        lead_prompt, _ = await assembler.compose(
            agent_type_code="evidence_lead",
            feature_code="ai_evidence_checker",
            org_id=org_id,
        )
        checker_prompt, _ = await assembler.compose(
            agent_type_code="evidence_checker_agent",
            feature_code="ai_evidence_checker",
            org_id=org_id,
        )
        return (
            lead_prompt or _EVIDENCE_LEAD_SYSTEM_FALLBACK,
            checker_prompt or _EVIDENCE_CHECKER_SYSTEM_FALLBACK,
        )
    except Exception as exc:
        _logger.warning("Prompt assembly failed (using defaults): %s", exc)
        return _EVIDENCE_LEAD_SYSTEM_FALLBACK, _EVIDENCE_CHECKER_SYSTEM_FALLBACK


# ── LangFuse init ────────────────────────────────────────────────────────────

def _init_langfuse(settings):
    if not getattr(settings, "ai_langfuse_enabled", False):
        return None
    try:
        from langfuse import Langfuse
        return Langfuse(
            public_key=settings.ai_langfuse_public_key,
            secret_key=settings.ai_langfuse_secret_key,
            host=settings.ai_langfuse_host or "https://cloud.langfuse.com",
        )
    except Exception as exc:
        _logger.warning("LangFuse init failed (non-fatal): %s", exc)
        return None


# ── Main orchestrator ────────────────────────────────────────────────────────

class EvidenceLeadAgent:
    """
    Orchestrates the full evidence evaluation for one task.

    Usage:
        lead = EvidenceLeadAgent(pool=pool, settings=settings, qdrant_client=qdrant)
        report = await lead.run(
            task_id=..., org_id=..., job_id=...,
            attachment_ids=[...],
            on_criterion_done=callback,
        )
    """

    def __init__(
        self,
        *,
        pool: asyncpg.Pool,
        settings,
        qdrant_client,
    ) -> None:
        self._pool = pool
        self._settings = settings
        self._qdrant = qdrant_client

    async def run(
        self,
        *,
        task_id: str,
        org_id: str,
        job_id: str,
        attachment_ids: list[str],
        on_criterion_done: Callable | None = None,
    ) -> EvidenceReport:
        t0 = time.monotonic()
        trace_id = str(uuid.uuid4())

        # 1. Resolve everything from DB
        criteria = await _load_criteria(self._pool, task_id)
        attachment_count = await _load_attachment_count(self._pool, task_id)
        lead_prompt, checker_prompt = await _resolve_prompts(self._pool, org_id)
        provider = await _resolve_checker_config(self._pool, org_id, self._settings)
        lf = _init_langfuse(self._settings)

        if not criteria:
            _logger.info("No criteria found for task %s — skipping evaluation", task_id)
            return EvidenceReport(
                job_id=job_id,
                task_id=task_id,
                overall_verdict="INCONCLUSIVE",
                attachment_count=attachment_count,
                total_pages_analyzed=0,
                tokens_consumed=0,
                duration_seconds=round(time.monotonic() - t0, 2),
                langfuse_trace_id=None,
            )

        # 2. LangFuse trace for this run
        lf_trace = None
        if lf:
            try:
                lf_trace = lf.trace(
                    id=trace_id,
                    name=f"evidence_lead/{task_id}",
                    metadata={"job_id": job_id, "task_id": task_id, "org_id": org_id},
                )
            except Exception:
                pass

        # 3. Build EvidenceCheckerAgent (shared, stateless)
        checker = EvidenceCheckerAgent(
            pool=self._pool,
            provider=provider,
            system_prompt=checker_prompt,
            qdrant_client=self._qdrant,
            langfuse_client=lf,
            settings=self._settings,
        )

        _logger.info(
            "evidence_check.lead_started",
            extra={
                "job_id": job_id, "task_id": task_id, "org_id": org_id,
                "criteria_count": len(criteria), "attachment_count": attachment_count,
            },
        )

        # 4. Fan out criterion evaluations with bounded concurrency
        semaphore = asyncio.Semaphore(_CRITERION_CONCURRENCY)
        results = []

        async def _run_one(criterion: Criterion) -> None:
            async with semaphore:
                result = await checker.evaluate_criterion(
                    task_id=task_id,
                    org_id=org_id,
                    criterion_id=criterion.id,
                    criterion_text=criterion.text,
                    threshold=criterion.threshold,
                    parent_trace_id=trace_id,
                )
                results.append(result)
                if on_criterion_done:
                    try:
                        await on_criterion_done(result, len(results), len(criteria))
                    except Exception as cb_exc:
                        _logger.warning("on_criterion_done callback failed: %s", cb_exc)

        await asyncio.gather(*[_run_one(c) for c in criteria])

        # 5. Compute overall verdict and token total
        overall = _overall_verdict(results)
        total_tokens = 0  # individual token counts not surfaced here; tracked at job level

        elapsed = round(time.monotonic() - t0, 2)

        if lf:
            try:
                asyncio.create_task(asyncio.to_thread(lf.flush))
            except Exception:
                pass

        _logger.info(
            "evidence_check.lead_done",
            extra={
                "job_id": job_id, "task_id": task_id, "overall_verdict": overall,
                "elapsed_s": elapsed, "criteria_count": len(criteria),
            },
        )

        return EvidenceReport(
            job_id=job_id,
            task_id=task_id,
            overall_verdict=overall,
            attachment_count=attachment_count,
            total_pages_analyzed=0,  # filled in by job handler from ingestion results
            tokens_consumed=total_tokens,
            duration_seconds=elapsed,
            langfuse_trace_id=trace_id,
            criteria_results=results,
        )
