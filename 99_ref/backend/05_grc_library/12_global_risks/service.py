from __future__ import annotations

import uuid
from enum import StrEnum
from importlib import import_module

from .repository import GlobalRiskRepository
from .schemas import (
    CreateGlobalRiskRequest,
    GlobalRiskListResponse,
    GlobalRiskResponse,
    LinkControlRequest,
    UpdateGlobalRiskRequest,
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

_CACHE_TTL_GLOBAL_RISKS = 300  # 5 minutes


class GlobalRiskAuditEventType(StrEnum):
    RISK_CREATED = "global_risk_created"
    RISK_UPDATED = "global_risk_updated"
    RISK_DELETED = "global_risk_deleted"
    CONTROL_LINKED = "global_risk_control_linked"
    CONTROL_UNLINKED = "global_risk_control_unlinked"


@instrument_class_methods(namespace="grc.global_risks.service", logger_name="backend.grc.global_risks.instrumentation")
class GlobalRiskService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = GlobalRiskRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.grc.global_risks")

    # ── List ──────────────────────────────────────────────────────────────

    async def list_global_risks(
        self,
        *,
        user_id: str,
        tenant_key: str,

        category: str | None = None,
        search: str | None = None,
        sort_by: str | None = None,
        sort_dir: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> GlobalRiskListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "global_risk_library.view")

        has_filters = any([category, search])
        cache_key = f"global_risks:list:{tenant_key}"
        if not has_filters and limit >= 100 and offset == 0:
            cached = await self._cache.get(cache_key)
            if cached is not None:
                return GlobalRiskListResponse.model_validate_json(cached)

        async with self._database_pool.acquire() as conn:
            records, total = await self._repository.list_global_risks(
                conn,
                tenant_key=tenant_key,
                category=category,
                search=search,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_detail_response(r) for r in records]
        result = GlobalRiskListResponse(items=items, total=total)
        if not has_filters and limit >= 100 and offset == 0:
            await self._cache.set(cache_key, result.model_dump_json(), _CACHE_TTL_GLOBAL_RISKS)
        return result

    # ── Get ───────────────────────────────────────────────────────────────

    async def get_global_risk(self, *, user_id: str, global_risk_id: str) -> GlobalRiskResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "global_risk_library.view")
            record = await self._repository.get_by_id(conn, global_risk_id)
        if record is None:
            raise NotFoundError(f"Global risk '{global_risk_id}' not found")
        return _detail_response(record)

    # ── Create ────────────────────────────────────────────────────────────

    async def create_global_risk(
        self, *, user_id: str, tenant_key: str, request: CreateGlobalRiskRequest
    ) -> GlobalRiskResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.create")
                existing = await self._repository.get_by_code(conn, request.risk_code)
                if existing:
                    raise ConflictError(f"Global risk code '{request.risk_code}' already exists")
                risk = await self._repository.create(
                    conn,
                    risk_id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    risk_code=request.risk_code,
                    risk_category_code=request.risk_category_code,
                    risk_level_code=request.risk_level_code,
                    inherent_likelihood=request.inherent_likelihood,
                    inherent_impact=request.inherent_impact,
                    created_by=user_id,
                    now=now,
                )
                # Write EAV properties
                props: dict[str, str] = {}
                if request.title:
                    props["title"] = request.title
                if request.description:
                    props["description"] = request.description
                if request.short_description:
                    props["short_description"] = request.short_description
                if request.mitigation_guidance:
                    props["mitigation_guidance"] = request.mitigation_guidance
                if request.detection_guidance:
                    props["detection_guidance"] = request.detection_guidance
                if props:
                    await self._repository.upsert_properties(
                        conn, global_risk_id=risk.id, properties=props, created_by=user_id, now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="global_risk",
                        entity_id=risk.id,
                        event_type=GlobalRiskAuditEventType.RISK_CREATED.value,
                        event_category="global_risk",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "risk_code": request.risk_code,
                            "risk_category_code": request.risk_category_code,
                            "title": request.title,
                        },
                    ),
                )
        await self._cache.delete_pattern("global_risks:list:*")
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_by_id(conn, risk.id)
        return _detail_response(record)

    # ── Update ────────────────────────────────────────────────────────────

    async def update_global_risk(
        self, *, user_id: str, global_risk_id: str, request: UpdateGlobalRiskRequest
    ) -> GlobalRiskResponse:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.update")
                risk = await self._repository.update(
                    conn,
                    global_risk_id,
                    risk_category_code=request.risk_category_code,
                    risk_level_code=request.risk_level_code,
                    inherent_likelihood=request.inherent_likelihood,
                    inherent_impact=request.inherent_impact,
                    updated_by=user_id,
                    now=now,
                )
                if risk is None:
                    raise NotFoundError(f"Global risk '{global_risk_id}' not found")
                # Update EAV properties
                props: dict[str, str] = {}
                if request.title is not None:
                    props["title"] = request.title
                if request.description is not None:
                    props["description"] = request.description
                if request.short_description is not None:
                    props["short_description"] = request.short_description
                if request.mitigation_guidance is not None:
                    props["mitigation_guidance"] = request.mitigation_guidance
                if request.detection_guidance is not None:
                    props["detection_guidance"] = request.detection_guidance
                if props:
                    await self._repository.upsert_properties(
                        conn, global_risk_id=global_risk_id, properties=props, created_by=user_id, now=now,
                    )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=risk.tenant_key,
                        entity_type="global_risk",
                        entity_id=global_risk_id,
                        event_type=GlobalRiskAuditEventType.RISK_UPDATED.value,
                        event_category="global_risk",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"risk_code": risk.risk_code},
                    ),
                )
        await self._cache.delete_pattern("global_risks:list:*")
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_by_id(conn, global_risk_id)
        return _detail_response(record)

    # ── Delete ────────────────────────────────────────────────────────────

    async def delete_global_risk(self, *, user_id: str, global_risk_id: str) -> None:
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.delete")
                deleted = await self._repository.soft_delete(
                    conn, global_risk_id, deleted_by=user_id, now=now,
                )
                if not deleted:
                    raise NotFoundError(f"Global risk '{global_risk_id}' not found")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key="__platform__",
                        entity_type="global_risk",
                        entity_id=global_risk_id,
                        event_type=GlobalRiskAuditEventType.RISK_DELETED.value,
                        event_category="global_risk",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={},
                    ),
                )
        await self._cache.delete_pattern("global_risks:list:*")

    # ── Control Links ─────────────────────────────────────────────────────

    async def link_control(
        self, *, user_id: str, global_risk_id: str, request: LinkControlRequest
    ) -> GlobalRiskResponse:
        """Link a library control to this global risk."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.update")
                record = await self._repository.get_by_id(conn, global_risk_id)
                if record is None:
                    raise NotFoundError(f"Global risk '{global_risk_id}' not found")
                await self._repository.link_control(
                    conn,
                    global_risk_id=global_risk_id,
                    control_id=request.control_id,
                    mapping_type=request.mapping_type,
                    created_by=user_id,
                    now=now,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=record.tenant_key,
                        entity_type="global_risk",
                        entity_id=global_risk_id,
                        event_type=GlobalRiskAuditEventType.CONTROL_LINKED.value,
                        event_category="global_risk",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "control_id": request.control_id,
                            "mapping_type": request.mapping_type,
                        },
                    ),
                )
        await self._cache.delete_pattern("global_risks:list:*")
        async with self._database_pool.acquire() as conn:
            fresh = await self._repository.get_by_id(conn, global_risk_id)
        return _detail_response(fresh)

    async def unlink_control(
        self, *, user_id: str, global_risk_id: str, control_id: str
    ) -> None:
        """Remove a control link from this global risk."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.update")
                record = await self._repository.get_by_id(conn, global_risk_id)
                if record is None:
                    raise NotFoundError(f"Global risk '{global_risk_id}' not found")
                removed = await self._repository.unlink_control(
                    conn, global_risk_id=global_risk_id, control_id=control_id,
                )
                if not removed:
                    raise NotFoundError(f"Control link '{control_id}' not found on global risk '{global_risk_id}'")
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=record.tenant_key,
                        entity_type="global_risk",
                        entity_id=global_risk_id,
                        event_type=GlobalRiskAuditEventType.CONTROL_UNLINKED.value,
                        event_category="global_risk",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={"control_id": control_id},
                    ),
                )
        await self._cache.delete_pattern("global_risks:list:*")


    # ── Risk Library Deployments ──────────────────────────────────────────────

    async def list_risk_deployments(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
    ) -> dict:
        """List global risks deployed to a workspace."""
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "global_risk_library.view")
            rows = await conn.fetch(
                """
                SELECT id::text, global_risk_id::text, workspace_risk_id::text,
                       deployment_status, is_active, created_at::text, updated_at::text,
                       risk_code, title, short_description, risk_category_code, risk_category_name,
                       risk_level_code, risk_level_name, risk_level_color,
                       inherent_likelihood, inherent_impact, inherent_risk_score,
                       linked_control_count
                FROM "05_grc_library"."45_vw_risk_library_deployments"
                WHERE tenant_key = $1 AND org_id = $2 AND workspace_id = $3
                  AND deployment_status = 'active'
                  AND workspace_risk_id IS NOT NULL
                ORDER BY risk_code ASC
                """,
                tenant_key, org_id, workspace_id,
            )
        items = [dict(r) for r in rows]
        return {"items": items, "total": len(items)}

    async def deploy_global_risks(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        global_risk_ids: list[str],
    ) -> dict:
        """Deploy a set of global risks to a workspace (idempotent)."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.create")
                inserted = 0
                skipped = 0
                for gid in global_risk_ids:
                    workspace_risk_id = await self._ensure_workspace_risk(
                        conn,
                        tenant_key=tenant_key,
                        org_id=org_id,
                        workspace_id=workspace_id,
                        global_risk_id=gid,
                        user_id=user_id,
                        now=now,
                    )
                    created_new_row = await conn.fetchval(
                        """
                        INSERT INTO "05_grc_library"."17_fct_risk_library_deployments"
                            (id, tenant_key, org_id, workspace_id, global_risk_id,
                             workspace_risk_id,
                             deployment_status, is_active,
                             created_at, updated_at, created_by, updated_by)
                        VALUES (gen_random_uuid(), $1, $2::uuid, $3::uuid, $4::uuid,
                                $5::uuid, 'active', TRUE, $6, $7, $8::uuid, $9::uuid)
                        ON CONFLICT (org_id, workspace_id, global_risk_id)
                        DO UPDATE SET deployment_status = 'active',
                                      workspace_risk_id = EXCLUDED.workspace_risk_id,
                                      updated_at = EXCLUDED.updated_at,
                                      updated_by = EXCLUDED.updated_by
                        RETURNING (xmax = 0) AS inserted
                        """,
                        tenant_key, org_id, workspace_id, gid,
                        workspace_risk_id,
                        now, now, user_id, user_id,
                    )
                    await self._sync_workspace_risk_control_links(
                        conn,
                        tenant_key=tenant_key,
                        org_id=org_id,
                        workspace_id=workspace_id,
                        global_risk_id=gid,
                        workspace_risk_id=workspace_risk_id,
                        user_id=user_id,
                        now=now,
                    )
                    if created_new_row:
                        inserted += 1
                    else:
                        skipped += 1
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="risk_library_deployment",
                        entity_id=workspace_id,
                        event_type="risk_library_deployed",
                        event_category="global_risk",
                        occurred_at=now,
                        actor_id=user_id,
                        actor_type="user",
                        properties={
                            "org_id": org_id,
                            "workspace_id": workspace_id,
                            "count": str(len(global_risk_ids)),
                        },
                    ),
                )
        return {
            "deployed": len(global_risk_ids),
            "inserted": inserted,
            "skipped": skipped,
            "org_id": org_id,
            "workspace_id": workspace_id,
        }

    async def remove_risk_deployment(
        self,
        *,
        user_id: str,
        tenant_key: str,
        deployment_id: str,
    ) -> None:
        """Remove a risk library deployment (soft-delete)."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            async with conn.transaction():
                await require_permission(conn, user_id, "global_risk_library.delete")
                result = await conn.execute(
                    """
                    UPDATE "05_grc_library"."17_fct_risk_library_deployments"
                    SET deployment_status = 'removed', updated_at = $1, updated_by = $2::uuid
                    WHERE id = $3 AND deployment_status = 'active'
                    """,
                    now, user_id, deployment_id,
                )
                if result == "UPDATE 0":
                    raise NotFoundError(f"Risk deployment '{deployment_id}' not found")
            
    async def _ensure_workspace_risk(
        self,
        conn,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        global_risk_id: str,
        user_id: str,
        now: object,
    ) -> str:
        global_risk = await conn.fetchrow(
            """
            SELECT gr.id::text AS global_risk_id,
                   gr.risk_code,
                   gr.risk_category_code,
                   gr.risk_level_code,
                   pt.property_value AS title,
                   COALESCE(pd.property_value, ps.property_value) AS description
            FROM "05_grc_library"."50_fct_global_risks" gr
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" pt
              ON pt.global_risk_id = gr.id
             AND pt.property_key = 'title'
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" pd
              ON pd.global_risk_id = gr.id
             AND pd.property_key = 'description'
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" ps
              ON ps.global_risk_id = gr.id
             AND ps.property_key = 'short_description'
            WHERE gr.id = $1::uuid
              AND gr.tenant_key = $2
              AND gr.is_deleted = FALSE
            """,
            global_risk_id,
            tenant_key,
        )
        if global_risk is None:
            raise NotFoundError(f"Global risk '{global_risk_id}' not found")

        workspace_suffix = workspace_id.replace("-", "")[:8].lower()
        workspace_risk_code = f"{global_risk['risk_code']}__ws_{workspace_suffix}"
        existing = await conn.fetchrow(
            """
            SELECT id::text
            FROM "14_risk_registry"."10_fct_risks"
            WHERE tenant_key = $1
              AND risk_code = $2
            LIMIT 1
            """,
            tenant_key,
            workspace_risk_code,
        )
        if existing is not None:
            workspace_risk_id = existing["id"]
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
                global_risk["risk_category_code"],
                global_risk["risk_level_code"],
                now,
                user_id,
                workspace_risk_id,
            )
        else:
            workspace_risk_id = str(uuid.uuid4())
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
                workspace_risk_id,
                tenant_key,
                workspace_risk_code,
                org_id,
                workspace_id,
                global_risk["risk_category_code"] or "operational",
                global_risk["risk_level_code"] or "medium",
                now,
                now,
                user_id,
                user_id,
            )

        title = str(global_risk["title"] or "").strip() or str(global_risk["risk_code"])
        await conn.execute(
            """
            INSERT INTO "14_risk_registry"."20_dtl_risk_properties"
                (id, risk_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
            VALUES
                (gen_random_uuid(), $1::uuid, 'title', $2, $3, $4, $5::uuid, $6::uuid)
            ON CONFLICT (risk_id, property_key)
            DO UPDATE SET property_value = EXCLUDED.property_value,
                          updated_at = EXCLUDED.updated_at,
                          updated_by = EXCLUDED.updated_by
            """,
            workspace_risk_id,
            title,
            now,
            now,
            user_id,
            user_id,
        )

        description = str(global_risk["description"] or "").strip()
        if description:
            await conn.execute(
                """
                INSERT INTO "14_risk_registry"."20_dtl_risk_properties"
                    (id, risk_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES
                    (gen_random_uuid(), $1::uuid, 'description', $2, $3, $4, $5::uuid, $6::uuid)
                ON CONFLICT (risk_id, property_key)
                DO UPDATE SET property_value = EXCLUDED.property_value,
                              updated_at = EXCLUDED.updated_at,
                              updated_by = EXCLUDED.updated_by
                """,
                workspace_risk_id,
                description,
                now,
                now,
                user_id,
                user_id,
            )

        return workspace_risk_id

    async def _sync_workspace_risk_control_links(
        self,
        conn,
        *,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        global_risk_id: str,
        workspace_risk_id: str,
        user_id: str,
        now: object,
    ) -> None:
        links = await conn.fetch(
            """
            SELECT DISTINCT c_ws.id::text AS control_id, lnk.mapping_type
            FROM "05_grc_library"."61_lnk_global_risk_control_mappings" lnk
            JOIN "05_grc_library"."13_fct_controls" c_src
              ON c_src.id = lnk.control_id
             AND c_src.is_deleted = FALSE
            JOIN "05_grc_library"."13_fct_controls" c_ws
              ON c_ws.control_code = c_src.control_code
             AND c_ws.is_deleted = FALSE
            JOIN "05_grc_library"."16_fct_framework_deployments" d
              ON d.framework_id = c_ws.framework_id
             AND d.tenant_key = $1
             AND d.org_id = $2::uuid
             AND d.workspace_id = $3::uuid
             AND d.deployment_status = 'active'
            WHERE lnk.global_risk_id = $4::uuid
            """,
            tenant_key,
            org_id,
            workspace_id,
            global_risk_id,
        )
        for link in links:
            await conn.execute(
                """
                INSERT INTO "14_risk_registry"."30_lnk_risk_control_mappings"
                    (id, risk_id, control_id, link_type, notes, created_at, created_by)
                VALUES
                    (gen_random_uuid(), $1::uuid, $2::uuid, $3, NULL, $4, $5::uuid)
                ON CONFLICT (risk_id, control_id) DO UPDATE
                SET link_type = EXCLUDED.link_type
                """,
                workspace_risk_id,
                link["control_id"],
                _to_risk_registry_link_type(link["mapping_type"]),
                now,
                user_id,
            )


def _detail_response(r) -> GlobalRiskResponse:
    return GlobalRiskResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        risk_code=r.risk_code,
        risk_category_code=r.risk_category_code,
        risk_category_name=r.risk_category_name,
        risk_level_code=r.risk_level_code,
        risk_level_name=r.risk_level_name,
        risk_level_color=r.risk_level_color,
        inherent_likelihood=r.inherent_likelihood,
        inherent_impact=r.inherent_impact,
        inherent_risk_score=r.inherent_risk_score,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        created_by=r.created_by,
        title=r.title,
        description=r.description,
        short_description=r.short_description,
        mitigation_guidance=r.mitigation_guidance,
        detection_guidance=r.detection_guidance,
        linked_control_count=r.linked_control_count,
        version=1,
    )


def _to_risk_registry_link_type(mapping_type: object) -> str:
    value = str(mapping_type or "mitigating").strip().lower()
    if value in {"mitigating", "compensating", "related"}:
        return value
    if value in {"detecting", "detects", "monitors"}:
        return "related"
    return "mitigating"
