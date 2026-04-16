"""
FastAPI routes for the Framework Builder agent.
Prefix: /api/v1/ai/framework-builder

Routes:
  POST   /sessions                          Create a new builder session
  GET    /sessions                          List user's sessions (history)
  GET    /sessions/{id}                     Get session detail
  PATCH  /sessions/{id}                     Update context/attachments/overrides
  POST   /sessions/{id}/enqueue-hierarchy   Enqueue Phase 1 hierarchy job (async, survives navigation)
  POST   /sessions/{id}/enqueue-controls    Enqueue Phase 2 controls job (async, survives navigation)
  GET    /sessions/{id}/stream/hierarchy    SSE Phase 1 (legacy, kept for backwards compat)
  GET    /sessions/{id}/stream/controls     SSE Phase 2 (legacy, kept for backwards compat)
  POST   /sessions/{id}/create             Enqueue Phase 3 background creation job
  GET    /sessions/{id}/stream/enhance      SSE Enhance (legacy, kept for backwards compat)
  POST   /sessions/{id}/enqueue-enhance     Enqueue enhance diff as background job
  POST   /sessions/{id}/apply              Enqueue apply-changes background job (enhance mode)
  GET    /sessions/{id}/job                Poll job status
  POST   /gap-analysis                     Enqueue gap analysis for any framework
  GET    /jobs/{job_id}                    Poll any builder job by ID
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Annotated, AsyncGenerator

from fastapi import Depends, File, Query, Request, UploadFile
from fastapi.responses import StreamingResponse

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.framework_builder.router")

_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_svc_module = import_module("backend.20_ai.21_framework_builder.service")
_schemas_module = import_module("backend.20_ai.21_framework_builder.schemas")
_deps_module = import_module("backend.20_ai.21_framework_builder.dependencies")
_agent_module = import_module("backend.20_ai.21_framework_builder.agent")
_pageindex_module = import_module("backend.20_ai.03_memory.pageindex")

InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims
FrameworkBuilderService = _svc_module.FrameworkBuilderService
CreateSessionRequest = _schemas_module.CreateSessionRequest
PatchSessionRequest = _schemas_module.PatchSessionRequest
CreateFrameworkFromSessionRequest = _schemas_module.CreateFrameworkFromSessionRequest
ApplyEnhancementsRequest = _schemas_module.ApplyEnhancementsRequest
GapAnalysisRequest = _schemas_module.GapAnalysisRequest
SessionResponse = _schemas_module.SessionResponse
SessionListResponse = _schemas_module.SessionListResponse
BuildJobStatusResponse = _schemas_module.BuildJobStatusResponse
get_framework_builder_service = _deps_module.get_framework_builder_service
FrameworkBuilderAgent = _agent_module.FrameworkBuilderAgent

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/framework-builder",
    tags=["ai-framework-builder"],
)


def _sse_bytes(event_type: str, data: dict) -> bytes:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()


# ── Activity log persistence helpers ─────────────────────────────────────────

_LOG_FLUSH_THRESHOLD = 1  # flush every event so DB always has latest (survives navigation)


def _buffer_sse_event(chunk: str, buffer: list[dict]) -> None:
    """Parse an SSE chunk and append it to the in-memory buffer."""
    for line in chunk.strip().split("\n"):
        if not line.startswith("data: "):
            continue
        try:
            data = json.loads(line[6:])
        except Exception:
            continue
        buffer.append(data)


async def _flush_log_buffer(
    service: FrameworkBuilderService,
    session_id: str,
    tenant_key: str,
    buffer: list[dict],
) -> None:
    """Flush buffered events to the session's activity_log column, then clear buffer."""
    if not buffer:
        return
    try:
        await service.append_activity_log(
            session_id=session_id, tenant_key=tenant_key, events=list(buffer),
        )
    except Exception as exc:
        _logger.warning("flush_activity_log failed: %s", exc)
    buffer.clear()


