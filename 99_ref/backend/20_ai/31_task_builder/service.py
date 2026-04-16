"""Service orchestration for AI-powered framework task generation.

Supports both:
  - Legacy direct endpoints (preview/apply) — synchronous, no sessions
  - Session-based async flow (create session → enqueue preview job → poll → review → enqueue apply job)
"""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from importlib import import_module
import asyncio
import re
import uuid

from pydantic import ValidationError

from .prompts import TASKS_PROMPT
from .repository import TaskBuilderRepository, TaskBuilderSessionRepository
from .schemas import (
    ApplyResponse,
    CreateTaskBuilderSessionRequest,
    GeneratedTask,
    PatchTaskBuilderSessionRequest,
    TaskBuilderJobStatusResponse,
    TaskBuilderSessionListResponse,
    TaskBuilderSessionResponse,
    TaskGroupResponse,
)


_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_llm_utils_mod = import_module("backend.20_ai._llm_utils")
_time_module = import_module("backend.01_core.time_utils")
_audit_module = import_module("backend.01_core.audit")
_task_repo_module = import_module("backend.07_tasks.02_tasks.repository")
_event_repo_module = import_module("backend.07_tasks.05_events.repository")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_task_constants_module = import_module("backend.07_tasks.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ServiceUnavailableError = _errors_module.ServiceUnavailableError
require_permission = _perm_check_module.require_permission
llm_complete = _llm_utils_mod.llm_complete
parse_json = _llm_utils_mod.parse_json
resolve_llm_config = _llm_utils_mod.resolve_llm_config
utc_now_sql = _time_module.utc_now_sql
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
TaskRepository = _task_repo_module.TaskRepository
EventRepository = _event_repo_module.EventRepository
AuditEventCategory = _auth_constants_module.AuditEventCategory
TaskAuditEventType = _task_constants_module.TaskAuditEventType
AppValidationError = _errors_module.ValidationError

_JOBS = '"20_ai"."45_fct_job_queue"'
_CONTROL_CHUNK_SIZE = 5
_DUE_DAY_CHOICES = (7, 14, 30, 60, 90)
_PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
_VALID_PRIORITIES = frozenset(_PRIORITY_ORDER)
_VALID_TASK_TYPES = frozenset({"evidence_collection", "control_remediation"})
_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "the",
        "to",
        "with",
    }
)


def _chunks(items: list[dict], size: int) -> list[list[dict]]:
    return [items[i : i + size] for i in range(0, len(items), size)]


def _clean_text(value: object, *, max_length: int | None = None) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if max_length is not None:
        return text[:max_length].strip()
    return text


def _normalize_priority(value: object) -> str:
    candidate = _clean_text(value).lower()
    return candidate if candidate in _VALID_PRIORITIES else "medium"


def _normalize_task_type(
    raw_task: dict, *, title: str, description: str, acceptance_criteria: str
) -> str:
    candidate = _clean_text(raw_task.get("task_type_code")).lower()
    if candidate in _VALID_TASK_TYPES:
        return candidate

    combined = " ".join(
        [
            title.lower(),
            description.lower(),
            acceptance_criteria.lower(),
            _clean_text(raw_task.get("remediation_plan")).lower(),
        ]
    )
    remediation_keywords = (
        "remedi",
        "fix",
        "patch",
        "implement",
        "enable",
        "configure",
        "close gap",
    )
    if any(keyword in combined for keyword in remediation_keywords):
        return "control_remediation"
    return "evidence_collection"


def _normalize_due_days(value: object) -> int:
    try:
        days = int(value)
    except (TypeError, ValueError):
        return 30
    if days <= 0:
        return 30
    return min(_DUE_DAY_CHOICES, key=lambda candidate: abs(candidate - days))


def _normalize_for_intent(value: str) -> str:
    lowered = value.lower()
    lowered = re.sub(r"[^a-z0-9\s]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _intent_token_set(
    task_type_code: str, title: str, acceptance_criteria: str
) -> set[str]:
    tokens = {
        token
        for token in _normalize_for_intent(
            f"{task_type_code} {title} {acceptance_criteria}"
        ).split()
        if len(token) > 1 and token not in _STOP_WORDS
    }
    return tokens


