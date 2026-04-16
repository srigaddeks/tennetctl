from __future__ import annotations

import hashlib
import json
import uuid
from importlib import import_module

from .repository import AssetRepository
from .schemas import (
    AssetAccessGrantResponse,
    AssetChangeEntry,
    AssetListResponse,
    AssetResponse,
    AssetStatsByStatus,
    AssetStatsByType,
    AssetStatsResponse,
    ConnectorHealthSummary,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.10_sandbox.constants")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ForbiddenError = _errors_module.AuthorizationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_KEY_PREFIX = "sb:assets"
_CACHE_TTL = 300


@instrument_class_methods(
    namespace="sandbox.assets.service",
    logger_name="backend.sandbox.assets.instrumentation",
)
class AssetService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = AssetRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.assets")

    async def list_assets(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        connector_id: str | None = None,
        asset_type: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
        user_group_ids: list[str] | None = None,
    ) -> AssetListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            all_assets, total = await self._repository.list_assets(
                conn,
                org_id=org_id,
                connector_id=connector_id,
                asset_type=asset_type,
                status=status,
                offset=offset,
                limit=limit,
            )

            # Filter to assets the caller's groups can view
            if user_group_ids:
                visible_assets = []
                for asset in all_assets:
                    for group_id in user_group_ids:
                        can_view = await self._repository.check_access_grant(
                            conn, asset.id, group_id, "view"
                        )
                        if can_view:
                            visible_assets.append(asset)
                            break
            else:
                visible_assets = list(all_assets)

        items = [_asset_response(a) for a in visible_assets]
        return AssetListResponse(items=items, total=total)

    async def get_asset_with_access_check(
        self,
        *,
        user_id: str,
        asset_id: str,
        org_id: str,
        user_group_ids: list[str] | None = None,
    ) -> AssetResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")

            if user_group_ids:
                has_access = False
                for group_id in user_group_ids:
                    if await self._repository.check_access_grant(
                        conn, asset_id, group_id, "view"
                    ):
                        has_access = True
                        break
                if not has_access:
                    raise ForbiddenError("You do not have view access to this asset")

            props = await self._repository.get_asset_properties(conn, asset_id)

        properties = (
            {p.property_key: p.property_value for p in props} if props else None
        )
        return _asset_response(asset, properties=properties)

    async def soft_delete_asset(
        self,
        *,
        user_id: str,
        tenant_key: str,
        asset_id: str,
        org_id: str,
        deleted_by: str,
        user_group_ids: list[str] | None = None,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.delete")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")

            if user_group_ids:
                has_access = False
                for group_id in user_group_ids:
                    if await self._repository.check_access_grant(
                        conn, asset_id, group_id, "edit"
                    ):
                        has_access = True
                        break
                if not has_access:
                    raise ForbiddenError("You do not have edit access to this asset")

            await self._repository.soft_delete_asset(conn, asset_id, deleted_by)
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset",
                    entity_id=asset_id,
                    event_type=SandboxAuditEventType.ASSET_DELETED.value,
                    event_category="asset_inventory",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "provider_code": asset.provider_code,
                        "asset_type_code": asset.asset_type_code,
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def grant_access(
        self,
        *,
        user_id: str,
        tenant_key: str,
        asset_id: str,
        org_id: str,
        user_group_id: str,
        role_code: str,
        granted_by: str,
    ) -> AssetAccessGrantResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.update")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")
            grant = await self._repository.create_access_grant(
                conn,
                asset_id=asset_id,
                user_group_id=user_group_id,
                role_code=role_code,
                granted_by=granted_by,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset",
                    entity_id=asset_id,
                    event_type=SandboxAuditEventType.ASSET_ACCESS_GRANTED.value,
                    event_category="asset_inventory",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "user_group_id": user_group_id,
                        "role_code": role_code,
                    },
                ),
            )

        return _grant_response(grant)

    async def revoke_access(
        self,
        *,
        user_id: str,
        tenant_key: str,
        grant_id: str,
        asset_id: str,
        org_id: str,
        revoked_by: str,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.update")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")
            deleted = await self._repository.delete_access_grant(conn, grant_id)
            if not deleted:
                raise NotFoundError(f"Access grant '{grant_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset",
                    entity_id=asset_id,
                    event_type=SandboxAuditEventType.ASSET_ACCESS_REVOKED.value,
                    event_category="asset_inventory",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"grant_id": grant_id},
                ),
            )

    async def get_asset_changes(
        self,
        *,
        user_id: str,
        asset_id: str,
        org_id: str,
    ) -> list[AssetChangeEntry]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")
            snapshots = await self._repository.get_snapshots(conn, asset_id, limit=20)

        if len(snapshots) < 2:
            return []

        # Snapshots are ordered newest-first; reverse for oldest-first comparison
        ordered = list(reversed(snapshots))
        changes: list[AssetChangeEntry] = []

        # We need properties for each snapshot — fetch in pairs
        for i in range(len(ordered) - 1):
            older = ordered[i]
            newer = ordered[i + 1]

            async with self._database_pool.acquire() as conn:
                older_props_list = await self._repository.get_snapshot_properties(
                    conn, older.id
                )
                newer_props_list = await self._repository.get_snapshot_properties(
                    conn, newer.id
                )

            older_props = {p.property_key: p.property_value for p in older_props_list}
            newer_props = {p.property_key: p.property_value for p in newer_props_list}

            all_keys = set(older_props) | set(newer_props)
            for key in sorted(all_keys):
                old_val = older_props.get(key)
                new_val = newer_props.get(key)
                if old_val != new_val:
                    changes.append(
                        AssetChangeEntry(
                            property_key=key,
                            old_value=old_val,
                            new_value=new_val,
                            changed_at=newer.collected_at,
                        )
                    )

        return changes

    async def list_access_grants(
        self,
        *,
        user_id: str,
        asset_id: str,
        org_id: str,
    ) -> list[AssetAccessGrantResponse]:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")
            grants = await self._repository.list_access_grants(conn, asset_id)

        return [_grant_response(g) for g in grants]

    async def get_asset_properties(
        self,
        *,
        user_id: str,
        asset_id: str,
        org_id: str,
    ):
        from .schemas import AssetPropertyResponse

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")
            props = await self._repository.get_asset_properties(conn, asset_id)

        return [
            AssetPropertyResponse(
                id=p.id,
                asset_id=p.asset_id,
                property_key=p.property_key,
                property_value=p.property_value,
                value_type=p.value_type,
                collected_at=p.collected_at,
            )
            for p in props
        ]

    async def get_asset_snapshots(
        self,
        *,
        user_id: str,
        asset_id: str,
        org_id: str,
    ):
        from .schemas import AssetSnapshotResponse

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            asset = await self._repository.get_asset(conn, asset_id, org_id)
            if asset is None:
                raise NotFoundError(f"Asset '{asset_id}' not found")
            snapshots = await self._repository.get_snapshots(conn, asset_id)

        return [
            AssetSnapshotResponse(
                id=s.id,
                asset_id=s.asset_id,
                collection_run_id=s.collection_run_id,
                snapshot_number=s.snapshot_number,
                schema_fingerprint=s.schema_fingerprint,
                property_count=s.property_count,
                collected_at=s.collected_at,
            )
            for s in snapshots
        ]


