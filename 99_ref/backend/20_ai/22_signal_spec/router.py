"""
FastAPI routes for the Signal Spec Agent.
Prefix: /api/v1/ai/signal-spec

Routes:
  POST   /sessions                              Create a new spec session
  GET    /sessions                              List user's sessions
  GET    /sessions/{id}                         Get session detail + current spec
  GET    /sessions/{id}/stream/generate         SSE: generate spec from prompt
  GET    /sessions/{id}/stream/refine           SSE: conversational refinement
  GET    /sessions/{id}/stream/feasibility      SSE: re-run feasibility only
  POST   /sessions/{id}/approve                 Lock spec + queue test dataset gen (422 if infeasible)
  GET    /jobs/{job_id}                         Poll pipeline job by ID
"""

from __future__ import annotations

import asyncio
import json
from importlib import import_module
from typing import Annotated, AsyncGenerator

from fastapi import Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse

_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_auth_module = import_module("backend.03_auth_manage.dependencies")
_svc_module = import_module("backend.20_ai.22_signal_spec.service")
_schemas_module = import_module("backend.20_ai.22_signal_spec.schemas")
_deps_module = import_module("backend.20_ai.22_signal_spec.dependencies")
_agent_module = import_module("backend.20_ai.22_signal_spec.agent")

_logger = _logging_module.get_logger("backend.ai.signal_spec.router")
InstrumentedAPIRouter = _telemetry_module.InstrumentedAPIRouter
get_current_access_claims = _auth_module.get_current_access_claims

SignalSpecService = _svc_module.SignalSpecService
CreateSpecSessionRequest = _schemas_module.CreateSpecSessionRequest
RefineRequest = _schemas_module.RefineRequest
ApproveSpecRequest = _schemas_module.ApproveSpecRequest
UpdateMarkdownRequest = _schemas_module.UpdateMarkdownRequest
UpdateMarkdownResponse = _schemas_module.UpdateMarkdownResponse
DataSufficiencyRequest = _schemas_module.DataSufficiencyRequest
DataSufficiencyResponse = _schemas_module.DataSufficiencyResponse
GenerateTestDatasetRequest = _schemas_module.GenerateTestDatasetRequest
GenerateTestDatasetResponse = _schemas_module.GenerateTestDatasetResponse
SpecSessionResponse = _schemas_module.SpecSessionResponse
SpecSessionListResponse = _schemas_module.SpecSessionListResponse
SpecJobStatusResponse = _schemas_module.SpecJobStatusResponse
get_signal_spec_service = _deps_module.get_signal_spec_service
SignalSpecAgent = _agent_module.SignalSpecAgent

router = InstrumentedAPIRouter(
    prefix="/api/v1/ai/signal-spec",
    tags=["ai-signal-spec"],
)


def _sse_bytes(event_type: str, data: dict) -> bytes:
    return f"event: {event_type}\ndata: {json.dumps(data)}\n\n".encode()


# ── Sessions CRUD ──────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=SpecSessionResponse, status_code=201)
async def create_session(
    payload: CreateSpecSessionRequest,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SpecSessionResponse:
    """Create a new signal spec session."""
    return await service.create_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        request=payload,
    )