def _is_duplicate_task(candidate: GeneratedTask, existing: dict) -> bool:
    if existing.get("is_terminal") is True:
        return False
    if _clean_text(existing.get("task_type_code")).lower() != candidate.task_type_code:
        return False

    existing_title = _clean_text(existing.get("title"))
    existing_acceptance = _clean_text(existing.get("acceptance_criteria"))
    if not existing_title and not existing_acceptance:
        return False

    if _normalize_for_intent(existing_title) == _normalize_for_intent(candidate.title):
        return True
    existing_combined = _normalize_for_intent(f"{existing_title} {existing_acceptance}")
    candidate_combined = _normalize_for_intent(
        f"{candidate.title} {candidate.acceptance_criteria}"
    )
    if existing_combined == candidate_combined:
        return True

    existing_tokens = _intent_token_set(
        candidate.task_type_code, existing_title, existing_acceptance
    )
    candidate_tokens = _intent_token_set(
        candidate.task_type_code, candidate.title, candidate.acceptance_criteria
    )
    if not existing_tokens or not candidate_tokens:
        return False

    overlap = len(existing_tokens & candidate_tokens)
    if overlap == 0:
        return False

    containment = overlap / min(len(existing_tokens), len(candidate_tokens))
    jaccard = overlap / len(existing_tokens | candidate_tokens)
    return overlap >= 4 and (containment >= 0.85 or jaccard >= 0.75)


def _sort_tasks(tasks: list[GeneratedTask]) -> list[GeneratedTask]:
    return sorted(
        tasks,
        key=lambda task: (
            _PRIORITY_ORDER.get(task.priority_code, 99),
            task.due_days_from_now,
            task.title.lower(),
        ),
    )


