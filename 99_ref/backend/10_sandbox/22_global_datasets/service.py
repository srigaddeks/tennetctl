from __future__ import annotations

import json
import uuid
from importlib import import_module

from .repository import GlobalDatasetRepository
from .schemas import (
    GlobalDatasetListResponse,
    GlobalDatasetResponse,
    GlobalDatasetStatsResponse,
    GlobalDatasetVersionListResponse,
    GlobalDatasetVersionResponse,
    PullResultResponse,
    PublishGlobalDatasetRequest,
    UpdateGlobalDatasetRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_settings_module = import_module("backend.00_config.settings")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission

_CACHE_TTL = 600  # 10 min
_CACHE_PREFIX = "sb:global_datasets"

logger = get_logger(__name__)


def _record_to_response(rec) -> GlobalDatasetResponse:
    return GlobalDatasetResponse(
        id=rec.id,
        global_code=rec.global_code,
        connector_type_code=rec.connector_type_code,
        connector_type_name=rec.connector_type_name,
        version_number=rec.version_number,
        json_schema=json.loads(rec.json_schema) if isinstance(rec.json_schema, str) else rec.json_schema,
        sample_payload=json.loads(rec.sample_payload) if isinstance(rec.sample_payload, str) else rec.sample_payload,
        record_count=rec.record_count,
        publish_status=rec.publish_status,
        is_featured=rec.is_featured,
        download_count=rec.download_count,
        source_dataset_id=rec.source_dataset_id,
        source_org_id=rec.source_org_id,
        published_by=rec.published_by,
        published_at=rec.published_at,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        name=rec.name,
        description=rec.description,
        tags=rec.tags,
        category=rec.category,
        collection_query=rec.collection_query,
        compatible_asset_types=rec.compatible_asset_types,
        changelog=rec.changelog,
    )


@instrument_class_methods(namespace="sandbox.global_datasets.service", logger_name="backend.sandbox.global_datasets.service.instrumentation")
class GlobalDatasetService:
    def __init__(self, *, settings: Settings, database_pool: DatabasePool, cache: CacheManager | NullCacheManager):
        self._settings = settings
        self._pool = database_pool
        self._cache = cache
        self._repo = GlobalDatasetRepository()

    # ── publish ──────────────────────────────────────────────────────

    async def _require_sandbox_permission(self, conn, *, user_id: str, permission_code: str, org_id: str) -> None:
        await require_permission(conn, user_id, permission_code, scope_org_id=org_id)

    async def publish_dataset(
        self,
        request: PublishGlobalDatasetRequest,
        org_id: str,
        user_id: str,
    ) -> GlobalDatasetResponse:
        async with self._pool.acquire() as conn:
            await self._require_sandbox_permission(conn, user_id=user_id, permission_code="sandbox.promote", org_id=org_id)
            # 1. Load source dataset
            source_row = await conn.fetchrow(
                """
                SELECT d.id, d.org_id, d.connector_instance_id, d.dataset_code,
                       d.schema_fingerprint, d.row_count
                FROM "15_sandbox"."21_fct_datasets" d
                WHERE d.id = $1 AND d.is_deleted = FALSE
                """,
                request.source_dataset_id,
            )
            if not source_row:
                raise NotFoundError("Source dataset not found")

            # 2. Get connector_type_code from connector instance
            connector_type_code = None
            if source_row["connector_instance_id"]:
                ci_row = await conn.fetchrow(
                    'SELECT connector_type_code FROM "15_sandbox"."20_fct_connector_instances" WHERE id = $1',
                    source_row["connector_instance_id"],
                )
                if ci_row:
                    connector_type_code = ci_row["connector_type_code"]

            # If no connector linked, try to get from properties
            if not connector_type_code:
                prop_row = await conn.fetchrow(
                    """
                    SELECT property_value FROM "15_sandbox"."42_dtl_dataset_properties"
                    WHERE dataset_id = $1 AND property_key = 'connector_type_code'
                    """,
                    request.source_dataset_id,
                )
                if prop_row:
                    connector_type_code = prop_row["property_value"]

            if not connector_type_code:
                raise ValidationError("Cannot determine connector type for this dataset. Link it to a connector first.")

            # 3. Get json_schema from source properties
            schema_row = await conn.fetchrow(
                """
                SELECT property_value FROM "15_sandbox"."42_dtl_dataset_properties"
                WHERE dataset_id = $1 AND property_key = 'json_schema'
                """,
                request.source_dataset_id,
            )
            json_schema = json.loads(schema_row["property_value"]) if schema_row and schema_row["property_value"] else {}

            # 4. Get sample records (max 10)
            record_rows = await conn.fetch(
                """
                SELECT record_data FROM "15_sandbox"."43_dtl_dataset_records" dr
                WHERE dr.dataset_id = $1
                ORDER BY dr.record_seq ASC LIMIT 10
                """,
                request.source_dataset_id,
            )
            sample_payload = []
            for rr in record_rows:
                rd = rr["record_data"]
                if isinstance(rd, str):
                    sample_payload.append(json.loads(rd))
                elif isinstance(rd, dict):
                    sample_payload.append(rd)

            # 5. Determine version
            max_ver = await self._repo.get_max_version(conn, request.global_code)
            new_version = max_ver + 1

            # 6. Insert global dataset
            dataset_id = str(uuid.uuid4())
            await self._repo.create(
                conn,
                dataset_id=dataset_id,
                global_code=request.global_code,
                connector_type_code=connector_type_code,
                version_number=new_version,
                source_dataset_id=request.source_dataset_id,
                source_org_id=org_id,
                json_schema=json_schema,
                sample_payload=sample_payload,
                record_count=len(sample_payload),
                published_by=user_id,
            )

            # 7. Set properties
            props = dict(request.properties)
            # Copy name/description from source if not provided
            if "name" not in props:
                name_row = await conn.fetchrow(
                    "SELECT property_value FROM \"15_sandbox\".\"42_dtl_dataset_properties\" WHERE dataset_id = $1 AND property_key = 'name'",
                    request.source_dataset_id,
                )
                if name_row and name_row["property_value"]:
                    props["name"] = name_row["property_value"]
            if "description" not in props:
                desc_row = await conn.fetchrow(
                    "SELECT property_value FROM \"15_sandbox\".\"42_dtl_dataset_properties\" WHERE dataset_id = $1 AND property_key = 'description'",
                    request.source_dataset_id,
                )
                if desc_row and desc_row["property_value"]:
                    props["description"] = desc_row["property_value"]

            if props:
                await self._repo.set_properties(conn, dataset_id, props)

            # 8. Invalidate cache
            await self._cache.delete(f"{_CACHE_PREFIX}:list")
            await self._cache.delete(f"{_CACHE_PREFIX}:list:{connector_type_code}")
            await self._cache.delete(f"{_CACHE_PREFIX}:stats")

            # 9. Return
            rec = await self._repo.get_by_id(conn, dataset_id)
            if not rec:
                raise NotFoundError("Failed to read back published dataset")
            return _record_to_response(rec)

    # ── list ─────────────────────────────────────────────────────────

    async def list_datasets(
        self,
        *,
        connector_type_code: str | None = None,
        category: str | None = None,
        search: str | None = None,
        publish_status: str | None = None,
        is_featured: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> GlobalDatasetListResponse:
        async with self._pool.acquire() as conn:
            records, total = await self._repo.list_datasets(
                conn,
                connector_type_code=connector_type_code,
                category=category,
                search=search,
                publish_status=publish_status,
                is_featured=is_featured,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
            return GlobalDatasetListResponse(
                items=[_record_to_response(r) for r in records],
                total=total,
            )

    # ── get ───────────────────────────────────────────────────────────

    async def get_dataset(self, dataset_id: str) -> GlobalDatasetResponse:
        async with self._pool.acquire() as conn:
            rec = await self._repo.get_by_id(conn, dataset_id)
            if not rec:
                raise NotFoundError("Global dataset not found")
            return _record_to_response(rec)

    # ── versions ─────────────────────────────────────────────────────

    async def list_versions(self, dataset_id: str) -> GlobalDatasetVersionListResponse:
        async with self._pool.acquire() as conn:
            # Get global_code from the dataset
            rec = await self._repo.get_by_id(conn, dataset_id)
            if not rec:
                raise NotFoundError("Global dataset not found")
            versions = await self._repo.list_versions(conn, rec.global_code)
            return GlobalDatasetVersionListResponse(
                global_code=rec.global_code,
                versions=[
                    GlobalDatasetVersionResponse(
                        version_number=v.version_number,
                        publish_status=v.publish_status,
                        record_count=v.record_count,
                        published_at=v.published_at,
                        changelog=v.changelog,
                        created_at=v.created_at,
                    )
                    for v in versions
                ],
            )

    # ── update ───────────────────────────────────────────────────────

    async def update_dataset(
        self,
        dataset_id: str,
        request: UpdateGlobalDatasetRequest,
        user_id: str,
        org_id: str,
    ) -> GlobalDatasetResponse:
        async with self._pool.acquire() as conn:
            await self._require_sandbox_permission(conn, user_id=user_id, permission_code="sandbox.promote", org_id=org_id)
            rec = await self._repo.get_by_id(conn, dataset_id)
            if not rec:
                raise NotFoundError("Global dataset not found")

            if request.properties:
                await self._repo.set_properties(conn, dataset_id, request.properties)
            if request.is_featured is not None:
                await self._repo.update_metadata(conn, dataset_id, is_featured=request.is_featured)

            # Invalidate cache
            await self._cache.delete(f"{_CACHE_PREFIX}:list")
            await self._cache.delete(f"{_CACHE_PREFIX}:list:{rec.connector_type_code}")
            await self._cache.delete(f"{_CACHE_PREFIX}:{dataset_id}")
            await self._cache.delete(f"{_CACHE_PREFIX}:stats")

            updated = await self._repo.get_by_id(conn, dataset_id)
            return _record_to_response(updated)  # type: ignore[arg-type]

    # ── deprecate ────────────────────────────────────────────────────

    async def deprecate_dataset(
        self,
        dataset_id: str,
        user_id: str,
        org_id: str,
    ) -> GlobalDatasetResponse:
        async with self._pool.acquire() as conn:
            await self._require_sandbox_permission(conn, user_id=user_id, permission_code="sandbox.promote", org_id=org_id)
            rec = await self._repo.get_by_id(conn, dataset_id)
            if not rec:
                raise NotFoundError("Global dataset not found")

            await self._repo.update_metadata(conn, dataset_id, publish_status="deprecated")

            await self._cache.delete(f"{_CACHE_PREFIX}:list")
            await self._cache.delete(f"{_CACHE_PREFIX}:list:{rec.connector_type_code}")
            await self._cache.delete(f"{_CACHE_PREFIX}:{dataset_id}")
            await self._cache.delete(f"{_CACHE_PREFIX}:stats")

            updated = await self._repo.get_by_id(conn, dataset_id)
            return _record_to_response(updated)  # type: ignore[arg-type]

    # ── pull ─────────────────────────────────────────────────────────

    async def pull_dataset(
        self,
        dataset_id: str,
        org_id: str,
        workspace_id: str | None,
        connector_instance_id: str | None,
        custom_dataset_code: str | None,
        user_id: str,
    ) -> PullResultResponse:
        async with self._pool.acquire() as conn:
            # 1. Load global dataset
            rec = await self._repo.get_by_id(conn, dataset_id)
            if not rec:
                raise NotFoundError("Global dataset not found")

            # 2. Generate local dataset_code
            dataset_code = custom_dataset_code or f"{rec.global_code}_v{rec.version_number}"

            # 3. Check for conflict
            existing = await conn.fetchrow(
                """
                SELECT id FROM "15_sandbox"."21_fct_datasets"
                WHERE org_id = $1 AND dataset_code = $2 AND is_deleted = FALSE
                ORDER BY version_number DESC LIMIT 1
                """,
                org_id, dataset_code,
            )
            if existing:
                raise ConflictError(f"Dataset code '{dataset_code}' already exists in this org")

            # 4. Create local dataset
            local_id = str(uuid.uuid4())
            json_schema = json.loads(rec.json_schema) if isinstance(rec.json_schema, str) else rec.json_schema
            sample_payload = json.loads(rec.sample_payload) if isinstance(rec.sample_payload, str) else rec.sample_payload

            await conn.execute(
                """
                INSERT INTO "15_sandbox"."21_fct_datasets"
                    (id, tenant_key, org_id, workspace_id, connector_instance_id,
                     dataset_code, dataset_source_code, version_number,
                     row_count, is_locked, is_active, created_by, updated_by)
                VALUES ($1, 'default', $2, $3, $4, $5, 'global_library', 1, 0, FALSE, TRUE, $6, $6)
                """,
                local_id, org_id, workspace_id, connector_instance_id,
                dataset_code, user_id,
            )

            # 5. Copy properties
            props: dict[str, str] = {
                "global_dataset_id": rec.id,
                "global_dataset_version": str(rec.version_number),
                "global_dataset_code": rec.global_code,
            }
            if rec.name:
                props["name"] = rec.name
            if rec.description:
                props["description"] = rec.description
            if rec.tags:
                props["tags"] = rec.tags
            if json_schema:
                props["json_schema"] = json.dumps(json_schema)
            if rec.collection_query:
                props["collection_query"] = rec.collection_query

            for key, value in props.items():
                prop_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "15_sandbox"."42_dtl_dataset_properties" (id, dataset_id, property_key, property_value)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (dataset_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                    """,
                    prop_id, local_id, key, value,
                )

            # 6. Copy sample records as initial data
            for idx, record_data in enumerate(sample_payload):
                record_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO "15_sandbox"."43_dtl_dataset_records"
                        (id, dataset_id, record_seq, recorded_at,
                         connector_instance_id, record_data)
                    VALUES ($1, $2, $3, NOW(), $4, $5::jsonb)
                    """,
                    record_id, local_id, idx + 1,
                    connector_instance_id, json.dumps(record_data),
                )

            # 7. Update row_count on local dataset
            await conn.execute(
                'UPDATE "15_sandbox"."21_fct_datasets" SET row_count = $1 WHERE id = $2',
                len(sample_payload), local_id,
            )

            # 8. Record pull + increment download count
            pull_id = str(uuid.uuid4())
            await self._repo.record_pull(
                conn,
                pull_id=pull_id,
                global_dataset_id=dataset_id,
                pulled_version=rec.version_number,
                target_org_id=org_id,
                target_workspace_id=workspace_id,
                target_dataset_id=local_id,
                pulled_by=user_id,
            )
            await self._repo.increment_download_count(conn, dataset_id)

            # 9. Invalidate caches
            await self._cache.delete(f"sb:datasets:{org_id}")
            await self._cache.delete(f"{_CACHE_PREFIX}:{dataset_id}")

            return PullResultResponse(
                local_dataset_id=local_id,
                dataset_code=dataset_code,
                version_number=1,
                global_source_code=rec.global_code,
                global_source_version=rec.version_number,
            )

    # ── stats ────────────────────────────────────────────────────────

    async def get_stats(self) -> GlobalDatasetStatsResponse:
        async with self._pool.acquire() as conn:
            data = await self._repo.get_stats(conn)
            return GlobalDatasetStatsResponse(**data)
