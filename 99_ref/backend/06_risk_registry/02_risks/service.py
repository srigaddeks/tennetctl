from __future__ import annotations

import uuid
from importlib import import_module

from .repository import RiskRepository
from .schemas import (
    CompleteReviewRequest,
    CreateRiskGroupAssignmentRequest,
    CreateRiskRequest,
    HeatMapCell,
    HeatMapResponse,
    OverdueReviewListResponse,
    OverdueReviewResponse,
    ReviewScheduleResponse,
    RiskAppetiteListResponse,
    RiskAppetiteResponse,
    RiskDetailResponse,
    RiskGroupAssignmentListResponse,
    RiskGroupAssignmentResponse,
    RiskListResponse,
    RiskResponse,
    RiskSummaryResponse,
    UpdateRiskRequest,
    UpsertReviewScheduleRequest,
    UpsertRiskAppetiteRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.06_risk_registry.constants")
_auto_task_module = import_module("backend.07_tasks._auto_task")
_auth_constants_module = import_module("backend.03_auth_manage.constants")
_spreadsheet_module = import_module("backend.01_core.spreadsheet")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
RiskAuditEventType = _constants_module.RiskAuditEventType
RISK_STATUS_TRANSITIONS = _constants_module.RISK_STATUS_TRANSITIONS
AuditEventCategory = _auth_constants_module.AuditEventCategory
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
auto_create_task = _auto_task_module.auto_create_task
to_csv = _spreadsheet_module.to_csv
to_json = _spreadsheet_module.to_json
to_xlsx = _spreadsheet_module.to_xlsx
to_xlsx_template = _spreadsheet_module.to_xlsx_template
parse_import = _spreadsheet_module.parse_import
make_streaming_response = _spreadsheet_module.make_streaming_response

# Risk levels that trigger automatic mitigation task creation
_HIGH_RISK_LEVELS = frozenset({"high", "critical"})

_CACHE_TTL_RISKS = 300  # 5 minutes


@instrument_class_methods(namespace="risk.risks.service", logger_name="backend.risk.risks.instrumentation")
class RiskService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = RiskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.risk.risks")

    async def _require_risk_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str | None,
        workspace_id: str | None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def list_risks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        category: str | None = None,
        status: str | None = None,
        level: str | None = None,
        search: str | None = None,
        treatment_type: str | None = None,
        control_id: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> RiskListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn, user_id, "risks.view",
                scope_org_id=org_id, scope_workspace_id=workspace_id,
            )

        # Only cache unfiltered full list
        has_filters = any([category, status, level, search, treatment_type, workspace_id, control_id])
        cache_key = f"risks:list:{tenant_key}:{org_id or 'all'}"
        if not has_filters and limit >= 100 and offset == 0:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return RiskListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            records, total = await self._repository.list_risks(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                category=category,
                status=status,
                level=level,
                search=search,
                treatment_type=treatment_type,
                control_id=control_id,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_detail_response(r) for r in records]

        # Batch-resolve owner display names
        owner_ids = [item.owner_user_id for item in items if item.owner_user_id]
        if owner_ids:
            async with self._database_pool.acquire() as conn2:
                owner_names = await self._repository.resolve_owner_names_batch(conn2, owner_ids)
            for item in items:
                if item.owner_user_id:
                    item.owner_display_name = owner_names.get(item.owner_user_id)

        result = RiskListResponse(items=items, total=total)
        if not has_filters and limit >= 100 and offset == 0:
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_RISKS)
        return result

    async def get_risk(self, *, user_id: str, risk_id: str) -> RiskDetailResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_risk_detail(conn, risk_id)
            if record is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )

        cache_key = f"risk:{risk_id}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return RiskDetailResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            result = _detail_response(record)
            # Resolve owner display name
            if result.owner_user_id:
                display_name = await self._repository.resolve_owner_display_name(conn, result.owner_user_id)
                result.owner_display_name = display_name
        await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_RISKS)
        return result

    async def create_risk(
        self, *, user_id: str, tenant_key: str, request: CreateRiskRequest
    ) -> RiskResponse:
        now = utc_now_sql()
        risk_id = str(uuid.uuid4())
        async with self._database_pool.transaction() as conn:
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.create",
                org_id=request.org_id,
                workspace_id=request.workspace_id,
            )
            risk = await self._repository.create_risk(
                conn,
                risk_id=risk_id,
                tenant_key=tenant_key,
                risk_code=request.risk_code,
                org_id=request.org_id,
                workspace_id=request.workspace_id,
                risk_category_code=request.risk_category_code,
                risk_level_code=request.risk_level_code,
                treatment_type_code=request.treatment_type_code,
                source_type=request.source_type,
                created_by=user_id,
                now=now,
            )
            # Write EAV properties (batch)
            eav_pairs = _collect_eav_properties(request)
            await self._repository.upsert_risk_properties_batch(
                conn,
                risk_id=risk_id,
                properties=eav_pairs,
                actor_id=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.RISK_CREATED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "risk_code": request.risk_code,
                        "org_id": request.org_id,
                        "workspace_id": request.workspace_id,
                        "risk_category_code": request.risk_category_code,
                        "title": request.title,
                    },
                ),
            )
            # Auto-create a risk_mitigation task for high/critical risks
            if request.risk_level_code in _HIGH_RISK_LEVELS:
                priority = "critical" if request.risk_level_code == "critical" else "high"
                await auto_create_task(
                    conn,
                    tenant_key=tenant_key,
                    org_id=request.org_id,
                    workspace_id=request.workspace_id,
                    task_type_code="risk_mitigation",
                    priority_code=priority,
                    title=f"Mitigate risk: {request.title}",
                    description=(
                        f"Risk '{request.title}' ({request.risk_level_code.upper()}) was identified. "
                        "Develop and execute a mitigation plan to reduce the risk to an acceptable level."
                    ),
                    entity_type="risk",
                    entity_id=risk_id,
                    reporter_user_id=user_id,
                )
        await self._cache.delete_pattern("risks:list:*")
        return _risk_response(risk)

    async def update_risk(
        self, *, user_id: str, risk_id: str, request: UpdateRiskRequest
    ) -> RiskResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            # Capture old status for review event
            old_risk = await self._repository.get_risk_by_id(conn, risk_id)
            if old_risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.update",
                org_id=old_risk.org_id,
                workspace_id=old_risk.workspace_id,
            )
            old_status = old_risk.risk_status

            # Enforce status state machine
            if request.risk_status and request.risk_status != old_status:
                allowed = RISK_STATUS_TRANSITIONS.get(old_status, set())
                if request.risk_status not in allowed:
                    raise ValidationError(
                        f"Cannot transition risk from '{old_status}' to '{request.risk_status}'. "
                        f"Allowed transitions: {', '.join(sorted(allowed)) if allowed else 'none (terminal state)'}"
                    )

            risk = await self._repository.update_risk(
                conn,
                risk_id,
                risk_category_code=request.risk_category_code,
                risk_level_code=request.risk_level_code,
                treatment_type_code=request.treatment_type_code,
                risk_status=request.risk_status,
                is_disabled=request.is_disabled,
                updated_by=user_id,
                now=now,
            )
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")

            # Write EAV properties (batch)
            eav_pairs = _collect_eav_update_properties(request)
            await self._repository.upsert_risk_properties_batch(
                conn,
                risk_id=risk_id,
                properties=eav_pairs,
                actor_id=user_id,
                now=now,
            )

            # Status change creates review event
            if request.risk_status is not None and request.risk_status != old_status:
                _review_repo_module = import_module("backend.06_risk_registry.06_review_events.repository")
                review_repo = _review_repo_module.ReviewEventRepository()
                await review_repo.create_review_event(
                    conn,
                    event_id=str(uuid.uuid4()),
                    risk_id=risk_id,
                    event_type="status_changed",
                    old_status=old_status,
                    new_status=request.risk_status,
                    actor_id=user_id,
                    comment=None,
                    now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.RISK_UPDATED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "risk_status": request.risk_status,
                        "risk_category_code": request.risk_category_code,
                    },
                ),
            )
        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")
        return _risk_response(risk)

    async def delete_risk(self, *, user_id: str, risk_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.delete",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            removed = await self._repository.soft_delete_risk(
                conn, risk_id, deleted_by=user_id, now=now
            )
            if not removed:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.RISK_DELETED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
        await self._cache.delete_pattern("risks:list:*")
        await self._cache.delete(f"risk:{risk_id}")

    async def get_heat_map(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> HeatMapResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn, user_id, "risks.view",
                scope_org_id=org_id, scope_workspace_id=workspace_id,
            )
            data = await self._repository.get_heat_map_data(conn, tenant_key, org_id, workspace_id)
        cells = [
            HeatMapCell(
                likelihood_score=row["likelihood_score"],
                impact_score=row["impact_score"],
                risk_count=row["risk_count"],
                risk_ids=row["risk_ids"],
            )
            for row in data
        ]
        return HeatMapResponse(cells=cells)

    async def get_risk_summary(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
    ) -> RiskSummaryResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn, user_id, "risks.view",
                scope_org_id=org_id, scope_workspace_id=workspace_id,
            )
            data = await self._repository.get_risk_summary(conn, tenant_key, org_id, workspace_id)
        return RiskSummaryResponse(**data)

    async def export_risks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        workspace_id: str | None = None,
        fmt: str = "csv",
        simplified: bool = False,
    ):
        """Export risks as CSV, JSON, or XLSX."""
        result = await self.list_risks(
            user_id=user_id, tenant_key=tenant_key,
            org_id=org_id, workspace_id=workspace_id,
            limit=5000, offset=0,
        )
        rows = []
        for risk in result.items:
            row = {
                "risk_code": risk.risk_code,
                "title": risk.title or "",
                "risk_status": risk.risk_status or "",
                "risk_level_code": risk.risk_level_code or "",
                "risk_category_code": risk.risk_category_code or "",
                "treatment_type_code": risk.treatment_type_code or "",
                "source_type": risk.source_type or "",
                "description": getattr(risk, "description", "") or "",
                "business_impact": getattr(risk, "business_impact", "") or "",
                "owner_email": getattr(risk, "owner_email", "") or "",
            }
            if not simplified:
                row["id"] = risk.id
                row["owner_user_id"] = risk.owner_user_id or ""
                row["inherent_risk_score"] = risk.inherent_risk_score or ""
                row["residual_risk_score"] = risk.residual_risk_score or ""
            rows.append(row)

        if simplified:
            columns = ["risk_code", "title", "risk_status", "risk_level_code",
                       "risk_category_code", "treatment_type_code", "source_type",
                       "description", "business_impact", "owner_email"]
        else:
            columns = ["id", "risk_code", "title", "risk_status", "risk_level_code",
                       "risk_category_code", "treatment_type_code", "source_type",
                       "owner_email", "owner_user_id",
                       "inherent_risk_score", "residual_risk_score",
                       "description", "business_impact"]

        if fmt == "json":
            data = to_json(rows)
        elif fmt == "xlsx":
            data = to_xlsx(rows, columns, sheet_name="Risks")
        else:
            data = to_csv(rows, columns)

        return make_streaming_response(data, fmt, "risks_export")

    async def import_risks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None,
        workspace_id: str | None,
        file_bytes: bytes,
        filename: str,
        dry_run: bool = False,
    ):
        """Import risks from CSV or JSON. Upserts by risk_code."""
        from .schemas import ImportRiskError, ImportRisksResult

        try:
            rows = parse_import(file_bytes, filename)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        created = 0
        updated = 0
        errors: list[ImportRiskError] = []

        for row_idx, row in enumerate(rows, start=2):
            risk_code = (row.get("risk_code") or "").strip()
            title = (row.get("title") or "").strip()
            if not risk_code:
                errors.append(ImportRiskError(row=row_idx, field="risk_code", message="risk_code is required"))
                continue
            if not title:
                errors.append(ImportRiskError(row=row_idx, key=risk_code, field="title", message="title is required"))
                continue
            try:
                if not dry_run:
                    from .schemas import CreateRiskRequest
                    req = CreateRiskRequest(
                        risk_code=risk_code,
                        title=title,
                        risk_category_code=row.get("risk_category_code") or "operational",
                        risk_level_code=row.get("risk_level_code") or "medium",
                        treatment_type_code=row.get("treatment_type_code") or "mitigate",
                        source_type=row.get("source_type") or "manual",
                        description=row.get("description") or None,
                        business_impact=row.get("business_impact") or None,
                        org_id=org_id,
                        workspace_id=workspace_id,
                    )
                    await self.create_risk(user_id=user_id, tenant_key=tenant_key, request=req)
                created += 1
            except Exception as exc:
                errors.append(ImportRiskError(row=row_idx, key=risk_code, message=str(exc)))

        return ImportRisksResult(created=created, updated=updated, errors=errors, dry_run=dry_run)

    async def get_import_template(self, *, fmt: str = "csv"):
        """Return a downloadable import template for risks."""
        columns = ["risk_code", "title", "risk_category_code", "risk_level_code",
                   "treatment_type_code", "source_type", "description", "business_impact"]
        examples = {
            "risk_code": "RISK-001",
            "title": "Unauthorized data access",
            "risk_category_code": "security",
            "risk_level_code": "high",
            "treatment_type_code": "mitigate",
            "source_type": "manual",
            "description": "Risk of unauthorized access to sensitive data",
            "business_impact": "Data breach, regulatory fines",
        }
        if fmt == "xlsx":
            data = to_xlsx_template(columns, examples, "Risks Template")
        else:
            data = to_csv([examples], columns)
        return make_streaming_response(data, fmt, "risks_import_template")

    # ─── Group Assignment ────────────────────────────────────────────────

    async def list_risk_groups(
        self, *, user_id: str, risk_id: str
    ) -> RiskGroupAssignmentListResponse:
        async with self._database_pool.acquire() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.view",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            rows = await self._repository.list_risk_groups(conn, risk_id)
        items = [
            RiskGroupAssignmentResponse(
                id=r["id"],
                risk_id=r["risk_id"],
                group_id=r["group_id"],
                group_name=r.get("group_name"),
                role=r["role"],
                assigned_by=r["assigned_by"],
                assigned_at=r["assigned_at"],
            )
            for r in rows
        ]
        return RiskGroupAssignmentListResponse(items=items)

    async def assign_risk_group(
        self,
        *,
        user_id: str,
        risk_id: str,
        request: CreateRiskGroupAssignmentRequest,
    ) -> RiskGroupAssignmentResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.assign",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            row = await self._repository.assign_risk_group(
                conn, risk_id, request.group_id, request.role, user_id
            )
            if row is None:
                raise ConflictError(
                    f"Group '{request.group_id}' already assigned with role '{request.role}'"
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.GROUP_ASSIGNED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "group_id": request.group_id,
                        "role": request.role,
                    },
                ),
            )
        await self._cache.delete(f"risk:{risk_id}")
        return RiskGroupAssignmentResponse(
            id=row["id"],
            risk_id=row["risk_id"],
            group_id=row["group_id"],
            role=row["role"],
            assigned_by=row["assigned_by"],
            assigned_at=row["assigned_at"],
        )

    async def unassign_risk_group(
        self, *, user_id: str, risk_id: str, assignment_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.revoke",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            removed = await self._repository.unassign_risk_group(conn, assignment_id)
            if not removed:
                raise NotFoundError(f"Assignment '{assignment_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.GROUP_UNASSIGNED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"assignment_id": assignment_id},
                ),
            )
        await self._cache.delete(f"risk:{risk_id}")

    # ─── Risk Appetite / Tolerance ───────────────────────────────────────

    async def get_risk_appetite(
        self, *, user_id: str, org_id: str
    ) -> RiskAppetiteListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn, user_id, "risks.view", scope_org_id=org_id
            )
            rows = await self._repository.get_risk_appetite(conn, org_id)
        items = [
            RiskAppetiteResponse(
                id=r["id"],
                org_id=r["org_id"],
                risk_category_code=r["risk_category_code"],
                appetite_level_code=r["appetite_level_code"],
                tolerance_threshold=r["tolerance_threshold"],
                max_acceptable_score=r["max_acceptable_score"],
                description=r.get("description"),
            )
            for r in rows
        ]
        return RiskAppetiteListResponse(items=items)

    async def upsert_risk_appetite(
        self,
        *,
        user_id: str,
        tenant_key: str,
        request: UpsertRiskAppetiteRequest,
    ) -> RiskAppetiteResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.update",
                org_id=request.org_id,
                workspace_id=None,
            )
            row = await self._repository.upsert_risk_appetite(
                conn,
                org_id=request.org_id,
                tenant_key=tenant_key,
                category_code=request.risk_category_code,
                appetite_level_code=request.appetite_level_code,
                tolerance_threshold=request.tolerance_threshold,
                max_acceptable_score=request.max_acceptable_score,
                description=request.description,
                created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="risk_appetite",
                    entity_id=row["id"],
                    event_type=RiskAuditEventType.APPETITE_UPDATED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "org_id": request.org_id,
                        "risk_category_code": request.risk_category_code,
                        "appetite_level_code": request.appetite_level_code,
                    },
                ),
            )
        return RiskAppetiteResponse(
            id=row["id"],
            org_id=row["org_id"],
            risk_category_code=row["risk_category_code"],
            appetite_level_code=row["appetite_level_code"],
            tolerance_threshold=row["tolerance_threshold"],
            max_acceptable_score=row["max_acceptable_score"],
            description=row.get("description"),
        )

    # ─── Scheduled Reviews ───────────────────────────────────────────────

    async def get_review_schedule(
        self, *, user_id: str, risk_id: str
    ) -> ReviewScheduleResponse | None:
        async with self._database_pool.acquire() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.view",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            row = await self._repository.get_review_schedule(conn, risk_id)
        if row is None:
            return None
        return ReviewScheduleResponse(
            id=row["id"],
            risk_id=row["risk_id"],
            review_frequency=row["review_frequency"],
            next_review_date=row["next_review_date"],
            last_reviewed_at=row.get("last_reviewed_at"),
            last_reviewed_by=row.get("last_reviewed_by"),
            assigned_reviewer_id=row.get("assigned_reviewer_id"),
            is_overdue=row["is_overdue"],
        )

    async def upsert_review_schedule(
        self,
        *,
        user_id: str,
        risk_id: str,
        request: UpsertReviewScheduleRequest,
    ) -> ReviewScheduleResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.update",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            row = await self._repository.upsert_review_schedule(
                conn,
                risk_id=risk_id,
                tenant_key=risk.tenant_key,
                frequency=request.review_frequency,
                next_review_date=request.next_review_date,
                reviewer_id=request.assigned_reviewer_id,
                created_by=user_id,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.REVIEW_SCHEDULED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "review_frequency": request.review_frequency,
                        "next_review_date": request.next_review_date,
                    },
                ),
            )
        return ReviewScheduleResponse(
            id=row["id"],
            risk_id=row["risk_id"],
            review_frequency=row["review_frequency"],
            next_review_date=row["next_review_date"],
            assigned_reviewer_id=row.get("assigned_reviewer_id"),
            is_overdue=row["is_overdue"],
        )

    async def complete_review(
        self,
        *,
        user_id: str,
        risk_id: str,
        request: CompleteReviewRequest,
    ) -> ReviewScheduleResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            risk = await self._repository.get_risk_by_id(conn, risk_id)
            if risk is None:
                raise NotFoundError(f"Risk '{risk_id}' not found")
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.update",
                org_id=risk.org_id,
                workspace_id=risk.workspace_id,
            )
            row = await self._repository.complete_review(
                conn, risk_id, user_id, request.next_review_date
            )
            if row is None:
                raise NotFoundError(f"Review schedule for risk '{risk_id}' not found")

            # Create a review event in the review events transaction table
            _review_repo_module = import_module(
                "backend.06_risk_registry.06_review_events.repository"
            )
            review_repo = _review_repo_module.ReviewEventRepository()
            await review_repo.create_review_event(
                conn,
                event_id=str(uuid.uuid4()),
                risk_id=risk_id,
                event_type="reviewed",
                old_status=None,
                new_status=None,
                actor_id=user_id,
                comment=f"Scheduled review completed. Next review: {request.next_review_date}",
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=risk.tenant_key,
                    entity_type="risk",
                    entity_id=risk_id,
                    event_type=RiskAuditEventType.REVIEW_COMPLETED.value,
                    event_category=AuditEventCategory.RISK.value,
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "next_review_date": request.next_review_date,
                    },
                ),
            )
        return ReviewScheduleResponse(
            id=row["id"],
            risk_id=row["risk_id"],
            review_frequency=row["review_frequency"],
            next_review_date=row["next_review_date"],
            last_reviewed_at=row.get("last_reviewed_at"),
            last_reviewed_by=row.get("last_reviewed_by"),
            is_overdue=row["is_overdue"],
        )

    async def list_overdue_reviews(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
    ) -> OverdueReviewListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_risk_permission(
                conn,
                user_id=user_id,
                permission_code="risks.view",
                org_id=org_id,
                workspace_id=None,
            )
            rows = await self._repository.list_overdue_reviews(
                conn, tenant_key, org_id
            )
        items = [
            OverdueReviewResponse(
                id=r["id"],
                risk_id=r["risk_id"],
                risk_title=r.get("risk_title"),
                review_frequency=r["review_frequency"],
                next_review_date=r["next_review_date"],
                assigned_reviewer_id=r.get("assigned_reviewer_id"),
                is_overdue=r["is_overdue"],
            )
            for r in rows
        ]
        return OverdueReviewListResponse(items=items)