@router.get("/sessions", response_model=SpecSessionListResponse)
async def list_sessions(
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SpecSessionListResponse:
    return await service.list_sessions(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        limit=limit,
        offset=offset,
    )


@router.get("/sessions/{session_id}", response_model=SpecSessionResponse)
async def get_session(
    session_id: str,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SpecSessionResponse:
    return await service.get_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
    )


# ── SSE: Generate Spec ─────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/stream/generate")
async def stream_generate(
    session_id: str,
    request: Request,
    prompt: str = Query(..., description="User's signal idea description"),
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)] = None,
    claims: Annotated[dict, Depends(get_current_access_claims)] = None,
) -> StreamingResponse:
    """
    SSE stream — generates a full signal spec from the user's prompt.
    Saves spec + feasibility result to session after completion.
    """
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )

    rich_schema = {}
    if session.source_dataset_id:
        try:
            rich_schema = await service.get_rich_schema(
                dataset_id=session.source_dataset_id,
                tenant_key=claims.tenant_key,
            )
        except Exception as exc:
            _logger.warning("stream_generate.schema_extraction_failed: %s", exc)

    agent = await _build_agent(request)

    # Fetch actual dataset records with names for grounding
    dataset_records = []
    record_names = []
    if session.source_dataset_id:
        try:
            _ds_dep = import_module("backend.10_sandbox.03_datasets.dependencies")
            ds_service = _ds_dep.get_dataset_service(request)
            recs_resp = await ds_service.get_dataset_records(
                user_id=claims.subject, dataset_id=session.source_dataset_id, limit=15,
            )
            dataset_records = [r.record_data for r in recs_resp.records]
            record_names = [r.record_name or f"record_{r.record_seq}" for r in recs_resp.records]
        except Exception as exc:
            _logger.warning("stream_generate.records_fetch_failed: %s", exc)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        final_spec = None
        final_feasibility = None
        try:
            async for chunk in agent.stream_generate(
                prompt=prompt,
                connector_type_code=session.connector_type_code or "",
                rich_schema=rich_schema,
                session_id=session_id,
                user_id=claims.subject,
                dataset_records=dataset_records,
                record_names=record_names,
            ):
                yield chunk.encode()
                if "spec_complete" in chunk:
                    try:
                        data_line = chunk.split("data: ", 1)[1].split("\n")[0]
                        data = json.loads(data_line)
                        final_spec = data.get("spec")
                        if final_spec:
                            final_feasibility = final_spec.get("feasibility")
                    except Exception as _parse_err:
                        _logger.warning("Failed to parse spec_complete SSE: %s", _parse_err)
        except Exception as exc:
            _logger.exception("stream_generate failed: %s", exc)
            yield _sse_bytes("error", {"message": str(exc)})
            return

        if final_spec:
            asyncio.create_task(service.save_spec_result(
                session_id=session_id,
                tenant_key=claims.tenant_key,
                spec=final_spec,
                feasibility_result=final_feasibility,
            ))
            asyncio.create_task(service.append_turn(
                session_id=session_id, role="user", content=prompt,
            ))
            asyncio.create_task(service.append_turn(
                session_id=session_id, role="assistant",
                content=f"Generated spec: {final_spec.get('display_name', 'signal')}",
            ))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── SSE: Refine Spec ───────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/stream/refine")
async def stream_refine(
    session_id: str,
    payload: RefineRequest,
    request: Request,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)] = None,
    claims: Annotated[dict, Depends(get_current_access_claims)] = None,
) -> StreamingResponse:
    """
    SSE stream — conversational spec refinement.
    Sends user's message, applies changes, re-checks feasibility, saves result.
    """
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )

    if not session.current_spec:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No spec exists yet — run /stream/generate first")

    rich_schema = {}
    if session.source_dataset_id:
        try:
            rich_schema = await service.get_rich_schema(
                dataset_id=session.source_dataset_id,
                tenant_key=claims.tenant_key,
            )
        except Exception as exc:
            _logger.warning("stream_refine.schema_extraction_failed: %s", exc)

    agent = await _build_agent(request)

    # Fetch dataset records for grounding
    dataset_records = []
    record_names = []
    if session.source_dataset_id:
        try:
            _ds_dep = import_module("backend.10_sandbox.03_datasets.dependencies")
            ds_service = _ds_dep.get_dataset_service(request)
            recs_resp = await ds_service.get_dataset_records(
                user_id=claims.subject, dataset_id=session.source_dataset_id, limit=15,
            )
            dataset_records = [r.record_data for r in recs_resp.records]
            record_names = [r.record_name or f"record_{r.record_seq}" for r in recs_resp.records]
        except Exception as exc:
            _logger.warning("stream_refine.records_fetch_failed: %s", exc)

    async def event_stream() -> AsyncGenerator[bytes, None]:
        updated_spec = None
        updated_feasibility = None
        try:
            async for chunk in agent.stream_refine(
                message=payload.message,
                current_spec=session.current_spec,
                connector_type_code=session.connector_type_code or "",
                rich_schema=rich_schema,
                conversation_history=session.conversation_history or [],
                session_id=session_id,
                user_id=claims.subject,
                dataset_records=dataset_records,
                record_names=record_names,
            ):
                yield chunk.encode()
                if '"spec_refined"' in chunk:
                    try:
                        data = json.loads(chunk.split("data: ", 1)[1])
                        updated_spec = data.get("spec")
                        if updated_spec:
                            updated_feasibility = updated_spec.get("feasibility")
                    except Exception:
                        pass
        except Exception as exc:
            _logger.exception("stream_refine failed: %s", exc)
            yield _sse_bytes("error", {"message": str(exc)})
            return

        if updated_spec:
            asyncio.create_task(service.save_spec_result(
                session_id=session_id,
                tenant_key=claims.tenant_key,
                spec=updated_spec,
                feasibility_result=updated_feasibility,
            ))
            asyncio.create_task(service.append_turn(
                session_id=session_id, role="user", content=payload.message,
            ))
            asyncio.create_task(service.append_turn(
                session_id=session_id, role="assistant",
                content=f"Refined spec based on: {payload.message[:100]}",
            ))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── SSE: Feasibility Only ──────────────────────────────────────────────────────

