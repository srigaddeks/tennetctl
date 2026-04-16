from __future__ import annotations

import asyncio
import hashlib
import json
import re
import uuid
from importlib import import_module

from .repository import DatasetRepository
from .schemas import (
    AddRecordsRequest,
    ComposeDatasetRequest,
    ComposeDatasetResponse,
    CreateDatasetRequest,
    DatasetDataRecord,
    DatasetListResponse,
    DatasetRecordsResponse,
    DatasetResponse,
    FieldOverrideRequest,
    SchemaDriftResponse,
    UpdateDatasetRequest,
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
_constants_module = import_module("backend.10_sandbox.constants")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql

_CACHE_TTL = 300
_CACHE_KEY_PREFIX = "sb:datasets"


def _cache_key(org_id: str) -> str:
    return f"{_CACHE_KEY_PREFIX}:{org_id}"


def _slugify(name: str) -> str:
    """Convert a name to a lowercase slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^a-z0-9\s_-]", "", slug)
    slug = re.sub(r"[\s_-]+", "-", slug)
    slug = slug.strip("-")
    return slug[:80] if slug else "dataset"


def _compute_schema_fingerprint(record: dict) -> str:
    """SHA-256 of sorted JSON keys from a single record."""
    def _sorted_keys(obj: object) -> list:
        if isinstance(obj, dict):
            return sorted([k, _sorted_keys(v)] for k, v in obj.items())
        if isinstance(obj, list):
            return [_sorted_keys(item) for item in obj]
        return []

    keys_structure = _sorted_keys(record)
    raw = json.dumps(keys_structure, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


@instrument_class_methods(namespace="sandbox.datasets.service", logger_name="backend.sandbox.datasets.instrumentation")
class DatasetService:
    # Class-level tracking for background description generation jobs
    _generation_jobs: dict[str, dict] = {}

    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = DatasetRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.datasets")

    async def _require_sandbox_permission(
        self,
        conn,
        *,
        user_id: str,
        permission_code: str,
        org_id: str,
        workspace_id: str | None = None,
    ) -> None:
        await require_permission(
            conn,
            user_id,
            permission_code,
            scope_org_id=org_id,
            scope_workspace_id=workspace_id,
        )

    async def _get_dataset_or_not_found(self, conn, dataset_id: str):
        record = await self._repository.get_dataset_by_id(conn, dataset_id)
        if record is None:
            raise NotFoundError(f"Dataset '{dataset_id}' not found")
        return record

    # ── list ──────────────────────────────────────────────────────────

    async def list_datasets(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        connector_instance_id: str | None = None,
        dataset_source_code: str | None = None,
        is_locked: bool | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> DatasetListResponse:
        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
                workspace_id=workspace_id,
            )
            records, total = await self._repository.list_datasets(
                conn,
                org_id,
                workspace_id=workspace_id,
                connector_instance_id=connector_instance_id,
                dataset_source_code=dataset_source_code,
                is_locked=is_locked,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
        items = [_dataset_response(r) for r in records]
        return DatasetListResponse(items=items, total=total)

    # ── get ───────────────────────────────────────────────────────────

    async def get_dataset(
        self, *, user_id: str, dataset_id: str,
    ) -> DatasetResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
                workspace_id=record.workspace_id,
            )
        return _dataset_response(record)

    # ── get records ───────────────────────────────────────────────────

    async def get_dataset_records(
        self,
        *,
        user_id: str,
        dataset_id: str,
        limit: int = 500,
        offset: int = 0,
    ) -> DatasetRecordsResponse:
        async with self._database_pool.acquire() as conn:
            dataset = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=dataset.org_id,
                workspace_id=dataset.workspace_id,
            )
            records, total = await self._repository.list_records(
                conn, dataset_id, limit=limit, offset=offset,
            )

        parsed_records = []
        for r in records:
            rd = r.record_data
            # Handle double-encoded JSON strings in JSONB
            if isinstance(rd, str):
                try:
                    rd = json.loads(rd)
                except (json.JSONDecodeError, TypeError):
                    rd = {}
            # If still a string after first parse (double-encoded), parse again
            if isinstance(rd, str):
                try:
                    rd = json.loads(rd)
                except (json.JSONDecodeError, TypeError):
                    rd = {}
            if not isinstance(rd, dict):
                rd = {"_raw": rd}
            parsed_records.append(
                DatasetDataRecord(
                    id=r.id,
                    dataset_id=r.dataset_id,
                    record_seq=r.record_seq,
                    record_name=getattr(r, "record_name", "") or "",
                    recorded_at=r.recorded_at,
                    source_asset_id=r.source_asset_id,
                    connector_instance_id=r.connector_instance_id,
                    record_data=rd,
                    description=getattr(r, "description", "") or "",
                )
            )

        return DatasetRecordsResponse(
            dataset_id=dataset_id,
            records=parsed_records,
            total=total,
        )

    # ── create ────────────────────────────────────────────────────────

    async def create_dataset(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: CreateDatasetRequest,
    ) -> DatasetResponse:
        now = utc_now_sql()
        dataset_id = str(uuid.uuid4())

        # Auto-generate dataset_code from name property or a UUID suffix
        name = (request.properties or {}).get("name", "")
        base_slug = _slugify(name) if name else "dataset"
        dataset_code = f"{base_slug}-{dataset_id[:8]}"

        row_count = len(request.records) if request.records else 0
        schema_fingerprint: str | None = None
        if request.records:
            schema_fingerprint = _compute_schema_fingerprint(request.records[0])

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
                workspace_id=request.workspace_id,
            )
            version_number = await self._repository.get_next_version_number(
                conn, org_id, dataset_code,
            )
            await self._repository.create_dataset(
                conn,
                id=dataset_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                connector_instance_id=request.connector_instance_id,
                dataset_code=dataset_code,
                dataset_source_code=request.dataset_source_code,
                version_number=version_number,
                schema_fingerprint=schema_fingerprint,
                row_count=row_count,
                byte_size=0,
                asset_ids=request.asset_ids,
                created_by=user_id,
                now=now,
            )

            if request.properties:
                await self._repository.upsert_properties(
                    conn, dataset_id, request.properties, created_by=user_id, now=now,
                )

            if request.records:
                record_jsons = [json.dumps(r, separators=(",", ":")) for r in request.records]
                await self._repository.add_records(
                    conn,
                    dataset_id=dataset_id,
                    records=record_jsons,
                    source_asset_id=None,
                    connector_instance_id=request.connector_instance_id,
                    start_seq=1,
                    now=now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=dataset_id,
                    event_type=SandboxAuditEventType.DATASET_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "dataset_code": dataset_code,
                        "version_number": str(version_number),
                        "record_count": str(row_count),
                    },
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, dataset_id)
        return _dataset_response(record)

    # ── add records ───────────────────────────────────────────────────

    async def add_records(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        dataset_id: str,
        request: AddRecordsRequest,
    ) -> DatasetResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            if existing.is_locked:
                raise ConflictError(f"Dataset '{dataset_id}' is locked")

            next_seq = await self._repository.get_next_record_seq(conn, dataset_id)
            record_jsons = [json.dumps(r, separators=(",", ":")) for r in request.records]
            await self._repository.add_records(
                conn,
                dataset_id=dataset_id,
                records=record_jsons,
                source_asset_id=request.source_asset_id,
                connector_instance_id=request.connector_instance_id,
                start_seq=next_seq,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=dataset_id,
                    event_type=SandboxAuditEventType.DATASET_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"records_added": str(len(request.records))},
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, dataset_id)
        return _dataset_response(record)

    # ── update ────────────────────────────────────────────────────────

    async def update_dataset(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        dataset_id: str,
        request: UpdateDatasetRequest,
    ) -> DatasetResponse:
        now = utc_now_sql()

        async with self._database_pool.transaction() as conn:
            existing = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            if existing.is_locked:
                raise ConflictError(f"Dataset '{dataset_id}' is locked")

            if request.properties:
                await self._repository.upsert_properties(
                    conn, dataset_id, request.properties, created_by=user_id, now=now,
                )

            if request.asset_ids is not None:
                await self._repository.update_asset_ids(
                    conn, dataset_id, request.asset_ids, now,
                )

            if request.connector_instance_id is not None:
                # Pass empty string to clear the connector link, or a valid UUID to set it
                cid = request.connector_instance_id if request.connector_instance_id != "" else None
                await self._repository.update_connector(
                    conn, dataset_id, cid, now,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=dataset_id,
                    event_type=SandboxAuditEventType.DATASET_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, dataset_id)
        return _dataset_response(record)

    # ── lock ──────────────────────────────────────────────────────────

    async def lock_dataset(
        self, *, user_id: str, tenant_key: str, org_id: str, dataset_id: str,
    ) -> DatasetResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            existing = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            locked = await self._repository.lock_dataset(conn, dataset_id, now)
            if not locked:
                raise ConflictError(f"Dataset '{dataset_id}' is already locked")

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=dataset_id,
                    event_type=SandboxAuditEventType.DATASET_LOCKED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, dataset_id)
        return _dataset_response(record)

    # ── clone ─────────────────────────────────────────────────────────

    async def clone_dataset(
        self, *, user_id: str, tenant_key: str, org_id: str, dataset_id: str,
    ) -> DatasetResponse:
        now = utc_now_sql()
        new_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            existing = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )

            new_version = await self._repository.get_next_version_number(
                conn, existing.org_id, existing.dataset_code,
            )
            await self._repository.clone_dataset(
                conn,
                dataset_id,
                new_id=new_id,
                new_version=new_version,
                created_by=user_id,
                now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=new_id,
                    event_type=SandboxAuditEventType.DATASET_CLONED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "source_dataset_id": dataset_id,
                        "version_number": str(new_version),
                    },
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, new_id)
        return _dataset_response(record)

    # ── field overrides ───────────────────────────────────────────────

    async def update_field_overrides(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        dataset_id: str,
        overrides: list[FieldOverrideRequest],
    ) -> DatasetResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            existing = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )

            override_dicts = [o.model_dump() for o in overrides]
            await self._repository.upsert_field_overrides(
                conn, dataset_id, override_dicts, created_by=user_id, now=now,
            )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=dataset_id,
                    event_type=SandboxAuditEventType.DATASET_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"field_overrides_count": str(len(overrides))},
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, dataset_id)
        return _dataset_response(record)

    # ── delete ────────────────────────────────────────────────────────

    async def delete_dataset(
        self, *, user_id: str, tenant_key: str, org_id: str, dataset_id: str,
    ) -> None:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            existing = await self._get_dataset_or_not_found(conn, dataset_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=existing.org_id,
                workspace_id=existing.workspace_id,
            )
            if existing.is_locked:
                raise ConflictError(f"Dataset '{dataset_id}' is locked and cannot be deleted")

            deleted = await self._repository.soft_delete_dataset(
                conn, dataset_id, deleted_by=user_id, now=now,
            )
            if not deleted:
                raise NotFoundError(f"Dataset '{dataset_id}' not found")

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=dataset_id,
                    event_type=SandboxAuditEventType.DATASET_DELETED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(_cache_key(org_id))

    # ── Dataset composition ────────────────────────────────────────────────────

    async def compose_dataset(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: ComposeDatasetRequest,
    ) -> ComposeDatasetResponse:
        """
        Compose a dataset from collected asset properties.

        For each source, fetch properties from 54_dtl_asset_properties,
        group by asset_type_code into a single JSON payload.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")

        composed: dict = {}  # {asset_type_code: [properties_dict, ...]}
        for source in request.sources:
            rows = await self._fetch_source_properties(
                tenant_key=tenant_key,
                org_id=org_id,
                source=source,
            )
            for row in rows:
                asset_type = row.get("asset_type_code") or "unknown"
                props = row.get("properties") or {}
                composed.setdefault(asset_type, []).append(props)

        fingerprint = _compute_schema_fingerprint(composed)

        # Create dataset record
        dataset_id = str(uuid.uuid4())
        slug = _slugify(request.name)
        dataset_code = f"{slug[:50]}_{dataset_id[:8]}"
        now = utc_now_sql()
        row_count = sum(len(v) for v in composed.values())
        if row_count <= 0:
            raise ValidationError("No asset rows matched the selected composition sources.")

        connector_ids = {
            source.connector_instance_id
            for source in request.sources
            if source.connector_instance_id
        }
        dataset_connector_instance_id = next(iter(connector_ids)) if len(connector_ids) == 1 else None
        dataset_payload = json.dumps(composed, separators=(",", ":"))

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
                workspace_id=request.workspace_id,
            )
            version_number = await self._repository.get_next_version_number(
                conn,
                org_id,
                dataset_code,
            )
            await self._repository.create_dataset(
                conn,
                id=dataset_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                connector_instance_id=dataset_connector_instance_id,
                dataset_code=dataset_code,
                dataset_source_code="composite",
                version_number=version_number,
                schema_fingerprint=fingerprint,
                row_count=row_count,
                byte_size=len(dataset_payload.encode()),
                asset_ids=None,
                created_by=user_id,
                now=now,
            )
            props_to_write = {
                "name": request.name,
                "schema_fingerprint": fingerprint,
                "compose_sources_json": json.dumps([s.model_dump() for s in request.sources]),
            }
            if request.description:
                props_to_write["description"] = request.description
            await self._repository.upsert_properties(
                conn,
                dataset_id,
                props_to_write,
                created_by=user_id,
                now=now,
            )
            await self._repository.add_records(
                conn,
                dataset_id=dataset_id,
                records=[dataset_payload],
                source_asset_id=None,
                connector_instance_id=dataset_connector_instance_id,
                start_seq=1,
                now=now,
            )

        await self._cache.delete(_cache_key(org_id))

        # Build preview (first item per type)
        preview = {atype: items[:2] for atype, items in composed.items()}

        return ComposeDatasetResponse(
            dataset_id=dataset_id,
            dataset_code=dataset_code,
            version_number=version_number,
            dataset_source_code="composite",
            schema_fingerprint=fingerprint,
            row_count=row_count,
            record_preview=preview,
        )

    async def _smart_select_samples(
        self,
        *,
        org_id: str,
        connector_instance_id: str,
        samples_per_type: int = 10,
    ) -> tuple[dict[str, list[dict]], str, list[str]]:
        """
        Core smart sampling algorithm. Returns (composed, auto_description, parts).

        For each asset type:
        1. Identifies boolean/enum keys (2-5 distinct values) dynamically.
        2. Groups assets by value combinations.
        3. Guarantees >=1 sample per group, fills rest from largest groups.
        """
        composed: dict[str, list[dict]] = {}
        composition_parts: list[str] = []

        async with self._database_pool.acquire() as conn:
            type_rows = await conn.fetch(
                """
                SELECT a.asset_type_code, COUNT(*) AS cnt
                FROM "15_sandbox"."33_fct_assets" a
                WHERE a.org_id = $1::uuid
                  AND a.connector_instance_id = $2::uuid
                  AND a.is_deleted = FALSE
                GROUP BY a.asset_type_code
                ORDER BY cnt DESC
                """,
                org_id, connector_instance_id,
            )
            if not type_rows:
                raise ValidationError("No assets found for this connector. Run a collection first.")

            for type_row in type_rows:
                asset_type = type_row["asset_type_code"]

                asset_rows = await conn.fetch(
                    """
                    SELECT a.id,
                           a.asset_external_id,
                           jsonb_object_agg(p.property_key, p.property_value) AS properties
                    FROM "15_sandbox"."33_fct_assets" a
                    JOIN "15_sandbox"."54_dtl_asset_properties" p ON p.asset_id = a.id
                    WHERE a.org_id = $1::uuid
                      AND a.connector_instance_id = $2::uuid
                      AND a.asset_type_code = $3
                      AND a.is_deleted = FALSE
                    GROUP BY a.id, a.asset_external_id
                    """,
                    org_id, connector_instance_id, asset_type,
                )
                if not asset_rows:
                    continue

                assets: list[dict] = []
                for r in asset_rows:
                    props = r["properties"]
                    if isinstance(props, str):
                        try:
                            props = json.loads(props)
                        except Exception:
                            props = {}
                    assets.append({
                        "asset_id": str(r["id"]),
                        "external_id": str(r["asset_external_id"]) if r["asset_external_id"] else None,
                        "properties": props,
                    })

                # Identify boolean/enum keys dynamically
                all_keys: set[str] = set()
                for a in assets:
                    all_keys.update(a["properties"].keys())

                diversity_keys: list[str] = []
                key_value_counts: dict[str, dict[str, int]] = {}
                for key in sorted(all_keys):
                    distinct_values: dict[str, int] = {}
                    for a in assets:
                        val = str(a["properties"].get(key, "")).lower()
                        distinct_values[val] = distinct_values.get(val, 0) + 1
                    if 2 <= len(distinct_values) <= 5:
                        diversity_keys.append(key)
                        key_value_counts[key] = distinct_values

                # Group by diversity key combinations
                groups: dict[str, list[dict]] = {}
                for a in assets:
                    gp = []
                    for key in diversity_keys:
                        val = str(a["properties"].get(key, "")).lower()
                        gp.append(f"{key}={val}")
                    group_label = " | ".join(gp) if gp else "all"
                    groups.setdefault(group_label, []).append(a)

                # Sample with diversity guarantee
                selected: list[dict] = []
                remaining = samples_per_type

                for gl in sorted(groups.keys()):
                    if remaining <= 0:
                        break
                    pick = groups[gl][0]
                    selected.append({
                        **pick["properties"],
                        "_asset_type": asset_type,
                        "_external_id": pick["external_id"],
                        "_diversity_group": gl,
                    })
                    remaining -= 1

                if remaining > 0:
                    for gl, ga in sorted(groups.items(), key=lambda x: len(x[1]), reverse=True):
                        if remaining <= 0:
                            break
                        already = {s.get("_external_id") for s in selected}
                        for a in ga[1:]:
                            if remaining <= 0:
                                break
                            if a["external_id"] in already:
                                continue
                            selected.append({
                                **a["properties"],
                                "_asset_type": asset_type,
                                "_external_id": a["external_id"],
                                "_diversity_group": gl,
                            })
                            remaining -= 1

                composed[asset_type] = selected

                summary_details: list[str] = []
                for key in diversity_keys[:3]:
                    counts = key_value_counts[key]
                    parts = [f"{ct} {val}" for val, ct in sorted(counts.items(), key=lambda x: -x[1])]
                    summary_details.append(f"{key}: {', '.join(parts[:3])}")
                detail_str = f" ({'; '.join(summary_details)})" if summary_details else ""
                composition_parts.append(f"{len(selected)} {asset_type}{detail_str}")

        total = sum(len(v) for v in composed.values())
        if total <= 0:
            raise ValidationError("No asset rows matched for smart composition.")

        auto_description = f"Smart sample: {', '.join(composition_parts)}"
        if len(auto_description) > 2000:
            auto_description = auto_description[:1997] + "..."

        return composed, auto_description, composition_parts

    async def smart_preview(
        self,
        *,
        user_id: str,
        org_id: str,
        connector_instance_id: str,
        samples_per_type: int = 10,
    ) -> dict:
        """Return smart-selected samples for preview without creating a dataset."""
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
        composed, summary, parts = await self._smart_select_samples(
            org_id=org_id,
            connector_instance_id=connector_instance_id,
            samples_per_type=samples_per_type,
        )
        # Flatten for preview: list of all records
        all_records = []
        for asset_type, items in composed.items():
            all_records.extend(items)
        return {
            "records": all_records,
            "total": len(all_records),
            "by_type": {k: len(v) for k, v in composed.items()},
            "composition_summary": summary,
            "type_details": parts,
        }

    async def smart_compose_dataset(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        connector_instance_id: str,
        name: str,
        description: str | None = None,
        workspace_id: str | None = None,
        samples_per_type: int = 10,
    ) -> ComposeDatasetResponse:
        """
        Build a diversity-maximising dataset from connector assets.

        For each asset type the algorithm:
        1. Identifies boolean/enum property keys (<=5 distinct values).
        2. Groups assets by their boolean/enum value combinations.
        3. Samples at least 1 asset per group, filling remaining quota from
           the largest groups so edge-case combinations are never dropped.
        4. Tags every record with ``_asset_type``, ``_external_id``, and
           ``_diversity_group`` metadata.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")

        composed, auto_description, _ = await self._smart_select_samples(
            org_id=org_id,
            connector_instance_id=connector_instance_id,
            samples_per_type=samples_per_type,
        )

        # Flatten: each asset becomes an individual JSON record
        all_records: list[dict] = []
        for items in composed.values():
            all_records.extend(items)

        row_count = len(all_records)
        final_description = description or auto_description

        fingerprint = _compute_schema_fingerprint(composed)
        dataset_id = str(uuid.uuid4())
        slug = _slugify(name)
        dataset_code = f"{slug[:50]}_{dataset_id[:8]}"
        now = utc_now_sql()
        record_jsons = [json.dumps(r, separators=(",", ":")) for r in all_records]
        total_bytes = sum(len(r.encode()) for r in record_jsons)

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
                workspace_id=workspace_id,
            )
            version_number = await self._repository.get_next_version_number(
                conn, org_id, dataset_code,
            )
            await self._repository.create_dataset(
                conn,
                id=dataset_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=workspace_id,
                connector_instance_id=connector_instance_id,
                dataset_code=dataset_code,
                dataset_source_code="composite",
                version_number=version_number,
                schema_fingerprint=fingerprint,
                row_count=row_count,
                byte_size=total_bytes,
                asset_ids=None,
                created_by=user_id,
                now=now,
            )
            props_to_write = {
                "name": name,
                "description": final_description,
                "schema_fingerprint": fingerprint,
                "composition_summary": auto_description,
            }
            await self._repository.upsert_properties(
                conn, dataset_id, props_to_write, created_by=user_id, now=now,
            )
            # Store each asset as a separate record — addable later
            await self._repository.add_records(
                conn,
                dataset_id=dataset_id,
                records=record_jsons,
                source_asset_id=None,
                connector_instance_id=connector_instance_id,
                start_seq=1,
                now=now,
            )

        await self._cache.delete(_cache_key(org_id))

        preview = {atype: items[:2] for atype, items in composed.items()}
        return ComposeDatasetResponse(
            dataset_id=dataset_id,
            dataset_code=dataset_code,
            version_number=version_number,
            dataset_source_code="composite",
            schema_fingerprint=fingerprint,
            row_count=row_count,
            record_preview=preview,
        )

    async def _fetch_source_properties(
        self, *, tenant_key: str, org_id: str, source
    ) -> list[dict]:
        """Fetch asset properties for a single source reference."""
        conditions = ["a.tenant_key = $1", "a.org_id = $2::uuid", "a.is_deleted = FALSE"]
        params: list = [tenant_key, org_id]
        idx = 3
        row_limit = source.limit or 1000

        if source.source_type == "asset_snapshot" and source.snapshot_id:
            conditions.append(f"s.id = ${idx}::uuid")
            params.append(source.snapshot_id)
            idx += 1
            if source.asset_type_filter:
                conditions.append(f"a.asset_type_code = ${idx}")
                params.append(source.asset_type_filter)
                idx += 1
            if source.asset_id:
                conditions.append(f"a.id = ${idx}::uuid")
                params.append(source.asset_id)
                idx += 1
            if source.connector_instance_id:
                conditions.append(f"a.connector_instance_id = ${idx}::uuid")
                params.append(source.connector_instance_id)
                idx += 1
            sql = f"""
                SELECT a.asset_type_code,
                       jsonb_object_agg(p.property_key, p.property_value) AS properties
                FROM "15_sandbox"."33_fct_assets" a
                JOIN "15_sandbox"."34_fct_asset_snapshots" s ON s.asset_id = a.id
                JOIN "15_sandbox"."55_dtl_asset_snapshot_properties" p ON p.snapshot_id = s.id
                WHERE {" AND ".join(conditions)}
                GROUP BY a.id, a.asset_type_code
                LIMIT {row_limit}
            """
        elif source.source_type == "asset_snapshot":
            raise ValidationError("snapshot_id is required when source_type is 'asset_snapshot'")
        else:
            if source.connector_instance_id:
                conditions.append(f"a.connector_instance_id = ${idx}::uuid")
                params.append(source.connector_instance_id)
                idx += 1
            if source.asset_type_filter:
                conditions.append(f"a.asset_type_code = ${idx}")
                params.append(source.asset_type_filter)
                idx += 1
            if source.asset_id:
                conditions.append(f"a.id = ${idx}::uuid")
                params.append(source.asset_id)
                idx += 1
            sql = f"""
                SELECT a.asset_type_code,
                       jsonb_object_agg(p.property_key, p.property_value) AS properties
                FROM "15_sandbox"."33_fct_assets" a
                JOIN "15_sandbox"."54_dtl_asset_properties" p ON p.asset_id = a.id
                WHERE {" AND ".join(conditions)}
                GROUP BY a.id, a.asset_type_code
                LIMIT {row_limit}
            """
        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        result = []
        for r in rows:
            props = r["properties"]
            if isinstance(props, str):
                try:
                    props = json.loads(props)
                except Exception:
                    props = {}
            result.append({"asset_type_code": r["asset_type_code"], "properties": props})
        return result

    # ── Record CRUD ────────────────────────────────────────────────────────────

    async def update_record(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        dataset_id: str,
        record_id: str,
        record_data: dict,
    ):
        """Update a single record's JSON data."""
        from .schemas import DatasetDataRecord

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            existing = await self._repository.get_dataset_by_id(conn, dataset_id)
            if existing is None:
                raise NotFoundError(f"Dataset '{dataset_id}' not found")
            if existing.is_locked:
                raise ConflictError(f"Dataset '{dataset_id}' is locked")

            row = await conn.fetchrow(
                """
                UPDATE "15_sandbox"."43_dtl_dataset_records"
                SET record_data = $1::jsonb, recorded_at = now()
                WHERE id = $2::uuid AND dataset_id = $3::uuid
                RETURNING id, dataset_id, record_seq, recorded_at, source_asset_id, connector_instance_id, record_data
                """,
                json.dumps(record_data), record_id, dataset_id,
            )
            if row is None:
                raise NotFoundError(f"Record '{record_id}' not found in dataset '{dataset_id}'")

        rd = row["record_data"]
        if isinstance(rd, str):
            try:
                rd = json.loads(rd)
            except Exception:
                rd = {}

        await self._cache.delete(_cache_key(org_id))
        return DatasetDataRecord(
            id=str(row["id"]),
            dataset_id=str(row["dataset_id"]),
            record_seq=row["record_seq"],
            recorded_at=str(row["recorded_at"]),
            source_asset_id=str(row["source_asset_id"]) if row["source_asset_id"] else None,
            connector_instance_id=str(row["connector_instance_id"]) if row["connector_instance_id"] else None,
            record_data=rd,
        )

    async def delete_record(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        dataset_id: str,
        record_id: str,
    ) -> None:
        """Delete a single record from the dataset."""
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            existing = await self._repository.get_dataset_by_id(conn, dataset_id)
            if existing is None:
                raise NotFoundError(f"Dataset '{dataset_id}' not found")
            if existing.is_locked:
                raise ConflictError(f"Dataset '{dataset_id}' is locked")

            deleted = await conn.execute(
                'DELETE FROM "15_sandbox"."43_dtl_dataset_records" WHERE id = $1::uuid AND dataset_id = $2::uuid',
                record_id, dataset_id,
            )
            if deleted == "DELETE 0":
                raise NotFoundError(f"Record '{record_id}' not found")

            # Update row count
            await conn.execute(
                'UPDATE "15_sandbox"."21_fct_datasets" SET row_count = row_count - 1 WHERE id = $1::uuid',
                dataset_id,
            )

        await self._cache.delete(_cache_key(org_id))

    # ── Record naming ─────────────────────────────────────────────────────

    async def update_record_name(
        self,
        *,
        user_id: str,
        org_id: str,
        dataset_id: str,
        record_id: str,
        record_name: str,
    ):
        """Set a unique short name for a record (used in data sufficiency checks)."""
        from .schemas import DatasetDataRecord

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.create")

            # Check uniqueness within dataset
            existing = await conn.fetchrow(
                """
                SELECT id FROM "15_sandbox"."43_dtl_dataset_records"
                WHERE dataset_id = $1::uuid AND record_name = $2 AND id != $3::uuid
                """,
                dataset_id, record_name, record_id,
            )
            if existing:
                raise ConflictError(f"Record name '{record_name}' already exists in this dataset")

            row = await conn.fetchrow(
                """
                UPDATE "15_sandbox"."43_dtl_dataset_records"
                SET record_name = $1
                WHERE id = $2::uuid AND dataset_id = $3::uuid
                RETURNING id, dataset_id, record_seq, COALESCE(record_name, '') AS record_name,
                          recorded_at::text, source_asset_id::text, connector_instance_id::text,
                          record_data::text AS record_data, COALESCE(description, '') AS description
                """,
                record_name, record_id, dataset_id,
            )
            if row is None:
                raise NotFoundError(f"Record '{record_id}' not found")

        rd = row["record_data"]
        if isinstance(rd, str):
            try:
                rd = json.loads(rd)
            except Exception:
                rd = {}
        if isinstance(rd, str):
            try:
                rd = json.loads(rd)
            except Exception:
                rd = {}

        return DatasetDataRecord(
            id=str(row["id"]),
            dataset_id=str(row["dataset_id"]),
            record_seq=row["record_seq"],
            record_name=row["record_name"],
            recorded_at=row["recorded_at"],
            source_asset_id=row["source_asset_id"],
            connector_instance_id=row["connector_instance_id"],
            record_data=rd if isinstance(rd, dict) else {"_raw": rd},
            description=row["description"],
        )

    # ── Record descriptions ─────────────────────────────────────────────────

    async def update_record_description(
        self,
        *,
        user_id: str,
        org_id: str,
        dataset_id: str,
        record_id: str,
        description: str,
    ):
        """Update the markdown description for a single record."""
        from .schemas import DatasetDataRecord

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            row = await conn.fetchrow(
                """
                UPDATE "15_sandbox"."43_dtl_dataset_records"
                SET description = $1
                WHERE id = $2::uuid AND dataset_id = $3::uuid
                RETURNING id, dataset_id, record_seq, recorded_at::text,
                          source_asset_id::text, connector_instance_id::text,
                          record_data::text AS record_data, COALESCE(description, '') AS description
                """,
                description, record_id, dataset_id,
            )
            if row is None:
                raise NotFoundError(f"Record '{record_id}' not found")

        rd = row["record_data"]
        if isinstance(rd, str):
            try:
                rd = json.loads(rd)
            except Exception:
                rd = {}
        if isinstance(rd, str):
            try:
                rd = json.loads(rd)
            except Exception:
                rd = {}

        return DatasetDataRecord(
            id=str(row["id"]),
            dataset_id=str(row["dataset_id"]),
            record_seq=row["record_seq"],
            recorded_at=row["recorded_at"],
            source_asset_id=row["source_asset_id"],
            connector_instance_id=row["connector_instance_id"],
            record_data=rd if isinstance(rd, dict) else {"_raw": rd},
            description=row["description"],
        )

    async def generate_descriptions(
        self,
        *,
        user_id: str,
        org_id: str,
        dataset_id: str,
        asset_type: str = "",
        connector_type: str = "",
    ) -> dict:
        """
        Start background AI description generation for all records.
        Returns immediately with job status.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            dataset = await self._repository.get_dataset_by_id(conn, dataset_id)
            if dataset is None:
                raise NotFoundError(f"Dataset '{dataset_id}' not found")

        # Check if already running
        existing = DatasetService._generation_jobs.get(dataset_id)
        if existing and existing["status"] == "running":
            return {
                "status": "running",
                "processed": existing["processed"],
                "total": existing["total"],
                "updated": existing["updated"],
                "errors": existing["errors"],
            }

        # Initialize job tracking
        DatasetService._generation_jobs[dataset_id] = {
            "status": "running",
            "processed": 0,
            "total": 0,
            "updated": 0,
            "errors": 0,
            "started_at": str(utc_now_sql()),
        }

        # Launch background task
        asyncio.create_task(
            self._generate_descriptions_background(
                user_id=user_id,
                dataset_id=dataset_id,
                asset_type=asset_type,
                connector_type=connector_type,
            )
        )

        return {"status": "started", "processed": 0, "total": 0, "updated": 0, "errors": 0}

    def get_generation_status(self, dataset_id: str) -> dict:
        """Get the current status of description generation for a dataset."""
        job = DatasetService._generation_jobs.get(dataset_id)
        if not job:
            return {"status": "idle", "processed": 0, "total": 0, "updated": 0, "errors": 0}
        return {
            "status": job["status"],
            "processed": job["processed"],
            "total": job["total"],
            "updated": job["updated"],
            "errors": job["errors"],
        }

    async def get_asset_type_descriptions(self, dataset_id: str) -> dict[str, str]:
        """Return stored asset type descriptions for this dataset."""
        async with self._database_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT property_key, property_value
                FROM "15_sandbox"."42_dtl_dataset_properties"
                WHERE dataset_id = $1::uuid AND property_key LIKE '_ai_desc:%'
                """,
                dataset_id,
            )
        return {
            r["property_key"].replace("_ai_desc:", ""): r["property_value"]
            for r in rows
        }

    async def _generate_descriptions_background(
        self,
        *,
        user_id: str,
        dataset_id: str,
        asset_type: str = "",
        connector_type: str = "",
    ) -> None:
        """Background task: generate one AI description per asset type (not per record)."""
        job = DatasetService._generation_jobs[dataset_id]
        try:
            _agent_service_mod = import_module("backend.20_ai.27_dataset_agent.service")
            agent = _agent_service_mod.DatasetAgentService(
                database_pool=self._database_pool,
                settings=self._settings,
            )

            # Find distinct asset types in this dataset
            # Note: record_data may be double-encoded (JSON string inside JSONB)
            async with self._database_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT asset_type, COUNT(*) AS cnt FROM (
                        SELECT COALESCE(
                            record_data->>'_asset_type',
                            (record_data #>> '{}')::jsonb->>'_asset_type'
                        ) AS asset_type
                        FROM "15_sandbox"."43_dtl_dataset_records"
                        WHERE dataset_id = $1::uuid
                    ) sub
                    GROUP BY asset_type
                    """,
                    dataset_id,
                )
                # Check which types already have descriptions
                existing = await conn.fetch(
                    """
                    SELECT property_key FROM "15_sandbox"."42_dtl_dataset_properties"
                    WHERE dataset_id = $1::uuid AND property_key LIKE '_ai_desc:%'
                    """,
                    dataset_id,
                )

            existing_types = {r["property_key"].replace("_ai_desc:", "") for r in existing}
            types_to_describe = [
                (r["asset_type"] or "unknown", r["cnt"])
                for r in rows
                if (r["asset_type"] or "unknown") not in existing_types
            ]

            job["total"] = len(types_to_describe)
            if job["total"] == 0:
                job["status"] = "completed"
                return

            for type_code, count in types_to_describe:
                try:
                    # Get ALL records for this type (up to 20) so AI sees full variety
                    async with self._database_pool.acquire() as conn:
                        samples = await conn.fetch(
                            """
                            SELECT record_data FROM "15_sandbox"."43_dtl_dataset_records"
                            WHERE dataset_id = $1::uuid
                              AND COALESCE(
                                  record_data->>'_asset_type',
                                  (record_data #>> '{}')::jsonb->>'_asset_type'
                              ) = $2
                            LIMIT 20
                            """,
                            dataset_id, type_code,
                        )

                    all_records = []
                    for sample in samples:
                        rd = sample["record_data"]
                        if isinstance(rd, str):
                            try:
                                rd = json.loads(rd)
                            except Exception:
                                rd = {}
                        if isinstance(rd, str):
                            try:
                                rd = json.loads(rd)
                            except Exception:
                                rd = {}
                        if isinstance(rd, dict):
                            all_records.append(rd)

                    # Build a combined payload showing all records for this type
                    combined_data = {
                        "_asset_type": type_code,
                        "_record_count": count,
                        "_sample_count": len(all_records),
                        "_records": all_records,
                    }

                    explanation = await agent.explain_record(
                        user_id=user_id,
                        record_data=combined_data,
                        asset_type_hint=type_code or asset_type,
                        connector_type=connector_type,
                    )

                    md_parts = [f"## {type_code.replace('_', ' ').title()} ({count} records)\n"]
                    summary = explanation.get("record_summary", "")
                    if summary:
                        md_parts.append(f"{summary}\n")

                    fields = explanation.get("fields", [])
                    if fields:
                        md_parts.append("### Key Fields\n")
                        for f in fields:
                            relevance = f.get("compliance_relevance", "")
                            desc = f.get("description", "")
                            line = f"- **{f['field_name']}** ({f.get('data_type', '?')}) — {desc}"
                            if relevance in ("high", "medium"):
                                line += f" ⚠️ *{relevance} compliance relevance*"
                            md_parts.append(line)

                    signals = explanation.get("recommended_signals", [])
                    if signals:
                        md_parts.append("\n### Recommended Signals\n")
                        for s in signals:
                            md_parts.append(f"- **{s['signal_name']}**: {s.get('description', '')}")

                    description_md = "\n".join(md_parts)

                    # Store as dataset property: _ai_desc:{asset_type}
                    async with self._database_pool.acquire() as conn:
                        await conn.execute(
                            """
                            INSERT INTO "15_sandbox"."42_dtl_dataset_properties"
                                (id, dataset_id, property_key, property_value)
                            VALUES (gen_random_uuid(), $1::uuid, $2, $3)
                            ON CONFLICT (dataset_id, property_key)
                            DO UPDATE SET property_value = EXCLUDED.property_value
                            """,
                            dataset_id, f"_ai_desc:{type_code}", description_md,
                        )
                    job["updated"] += 1

                except Exception as exc:
                    self._logger.warning(
                        "generate_descriptions: failed for asset type %s: %s", type_code, exc
                    )
                    job["errors"] += 1

                job["processed"] += 1

            job["status"] = "completed"
        except Exception as exc:
            self._logger.error("generate_descriptions background task failed: %s", exc)
            job["status"] = "failed"
            job["error_message"] = str(exc)

    # ── Versioning ────────────────────────────────────────────────────────────

    async def create_version(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        dataset_id: str,
        description: str | None = None,
    ) -> DatasetResponse:
        """
        Snapshot current dataset as a new immutable version.
        Creates a new dataset row with version_number+1, copies all records, locks the old version.
        """
        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            existing = await self._repository.get_dataset_by_id(conn, dataset_id)
            if existing is None:
                raise NotFoundError(f"Dataset '{dataset_id}' not found")

            # Lock the current version
            if not existing.is_locked:
                await conn.execute(
                    'UPDATE "15_sandbox"."21_fct_datasets" SET is_locked = true, updated_at = now() WHERE id = $1::uuid',
                    dataset_id,
                )

            # Create new version
            new_id = str(uuid.uuid4())
            new_version = existing.version_number + 1
            await conn.execute(
                """
                INSERT INTO "15_sandbox"."21_fct_datasets"
                    (id, tenant_key, org_id, workspace_id, connector_instance_id,
                     dataset_code, dataset_source_code, version_number,
                     schema_fingerprint, row_count, byte_size,
                     is_locked, is_active, created_by)
                SELECT $1::uuid, tenant_key, org_id, workspace_id, connector_instance_id,
                       dataset_code, dataset_source_code, $2,
                       schema_fingerprint, row_count, byte_size,
                       false, true, $3::uuid
                FROM "15_sandbox"."21_fct_datasets" WHERE id = $4::uuid
                """,
                new_id, new_version, user_id, dataset_id,
            )

            # Copy all records to new version
            await conn.execute(
                """
                INSERT INTO "15_sandbox"."43_dtl_dataset_records"
                    (id, dataset_id, record_seq, recorded_at, source_asset_id,
                     connector_instance_id, record_data)
                SELECT gen_random_uuid(), $1::uuid, record_seq, recorded_at,
                       source_asset_id, connector_instance_id, record_data
                FROM "15_sandbox"."43_dtl_dataset_records"
                WHERE dataset_id = $2::uuid
                ORDER BY record_seq
                """,
                new_id, dataset_id,
            )

            # Copy properties (generate new UUIDs for id column)
            await conn.execute(
                """
                INSERT INTO "15_sandbox"."42_dtl_dataset_properties"
                    (id, dataset_id, property_key, property_value)
                SELECT gen_random_uuid(), $1::uuid, property_key, property_value
                FROM "15_sandbox"."42_dtl_dataset_properties"
                WHERE dataset_id = $2::uuid
                ON CONFLICT DO NOTHING
                """,
                new_id, dataset_id,
            )

            if description:
                await conn.execute(
                    """
                    INSERT INTO "15_sandbox"."42_dtl_dataset_properties"
                        (id, dataset_id, property_key, property_value)
                    VALUES (gen_random_uuid(), $1::uuid, 'version_description', $2)
                    ON CONFLICT (dataset_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                    """,
                    new_id, description,
                )

            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="dataset",
                    entity_id=new_id,
                    event_type=SandboxAuditEventType.DATASET_CREATED.value,
                    event_category="sandbox",
                    occurred_at=utc_now_sql(),
                    actor_id=user_id,
                    actor_type="user",
                    properties={"action": "version_created", "version": str(new_version), "from_dataset_id": dataset_id},
                ),
            )

        await self._cache.delete(_cache_key(org_id))

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_dataset_by_id(conn, new_id)
        return _dataset_response(record)

    async def list_versions(
        self,
        *,
        user_id: str,
        org_id: str,
        dataset_id: str,
    ):
        """List all versions of a dataset (by dataset_code)."""
        from .schemas import DatasetVersionResponse, DatasetVersionListResponse

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            existing = await self._repository.get_dataset_by_id(conn, dataset_id)
            if existing is None:
                raise NotFoundError(f"Dataset '{dataset_id}' not found")

            rows = await conn.fetch(
                """
                SELECT d.id, d.version_number, d.row_count, d.schema_fingerprint,
                       d.is_locked, d.created_at,
                       p.property_value AS description
                FROM "15_sandbox"."21_fct_datasets" d
                LEFT JOIN "15_sandbox"."42_dtl_dataset_properties" p
                    ON p.dataset_id = d.id AND p.property_key = 'version_description'
                WHERE d.dataset_code = $1 AND d.org_id = $2::uuid AND d.is_active = true
                ORDER BY d.version_number DESC
                """,
                existing.dataset_code, org_id,
            )

        versions = [
            DatasetVersionResponse(
                version_number=r["version_number"],
                record_count=r["row_count"],
                schema_fingerprint=r["schema_fingerprint"],
                created_at=str(r["created_at"]),
                description=r["description"],
                is_current=(str(r["id"]) == dataset_id),
            )
            for r in rows
        ]

        return DatasetVersionListResponse(
            dataset_code=existing.dataset_code,
            versions=versions,
        )

    # ── Schema drift ───────────────────────────────────────────────────────────

    async def check_schema_drift(
        self,
        *,
        user_id: str,
        dataset_id: str,
        org_id: str,
        tenant_key: str,
    ) -> SchemaDriftResponse:
        """
        Compare the dataset's stored schema fingerprint against what would
        be composed NOW from the same sources.
        """
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")

            # Load dataset + stored sources
            props_rows = await conn.fetch(
                """
                SELECT property_key, property_value
                FROM "15_sandbox"."42_dtl_dataset_properties"
                WHERE dataset_id = $1::uuid
                  AND property_key IN ('schema_fingerprint', 'compose_sources_json')
                """,
                dataset_id,
            )

        props = {r["property_key"]: r["property_value"] for r in props_rows}
        original_fingerprint = props.get("schema_fingerprint")
        sources_json = props.get("compose_sources_json")

        if not sources_json:
            return SchemaDriftResponse(
                dataset_id=dataset_id,
                has_drift=False,
                original_fingerprint=original_fingerprint,
                current_fingerprint=original_fingerprint,
                changes={"added_fields": [], "removed_fields": [], "type_changes": []},
                recommendation="Dataset was not composed from asset properties — drift detection not available.",
            )

        try:
            from .schemas import DatasetSourceRef
            sources = [DatasetSourceRef(**s) for s in json.loads(sources_json)]
        except Exception:
            return SchemaDriftResponse(
                dataset_id=dataset_id,
                has_drift=False,
                original_fingerprint=original_fingerprint,
                current_fingerprint=None,
                changes={"added_fields": [], "removed_fields": [], "type_changes": []},
                recommendation="Could not parse stored sources for drift comparison.",
            )

        # Re-compose current data
        current_composed: dict = {}
        for source in sources:
            rows = await self._fetch_source_properties(
                tenant_key=tenant_key, org_id=org_id, source=source,
            )
            for row in rows:
                asset_type = row.get("asset_type_code") or "unknown"
                props_data = row.get("properties") or {}
                current_composed.setdefault(asset_type, []).append(props_data)

        current_fingerprint = _compute_schema_fingerprint(current_composed)
        has_drift = current_fingerprint != original_fingerprint

        # Compute field-level changes
        changes = _compute_schema_changes(original_fingerprint, current_composed)

        recommendation = (
            "Dataset schema has changed. Create a new version to update signal specs."
            if has_drift
            else "No schema drift detected."
        )

        return SchemaDriftResponse(
            dataset_id=dataset_id,
            has_drift=has_drift,
            original_fingerprint=original_fingerprint,
            current_fingerprint=current_fingerprint,
            changes=changes,
            recommendation=recommendation,
        )

    # ── Asset type discovery + sample preview ─────────────────────────

    async def get_connector_asset_types(
        self,
        *,
        user_id: str,
        org_id: str,
        connector_instance_id: str,
    ):
        """Discover asset types available for a connector with counts and sample property keys."""
        from .schemas import AssetTypeInfo, ConnectorAssetTypesResponse

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")

            connector = await conn.fetchrow(
                """
                SELECT ci.id, p.property_value AS name, ci.connector_type_code
                FROM "15_sandbox"."20_fct_connector_instances" ci
                LEFT JOIN "15_sandbox"."40_dtl_connector_instance_properties" p
                    ON p.connector_instance_id = ci.id AND p.property_key = 'name'
                WHERE ci.id = $1::uuid AND ci.org_id = $2::uuid
                """,
                connector_instance_id, org_id,
            )
            connector_name = connector["name"] if connector else None
            provider_code = connector["connector_type_code"] if connector else None

            try:
                rows = await conn.fetch(
                    """
                    SELECT a.asset_type_code,
                           COUNT(*) AS asset_count,
                           array_agg(DISTINCT p.property_key ORDER BY p.property_key)
                               FILTER (WHERE p.property_key IS NOT NULL) AS property_keys
                    FROM "15_sandbox"."33_fct_assets" a
                    LEFT JOIN "15_sandbox"."54_dtl_asset_properties" p ON p.asset_id = a.id
                    WHERE a.org_id = $1::uuid
                      AND a.connector_instance_id = $2::uuid
                      AND a.is_deleted = FALSE
                    GROUP BY a.asset_type_code
                    ORDER BY asset_count DESC
                    """,
                    org_id, connector_instance_id,
                )
            except Exception:
                rows = []

        asset_types = []
        for r in rows:
            keys = r["property_keys"] or []
            asset_types.append(AssetTypeInfo(
                asset_type_code=r["asset_type_code"],
                asset_count=r["asset_count"],
                sample_property_keys=list(keys)[:30],
            ))

        return ConnectorAssetTypesResponse(
            connector_instance_id=connector_instance_id,
            connector_name=connector_name,
            provider_code=provider_code,
            asset_types=asset_types,
        )

    async def get_asset_samples(
        self,
        *,
        user_id: str,
        org_id: str,
        connector_instance_id: str,
        asset_type_code: str,
        limit: int = 5,
    ):
        """Preview sample asset records for a connector + asset type."""
        from .schemas import AssetSampleRecord, AssetSamplesResponse

        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")

            try:
                count_row = await conn.fetchrow(
                    """
                    SELECT COUNT(*) AS cnt
                    FROM "15_sandbox"."33_fct_assets"
                    WHERE org_id = $1::uuid
                      AND connector_instance_id = $2::uuid
                      AND asset_type_code = $3
                      AND is_deleted = FALSE
                    """,
                    org_id, connector_instance_id, asset_type_code,
                )
                total_count = count_row["cnt"] if count_row else 0

                rows = await conn.fetch(
                    """
                    SELECT a.id AS asset_id,
                           a.asset_external_id,
                           jsonb_object_agg(p.property_key, p.property_value) AS properties
                    FROM "15_sandbox"."33_fct_assets" a
                    JOIN "15_sandbox"."54_dtl_asset_properties" p ON p.asset_id = a.id
                    WHERE a.org_id = $1::uuid
                      AND a.connector_instance_id = $2::uuid
                      AND a.asset_type_code = $3
                      AND a.is_deleted = FALSE
                    GROUP BY a.id, a.asset_external_id
                    LIMIT $4
                    """,
                    org_id, connector_instance_id, asset_type_code, limit,
                )
            except Exception:
                total_count = 0
                rows = []

        all_keys: set[str] = set()
        samples = []
        for r in rows:
            props = r["properties"]
            if isinstance(props, str):
                try:
                    props = json.loads(props)
                except Exception:
                    props = {}
            all_keys.update(props.keys())
            samples.append(AssetSampleRecord(
                asset_id=str(r["asset_id"]),
                asset_external_id=r["asset_external_id"],
                properties=props,
            ))

        return AssetSamplesResponse(
            connector_instance_id=connector_instance_id,
            asset_type_code=asset_type_code,
            total_count=total_count,
            property_keys=sorted(all_keys),
            samples=samples,
        )


def _compute_schema_changes(original_fingerprint: str | None, current_composed: dict) -> dict:
    """Compute added/removed/changed fields between original and current."""
    # Extract flat field paths from current data
    def _extract_paths(obj, prefix="") -> dict[str, str]:
        paths = {}
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f"{prefix}.{k}" if prefix else k
                paths[path] = type(v).__name__
                paths.update(_extract_paths(v, path))
        elif isinstance(obj, list) and obj:
            paths.update(_extract_paths(obj[0], f"{prefix}[]"))
        return paths

    current_paths: dict[str, str] = {}
    for asset_type, items in current_composed.items():
        for item in items[:3]:
            current_paths.update(_extract_paths(item, asset_type))

    # Without original data we can only report current structure
    return {
        "added_fields": [],
        "removed_fields": [],
        "type_changes": [],
        "current_field_count": len(current_paths),
    }


def _dataset_response(r) -> DatasetResponse:
    return DatasetResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        connector_instance_id=r.connector_instance_id,
        dataset_code=r.dataset_code,
        dataset_source_code=r.dataset_source_code,
        version_number=r.version_number,
        schema_fingerprint=r.schema_fingerprint,
        row_count=r.row_count,
        byte_size=r.byte_size,
        collected_at=r.collected_at,
        is_locked=r.is_locked,
        is_active=r.is_active,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
        asset_ids=r.asset_ids,
    )
