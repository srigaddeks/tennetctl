from __future__ import annotations

import asyncio
import json
import uuid
from importlib import import_module

import asyncpg

from .repository import FrameworkRepository
from .schemas import (
    BundleImportError,
    BundleImportResult,
    ControlDiff,
    CreateFrameworkRequest,
    FrameworkBundle,
    FrameworkDiff,
    FrameworkListResponse,
    FrameworkResponse,
    RequirementDiff,
    ReviewSelectionResponse,
    SubmitForReviewRequest,
    UpdateFrameworkRequest,
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
_controls_repo_module = import_module("backend.05_grc_library.05_controls.repository")
_spreadsheet_module = import_module("backend.01_core.spreadsheet")
_versions_repo_module = import_module("backend.05_grc_library.03_versions.repository")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
FrameworkAuditEventType = _constants_module.FrameworkAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
ControlRepository = _controls_repo_module.ControlRepository
VersionRepository = _versions_repo_module.VersionRepository
make_streaming_response = _spreadsheet_module.make_streaming_response

_CACHE_TTL_FRAMEWORKS = 300  # 5 minutes


@instrument_class_methods(
    namespace="grc.frameworks.service",
    logger_name="backend.grc.frameworks.instrumentation",
)
class FrameworkService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.frameworks")

    async def _has_permission_any_scope(
        self, conn, user_id: str, permission_code: str
    ) -> bool:
        # Check if user holds the permission at any scope (platform or any org/workspace)
        row = await conn.fetchval(
            """
            SELECT 1
            FROM "03_auth_manage"."18_lnk_group_memberships" gm
            JOIN "03_auth_manage"."17_fct_user_groups" g ON g.id = gm.group_id
            JOIN "03_auth_manage"."19_lnk_group_role_assignments" gra ON gra.group_id = gm.group_id
            JOIN "03_auth_manage"."20_lnk_role_feature_permissions" rfp ON rfp.role_id = gra.role_id
            JOIN "03_auth_manage"."15_dim_feature_permissions" fp ON fp.id = rfp.feature_permission_id
            WHERE gm.user_id = $1::UUID
              AND fp.code = $2
              AND gm.is_active = TRUE AND gm.is_deleted = FALSE
              AND (gm.effective_to IS NULL OR gm.effective_to > NOW())
              AND gra.is_active = TRUE AND gra.is_deleted = FALSE
              AND (gra.effective_to IS NULL OR gra.effective_to > NOW())
              AND rfp.is_active = TRUE AND rfp.is_deleted = FALSE
              AND g.is_active = TRUE AND g.is_deleted = FALSE
            LIMIT 1
            """,
            user_id,
            permission_code,
        )
        return bool(row)

    async def _require_framework_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        scope_org_id: str | None,
        scope_workspace_id: str | None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=scope_org_id,
            scope_workspace_id=scope_workspace_id,
        )

    async def list_frameworks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        category: str | None = None,
        framework_type: str | None = None,
        approval_status: str | None = None,
        is_active: bool | None = None,
        is_marketplace_visible: bool | None = None,
        search: str | None = None,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        deployed_org_id: str | None = None,
        deployed_workspace_id: str | None = None,
        only_engaged: bool = False,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> FrameworkListResponse:
        async with self._database_pool.acquire() as conn:
            if is_marketplace_visible is True:
                # Marketplace is public to anyone with the feature permission at any scope
                if not await self._has_permission_any_scope(
                    conn, user_id, "frameworks.view"
                ):
                    raise AuthorizationError("Permission required: frameworks.view")
            else:
                # Fallback to deployed scope if explicit scope is missing, so org-scoped users can list their own deployments
                check_org = scope_org_id or deployed_org_id
                check_ws = scope_workspace_id or deployed_workspace_id
                await require_permission(
                    conn,
                    user_id,
                    "frameworks.view",
                    scope_org_id=check_org,
                    scope_workspace_id=check_ws,
                )

        # Marketplace visibility is global within the tenant once a framework is approved
        # for publishing. We still check org/workspace permission above, but we must not
        # scope-filter the returned marketplace catalog or regular users will see an empty
        # library unless the source framework belongs to their current org/workspace.
        list_scope_org_id = None if is_marketplace_visible else scope_org_id
        list_scope_workspace_id = None if is_marketplace_visible else scope_workspace_id

        has_filters = any(
            [
                category,
                framework_type,
                approval_status,
                search,
                list_scope_org_id,
                list_scope_workspace_id,
                deployed_org_id,
                deployed_workspace_id,
                is_active is not None,
                is_marketplace_visible is not None,
                only_engaged,
            ]
        )
        cache_key = f"frameworks:list:{tenant_key}"
        if not has_filters and limit >= 100 and offset == 0:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return FrameworkListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            is_admin = await self._has_permission_any_scope(conn, user_id, "frameworks.update")
            records, total = await self._repository.list_frameworks(
                conn,
                tenant_key=tenant_key,
                category=category,
                framework_type=framework_type,
                approval_status=approval_status,
                is_active=is_active,
                is_marketplace_visible=is_marketplace_visible,
                search=search,
                scope_org_id=list_scope_org_id,
                scope_workspace_id=list_scope_workspace_id,
                deployed_org_id=deployed_org_id,
                deployed_workspace_id=deployed_workspace_id,
                only_engaged=only_engaged,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
                mask_status=(approval_status == "approved" and not is_admin),
            )
        items = [_catalog_response(r) for r in records]
        result = FrameworkListResponse(items=items, total=total)
        if not has_filters and limit >= 100 and offset == 0:
            await self._cache.set(
                cache_key, result.model_dump_json(), _CACHE_TTL_FRAMEWORKS
            )
        return result

    async def get_framework(
        self, *, user_id: str, framework_id: str
    ) -> FrameworkResponse:
        async with self._database_pool.acquire() as conn:
            # First fetch without masking to check perms and visibility
            record = await self._repository.get_framework_by_id(conn, framework_id, mask_status=False)
            if record is None:
                raise NotFoundError(f"Framework '{framework_id}' not found")

            # Determine if we should mask the status (e.g. for marketplace view by non-admins)
            is_admin = await self._has_permission_any_scope(conn, user_id, "frameworks.update")
            mask_status = record.is_marketplace_visible and not is_admin

            if mask_status:
                record = await self._repository.get_framework_by_id(conn, framework_id, mask_status=True)

            if record.is_marketplace_visible:
                if not await self._has_permission_any_scope(
                    conn, user_id, "frameworks.view"
                ):
                    raise AuthorizationError("Permission required: frameworks.view")
            else:
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.view",
                    scope_org_id=record.scope_org_id,
                    scope_workspace_id=record.scope_workspace_id,
                )
        return _catalog_response(record)

    async def create_framework(
        self, *, user_id: str, tenant_key: str, request: CreateFrameworkRequest
    ) -> FrameworkResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.create",
                    scope_org_id=request.scope_org_id,
                    scope_workspace_id=request.scope_workspace_id,
                )
                existing = await self._repository.get_framework_by_code(
                    conn,
                    request.framework_code,
                    tenant_key,
                    include_deleted=True,
                )
                if existing:
                    status_text = (
                        " (archived/deleted)" if existing.is_active is False else ""
                    )
                    raise ConflictError(
                        f"Framework code '{request.framework_code}' is already in use{status_text}."
                    )
                try:
                    framework = await self._repository.create_framework(
                        conn,
                        framework_id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        framework_code=request.framework_code,
                        framework_type_code=request.framework_type_code,
                        framework_category_code=request.framework_category_code,
                        scope_org_id=request.scope_org_id,
                        scope_workspace_id=request.scope_workspace_id,
                        created_by=user_id,
                        now=now,
                    )
                except asyncpg.UniqueViolationError:
                    raise ConflictError(
                        f"Framework code '{request.framework_code}' was claimed by concurrent request."
                    )
                # Write EAV properties
                props: dict[str, str] = {}
                if request.name:
                    props["name"] = request.name
                if request.description:
                    props["description"] = request.description
                if request.short_description:
                    props["short_description"] = request.short_description
                if request.publisher_type:
                    props["publisher_type"] = request.publisher_type
                if request.publisher_name:
                    props["publisher_name"] = request.publisher_name
                if request.logo_url:
                    props["logo_url"] = request.logo_url
                if request.documentation_url:
                    props["documentation_url"] = request.documentation_url
                if request.properties:
                    props.update(request.properties)
                if props:
                    await self._repository.upsert_framework_properties(
                        conn,
                        framework_id=framework.id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework",
                        entity_id=framework.id,
                        event_type=FrameworkAuditEventType.FRAMEWORK_CREATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_code": request.framework_code,
                            "framework_type_code": request.framework_type_code,
                            "framework_category_code": request.framework_category_code,
                            "name": request.name,
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        # Re-fetch from view for full response
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_framework_by_id(conn, framework.id)
        return _catalog_response(record)

    async def update_framework(
        self, *, user_id: str, framework_id: str, request: UpdateFrameworkRequest
    ) -> FrameworkResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_framework_by_id(
                    conn, framework_id
                )
                if existing is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.update",
                    scope_org_id=existing.scope_org_id,
                    scope_workspace_id=existing.scope_workspace_id,
                )
                # Auto-revert to draft if framework is already published and properties are being updated
                auto_revert_to_draft = existing.approval_status == "approved" and (
                    request.name is not None
                    or request.description is not None
                    or request.short_description is not None
                    or request.publisher_type is not None
                    or request.publisher_name is not None
                    or request.logo_url is not None
                    or request.documentation_url is not None
                    or (request.properties and len(request.properties) > 0)
                )
                framework = await self._repository.update_framework(
                    conn,
                    framework_id,
                    framework_type_code=request.framework_type_code,
                    framework_category_code=request.framework_category_code,
                    approval_status="draft"
                    if auto_revert_to_draft
                    else request.approval_status,
                    is_marketplace_visible=existing.is_marketplace_visible
                    if auto_revert_to_draft
                    else request.is_marketplace_visible,
                    updated_by=user_id,
                    now=now,
                )
                if framework is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                # Update EAV properties
                props: dict[str, str] = {}
                if request.name is not None:
                    props["name"] = request.name
                if request.description is not None:
                    props["description"] = request.description
                if request.short_description is not None:
                    props["short_description"] = request.short_description
                if request.publisher_type is not None:
                    props["publisher_type"] = request.publisher_type
                if request.publisher_name is not None:
                    props["publisher_name"] = request.publisher_name
                if request.logo_url is not None:
                    props["logo_url"] = request.logo_url
                if request.documentation_url is not None:
                    props["documentation_url"] = request.documentation_url
                if request.properties:
                    props.update(request.properties)
                if props:
                    await self._repository.upsert_framework_properties(
                        conn,
                        framework_id=framework_id,
                        properties=props,
                        created_by=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=framework.tenant_key,
                        entity_type="framework",
                        entity_id=framework_id,
                        event_type=FrameworkAuditEventType.FRAMEWORK_UPDATED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_code": framework.framework_code,
                            "auto_reverted_to_draft": str(auto_revert_to_draft),
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_framework_by_id(conn, framework_id)
        return _catalog_response(record)

    async def delete_framework(self, *, user_id: str, framework_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_framework_by_id(
                    conn, framework_id
                )
                if existing is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.delete",
                    scope_org_id=existing.scope_org_id,
                    scope_workspace_id=existing.scope_workspace_id,
                )
                deleted = await self._repository.soft_delete_framework_graph(
                    conn,
                    framework_id,
                    deleted_by=user_id,
                    now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                # Fetch tenant_key for audit from the record before deletion
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=existing.tenant_key,
                        entity_type="framework",
                        entity_id=framework_id,
                        event_type=FrameworkAuditEventType.FRAMEWORK_DELETED.value,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={},
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")

    # ── Approval Workflow ─────────────────────────────────────────────────

    _SUBMIT_FROM = frozenset({"draft", "rejected", "approved"})
    _APPROVE_FROM = frozenset({"pending_review"})

    async def submit_for_review(
        self,
        *,
        user_id: str,
        framework_id: str,
        request: SubmitForReviewRequest | None = None,
    ) -> FrameworkResponse:
        """Submit a framework for admin review. Both super admins and regular users can submit.

        If request is provided with requirement_ids or control_ids, only those items are submitted for review.
        Otherwise, all requirements and controls are submitted (backward compatible).
        """
        now = utc_now_sql()

        req_ids = request.requirement_ids if request else []
        ctrl_ids = request.control_ids if request else []
        notes = request.notes if request else None

        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                record = await self._repository.get_framework_by_id(conn, framework_id)
                if record is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                if record.approval_status not in self._SUBMIT_FROM:
                    raise ConflictError(
                        f"Cannot submit: current status is '{record.approval_status}'"
                    )
                # Require 'frameworks.submit' permission at the framework's scope.
                # If the user has it as a platform-level permission (Super Admin),
                # require_permission handles that automatically by checking all branches.
                await self._require_framework_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.submit",
                    scope_org_id=record.scope_org_id,
                    scope_workspace_id=record.scope_workspace_id,
                )
                framework = await self._repository.update_framework(
                    conn,
                    framework_id,
                    approval_status="pending_review",
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=record.tenant_key,
                        entity_type="framework",
                        entity_id=framework_id,
                        event_type="framework_submitted_for_review",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"from_status": record.approval_status},
                    ),
                )

                # Store submitted requirements and controls in EAV properties
                review_props: dict[str, str] = {}
                if req_ids:
                    review_props["submitted_requirements"] = json.dumps(req_ids)
                if ctrl_ids:
                    review_props["submitted_controls"] = json.dumps(ctrl_ids)
                if notes:
                    review_props["review_notes"] = notes
                review_props["review_submitted_at"] = str(now)

                if review_props:
                    await self._repository.upsert_framework_properties(
                        conn,
                        framework_id=framework_id,
                        properties=review_props,
                        created_by=user_id,
                        now=now,
                    )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            fresh = await self._repository.get_framework_by_id(conn, framework_id)
        return _catalog_response(fresh)

    # ── Review Selection ─────────────────────────────────────────────────────

    async def get_review_selection(
        self, *, framework_id: str
    ) -> ReviewSelectionResponse:
        """Get the current review submission details for a framework."""
        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT property_key, property_value
                FROM "05_grc_library"."20_dtl_framework_properties"
                WHERE framework_id = $1
                  AND property_key IN (
                    'submitted_requirements',
                    'submitted_controls',
                    'review_notes',
                    'review_submitted_at'
                  )
                """,
                framework_id,
            )

            prop_map = {row["property_key"]: row["property_value"] for row in rows}

            req_ids: list[str] = []
            ctrl_ids: list[str] = []

            if "submitted_requirements" in prop_map:
                try:
                    req_ids = json.loads(prop_map["submitted_requirements"])
                except (json.JSONDecodeError, TypeError):
                    pass

            if "submitted_controls" in prop_map:
                try:
                    ctrl_ids = json.loads(prop_map["submitted_controls"])
                except (json.JSONDecodeError, TypeError):
                    pass

            return ReviewSelectionResponse(
                framework_id=framework_id,
                requirement_ids=req_ids,
                control_ids=ctrl_ids,
                notes=prop_map.get("review_notes"),
                submitted_at=prop_map.get("review_submitted_at"),
            )

    async def get_review_diff(self, *, framework_id: str) -> dict:
        """Get diff between submitted items and previous approved version."""
        async with self._database_pool.acquire() as conn:
            review_selection = await self.get_review_selection(
                framework_id=framework_id
            )
            submitted_control_ids = set(review_selection.control_ids)
            submitted_req_ids = set(review_selection.requirement_ids)

            (
                prev_version_code,
                prev_controls,
            ) = await self._repository.get_previous_published_version_controls(
                conn, framework_id=framework_id
            )

            if not prev_controls:
                return {
                    "has_previous_version": False,
                    "previous_version_code": None,
                    "added": review_selection.control_ids,
                    "removed": [],
                    "added_count": len(review_selection.control_ids),
                    "removed_count": 0,
                }

            prev_control_ids = {
                c["control_id"] for c in prev_controls if c.get("control_id")
            }
            prev_control_codes = {c["control_code"] for c in prev_controls}

            submitted_controls_full = await conn.fetch(
                """
                SELECT c.id::text as control_id, c.control_code,
                       p_name.property_value AS name,
                       c.criticality_code
                FROM "05_grc_library"."13_fct_controls" c
                LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
                    ON p_name.control_id = c.id AND p_name.property_key = 'name'
                WHERE c.id = ANY($1::uuid[])
                """,
                review_selection.control_ids,
            )

            submitted_codes = {row["control_code"] for row in submitted_controls_full}

            added_ids = submitted_control_ids - prev_control_ids
            added_codes = submitted_codes - prev_control_codes

            removed_codes = prev_control_codes - submitted_codes

            added_controls = [
                {
                    "id": row["control_id"],
                    "control_code": row["control_code"],
                    "name": row["name"],
                    "criticality_code": row["criticality_code"],
                }
                for row in submitted_controls_full
                if row["control_code"] in added_codes
            ]

            removed_controls = [
                {
                    "id": c["control_id"],
                    "control_code": c["control_code"],
                    "name": c.get("name"),
                    "criticality_code": c.get("criticality_code"),
                }
                for c in prev_controls
                if c["control_code"] in removed_codes
            ]

            return {
                "has_previous_version": True,
                "previous_version_code": prev_version_code,
                "added": added_controls,
                "removed": removed_controls,
                "added_count": len(added_controls),
                "removed_count": len(removed_controls),
            }

    async def approve_framework(
        self, *, user_id: str, framework_id: str, control_ids: list[str] | None = None
    ) -> FrameworkResponse:
        """Super admin approves framework, publishes it to marketplace, and auto-creates a version snapshot.
        If the framework is a clone, the changes are merged back to the original source.
        """
        import logging

        logger = logging.getLogger(__name__)

        now = utc_now_sql()
        version_repo = VersionRepository()

        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "frameworks.approve")

                # Check if this is a clone (proposing changes to a source)
                source_id = await conn.fetchval(
                    """
                    SELECT property_value FROM "05_grc_library"."20_dtl_framework_properties"
                    WHERE framework_id = $1::uuid AND property_key = 'source_framework_id'
                    """,
                    framework_id
                )
                
                # Determine which framework record is the permanent library entry
                target_framework_id = source_id if source_id else framework_id
                is_clone = source_id is not None
                
                # Record being approved (the submission)
                submitted_record = await self._repository.get_framework_by_id(conn, framework_id)
                if submitted_record is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")

                # The framework that will be visible in the library
                library_record = submitted_record
                if is_clone:
                    library_record = await self._repository.get_framework_by_id(conn, target_framework_id)
                    if library_record is None:
                        raise NotFoundError(f"Original source framework '{target_framework_id}' not found")

                # Only block if we are approving a standalone/global framework that is already approved
                if not is_clone and library_record.approval_status == "approved":
                    raise ConflictError(
                        f"Cannot approve: '{library_record.name}' is already approved."
                    )

                # Ensure marketplace-published frameworks use global library sentinel scope
                scope_org_id = (
                    library_record.scope_org_id or "00000000-0000-0000-0000-000000000010"
                )
                scope_workspace_id = (
                    library_record.scope_workspace_id or "00000000-0000-0000-0000-000000000011"
                )

                # 1. Update the official Library Framework status and metadata
                # We copy the name/description from the submission to the library record
                await self._repository.update_framework(
                    conn,
                    target_framework_id,
                    approval_status="approved",
                    is_marketplace_visible=True,
                    scope_org_id=scope_org_id,
                    scope_workspace_id=scope_workspace_id,
                    updated_by=user_id,
                    now=now,
                )
                
                # Sync metadata properties from clone to source if it's a merge
                if is_clone:
                    props_to_sync = {
                        "name": submitted_record.name,
                        "description": submitted_record.description,
                        "short_description": submitted_record.short_description,
                        "publisher_type": submitted_record.publisher_type,
                        "publisher_name": submitted_record.publisher_name,
                        "logo_url": submitted_record.logo_url,
                        "documentation_url": submitted_record.documentation_url
                    }
                    cleaned_props = {k: v for k, v in props_to_sync.items() if v is not None}
                    if cleaned_props:
                        await self._repository.upsert_framework_properties(
                            conn,
                            framework_id=target_framework_id,
                            properties=cleaned_props,
                            created_by=user_id,
                            now=now
                        )

                # 2. If it's a clone, reset the clone's marketplace visibility so it doesn't duplicate
                if is_clone:
                    await self._repository.update_framework(
                        conn,
                        framework_id,
                        approval_status="approved", 
                        is_marketplace_visible=False, # HIDDEN from library to prevent duplication
                        updated_by=user_id,
                        now=now,
                    )

                # 3. Create the version snapshot on the TARGET (Source) framework
                next_version = await version_repo.next_version_number(
                    conn, framework_id=target_framework_id
                )
                version_id = str(uuid.uuid4())
                await version_repo.create_version(
                    conn,
                    version_id=version_id,
                    framework_id=target_framework_id,
                    version_code=next_version,
                    change_severity="major",
                    previous_version_id=None,
                    created_by=user_id,
                    now=now,
                )

                # Snapshot metadata to version properties
                metadata_props = {}
                for key in ["name", "description", "short_description", "publisher_type", "publisher_name", "logo_url", "documentation_url"]:
                    val = getattr(submitted_record, key, None)
                    if val is not None:
                        metadata_props[key] = str(val)
                
                if metadata_props:
                    await version_repo.upsert_version_properties(
                        conn,
                        version_id=version_id,
                        properties=metadata_props,
                        created_by=user_id,
                        now=now,
                    )

                # 4. Snapshot controls FROM the submitted copy INTO the new library version
                # If specific control_ids were reviewed, only snapshot those.
                # If it's a clone approval, we use the submitted clone's controls.
                snapshot_ctrl_ids = (
                    control_ids if control_ids is not None and len(control_ids) > 0 else None
                )
                
                snapshot_count = await version_repo.snapshot_controls_to_version(
                    conn,
                    framework_id=framework_id, # Source the controls from the submitted record
                    version_id=version_id,     # Link them to the official library version
                    created_by=user_id,
                    now=now,
                    control_ids=snapshot_ctrl_ids,
                )
                
                await version_repo.update_version_control_count(
                    conn,
                    version_id=version_id,
                    control_count=snapshot_count,
                )
                await version_repo.update_lifecycle_state(
                    conn,
                    version_id,
                    lifecycle_state="published",
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=submitted_record.tenant_key,
                        entity_type="framework",
                        entity_id=target_framework_id,
                        event_type="framework_approved",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"version_code": next_version, "merging_from_clone": str(is_clone)},
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            fresh = await self._repository.get_framework_by_id(conn, target_framework_id)
        return _catalog_response(fresh)
    async def reject_framework(
        self, *, user_id: str, framework_id: str, reason: str | None = None
    ) -> FrameworkResponse:
        """Super admin rejects framework."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "frameworks.approve")
                record = await self._repository.get_framework_by_id(conn, framework_id)
                if record is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                if record.approval_status == "rejected":
                    raise ConflictError(f"Cannot reject: already rejected")
                await self._repository.update_framework(
                    conn,
                    framework_id,
                    approval_status="pending_review",
                    is_marketplace_visible=False,
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=record.tenant_key,
                        entity_type="framework",
                        entity_id=framework_id,
                        event_type="framework_rejected",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"reason": reason or ""},
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            fresh = await self._repository.get_framework_by_id(conn, framework_id)
        return _catalog_response(fresh)

    async def update_framework_status(
        self, *, user_id: str, framework_id: str, new_status: str
    ) -> FrameworkResponse:
        """Update framework approval status directly."""
        valid = {"draft", "pending_review", "approved", "rejected"}
        if new_status not in valid:
            raise ConflictError(f"Invalid status. Use: {', '.join(valid)}")
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "frameworks.approve")
                record = await self._repository.get_framework_by_id(conn, framework_id)
                if record is None:
                    raise NotFoundError(f"Framework '{framework_id}' not found")
                if record.approval_status == new_status:
                    return _catalog_response(record)
                # Hide from marketplace if rejected
                visibility = record.is_marketplace_visible
                if new_status == "rejected":
                    visibility = False
                elif new_status == "approved":
                    # Validate that the framework has at least one published version before approving
                    # (Unless it's a clone being approved as part of a merge submittal, 
                    # which is handled in approve_framework)
                    latest_ver = await conn.fetchval(
                        """
                        SELECT version_code FROM "05_grc_library"."11_fct_framework_versions"
                        WHERE framework_id = $1 AND lifecycle_state = 'published' AND is_deleted = FALSE
                        ORDER BY created_at DESC LIMIT 1
                        """,
                        framework_id
                    )
                    if not latest_ver:
                        raise _errors_module.ValidationError(
                            "Framework cannot be approved without at least one published version. "
                            "Please use the 'Review and Approve' workflow to snapshot and publish a version."
                        )
                    visibility = True

                await self._repository.update_framework(
                    conn,
                    framework_id,
                    approval_status=new_status,
                    is_marketplace_visible=visibility,
                    updated_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=record.tenant_key,
                        entity_type="framework",
                        entity_id=framework_id,
                        event_type="framework_status_changed",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "from_status": record.approval_status,
                            "to_status": new_status,
                        },
                    ),
                )
        await self._cache.delete_pattern("frameworks:list:*")
        async with self._database_pool.acquire() as conn:
            fresh = await self._repository.get_framework_by_id(conn, framework_id)
        return _catalog_response(fresh)

    # ── Diff ──────────────────────────────────────────────────────────────────

    async def get_framework_diff(
        self, *, user_id: str, framework_id: str
    ) -> FrameworkDiff:
        """Compare live controls vs latest published version snapshot."""
        _COMPARED_FIELDS = (
            "name",
            "description",
            "guidance",
            "criticality_code",
            "control_type",
            "automation_potential",
            "control_category_code",
            "requirement_code",
        )

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_framework_by_id(conn, framework_id)
            if record is None:
                raise NotFoundError(f"Framework '{framework_id}' not found")
            await self._require_framework_permission(
                conn,
                user_id=user_id,
                permission_code="frameworks.view",
                scope_org_id=record.scope_org_id,
                scope_workspace_id=record.scope_workspace_id,
            )

            ctrl_repo = ControlRepository()
            live_controls_raw = await ctrl_repo.list_controls_with_properties(
                conn, framework_id=framework_id
            )
            (
                version_code,
                base_controls_raw,
            ) = await self._repository.get_latest_published_version_controls(
                conn, framework_id=framework_id
            )

        # Build lookup by control_code
        live_by_code = {c["control_code"]: c for c in live_controls_raw}
        base_by_code = {c["control_code"]: c for c in base_controls_raw}
        all_codes = set(live_by_code) | set(base_by_code)

        # Group by requirement
        req_diffs: dict[str, RequirementDiff] = {}
        totals = {"added": 0, "removed": 0, "modified": 0, "unchanged": 0}

        for code in sorted(all_codes):
            live_c = live_by_code.get(code)
            base_c = base_by_code.get(code)
            req_code = (live_c or base_c).get("requirement_code") or "__no_req__"

            if live_c is None:
                status = "removed"
                field_changes = {}
            elif base_c is None:
                status = "added"
                field_changes = {}
            else:
                field_changes = {}
                for field in _COMPARED_FIELDS:
                    bv = str(base_c.get(field) or "")
                    lv = str(live_c.get(field) or "")
                    if bv != lv:
                        field_changes[field] = (bv or None, lv or None)
                status = "modified" if field_changes else "unchanged"

            totals[status] += 1
            if req_code not in req_diffs:
                # Get requirement name from live or base
                req_name = None
                req_desc = None
                if live_c:
                    req_name = live_c.get("requirement_name")
                    req_desc = live_c.get("requirement_description")
                elif base_c:
                    req_name = base_c.get("requirement_name")
                    req_desc = base_c.get("requirement_description")
                req_diffs[req_code] = RequirementDiff(
                    requirement_code=req_code,
                    name=req_name,
                    description=req_desc,
                    status="unchanged",
                    controls=[],
                )
            ctrl_name = None
            ctrl_desc = None
            if live_c:
                ctrl_name = live_c.get("name")
                ctrl_desc = live_c.get("description")
            elif base_c:
                ctrl_name = base_c.get("name")
                ctrl_desc = base_c.get("description")
            req_diffs[req_code].controls.append(
                ControlDiff(
                    control_code=code,
                    control_name=ctrl_name,
                    control_description=ctrl_desc,
                    status=status,
                    field_changes=field_changes,
                )
            )
            if status in ("added", "removed", "modified"):
                req_diffs[req_code].status = "modified"

        return FrameworkDiff(
            framework_id=framework_id,
            framework_code=record.framework_code,
            base_label=f"{version_code} (published)"
            if version_code
            else "no published version",
            compare_label="current (live)",
            requirements=list(req_diffs.values()),
            controls_added=totals["added"],
            controls_removed=totals["removed"],
            controls_modified=totals["modified"],
            controls_unchanged=totals["unchanged"],
        )

    # ── Bundle Export ─────────────────────────────────────────────────────────

    async def export_bundle(
        self, *, user_id: str, framework_id: str, fmt: str = "json"
    ):
        """Export a framework as a portable bundle (no UUIDs)."""
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_framework_by_id(conn, framework_id)
            if record is None:
                raise NotFoundError(f"Framework '{framework_id}' not found")
            await self._require_framework_permission(
                conn,
                user_id=user_id,
                permission_code="frameworks.view",
                scope_org_id=record.scope_org_id,
                scope_workspace_id=record.scope_workspace_id,
            )

            # Build requirement_id -> requirement_code map for parent_code lookup
            reqs = await self._repository.list_requirements_for_bundle(
                conn, framework_id=framework_id
            )
            req_id_to_code = {r["id"]: r["requirement_code"] for r in reqs}

            bundle_reqs = []
            for r in reqs:
                parent_code = (
                    req_id_to_code.get(r["parent_requirement_id"])
                    if r["parent_requirement_id"]
                    else None
                )
                bundle_reqs.append(
                    {
                        "requirement_code": r["requirement_code"],
                        "name": r["name"],
                        "description": r["description"],
                        "sort_order": r["sort_order"],
                        "parent_requirement_code": parent_code,
                    }
                )

            ctrl_repo = ControlRepository()
            controls_raw = await ctrl_repo.list_controls_with_properties(
                conn, framework_id=framework_id
            )
            bundle_controls = []
            for c in controls_raw:
                req_code = c.get("requirement_code")
                bundle_controls.append(
                    {
                        "control_code": c["control_code"],
                        "name": c.get("name"),
                        "description": c.get("description"),
                        "guidance": c.get("guidance"),
                        "implementation_notes": c.get("implementation_notes"),
                        "criticality_code": c.get("criticality_code"),
                        "control_type": c.get("control_type"),
                        "automation_potential": c.get("automation_potential"),
                        "control_category_code": c.get("control_category_code"),
                        "requirement_code": req_code,
                        "tags": c.get("tags"),
                        "implementation_guidance": c.get("implementation_guidance"),
                        "responsible_teams": c.get("responsible_teams"),
                    }
                )

            global_risks = await self._repository.list_global_risks_by_framework(
                conn, tenant_key=record.tenant_key, framework_id=framework_id
            )
            risk_control_pairs = (
                await self._repository.list_risk_control_codes_for_framework(
                    conn, framework_id=framework_id
                )
            )
            # Build linked_control_codes per risk_code
            risk_ctrl_map: dict[str, list[str]] = {}
            for risk_code, ctrl_code in risk_control_pairs:
                risk_ctrl_map.setdefault(risk_code, []).append(ctrl_code)

            bundle_risks = []
            for gr in global_risks:
                bundle_risks.append(
                    {
                        "risk_code": gr["risk_code"],
                        "title": gr["title"],
                        "description": gr["description"],
                        "short_description": gr["short_description"],
                        "risk_category_code": gr["risk_category_code"],
                        "risk_level_code": gr["risk_level_code"],
                        "inherent_likelihood": gr["inherent_likelihood"],
                        "inherent_impact": gr["inherent_impact"],
                        "mitigation_guidance": gr["mitigation_guidance"],
                        "detection_guidance": gr["detection_guidance"],
                        "linked_control_codes": risk_ctrl_map.get(gr["risk_code"], []),
                    }
                )

        bundle = {
            "framework_code": record.framework_code,
            "framework_type_code": record.framework_type_code,
            "framework_category_code": record.framework_category_code,
            "name": record.name,
            "description": record.description,
            "short_description": record.short_description,
            "publisher_type": record.publisher_type,
            "publisher_name": record.publisher_name,
            "documentation_url": record.documentation_url,
            "requirements": bundle_reqs,
            "controls": bundle_controls,
            "global_risks": bundle_risks,
        }

        data = json.dumps(bundle, indent=2, default=str).encode("utf-8")
        stem = record.framework_code or "framework_bundle"
        return make_streaming_response(data, "json", stem)

    # ── Bundle Import ─────────────────────────────────────────────────────────

    async def import_bundle(
        self,
        *,
        user_id: str,
        tenant_key: str,
        bundle: FrameworkBundle,
        scope_org_id: str | None = None,
        scope_workspace_id: str | None = None,
        dry_run: bool = False,
    ) -> BundleImportResult:
        """Import a framework bundle. Upserts by natural keys; never touches UUIDs from the bundle."""
        now = utc_now_sql()
        result = BundleImportResult(dry_run=dry_run)
        errors: list[BundleImportError] = []

        try:
            async with self._database_pool.acquire() as conn:
                async with conn.transaction():
                    # 1. Upsert framework
                    existing_fw = await self._repository.get_framework_by_code(
                        conn, bundle.framework_code, tenant_key
                    )
                    await self._require_framework_permission(
                        conn,
                        user_id=user_id,
                        permission_code="frameworks.create",
                        scope_org_id=existing_fw.scope_org_id
                        if existing_fw
                        else scope_org_id,
                        scope_workspace_id=existing_fw.scope_workspace_id
                        if existing_fw
                        else scope_workspace_id,
                    )
                    if existing_fw:
                        framework_id = existing_fw.id
                        await self._repository.update_framework(
                            conn,
                            framework_id,
                            framework_type_code=bundle.framework_type_code,
                            framework_category_code=bundle.framework_category_code,
                            updated_by=user_id,
                            now=now,
                        )
                        result.framework_updated = True
                    else:
                        framework_id = str(uuid.uuid4())
                        await self._repository.create_framework(
                            conn,
                            framework_id=framework_id,
                            tenant_key=tenant_key,
                            framework_code=bundle.framework_code,
                            framework_type_code=bundle.framework_type_code,
                            framework_category_code=bundle.framework_category_code,
                            scope_org_id=scope_org_id,
                            scope_workspace_id=scope_workspace_id,
                            created_by=user_id,
                            now=now,
                        )
                        result.framework_created = True

                    fw_props: dict[str, str] = {}
                    if bundle.name:
                        fw_props["name"] = bundle.name
                    if bundle.description:
                        fw_props["description"] = bundle.description
                    if bundle.short_description:
                        fw_props["short_description"] = bundle.short_description
                    if bundle.publisher_type:
                        fw_props["publisher_type"] = bundle.publisher_type
                    if bundle.publisher_name:
                        fw_props["publisher_name"] = bundle.publisher_name
                    if bundle.documentation_url:
                        fw_props["documentation_url"] = bundle.documentation_url
                    if fw_props:
                        await self._repository.upsert_framework_properties(
                            conn,
                            framework_id=framework_id,
                            properties=fw_props,
                            created_by=user_id,
                            now=now,
                        )

                    # 2. Upsert requirements — two passes to resolve parent codes
                    req_code_to_id: dict[str, str] = {}
                    for req in bundle.requirements:
                        if not req.requirement_code:
                            errors.append(
                                BundleImportError(
                                    section="requirements",
                                    message="Missing requirement_code",
                                )
                            )
                            continue
                        try:
                            (
                                req_id,
                                req_created,
                            ) = await self._repository.upsert_requirement(
                                conn,
                                requirement_id=str(uuid.uuid4()),
                                framework_id=framework_id,
                                requirement_code=req.requirement_code,
                                sort_order=req.sort_order,
                                parent_requirement_id=None,  # resolved in second pass
                                name=req.name,
                                description=req.description,
                                created_by=user_id,
                                now=now,
                            )
                            req_code_to_id[req.requirement_code] = req_id
                            if req_created:
                                result.requirements_created += 1
                            else:
                                result.requirements_updated += 1
                        except Exception as exc:
                            errors.append(
                                BundleImportError(
                                    section="requirements",
                                    key=req.requirement_code,
                                    message=str(exc),
                                )
                            )

                    # Second pass: resolve parent requirement links
                    for req in bundle.requirements:
                        if (
                            req.parent_requirement_code
                            and req.requirement_code in req_code_to_id
                        ):
                            parent_id = req_code_to_id.get(req.parent_requirement_code)
                            if parent_id:
                                await conn.execute(
                                    'UPDATE "05_grc_library"."12_fct_requirements" SET parent_requirement_id = $1 WHERE id = $2',
                                    parent_id,
                                    req_code_to_id[req.requirement_code],
                                )
                            else:
                                result.warnings.append(
                                    f"Requirement '{req.requirement_code}': parent '{req.parent_requirement_code}' not found in bundle"
                                )

                    # 3. Upsert controls
                    ctrl_repo = ControlRepository()
                    ctrl_code_to_id: dict[
                        str, str
                    ] = await ctrl_repo.list_controls_by_code(
                        conn, framework_id=framework_id
                    )
                    for i, ctrl in enumerate(bundle.controls):
                        if not ctrl.control_code:
                            errors.append(
                                BundleImportError(
                                    section="controls",
                                    key=f"row_{i}",
                                    message="Missing control_code",
                                )
                            )
                            continue
                        req_id = (
                            req_code_to_id.get(ctrl.requirement_code)
                            if ctrl.requirement_code
                            else None
                        )
                        try:
                            if ctrl.control_code in ctrl_code_to_id:
                                ctrl_id = ctrl_code_to_id[ctrl.control_code]
                                await ctrl_repo.update_control(
                                    conn,
                                    ctrl_id,
                                    control_category_code=ctrl.control_category_code,
                                    criticality_code=ctrl.criticality_code,
                                    control_type=ctrl.control_type,
                                    automation_potential=ctrl.automation_potential,
                                    requirement_id=req_id,
                                    updated_by=user_id,
                                    now=now,
                                )
                                result.controls_updated += 1
                            else:
                                ctrl_id = str(uuid.uuid4())
                                await ctrl_repo.create_control(
                                    conn,
                                    control_id=ctrl_id,
                                    framework_id=framework_id,
                                    tenant_key=tenant_key,
                                    control_code=ctrl.control_code,
                                    control_category_code=ctrl.control_category_code
                                    or "general",
                                    criticality_code=ctrl.criticality_code or "medium",
                                    control_type=ctrl.control_type or "preventive",
                                    automation_potential=ctrl.automation_potential
                                    or "manual",
                                    requirement_id=req_id,
                                    sort_order=i,
                                    created_by=user_id,
                                    now=now,
                                )
                                ctrl_code_to_id[ctrl.control_code] = ctrl_id
                                result.controls_created += 1
                            ctrl_props: dict[str, str] = {}
                            for field, key in [
                                (ctrl.name, "name"),
                                (ctrl.description, "description"),
                                (ctrl.guidance, "guidance"),
                                (ctrl.implementation_notes, "implementation_notes"),
                                (ctrl.tags, "tags"),
                                (
                                    ctrl.implementation_guidance,
                                    "implementation_guidance",
                                ),
                                (ctrl.responsible_teams, "responsible_teams"),
                            ]:
                                if field:
                                    ctrl_props[key] = field
                            if ctrl_props:
                                await ctrl_repo.upsert_control_properties(
                                    conn,
                                    control_id=ctrl_code_to_id[ctrl.control_code],
                                    properties=ctrl_props,
                                    created_by=user_id,
                                    now=now,
                                )
                        except Exception as exc:
                            errors.append(
                                BundleImportError(
                                    section="controls",
                                    key=ctrl.control_code,
                                    message=str(exc),
                                )
                            )

                    # 4. Upsert global risks + links
                    for gr in bundle.global_risks:
                        if not gr.risk_code:
                            errors.append(
                                BundleImportError(
                                    section="global_risks", message="Missing risk_code"
                                )
                            )
                            continue
                        try:
                            (
                                gr_id,
                                gr_created,
                            ) = await self._repository.upsert_global_risk(
                                conn,
                                global_risk_id=str(uuid.uuid4()),
                                tenant_key=tenant_key,
                                risk_code=gr.risk_code,
                                risk_category_code=gr.risk_category_code,
                                risk_level_code=gr.risk_level_code,
                                inherent_likelihood=gr.inherent_likelihood,
                                inherent_impact=gr.inherent_impact,
                                title=gr.title,
                                description=gr.description,
                                short_description=gr.short_description,
                                mitigation_guidance=gr.mitigation_guidance,
                                detection_guidance=gr.detection_guidance,
                                created_by=user_id,
                                now=now,
                            )
                            if gr_created:
                                result.global_risks_created += 1
                            else:
                                result.global_risks_updated += 1
                            for ctrl_code in gr.linked_control_codes:
                                ctrl_id = ctrl_code_to_id.get(ctrl_code)
                                if ctrl_id:
                                    inserted = await self._repository.link_global_risk_to_control(
                                        conn,
                                        global_risk_id=gr_id,
                                        control_id=ctrl_id,
                                        created_by=user_id,
                                        now=now,
                                    )
                                    if inserted:
                                        result.risk_control_links_created += 1
                                else:
                                    result.warnings.append(
                                        f"Risk '{gr.risk_code}': linked control '{ctrl_code}' not found"
                                    )
                        except Exception as exc:
                            errors.append(
                                BundleImportError(
                                    section="global_risks",
                                    key=gr.risk_code,
                                    message=str(exc),
                                )
                            )

                    result.errors = errors
                    if dry_run or errors:
                        raise _DryRunRollback()
        except _DryRunRollback:
            pass  # Transaction rolled back; result still populated for preview

        return result


class _DryRunRollback(Exception):
    """Signal to roll back a dry-run or errored transaction."""


def _catalog_response(r) -> FrameworkResponse:
    if r is None:
        raise NotFoundError("Framework record not found in catalog view.")

    return FrameworkResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        framework_code=r.framework_code,
        framework_type_code=r.framework_type_code,
        type_name=r.type_name,
        framework_category_code=r.framework_category_code,
        category_name=r.category_name,
        scope_org_id=r.scope_org_id,
        scope_workspace_id=r.scope_workspace_id,
        approval_status=r.approval_status,
        is_marketplace_visible=r.is_marketplace_visible,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
        name=r.name,
        description=r.description,
        short_description=r.short_description,
        publisher_type=r.publisher_type,
        publisher_name=r.publisher_name,
        logo_url=r.logo_url,
        documentation_url=r.documentation_url,
        latest_version_code=r.latest_version_code,
        control_count=r.control_count,
        has_pending_changes=getattr(r, "has_pending_changes", False),
    )