@router.get("/sessions/{session_id}/stream/feasibility")
async def stream_feasibility(
    session_id: str,
    request: Request,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)] = None,
    claims: Annotated[dict, Depends(get_current_access_claims)] = None,
) -> StreamingResponse:
    """Re-run feasibility check on the current spec (e.g. after dataset change)."""
    session = await service.get_session(
        user_id=claims.subject, tenant_key=claims.tenant_key, session_id=session_id,
    )
    if not session.current_spec:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No spec to check — run /stream/generate first")

    rich_schema = {}
    if session.source_dataset_id:
        try:
            rich_schema = await service.get_rich_schema(
                dataset_id=session.source_dataset_id,
                tenant_key=claims.tenant_key,
            )
        except Exception as exc:
            _logger.warning("stream_feasibility.schema_extraction_failed: %s", exc)

    agent = await _build_agent(request)
    fields_used = session.current_spec.get("dataset_fields_used", [])

    async def event_stream() -> AsyncGenerator[bytes, None]:
        yield _sse_bytes("feasibility_checking", {"message": "Running feasibility check..."})
        try:
            result = await agent.check_feasibility(
                fields_used=fields_used,
                rich_schema=rich_schema,
            )
        except Exception as exc:
            _logger.exception("stream_feasibility failed: %s", exc)
            yield _sse_bytes("error", {"message": str(exc)})
            return

        yield _sse_bytes("feasibility_result", {
            "status": result.get("status", "unknown"),
            "confidence": result.get("confidence", "low"),
            "missing_fields": result.get("missing_fields", []),
            "blocking_issues": result.get("blocking_issues", []),
            "notes": result.get("notes", ""),
        })

        asyncio.create_task(service.save_spec_result(
            session_id=session_id,
            tenant_key=claims.tenant_key,
            spec=session.current_spec,
            feasibility_result=result,
        ))

    return StreamingResponse(event_stream(), media_type="text/event-stream")


# ── Markdown Edit Round-trip ────────────────────────────────────────────────────

@router.patch("/sessions/{session_id}/markdown", response_model=UpdateMarkdownResponse)
async def update_markdown(
    session_id: str,
    payload: UpdateMarkdownRequest,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> UpdateMarkdownResponse:
    """
    Accept edited Markdown spec, parse back to JSON, and save to the session.
    Allows users to make manual edits in a Markdown editor and sync them back.
    """
    return await service.update_markdown(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        request=payload,
    )


# ── Data Sufficiency Check ─────────────────────────────────────────────────────

@router.post("/data-sufficiency", response_model=DataSufficiencyResponse)
async def check_data_sufficiency(
    payload: DataSufficiencyRequest,
    request: Request,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)] = None,
    claims: Annotated[dict, Depends(get_current_access_claims)] = None,
) -> DataSufficiencyResponse:
    """
    Two-phase data sufficiency check: primary analysis + independent verifier.
    Checks if dataset JSON records have the fields needed to build the signal.
    """
    _ds_module = import_module("backend.20_ai.22_signal_spec.data_sufficiency")
    _factory_mod = import_module("backend.20_ai.14_llm_providers.factory")

    # Load dataset records
    _ds_service_mod = import_module("backend.10_sandbox.03_datasets.service")
    _ds_dep_mod = import_module("backend.10_sandbox.03_datasets.dependencies")
    ds_service = _ds_dep_mod.get_dataset_service(request)

    records_response = await ds_service.get_dataset_records(
        user_id=claims.subject,
        dataset_id=payload.dataset_id,
        limit=30,
    )

    dataset_records = [r.record_data for r in records_response.records]
    record_names = [r.record_name or f"record_{r.record_seq}" for r in records_response.records]

    # Build signal requirements from description + explicit fields
    signal_requirements = {
        "signal_description": payload.signal_description,
        "required_fields": payload.required_fields,
    }

    # Get LLM provider
    agent = await _build_agent(request)
    config = agent._config
    provider = _factory_mod.get_provider(
        provider_type=config.provider_type,
        provider_base_url=config.provider_base_url,
        api_key=config.api_key,
        model_id=config.model_id,
        temperature=1.0,
    )

    # Run dual-phase check
    result = await _ds_module.check_data_sufficiency(
        provider=provider,
        signal_requirements=signal_requirements,
        dataset_records=dataset_records,
        record_names=record_names,
    )

    return DataSufficiencyResponse(**result)