# ── Sessions CRUD ─────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SessionResponse, status_code=201)
async def create_session(
    payload: CreateSessionRequest,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SessionResponse:
    """Create a new framework builder session."""
    return await service.create_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions(
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    scope_org_id: str | None = Query(default=None),
    scope_workspace_id: str | None = Query(default=None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SessionListResponse:
    """List all builder sessions for the current user."""
    return await service.list_sessions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        scope_org_id=scope_org_id,
        scope_workspace_id=scope_workspace_id,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SessionResponse:
    return await service.get_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
async def patch_session(
    session_id: str,
    payload: PatchSessionRequest,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SessionResponse:
    """Update context, attachments, or node overrides on an existing session."""
    return await service.patch_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        request=payload,
    )


# ── Phase 1: Stream Hierarchy (SSE) ──────────────────────────────────────────

@router.get("/sessions/{session_id}/stream/hierarchy")
async def stream_hierarchy(
    session_id: str,
    request: Request,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> StreamingResponse:
    """
    SSE stream — Phase 1: analyzes uploaded documents and proposes requirement hierarchy.
    No DB writes to GRC tables. Saves result to session after completion.
    """
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )
    existing_risks = await _fetch_existing_risks(request, claims.tenant_key, claims.subject)

    agent = await _build_agent(request, claims)

    # Mark session as streaming and clear prior activity log
    await service.update_session_status(
        session_id=session_id, tenant_key=claims.tenant_key, status="phase1_streaming",
    )
    await service.clear_activity_log(session_id=session_id, tenant_key=claims.tenant_key)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        hierarchy_data: dict | None = None
        log_buffer: list[dict] = []
        try:
            async for chunk in agent.stream_hierarchy(
                framework_name=session.framework_name or "",
                framework_type_code=session.framework_type_code or "custom",
                framework_category_code=session.framework_category_code or "security",
                user_context=session.user_context or "",
                attachment_ids=session.attachment_ids or [],
                existing_risks=existing_risks,
            ):
                yield chunk.encode()
                # Buffer SSE events for persistence
                _buffer_sse_event(chunk, log_buffer)
                if len(log_buffer) >= _LOG_FLUSH_THRESHOLD:
                    await _flush_log_buffer(service, session_id, claims.tenant_key, log_buffer)
                if "phase1_complete" in chunk:
                    try:
                        data = json.loads(chunk.split("data: ", 1)[1])
                        hierarchy_data = data.get("hierarchy")
                    except Exception:
                        pass
        except Exception as exc:
            _logger.exception("stream_hierarchy failed: %s", exc)
            yield _sse_bytes("error", {"message": str(exc)})
            return
        finally:
            await _flush_log_buffer(service, session_id, claims.tenant_key, log_buffer)

        # Save Phase 1 result directly — happens after last yield, before generator closes
        if hierarchy_data:
            try:
                await service.save_phase1_result(
                    session_id=session_id,
                    tenant_key=claims.tenant_key,
                    hierarchy=hierarchy_data,
                )
            except Exception as exc:
                _logger.warning("save_phase1_result failed: %s", exc)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Phase 2: Stream Controls + Risks (SSE) ───────────────────────────────────

@router.get("/sessions/{session_id}/stream/controls")
async def stream_controls(
    session_id: str,
    request: Request,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> StreamingResponse:
    """
    SSE stream — Phase 2: generates controls and maps to risks.
    No DB writes to GRC tables. Saves result to session after completion.
    """
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )
    if not session.proposed_hierarchy:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Run Phase 1 (stream/hierarchy) first")

    # Fetch existing global risks for mapping reference
    existing_risks = await _fetch_existing_risks(request, claims.tenant_key, claims.subject)

    agent = await _build_agent(request, claims)

    # Mark session as streaming and clear prior activity log
    await service.update_session_status(
        session_id=session_id, tenant_key=claims.tenant_key, status="phase2_streaming",
    )
    await service.clear_activity_log(session_id=session_id, tenant_key=claims.tenant_key)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        all_controls: list = []
        new_risks: list = []
        risk_mappings: list = []
        log_buffer: list[dict] = []

        try:
            async for chunk in agent.stream_controls_and_risks(
                framework_name=session.framework_name or "",
                framework_type_code=session.framework_type_code or "custom",
                hierarchy=session.proposed_hierarchy or {},
                node_overrides=session.node_overrides or {},
                user_context=session.user_context or "",
                attachment_ids=session.attachment_ids or [],
                existing_risks=existing_risks,
            ):
                yield chunk.encode()
                _buffer_sse_event(chunk, log_buffer)
                if len(log_buffer) >= _LOG_FLUSH_THRESHOLD:
                    await _flush_log_buffer(service, session_id, claims.tenant_key, log_buffer)
                # Capture phase2_complete payload for persistence
                if "phase2_complete" in chunk:
                    try:
                        data = json.loads(chunk.split("data: ", 1)[1])
                        all_controls = data.get("all_controls", [])
                        new_risks = data.get("new_risks", [])
                        risk_mappings = data.get("risk_mappings", [])
                    except Exception:
                        pass
        except Exception as exc:
            _logger.exception("stream_controls failed: %s", exc)
            yield _sse_bytes("error", {"message": str(exc)})
            return
        finally:
            await _flush_log_buffer(service, session_id, claims.tenant_key, log_buffer)

        if all_controls:
            try:
                await service.save_phase2_result(
                    session_id=session_id,
                    tenant_key=claims.tenant_key,
                    controls=all_controls,
                    risks=new_risks,
                    risk_mappings=risk_mappings,
                )
            except Exception as exc:
                _logger.warning("save_phase2_result failed: %s", exc)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Phase 1: Enqueue Hierarchy Job (async, survives navigation) ───────────────

@router.post("/sessions/{session_id}/enqueue-hierarchy", response_model=BuildJobStatusResponse, status_code=202)
async def enqueue_hierarchy(
    session_id: str,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Enqueue Phase 1 hierarchy generation as a background job. User can navigate away."""
    return await service.enqueue_hierarchy(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


# ── Phase 2: Enqueue Controls Job (async, survives navigation) ───────────────

@router.post("/sessions/{session_id}/enqueue-controls", response_model=BuildJobStatusResponse, status_code=202)
async def enqueue_controls(
    session_id: str,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Enqueue Phase 2 control generation as a background job. User can navigate away."""
    return await service.enqueue_controls(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


# ── Phase 3: Enqueue Creation Job ─────────────────────────────────────────────

@router.post("/sessions/{session_id}/create", response_model=BuildJobStatusResponse, status_code=202)
async def create_framework(
    session_id: str,
    payload: CreateFrameworkFromSessionRequest,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """
    Final approval — enqueues the Phase 3 background job to write everything to DB.
    User can navigate away and return; job persists.
    """
    return await service.enqueue_create_framework(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        request=payload,
    )


# ── Enhance Mode: Stream Diff (SSE) ──────────────────────────────────────────

@router.get("/sessions/{session_id}/stream/enhance")
async def stream_enhance(
    session_id: str,
    request: Request,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> StreamingResponse:
    """
    SSE stream — Enhance mode: reads existing framework, streams diff proposals.
    No DB writes until user approves and calls /apply.
    """
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )
    if session.session_type != "enhance" or not session.framework_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Session must be type='enhance' with a framework_id")

    framework_data = await _fetch_full_framework(request, session.framework_id, claims.tenant_key)
    existing_risks = await _fetch_existing_risks(request, claims.tenant_key, claims.subject)
    agent = await _build_agent(request, claims)

    # Mark session as streaming and clear prior activity log
    await service.update_session_status(
        session_id=session_id, tenant_key=claims.tenant_key, status="phase1_streaming",
    )
    await service.clear_activity_log(session_id=session_id, tenant_key=claims.tenant_key)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        proposals: list = []
        log_buffer: list[dict] = []
        try:
            async for chunk in agent.stream_enhance_diff(
                framework_data=framework_data,
                existing_risks=existing_risks,
                user_context=session.user_context or "",
                attachment_ids=session.attachment_ids or [],
            ):
                yield chunk.encode()
                _buffer_sse_event(chunk, log_buffer)
                if len(log_buffer) >= _LOG_FLUSH_THRESHOLD:
                    await _flush_log_buffer(service, session_id, claims.tenant_key, log_buffer)
                if "enhance_complete" in chunk:
                    try:
                        data = json.loads(chunk.split("data: ", 1)[1])
                        proposals = data.get("proposals", [])
                    except Exception:
                        pass
        except Exception as exc:
            _logger.exception("stream_enhance failed: %s", exc)
            yield _sse_bytes("error", {"message": str(exc)})
            return
        finally:
            await _flush_log_buffer(service, session_id, claims.tenant_key, log_buffer)

        if proposals:
            try:
                await service.save_enhance_diff(
                    session_id=session_id,
                    tenant_key=claims.tenant_key,
                    diff=proposals,
                )
            except Exception as exc:
                _logger.warning("save_enhance_diff failed: %s", exc)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Enhance Mode: Enqueue Diff Job ────────────────────────────────────────────

@router.post("/sessions/{session_id}/enqueue-enhance", response_model=BuildJobStatusResponse, status_code=202)
async def enqueue_enhance(
    session_id: str,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Enqueue enhance diff analysis as a background job (survives navigation)."""
    return await service.enqueue_enhance_diff(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


# ── Enhance Mode: Apply Changes ───────────────────────────────────────────────

@router.post("/sessions/{session_id}/apply", response_model=BuildJobStatusResponse, status_code=202)
async def apply_changes(
    session_id: str,
    payload: ApplyEnhancementsRequest,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Apply user-accepted enhance-mode changes as a background job."""
    return await service.enqueue_apply_changes(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        request=payload,
    )


# ── Poll Job Status ───────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/job", response_model=BuildJobStatusResponse)
async def get_session_job(
    session_id: str,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Poll the Phase 3 job status for a session."""
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )
    if not session.job_id:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="No background job found for this session")
    return await service.get_job_status(
        user_id=claims.subject, tenant_key=claims.tenant_key, job_id=session.job_id,
    )


@router.get("/jobs/{job_id}", response_model=BuildJobStatusResponse)
async def get_job(
    job_id: str,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Poll any framework builder job by ID."""
    return await service.get_job_status(
        user_id=claims.subject, tenant_key=claims.tenant_key, job_id=job_id,
    )


# ── Attachment Upload ─────────────────────────────────────────────────────────

@router.post("/attachments", status_code=201)
async def upload_builder_attachment(
    request: Request,
    file: Annotated[UploadFile, File(description="Document to attach (PDF, DOCX, TXT, MD, etc.)")],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> dict:
    """
    Upload a document for use with the framework builder.
    Extracts text and stores in 20_ai.19_fct_attachments so the builder agent can read it.
    Returns attachment ID to include in session attachment_ids.
    """
    _chunker_module = import_module("backend.20_ai.03_memory.chunker")

    file_bytes = await file.read()
    filename = file.filename or "document"
    content_type = file.content_type or "application/octet-stream"
    file_size = len(file_bytes)

    # Extract text from the uploaded file
    try:
        extracted_text = _chunker_module.extract_text(file_bytes, content_type, filename)
        status = "ready"
    except Exception as exc:
        _logger.warning("attachment_text_extraction_failed filename=%s: %s", filename, exc)
        extracted_text = ""
        status = "failed"

    pool = request.app.state.database_pool._pool
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO "20_ai"."19_fct_attachments"
                (tenant_key, user_id, filename, content_type, file_size_bytes, extracted_text, status_code)
            VALUES ($1, $2::uuid, $3, $4, $5, $6, $7)
            RETURNING id::text, filename, file_size_bytes, status_code
            """,
            claims.tenant_key, claims.subject, filename, content_type,
            file_size, extracted_text, status,
        )

    return {
        "id": row["id"],
        "filename": row["filename"],
        "file_size_bytes": row["file_size_bytes"],
        "status_code": row["status_code"],
    }


# ── Gap Analysis ──────────────────────────────────────────────────────────────

@router.post("/gap-analysis", response_model=BuildJobStatusResponse, status_code=202)
async def run_gap_analysis(
    payload: GapAnalysisRequest,
    service: Annotated[FrameworkBuilderService, Depends(get_framework_builder_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> BuildJobStatusResponse:
    """Enqueue a gap analysis for any framework. Returns job_id to poll."""
    return await service.enqueue_gap_analysis(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

async def _build_agent(request: Request, claims) -> FrameworkBuilderAgent:
    """Resolve LLM config and build the agent."""
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")

    config_repo = _config_repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=request.app.state.database_pool,
        settings=request.app.state.settings,
    )
    llm_config = await resolver.resolve(
        agent_type_code="framework_builder",
        org_id=None,
    )
    return FrameworkBuilderAgent(
        llm_config=llm_config,
        settings=request.app.state.settings,
        pool=request.app.state.database_pool._pool,
    )


async def _fetch_existing_risks(request: Request, tenant_key: str, user_id: str) -> list[dict]:
    """Fetch top 200 global risks for risk mapping context."""
    try:
        pool = request.app.state.database_pool._pool
        async with pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT gr.id::text, gr.risk_code, gr.risk_category_code,
                       p_title.property_value AS title
                FROM "05_grc_library"."50_fct_global_risks" gr
                LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
                    ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
                WHERE gr.tenant_key = $1 AND gr.is_active = TRUE AND gr.is_deleted = FALSE
                ORDER BY gr.risk_code
                LIMIT 200
                """,
                tenant_key,
            )
        return [dict(r) for r in rows]
    except Exception:
        return []


async def _fetch_full_framework(request: Request, framework_id: str, tenant_key: str) -> dict:
    """Load full framework data for enhance mode analysis."""
    pool = request.app.state.database_pool._pool
    async with pool.acquire() as conn:
        fw = await conn.fetchrow(
            """
            SELECT f.id::text, f.framework_code, f.framework_type_code, f.framework_category_code,
                   p_name.property_value AS name, p_desc.property_value AS description,
                   p_accept.property_value AS acceptance_criteria
            FROM "05_grc_library"."10_fct_frameworks" f
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
                ON p_name.framework_id = f.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_desc
                ON p_desc.framework_id = f.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_accept
                ON p_accept.framework_id = f.id AND p_accept.property_key = 'acceptance_criteria'
            WHERE f.id = $1 AND f.tenant_key = $2
            """,
            framework_id, tenant_key,
        )
        reqs = await conn.fetch(
            """
            SELECT r.id::text, r.requirement_code AS code, r.parent_requirement_id::text,
                   r.sort_order,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_accept.property_value AS acceptance_criteria
            FROM "05_grc_library"."12_fct_requirements" r
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_name
                ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_desc
                ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_accept
                ON p_accept.requirement_id = r.id AND p_accept.property_key = 'acceptance_criteria'
            WHERE r.framework_id = $1
            ORDER BY r.sort_order
            """,
            framework_id,
        )
        ctrls = await conn.fetch(
            """
            SELECT c.id::text, c.control_code AS code, c.requirement_id::text,
                   r.requirement_code AS requirement_code,
                   c.control_type, c.criticality_code, c.automation_potential,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_guidance.property_value AS guidance,
                   p_ig.property_value AS implementation_guidance,
                   p_tags.property_value AS tags,
                   p_accept.property_value AS acceptance_criteria
            FROM "05_grc_library"."13_fct_controls" c
            LEFT JOIN "05_grc_library"."12_fct_requirements" r
                ON r.id = c.requirement_id
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
                ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guidance
                ON p_guidance.control_id = c.id AND p_guidance.property_key = 'guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_ig
                ON p_ig.control_id = c.id AND p_ig.property_key = 'implementation_guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_tags
                ON p_tags.control_id = c.id AND p_tags.property_key = 'tags'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_accept
                ON p_accept.control_id = c.id AND p_accept.property_key = 'acceptance_criteria'
            WHERE c.framework_id = $1
            """,
            framework_id,
        )
        risk_links = await conn.fetch(
            """
            SELECT lrc.control_id::text, lrc.global_risk_id::text, lrc.mapping_type AS coverage_type,
                   gr.risk_code,
                   p_title.property_value AS risk_title
            FROM "05_grc_library"."61_lnk_global_risk_control_mappings" lrc
            JOIN "05_grc_library"."50_fct_global_risks" gr ON gr.id = lrc.global_risk_id
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
                ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
            WHERE lrc.control_id = ANY(
                SELECT id FROM "05_grc_library"."13_fct_controls" WHERE framework_id = $1
            )
            """,
            framework_id,
        )

    return {
        "id": fw["id"] if fw else framework_id,
        "name": fw["name"] if fw else "",
        "framework_code": fw["framework_code"] if fw else "",
        "framework_type_code": fw["framework_type_code"] if fw else "",
        "framework_category_code": fw["framework_category_code"] if fw else "",
        "description": fw["description"] if fw else "",
        "acceptance_criteria": fw["acceptance_criteria"] if fw else "",
        "requirements": [dict(r) for r in reqs],
        "controls": [dict(c) for c in ctrls],
        "risk_mappings": [dict(r) for r in risk_links],
    }
