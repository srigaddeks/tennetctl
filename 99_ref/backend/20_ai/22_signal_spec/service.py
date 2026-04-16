"""
SignalSpecService — orchestrates spec session CRUD, job enqueuing, and approval.
"""

from __future__ import annotations

import json
import uuid
from importlib import import_module

from .repository import SpecSessionRepository
from .schemas import (
    ApproveSpecRequest,
    CreateSpecSessionRequest,
    SpecJobStatusResponse,
    SpecSessionListResponse,
    SpecSessionResponse,
    UpdateMarkdownRequest,
    UpdateMarkdownResponse,
)

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_time_module = import_module("backend.01_core.time_utils")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_JOBS = '"20_ai"."45_fct_job_queue"'
_DATASETS = '"15_sandbox"."21_fct_datasets"'
_DATASET_RECORDS = '"15_sandbox"."43_dtl_dataset_records"'
_DATASET_PROPS = '"15_sandbox"."42_dtl_dataset_properties"'
_SIGNALS = '"15_sandbox"."22_fct_signals"'
_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'


@instrument_class_methods(
    namespace="ai.signal_spec.service",
    logger_name="backend.ai.signal_spec.instrumentation",
)
class SignalSpecService:
    def __init__(self, *, settings, database_pool: DatabasePool) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._repository = SpecSessionRepository()
        self._logger = get_logger("backend.ai.signal_spec")

    async def _require_session_permission(
        self,
        conn,
        *,
        user_id: str,
        action: str,
        row: dict,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            action,
            scope_org_id=row.get("org_id"),
            scope_workspace_id=row.get("workspace_id"),
        )

    # ── Sessions CRUD ──────────────────────────────────────────────────────────

    async def create_session(
        self, *, user_id: str, tenant_key: str, request: CreateSpecSessionRequest
    ) -> SpecSessionResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "sandbox.create",
                scope_org_id=request.org_id,
                scope_workspace_id=request.workspace_id,
            )
            row = await self._repository.create_session(
                conn,
                session_id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                connector_type_code=request.connector_type_code,
                source_dataset_id=request.source_dataset_id,
                now=now,
            )
        return _session_response(row)

    async def get_session(
        self, *, user_id: str, tenant_key: str, session_id: str
    ) -> SpecSessionResponse:
        async with self._database_pool.acquire() as conn:
            row = await self._repository.get_by_id(conn, session_id, tenant_key)
            if row:
                await self._require_session_permission(
                    conn,
                    user_id=user_id,
                    action="sandbox.view",
                    row=row,
                )
        if not row:
            raise NotFoundError(f"Signal spec session '{session_id}' not found")
        return _session_response(row)

    async def list_sessions(
        self, *, user_id: str, tenant_key: str, limit: int = 50, offset: int = 0
    ) -> SpecSessionListResponse:
        async with self._database_pool.acquire() as conn:
            rows, total = await self._repository.list_sessions(
                conn, tenant_key=tenant_key, user_id=user_id, limit=limit, offset=offset,
            )
            filtered_rows = []
            for row in rows:
                try:
                    await self._require_session_permission(
                        conn,
                        user_id=user_id,
                        action="sandbox.view",
                        row=row,
                    )
                except AuthorizationError:
                    continue
                filtered_rows.append(row)
        return SpecSessionListResponse(
            items=[_session_response(r) for r in filtered_rows],
            total=min(total, len(filtered_rows)),
        )

    async def save_spec_result(
        self,
        *,
        session_id: str,
        tenant_key: str,
        spec: dict,
        feasibility_result: dict | None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.save_spec(
                conn, session_id,
                spec=spec,
                feasibility_result=feasibility_result,
                now=now,
            )

    async def append_turn(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.append_turn(
                conn, session_id,
                turn={"role": role, "content": content},
                now=now,
            )

    async def update_markdown(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
        request: UpdateMarkdownRequest,
    ) -> UpdateMarkdownResponse:
        """
        Accept edited Markdown, parse it back into spec JSON, save to session.
        Returns updated spec JSON + the canonical markdown + parse warnings.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            row = await self._repository.get_by_id(conn, session_id, tenant_key)
        if not row:
            raise NotFoundError(f"Session '{session_id}' not found")

        spec_json, warnings = _parse_markdown_spec(request.markdown)

        # Preserve existing non-markdown fields from current spec
        current_spec = row.get("current_spec") or {}
        if current_spec:
            for key in ("signal_code", "connector_type_code", "dataset_fields_used",
                        "ssf_mapping", "feasibility"):
                if key in current_spec and key not in spec_json:
                    spec_json[key] = current_spec[key]

        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.save_spec(
                conn, session_id,
                spec=spec_json,
                feasibility_result=row.get("feasibility_result"),
                now=now,
            )

        return UpdateMarkdownResponse(
            session_id=session_id,
            spec_json=spec_json,
            markdown=request.markdown,
            parse_warnings=warnings,
        )

    # ── Approval ───────────────────────────────────────────────────────────────

    async def approve_spec(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
        request: ApproveSpecRequest,
    ) -> SpecJobStatusResponse:
        """
        Lock spec and enqueue test dataset generation.
        Returns 422 if feasibility is infeasible.
        """
        async with self._database_pool.acquire() as conn:
            row = await self._repository.get_by_id(conn, session_id, tenant_key)
            if row:
                await self._require_session_permission(
                    conn,
                    user_id=user_id,
                    action="sandbox.create",
                    row=row,
                )

        if not row:
            raise NotFoundError(f"Session '{session_id}' not found")

        spec = row.get("current_spec")
        if not spec:
            raise ValidationError("No spec generated yet — generate a spec first")

        feasibility = row.get("feasibility_result") or spec.get("feasibility") or {}
        feas_status = feasibility.get("status", "unknown")
        feas_confidence = feasibility.get("confidence", "unknown")

        # Gate 1: Feasibility check
        if feas_status == "infeasible":
            missing = feasibility.get("missing_fields", [])
            issues = feasibility.get("blocking_issues", [])
            raise ValidationError(
                f"Signal is infeasible — cannot approve. "
                f"Missing fields: {[f.get('field_path') for f in missing]}. "
                f"Issues: {issues}"
            )

        # Gate 2: Data sufficiency check from spec
        data_suff = spec.get("data_sufficiency", {})
        if data_suff.get("status") == "insufficient":
            raise ValidationError(
                f"Data insufficient — cannot approve. "
                f"Missing fields: {data_suff.get('missing_fields', [])}. "
                f"Notes: {data_suff.get('notes', '')}"
            )

        # Gate 3: Low confidence warning (allow but log)
        if feas_confidence == "low":
            self._logger.warning(
                "approve_spec: approving with LOW confidence for session %s", session_id
            )

        # Create signal record from spec
        signal_id = await self._create_signal_from_spec(
            user_id=user_id,
            tenant_key=tenant_key,
            org_id=row.get("org_id"),
            workspace_id=row.get("workspace_id"),
            spec=spec,
        )

        # Enqueue test dataset gen job
        job_id = str(uuid.uuid4())
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {_JOBS} (
                    id, tenant_key, user_id, org_id, workspace_id,
                    agent_type_code,
                    job_type, status_code, priority_code, scheduled_at,
                    input_json, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid,
                    'signal_generate',
                    'signal_test_dataset_gen', 'queued', $6, NOW(),
                    $7::jsonb, NOW(), NOW()
                )
                """,
                job_id, tenant_key, user_id,
                row.get("org_id"), row.get("workspace_id"),
                request.priority_code,
                json.dumps({
                    "signal_id": signal_id,
                    "session_id": session_id,
                    "source_dataset_id": row.get("source_dataset_id"),
                    "connector_type_code": row.get("connector_type_code"),
                    "spec": spec,
                    "auto_compose_threats": request.auto_compose_threats,
                    "auto_build_library": request.auto_build_library,
                }),
            )
            await self._repository.set_job(conn, session_id, job_id=job_id, status="approved", now=now)
            await self._repository.set_signal_id(conn, session_id, signal_id=signal_id, now=now)

            # Mark spec as locked in signal EAV
            await conn.execute(
                f"""
                INSERT INTO {_SIGNAL_PROPS} (id, signal_id, property_key, property_value)
                VALUES (gen_random_uuid(), $1::uuid, 'signal_spec_locked', 'true'),
                       (gen_random_uuid(), $1::uuid, 'signal_spec', $2)
                ON CONFLICT (signal_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                signal_id, json.dumps(spec),
            )

        self._logger.info(
            "signal_spec.approved",
            extra={"session_id": session_id, "signal_id": signal_id, "job_id": job_id},
        )

        return SpecJobStatusResponse(
            job_id=job_id,
            status="queued",
            job_type="signal_test_dataset_gen",
            signal_id=signal_id,
        )

    async def retry_pipeline_step(
        self, *, signal_id: str, step: str, user_id: str, org_id: str
    ) -> dict:
        """Reset a failed/completed pipeline job to queued so the worker picks it up again.

        Tries failed first, then completed. If no job exists at all, creates a new one
        from the signal's stored spec so the pipeline can always be re-triggered.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute", scope_org_id=org_id)

            # Try failed first, then running (stuck), then completed — all retryable
            for status in ("failed", "running", "completed"):
                row = await conn.fetchrow(
                    f"""
                    UPDATE {_JOBS}
                    SET status_code = 'queued', error_message = NULL, retry_count = 0,
                        scheduled_at = NOW(), next_retry_at = NULL, updated_at = NOW()
                    WHERE id = (
                        SELECT id FROM {_JOBS}
                        WHERE job_type = $1
                          AND input_json->>'signal_id' = $2
                          AND status_code = $3
                        ORDER BY created_at DESC
                        LIMIT 1
                    )
                    RETURNING id::text, job_type, status_code
                    """,
                    step, signal_id, status,
                )
                if row:
                    return {"job_id": row["id"], "job_type": row["job_type"], "status": "queued"}

            # No existing job found — create a new one from signal spec
            return await self._create_retry_job(conn, signal_id=signal_id, step=step,
                                                user_id=user_id, org_id=org_id)

    async def _create_retry_job(
        self, conn, *, signal_id: str, step: str, user_id: str, org_id: str
    ) -> dict:
        """Create a brand-new pipeline job when no retryable job exists."""
        # Read signal properties
        signal_row = await conn.fetchrow(
            f'SELECT org_id::text, workspace_id::text, tenant_key FROM {_SIGNALS} WHERE id = $1::uuid',
            signal_id,
        )
        if not signal_row:
            raise NotFoundError(f"Signal {signal_id} not found")

        # Read spec from signal EAV
        spec_row = await conn.fetchrow(
            f"SELECT property_value FROM {_SIGNAL_PROPS} WHERE signal_id = $1::uuid AND property_key = 'signal_spec'",
            signal_id,
        )
        spec = json.loads(spec_row["property_value"]) if spec_row else {}

        # Read source_dataset_id from spec session (if any)
        source_dataset_id = None
        ds_row = await conn.fetchrow(
            f"SELECT property_value FROM {_SIGNAL_PROPS} WHERE signal_id = $1::uuid AND property_key = 'test_dataset_id'",
            signal_id,
        )
        if ds_row:
            source_dataset_id = ds_row["property_value"]

        job_id = str(uuid.uuid4())
        input_json = {
            "signal_id": signal_id,
            "spec": spec,
            "source_dataset_id": source_dataset_id,
        }

        await conn.execute(
            f"""
            INSERT INTO {_JOBS} (
                id, tenant_key, user_id, org_id, workspace_id,
                agent_type_code, job_type, status_code, priority_code,
                scheduled_at, input_json, created_at, updated_at
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid, $5::uuid,
                'signal_generate', $6, 'queued', 'normal',
                NOW(), $7::jsonb, NOW(), NOW()
            )
            """,
            job_id, signal_row["tenant_key"], user_id,
            signal_row["org_id"], signal_row["workspace_id"],
            step, json.dumps(input_json),
        )
        return {"job_id": job_id, "job_type": step, "status": "queued", "created": True}

    async def retry_all_failed_steps(
        self, *, signal_id: str, user_id: str, org_id: str
    ) -> list[dict]:
        """Reset ALL failed/completed pipeline jobs for a signal to queued."""
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute", scope_org_id=org_id)
            rows = await conn.fetch(
                f"""
                UPDATE {_JOBS}
                SET status_code = 'queued', error_message = NULL, retry_count = 0,
                    scheduled_at = NOW(), next_retry_at = NULL, updated_at = NOW()
                WHERE id IN (
                    SELECT DISTINCT ON (job_type) id
                    FROM {_JOBS}
                    WHERE input_json->>'signal_id' = $1
                      AND status_code IN ('failed', 'running', 'completed')
                    ORDER BY job_type, created_at DESC
                )
                RETURNING id::text, job_type, status_code
                """,
                signal_id,
            )
        if not rows:
            raise NotFoundError(f"No retryable jobs found for signal {signal_id}")
        return [{"job_id": r["id"], "job_type": r["job_type"], "status": "queued"} for r in rows]

    async def get_job_status(
        self, *, user_id: str, tenant_key: str, job_id: str
    ) -> SpecJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT id::text, status_code, job_type, error_message,
                       started_at::text, completed_at::text,
                       output_json
                FROM {_JOBS}
                WHERE id = $1 AND tenant_key = $2
                """,
                job_id, tenant_key,
            )
        if not row:
            raise NotFoundError(f"Job '{job_id}' not found")
        out = {}
        if row["output_json"]:
            try:
                out = json.loads(row["output_json"]) if isinstance(row["output_json"], str) else row["output_json"]
            except Exception:
                pass
        return SpecJobStatusResponse(
            job_id=row["id"],
            status=row["status_code"],
            job_type=row["job_type"],
            signal_id=out.get("signal_id"),
            error_message=row["error_message"],
            started_at=row["started_at"],
            completed_at=row["completed_at"],
            output_json=out if out else None,
        )

    # ── Dataset schema extraction ──────────────────────────────────────────────

    async def get_rich_schema(self, *, dataset_id: str, tenant_key: str) -> dict:
        """
        Extract rich schema from a dataset: {field_path: {type, example, nullable}}.
        Samples up to 5 real records, returns detailed field metadata.
        """
        from importlib import import_module
        tools_mod = import_module("backend.10_sandbox.13_signal_agent.tools")

        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                f"""
                SELECT record_data
                FROM {_DATASET_RECORDS}
                WHERE dataset_id = $1::uuid
                ORDER BY record_seq ASC
                LIMIT 5
                """,
                dataset_id,
            )

        records = []
        for r in rows:
            payload = r["record_data"]
            if isinstance(payload, str):
                try:
                    payload = json.loads(payload)
                except Exception:
                    continue
            if isinstance(payload, dict):
                records.append(payload)
            elif isinstance(payload, list):
                records.extend(payload[:3])

        if not records:
            return {}

        return tools_mod.AgentTools.extract_rich_schema(records, max_records=5)

    # ── Private helpers ────────────────────────────────────────────────────────

    async def _create_signal_from_spec(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        spec: dict,
    ) -> str:
        """Create a signal record in draft state from the approved spec."""
        signal_id = str(uuid.uuid4())
        signal_code = spec.get("signal_code", f"signal_{signal_id[:8]}")
        display_name = spec.get("display_name", signal_code)
        description = spec.get("description", "")
        connector_type_code = spec.get("connector_type_code", "")

        async with self._database_pool.acquire() as conn:
            # Check if signal with this code already exists in this org
            existing = await conn.fetchval(
                """
                SELECT id FROM "15_sandbox"."22_fct_signals"
                WHERE signal_code = $1 AND org_id = $2::uuid AND is_active = true
                LIMIT 1
                """,
                signal_code, org_id,
            )
            if existing:
                signal_id = str(existing)
            else:
                await conn.execute(
                    """
                    INSERT INTO "15_sandbox"."22_fct_signals" (
                        id, tenant_key, org_id, workspace_id,
                        signal_code, version_number,
                        signal_status_code,
                        is_active, timeout_ms, max_memory_mb,
                        created_by, created_at, updated_at
                    ) VALUES (
                        $1::uuid, $2, $3::uuid, $4::uuid,
                        $5, 1,
                        'draft',
                        true, 10000, 256,
                        $6::uuid, NOW(), NOW()
                    )
                    """,
                    signal_id, tenant_key,
                    org_id, workspace_id,
                    signal_code,
                    user_id,
                )

            # Write EAV properties
            props = [
                (signal_id, "name", display_name),
                (signal_id, "description", description),
            ]
            for sid, key, val in props:
                await conn.execute(
                    """
                    INSERT INTO "15_sandbox"."45_dtl_signal_properties" (id, signal_id, property_key, property_value)
                    VALUES (gen_random_uuid(), $1::uuid, $2, $3)
                    ON CONFLICT (signal_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                    """,
                    sid, key, val,
                )

        return signal_id


    async def get_signal_test_datasets(self, signal_id: str) -> list[dict]:
        """Get all AI-generated test datasets linked to a signal."""
        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT d.id::text, d.dataset_code, d.created_at::text,
                       (SELECT COUNT(*) FROM "15_sandbox"."43_dtl_dataset_records" r
                        WHERE r.dataset_id = d.id) as record_count,
                       (SELECT property_value FROM "15_sandbox"."42_dtl_dataset_properties" p
                        WHERE p.dataset_id = d.id AND p.property_key = 'name') as name
                FROM "15_sandbox"."21_fct_datasets" d
                JOIN "15_sandbox"."42_dtl_dataset_properties" link
                    ON link.dataset_id = d.id
                    AND link.property_key = 'linked_signal_id'
                    AND link.property_value = $1
                WHERE d.dataset_source_code = 'ai_generated_tests'
                ORDER BY d.created_at DESC
                """,
                signal_id,
            )
            return [dict(r) for r in rows]


def _parse_markdown_spec(markdown: str) -> tuple[dict, list[str]]:
    """
    Parse a Markdown signal spec back into a structured spec dict.
    Extracts H2/H3 sections and key: value pairs.
    Returns (spec_json, warnings).
    """
    import re
    spec: dict = {}
    warnings: list[str] = []
    current_section: str | None = None
    section_lines: list[str] = []

    _FIELD_MAP = {
        "signal code": "signal_code",
        "display name": "display_name",
        "name": "display_name",
        "description": "description",
        "intent": "intent",
        "connector type": "connector_type_code",
        "connector": "connector_type_code",
    }

    def _flush_section():
        nonlocal section_lines, current_section
        if not current_section:
            return
        text = "\n".join(section_lines).strip()
        if current_section == "description":
            spec.setdefault("description", text)
        elif current_section == "intent":
            spec.setdefault("intent", text)
        section_lines = []

    for line in markdown.splitlines():
        stripped = line.strip()

        if stripped.startswith("## ") or stripped.startswith("# "):
            _flush_section()
            heading = re.sub(r"^#+\s+", "", stripped).lower()
            current_section = heading
        elif stripped.startswith("- **") or stripped.startswith("**"):
            # Bold key-value pattern: **Key:** value
            m = re.match(r"\*?\*?([^:*]+)\*?\*?:\s*(.+)", stripped.lstrip("- "))
            if m:
                raw_key = m.group(1).strip().lower()
                val = m.group(2).strip().strip("`")
                mapped = _FIELD_MAP.get(raw_key)
                if mapped:
                    spec.setdefault(mapped, val)
        else:
            if current_section:
                section_lines.append(line)

    _flush_section()

    if not spec.get("display_name") and not spec.get("signal_code"):
        # Try to grab name from first H1/H2 heading
        for line in markdown.splitlines():
            m = re.match(r"^#+\s+(.+)", line.strip())
            if m:
                spec.setdefault("display_name", m.group(1).strip())
                break
        if not spec.get("display_name"):
            warnings.append("Could not extract display_name from Markdown")

    return spec, warnings


def _session_response(row: dict) -> SpecSessionResponse:
    return SpecSessionResponse(
        id=row["id"],
        tenant_key=row["tenant_key"],
        user_id=row["user_id"],
        org_id=row.get("org_id"),
        workspace_id=row.get("workspace_id"),
        signal_id=row.get("signal_id"),
        connector_type_code=row.get("connector_type_code"),
        source_dataset_id=row.get("source_dataset_id"),
        status=row.get("status", "drafting"),
        current_spec=row.get("current_spec"),
        feasibility_result=row.get("feasibility_result"),
        conversation_history=row.get("conversation_history") or [],
        job_id=row.get("job_id"),
        error_message=row.get("error_message"),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
    )
