"""
Job handlers for async task builder operations.

Called by the job queue worker via job_processor.dispatch():
  - task_builder_preview  → Generate task suggestions and persist to session
  - task_builder_apply    → Create approved tasks in DB and persist result
"""

from __future__ import annotations

import asyncio
import datetime
import json
from contextlib import asynccontextmanager
from importlib import import_module
from typing import AsyncIterator

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.task_builder.job_handler")

_JOBS = '"20_ai"."45_fct_job_queue"'
_SESSIONS = '"20_ai"."65_fct_task_builder_sessions"'


# ── Helpers ──────────────────────────────────────────────────────────────────


async def _append_progress(conn: asyncpg.Connection, job_id: str, event: dict) -> None:
    """Append a single progress event to output_json.creation_log."""
    event["ts"] = datetime.datetime.utcnow().isoformat()
    await conn.execute(
        f"""
        UPDATE {_JOBS}
        SET output_json = jsonb_set(
            COALESCE(output_json, '{{"creation_log":[]}}'),
            '{{creation_log}}',
            COALESCE(output_json->'creation_log', '[]') || $2::jsonb
        ),
        updated_at = NOW()
        WHERE id = $1
        """,
        job_id,
        event,
    )


class _PoolAdapter:
    """Adapter wrapping asyncpg.Pool with acquire()/transaction() interface."""

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn


def _chunks(items: list, size: int) -> list[list]:
    return [items[i : i + size] for i in range(0, len(items), size)]


async def _init_output(conn: asyncpg.Connection, job_id: str) -> None:
    """Ensure output_json is a proper JSON object (not null/array)."""
    await conn.execute(
        f"""
        UPDATE {_JOBS}
        SET output_json = '{{"creation_log":[]}}'::jsonb
        WHERE id = $1 AND (output_json IS NULL OR jsonb_typeof(output_json) != 'object')
        """,
        job_id,
    )


# ── Preview Job Handler ──────────────────────────────────────────────────────


