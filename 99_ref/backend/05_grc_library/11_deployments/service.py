from __future__ import annotations

import uuid
from importlib import import_module

from .repository import DeploymentRepository
from .schemas import (
    DeployFrameworkRequest,
    FrameworkDeploymentListResponse,
    FrameworkDeploymentResponse,
    UpdateDeploymentRequest,
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
_frameworks_repo_module = import_module(
    "backend.05_grc_library.02_frameworks.repository"
)

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
ConflictError = _errors_module.ConflictError
NotFoundError = _errors_module.NotFoundError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
FrameworkRepository = _frameworks_repo_module.FrameworkRepository


@instrument_class_methods(
    namespace="grc.deployments.service",
    logger_name="backend.grc.deployments.instrumentation",
)
class DeploymentService:
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
        self._repository = DeploymentRepository()
        self._framework_repository = FrameworkRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.deployments")

    async def _require_deployment_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
        workspace_id: str | None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def list_deployments(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        has_update: bool | None = None,
    ) -> FrameworkDeploymentListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_deployment_permission(
                conn,
                user_id=user_id,
                permission_code="frameworks.view",
                org_id=org_id,
                workspace_id=workspace_id,
            )
            records, total = await self._repository.list_deployments(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                has_update=has_update,
            )
        return FrameworkDeploymentListResponse(
            items=[_deployment_response(r) for r in records],
            total=total,
        )

    async def get_deployment(
        self, *, user_id: str, deployment_id: str
    ) -> FrameworkDeploymentResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_deployment(conn, deployment_id)
            if record is None:
                raise NotFoundError(f"Deployment '{deployment_id}' not found")
            await self._require_deployment_permission(
                conn,
                user_id=user_id,
                permission_code="frameworks.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        return _deployment_response(record)

    async def deploy_framework(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: DeployFrameworkRequest,
    ) -> FrameworkDeploymentResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await self._require_deployment_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.create",
                    org_id=org_id,
                    workspace_id=request.workspace_id,
                )

                conflict = await conn.fetchrow(
                    """
                    SELECT d.id::text, d.workspace_id::text
                    FROM "05_grc_library"."16_fct_framework_deployments" d
                    LEFT JOIN "05_grc_library"."20_dtl_framework_properties" src_fw
                      ON src_fw.framework_id = d.framework_id
                     AND src_fw.property_key = 'source_framework_id'
                    WHERE d.org_id = $1::uuid
                      AND d.deployment_status != 'removed'
                      AND (
                        d.framework_id = $2::uuid
                        OR src_fw.property_value::uuid = $2::uuid
                      )
                      AND ($3::uuid IS NOT NULL AND d.workspace_id IS NOT NULL AND d.workspace_id IS DISTINCT FROM $3::uuid)
                    LIMIT 1
                    """,
                    org_id,
                    request.framework_id,
                    request.workspace_id,
                )
                if conflict is not None:
                    raise ConflictError(
                        f"Framework '{request.framework_id}' is already deployed in another workspace. "
                        "Remove it there first before deploying to this workspace."
                    )

                existing = await self._repository.get_deployment_for_source(
                    conn,
                    org_id=org_id,
                    workspace_id=request.workspace_id,
                    source_framework_id=request.framework_id,
                )

                preferred_clone_framework_id: str | None = None
                if existing and existing.source_framework_id:
                    preferred_clone_framework_id = existing.framework_id

                (
                    target_framework_id,
                    target_version_id,
                ) = await self._materialize_workspace_framework(
                    conn,
                    tenant_key=tenant_key,
                    source_framework_id=request.framework_id,
                    source_version_id=request.version_id,
                    scope_org_id=org_id,
                    scope_workspace_id=request.workspace_id,
                    user_id=user_id,
                    now=now,
                    preferred_clone_framework_id=preferred_clone_framework_id,
                )

                deployment_id = str(uuid.uuid4())
                if existing is not None:
                    record = await self._repository.update_deployment(
                        conn,
                        existing.id,
                        framework_id=target_framework_id,
                        version_id=target_version_id,
                        deployment_status="active",
                        workspace_id=request.workspace_id,
                        updated_by=user_id,
                        now=now,
                    )
                else:
                    record = await self._repository.create_deployment(
                        conn,
                        deployment_id=deployment_id,
                        tenant_key=tenant_key,
                        org_id=org_id,
                        framework_id=target_framework_id,
                        version_id=target_version_id,
                        workspace_id=request.workspace_id,
                        created_by=user_id,
                        now=now,
                    )

                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_deployment",
                        entity_id=record.id,
                        event_type="framework_deployed",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "framework_id": request.framework_id,
                            "version_id": request.version_id,
                            "org_id": org_id,
                            "workspace_id": request.workspace_id,
                        },
                    ),
                )
        await self._cache.delete_pattern(f"deployments:{org_id}:*")
        return _deployment_response(record)

    async def update_deployment(
        self,
        *,
        user_id: str,
        tenant_key: str,
        deployment_id: str,
        request: UpdateDeploymentRequest,
    ) -> FrameworkDeploymentResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_deployment(conn, deployment_id)
                if existing is None:
                    raise NotFoundError(f"Deployment '{deployment_id}' not found")
                await self._require_deployment_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.update",
                    org_id=existing.org_id,
                    workspace_id=existing.workspace_id,
                )

                target_framework_id: str | None = None
                target_version_id: str | None = request.version_id
                source_to_version_id = (
                    request.version_id
                    or existing.source_version_id
                    or existing.deployed_version_id
                )
                if request.version_id and existing.workspace_id:
                    source_framework_id = (
                        existing.source_framework_id or existing.framework_id
                    )
                    preferred_clone_framework_id = existing.framework_id

                    # Check if source framework still exists in catalog
                    source_in_catalog = await conn.fetchrow(
                        """
                        SELECT id::text FROM "05_grc_library"."40_vw_framework_catalog"
                        WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
                        """,
                        source_framework_id,
                        tenant_key,
                    )

                    if source_in_catalog is None and preferred_clone_framework_id:
                        # Source framework deleted/not visible, but we have a clone.
                        # Sync the clone to the new version using direct version data.
                        (
                            target_framework_id,
                            target_version_id,
                        ) = await self._sync_clone_to_new_version(
                            conn,
                            tenant_key=tenant_key,
                            source_framework_id=source_framework_id,
                            source_version_id=request.version_id,
                            clone_fw_id=preferred_clone_framework_id,
                            scope_org_id=existing.org_id,
                            scope_workspace_id=existing.workspace_id,
                            user_id=user_id,
                            now=now,
                        )
                    else:
                        (
                            target_framework_id,
                            target_version_id,
                        ) = await self._materialize_workspace_framework(
                            conn,
                            tenant_key=tenant_key,
                            source_framework_id=source_framework_id,
                            source_version_id=request.version_id,
                            scope_org_id=existing.org_id,
                            scope_workspace_id=existing.workspace_id,
                            user_id=user_id,
                            now=now,
                            preferred_clone_framework_id=preferred_clone_framework_id,
                        )

                record = await self._repository.update_deployment(
                    conn,
                    deployment_id,
                    framework_id=target_framework_id,
                    version_id=target_version_id,
                    deployment_status=request.deployment_status,
                    updated_by=user_id,
                    now=now,
                )
                event_type = "framework_deployment_updated"
                if (
                    request.version_id
                    and source_to_version_id != existing.source_version_id
                ):
                    event_type = "framework_deployment_upgraded"

                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_deployment",
                        entity_id=deployment_id,
                        event_type=event_type,
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "from_version_id": existing.source_version_id
                            or existing.deployed_version_id,
                            "to_version_id": source_to_version_id,
                        },
                    ),
                )
        await self._cache.delete_pattern(f"deployments:{existing.org_id}:*")
        return _deployment_response(record)

    async def list_deployment_controls(
        self,
        *,
        user_id: str,
        deployment_id: str,
    ) -> dict:
        async with self._database_pool.acquire() as conn:
            deployment = await self._repository.get_deployment(conn, deployment_id)
            if deployment is None:
                raise NotFoundError(f"Deployment '{deployment_id}' not found")
            await self._require_deployment_permission(
                conn,
                user_id=user_id,
                permission_code="frameworks.view",
                org_id=deployment.org_id,
                workspace_id=deployment.workspace_id,
            )
            controls = await self._repository.list_deployment_controls(
                conn, deployment_id=deployment_id
            )
        return {
            "deployment_id": deployment_id,
            "framework_name": deployment.framework_name,
            "deployed_version_code": deployment.deployed_version_code,
            "controls": controls,
            "total": len(controls),
        }

    async def get_upgrade_diff(
        self,
        *,
        user_id: str,
        deployment_id: str,
        new_version_id: str,
    ) -> dict:
        async with self._database_pool.acquire() as conn:
            deployment = await self._repository.get_deployment(conn, deployment_id)
            if deployment is None:
                raise NotFoundError(f"Deployment '{deployment_id}' not found")
            await self._require_deployment_permission(
                conn,
                user_id=user_id,
                permission_code="frameworks.view",
                org_id=deployment.org_id,
                workspace_id=deployment.workspace_id,
            )
            if deployment.source_framework_id and deployment.source_version_id:
                diff = await self._repository.get_source_upgrade_diff(
                    conn,
                    from_version_id=deployment.source_version_id,
                    new_version_id=new_version_id,
                )
            else:
                diff = await self._repository.get_upgrade_diff(
                    conn, deployment_id=deployment_id, new_version_id=new_version_id
                )

            new_version = await conn.fetchrow(
                """
                SELECT v.version_code,
                       p_notes.property_value AS release_notes,
                       p_severity.property_value AS change_severity,
                       p_summary.property_value AS change_summary
                FROM "05_grc_library"."11_fct_framework_versions" v
                LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_notes
                    ON p_notes.framework_version_id = v.id AND p_notes.property_key = 'release_notes'
                LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_severity
                    ON p_severity.framework_version_id = v.id AND p_severity.property_key = 'change_severity_label'
                LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_summary
                    ON p_summary.framework_version_id = v.id AND p_summary.property_key = 'change_summary'
                WHERE v.id = $1::uuid AND v.is_deleted = FALSE
                """,
                new_version_id,
            )

        return {
            "deployment_id": deployment_id,
            "from_version_code": deployment.deployed_version_code,
            "to_version_id": new_version_id,
            "to_version_code": new_version["version_code"] if new_version else None,
            "release_notes": new_version["release_notes"] if new_version else None,
            "change_severity": new_version["change_severity"] if new_version else None,
            "change_summary": new_version["change_summary"] if new_version else None,
            **diff,
        }

    async def _materialize_workspace_framework(
        self,
        conn,
        *,
        tenant_key: str,
        source_framework_id: str,
        source_version_id: str,
        scope_org_id: str,
        scope_workspace_id: str | None,
        user_id: str,
        now: object,
        preferred_clone_framework_id: str | None = None,
    ) -> tuple[str, str]:
        if not scope_workspace_id:
            return source_framework_id, source_version_id

        source_fw = await conn.fetchrow(
            """
            SELECT id::text, framework_code, framework_type_code, framework_category_code,
                   name, description, short_description, publisher_type, publisher_name,
                   logo_url, documentation_url
            FROM "05_grc_library"."40_vw_framework_catalog"
            WHERE id = $1::uuid AND tenant_key = $2 AND is_deleted = FALSE
            """,
            source_framework_id,
            tenant_key,
        )
        if source_fw is None:
            raise NotFoundError(f"Framework '{source_framework_id}' not found")

        source_ver = await conn.fetchrow(
            """
            SELECT v.id::text, v.framework_id::text, v.version_code, v.change_severity, v.lifecycle_state,
                   p_label.property_value AS version_label,
                   p_notes.property_value AS release_notes,
                   p_summary.property_value AS change_summary
            FROM "05_grc_library"."11_fct_framework_versions" v
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_label
              ON p_label.framework_version_id = v.id AND p_label.property_key = 'version_label'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_notes
              ON p_notes.framework_version_id = v.id AND p_notes.property_key = 'release_notes'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_summary
              ON p_summary.framework_version_id = v.id AND p_summary.property_key = 'change_summary'
            WHERE v.id = $1::uuid AND v.framework_id = $2::uuid AND v.is_deleted = FALSE
            """,
            source_version_id,
            source_framework_id,
        )
        if source_ver is None:
            raise NotFoundError(
                f"Version '{source_version_id}' not found for framework '{source_framework_id}'"
            )

        clone_fw_id: str | None = None
        if preferred_clone_framework_id:
            row = await conn.fetchrow(
                """
                SELECT id::text
                FROM "05_grc_library"."10_fct_frameworks"
                WHERE id = $1::uuid
                  AND tenant_key = $2
                  AND scope_org_id = $3::uuid
                  AND scope_workspace_id = $4::uuid
                  AND is_deleted = FALSE
                """,
                preferred_clone_framework_id,
                tenant_key,
                scope_org_id,
                scope_workspace_id,
            )
            if row:
                clone_fw_id = row["id"]

        if clone_fw_id is None:
            row = await conn.fetchrow(
                """
                SELECT f.id::text
                FROM "05_grc_library"."10_fct_frameworks" f
                JOIN "05_grc_library"."20_dtl_framework_properties" p
                  ON p.framework_id = f.id
                 AND p.property_key = 'source_framework_id'
                WHERE f.tenant_key = $1
                  AND f.scope_org_id = $2::uuid
                  AND f.scope_workspace_id = $3::uuid
                  AND f.is_deleted = FALSE
                  AND p.property_value = $4
                ORDER BY f.updated_at DESC
                LIMIT 1
                """,
                tenant_key,
                scope_org_id,
                scope_workspace_id,
                source_framework_id,
            )
            if row:
                clone_fw_id = row["id"]

        if clone_fw_id is None:
            clone_fw_id = str(uuid.uuid4())
            clone_code = await self._next_clone_framework_code(
                conn,
                tenant_key=tenant_key,
                source_framework_code=source_fw["framework_code"],
                workspace_id=scope_workspace_id,
            )
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."10_fct_frameworks"
                    (id, tenant_key, framework_code, framework_type_code, framework_category_code,
                     scope_org_id, scope_workspace_id, approval_status, is_marketplace_visible,
                     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                     created_at, updated_at, created_by, updated_by)
                VALUES
                    ($1::uuid, $2, $3, $4, $5,
                     $6::uuid, $7::uuid, 'approved', FALSE,
                     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                     $8, $9, $10::uuid, $11::uuid)
                """,
                clone_fw_id,
                tenant_key,
                clone_code,
                source_fw["framework_type_code"],
                source_fw["framework_category_code"],
                scope_org_id,
                scope_workspace_id,
                now,
                now,
                user_id,
                user_id,
            )
        else:
            await conn.execute(
                """
                UPDATE "05_grc_library"."10_fct_frameworks"
                SET framework_type_code = $1,
                    framework_category_code = $2,
                    approval_status = 'approved',
                    is_active = TRUE,
                    is_disabled = FALSE,
                    is_deleted = FALSE,
                    updated_at = $3,
                    updated_by = $4::uuid
                WHERE id = $5::uuid
                """,
                source_fw["framework_type_code"],
                source_fw["framework_category_code"],
                now,
                user_id,
                clone_fw_id,
            )

        fw_props: dict[str, str] = {
            "source_framework_id": source_framework_id,
            "source_version_id": source_version_id,
        }
        for key in (
            "name",
            "description",
            "short_description",
            "publisher_type",
            "publisher_name",
            "logo_url",
            "documentation_url",
        ):
            value = source_fw.get(key)
            if value is not None and str(value).strip() != "":
                fw_props[key] = str(value)
        for key, value in fw_props.items():
            await self._upsert_property(
                conn,
                table='"05_grc_library"."20_dtl_framework_properties"',
                owner_col="framework_id",
                owner_id=clone_fw_id,
                key_col="property_key",
                val_col="property_value",
                key=key,
                value=value,
                actor_id=user_id,
                now=now,
            )

        source_reqs = await conn.fetch(
            """
            SELECT r.id::text AS source_requirement_id,
                   r.requirement_code,
                   r.sort_order,
                   parent.requirement_code AS parent_requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description
            FROM "05_grc_library"."12_fct_requirements" r
            LEFT JOIN "05_grc_library"."12_fct_requirements" parent
              ON parent.id = r.parent_requirement_id
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_name
              ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_desc
              ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            WHERE r.framework_id = $1::uuid AND r.is_deleted = FALSE
            ORDER BY r.sort_order, r.requirement_code
            """,
            source_framework_id,
        )

        existing_clone_reqs = await conn.fetch(
            """
            SELECT id::text, requirement_code
            FROM "05_grc_library"."12_fct_requirements"
            WHERE framework_id = $1::uuid
            """,
            clone_fw_id,
        )
        clone_req_by_code: dict[str, str] = {
            r["requirement_code"]: r["id"] for r in existing_clone_reqs
        }

        for req in source_reqs:
            req_code = req["requirement_code"]
            clone_req_id = clone_req_by_code.get(req_code)
            if clone_req_id:
                await conn.execute(
                    """
                    UPDATE "05_grc_library"."12_fct_requirements"
                    SET sort_order = $1,
                        parent_requirement_id = NULL,
                        is_active = TRUE,
                        is_disabled = FALSE,
                        is_deleted = FALSE,
                        updated_at = $2,
                        updated_by = $3::uuid
                    WHERE id = $4::uuid
                    """,
                    req["sort_order"],
                    now,
                    user_id,
                    clone_req_id,
                )
            else:
                clone_req_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."12_fct_requirements"
                        (id, framework_id, requirement_code, sort_order, parent_requirement_id,
                         is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                         created_at, updated_at, created_by, updated_by)
                    VALUES
                        ($1::uuid, $2::uuid, $3, $4, NULL,
                         TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                         $5, $6, $7::uuid, $8::uuid)
                    """,
                    clone_req_id,
                    clone_fw_id,
                    req_code,
                    req["sort_order"],
                    now,
                    now,
                    user_id,
                    user_id,
                )
                clone_req_by_code[req_code] = clone_req_id

            if req["name"] is not None:
                await self._upsert_property(
                    conn,
                    table='"05_grc_library"."22_dtl_requirement_properties"',
                    owner_col="requirement_id",
                    owner_id=clone_req_id,
                    key_col="property_key",
                    val_col="property_value",
                    key="name",
                    value=str(req["name"]),
                    actor_id=user_id,
                    now=now,
                    on_conflict_do_nothing=True,
                )
            if req["description"] is not None:
                await self._upsert_property(
                    conn,
                    table='"05_grc_library"."22_dtl_requirement_properties"',
                    owner_col="requirement_id",
                    owner_id=clone_req_id,
                    key_col="property_key",
                    val_col="property_value",
                    key="description",
                    value=str(req["description"]),
                    actor_id=user_id,
                    now=now,
                    on_conflict_do_nothing=True,
                )

        for req in source_reqs:
            parent_code = req["parent_requirement_code"]
            if not parent_code:
                continue
            child_id = clone_req_by_code.get(req["requirement_code"])
            parent_id = clone_req_by_code.get(parent_code)
            if child_id and parent_id:
                await conn.execute(
                    """
                    UPDATE "05_grc_library"."12_fct_requirements"
                    SET parent_requirement_id = $1::uuid,
                        updated_at = $2,
                        updated_by = $3::uuid
                    WHERE id = $4::uuid
                    """,
                    parent_id,
                    now,
                    user_id,
                    child_id,
                )

        version_controls_count = await conn.fetchval(
            """
            SELECT COUNT(*)::int
            FROM "05_grc_library"."31_lnk_framework_version_controls"
            WHERE framework_version_id = $1::uuid
            """,
            source_version_id,
        )
        use_all_controls = int(version_controls_count or 0) == 0
        source_controls = await conn.fetch(
            """
            SELECT c.id::text AS source_control_id,
                   c.control_code,
                   c.control_category_code,
                   c.criticality_code,
                   c.control_type,
                   c.automation_potential,
                   COALESCE(lvc.sort_order, c.sort_order) AS deploy_sort_order,
                   req.requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_guid.property_value AS guidance,
                   p_notes.property_value AS implementation_notes,
                   p_tags.property_value AS tags,
                   p_impl.property_value AS implementation_guidance,
                   p_teams.property_value AS responsible_teams
            FROM "05_grc_library"."13_fct_controls" c
            LEFT JOIN "05_grc_library"."31_lnk_framework_version_controls" lvc
              ON lvc.control_id = c.id
             AND lvc.framework_version_id = $2::uuid
            LEFT JOIN "05_grc_library"."12_fct_requirements" req
              ON req.id = c.requirement_id
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
              ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
              ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guid
              ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_notes
              ON p_notes.control_id = c.id AND p_notes.property_key = 'implementation_notes'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_tags
              ON p_tags.control_id = c.id AND p_tags.property_key = 'tags'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_impl
              ON p_impl.control_id = c.id AND p_impl.property_key = 'implementation_guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_teams
              ON p_teams.control_id = c.id AND p_teams.property_key = 'responsible_teams'
            WHERE c.framework_id = $1::uuid
              AND c.is_deleted = FALSE
              AND ($3::boolean OR lvc.framework_version_id IS NOT NULL)
            ORDER BY deploy_sort_order, c.control_code
            """,
            source_framework_id,
            source_version_id,
            use_all_controls,
        )

        existing_clone_controls = await conn.fetch(
            """
            SELECT id::text, control_code
            FROM "05_grc_library"."13_fct_controls"
            WHERE framework_id = $1::uuid
            """,
            clone_fw_id,
        )
        clone_ctrl_by_code: dict[str, str] = {
            r["control_code"]: r["id"] for r in existing_clone_controls
        }
        source_to_clone_control: dict[str, str] = {}
        source_codes: set[str] = set()

        for ctrl in source_controls:
            ctrl_code = ctrl["control_code"]
            source_codes.add(ctrl_code)
            clone_ctrl_id = clone_ctrl_by_code.get(ctrl_code)
            requirement_id = (
                clone_req_by_code.get(ctrl["requirement_code"])
                if ctrl["requirement_code"]
                else None
            )
            if clone_ctrl_id:
                await conn.execute(
                    """
                    UPDATE "05_grc_library"."13_fct_controls"
                    SET requirement_id = $1::uuid,
                        control_category_code = $2,
                        criticality_code = $3,
                        control_type = $4,
                        automation_potential = $5,
                        sort_order = $6,
                        is_active = TRUE,
                        is_disabled = FALSE,
                        is_deleted = FALSE,
                        updated_at = $7,
                        updated_by = $8::uuid
                    WHERE id = $9::uuid
                    """,
                    requirement_id,
                    ctrl["control_category_code"],
                    ctrl["criticality_code"],
                    ctrl["control_type"],
                    ctrl["automation_potential"],
                    ctrl["deploy_sort_order"],
                    now,
                    user_id,
                    clone_ctrl_id,
                )
            else:
                clone_ctrl_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."13_fct_controls"
                        (id, framework_id, requirement_id, tenant_key, control_code,
                         control_category_code, criticality_code, control_type, automation_potential, sort_order,
                         is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                         created_at, updated_at, created_by, updated_by)
                    VALUES
                        ($1::uuid, $2::uuid, $3::uuid, $4, $5,
                         $6, $7, $8, $9, $10,
                         TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                         $11, $12, $13::uuid, $14::uuid)
                    """,
                    clone_ctrl_id,
                    clone_fw_id,
                    requirement_id,
                    tenant_key,
                    ctrl_code,
                    ctrl["control_category_code"],
                    ctrl["criticality_code"],
                    ctrl["control_type"],
                    ctrl["automation_potential"],
                    ctrl["deploy_sort_order"],
                    now,
                    now,
                    user_id,
                    user_id,
                )
                clone_ctrl_by_code[ctrl_code] = clone_ctrl_id

            source_to_clone_control[ctrl["source_control_id"]] = clone_ctrl_id
            for key in (
                "name",
                "description",
                "guidance",
                "implementation_notes",
                "tags",
                "implementation_guidance",
                "responsible_teams",
            ):
                value = ctrl.get(key)
                if value is not None:
                    await self._upsert_property(
                        conn,
                        table='"05_grc_library"."23_dtl_control_properties"',
                        owner_col="control_id",
                        owner_id=clone_ctrl_id,
                        key_col="property_key",
                        val_col="property_value",
                        key=key,
                        value=str(value),
                        actor_id=user_id,
                        now=now,
                        on_conflict_do_nothing=True,
                    )

        if source_codes:
            await conn.execute(
                """
                UPDATE "05_grc_library"."13_fct_controls"
                SET is_deleted = TRUE,
                    is_active = FALSE,
                    deleted_at = $1,
                    deleted_by = $2::uuid,
                    updated_at = $3,
                    updated_by = $4::uuid
                WHERE framework_id = $5::uuid
                  AND is_deleted = FALSE
                  AND NOT (control_code = ANY($6::text[]))
                """,
                now,
                user_id,
                now,
                user_id,
                clone_fw_id,
                list(source_codes),
            )

        clone_ver_row = await conn.fetchrow(
            """
            SELECT id::text
            FROM "05_grc_library"."11_fct_framework_versions"
            WHERE framework_id = $1::uuid
              AND version_code = $2
              AND is_deleted = FALSE
            LIMIT 1
            """,
            clone_fw_id,
            source_ver["version_code"],
        )
        clone_version_id = clone_ver_row["id"] if clone_ver_row else str(uuid.uuid4())
        if clone_ver_row:
            await conn.execute(
                """
                UPDATE "05_grc_library"."11_fct_framework_versions"
                SET change_severity = $1,
                    lifecycle_state = 'published',
                    control_count = $2,
                    is_active = TRUE,
                    is_disabled = FALSE,
                    is_deleted = FALSE,
                    updated_at = $3,
                    updated_by = $4::uuid
                WHERE id = $5::uuid
                """,
                source_ver["change_severity"],
                len(source_to_clone_control),
                now,
                user_id,
                clone_version_id,
            )
        else:
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."11_fct_framework_versions"
                    (id, framework_id, version_code, change_severity, lifecycle_state,
                     control_count, previous_version_id,
                     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                     created_at, updated_at, created_by, updated_by)
                VALUES
                    ($1::uuid, $2::uuid, $3, $4, 'published',
                     $5, NULL,
                     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                     $6, $7, $8::uuid, $9::uuid)
                """,
                clone_version_id,
                clone_fw_id,
                source_ver["version_code"],
                source_ver["change_severity"],
                len(source_to_clone_control),
                now,
                now,
                user_id,
                user_id,
            )

        for key in ("version_label", "release_notes", "change_summary"):
            value = source_ver.get(key)
            if value is not None:
                await self._upsert_property(
                    conn,
                    table='"05_grc_library"."21_dtl_version_properties"',
                    owner_col="framework_version_id",
                    owner_id=clone_version_id,
                    key_col="property_key",
                    val_col="property_value",
                    key=key,
                    value=str(value),
                    actor_id=user_id,
                    now=now,
                )

        await conn.execute(
            """
            DELETE FROM "05_grc_library"."31_lnk_framework_version_controls"
            WHERE framework_version_id = $1::uuid
            """,
            clone_version_id,
        )
        for idx, ctrl in enumerate(source_controls):
            clone_ctrl_id = source_to_clone_control.get(ctrl["source_control_id"])
            if not clone_ctrl_id:
                continue
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."31_lnk_framework_version_controls"
                    (id, framework_version_id, control_id, sort_order, created_at, created_by)
                VALUES
                    (gen_random_uuid(), $1::uuid, $2::uuid, $3, $4, $5::uuid)
                ON CONFLICT (framework_version_id, control_id) DO NOTHING
                """,
                clone_version_id,
                clone_ctrl_id,
                int(
                    ctrl["deploy_sort_order"]
                    if ctrl["deploy_sort_order"] is not None
                    else idx
                ),
                now,
                user_id,
            )

        source_control_ids = list(source_to_clone_control.keys())
        if source_control_ids:
            risk_links = await conn.fetch(
                """
                SELECT lnk.global_risk_id::text AS global_risk_id,
                       lnk.control_id::text AS source_control_id,
                       lnk.mapping_type
                FROM "05_grc_library"."61_lnk_global_risk_control_mappings" lnk
                WHERE lnk.control_id = ANY($1::uuid[])
                """,
                source_control_ids,
            )
            for link in risk_links:
                clone_ctrl_id = source_to_clone_control.get(link["source_control_id"])
                if not clone_ctrl_id:
                    continue
                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."61_lnk_global_risk_control_mappings"
                        (id, global_risk_id, control_id, mapping_type, sort_order, created_at, created_by)
                    VALUES
                        (gen_random_uuid(), $1::uuid, $2::uuid, $3, 0, $4, $5::uuid)
                    ON CONFLICT (global_risk_id, control_id) DO UPDATE
                    SET mapping_type = EXCLUDED.mapping_type,
                        sort_order = EXCLUDED.sort_order
                    """,
                    link["global_risk_id"],
                    clone_ctrl_id,
                    link["mapping_type"],
                    now,
                    user_id,
                )

        await self._sync_workspace_risks(
            conn,
            tenant_key=tenant_key,
            org_id=scope_org_id,
            workspace_id=scope_workspace_id,
            framework_id=clone_fw_id,
            user_id=user_id,
            now=now,
        )
        return clone_fw_id, clone_version_id

    async def _sync_clone_to_new_version(
        self,
        conn,
        *,
        tenant_key: str,
        source_framework_id: str,
        source_version_id: str,
        clone_fw_id: str,
        scope_org_id: str,
        scope_workspace_id: str,
        user_id: str,
        now: object,
    ) -> tuple[str, str]:
        """Sync an existing workspace clone to a new source version.

        Used when the source framework is no longer in the catalog (deleted/deprecated)
        but we still need to upgrade a deployment to a newer version.
        Reads source version data directly from version controls link table.
        """
        # Get source version info
        source_ver = await conn.fetchrow(
            """
            SELECT v.id::text, v.framework_id::text, v.version_code, v.change_severity, v.lifecycle_state,
                   p_label.property_value AS version_label,
                   p_notes.property_value AS release_notes,
                   p_summary.property_value AS change_summary
            FROM "05_grc_library"."11_fct_framework_versions" v
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_label
              ON p_label.framework_version_id = v.id AND p_label.property_key = 'version_label'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_notes
              ON p_notes.framework_version_id = v.id AND p_notes.property_key = 'release_notes'
            LEFT JOIN "05_grc_library"."21_dtl_version_properties" p_summary
              ON p_summary.framework_version_id = v.id AND p_summary.property_key = 'change_summary'
            WHERE v.id = $1::uuid AND v.is_deleted = FALSE
            """,
            source_version_id,
        )
        if source_ver is None:
            raise NotFoundError(f"Version '{source_version_id}' not found")

        # Get source framework metadata (from the fact table, not catalog)
        source_fw = await conn.fetchrow(
            """
            SELECT id::text, framework_code, framework_type_code, framework_category_code
            FROM "05_grc_library"."10_fct_frameworks"
            WHERE id = $1::uuid AND is_deleted = FALSE
            """,
            source_framework_id,
        )
        if source_fw is None:
            # Framework was hard-deleted, use clone's existing metadata
            source_fw = await conn.fetchrow(
                """
                SELECT id::text, framework_code, framework_type_code, framework_category_code
                FROM "05_grc_library"."10_fct_frameworks"
                WHERE id = $1::uuid AND is_deleted = FALSE
                """,
                clone_fw_id,
            )

        # Get requirements from source version's framework
        source_reqs = await conn.fetch(
            """
            SELECT r.id::text AS source_requirement_id,
                   r.requirement_code,
                   r.sort_order,
                   parent.requirement_code AS parent_requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description
            FROM "05_grc_library"."12_fct_requirements" r
            LEFT JOIN "05_grc_library"."12_fct_requirements" parent
              ON parent.id = r.parent_requirement_id
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_name
              ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_desc
              ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            WHERE r.framework_id = $1::uuid AND r.is_deleted = FALSE
            ORDER BY r.sort_order, r.requirement_code
            """,
            source_framework_id,
        )

        # Sync requirements to clone
        existing_clone_reqs = await conn.fetch(
            """
            SELECT id::text, requirement_code
            FROM "05_grc_library"."12_fct_requirements"
            WHERE framework_id = $1::uuid
            """,
            clone_fw_id,
        )
        clone_req_by_code: dict[str, str] = {
            r["requirement_code"]: r["id"] for r in existing_clone_reqs
        }

        for req in source_reqs:
            req_code = req["requirement_code"]
            clone_req_id = clone_req_by_code.get(req_code)
            if clone_req_id:
                await conn.execute(
                    """
                    UPDATE "05_grc_library"."12_fct_requirements"
                    SET sort_order = $1,
                        parent_requirement_id = NULL,
                        is_active = TRUE,
                        is_disabled = FALSE,
                        is_deleted = FALSE,
                        updated_at = $2,
                        updated_by = $3::uuid
                    WHERE id = $4::uuid
                    """,
                    req["sort_order"],
                    now,
                    user_id,
                    clone_req_id,
                )
            else:
                clone_req_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."12_fct_requirements"
                        (id, framework_id, requirement_code, sort_order, parent_requirement_id,
                         is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                         created_at, updated_at, created_by, updated_by)
                    VALUES
                        ($1::uuid, $2::uuid, $3, $4, NULL,
                         TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                         $5, $6, $7::uuid, $8::uuid)
                    """,
                    clone_req_id,
                    clone_fw_id,
                    req_code,
                    req["sort_order"],
                    now,
                    now,
                    user_id,
                    user_id,
                )
                clone_req_by_code[req_code] = clone_req_id

            if req["name"] is not None:
                await self._upsert_property(
                    conn,
                    table='"05_grc_library"."22_dtl_requirement_properties"',
                    owner_col="requirement_id",
                    owner_id=clone_req_id,
                    key_col="property_key",
                    val_col="property_value",
                    key="name",
                    value=str(req["name"]),
                    actor_id=user_id,
                    now=now,
                    on_conflict_do_nothing=True,
                )
            if req["description"] is not None:
                await self._upsert_property(
                    conn,
                    table='"05_grc_library"."22_dtl_requirement_properties"',
                    owner_col="requirement_id",
                    owner_id=clone_req_id,
                    key_col="property_key",
                    val_col="property_value",
                    key="description",
                    value=str(req["description"]),
                    actor_id=user_id,
                    now=now,
                    on_conflict_do_nothing=True,
                )

        # Set parent requirements
        for req in source_reqs:
            parent_code = req["parent_requirement_code"]
            if not parent_code:
                continue
            child_id = clone_req_by_code.get(req["requirement_code"])
            parent_id = clone_req_by_code.get(parent_code)
            if child_id and parent_id:
                await conn.execute(
                    """
                    UPDATE "05_grc_library"."12_fct_requirements"
                    SET parent_requirement_id = $1::uuid,
                        updated_at = $2,
                        updated_by = $3::uuid
                    WHERE id = $4::uuid
                    """,
                    parent_id,
                    now,
                    user_id,
                    child_id,
                )

        # Get controls from source version
        version_controls_count = await conn.fetchval(
            """
            SELECT COUNT(*)::int
            FROM "05_grc_library"."31_lnk_framework_version_controls"
            WHERE framework_version_id = $1::uuid
            """,
            source_version_id,
        )
        use_all_controls = int(version_controls_count or 0) == 0
        source_controls = await conn.fetch(
            """
            SELECT c.id::text AS source_control_id,
                   c.control_code,
                   c.control_category_code,
                   c.criticality_code,
                   c.control_type,
                   c.automation_potential,
                   COALESCE(lvc.sort_order, c.sort_order) AS deploy_sort_order,
                   req.requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_guid.property_value AS guidance,
                   p_notes.property_value AS implementation_notes,
                   p_tags.property_value AS tags,
                   p_impl.property_value AS implementation_guidance,
                   p_teams.property_value AS responsible_teams
            FROM "05_grc_library"."13_fct_controls" c
            LEFT JOIN "05_grc_library"."31_lnk_framework_version_controls" lvc
              ON lvc.control_id = c.id
             AND lvc.framework_version_id = $2::uuid
            LEFT JOIN "05_grc_library"."12_fct_requirements" req
              ON req.id = c.requirement_id
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
              ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
              ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guid
              ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_notes
              ON p_notes.control_id = c.id AND p_notes.property_key = 'implementation_notes'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_tags
              ON p_tags.control_id = c.id AND p_tags.property_key = 'tags'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_impl
              ON p_impl.control_id = c.id AND p_impl.property_key = 'implementation_guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_teams
              ON p_teams.control_id = c.id AND p_teams.property_key = 'responsible_teams'
            WHERE c.framework_id = $1::uuid
              AND c.is_deleted = FALSE
              AND ($3::boolean OR lvc.framework_version_id IS NOT NULL)
            ORDER BY deploy_sort_order, c.control_code
            """,
            source_framework_id,
            source_version_id,
            use_all_controls,
        )

        # Sync controls to clone
        existing_clone_controls = await conn.fetch(
            """
            SELECT id::text, control_code
            FROM "05_grc_library"."13_fct_controls"
            WHERE framework_id = $1::uuid
            """,
            clone_fw_id,
        )
        clone_ctrl_by_code: dict[str, str] = {
            r["control_code"]: r["id"] for r in existing_clone_controls
        }
        source_to_clone_control: dict[str, str] = {}
        source_codes: set[str] = set()

        for ctrl in source_controls:
            ctrl_code = ctrl["control_code"]
            source_codes.add(ctrl_code)
            clone_ctrl_id = clone_ctrl_by_code.get(ctrl_code)
            requirement_id = (
                clone_req_by_code.get(ctrl["requirement_code"])
                if ctrl["requirement_code"]
                else None
            )
            if clone_ctrl_id:
                await conn.execute(
                    """
                    UPDATE "05_grc_library"."13_fct_controls"
                    SET requirement_id = $1::uuid,
                        control_category_code = $2,
                        criticality_code = $3,
                        control_type = $4,
                        automation_potential = $5,
                        sort_order = $6,
                        is_active = TRUE,
                        is_disabled = FALSE,
                        is_deleted = FALSE,
                        updated_at = $7,
                        updated_by = $8::uuid
                    WHERE id = $9::uuid
                    """,
                    requirement_id,
                    ctrl["control_category_code"],
                    ctrl["criticality_code"],
                    ctrl["control_type"],
                    ctrl["automation_potential"],
                    ctrl["deploy_sort_order"],
                    now,
                    user_id,
                    clone_ctrl_id,
                )
            else:
                clone_ctrl_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."13_fct_controls"
                        (id, framework_id, requirement_id, tenant_key, control_code,
                         control_category_code, criticality_code, control_type, automation_potential, sort_order,
                         is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                         created_at, updated_at, created_by, updated_by)
                    VALUES
                        ($1::uuid, $2::uuid, $3::uuid, $4, $5,
                         $6, $7, $8, $9, $10,
                         TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                         $11, $12, $13::uuid, $14::uuid)
                    """,
                    clone_ctrl_id,
                    clone_fw_id,
                    requirement_id,
                    tenant_key,
                    ctrl_code,
                    ctrl["control_category_code"],
                    ctrl["criticality_code"],
                    ctrl["control_type"],
                    ctrl["automation_potential"],
                    ctrl["deploy_sort_order"],
                    now,
                    now,
                    user_id,
                    user_id,
                )
                clone_ctrl_by_code[ctrl_code] = clone_ctrl_id

            source_to_clone_control[ctrl["source_control_id"]] = clone_ctrl_id
            for key in (
                "name",
                "description",
                "guidance",
                "implementation_notes",
                "tags",
                "implementation_guidance",
                "responsible_teams",
            ):
                value = ctrl.get(key)
                if value is not None:
                    await self._upsert_property(
                        conn,
                        table='"05_grc_library"."23_dtl_control_properties"',
                        owner_col="control_id",
                        owner_id=clone_ctrl_id,
                        key_col="property_key",
                        val_col="property_value",
                        key=key,
                        value=str(value),
                        actor_id=user_id,
                        now=now,
                        on_conflict_do_nothing=True,
                    )

        # Soft-delete controls no longer in source
        if source_codes:
            await conn.execute(
                """
                UPDATE "05_grc_library"."13_fct_controls"
                SET is_deleted = TRUE,
                    is_active = FALSE,
                    deleted_at = $1,
                    deleted_by = $2::uuid,
                    updated_at = $3,
                    updated_by = $4::uuid
                WHERE framework_id = $5::uuid
                  AND is_deleted = FALSE
                  AND NOT (control_code = ANY($6::text[]))
                """,
                now,
                user_id,
                now,
                user_id,
                clone_fw_id,
                list(source_codes),
            )

        # Update or create clone version
        clone_ver_row = await conn.fetchrow(
            """
            SELECT id::text
            FROM "05_grc_library"."11_fct_framework_versions"
            WHERE framework_id = $1::uuid
              AND version_code = $2
              AND is_deleted = FALSE
            LIMIT 1
            """,
            clone_fw_id,
            source_ver["version_code"],
        )
        clone_version_id = clone_ver_row["id"] if clone_ver_row else str(uuid.uuid4())
        if clone_ver_row:
            await conn.execute(
                """
                UPDATE "05_grc_library"."11_fct_framework_versions"
                SET change_severity = $1,
                    lifecycle_state = 'published',
                    control_count = $2,
                    is_active = TRUE,
                    is_disabled = FALSE,
                    is_deleted = FALSE,
                    updated_at = $3,
                    updated_by = $4::uuid
                WHERE id = $5::uuid
                """,
                source_ver["change_severity"],
                len(source_to_clone_control),
                now,
                user_id,
                clone_version_id,
            )
        else:
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."11_fct_framework_versions"
                    (id, framework_id, version_code, change_severity, lifecycle_state,
                     control_count, previous_version_id,
                     is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                     created_at, updated_at, created_by, updated_by)
                VALUES
                    ($1::uuid, $2::uuid, $3, $4, 'published',
                     $5, NULL,
                     TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                     $6, $7, $8::uuid, $9::uuid)
                """,
                clone_version_id,
                clone_fw_id,
                source_ver["version_code"],
                source_ver["change_severity"],
                len(source_to_clone_control),
                now,
                now,
                user_id,
                user_id,
            )

        for key in ("version_label", "release_notes", "change_summary"):
            value = source_ver.get(key)
            if value is not None:
                await self._upsert_property(
                    conn,
                    table='"05_grc_library"."21_dtl_version_properties"',
                    owner_col="framework_version_id",
                    owner_id=clone_version_id,
                    key_col="property_key",
                    val_col="property_value",
                    key=key,
                    value=str(value),
                    actor_id=user_id,
                    now=now,
                )

        # Update version controls link
        await conn.execute(
            """
            DELETE FROM "05_grc_library"."31_lnk_framework_version_controls"
            WHERE framework_version_id = $1::uuid
            """,
            clone_version_id,
        )
        for idx, ctrl in enumerate(source_controls):
            clone_ctrl_id = source_to_clone_control.get(ctrl["source_control_id"])
            if not clone_ctrl_id:
                continue
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."31_lnk_framework_version_controls"
                    (id, framework_version_id, control_id, sort_order, created_at, created_by)
                VALUES
                    (gen_random_uuid(), $1::uuid, $2::uuid, $3, $4, $5::uuid)
                ON CONFLICT (framework_version_id, control_id) DO NOTHING
                """,
                clone_version_id,
                clone_ctrl_id,
                int(
                    ctrl["deploy_sort_order"]
                    if ctrl["deploy_sort_order"] is not None
                    else idx
                ),
                now,
                user_id,
            )

        # CRITICAL: Update source_version_id property on the clone framework
        await self._upsert_property(
            conn,
            table='"05_grc_library"."20_dtl_framework_properties"',
            owner_col="framework_id",
            owner_id=clone_fw_id,
            key_col="property_key",
            val_col="property_value",
            key="source_version_id",
            value=source_version_id,
            actor_id=user_id,
            now=now,
        )

        await self._sync_workspace_risks(
            conn,
            tenant_key=tenant_key,
            org_id=scope_org_id,
            workspace_id=scope_workspace_id,
            framework_id=clone_fw_id,
            user_id=user_id,
            now=now,
        )
        return clone_fw_id, clone_version_id

    async def _next_clone_framework_code(
        self,
        conn,
        *,
        tenant_key: str,
        source_framework_code: str,
        workspace_id: str,
    ) -> str:
        suffix = workspace_id.replace("-", "")[:8].lower()
        base = f"{source_framework_code}__ws_{suffix}"
        candidate = base
        n = 2
        while True:
            exists = await conn.fetchrow(
                """
                SELECT 1
                FROM "05_grc_library"."10_fct_frameworks"
                WHERE tenant_key = $1 AND framework_code = $2
                LIMIT 1
                """,
                tenant_key,
                candidate,
            )
            if not exists:
                return candidate
            candidate = f"{base}_{n}"
            n += 1

    async def _sync_workspace_risks(
        self,
        conn,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        framework_id: str,
        user_id: str,
        now: object,
    ) -> None:
        rows = await conn.fetch(
            """
            SELECT
                gr.id::text AS global_risk_id,
                gr.risk_code,
                gr.risk_category_code,
                gr.risk_level_code,
                gt.property_value AS title,
                gd.property_value AS description,
                lnk.control_id::text AS control_id,
                lnk.mapping_type
            FROM "05_grc_library"."61_lnk_global_risk_control_mappings" lnk
            JOIN "05_grc_library"."13_fct_controls" c
              ON c.id = lnk.control_id
             AND c.framework_id = $1::uuid
             AND c.tenant_key = $2
             AND c.is_deleted = FALSE
            JOIN "05_grc_library"."50_fct_global_risks" gr
              ON gr.id = lnk.global_risk_id
             AND gr.tenant_key = $2
             AND gr.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" gt
              ON gt.global_risk_id = gr.id
             AND gt.property_key = 'title'
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" gd
              ON gd.global_risk_id = gr.id
             AND gd.property_key = 'description'
            ORDER BY gr.risk_code, lnk.control_id
            """,
            framework_id,
            tenant_key,
        )
        if not rows:
            return

        workspace_code_suffix = workspace_id.replace("-", "")[:8].lower()
        rr_risk_by_global: dict[str, str] = {}
        for row in rows:
            global_risk_id = row["global_risk_id"]
            rr_id = rr_risk_by_global.get(global_risk_id)
            if not rr_id:
                workspace_risk_code = f"{row['risk_code']}__ws_{workspace_code_suffix}"
                existing = await conn.fetchrow(
                    """
                    SELECT id::text
                    FROM "14_risk_registry"."10_fct_risks"
                    WHERE tenant_key = $1 AND risk_code = $2
                    LIMIT 1
                    """,
                    tenant_key,
                    workspace_risk_code,
                )
                if existing:
                    rr_id = existing["id"]
                    await conn.execute(
                        """
                        UPDATE "14_risk_registry"."10_fct_risks"
                        SET org_id = $1::uuid,
                            workspace_id = $2::uuid,
                            risk_category_code = COALESCE($3, risk_category_code),
                            risk_level_code = COALESCE($4, risk_level_code),
                            is_active = TRUE,
                            is_disabled = FALSE,
                            is_deleted = FALSE,
                            updated_at = $5,
                            updated_by = $6::uuid
                        WHERE id = $7::uuid
                        """,
                        org_id,
                        workspace_id,
                        row["risk_category_code"],
                        row["risk_level_code"],
                        now,
                        user_id,
                        rr_id,
                    )
                else:
                    rr_id = str(uuid.uuid4())
                    await conn.execute(
                        """
                        INSERT INTO "14_risk_registry"."10_fct_risks"
                            (id, tenant_key, risk_code, org_id, workspace_id,
                             risk_category_code, risk_level_code, treatment_type_code,
                             source_type, risk_status,
                             is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                             created_at, updated_at, created_by, updated_by)
                        VALUES
                            ($1::uuid, $2, $3, $4::uuid, $5::uuid,
                             $6, $7, 'mitigate',
                             'manual', 'identified',
                             TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                             $8, $9, $10::uuid, $11::uuid)
                        """,
                        rr_id,
                        tenant_key,
                        workspace_risk_code,
                        org_id,
                        workspace_id,
                        row["risk_category_code"] or "operational",
                        row["risk_level_code"] or "medium",
                        now,
                        now,
                        user_id,
                        user_id,
                    )

                title = str(row["title"] or "").strip() or str(row["risk_code"])
                description = str(row["description"] or "").strip()
                await self._upsert_property(
                    conn,
                    table='"14_risk_registry"."20_dtl_risk_properties"',
                    owner_col="risk_id",
                    owner_id=rr_id,
                    key_col="property_key",
                    val_col="property_value",
                    key="title",
                    value=title,
                    actor_id=user_id,
                    now=now,
                )
                if description:
                    await self._upsert_property(
                        conn,
                        table='"14_risk_registry"."20_dtl_risk_properties"',
                        owner_col="risk_id",
                        owner_id=rr_id,
                        key_col="property_key",
                        val_col="property_value",
                        key="description",
                        value=description,
                        actor_id=user_id,
                        now=now,
                    )

                await conn.execute(
                    """
                    INSERT INTO "05_grc_library"."17_fct_risk_library_deployments"
                        (id, tenant_key, org_id, workspace_id, global_risk_id, workspace_risk_id,
                         deployment_status, is_active, created_at, updated_at, created_by, updated_by)
                    VALUES
                        (gen_random_uuid(), $1, $2::uuid, $3::uuid, $4::uuid, $5::uuid,
                         'active', TRUE, $6, $7, $8::uuid, $9::uuid)
                    ON CONFLICT (org_id, workspace_id, global_risk_id)
                    DO UPDATE SET workspace_risk_id = EXCLUDED.workspace_risk_id,
                                  deployment_status = 'active',
                                  updated_at = EXCLUDED.updated_at,
                                  updated_by = EXCLUDED.updated_by
                    """,
                    tenant_key,
                    org_id,
                    workspace_id,
                    global_risk_id,
                    rr_id,
                    now,
                    now,
                    user_id,
                    user_id,
                )
                rr_risk_by_global[global_risk_id] = rr_id

            rr_link_type = _to_risk_registry_link_type(row["mapping_type"])
            await conn.execute(
                """
                INSERT INTO "14_risk_registry"."30_lnk_risk_control_mappings"
                    (id, risk_id, control_id, link_type, notes, created_at, created_by)
                VALUES
                    (gen_random_uuid(), $1::uuid, $2::uuid, $3, NULL, $4, $5::uuid)
                ON CONFLICT (risk_id, control_id) DO UPDATE
                SET link_type = EXCLUDED.link_type
                """,
                rr_risk_by_global[global_risk_id],
                row["control_id"],
                rr_link_type,
                now,
                user_id,
            )

    async def _upsert_property(
        self,
        conn,
        *,
        table: str,
        owner_col: str,
        owner_id: str,
        key_col: str,
        val_col: str,
        key: str,
        value: str,
        actor_id: str,
        now: object,
        on_conflict_do_nothing: bool = False,
    ) -> None:
        conflict_action = "DO NOTHING" if on_conflict_do_nothing else f"DO UPDATE SET {val_col} = EXCLUDED.{val_col}, updated_at = EXCLUDED.updated_at, updated_by = EXCLUDED.updated_by"
        
        await conn.execute(
            f"""
            INSERT INTO {table}
                (id, {owner_col}, {key_col}, {val_col}, created_at, updated_at, created_by, updated_by)
            VALUES
                (gen_random_uuid(), $1::uuid, $2, $3, $4, $5, $6::uuid, $7::uuid)
            ON CONFLICT ({owner_col}, {key_col}) {conflict_action}
            """,
            owner_id,
            key,
            value,
            now,
            now,
            actor_id,
            actor_id,
        )

    async def remove_deployment(
        self, *, user_id: str, tenant_key: str, deployment_id: str
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                existing = await self._repository.get_deployment(conn, deployment_id)
                if existing is None:
                    raise NotFoundError(f"Deployment '{deployment_id}' not found")
                await self._require_deployment_permission(
                    conn,
                    user_id=user_id,
                    permission_code="frameworks.delete",
                    org_id=existing.org_id,
                    workspace_id=existing.workspace_id,
                )
                await self._repository.update_deployment(
                    conn,
                    deployment_id,
                    deployment_status="removed",
                    updated_by=user_id,
                    now=now,
                )
                if existing.source_framework_id and existing.workspace_id:
                    await self._soft_delete_framework_clone(
                        conn,
                        framework_id=existing.framework_id,
                        actor_id=user_id,
                        now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="framework_deployment",
                        entity_id=deployment_id,
                        event_type="framework_deployment_removed",
                        event_category="framework",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"org_id": existing.org_id},
                    ),
                )
        await self._cache.delete_pattern(f"deployments:{existing.org_id}:*")

    async def _soft_delete_framework_clone(
        self,
        conn,
        *,
        framework_id: str,
        actor_id: str,
        now: object,
    ) -> None:
        await self._framework_repository.soft_delete_framework_graph(
            conn,
            framework_id,
            deleted_by=actor_id,
            now=now,
        )


def _to_risk_registry_link_type(mapping_type: object) -> str:
    value = str(mapping_type or "mitigating").strip().lower()
    if value in {"mitigating", "compensating", "related"}:
        return value
    if value in {"detecting", "detects", "monitors"}:
        return "related"
    return "mitigating"


def _deployment_response(r) -> FrameworkDeploymentResponse:
    return FrameworkDeploymentResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        framework_id=r.framework_id,
        deployed_version_id=r.deployed_version_id,
        deployment_status=r.deployment_status,
        workspace_id=r.workspace_id,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
        framework_code=r.framework_code,
        framework_name=r.framework_name,
        framework_description=r.framework_description,
        publisher_name=r.publisher_name,
        logo_url=r.logo_url,
        approval_status=r.approval_status,
        is_marketplace_visible=r.is_marketplace_visible,
        deployed_version_code=r.deployed_version_code,
        deployed_lifecycle_state=r.deployed_lifecycle_state,
        latest_version_id=r.latest_version_id,
        latest_version_code=r.latest_version_code,
        has_update=r.has_update,
        source_framework_id=r.source_framework_id,
        source_version_id=r.source_version_id,
    )