def _collect_eav_properties(request: CreateRiskRequest) -> dict[str, str]:
    props: dict[str, str] = {"title": request.title}
    if request.description is not None:
        props["description"] = request.description
    if request.notes is not None:
        props["notes"] = request.notes
    if request.owner_user_id is not None:
        props["owner_user_id"] = request.owner_user_id
    if request.business_impact is not None:
        props["business_impact"] = request.business_impact
    if request.properties:
        props.update(request.properties)
    return props


def _collect_eav_update_properties(request: UpdateRiskRequest) -> dict[str, str]:
    props: dict[str, str] = {}
    if request.title is not None:
        props["title"] = request.title
    if request.description is not None:
        props["description"] = request.description
    if request.notes is not None:
        props["notes"] = request.notes
    if request.owner_user_id is not None:
        props["owner_user_id"] = request.owner_user_id
    if request.business_impact is not None:
        props["business_impact"] = request.business_impact
    if request.properties:
        props.update(request.properties)
    return props


def _risk_response(r) -> RiskResponse:
    return RiskResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        risk_code=r.risk_code,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        risk_category_code=r.risk_category_code,
        risk_level_code=r.risk_level_code,
        treatment_type_code=r.treatment_type_code,
        source_type=r.source_type,
        risk_status=r.risk_status,
        is_active=r.is_active,
        version=r.version,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
    )


def _detail_response(r) -> RiskDetailResponse:
    return RiskDetailResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        risk_code=r.risk_code,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        risk_category_code=r.risk_category_code,
        category_name=r.category_name,
        risk_level_code=r.risk_level_code,
        risk_level_name=r.risk_level_name,
        risk_level_color=r.risk_level_color,
        treatment_type_code=r.treatment_type_code,
        treatment_type_name=r.treatment_type_name,
        source_type=r.source_type,
        risk_status=r.risk_status,
        is_active=r.is_active,
        version=r.version,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
        title=r.title,
        description=r.description,
        notes=r.notes,
        owner_user_id=r.owner_user_id,
        business_impact=r.business_impact,
        inherent_risk_score=r.inherent_risk_score,
        residual_risk_score=r.residual_risk_score,
        linked_control_count=r.linked_control_count,
        treatment_plan_status=r.treatment_plan_status,
        treatment_plan_target_date=r.treatment_plan_target_date,
    )
