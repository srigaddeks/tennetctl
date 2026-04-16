from __future__ import annotations

import json
import uuid
from importlib import import_module

from .repository import ControlRepository
from .schemas import (
    ControlListResponse,
    ControlResponse,
    CreateControlRequest,
    UpdateControlRequest,
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
_constants_module = import_module("backend.05_grc_library.constants")
_spreadsheet_module = import_module("backend.01_core.spreadsheet")
_frameworks_repo_module = import_module(
    "backend.05_grc_library.02_frameworks.repository"
)
_scoped_groups = import_module("backend.03_auth_manage._scoped_group_provisioning")
_versions_repo_module = import_module("backend.05_grc_library.03_versions.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
FrameworkAuditEventType = _constants_module.FrameworkAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
to_csv = _spreadsheet_module.to_csv
to_json = _spreadsheet_module.to_json
to_xlsx = _spreadsheet_module.to_xlsx
to_xlsx_template = _spreadsheet_module.to_xlsx_template
parse_import = _spreadsheet_module.parse_import
make_streaming_response = _spreadsheet_module.make_streaming_response
FrameworkRepository = _frameworks_repo_module.FrameworkRepository
VersionRepository = _versions_repo_module.VersionRepository


@instrument_class_methods(
    namespace="grc.controls.service", logger_name="backend.grc.controls.instrumentation"
)
class ControlService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ControlRepository()
        self._framework_repository = FrameworkRepository()
        self._version_repository = VersionRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.controls")

    async def _get_framework_or_not_found(self, conn, framework_id: str):
        framework = await self._framework_repository.get_framework_by_id(
            conn, framework_id
        )
        if framework is None:
            raise NotFoundError(f"Framework '{framework_id}' not found")
        return framework

    async def _require_control_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        framework_id: str,
    ):
        framework = await self._get_framework_or_not_found(conn, framework_id)
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=framework.scope_org_id,
            scope_workspace_id=framework.scope_workspace_id,
        )
        return framework

    async def _get_latest_published_version_id(
        self, conn, framework_id: str
    ) -> str | None:
        """Get the latest published version ID for a framework, or None if no published version exists."""
        row = await conn.fetchrow(
            """
            SELECT id FROM "05_grc_library"."11_fct_framework_versions"
            WHERE framework_id = $1 AND lifecycle_state = 'published' AND is_deleted = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            framework_id,
        )
        return row["id"] if row else None

    async def list_all_controls(
        self,
        *,
        user_id: str,
        tenant_key: str,
        search: str | None = None,
        framework_id: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        deployed_org_id: str | None = None,
        deployed_workspace_id: str | None = None,
        owner_user_id: str | None = None,
        control_category_code: str | None = None,
        criticality_code: str | None = None,
        control_type: str | None = None,
        automation_potential: str | None = None,
        sort_by: str = "sort_order",
        sort_dir: str = "asc",
        limit: int = 100,
        offset: int = 0,
    ) -> ControlListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "controls.view",
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            # Engineers see only controls they own — auto-apply ownership filter.
            # Caller may also pass owner_user_id explicitly; engineer restriction takes precedence.
            effective_owner_filter = owner_user_id
            if scope_workspace_id is not None:
                grc_role = await _scoped_groups.get_workspace_member_grc_role(
                    conn, workspace_id=scope_workspace_id, user_id=user_id
                )
                if grc_role == "grc_engineer":
                    effective_owner_filter = user_id
            records, total = await self._repository.list_all_controls(
                conn,
                tenant_key=tenant_key,
                search=search,
                framework_id=framework_id,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
                deployed_org_id=deployed_org_id,
                deployed_workspace_id=deployed_workspace_id,
                owner_user_id=effective_owner_filter,
                control_category_code=control_category_code,
                criticality_code=criticality_code,
                control_type=control_type,
                automation_potential=automation_potential,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_control_response(r) for r in records]
        items = await _resolve_control_owners(
            self._database_pool, self._repository, items
        )
        return ControlListResponse(items=items, total=total)

    async def list_controls(
        self,
        *,
        user_id: str,
        framework_id: str,
        search: str | None = None,
        control_category_code: str | None = None,
        criticality_code: str | None = None,
        control_type: str | None = None,
        automation_potential: str | None = None,
        limit: int = 100,
        offset: int = 0,
        version_id: str | None = None,
    ) -> ControlListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_control_permission(
                conn,
                user_id=user_id,
                permission_code="controls.view",
                framework_id=framework_id,
            )

            # Workspace frameworks show ALL controls - not filtered by library version
            # version_id is only used when explicitly requested by the caller
            # This ensures workspace controls don't auto-update until user takes pull

            records, total = await self._repository.list_controls(
                conn,
                framework_id=framework_id,
                search=search,
                control_category_code=control_category_code,
                criticality_code=criticality_code,
                control_type=control_type,
                automation_potential=automation_potential,
                limit=limit,
                offset=offset,
                version_id=version_id,
            )
        items = [_control_response(r) for r in records]
        items = await _resolve_control_owners(
            self._database_pool, self._repository, items
        )
        return ControlListResponse(items=items, total=total)

    async def get_control(
        self, *, user_id: str, framework_id: str, control_id: str
    ) -> ControlResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_control_permission(
                conn,
                user_id=user_id,
                permission_code="controls.view",
                framework_id=framework_id,
            )
            record = await self._repository.get_control_by_id(conn, control_id)
            if record is None or record.framework_id != framework_id:
                raise NotFoundError(
                    f"Control '{control_id}' not found in framework '{framework_id}'"
                )
            all_props = await self._repository.get_all_properties(conn, control_id)
            owner_user_id = all_props.get("owner_user_id")
            owner_info: tuple[str | None, str | None] | None = None
            if owner_user_id:
                names = await self._repository.resolve_owner_names_batch(
                    conn, [owner_user_id]
                )
                owner_info = names.get(owner_user_id)
        resp = _control_response(record, all_properties=all_props)
        if owner_info:
            resp.owner_display_name = owner_info[0]
            resp.owner_email = owner_info[1]
        return resp

    async def create_control(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        request: CreateControlRequest,
    ) -> ControlResponse:
        now = utc_now_sql()
        control_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_control_permission(
                    conn,
                    user_id=user_id,
                    permission_code="controls.create",
                    framework_id=framework_id,
                )
                # Auto-revert framework to draft if published
                framework = await self._framework_repository.get_framework_by_id(
                    conn, framework_id
                )
                if framework and framework.approval_status == "approved":
                    await self._framework_repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="draft",
                        is_marketplace_visible=False,
                        updated_by=user_id,
                        now=now,
                    )
                await self._repository.create_control(
                    conn,
                    control_id=control_id,
                    framework_id=framework_id,
                    tenant_key=tenant_key,
                    control_code=request.control_code,
                    control_category_code=request.control_category_code,
                    criticality_code=request.criticality_code,
                    control_type=request.control_type,
                    automation_potential=request.automation_potential,
                    requirement_id=request.requirement_id,
                    sort_order=request.sort_order,
                    created_by=user_id,
                    now=now,
                )
                props = _collect_create_props(request)
                if props:
                    await self._repository.upsert_control_properties(
                        conn,
                        control_id=control_id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                if request.responsible_teams:
                    await _set_groups_locked(
                        conn,
                        request.responsible_teams,
                        locked=True,
                        updated_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="control",
                        entity_id=control_id,
                        event_type=FrameworkAuditEventType.CONTROL_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "control_code": request.control_code,
                            "name": request.name,
                            "auto_reverted_to_draft": str(
                                framework.approval_status == "approved"
                                if framework
                                else False
                            ),
                        },
                    ),
                )
                record = await self._repository.get_control_by_id(conn, control_id)
        await self._cache.delete_pattern("frameworks:list:*")
        await self._auto_version_if_approved(
            framework_id=framework_id,
            change_type="control_added",
            change_summary=f"Added control '{request.control_code}'",
        )
        return _control_response(record)

    async def update_control(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        control_id: str,
        request: UpdateControlRequest,
    ) -> ControlResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_control_permission(
                    conn,
                    user_id=user_id,
                    permission_code="controls.update",
                    framework_id=framework_id,
                )
                # Verify control belongs to framework
                existing = await self._repository.get_control_by_id(conn, control_id)
                if existing is None or existing.framework_id != framework_id:
                    raise NotFoundError(
                        f"Control '{control_id}' not found in framework '{framework_id}'"
                    )
                # Auto-revert framework to draft if published
                framework = await self._framework_repository.get_framework_by_id(
                    conn, framework_id
                )
                auto_reverted = False
                if framework and framework.approval_status == "approved":
                    await self._framework_repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="draft",
                        is_marketplace_visible=False,
                        updated_by=user_id,
                        now=now,
                    )
                    auto_reverted = True
                updated = await self._repository.update_control(
                    conn,
                    control_id,
                    control_category_code=request.control_category_code,
                    criticality_code=request.criticality_code,
                    control_type=request.control_type,
                    automation_potential=request.automation_potential,
                    requirement_id=request.requirement_id,
                    sort_order=request.sort_order,
                    updated_by=user_id,
                    now=now,
                )
                if not updated:
                    raise NotFoundError(f"Control '{control_id}' not found")
                props = _collect_update_props(request)
                if props:
                    await self._repository.upsert_control_properties(
                        conn,
                        control_id=control_id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                # Sync group locks: unlock old groups no longer referenced, lock new ones
                if request.responsible_teams is not None:
                    old_teams = (
                        _parse_json_list(
                            (
                                await self._repository.get_all_properties(
                                    conn, control_id
                                )
                            ).get("responsible_teams")
                        )
                        or []
                    )
                    new_teams = request.responsible_teams
                    to_unlock = [g for g in old_teams if g not in new_teams]
                    to_lock = [g for g in new_teams if g not in old_teams]
                    if to_unlock:
                        # Only unlock groups not referenced by any other control
                        still_used = await _groups_still_in_use(
                            conn, to_unlock, exclude_control_id=control_id
                        )
                        safe_unlock = [g for g in to_unlock if g not in still_used]
                        if safe_unlock:
                            await _set_groups_locked(
                                conn,
                                safe_unlock,
                                locked=False,
                                updated_by=user_id,
                                now=now,
                            )
                    if to_lock:
                        await _set_groups_locked(
                            conn, to_lock, locked=True, updated_by=user_id, now=now
                        )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="control",
                        entity_id=control_id,
                        event_type=FrameworkAuditEventType.CONTROL_UPDATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "auto_reverted_to_draft": str(auto_reverted),
                        },
                    ),
                )
                record = await self._repository.get_control_by_id(conn, control_id)
        await self._cache.delete_pattern("frameworks:list:*")
        await self._auto_version_if_approved(
            framework_id=framework_id,
            change_type="control_modified",
            change_summary=f"Modified control '{existing.control_code}'",
        )
        return _control_response(record)

    async def delete_control(
        self, *, user_id: str, tenant_key: str, framework_id: str, control_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_control_permission(
                    conn,
                    user_id=user_id,
                    permission_code="controls.delete",
                    framework_id=framework_id,
                )
                existing = await self._repository.get_control_by_id(conn, control_id)
                if existing is None or existing.framework_id != framework_id:
                    raise NotFoundError(
                        f"Control '{control_id}' not found in framework '{framework_id}'"
                    )
                # Auto-revert framework to draft if published
                framework = await self._framework_repository.get_framework_by_id(
                    conn, framework_id
                )
                auto_reverted = False
                if framework and framework.approval_status == "approved":
                    await self._framework_repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="draft",
                        is_marketplace_visible=False,
                        updated_by=user_id,
                        now=now,
                    )
                    auto_reverted = True
                deleted = await self._repository.soft_delete_control(
                    conn,
                    control_id,
                    deleted_by=user_id,
                    now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Control '{control_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="control",
                        entity_id=control_id,
                        event_type=FrameworkAuditEventType.CONTROL_DELETED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": framework_id,
                            "auto_reverted_to_draft": str(auto_reverted),
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        await self._auto_version_if_approved(
            framework_id=framework_id,
            change_type="control_removed",
            change_summary=f"Removed control '{existing.control_code}'",
        )

    async def export_controls(
        self,
        *,
        user_id: str,
        framework_id: str,
        fmt: str = "csv",
        simplified: bool = False,
    ):
        """Export all controls in a framework as CSV, JSON, or XLSX."""
        from fastapi.responses import StreamingResponse as _SR

        async with self._database_pool.acquire() as conn:
            await self._require_control_permission(
                conn,
                user_id=user_id,
                permission_code="controls.view",
                framework_id=framework_id,
            )
            raw = await self._repository.list_controls_with_properties(
                conn, framework_id=framework_id
            )

        # Resolve owner emails in batch
        owner_ids = [r["owner_user_id"] for r in raw if r.get("owner_user_id")]
        owner_map: dict[str, tuple] = {}
        if owner_ids:
            async with self._database_pool.acquire() as conn:
                owner_map = await self._repository.resolve_owner_names_batch(
                    conn, owner_ids
                )

        import json as _json

        rows = []
        for r in raw:
            owner_uid = r.get("owner_user_id") or ""
            owner_info = owner_map.get(owner_uid, (None, None))
            tags_raw = r.get("tags")
            tags_list: list[str] = []
            if tags_raw:
                try:
                    tags_list = (
                        _json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
                    )
                except Exception:
                    pass
            teams_raw = r.get("responsible_teams")
            teams_list: list[str] = []
            if teams_raw:
                try:
                    teams_list = (
                        _json.loads(teams_raw)
                        if isinstance(teams_raw, str)
                        else teams_raw
                    )
                except Exception:
                    pass
            row = {
                "control_code": r.get("control_code", ""),
                "name": r.get("name", ""),
                "description": r.get("description", "") or "",
                "guidance": r.get("guidance", "") or "",
                "implementation_notes": r.get("implementation_notes", "") or "",
                "criticality_code": r.get("criticality_code", ""),
                "control_type": r.get("control_type", ""),
                "automation_potential": r.get("automation_potential", ""),
                "control_category_code": r.get("control_category_code", ""),
                "requirement_code": r.get("requirement_code", "") or "",
                "tags": "; ".join(tags_list),
                "owner_email": owner_info[1] or "" if owner_info else "",
                "framework_code": r.get("framework_code", "") or "",
            }
            if not simplified:
                row["id"] = r.get("id", "")
                row["framework_id"] = r.get("framework_id", "")
                row["requirement_id"] = r.get("requirement_id", "") or ""
                row["owner_user_id"] = owner_uid
                row["responsible_teams"] = "; ".join(teams_list)
            rows.append(row)

        if simplified:
            columns = [
                "control_code",
                "name",
                "criticality_code",
                "control_type",
                "automation_potential",
                "control_category_code",
                "requirement_code",
                "tags",
                "owner_email",
                "description",
                "guidance",
                "implementation_notes",
                "framework_code",
            ]
        else:
            columns = [
                "id",
                "control_code",
                "name",
                "criticality_code",
                "control_type",
                "automation_potential",
                "control_category_code",
                "requirement_code",
                "tags",
                "owner_email",
                "owner_user_id",
                "responsible_teams",
                "description",
                "guidance",
                "implementation_notes",
                "framework_id",
                "requirement_id",
                "framework_code",
            ]

        if fmt == "json":
            data = to_json(rows)
        elif fmt == "xlsx":
            data = to_xlsx(rows, columns, sheet_name="Controls")
        else:
            data = to_csv(rows, columns)

        return make_streaming_response(data, fmt, f"controls_export")

    async def import_controls(
        self,
        *,
        user_id: str,
        tenant_key: str,
        framework_id: str,
        file_bytes: bytes,
        filename: str,
        dry_run: bool = False,
    ):
        """Import controls from CSV or JSON into a framework. Upserts by control_code."""
        from .schemas import ImportControlError, ImportControlsResult
        import json as _json

        async with self._database_pool.acquire() as conn:
            await self._require_control_permission(
                conn,
                user_id=user_id,
                permission_code="controls.create",
                framework_id=framework_id,
            )

        try:
            rows = parse_import(file_bytes, filename)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc

        now = utc_now_sql()
        created = 0
        updated = 0
        skipped = 0
        errors: list[ImportControlError] = []
        warnings: list[str] = []

        async with self._database_pool.acquire() as conn:
            existing_by_code = await self._repository.list_controls_by_code(
                conn, framework_id=framework_id
            )

        for row_idx, row in enumerate(rows, start=2):
            control_code = (row.get("control_code") or "").strip()
            name = (row.get("name") or "").strip()

            if not control_code:
                errors.append(
                    ImportControlError(
                        row=row_idx,
                        key=None,
                        field="control_code",
                        message="control_code is required",
                    )
                )
                continue
            if not name:
                errors.append(
                    ImportControlError(
                        row=row_idx,
                        key=control_code,
                        field="name",
                        message="name is required",
                    )
                )
                continue

            # Parse tags
            tags_str = (row.get("tags") or "").strip()
            tags: list[str] = (
                [t.strip() for t in tags_str.replace(";", ",").split(",") if t.strip()]
                if tags_str
                else []
            )

            try:
                if control_code in existing_by_code:
                    # Update
                    if not dry_run:
                        control_id = existing_by_code[control_code]
                        async with self._database_pool.acquire() as conn:
                            async with conn.transaction():
                                await self._repository.update_control(
                                    conn,
                                    control_id,
                                    control_category_code=row.get(
                                        "control_category_code"
                                    )
                                    or None,
                                    criticality_code=row.get("criticality_code")
                                    or None,
                                    control_type=row.get("control_type") or None,
                                    automation_potential=row.get("automation_potential")
                                    or None,
                                    updated_by=user_id,
                                    now=now,
                                )
                                props: dict[str, str] = {}
                                if name:
                                    props["name"] = name
                                if row.get("description"):
                                    props["description"] = row["description"]
                                if row.get("guidance"):
                                    props["guidance"] = row["guidance"]
                                if row.get("implementation_notes"):
                                    props["implementation_notes"] = row[
                                        "implementation_notes"
                                    ]
                                if tags:
                                    props["tags"] = _json.dumps(tags)
                                if props:
                                    await self._repository.upsert_control_properties(
                                        conn,
                                        control_id=control_id,
                                        properties=props,
                                        created_by=user_id,
                                        now=now,
                                    )
                    updated += 1
                else:
                    # Create
                    if not dry_run:
                        import uuid as _uuid

                        control_id = str(_uuid.uuid4())
                        async with self._database_pool.acquire() as conn:
                            async with conn.transaction():
                                await self._repository.create_control(
                                    conn,
                                    control_id=control_id,
                                    framework_id=framework_id,
                                    tenant_key=tenant_key,
                                    control_code=control_code,
                                    control_category_code=row.get(
                                        "control_category_code"
                                    )
                                    or "general",
                                    criticality_code=row.get("criticality_code")
                                    or "medium",
                                    control_type=row.get("control_type")
                                    or "preventive",
                                    automation_potential=row.get("automation_potential")
                                    or "manual",
                                    requirement_id=None,
                                    sort_order=0,
                                    created_by=user_id,
                                    now=now,
                                )
                                props = {"name": name}
                                if row.get("description"):
                                    props["description"] = row["description"]
                                if row.get("guidance"):
                                    props["guidance"] = row["guidance"]
                                if row.get("implementation_notes"):
                                    props["implementation_notes"] = row[
                                        "implementation_notes"
                                    ]
                                if tags:
                                    props["tags"] = _json.dumps(tags)
                                await self._repository.upsert_control_properties(
                                    conn,
                                    control_id=control_id,
                                    properties=props,
                                    created_by=user_id,
                                    now=now,
                                )
                    created += 1
            except Exception as exc:
                errors.append(
                    ImportControlError(row=row_idx, key=control_code, message=str(exc))
                )

        if not dry_run and (created > 0 or updated > 0):
            await self._cache.delete_pattern("frameworks:list:*")

    async def _auto_version_if_approved(
        self,
        *,
        framework_id: str,
        change_type: str,
        change_summary: str | None = None,
    ) -> None:
        """Create an auto-version if the framework is approved and has no draft version."""
        try:
            async with self._database_pool.acquire() as conn:
                fw = await self._framework_repository.get_framework_by_id(
                    conn, framework_id
                )
                if not fw or fw.approval_status != "approved":
                    return
                existing_draft = await self._version_repository.has_draft_version(
                    conn, framework_id=framework_id
                )
                if existing_draft:
                    return
                next_version = await self._version_repository.next_version_number(
                    conn, framework_id=framework_id
                )
                version_id = str(uuid.uuid4())
                now = utc_now_sql()
                severity_map = {
                    "control_added": "minor",
                    "control_removed": "minor",
                    "control_modified": "patch",
                }
                severity = severity_map.get(change_type, "minor")
                await self._version_repository.create_version(
                    conn,
                    version_id=version_id,
                    framework_id=framework_id,
                    version_code=next_version,
                    change_severity=severity,
                    previous_version_id=None,
                    created_by="system",
                    now=now,
                )
                props = {
                    "auto_created": "true",
                    "auto_change_type": change_type,
                }
                if change_summary:
                    props["change_summary"] = change_summary
                    props["auto_change_summary"] = change_summary
                await self._version_repository.upsert_version_properties(
                    conn,
                    version_id=version_id,
                    properties=props,
                    created_by="system",
                    now=now,
                )
                self._logger.info(
                    "Auto-created version %s for framework %s (%s)",
                    next_num,
                    framework_id,
                    change_type,
                )
        except Exception:
            self._logger.warning(
                "Failed to auto-create version for framework %s",
                framework_id,
                exc_info=True,
            )

        return ImportControlsResult(
            created=created,
            updated=updated,
            skipped=skipped,
            warnings=warnings,
            errors=errors,
            dry_run=dry_run,
        )

    async def get_import_template(self, *, fmt: str = "csv"):
        """Return a downloadable import template."""
        columns = [
            "control_code",
            "name",
            "criticality_code",
            "control_type",
            "automation_potential",
            "control_category_code",
            "requirement_code",
            "tags",
            "owner_email",
            "description",
            "guidance",
            "implementation_notes",
        ]
        examples = {
            "control_code": "CC-6.1",
            "name": "Multi-Factor Authentication",
            "criticality_code": "high",
            "control_type": "preventive",
            "automation_potential": "full",
            "control_category_code": "access",
            "requirement_code": "CC6",
            "tags": "authentication; mfa; access",
            "owner_email": "owner@company.com",
            "description": "Require MFA for all privileged accounts",
            "guidance": "Configure MFA in identity provider settings",
            "implementation_notes": "Use TOTP or hardware key",
        }
        instructions = {
            "control_code": "Required. Unique code within this framework (e.g. CC-6.1)",
            "name": "Required. Display name of the control",
            "criticality_code": "Optional. One of: critical, high, medium, low (default: medium)",
            "control_type": "Optional. One of: preventive, detective, corrective, compensating",
            "automation_potential": "Optional. One of: full, partial, manual",
            "control_category_code": "Optional. Category code (default: general)",
            "requirement_code": "Optional. Requirement code this control belongs to",
            "tags": "Optional. Comma or semicolon-separated tags",
            "owner_email": "Optional. Email of the control owner",
            "description": "Optional. Full description",
            "guidance": "Optional. Implementation guidance",
            "implementation_notes": "Optional. Additional notes",
        }
        if fmt == "xlsx":
            data = to_xlsx_template(
                columns, examples, "Controls Template", instructions
            )
        else:
            data = to_csv([examples], columns)
        return make_streaming_response(data, fmt, "controls_import_template")


def _collect_create_props(request: CreateControlRequest) -> dict[str, str]:
    """Collect EAV properties from create request, serialising JSON fields."""
    props: dict[str, str] = {}
    if request.name:
        props["name"] = request.name
    if request.description:
        props["description"] = request.description
    if request.guidance:
        props["guidance"] = request.guidance
    if request.implementation_notes:
        props["implementation_notes"] = request.implementation_notes
    if request.implementation_guidance:
        props["implementation_guidance"] = json.dumps(request.implementation_guidance)
    if request.owner_user_id:
        props["owner_user_id"] = request.owner_user_id
    if request.responsible_teams:
        props["responsible_teams"] = json.dumps(request.responsible_teams)
    if request.tags:
        props["tags"] = json.dumps(request.tags)
    if request.properties:
        props.update(request.properties)
    return props


def _collect_update_props(request: UpdateControlRequest) -> dict[str, str]:
    """Collect EAV properties from update request, serialising JSON fields."""
    props: dict[str, str] = {}
    if request.name is not None:
        props["name"] = request.name
    if request.description is not None:
        props["description"] = request.description
    if request.guidance is not None:
        props["guidance"] = request.guidance
    if request.implementation_notes is not None:
        props["implementation_notes"] = request.implementation_notes
    if request.implementation_guidance is not None:
        props["implementation_guidance"] = json.dumps(request.implementation_guidance)
    if request.owner_user_id is not None:
        props["owner_user_id"] = request.owner_user_id
    if request.responsible_teams is not None:
        props["responsible_teams"] = json.dumps(request.responsible_teams)
    if request.tags is not None:
        props["tags"] = json.dumps(request.tags)
    if request.properties:
        props.update(request.properties)
    return props


async def _set_groups_locked(
    conn, group_ids: list[str], *, locked: bool, updated_by: str, now
) -> None:
    """Set is_locked on the given group IDs. Does not touch is_system groups."""
    if not group_ids:
        return
    await conn.execute(
        """
        UPDATE "03_auth_manage"."17_fct_user_groups"
        SET is_locked = $1, updated_at = $2, updated_by = $3
        WHERE id = ANY($4::uuid[]) AND is_deleted = FALSE AND is_system = FALSE
        """,
        locked,
        now,
        updated_by,
        group_ids,
    )


async def _groups_still_in_use(
    conn, group_ids: list[str], *, exclude_control_id: str
) -> set[str]:
    """Return subset of group_ids that appear in responsible_teams of any other control."""
    if not group_ids:
        return set()
    rows = await conn.fetch(
        """
        SELECT property_value
        FROM "05_grc_library"."23_dtl_control_properties"
        WHERE property_key = 'responsible_teams'
          AND control_id != $1::uuid
        """,
        exclude_control_id,
    )
    used: set[str] = set()
    for row in rows:
        try:
            teams = json.loads(row["property_value"])
            if isinstance(teams, list):
                used.update(str(g) for g in teams)
        except (json.JSONDecodeError, TypeError):
            pass
    return {g for g in group_ids if g in used}


def _parse_json_list(value: str | None) -> list[str] | None:
    """Safely parse a JSON array string, returning None on failure."""
    if not value:
        return None
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else None
    except (json.JSONDecodeError, TypeError):
        return None


async def _resolve_control_owners(database_pool, repository, items: list) -> list:
    """Batch-resolve owner display name and email for a list of ControlResponse items."""
    owner_ids = [item.owner_user_id for item in items if item.owner_user_id]
    if not owner_ids:
        return items
    async with database_pool.acquire() as conn:
        owner_map = await repository.resolve_owner_names_batch(conn, owner_ids)
    for item in items:
        if item.owner_user_id:
            info = owner_map.get(item.owner_user_id)
            if info:
                item.owner_display_name = info[0]
                item.owner_email = info[1]
    return items


def _control_response(
    r, all_properties: dict[str, str] | None = None
) -> ControlResponse:
    # Merge view-flattened fields with any extra properties
    props = all_properties or {}
    return ControlResponse(
        id=r.id,
        framework_id=r.framework_id,
        requirement_id=r.requirement_id,
        tenant_key=r.tenant_key,
        control_code=r.control_code,
        control_category_code=r.control_category_code,
        category_name=r.category_name,
        criticality_code=r.criticality_code,
        criticality_name=r.criticality_name,
        control_type=r.control_type,
        automation_potential=r.automation_potential,
        sort_order=r.sort_order,
        version=r.version,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
        guidance=r.guidance,
        implementation_notes=r.implementation_notes,
        implementation_guidance=_parse_json_list(props.get("implementation_guidance")),
        owner_user_id=props.get("owner_user_id"),
        responsible_teams=_parse_json_list(props.get("responsible_teams")),
        tags=_parse_json_list(props.get("tags")),
        framework_code=r.framework_code,
        framework_name=r.framework_name,
        requirement_code=r.requirement_code,
        requirement_name=r.requirement_name,
        test_count=r.test_count,
        properties=props if props else None,
    )