# ── Generate Signal-Specific Test Dataset ──────────────────────────────────────

@router.post("/generate-test-dataset", response_model=GenerateTestDatasetResponse)
async def generate_test_dataset(
    payload: GenerateTestDatasetRequest,
    request: Request,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)] = None,
    claims: Annotated[dict, Depends(get_current_access_claims)] = None,
) -> GenerateTestDatasetResponse:
    """
    Generate a comprehensive signal-specific test dataset.
    Phase 1: AI generates varied scenarios using source record structure.
    Phase 2: Structural verification against live data.
    Saves test records to a new dataset version.
    """
    _test_gen_mod = import_module("backend.20_ai.22_signal_spec.test_dataset_gen")
    _factory_mod = import_module("backend.20_ai.14_llm_providers.factory")
    _ds_dep_mod = import_module("backend.10_sandbox.03_datasets.dependencies")

    # Load session spec
    session = await service.get_session(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=payload.session_id,
    )
    if not session.current_spec:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="No spec in session — generate a spec first")

    # Load source dataset records
    ds_service = _ds_dep_mod.get_dataset_service(request)
    recs_resp = await ds_service.get_dataset_records(
        user_id=claims.subject,
        dataset_id=payload.dataset_id,
        limit=20,
    )
    source_records = [r.record_data for r in recs_resp.records]
    record_names = [r.record_name or f"record_{r.record_seq}" for r in recs_resp.records]

    # Use sufficiency result if provided, otherwise use spec's data_sufficiency
    sufficiency = payload.sufficiency_result or session.current_spec.get("data_sufficiency", {})

    # Get LLM provider
    agent = await _build_agent(request)
    config = agent._config
    provider = _factory_mod.get_provider(
        provider_type=config.provider_type,
        provider_base_url=config.provider_base_url,
        api_key=config.api_key,
        model_id=config.model_id,
        temperature=1.0,
    )

    # Run generate + verify
    result = await _test_gen_mod.generate_and_verify(
        provider=provider,
        signal_spec=session.current_spec,
        sufficiency_result=sufficiency,
        source_records=source_records,
        record_names=record_names,
    )

    # Save test records as a new dataset (even if needs_fixes, so user can review/edit)
    if result.get("generation", {}).get("records"):
        try:
            test_records = result["generation"]["records"]
            signal_code = session.current_spec.get("signal_code", "unknown")

            # Create test dataset
            _ds_schemas = import_module("backend.10_sandbox.03_datasets.schemas")
            test_ds = await ds_service.create_dataset(
                user_id=claims.subject,
                tenant_key=claims.tenant_key,
                org_id=session.org_id or "",
                request=_ds_schemas.CreateDatasetRequest(
                    dataset_source_code="ai_generated_tests",
                    properties={
                        "name": f"Test: {signal_code}",
                        "description": f"AI-generated test dataset for signal {signal_code}. {len(test_records)} scenarios.",
                        "signal_code": signal_code,
                        "generation_type": "signal_specific_test",
                    },
                    records=test_records,
                ),
            )
            result["saved_dataset_id"] = test_ds.id
            result["saved_dataset_name"] = f"Test: {signal_code}"

            # Link test dataset to signal via EAV property
            if payload.signal_id:
                try:
                    async with request.app.state.database_pool.acquire() as conn:
                        import uuid as _uuid
                        await conn.execute(
                            """
                            INSERT INTO "15_sandbox"."45_dtl_signal_properties"
                                (id, signal_id, property_key, property_value)
                            VALUES ($1::uuid, $2::uuid, 'test_dataset_id', $3)
                            ON CONFLICT (signal_id, property_key)
                                DO UPDATE SET property_value = EXCLUDED.property_value, updated_at = now()
                            """,
                            str(_uuid.uuid4()), payload.signal_id, test_ds.id,
                        )
                    result["linked_to_signal"] = payload.signal_id
                except Exception as link_exc:
                    _logger.warning("generate_test_dataset: signal link failed: %s", link_exc)
        except Exception as exc:
            _logger.warning("generate_test_dataset: save failed: %s", exc)
            result["save_error"] = str(exc)

    return GenerateTestDatasetResponse(**result)


