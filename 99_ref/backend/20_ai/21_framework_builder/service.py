"""
FrameworkBuilderService — orchestrates session CRUD and job enqueuing.
"""

from __future__ import annotations

import json
import uuid
from collections import Counter
from importlib import import_module

import asyncpg

from .repository import BuilderSessionRepository
from .schemas import (
    ApplyEnhancementsRequest,
    BuildJobStatusResponse,
    CreateFrameworkFromSessionRequest,
    CreateSessionRequest,
    GapAnalysisRequest,
    PatchSessionRequest,
    SessionListResponse,
    SessionResponse,
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
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_JOBS = '"20_ai"."45_fct_job_queue"'
_SESSIONS = '"20_ai"."60_fct_builder_sessions"'
_FRAMEWORKS = '"05_grc_library"."10_fct_frameworks"'


@instrument_class_methods(
    namespace="ai.framework_builder.service",
    logger_name="backend.ai.framework_builder.instrumentation",
)
class FrameworkBuilderService:
    def __init__(self, *, settings, database_pool: DatabasePool) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._repository = BuilderSessionRepository()
        self._logger = get_logger("backend.ai.framework_builder")

    # ── Sessions ───────────────────────────────────────────────────────────────

    async def create_session(
        self, *, user_id: str, tenant_key: str, request: CreateSessionRequest
    ) -> SessionResponse:
        session_type = (request.session_type or "create").strip().lower()
        if session_type not in {"create", "enhance", "gap"}:
            raise ValidationError("session_type must be one of: create, enhance, gap")

        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            framework_id = request.framework_id
            scope_org_id = request.scope_org_id
            scope_workspace_id = request.scope_workspace_id
            framework_name = request.framework_name
            framework_type_code = request.framework_type_code
            framework_category_code = request.framework_category_code

            if not scope_org_id:
                raise ValidationError("scope_org_id is required")
            if not scope_workspace_id:
                raise ValidationError("scope_workspace_id is required")
            permission = (
                "frameworks.update"
                if session_type == "enhance"
                else "frameworks.create"
            )
            await require_permission(
                conn,
                user_id,
                permission,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )

            if session_type == "enhance":
                if not framework_id:
                    raise ValidationError(
                        "framework_id is required when session_type='enhance'"
                    )

                framework_row = await conn.fetchrow(
                    """
                    SELECT f.id::text AS id,
                           f.framework_code,
                           f.framework_type_code,
                           f.framework_category_code,
                           f.scope_org_id::text AS scope_org_id,
                           f.scope_workspace_id::text AS scope_workspace_id,
                           p_name.property_value AS name
                    FROM "05_grc_library"."10_fct_frameworks" f
                    LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
                        ON p_name.framework_id = f.id AND p_name.property_key = 'name'
                    WHERE f.id = $1::uuid
                      AND f.tenant_key = $2
                      AND f.is_active = TRUE
                      AND f.is_deleted = FALSE
                    """,
                    framework_id,
                    tenant_key,
                )
                if not framework_row:
                    raise ValidationError(
                        "framework_id does not exist or is not accessible in this tenant"
                    )

                framework_name = (
                    framework_name
                    or framework_row["name"]
                    or framework_row["framework_code"]
                )
                framework_type_code = (
                    framework_type_code or framework_row["framework_type_code"]
                )
                framework_category_code = (
                    framework_category_code or framework_row["framework_category_code"]
                )
                framework_scope_org_id = framework_row.get("scope_org_id")
                framework_scope_workspace_id = framework_row.get("scope_workspace_id")

                if not framework_scope_org_id or not framework_scope_workspace_id:
                    # Check if this is a marketplace framework that was deployed to this workspace
                    check_deployed = await conn.fetchrow(
                        """
                        SELECT d.framework_id::text AS clone_id, d.workspace_id::text AS clone_workspace_id
                        FROM "05_grc_library"."16_fct_framework_deployments" d
                        JOIN "05_grc_library"."20_dtl_framework_properties" p_fw
                          ON p_fw.framework_id = d.framework_id AND p_fw.property_key = 'source_framework_id'
                        WHERE p_fw.property_value::uuid = $1::uuid
                          AND d.org_id = $2::uuid
                          AND d.workspace_id = $3::uuid
                          AND d.deployment_status = 'active'
                        LIMIT 1
                        """,
                        framework_id,
                        scope_org_id,
                        scope_workspace_id,
                    )
                    if check_deployed:
                        # User passed marketplace framework ID but it's deployed to this workspace
                        # Get the clone ID instead
                        clone_row = await conn.fetchrow(
                            """
                            SELECT f.id::text AS id,
                                   f.framework_code,
                                   f.framework_type_code,
                                   f.framework_category_code,
                                   f.scope_org_id::text AS scope_org_id,
                                   f.scope_workspace_id::text AS scope_workspace_id,
                                   p_name.property_value AS name
                            FROM "05_grc_library"."10_fct_frameworks" f
                            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
                                ON p_name.framework_id = f.id AND p_name.property_key = 'name'
                            WHERE f.id = $1::uuid
                              AND f.tenant_key = $2
                              AND f.is_active = TRUE
                              AND f.is_deleted = FALSE
                            """,
                            check_deployed["clone_id"],
                            tenant_key,
                        )
                        if clone_row:
                            framework_id = clone_row["id"]
                            framework_row = clone_row
                            framework_name = (
                                framework_name
                                or framework_row["name"]
                                or framework_row["framework_code"]
                            )
                            framework_type_code = (
                                framework_type_code
                                or framework_row["framework_type_code"]
                            )
                            framework_category_code = (
                                framework_category_code
                                or framework_row["framework_category_code"]
                            )
                            framework_scope_org_id = framework_row.get("scope_org_id")
                            framework_scope_workspace_id = framework_row.get(
                                "scope_workspace_id"
                            )

                if not framework_scope_org_id or not framework_scope_workspace_id:
                    # For frameworks without scope, check if they have an active workspace deployment
                    # If they do, allow access (the framework is deployed to some workspace)
                    has_deployment = await conn.fetchrow(
                        """
                        SELECT 1 FROM "05_grc_library"."16_fct_framework_deployments"
                        WHERE framework_id = $1 AND workspace_id IS NOT NULL AND deployment_status = 'active'
                        """,
                        framework_id,
                    )
                    if not has_deployment:
                        raise ValidationError(
                            "Selected framework is not deployed to any workspace. Deploy it first to use with AI builder."
                        )
                elif (
                    framework_scope_org_id != scope_org_id
                    or framework_scope_workspace_id != scope_workspace_id
                ):
                    # Only check scope mismatch if framework has scope set
                    raise ValidationError(
                        f"Selected framework is deployed to a different org/workspace. Please switch to that org/workspace or use a framework deployed to the current one."
                    )

            row = await self._repository.create_session(
                conn,
                session_id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                user_id=user_id,
                session_type=session_type,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
                framework_id=framework_id,
                framework_name=framework_name,
                framework_type_code=framework_type_code,
                framework_category_code=framework_category_code,
                user_context=request.user_context,
                attachment_ids=request.attachment_ids,
                now=now,
            )
        return _session_response(row)

    async def get_session(
        self, *, user_id: str, tenant_key: str, session_id: str
    ) -> SessionResponse:
        async with self._database_pool.acquire() as conn:
            row = await self._repository.get_by_id(conn, session_id, tenant_key)
            if not row or row.get("user_id") != user_id:
                raise NotFoundError(f"Builder session '{session_id}' not found")
            scope_org_id = row.get("scope_org_id")
            scope_workspace_id = row.get("scope_workspace_id")
            if not scope_org_id or not scope_workspace_id:
                raise ValidationError(
                    "Builder session is missing org/workspace scope and cannot be accessed. Create a new scoped session."
                )
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
        return _session_response(row)

    async def list_sessions(
        self,
        *,
        user_id: str,
        tenant_key: str,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> SessionListResponse:
        if not scope_org_id or not scope_workspace_id:
            raise ValidationError(
                "scope_org_id and scope_workspace_id are required for listing builder sessions"
            )
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            rows, total = await self._repository.list_sessions(
                conn,
                tenant_key=tenant_key,
                user_id=user_id,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
                limit=limit,
                offset=offset,
            )
        return SessionListResponse(
            items=[_session_response(r) for r in rows], total=total
        )

    async def patch_session(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
        request: PatchSessionRequest,
    ) -> SessionResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            existing = await self._repository.get_by_id(conn, session_id, tenant_key)
            if not existing or existing.get("user_id") != user_id:
                raise NotFoundError(f"Builder session '{session_id}' not found")

            permission = (
                "frameworks.update"
                if existing.get("session_type") == "enhance"
                else "frameworks.create"
            )
            await require_permission(
                conn,
                user_id,
                permission,
                scope_org_id=existing.get("scope_org_id"),
                scope_workspace_id=existing.get("scope_workspace_id"),
            )

            row = await self._repository.update_patch(
                conn,
                session_id,
                tenant_key=tenant_key,
                user_id=user_id,
                user_context=request.user_context,
                attachment_ids=request.attachment_ids,
                node_overrides=request.node_overrides,
                accepted_changes=request.accepted_changes,
                proposed_hierarchy=request.proposed_hierarchy,
                proposed_controls=request.proposed_controls,
                proposed_risks=request.proposed_risks,
                proposed_risk_mappings=request.proposed_risk_mappings,
                now=now,
            )
        if not row:
            raise NotFoundError(f"Builder session '{session_id}' not found")
        return _session_response(row)

    async def update_session_status(
        self, *, session_id: str, tenant_key: str, status: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.update_status(
                conn, session_id, tenant_key=tenant_key, status=status, now=now
            )

    async def append_activity_log(
        self, *, session_id: str, tenant_key: str, events: list[dict]
    ) -> None:
        """Append SSE feed events to the session's persisted activity log."""
        if not events:
            return
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.append_activity_log(
                conn,
                session_id,
                tenant_key=tenant_key,
                events=events,
                now=now,
            )

    async def clear_activity_log(self, *, session_id: str, tenant_key: str) -> None:
        """Reset the activity log when a new streaming phase begins."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.clear_activity_log(
                conn,
                session_id,
                tenant_key=tenant_key,
                now=now,
            )

    async def save_phase1_result(
        self, *, session_id: str, tenant_key: str, hierarchy: dict
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.save_phase1(
                conn, session_id, tenant_key=tenant_key, hierarchy=hierarchy, now=now
            )
            # If the LLM returned controls/risks embedded in the hierarchy (unified call),
            # also persist them as phase2 data so Create Framework works without a separate Phase 2.
            controls = hierarchy.get("controls", [])
            risks = hierarchy.get("risks", [])
            risk_mappings = hierarchy.get("risk_mappings", [])
            if controls or risks:
                await self._repository.save_phase2(
                    conn,
                    session_id,
                    tenant_key=tenant_key,
                    controls=controls,
                    risks=risks,
                    risk_mappings=risk_mappings,
                    now=now,
                )

    async def save_phase2_result(
        self,
        *,
        session_id: str,
        tenant_key: str,
        controls: list,
        risks: list,
        risk_mappings: list,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.save_phase2(
                conn,
                session_id,
                tenant_key=tenant_key,
                controls=controls,
                risks=risks,
                risk_mappings=risk_mappings,
                now=now,
            )

    async def save_enhance_diff(
        self, *, session_id: str, tenant_key: str, diff: list
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.save_enhance_diff(
                conn, session_id, tenant_key=tenant_key, diff=diff, now=now
            )

    # ── Enqueue Phase 3: Create Framework ─────────────────────────────────────

    async def enqueue_create_framework(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
        request: CreateFrameworkFromSessionRequest,
    ) -> BuildJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            session = await self._repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "frameworks.create",
                scope_org_id=session.get("scope_org_id"),
                scope_workspace_id=session.get("scope_workspace_id"),
            )
        if session.get("session_type") != "create":
            raise ValidationError(
                "Session must be type='create' for framework creation"
            )
        if session.get("status") not in {"phase1_review", "phase2_review", "failed"}:
            raise ValidationError(
                "Session must be in review state before human-approved creation"
            )
        if not session.get("scope_org_id") or not session.get("scope_workspace_id"):
            raise ValidationError(
                "Session is missing org/workspace scope; regenerate from current scope"
            )
        if not session.get("proposed_hierarchy"):
            raise ValidationError(
                "Session has no proposed hierarchy — run Phase 1 first"
            )
        proposed_controls = session.get("proposed_controls") or []
        if isinstance(proposed_controls, str):
            try:
                proposed_controls = json.loads(proposed_controls)
            except Exception:
                proposed_controls = []
        if not proposed_controls:
            raise ValidationError(
                "Session has no proposed controls — cannot create incomplete framework"
            )
        if not isinstance(proposed_controls, list):
            raise ValidationError(
                "Session proposed controls are invalid — regenerate the proposal"
            )
        proposed_risk_mappings = session.get("proposed_risk_mappings") or []
        if isinstance(proposed_risk_mappings, str):
            try:
                proposed_risk_mappings = json.loads(proposed_risk_mappings)
            except Exception:
                proposed_risk_mappings = []
        if not proposed_risk_mappings:
            raise ValidationError(
                "Session has no proposed risk mappings — review and regenerate before creation"
            )
        if not isinstance(proposed_risk_mappings, list):
            raise ValidationError(
                "Session proposed risk mappings are invalid — regenerate the proposal"
            )

        control_codes: list[str] = []
        for control in proposed_controls:
            if not isinstance(control, dict):
                continue
            normalized = _normalize_entity_code(control.get("control_code"))
            if normalized:
                control_codes.append(normalized)

        if not control_codes:
            raise ValidationError(
                "Session has no valid control codes — regenerate controls before creation"
            )
        unique_control_codes = set(control_codes)
        if len(unique_control_codes) != len(control_codes):
            duplicates = sorted(
                {code for code in unique_control_codes if control_codes.count(code) > 1}
            )
            preview = ", ".join(duplicates[:10])
            raise ValidationError(
                f"Duplicate control codes detected in proposal ({len(duplicates)} duplicates): {preview}"
            )

        mapped_codes: set[str] = set()
        invalid_mappings: list[int] = []
        for index, mapping in enumerate(proposed_risk_mappings, start=1):
            if not isinstance(mapping, dict):
                invalid_mappings.append(index)
                continue
            control_code = _normalize_entity_code(mapping.get("control_code"))
            risk_code = _normalize_entity_code(mapping.get("risk_code"))
            if not control_code or not risk_code:
                invalid_mappings.append(index)
                continue
            mapped_codes.add(control_code)
        if invalid_mappings:
            preview = ", ".join(str(i) for i in invalid_mappings[:10])
            raise ValidationError(
                f"Risk mappings contain invalid entries (missing control_code/risk_code) at positions: {preview}"
            )

        unmapped_controls = sorted(unique_control_codes - mapped_codes)
        if unmapped_controls:
            preview = ", ".join(unmapped_controls[:10])
            raise ValidationError(
                f"Every control must be risk-mapped before creation. Unmapped controls: {preview}"
            )

        hierarchy = session.get("proposed_hierarchy") or {}
        framework_code = hierarchy.get("framework_code") or _slugify(
            session.get("framework_name", "custom")
        )

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_name": session.get("framework_name", "Custom Framework"),
            "framework_code": framework_code,
            "framework_type_code": session.get("framework_type_code", "custom"),
            "framework_category_code": session.get(
                "framework_category_code", "security"
            ),
            "scope_org_id": session.get("scope_org_id"),
            "scope_workspace_id": session.get("scope_workspace_id"),
            "user_context": session.get("user_context", ""),
            "hierarchy": hierarchy,
            "controls": proposed_controls,
            "new_risks": session.get("proposed_risks", []),
            "risk_mappings": proposed_risk_mappings,
        }

        job_id = await self._enqueue_job(
            job_type="framework_build",
            agent_type_code="framework_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code=request.priority_code,
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.set_job(
                conn,
                session_id,
                tenant_key=tenant_key,
                job_id=job_id,
                status="creating",
                now=now,
            )

        return BuildJobStatusResponse(
            job_id=job_id, status="queued", job_type="framework_build"
        )

    # ── Enqueue Apply Changes (Enhance Mode) ──────────────────────────────────

    async def enqueue_apply_changes(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
        request: ApplyEnhancementsRequest,
    ) -> BuildJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            session = await self._repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "frameworks.update",
                scope_org_id=session.get("scope_org_id"),
                scope_workspace_id=session.get("scope_workspace_id"),
            )
        if session.get("session_type") != "enhance":
            raise ValidationError("Session must be type='enhance' for apply changes")
        if session.get("status") not in {"phase2_review", "failed"}:
            raise ValidationError(
                "Session must be in review state before human-approved enhancement apply"
            )
        if not session.get("scope_org_id") or not session.get("scope_workspace_id"):
            raise ValidationError(
                "Session is missing org/workspace scope; regenerate from current scope"
            )
        if not request.accepted_changes:
            raise ValidationError(
                "accepted_changes must contain at least one user-approved change"
            )
        proposed_changes = session.get("enhance_diff") or []
        if isinstance(proposed_changes, str):
            try:
                proposed_changes = json.loads(proposed_changes)
            except Exception:
                proposed_changes = []
        if not isinstance(proposed_changes, list) or not proposed_changes:
            raise ValidationError("Session has no proposed enhance changes to approve")

        allowed_signatures = Counter(
            _change_signature(change)
            for change in proposed_changes
            if isinstance(change, dict)
        )
        if not allowed_signatures:
            raise ValidationError(
                "Session proposals are invalid; regenerate enhancement suggestions"
            )
        for change in request.accepted_changes:
            if not isinstance(change, dict):
                raise ValidationError("accepted_changes entries must be objects")
            signature = _change_signature(change)
            if allowed_signatures[signature] <= 0:
                raise ValidationError(
                    "accepted_changes contains entries not present in the proposed enhancement diff"
                )
            allowed_signatures[signature] -= 1

            change_type = str(change.get("change_type") or "").strip()
            proposed_value = change.get("proposed_value")
            if change_type == "add_control":
                if not isinstance(proposed_value, dict):
                    raise ValidationError(
                        "add_control changes must provide a structured proposed_value object"
                    )
                risk_mappings = proposed_value.get("risk_mappings")
                risk_mapping = proposed_value.get("risk_mapping")
                if risk_mappings is None and isinstance(risk_mapping, dict):
                    risk_mappings = [risk_mapping]
                if not isinstance(risk_mappings, list) or len(risk_mappings) == 0:
                    raise ValidationError(
                        "add_control changes must include at least one risk mapping in proposed_value.risk_mappings"
                    )
                for index, mapping in enumerate(risk_mappings, start=1):
                    if not isinstance(mapping, dict):
                        raise ValidationError(
                            f"add_control risk_mappings[{index}] must be an object"
                        )
                    risk_code = _normalize_entity_code(mapping.get("risk_code"))
                    new_risk = mapping.get("new_risk")
                    has_new_risk_payload = isinstance(new_risk, dict) and bool(
                        str(new_risk.get("title") or "").strip()
                    )
                    if not risk_code and not has_new_risk_payload:
                        raise ValidationError(
                            "add_control risk mappings must include risk_code or a new_risk object with title"
                        )
            if change_type == "add_risk_mapping":
                if not isinstance(proposed_value, dict):
                    raise ValidationError(
                        "add_risk_mapping changes must provide a structured proposed_value object"
                    )
                risk_code = _normalize_entity_code(proposed_value.get("risk_code"))
                new_risk = proposed_value.get("new_risk")
                has_new_risk_payload = isinstance(new_risk, dict) and bool(
                    str(new_risk.get("title") or "").strip()
                )
                if not risk_code and not has_new_risk_payload:
                    raise ValidationError(
                        "add_risk_mapping changes must include risk_code or a new_risk object with title"
                    )

        framework_id = session.get("framework_id")
        if not framework_id:
            raise ValidationError("Session has no target framework_id for enhance mode")

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_id": framework_id,
            "scope_org_id": session.get("scope_org_id"),
            "scope_workspace_id": session.get("scope_workspace_id"),
            "accepted_changes": request.accepted_changes,
        }

        job_id = await self._enqueue_job(
            job_type="framework_apply_changes",
            agent_type_code="framework_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code=request.priority_code,
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.set_job(
                conn,
                session_id,
                tenant_key=tenant_key,
                job_id=job_id,
                status="creating",
                now=now,
            )

        return BuildJobStatusResponse(
            job_id=job_id, status="queued", job_type="framework_apply_changes"
        )

    # ── Enqueue Phase 1: Hierarchy (background job) ────────────────────────────

    async def enqueue_hierarchy(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
    ) -> BuildJobStatusResponse:
        """Enqueue Phase 1 hierarchy generation as a background job (survives navigation)."""
        async with self._database_pool.acquire() as conn:
            session = await self._repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        if session.get("session_type") != "create":
            raise ValidationError(
                "Session must be type='create' for hierarchy generation"
            )

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_name": session.get("framework_name") or "",
            "framework_type_code": session.get("framework_type_code") or "custom",
            "framework_category_code": session.get("framework_category_code")
            or "security",
            "user_context": session.get("user_context") or "",
            "attachment_ids": session.get("attachment_ids") or [],
            "scope_org_id": session.get("scope_org_id"),
            "scope_workspace_id": session.get("scope_workspace_id"),
        }
        job_id = await self._enqueue_job(
            job_type="framework_hierarchy",
            agent_type_code="framework_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code="normal",
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.set_job(
                conn,
                session_id,
                tenant_key=tenant_key,
                job_id=job_id,
                status="phase1_streaming",
                now=now,
            )
        # Clear activity log for fresh progress feed
        await self.clear_activity_log(session_id=session_id, tenant_key=tenant_key)
        return BuildJobStatusResponse(
            job_id=job_id, status="queued", job_type="framework_hierarchy"
        )

    # ── Enqueue Phase 2: Controls (background job) ───────────────────────────

    async def enqueue_controls(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
    ) -> BuildJobStatusResponse:
        """Enqueue Phase 2 control generation as a background job (survives navigation)."""
        async with self._database_pool.acquire() as conn:
            session = await self._repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        if session.get("session_type") != "create":
            raise ValidationError(
                "Session must be type='create' for control generation"
            )
        if not session.get("proposed_hierarchy"):
            raise ValidationError("Run Phase 1 (hierarchy) first")

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_name": session.get("framework_name") or "",
            "framework_type_code": session.get("framework_type_code") or "custom",
            "user_context": session.get("user_context") or "",
            "attachment_ids": session.get("attachment_ids") or [],
            "node_overrides": session.get("node_overrides") or {},
            "scope_org_id": session.get("scope_org_id"),
            "scope_workspace_id": session.get("scope_workspace_id"),
        }
        job_id = await self._enqueue_job(
            job_type="framework_controls",
            agent_type_code="framework_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code="normal",
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.set_job(
                conn,
                session_id,
                tenant_key=tenant_key,
                job_id=job_id,
                status="phase2_streaming",
                now=now,
            )
        # Clear activity log for fresh progress feed
        await self.clear_activity_log(session_id=session_id, tenant_key=tenant_key)
        return BuildJobStatusResponse(
            job_id=job_id, status="queued", job_type="framework_controls"
        )

    # ── Enqueue Enhance Diff (background job) ────────────────────────────────

    async def enqueue_enhance_diff(
        self,
        *,
        user_id: str,
        tenant_key: str,
        session_id: str,
    ) -> BuildJobStatusResponse:
        """Enqueue the enhance diff analysis as a background job instead of SSE."""
        async with self._database_pool.acquire() as conn:
            session = await self._repository.get_by_id(conn, session_id, tenant_key)
        if not session or session.get("user_id") != user_id:
            raise NotFoundError(f"Session '{session_id}' not found")
        if session.get("session_type") != "enhance":
            raise ValidationError("Session must be type='enhance' for enhance diff")
        framework_id = session.get("framework_id")
        if not framework_id:
            raise ValidationError("Session has no target framework_id")

        input_json = {
            "session_id": session_id,
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_id": framework_id,
            "scope_org_id": session.get("scope_org_id"),
            "scope_workspace_id": session.get("scope_workspace_id"),
            "user_context": session.get("user_context") or "",
            "attachment_ids": session.get("attachment_ids") or [],
        }
        job_id = await self._enqueue_job(
            job_type="framework_enhance_diff",
            agent_type_code="framework_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code="normal",
            input_json=input_json,
            scope_org_id=session.get("scope_org_id"),
            scope_workspace_id=session.get("scope_workspace_id"),
        )
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.set_job(
                conn,
                session_id,
                tenant_key=tenant_key,
                job_id=job_id,
                status="phase1_streaming",
                now=now,
            )
        return BuildJobStatusResponse(
            job_id=job_id, status="queued", job_type="framework_enhance_diff"
        )

    # ── Enqueue Gap Analysis ───────────────────────────────────────────────────

    async def enqueue_gap_analysis(
        self, *, user_id: str, tenant_key: str, request: GapAnalysisRequest
    ) -> BuildJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            framework = await conn.fetchrow(
                f"""
                SELECT f.id::text AS id,
                       f.scope_org_id::text AS scope_org_id,
                       f.scope_workspace_id::text AS scope_workspace_id,
                       f.framework_code AS framework_name,
                       f.framework_code AS framework_code
                FROM {_FRAMEWORKS} f
                WHERE f.id = $1::uuid
                  AND f.tenant_key = $2
                  AND f.is_active = TRUE
                  AND f.is_deleted = FALSE
                """,
                request.framework_id,
                tenant_key,
            )
            if not framework:
                raise NotFoundError(f"Framework '{request.framework_id}' not found")
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=framework.get("scope_org_id"),
                scope_workspace_id=framework.get("scope_workspace_id"),
            )

        input_json = {
            "user_id": user_id,
            "tenant_key": tenant_key,
            "framework_id": request.framework_id,
            "user_context": request.user_context or "",
            "attachment_ids": request.attachment_ids or [],
        }
        job_id = await self._enqueue_job(
            job_type="framework_gap_analysis",
            agent_type_code="framework_builder",
            user_id=user_id,
            tenant_key=tenant_key,
            priority_code=request.priority_code,
            input_json=input_json,
            scope_org_id=framework.get("scope_org_id"),
            scope_workspace_id=framework.get("scope_workspace_id"),
        )

        # Also create a session entry so gap analysis appears in sidebar history
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await self._repository.create_session(
                conn=conn,
                session_id=str(uuid.uuid4()),
                tenant_key=tenant_key,
                user_id=user_id,
                session_type="gap",
                scope_org_id=framework.get("scope_org_id"),
                scope_workspace_id=framework.get("scope_workspace_id"),
                framework_id=request.framework_id,
                framework_name=framework.get("framework_name"),
                framework_type_code=None,
                framework_category_code=None,
                user_context=request.user_context,
                attachment_ids=request.attachment_ids or [],
                job_id=job_id,
                now=now,
            )

        return BuildJobStatusResponse(
            job_id=job_id, status="queued", job_type="framework_gap_analysis"
        )

    # ── Poll Job Status ────────────────────────────────────────────────────────

    async def get_job_status(
        self, *, user_id: str, tenant_key: str, job_id: str
    ) -> BuildJobStatusResponse:
        async with self._database_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"""
                SELECT id::text, status_code, job_type, output_json,
                       error_message, started_at::text, completed_at::text,
                       org_id::text AS scope_org_id,
                       workspace_id::text AS scope_workspace_id
                FROM {_JOBS}
                WHERE id = $1 AND tenant_key = $2 AND user_id = $3::uuid
                """,
                job_id,
                tenant_key,
                user_id,
            )
            if not row:
                raise NotFoundError(f"Job '{job_id}' not found")
            await require_permission(
                conn,
                user_id,
                "frameworks.view",
                scope_org_id=row.get("scope_org_id"),
                scope_workspace_id=row.get("scope_workspace_id"),
            )

        output = row["output_json"]
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except Exception:
                output = {}
        output = output or {}

        def _dt(v):
            return v.isoformat() if v is not None and hasattr(v, "isoformat") else v

        # creation_log items may be stored as JSON strings; parse them
        raw_log = output.get("creation_log", [])
        creation_log = []
        for item in raw_log:
            if isinstance(item, str):
                try:
                    item = json.loads(item)
                except Exception:
                    item = {"event": "raw", "message": item}
            creation_log.append(item)

        stats = output.get("stats")

        def _to_int(value: object, default: int = 0) -> int:
            if isinstance(value, bool):
                return default
            if isinstance(value, int):
                return value
            if isinstance(value, float):
                return int(value)
            try:
                return int(str(value))
            except Exception:
                return default

        if row["job_type"] == "framework_apply_changes":
            existing_stats = stats if isinstance(stats, dict) else {}
            stats = {
                "requested_count": _to_int(
                    output.get(
                        "requested_count", existing_stats.get("requested_count", 0)
                    ),
                    default=0,
                ),
                "applied_count": _to_int(
                    output.get("applied_count", existing_stats.get("applied_count", 0)),
                    default=0,
                ),
                "failed_count": _to_int(
                    output.get("failed_count", existing_stats.get("failed_count", 0)),
                    default=0,
                ),
            }

        if row["status_code"] == "completed" and row["job_type"] in {
            "framework_build",
            "framework_apply_changes",
        }:
            async with self._database_pool.acquire() as conn:
                repaired_framework_id = await self._repair_framework_scope_from_session(
                    conn=conn,
                    job_id=job_id,
                    tenant_key=tenant_key,
                    user_id=user_id,
                    framework_id=output.get("framework_id"),
                )
            if repaired_framework_id and not output.get("framework_id"):
                output["framework_id"] = repaired_framework_id

        return BuildJobStatusResponse(
            job_id=str(row["id"]),
            status=row["status_code"],
            job_type=row["job_type"],
            creation_log=creation_log,
            framework_id=output.get("framework_id"),
            stats=stats,
            error_message=row["error_message"],
            started_at=_dt(row["started_at"]),
            completed_at=_dt(row["completed_at"]),
        )

    # ── Internals ─────────────────────────────────────────────────────────────

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

    async def _repair_framework_scope_from_session(
        self,
        *,
        conn: asyncpg.Connection,
        job_id: str,
        tenant_key: str,
        user_id: str,
        framework_id: str | None,
    ) -> str | None:
        session = await conn.fetchrow(
            f"""
            SELECT scope_org_id::text AS scope_org_id,
                   scope_workspace_id::text AS scope_workspace_id,
                   framework_id::text AS source_framework_id,
                   result_framework_id::text AS result_framework_id
            FROM {_SESSIONS}
            WHERE job_id = $1::uuid
              AND tenant_key = $2
              AND user_id = $3::uuid
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            job_id,
            tenant_key,
            user_id,
        )
        if not session:
            return framework_id

        scope_org_id = session.get("scope_org_id")
        scope_workspace_id = session.get("scope_workspace_id")
        if not scope_org_id or not scope_workspace_id:
            return framework_id

        resolved_framework_id = (
            str(framework_id).strip()
            if framework_id
            else str(
                session.get("result_framework_id")
                or session.get("source_framework_id")
                or ""
            ).strip()
        ) or None
        if not resolved_framework_id:
            return None

        updated_id = await conn.fetchval(
            f"""
            UPDATE {_FRAMEWORKS}
            SET scope_org_id = $2::uuid,
                scope_workspace_id = $3::uuid,
                updated_at = NOW(),
                updated_by = $4::uuid
            WHERE id = $1::uuid
              AND tenant_key = $5
              AND (
                  scope_org_id IS DISTINCT FROM $2::uuid
                  OR scope_workspace_id IS DISTINCT FROM $3::uuid
              )
            RETURNING id::text
            """,
            resolved_framework_id,
            scope_org_id,
            scope_workspace_id,
            user_id,
            tenant_key,
        )
        if updated_id:
            self._logger.warning(
                "framework_builder.scope_repaired",
                extra={
                    "job_id": job_id,
                    "framework_id": resolved_framework_id,
                    "scope_org_id": scope_org_id,
                    "scope_workspace_id": scope_workspace_id,
                },
            )
        return resolved_framework_id


def _parse_activity_log(raw: list) -> list:
    """Flatten activity_log items that may be JSON strings or nested arrays."""
    result = []
    for item in raw:
        if isinstance(item, str):
            try:
                parsed = json.loads(item)
                if isinstance(parsed, list):
                    result.extend(parsed)
                elif isinstance(parsed, dict):
                    result.append(parsed)
            except Exception:
                pass
        elif isinstance(item, list):
            result.extend(item)
        elif isinstance(item, dict):
            result.append(item)
    return result


def _session_response(row: dict) -> SessionResponse:
    return SessionResponse(
        id=row["id"],
        tenant_key=row["tenant_key"],
        user_id=row["user_id"],
        session_type=row["session_type"],
        status=row["status"],
        scope_org_id=row.get("scope_org_id"),
        scope_workspace_id=row.get("scope_workspace_id"),
        framework_id=row.get("framework_id"),
        framework_name=row.get("framework_name"),
        framework_type_code=row.get("framework_type_code"),
        framework_category_code=row.get("framework_category_code"),
        user_context=row.get("user_context"),
        attachment_ids=row.get("attachment_ids") or [],
        node_overrides=row.get("node_overrides") or {},
        proposed_hierarchy=row.get("proposed_hierarchy"),
        proposed_controls=row.get("proposed_controls"),
        proposed_risks=row.get("proposed_risks"),
        proposed_risk_mappings=row.get("proposed_risk_mappings"),
        enhance_diff=row.get("enhance_diff"),
        accepted_changes=row.get("accepted_changes"),
        job_id=row.get("job_id"),
        result_framework_id=row.get("result_framework_id"),
        error_message=row.get("error_message"),
        activity_log=_parse_activity_log(row.get("activity_log") or []),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
    )


def _slugify(name: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")[:50]


def _change_signature(change: dict) -> str:
    payload = {
        "change_type": change.get("change_type"),
        "entity_type": change.get("entity_type"),
        "entity_id": change.get("entity_id"),
        "entity_code": change.get("entity_code"),
        "field": change.get("field"),
        "proposed_value": change.get("proposed_value"),
    }
    return json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))


def _normalize_entity_code(value: object) -> str:
    return str(value or "").strip().upper()