def compute_schema_fingerprint(properties: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(sorted(properties.keys())).encode()).hexdigest()[
        :16
    ]


def _asset_response(a, properties: dict[str, str] | None = None) -> AssetResponse:
    return AssetResponse(
        id=a.id,
        tenant_key=a.tenant_key,
        org_id=a.org_id,
        workspace_id=a.workspace_id,
        connector_instance_id=a.connector_instance_id,
        provider_code=a.provider_code,
        asset_type_code=a.asset_type_code,
        asset_external_id=a.asset_external_id,
        parent_asset_id=a.parent_asset_id,
        status_code=a.status_code,
        current_snapshot_id=a.current_snapshot_id,
        last_collected_at=a.last_collected_at,
        consecutive_misses=a.consecutive_misses,
        created_by=a.created_by,
        created_at=a.created_at,
        updated_at=a.updated_at,
        is_deleted=a.is_deleted,
        properties=properties,
    )

    async def get_stats(
        self,
        *,
        user_id: str,
        org_id: str,
    ) -> AssetStatsResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")

            total_row = await conn.fetchrow(
                'SELECT COUNT(*)::int AS total FROM "15_sandbox"."33_fct_assets"'
                " WHERE org_id = $1 AND is_deleted = FALSE",
                org_id,
            )
            total = total_row["total"] if total_row else 0

            type_rows = await conn.fetch(
                "SELECT asset_type_code, COUNT(*)::int AS cnt"
                ' FROM "15_sandbox"."33_fct_assets"'
                " WHERE org_id = $1 AND is_deleted = FALSE"
                " GROUP BY asset_type_code ORDER BY cnt DESC",
                org_id,
            )

            status_rows = await conn.fetch(
                "SELECT status_code, COUNT(*)::int AS cnt"
                ' FROM "15_sandbox"."33_fct_assets"'
                " WHERE org_id = $1 AND is_deleted = FALSE"
                " GROUP BY status_code ORDER BY cnt DESC",
                org_id,
            )

            connector_rows = await conn.fetch(
                "SELECT id::text, provider_definition_code, health_status,"
                "       consecutive_failures, last_collected_at::text, collection_schedule"
                ' FROM "15_sandbox"."20_fct_connector_instances"'
                " WHERE org_id = $1 AND is_deleted = FALSE"
                "   AND provider_definition_code IS NOT NULL"
                " ORDER BY created_at DESC",
                org_id,
            )

            last_row = await conn.fetchrow(
                "SELECT MAX(last_collected_at)::text AS last_at"
                ' FROM "15_sandbox"."33_fct_assets"'
                " WHERE org_id = $1 AND is_deleted = FALSE",
                org_id,
            )

        return AssetStatsResponse(
            total_assets=total,
            by_type=[
                AssetStatsByType(asset_type_code=r["asset_type_code"], count=r["cnt"])
                for r in type_rows
            ],
            by_status=[
                AssetStatsByStatus(status_code=r["status_code"], count=r["cnt"])
                for r in status_rows
            ],
            connectors=[
                ConnectorHealthSummary(
                    connector_id=r["id"],
                    provider_code=r["provider_definition_code"],
                    health_status=r["health_status"],
                    consecutive_failures=r["consecutive_failures"],
                    last_collected_at=r["last_collected_at"],
                    collection_schedule=r["collection_schedule"],
                )
                for r in connector_rows
            ],
            last_collection_at=last_row["last_at"] if last_row else None,
        )


def _grant_response(g) -> AssetAccessGrantResponse:
    return AssetAccessGrantResponse(
        id=g.id,
        asset_id=g.asset_id,
        user_group_id=g.user_group_id,
        role_code=g.role_code,
        granted_by=g.granted_by,
        granted_at=g.granted_at,
    )
