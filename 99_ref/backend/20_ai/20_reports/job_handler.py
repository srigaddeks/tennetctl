"""
Job handler for generate_report jobs.

Called by job_processor.dispatch() → runs the full report generation pipeline.
"""

from __future__ import annotations

import time
from importlib import import_module

import asyncpg

from .agent import ReportGenerationAgent
from .models import ReportGenState
from .repository import ReportRepository

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.reports.job_handler")

_JOBS = '"20_ai"."45_fct_job_queue"'


async def handle_generate_report_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Entry point called by the job queue worker for job_type='generate_report'.

    job.input_json must contain:
      - report_id: str
      - report_type: str
      - org_id: str
      - workspace_id: str | None
      - user_id: str
      - tenant_key: str
      - parameters: dict
    """
    inp = job.input_json
    report_id = inp["report_id"]
    report_type = inp["report_type"]
    org_id = inp["org_id"]
    workspace_id = inp.get("workspace_id")
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    parameters = inp.get("parameters", {})

    _logger.info(
        "report_job.start",
        extra={"job_id": job.id, "report_id": report_id, "report_type": report_type},
    )

    # Resolve LLM config
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    config_repo = _repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(
        agent_type_code="report_generator",
        org_id=org_id,
    )

    state = ReportGenState(
        report_id=report_id,
        job_id=job.id,
        report_type=report_type,
        org_id=org_id,
        workspace_id=workspace_id,
        parameters=parameters,
        user_id=user_id,
        tenant_key=tenant_key,
    )

    agent = ReportGenerationAgent(config=llm_config, settings=settings, pool=pool)
    await agent.run(state)

    _logger.info(
        "report_job.done",
        extra={
            "job_id": job.id,
            "report_id": report_id,
            "status": state.status,
            "tokens": state.tokens_consumed,
        },
    )
