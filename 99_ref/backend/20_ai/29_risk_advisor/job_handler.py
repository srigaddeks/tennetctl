from __future__ import annotations

import asyncio
import json
import uuid
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
get_logger = _logging_module.get_logger
_logger = get_logger("backend.ai.risk_advisor.bulk_link")

_JOBS = '"20_ai"."45_fct_job_queue"'


async def handle_bulk_link_job(job, pool, settings) -> None:
    """Background job: auto-link all controls in a framework to matching risks."""
    input_data = job.input_json or {}
    framework_id = input_data.get("framework_id") or None  # None = all frameworks
    risk_id = input_data.get("risk_id") or None            # None = all risks in workspace
    org_id = input_data["org_id"]
    workspace_id = input_data.get("workspace_id")
    tenant_key = input_data["tenant_key"]
    user_id = input_data.get("user_id")
    dry_run = bool(input_data.get("dry_run", False))

    from .repository import RiskAdvisorRepository
    from .service import RiskAdvisorService, _parse_json_array

    repo = RiskAdvisorRepository()
    service = RiskAdvisorService(settings=settings, database_pool=pool)

    try:
        provider, _ = await service._get_provider()
    except Exception as exc:
        await _fail_job(pool, job.id, str(exc))
        return

    async with pool.acquire() as conn:
        controls = await repo.fetch_candidate_controls(
            conn,
            tenant_key=tenant_key,
            org_id=org_id,
            framework_ids=[framework_id] if framework_id else None,  # None = all frameworks
            limit=500,
        )
        risks = await repo.fetch_risks_for_bulk(
            conn,
            tenant_key=tenant_key,
            org_id=org_id,
            workspace_id=workspace_id,
            risk_id=risk_id,
        )

    if not controls or not risks:
        await _complete_job(pool, job.id, {
            "total_controls": len(controls),
            "risks_scanned": len(risks),
            "mappings_created": 0,
            "mappings_skipped": 0,
            "errors": 0,
            "dry_run": dry_run,
        })
        return

    from .prompts import BULK_LINK_CONTROL_USER, BULK_LINK_SYSTEM

    risks_data = [
        {
            "risk_id": r["id"],
            "risk_code": r["risk_code"],
            "category": r["risk_category_code"],
            "level": r["risk_level_code"],
            "title": r.get("title") or "",
            "description": (r.get("description") or "")[:300],
        }
        for r in risks
    ]

    total = len(controls)
    mappings_created = 0
    mappings_skipped = 0
    errors = 0
    log_lines: list[str] = []

    def _log(msg: str) -> None:
        log_lines.append(msg)
        # keep last 50 lines to bound payload
        if len(log_lines) > 50:
            del log_lines[: len(log_lines) - 50]

    _logger.info(
        "bulk_link.started",
        extra={"job_id": job.id, "total_controls": total, "risks_count": len(risks)},
    )
    _log(f"Loaded {total} controls and {len(risks)} risks")
    _log(f"Starting AI analysis with concurrency=2…")
    await _update_progress(
        pool, job.id, 1,
        {"status": "running", "total_controls": total, "risks_scanned": len(risks),
         "mappings_created": 0, "mappings_skipped": 0, "errors": 0, "log": log_lines,
         "current_control": None, "idx": 0}
    )

    sem = asyncio.Semaphore(2)
    state = {"done": 0, "created": mappings_created, "skipped": mappings_skipped, "errors": errors}
    state_lock = asyncio.Lock()

    async def _process_one(idx: int, c) -> None:
        local_created = 0
        local_skipped = 0
        local_errors = 0
        try:
            user_msg = BULK_LINK_CONTROL_USER.format(
                control_code=c.control_code,
                control_name=c.control_name or "",
                control_category_code=c.control_category_code or "",
                description=(c.description or "")[:400],
                tags=c.tags or "",
                framework_code=c.framework_code,
                risk_count=len(risks_data),
                risks_json=json.dumps(risks_data[:100]),
            )
            raw = await service._llm_call(provider, BULK_LINK_SYSTEM, user_msg)
            matches = _parse_json_array(raw)
            if not isinstance(matches, list):
                matches = []

            for match in matches:
                r_id = str(match.get("risk_id", ""))
                link_type = match.get("link_type", "related")
                confidence = float(match.get("confidence", 0))
                if not r_id or confidence < 0.7:
                    continue
                if link_type not in {"mitigating", "compensating", "related"}:
                    link_type = "related"
                if not dry_run:
                    async with pool.acquire() as conn:
                        inserted = await repo.create_mapping_if_not_exists(
                            conn,
                            mapping_id=str(uuid.uuid4()),
                            risk_id=r_id,
                            control_id=c.control_id,
                            link_type=link_type,
                            notes=f"AI proposed (confidence: {confidence:.0%})",
                            created_by=user_id,
                            approval_status="pending",
                            ai_confidence=round(confidence * 100, 1),
                            ai_rationale=str(match.get("rationale", ""))[:500],
                        )
                    if inserted:
                        local_created += 1
                    else:
                        local_skipped += 1
                else:
                    local_created += 1
        except Exception as exc:  # noqa: BLE001
            _logger.warning("Bulk link error for control %s: %s", c.control_code, exc)
            local_errors += 1

        async with state_lock:
            state["created"] += local_created
            state["skipped"] += local_skipped
            state["errors"] += local_errors
            state["done"] += 1
            done = state["done"]
            pct = max(1, min(99, int((done / total) * 98) + 1))
            if local_errors:
                _log(f"[{done}/{total}] {c.control_code}: error")
            else:
                _log(f"[{done}/{total}] {c.control_code}: {local_created} created, {local_skipped} existed")
            snapshot = {
                "status": "running", "total_controls": total, "risks_scanned": len(risks),
                "mappings_created": state["created"], "mappings_skipped": state["skipped"],
                "errors": state["errors"], "log": list(log_lines),
                "current_control": c.control_code, "idx": done,
            }
        await _update_progress(pool, job.id, pct, snapshot)

    async def _bounded(idx: int, c) -> None:
        async with sem:
            await _process_one(idx, c)

    await asyncio.gather(*[_bounded(i, c) for i, c in enumerate(controls)])

    mappings_created = state["created"]
    mappings_skipped = state["skipped"]
    errors = state["errors"]

    await _complete_job(pool, job.id, {
        "total_controls": total,
        "risks_scanned": len(risks),
        "mappings_created": mappings_created,
        "mappings_skipped": mappings_skipped,
        "errors": errors,
        "dry_run": dry_run,
    })


async def _update_progress(pool, job_id: str, pct: int, output: dict | None = None) -> None:
    try:
        async with pool.acquire() as conn:
            if output is not None:
                await conn.execute(
                    f"UPDATE {_JOBS} SET progress_pct = $1, output_json = $2::jsonb, updated_at = NOW() WHERE id = $3::uuid",
                    pct,
                    json.dumps(output),
                    job_id,
                )
            else:
                await conn.execute(
                    f"UPDATE {_JOBS} SET progress_pct = $1, updated_at = NOW() WHERE id = $2::uuid",
                    pct,
                    job_id,
                )
    except Exception:  # noqa: BLE001
        pass


async def _complete_job(pool, job_id: str, output: dict) -> None:
    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            UPDATE {_JOBS}
            SET status_code = 'completed', progress_pct = 100,
                output_json = $1::jsonb, updated_at = NOW()
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
            SET status_code = 'failed', error_message = $1, updated_at = NOW()
            WHERE id = $2::uuid
            """,
            error_message,
            job_id,
        )
