from __future__ import annotations

import json

from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger
_logger = get_logger("backend.ai.test_linker.bulk_link")

_JOBS = '"20_ai"."45_fct_job_queue"'


async def handle_bulk_link_job(job, pool, settings) -> None:
    """Background job: propose bulk control test ↔ control mappings."""
    input_data = job.input_json or {}
    org_id = input_data["org_id"]
    workspace_id = input_data.get("workspace_id")
    framework_id = input_data.get("framework_id")
    control_ids = input_data.get("control_ids") or None
    test_ids = input_data.get("test_ids") or None
    tenant_key = input_data["tenant_key"]
    user_id = input_data.get("user_id")
    dry_run = bool(input_data.get("dry_run", False))

    from .repository import TestLinkerRepository
    from .service import TestLinkerService

    repo = TestLinkerRepository()
    service = TestLinkerService(settings=settings, database_pool=pool)

    async with pool.acquire() as conn:
        controls = await repo.list_all_controls(
            conn,
            tenant_key=tenant_key,
            framework_id=framework_id,
            deployed_org_id=org_id,
            deployed_workspace_id=workspace_id,
            control_ids=control_ids,
            limit=1000,
        )
        tests = await repo.list_tests(
            conn,
            tenant_key=tenant_key,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
            test_ids=test_ids,
            limit=1000,
        )

    if not controls or not tests:
        await _complete_job(
            pool,
            job.id,
            {
                "total_controls": len(controls),
                "total_tests": len(tests),
                "mappings_created": 0,
                "mappings_skipped": 0,
                "errors": 0,
                "dry_run": dry_run,
            },
        )
        return

    total_controls = len(controls)
    mappings_created = 0
    mappings_skipped = 0
    errors = 0

    for index, control in enumerate(controls):
        pct = int((index / total_controls) * 100)
        await _update_progress(pool, job.id, pct)
        try:
            async with pool.acquire() as conn:
                existing = await repo.get_existing_mappings_for_control(
                    conn,
                    control_id=control["id"],
                )

            suggestions = await service._suggest_tests_for_control_candidates(
                control=control,
                tests=tests,
                existing_test_ids=existing,
            )

            if dry_run:
                mappings_created += len(suggestions)
                continue

            async with pool.acquire() as conn:
                for suggestion in suggestions:
                    inserted = await repo.create_mapping_if_not_exists(
                        conn,
                        test_id=suggestion.test_id,
                        control_id=control["id"],
                        link_type=suggestion.link_type,
                        ai_confidence=suggestion.confidence,
                        ai_rationale=suggestion.rationale,
                        created_by=user_id,
                    )
                    if inserted:
                        mappings_created += 1
                    else:
                        mappings_skipped += 1
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Bulk test linking failed for control %s: %s", control.get("control_code"), exc)
            errors += 1

    await _complete_job(
        pool,
        job.id,
        {
            "total_controls": total_controls,
            "total_tests": len(tests),
            "mappings_created": mappings_created,
            "mappings_skipped": mappings_skipped,
            "errors": errors,
            "dry_run": dry_run,
        },
    )


async def _update_progress(pool, job_id: str, pct: int) -> None:
    """Update job progress (stored in output_json since progress_pct column doesn't exist)."""
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {_JOBS} SET output_json = jsonb_set(COALESCE(output_json, '{{}}'::jsonb), '{{progress_pct}}', $1::jsonb), updated_at = NOW() WHERE id = $2::uuid",
                json.dumps(pct),
                job_id,
            )
    except Exception:  # noqa: BLE001
        pass


async def _complete_job(pool, job_id: str, output: dict) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            UPDATE {_JOBS}
            SET status_code = 'completed',
                output_json = $1::jsonb,
                updated_at = NOW()
            WHERE id = $2::uuid
            """,
            json.dumps(output),
            job_id,
        )


async def _fail_job(pool, job_id: str, error_message: str) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            UPDATE {_JOBS}
            SET status_code = 'failed',
                error_message = $1,
                updated_at = NOW()
            WHERE id = $2::uuid
            """,
            error_message,
            job_id,
        )