def _session_response(row: dict) -> TaskBuilderSessionResponse:
    return TaskBuilderSessionResponse(
        id=row["id"],
        tenant_key=row["tenant_key"],
        user_id=row["user_id"],
        status=row["status"],
        framework_id=row["framework_id"],
        scope_org_id=row.get("scope_org_id"),
        scope_workspace_id=row.get("scope_workspace_id"),
        user_context=row.get("user_context") or "",
        attachment_ids=row.get("attachment_ids") or [],
        control_ids=row.get("control_ids"),
        proposed_tasks=row.get("proposed_tasks"),
        apply_result=row.get("apply_result"),
        job_id=row.get("job_id"),
        error_message=row.get("error_message"),
        activity_log=row.get("activity_log") or [],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@instrument_class_methods(
    namespace="ai.task_builder.service",
    logger_name="backend.ai.task_builder.instrumentation",
)
class TaskBuilderService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = TaskBuilderRepository()
        self._session_repository = TaskBuilderSessionRepository()
        self._task_repository = TaskRepository()
        self._event_repository = EventRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.ai.task_builder")

    # ── Session CRUD ──────────────────────────────────────────────────────────

    async def create_session(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: CreateTaskBuilderSessionRequest,
    ) -> TaskBuilderSessionResponse:
        if not request.scope_org_id or not request.scope_workspace_id:
            raise AppValidationError("scope_org_id and scope_workspace_id are required")

        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=request.scope_org_id,
                scope_workspace_id=request.scope_workspace_id,
            )
            framework = await self._repository.get_framework(
                conn,
                framework_id=request.framework_id,
                tenant_key=tenant_key,
            )
            if not framework:
                raise NotFoundError(f"Framework {request.framework_id} not found")

            row = await self._session_repository.create_session(
                conn,
                session_id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                user_id=user_id,
                framework_id=request.framework_id,
                scope_org_id=request.scope_org_id,
                scope_workspace_id=request.scope_workspace_id,
                user_context=request.user_context or "",
                attachment_ids=request.attachment_ids or [],
                control_ids=request.control_ids,
                now=now,
            )
        return _session_response(row)

    async def get_session(
        self, *, user_id: str, tenant_key: str, session_id: str
    ) -> TaskBuilderSessionResponse:
        async with self._database_pool.acquire() as conn:
            row = await self._session_repository.get_by_id(conn, session_id, tenant_key)
            if not row or row.get("user_id") != user_id:
                raise NotFoundError(f"Task builder session '{session_id}' not found")
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=row.get("scope_org_id"),
                scope_workspace_id=row.get("scope_workspace_id"),
            )
        return _session_response(row)

    async def list_sessions(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> TaskBuilderSessionListResponse:
        if not scope_org_id or not scope_workspace_id:
            raise AppValidationError("scope_org_id and scope_workspace_id are required")
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn, user_id, "frameworks.view",
                scope_org_id=scope_org_id, scope_workspace_id=scope_workspace_id,
            )
            rows, total = await self._session_repository.list_sessions(
                conn,
                tenant_key=tenant_key,
                user_id=user_id,
                framework_id=framework_id,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
                limit=limit,
                offset=offset,
            )
        return TaskBuilderSessionListResponse(items=[_session_response(r) for r in rows], total=total)

    async def patch_session(
        self, *, user_id: str, tenant_key: str, session_id: str, request: PatchTaskBuilderSessionRequest
    ) -> TaskBuilderSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            existing = await self._session_repository.get_by_id(conn, session_id, tenant_key)
            if not existing or existing.get("user_id") != user_id:
                raise NotFoundError(f"Task builder session '{session_id}' not found")
            await require_permission(
                conn, user_id, "frameworks.view",
                scope_org_id=existing.get("scope_org_id"),
                scope_workspace_id=existing.get("scope_workspace_id"),
            )
            row = await self._session_repository.update_patch(
                conn, session_id,
                tenant_key=tenant_key,
                user_context=request.user_context,
                attachment_ids=request.attachment_ids,
                control_ids=request.control_ids,
                proposed_tasks=request.proposed_tasks,
                now=now,
            )
        if not row:
            raise NotFoundError(f"Task builder session '{session_id}' not found")
        return _session_response(row)

    async def update_session_status(
        self, *, session_id: str, tenant_key: str, status: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.update_status(
                conn, session_id, tenant_key=tenant_key, status=status, now=now,
            )

    async def append_activity_log(
        self, *, session_id: str, tenant_key: str, events: list[dict]
    ) -> None:
        if not events:
            return
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.append_activity_log(
                conn, session_id, tenant_key=tenant_key, events=events, now=now,
            )

    async def clear_activity_log(
        self, *, session_id: str, tenant_key: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.clear_activity_log(
                conn, session_id, tenant_key=tenant_key, now=now,
            )

    async def save_preview_result(
        self, *, session_id: str, tenant_key: str, proposed_tasks: list
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.save_proposed_tasks(
                conn, session_id, tenant_key=tenant_key, proposed_tasks=proposed_tasks, now=now,
            )

    async def save_apply_result(
        self, *, session_id: str, tenant_key: str, apply_result: dict
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.save_apply_result(
                conn, session_id, tenant_key=tenant_key, apply_result=apply_result, now=now,
            )

    # ── Enqueue Preview (background job) ──────────────────────────────────────

    async def enqueue_preview(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
    ) -> TaskBuilderJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            session = await self._session_repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        if session.get("status") not in {"idle", "reviewing", "failed"}:
            raise AppValidationError("Session must be idle, reviewing, or failed to enqueue preview")

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_id": session["framework_id"],
            "scope_org_id": session.get("scope_org_id"),
            "scope_workspace_id": session.get("scope_workspace_id"),
            "user_context": session.get("user_context") or "",
            "attachment_ids": session.get("attachment_ids") or [],
            "control_ids": session.get("control_ids"),
        }
        job_id = await self._enqueue_job(
            job_type="task_builder_preview",
            agent_type_code="task_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code="normal",
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.set_job(
                conn, session_id, tenant_key=tenant_key, job_id=job_id, status="generating", now=now,
            )
        await self.clear_activity_log(session_id=session_id, tenant_key=tenant_key)
        return TaskBuilderJobStatusResponse(job_id=job_id, status="queued", job_type="task_builder_preview")

    # ── Enqueue Apply (background job) ────────────────────────────────────────

    async def enqueue_apply(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
        task_groups: list[dict] | None = None,
    ) -> TaskBuilderJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            session = await self._session_repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        if session.get("status") not in {"reviewing", "failed"}:
            raise AppValidationError("Session must be in reviewing state to apply tasks")
        if not session.get("scope_org_id") or not session.get("scope_workspace_id"):
            raise AppValidationError("Session is missing org/workspace scope")

        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn, user_id, "tasks.create",
                scope_org_id=session.get("scope_org_id"),
                scope_workspace_id=session.get("scope_workspace_id"),
            )

        proposed = task_groups if task_groups is not None else session.get("proposed_tasks") or []
        if not proposed:
            raise AppValidationError("No task groups to apply")

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_id": session["framework_id"],
            "scope_org_id": session["scope_org_id"],
            "scope_workspace_id": session["scope_workspace_id"],
            "task_groups": proposed,
        }
        job_id = await self._enqueue_job(
            job_type="task_builder_apply",
            agent_type_code="task_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code="normal",
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._session_repository.set_job(
                conn, session_id, tenant_key=tenant_key, job_id=job_id, status="applying", now=now,
            )
        await self.clear_activity_log(session_id=session_id, tenant_key=tenant_key)
        return TaskBuilderJobStatusResponse(job_id=job_id, status="queued", job_type="task_builder_apply")

    # ── Poll Job Status ───────────────────────────────────────────────────────

    async def get_job_status(
        self, *, user_id: str, tenant_key: str, job_id: str
    ) -> TaskBuilderJobStatusResponse:
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"Fetching job status: job_id={job_id!r}, user_id={user_id!r}, tenant={tenant_key!r}")

        async with self._database_pool.acquire() as conn:
            try:
                row = await conn.fetchrow(
                    f"""
                    SELECT id::text, status_code, job_type, output_json,
                           error_message, started_at::text, completed_at::text,
                           org_id::text AS scope_org_id,
                           workspace_id::text AS scope_workspace_id
                    FROM {_JOBS}
                    WHERE id = $1::uuid AND tenant_key = $2 AND user_id = $3::uuid
                    """,
                    job_id, tenant_key, user_id,
                )
            except Exception as e:
                logger.error(f"Database error in get_job_status: {e}")
                raise

            if not row:
                logger.warning(f"Job not found or access denied: job_id={job_id!r}, user_id={user_id!r}")
                raise NotFoundError(f"Job '{job_id}' not found")

            # Convert Record to dict to safely use .get()
            data = dict(row)
            logger.debug(f"Job row found: status={data.get('status_code')}")

        output = data.get("output_json")
        if isinstance(output, str):
            try:
                output = json.loads(output)
                logger.debug(f"Parsed output_json from string: {len(str(output))} chars")
            except Exception as e:
                logger.error(f"Failed to parse job output_json for job {job_id}: {e}")
                output = {}
        output = output or {}

        raw_log = output.get("creation_log", [])
        creation_log = []
        for item in raw_log:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except Exception:
                    item = {"event": "log", "message": item}
            creation_log.append(item)

        stats = output.get("stats", {})
        if isinstance(stats, str):
            try:
                stats = json.loads(stats)
            except Exception:
                stats = {}

        def _dt(v):
            return v.isoformat() if v is not None and hasattr(v, "isoformat") else v

        try:
            res = TaskBuilderJobStatusResponse(
                job_id=str(data["id"]),
                status=data["status_code"],
                job_type=data["job_type"],
                creation_log=creation_log,
                stats=stats,
                error_message=data.get("error_message"),
                started_at=_dt(data.get("started_at")),
                completed_at=_dt(data.get("completed_at")),
            )
            logger.debug(f"Constructed TaskBuilderJobStatusResponse for {job_id}")
            return res
        except Exception as e:
            logger.error(f"TaskBuilderJobStatusResponse construction failed for {job_id}: {type(e).__name__}: {e}")
            raise

    # ── Internal: enqueue job ──────────────────────────────────────────────────

    async def _enqueue_job(
        self,
        *,
        job_type: str,
        agent_type_code: str,
        user_id: str,
        tenant_key: str,
        priority_code: str,
        input_json: dict,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {_JOBS} (
                    id, tenant_key, user_id, org_id, workspace_id, agent_type_code, priority_code,
                    status_code, job_type, input_json,
                    scheduled_at, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid, $6, $7,
                    'queued', $8, $9::jsonb,
                    NOW(), NOW(), NOW()
                )
                """,
                job_id,
                tenant_key,
                user_id,
                scope_org_id,
                scope_workspace_id,
                agent_type_code,
                priority_code,
                job_type,
                input_json,
            )
        return job_id

    # ── LLM config ────────────────────────────────────────────────────────────

    async def _resolve_llm(self) -> tuple[str, str, str]:
        _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
        _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")

        config_repo = _config_repo_mod.AgentConfigRepository()
        resolver = _resolver_mod.AgentConfigResolver(
            repository=config_repo,
            database_pool=self._database_pool,
            settings=self._settings,
        )
        llm_config = await resolver.resolve(agent_type_code="task_builder", org_id=None)
        return resolve_llm_config(llm_config, self._settings)

    # ── Controls prompt builder ───────────────────────────────────────────────

    def _build_controls_prompt(
        self, controls: list[dict], existing_tasks_by_control: dict[str, list[dict]]
    ) -> str:
        blocks: list[str] = []
        for control in controls:
            control_id = control["id"]
            existing_tasks = existing_tasks_by_control.get(control_id, [])
            task_lines = [
                (
                    f"    - [{task.get('status_code')}] {task.get('task_type_code')}: "
                    f"{_clean_text(task.get('title'), max_length=120)} | "
                    f"Acceptance: {_clean_text(task.get('acceptance_criteria'), max_length=160)}"
                )
                for task in existing_tasks
            ]
            if not task_lines:
                task_lines = ["    - none"]

            test_summary = (
                f"tests={control.get('test_count', 0)}, "
                f"passing_latest={control.get('passing_execution_count', 0)}, "
                f"failing_latest={control.get('failing_execution_count', 0)}, "
                f"latest_statuses={control.get('latest_result_statuses') or 'none'}, "
                f"latest_execution_at={control.get('latest_execution_at') or 'none'}"
            )
            evidence_summary = control.get("evidence_summaries") or "none"

            blocks.append(
                "\n".join(
                    [
                        f"- control_id: {control_id}",
                        f"  control_code: {control['control_code']}",
                        f"  control_type: {control.get('control_type') or 'unknown'}",
                        f"  criticality_code: {control.get('criticality_code') or 'unknown'}",
                        f"  automation_potential: {control.get('automation_potential') or 'unknown'}",
                        f"  name: {_clean_text(control.get('name')) or 'N/A'}",
                        f"  description: {_clean_text(control.get('description'), max_length=240) or 'N/A'}",
                        f"  implementation_guidance: {_clean_text(control.get('implementation_guidance'), max_length=240) or 'N/A'}",
                        f"  test_context: {test_summary}",
                        f"  evidence_context: {_clean_text(evidence_summary, max_length=240)}",
                        "  existing_non_terminal_tasks:",
                        *task_lines,
                    ]
                )
            )
        return "\n\n".join(blocks)

    # ── Task normalization ────────────────────────────────────────────────────

    def _normalize_generated_task(self, raw_task: dict) -> GeneratedTask | None:
        if not isinstance(raw_task, dict):
            return None

        title = _clean_text(raw_task.get("title"), max_length=500)
        description = _clean_text(raw_task.get("description"), max_length=4000)
        acceptance_criteria = _clean_text(
            raw_task.get("acceptance_criteria"), max_length=4000
        )
        if not title or not description or not acceptance_criteria:
            return None

        task_type_code = _normalize_task_type(
            raw_task,
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
        )
        remediation_plan = (
            _clean_text(raw_task.get("remediation_plan"), max_length=4000) or None
        )
        if task_type_code != "control_remediation":
            remediation_plan = None

        try:
            return GeneratedTask.model_validate(
                {
                    "title": title,
                    "description": description,
                    "priority_code": _normalize_priority(raw_task.get("priority_code")),
                    "due_days_from_now": _normalize_due_days(
                        raw_task.get("due_days_from_now")
                    ),
                    "acceptance_criteria": acceptance_criteria,
                    "task_type_code": task_type_code,
                    "remediation_plan": remediation_plan,
                }
            )
        except ValidationError:
            return None

    def _normalize_llm_groups(
        self,
        raw_result: object,
        *,
        controls_by_id: dict[str, dict],
        existing_tasks_by_control: dict[str, list[dict]],
    ) -> list[TaskGroupResponse]:
        if isinstance(raw_result, dict):
            raw_result = [raw_result]

        if not isinstance(raw_result, list):
            return []

        groups: list[TaskGroupResponse] = []
        for raw_group in raw_result:
            if not isinstance(raw_group, dict):
                continue
            control_id = _clean_text(raw_group.get("control_id"))
            control = controls_by_id.get(control_id)

            if not control:
                # AI might have mixed up record ID (UUID) with control_code
                code_to_match = _clean_text(raw_group.get("control_code")) or control_id
                if code_to_match:
                    for c in controls_by_id.values():
                        if c["control_code"] == code_to_match:
                            control = c
                            control_id = c["id"]
                            break

            if not control:
                continue

            raw_tasks = raw_group.get("tasks")
            if not isinstance(raw_tasks, list):
                continue

            seen_generated: list[dict] = []
            deduped_tasks: list[GeneratedTask] = []
            existing_tasks = existing_tasks_by_control.get(control_id, [])
            for raw_task in raw_tasks:
                task = self._normalize_generated_task(raw_task)
                if task is None:
                    continue
                if any(
                    _is_duplicate_task(task, existing) for existing in existing_tasks
                ):
                    continue
                if any(
                    _is_duplicate_task(task, existing) for existing in seen_generated
                ):
                    continue
                deduped_tasks.append(task)
                seen_generated.append(
                    {
                        "task_type_code": task.task_type_code,
                        "title": task.title,
                        "acceptance_criteria": task.acceptance_criteria,
                        "is_terminal": False,
                    }
                )

            if deduped_tasks:
                groups.append(
                    TaskGroupResponse(
                        control_id=control_id,
                        control_code=control["control_code"],
                        tasks=_sort_tasks(deduped_tasks),
                    )
                )
        return groups

    # ── Attachment upload ─────────────────────────────────────────────────────

    async def upload_attachment(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        filename: str,
        content_type: str,
        file_bytes: bytes,
    ) -> dict:
        _att_svc_mod = import_module("backend.20_ai.19_attachments.service")
        AttachmentService = _att_svc_mod.AttachmentService
        att_service = AttachmentService(
            settings=self._settings,
            database_pool=self._database_pool,
        )

        async with self._database_pool.acquire() as conn:
            sentinel_row = await conn.fetchrow(
                """
                SELECT id::text AS id
                FROM "20_ai"."20_fct_conversations"
                WHERE user_id        = $1::uuid
                  AND org_id         = $2::uuid
                  AND workspace_id   = $3::uuid
                  AND tenant_key     = $4
                  AND agent_type_code = 'task_agent'
                  AND title           = 'Task Builder Uploads'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                user_id, org_id, workspace_id, tenant_key,
            )
            if sentinel_row:
                conv_id = sentinel_row["id"]
            else:
                new_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "20_ai"."20_fct_conversations"
                        (id, user_id, tenant_key, org_id, workspace_id, agent_type_code, title)
                    VALUES ($1::uuid, $2::uuid, $3, $4::uuid, $5::uuid, 'task_agent', 'Task Builder Uploads')
                    """,
                    new_id, user_id, tenant_key, org_id, workspace_id,
                )
                conv_id = new_id

        result = await att_service.upload_and_ingest(
            conversation_id=conv_id,
            user_id=user_id,
            tenant_key=tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            filename=filename,
            content_type=content_type,
            file_bytes=file_bytes,
        )
        return result.model_dump() if hasattr(result, "model_dump") else dict(result)

    # ── Attachment context retrieval ──────────────────────────────────────────

    async def _retrieve_attachment_context(
        self,
        *,
        attachment_ids: list[str],
        user_id: str,
        tenant_key: str,
        query: str,
    ) -> str:
        if not attachment_ids:
            return ""
        try:
            _att_repo_mod = import_module("backend.20_ai.19_attachments.repository")
            _pi_mod = import_module("backend.20_ai.03_memory.pageindex")

            repo = _att_repo_mod.AttachmentRepository()
            async with self._database_pool.acquire() as conn:
                records = [
                    rec
                    for att_id in attachment_ids
                    if (
                        rec := await repo.get(
                            conn, attachment_id=att_id, user_id=user_id
                        )
                    )
                    is not None
                ]

            if not records:
                return ""

            pageindexer = (
                _pi_mod.PageIndexer(settings=self._settings)
                if (
                    self._settings.ai_pageindex_enabled
                    and self._settings.ai_provider_url
                )
                else _pi_mod.NullPageIndexer()
            )
            pi_blocks: list[str] = []
            for att in records:
                if att.pageindex_status == "ready" and att.pageindex_tree:
                    try:
                        answer = await pageindexer.retrieve(
                            query=query,
                            tree=att.pageindex_tree,
                            filename=att.filename,
                        )
                        if answer:
                            pi_blocks.append(f"### {att.filename}\n{answer}")
                    except Exception as exc:
                        self._logger.warning(
                            "task_builder.pageindex_failed attachment=%s: %s",
                            att.id,
                            exc,
                        )

            vec_block = ""
            try:
                if self._settings.ai_qdrant_url:
                    _embed_mod = import_module("backend.20_ai.03_memory.embedder")
                    _doc_store_mod = import_module(
                        "backend.20_ai.03_memory.document_store"
                    )
                    embedder = _embed_mod.Embedder(settings=self._settings)
                    vector = await embedder.embed(query)
                    if vector is not None:
                        doc_store = _doc_store_mod.CopilotDocumentStore(
                            qdrant_url=self._settings.ai_qdrant_url,
                            api_key=self._settings.ai_qdrant_api_key or "",
                        )
                        conv_ids = {
                            att.conversation_id
                            for att in records
                            if att.ingest_status == "ready" and att.chunk_count > 0
                        }
                        chunks: list = []
                        for conv_id in conv_ids:
                            chunks.extend(
                                await doc_store.search(
                                    query_vector=vector,
                                    tenant_key=tenant_key,
                                    conversation_id=conv_id,
                                    top_k=4,
                                    score_threshold=0.4,
                                )
                            )
                        if chunks:
                            seen: set[str] = set()
                            vec_lines = ["### Relevant Document Excerpts"]
                            for chunk in chunks:
                                if chunk.filename not in seen:
                                    vec_lines.append(f"**{chunk.filename}**")
                                    seen.add(chunk.filename)
                                vec_lines.append(chunk.chunk_text)
                            vec_block = "\n".join(vec_lines)
            except Exception as exc:
                self._logger.warning("task_builder.vector_rag_failed: %s", exc)

            parts: list[str] = []
            if pi_blocks:
                parts.append(
                    "## Document Context (Hierarchical)\n" + "\n\n".join(pi_blocks)
                )
            if vec_block:
                parts.append(vec_block)
            return "\n\n".join(parts)
        except Exception as exc:
            self._logger.warning("task_builder.attachment_context_failed: %s", exc)
            return ""

    # ── Preview tasks (core logic — used by both sync endpoint and job handler) ──

    async def preview_tasks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        user_context: str,
        control_ids: list[str] | None = None,
        attachment_ids: list[str] | None = None,
    ) -> list[TaskGroupResponse]:
        async with self._database_pool.acquire() as connection:
            await require_permission(
                connection,
                user_id,
                "frameworks.view",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )
            framework = await self._repository.get_framework(
                connection,
                framework_id=framework_id,
                tenant_key=tenant_key,
            )
            if framework is None:
                raise NotFoundError(f"Framework {framework_id} not found")

            controls = await self._repository.list_controls(
                connection,
                framework_id=framework_id,
                tenant_key=tenant_key,
                control_ids=control_ids,
            )
            control_id_list = [control["id"] for control in controls]
            existing_tasks = await self._repository.list_existing_non_terminal_tasks(
                connection,
                tenant_key=tenant_key,
                control_ids=control_id_list,
            )

        if not controls:
            return []

        existing_tasks_by_control: dict[str, list[dict]] = {}
        for task in existing_tasks:
            existing_tasks_by_control.setdefault(task["control_id"], []).append(task)

        attachment_context = ""
        if attachment_ids:
            attachment_query = (
                f"{user_context or ''} {framework.get('name') or framework['framework_code']}".strip()
                or "compliance tasks evidence remediation controls"
            )
            attachment_context = await self._retrieve_attachment_context(
                attachment_ids=attachment_ids,
                user_id=user_id,
                tenant_key=tenant_key,
                query=attachment_query,
            )

        document_context_section = (
            f"\n## Uploaded Document Context\n{attachment_context}\n"
            if attachment_context
            else ""
        )

        try:
            provider_url, api_key, model = await self._resolve_llm()
        except RuntimeError as exc:
            # Runtime error from resolve_llm_config usually means missing env/db config
            self._logger.error("task_builder.resolve_failed", extra={"error": str(exc)})
            raise ServiceUnavailableError(
                "AI is not configured. Please check your AI provider settings."
            ) from exc
        except Exception as exc:
            self._logger.error(
                "task_builder.llm_config_failed: %s",
                str(exc)[:500],
            )
            raise ServiceUnavailableError(
                "AI configuration error. Please contact your administrator."
            ) from exc

        groups: list[TaskGroupResponse] = []
        errors: list[str] = []

        batch_size_raw = getattr(self._settings, "task_builder_batch_size", None)
        batch_size = max(1, int(batch_size_raw)) if batch_size_raw else _CONTROL_CHUNK_SIZE
        concurrency_raw = getattr(self._settings, "task_builder_concurrency", None)
        concurrency = max(1, int(concurrency_raw)) if concurrency_raw else 5
        chunks = _chunks(controls, batch_size)
        semaphore = asyncio.Semaphore(concurrency)  # Limit concurrent LLM calls to avoid rate limits

        async def process_chunk_with_sem(chunk: list[dict]) -> list[TaskGroupResponse]:
            async with semaphore:
                chunk_controls_by_id = {c["id"]: c for c in chunk}
                chunk_prompt = TASKS_PROMPT.format(
                    framework_name=framework.get("name") or framework["framework_code"],
                    framework_code=framework["framework_code"],
                    user_context=user_context or "No specific focus provided.",
                    document_context=document_context_section,
                    controls_list=self._build_controls_prompt(
                        chunk, existing_tasks_by_control
                    ),
                )
                try:
                    raw = await llm_complete(
                        provider_url=provider_url,
                        api_key=api_key,
                        model=model,
                        system=chunk_prompt,
                        user="Generate the task groups now.",
                        max_tokens=min(8000, self._settings.ai_max_tokens),
                        temperature=1.0,  # Slight variation allowed
                    )
                    parsed = parse_json(raw)
                    return self._normalize_llm_groups(
                        parsed,
                        controls_by_id=chunk_controls_by_id,
                        existing_tasks_by_control=existing_tasks_by_control,
                    )
                except import_module("httpx").HTTPStatusError as exc:
                    status = exc.response.status_code
                    msg = str(exc)
                    if status == 429:
                        msg = "AI rate limit reached. Please try again in a few moments."
                    elif status >= 500:
                        msg = f"AI provider error ({status})."
                    self._logger.warning("task_builder.chunk_http_failed: %s", msg)
                    errors.append(msg)
                    return []
                except asyncio.TimeoutError:
                    self._logger.warning("task_builder.chunk_timeout")
                    errors.append("AI request timed out.")
                    return []
                except Exception as exc:
                    self._logger.warning("task_builder.chunk_failed: %s", str(exc)[:200])
                    errors.append(f"Unexpected AI error: {type(exc).__name__}")
                    return []

        results = await asyncio.gather(*(process_chunk_with_sem(c) for c in chunks))

        for chunk_result in results:
            groups.extend(chunk_result)

        if not groups and len(chunks) > 0:
            # If everything failed, report the most common error
            if errors:
                from collections import Counter
                most_common_err = Counter(errors).most_common(1)[0][0]
                raise ServiceUnavailableError(most_common_err)
            
            # If it succeeded but just returned no tasks
            pass

        groups.sort(key=lambda group: group.control_code)
        return groups

    # ── Create task record ────────────────────────────────────────────────────

    async def _create_task_record(
        self,
        connection,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        control_id: str,
        user_id: str,
        task: GeneratedTask,
    ) -> None:
        now = utc_now_sql()
        due_date = (
            datetime.now(tz=UTC).date() + timedelta(days=task.due_days_from_now)
        ).isoformat()
        task_id = str(uuid.uuid4())

        await connection.execute(
            "SELECT pg_advisory_xact_lock(hashtext($1), hashtext($2))",
            control_id,
            f"{task.task_type_code}:{_normalize_for_intent(task.title + ' ' + task.acceptance_criteria)}",
        )

        existing_tasks = await self._repository.list_existing_non_terminal_tasks(
            connection,
            tenant_key=tenant_key,
            control_ids=[control_id],
        )
        if any(_is_duplicate_task(task, existing) for existing in existing_tasks):
            raise FileExistsError("duplicate_task")

        await self._task_repository.create_task(
            connection,
            task_id=task_id,
            tenant_key=tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            task_type_code=task.task_type_code,
            priority_code=task.priority_code,
            entity_type="control",
            entity_id=control_id,
            assignee_user_id=None,
            reporter_user_id=user_id,
            due_date=due_date,
            start_date=None,
            estimated_hours=None,
            created_by=user_id,
            now=now,
        )
        await self._task_repository.set_task_property(
            connection,
            prop_id=str(uuid.uuid4()),
            task_id=task_id,
            property_key="title",
            property_value=task.title,
            actor_id=user_id,
            now=now,
        )
        await self._task_repository.set_task_property(
            connection,
            prop_id=str(uuid.uuid4()),
            task_id=task_id,
            property_key="description",
            property_value=task.description,
            actor_id=user_id,
            now=now,
        )
        await self._task_repository.set_task_property(
            connection,
            prop_id=str(uuid.uuid4()),
            task_id=task_id,
            property_key="acceptance_criteria",
            property_value=task.acceptance_criteria,
            actor_id=user_id,
            now=now,
        )
        if task.remediation_plan:
            await self._task_repository.set_task_property(
                connection,
                prop_id=str(uuid.uuid4()),
                task_id=task_id,
                property_key="remediation_plan",
                property_value=task.remediation_plan,
                actor_id=user_id,
                now=now,
            )
        await self._event_repository.create_event(
            connection,
            event_id=str(uuid.uuid4()),
            task_id=task_id,
            event_type="created",
            old_value=None,
            new_value=None,
            comment="Created by AI task builder",
            actor_id=user_id,
            now=now,
        )
        await self._audit_writer.write_entry(
            connection,
            AuditEntry(
                id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                entity_type="task",
                entity_id=task_id,
                event_type=TaskAuditEventType.TASK_CREATED.value,
                event_category=AuditEventCategory.TASK.value,
                occurred_at=now,
                actor_id=user_id,
                actor_type="user",
                properties={
                    "title": task.title,
                    "task_type_code": task.task_type_code,
                    "priority_code": task.priority_code,
                    "org_id": org_id,
                    "workspace_id": workspace_id,
                    "entity_type": "control",
                    "entity_id": control_id,
                    "source": "ai_task_builder",
                },
            ),
        )

    # ── Apply tasks (core logic — used by both sync endpoint and job handler) ──

    async def apply_tasks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        framework_id: str,
        task_groups: list[TaskGroupResponse],
    ) -> ApplyResponse:
        del (
            framework_id
        )  # framework scoping is already encoded by the control-linked tasks

        async with self._database_pool.acquire() as connection:
            await require_permission(
                connection,
                user_id,
                "tasks.create",
                scope_org_id=org_id,
                scope_workspace_id=workspace_id,
            )

        created = 0
        skipped = 0
        for group in task_groups:
            control_id = group.control_id
            seen_payload: list[dict] = []
            for task in group.tasks:
                if any(_is_duplicate_task(task, existing) for existing in seen_payload):
                    skipped += 1
                    continue

                try:
                    async with self._database_pool.transaction() as connection:
                        await self._create_task_record(
                            connection,
                            tenant_key=tenant_key,
                            org_id=org_id,
                            workspace_id=workspace_id,
                            control_id=control_id,
                            user_id=user_id,
                            task=task,
                        )
                    created += 1
                    seen_payload.append(
                        {
                            "task_type_code": task.task_type_code,
                            "title": task.title,
                            "acceptance_criteria": task.acceptance_criteria,
                            "is_terminal": False,
                        }
                    )
                except FileExistsError:
                    skipped += 1
                except Exception as exc:
                    self._logger.error(
                        "task_builder.apply_failed",
                        extra={
                            "control_id": control_id,
                            "task_type_code": task.task_type_code,
                            "title": task.title[:120],
                            "error": str(exc),
                        },
                        exc_info=True
                    )
                    skipped += 1

        await self._cache.delete_pattern(f"tasks:list:{tenant_key}:*")
        await self._cache.delete_pattern(f"tasks:summary:{tenant_key}:*")
        return ApplyResponse(created=created, skipped=skipped)