# ── Approve Spec ───────────────────────────────────────────────────────────────

@router.post("/sessions/{session_id}/approve", response_model=SpecJobStatusResponse, status_code=202)
async def approve_spec(
    session_id: str,
    payload: ApproveSpecRequest,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SpecJobStatusResponse:
    """
    Lock the spec and queue test dataset generation.
    Returns 422 if the spec is infeasible — must resolve feasibility issues first.
    """
    return await service.approve_spec(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        session_id=session_id,
        request=payload,
    )


# ── Job Polling ────────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=SpecJobStatusResponse)
async def get_job(
    job_id: str,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims: Annotated[dict, Depends(get_current_access_claims)],
) -> SpecJobStatusResponse:
    """Poll a signal pipeline job by ID."""
    return await service.get_job_status(
        user_id=claims.subject,
        tenant_key=claims.tenant_key,
        job_id=job_id,
    )


# ── Signal Test Datasets ──────────────────────────────────────────────────

@router.get("/signals/{signal_id}/test-datasets")
async def get_signal_test_datasets(
    signal_id: str,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims=Depends(get_current_access_claims),
) -> list[dict]:
    """Get all AI-generated test datasets for a signal."""
    return await service.get_signal_test_datasets(signal_id)


# ── Pipeline Step Retry ────────────────────────────────────────────────────────

_VALID_RETRY_STEPS = frozenset([
    "signal_test_dataset_gen",
    "signal_codegen",
    "threat_composer",
    "library_builder",
])


@router.post("/pipelines/{signal_id}/retry-step")
async def retry_pipeline_step(
    signal_id: str,
    body: dict,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> dict:
    """Reset a failed pipeline step to queued so the worker picks it up again."""
    step = body.get("step", "")
    if step not in _VALID_RETRY_STEPS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid step. Must be one of: {sorted(_VALID_RETRY_STEPS)}",
        )
    return await service.retry_pipeline_step(
        signal_id=signal_id, step=step, user_id=claims.subject, org_id=org_id,
    )


@router.post("/pipelines/{signal_id}/retry-all")
async def retry_all_failed_steps(
    signal_id: str,
    service: Annotated[SignalSpecService, Depends(get_signal_spec_service)],
    claims=Depends(get_current_access_claims),
    org_id: str = Query(...),
) -> dict:
    """Reset ALL failed pipeline steps for a signal to queued."""
    results = await service.retry_all_failed_steps(
        signal_id=signal_id, user_id=claims.subject, org_id=org_id,
    )
    return {"retried": results}


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _build_agent(request: Request) -> SignalSpecAgent:
    """Resolve LLM config and build the agent."""
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _config_repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    _tracer_mod = import_module("backend.20_ai.14_llm_providers.langfuse_tracer")

    settings = request.app.state.settings
    config_repo = _config_repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=request.app.state.database_pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(
        agent_type_code="signal_spec",
        org_id=None,
    )
    tracer = _tracer_mod.LangFuseTracer.from_settings(settings)
    return SignalSpecAgent(
        llm_config=llm_config,
        settings=settings,
        tracer=tracer,
    )