async def handle_preview_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """Generate task suggestions with per-chunk progress and persist to session."""
    # Ensure output_json is properly initialized as an object
    async with pool.acquire() as conn:
        await _init_output(conn, job.id)

    inp = job.input_json if isinstance(job.input_json, dict) else json.loads(job.input_json or "{}")
    session_id = inp["session_id"]
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    framework_id = inp["framework_id"]
    org_id = inp.get("scope_org_id")
    workspace_id = inp.get("scope_workspace_id")
    user_context = inp.get("user_context", "")
    attachment_ids = inp.get("attachment_ids") or []
    control_ids = inp.get("control_ids")

    adapter = _PoolAdapter(pool)

    _svc_module = import_module("backend.20_ai.31_task_builder.service")
    _cache_module = import_module("backend.01_core.cache")
    _llm_utils_mod = import_module("backend.20_ai._llm_utils")
    _prompts_module = import_module("backend.20_ai.31_task_builder.prompts")

    cache = _cache_module.NullCacheManager()
    service = _svc_module.TaskBuilderService(
        settings=settings,
        database_pool=adapter,
        cache=cache,
    )
    llm_complete = _llm_utils_mod.llm_complete
    parse_json = _llm_utils_mod.parse_json
    TASKS_PROMPT = _prompts_module.TASKS_PROMPT

    try:
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, {
                "event": "stage_start",
                "stage": "preview",
                "title": "Generating task suggestions",
                "message": "Loading framework controls and existing tasks...",
            })

        # Load controls and existing tasks
        _repo_module = import_module("backend.20_ai.31_task_builder.repository")
        repo = _repo_module.TaskBuilderRepository()
        _perm_module = import_module("backend.03_auth_manage._permission_check")
        require_permission = _perm_module.require_permission

        async with pool.acquire() as conn:
            await require_permission(conn, user_id, "frameworks.view",
                                     scope_org_id=org_id, scope_workspace_id=workspace_id)
            framework = await repo.get_framework(conn, framework_id=framework_id, tenant_key=tenant_key)
            if not framework:
                raise ValueError(f"Framework {framework_id} not found")
            controls = await repo.list_controls(conn, framework_id=framework_id,
                                                tenant_key=tenant_key, control_ids=control_ids)
            control_id_list = [c["id"] for c in controls]
            existing_tasks = await repo.list_existing_non_terminal_tasks(
                conn, tenant_key=tenant_key, control_ids=control_id_list)

        if not controls:
            async with pool.acquire() as conn:
                await _append_progress(conn, job.id, {
                    "event": "preview_complete",
                    "stage": "preview",
                    "message": "No controls found in framework",
                    "task_count": 0,
                    "group_count": 0,
                })
            await service.save_preview_result(session_id=session_id, tenant_key=tenant_key, proposed_tasks=[])
            return

        existing_tasks_by_control: dict[str, list[dict]] = {}
        for task in existing_tasks:
            existing_tasks_by_control.setdefault(task["control_id"], []).append(task)

        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, {
                "event": "controls_loaded",
                "stage": "preview",
                "message": f"Found {len(controls)} controls, {len(existing_tasks)} existing tasks",
                "control_count": len(controls),
                "existing_task_count": len(existing_tasks),
            })

        # Retrieve attachment context
        attachment_context = ""
        if attachment_ids:
            async with pool.acquire() as conn:
                await _append_progress(conn, job.id, {
                    "event": "doc_analyzing",
                    "stage": "preview",
                    "message": f"Analyzing {len(attachment_ids)} uploaded document(s)...",
                })
            attachment_query = (
                f"{user_context or ''} {framework.get('name') or framework['framework_code']}".strip()
                or "compliance tasks evidence remediation controls"
            )
            attachment_context = await service._retrieve_attachment_context(
                attachment_ids=attachment_ids, user_id=user_id,
                tenant_key=tenant_key, query=attachment_query,
            )
            if attachment_context:
                async with pool.acquire() as conn:
                    await _append_progress(conn, job.id, {
                        "event": "doc_ready",
                        "stage": "preview",
                        "message": "Document context retrieved",
                    })

        document_context_section = (
            f"\n## Uploaded Document Context\n{attachment_context}\n"
            if attachment_context else ""
        )

        # Resolve LLM config
        try:
            provider_url, api_key, model = await service._resolve_llm()
        except Exception as exc:
            raise ValueError(f"LLM config failed: {exc}") from exc

        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, {
                "event": "llm_call_start",
                "stage": "preview",
                "message": f"Calling AI model ({model}) to generate tasks...",
                "model": model,
            })

        # Process controls in chunks — chunks run in parallel with bounded concurrency.
        # Batch size and concurrency come from settings (TASK_BUILDER_BATCH_SIZE,
        # TASK_BUILDER_CONCURRENCY) so they can be tuned without code changes.
        batch_size_raw = getattr(settings, "task_builder_batch_size", None)
        batch_size = max(1, int(batch_size_raw)) if batch_size_raw else 8
        concurrency_raw = getattr(settings, "task_builder_concurrency", None)
        concurrency = max(1, int(concurrency_raw)) if concurrency_raw else 5

        all_groups = []
        control_chunks = _chunks(controls, batch_size)
        total_chunks = len(control_chunks)
        semaphore = asyncio.Semaphore(concurrency)
        completed_count = 0
        completed_lock = asyncio.Lock()

        async def _process_chunk(chunk_idx: int, control_chunk: list[dict]):
            nonlocal completed_count
            chunk_codes = [c["control_code"] for c in control_chunk]

            async with semaphore:
                async with pool.acquire() as conn:
                    await _append_progress(conn, job.id, {
                        "event": "chunk_start",
                        "stage": "preview",
                        "message": f"Processing controls batch {chunk_idx}/{total_chunks} ({', '.join(chunk_codes[:3])}{'...' if len(chunk_codes) > 3 else ''})",
                        "chunk": chunk_idx,
                        "total_chunks": total_chunks,
                        "control_codes": chunk_codes,
                    })

                controls_by_id = {c["id"]: c for c in control_chunk}
                prompt = TASKS_PROMPT.format(
                    framework_name=framework.get("name") or framework["framework_code"],
                    framework_code=framework["framework_code"],
                    user_context=user_context or "No specific focus provided.",
                    document_context=document_context_section,
                    controls_list=service._build_controls_prompt(control_chunk, existing_tasks_by_control),
                )

                try:
                    raw = await llm_complete(
                        provider_url=provider_url,
                        api_key=api_key,
                        model=model,
                        system=prompt,
                        user="Generate the task groups now.",
                        max_tokens=min(8000, settings.ai_max_tokens),
                        temperature=1.0,
                    )
                except Exception as exc:
                    async with pool.acquire() as conn:
                        await _append_progress(conn, job.id, {
                            "event": "chunk_error",
                            "stage": "preview",
                            "message": f"LLM call failed for batch {chunk_idx}: {str(exc)[:200]}",
                            "chunk": chunk_idx,
                        })
                    return []

                try:
                    parsed = parse_json(raw)
                except Exception as exc:
                    async with pool.acquire() as conn:
                        await _append_progress(conn, job.id, {
                            "event": "chunk_parse_error",
                            "stage": "preview",
                            "message": f"Failed to parse AI response for batch {chunk_idx}: {str(exc)[:200]}",
                            "chunk": chunk_idx,
                        })
                    return []

                chunk_groups = service._normalize_llm_groups(
                    parsed, controls_by_id=controls_by_id,
                    existing_tasks_by_control=existing_tasks_by_control,
                )
                chunk_task_count = sum(len(g.tasks) for g in chunk_groups)

                async with completed_lock:
                    completed_count += 1
                    completed_so_far = completed_count

                async with pool.acquire() as conn:
                    await _append_progress(conn, job.id, {
                        "event": "chunk_complete",
                        "stage": "preview",
                        "message": f"Batch {chunk_idx}/{total_chunks}: {chunk_task_count} tasks generated ({completed_so_far}/{total_chunks} done)",
                        "chunk": chunk_idx,
                        "total_chunks": total_chunks,
                        "chunk_task_count": chunk_task_count,
                        "completed_chunks": completed_so_far,
                    })
                return chunk_groups

        chunk_results = await asyncio.gather(
            *(_process_chunk(idx, chunk) for idx, chunk in enumerate(control_chunks, 1))
        )
        for chunk_groups in chunk_results:
            all_groups.extend(chunk_groups)

        all_groups.sort(key=lambda g: g.control_code)
        groups_data = [g.model_dump() for g in all_groups]
        total_tasks = sum(len(g.tasks) for g in all_groups)

        # Save to session
        await service.save_preview_result(
            session_id=session_id,
            tenant_key=tenant_key,
            proposed_tasks=groups_data,
        )

        # Save stats to job output
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_JOBS}
                SET output_json = jsonb_set(
                    COALESCE(output_json, '{{}}'::jsonb),
                    '{{stats}}',
                    $1::jsonb
                ),
                    updated_at = NOW()
                WHERE id = $2
                """,
                {"task_count": total_tasks, "group_count": len(all_groups)},
                job.id,
            )
            await _append_progress(conn, job.id, {
                "event": "preview_complete",
                "stage": "preview",
                "message": f"Preview complete — {total_tasks} tasks ready for review across {len(all_groups)} controls",
                "task_count": total_tasks,
                "group_count": len(all_groups),
            })

    except Exception as exc:
        _logger.exception("task_builder.preview_job_failed: %s", exc)
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, {
                "event": "error",
                "stage": "preview",
                "message": f"Preview failed: {str(exc)[:500]}",
            })
            await conn.execute(
                f"UPDATE {_SESSIONS} SET status = 'failed', error_message = $1, updated_at = NOW() WHERE id = $2 AND tenant_key = $3",
                str(exc)[:2000], session_id, tenant_key,
            )
        raise


# ── Apply Job Handler ────────────────────────────────────────────────────────


async def handle_apply_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """Create approved tasks in DB and persist result to session."""
    async with pool.acquire() as conn:
        await _init_output(conn, job.id)

    inp = job.input_json if isinstance(job.input_json, dict) else json.loads(job.input_json or "{}")
    session_id = inp["session_id"]
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    org_id = inp["scope_org_id"]
    workspace_id = inp["scope_workspace_id"]
    framework_id = inp["framework_id"]
    task_groups_data = inp.get("task_groups", [])

    adapter = _PoolAdapter(pool)

    total_task_count = sum(len(g.get("tasks", [])) for g in task_groups_data)

    async with pool.acquire() as conn:
        await _append_progress(conn, job.id, {
            "event": "stage_start",
            "stage": "apply",
            "title": "Creating tasks",
            "message": f"Applying {total_task_count} tasks across {len(task_groups_data)} controls...",
        })

    _svc_module = import_module("backend.20_ai.31_task_builder.service")
    _cache_module = import_module("backend.01_core.cache")
    _schemas_module = import_module("backend.20_ai.31_task_builder.schemas")

    cache = _cache_module.NullCacheManager()
    service = _svc_module.TaskBuilderService(
        settings=settings,
        database_pool=adapter,
        cache=cache,
    )
    TaskGroupResponse = _schemas_module.TaskGroupResponse

    try:
        groups = [TaskGroupResponse.model_validate(g) for g in task_groups_data]

        created = 0
        skipped = 0
        for i, group in enumerate(groups, 1):
            async with pool.acquire() as conn:
                await _append_progress(conn, job.id, {
                    "event": "control_processing",
                    "stage": "apply",
                    "message": f"Processing {group.control_code} ({i}/{len(groups)}) — {len(group.tasks)} tasks",
                    "control_code": group.control_code,
                    "progress": i,
                    "total": len(groups),
                })

            result = await service.apply_tasks(
                user_id=user_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                framework_id=framework_id,
                task_groups=[group],
            )
            created += result.created
            skipped += result.skipped

            async with pool.acquire() as conn:
                await _append_progress(conn, job.id, {
                    "event": "control_complete",
                    "stage": "apply",
                    "message": f"{group.control_code}: {result.created} created, {result.skipped} skipped",
                    "control_code": group.control_code,
                    "created": result.created,
                    "skipped": result.skipped,
                    "running_created": created,
                    "running_skipped": skipped,
                })

        apply_result = {"created": created, "skipped": skipped}
        await service.save_apply_result(
            session_id=session_id,
            tenant_key=tenant_key,
            apply_result=apply_result,
        )

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_JOBS}
                SET output_json = jsonb_set(
                    COALESCE(output_json, '{{}}'::jsonb),
                    '{{stats}}',
                    $1::jsonb
                ),
                    updated_at = NOW()
                WHERE id = $2
                """,
                apply_result,
                job.id,
            )
            await _append_progress(conn, job.id, {
                "event": "apply_complete",
                "stage": "apply",
                "message": f"Apply complete — {created} tasks created, {skipped} skipped",
                "created": created,
                "skipped": skipped,
            })

    except Exception as exc:
        _logger.exception("task_builder.apply_job_failed: %s", exc)
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, {
                "event": "error",
                "stage": "apply",
                "message": f"Apply failed: {str(exc)[:500]}",
            })
            await conn.execute(
                f"UPDATE {_SESSIONS} SET status = 'failed', error_message = $1, updated_at = NOW() WHERE id = $2 AND tenant_key = $3",
                str(exc)[:2000], session_id, tenant_key,
            )
        raise
