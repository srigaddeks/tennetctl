from __future__ import annotations

import asyncio
import hashlib
import json
import os
import uuid
from importlib import import_module


def _compute_fingerprint(properties: dict[str, str]) -> str:
    return hashlib.sha256(json.dumps(sorted(properties.keys())).encode()).hexdigest()[
        :16
    ]


from .repository import CollectionRunRepository
from .schemas import CollectionRunListResponse, CollectionRunResponse

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_time_module = import_module("backend.01_core.time_utils")
_constants_module = import_module("backend.10_sandbox.constants")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
utc_now_sql = _time_module.utc_now_sql
require_permission = _perm_check_module.require_permission

_CACHE_KEY_PREFIX = "sb:collection_runs"
_CACHE_TTL = 60  # Short TTL — run status changes frequently


@instrument_class_methods(
    namespace="sandbox.collection_runs.service",
    logger_name="backend.sandbox.collection_runs.instrumentation",
)
class CollectionRunService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = CollectionRunRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.collection_runs")

    async def trigger_collection(
        self,
        *,
        user_id: str,
        connector_instance_id: str,
        org_id: str,
        tenant_key: str,
        triggered_by: str | None,
        asset_types: list[str] | None = None,
    ) -> CollectionRunResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            # Verify the connector exists and belongs to this org
            row = await conn.fetchrow(
                """
                SELECT id::text, tenant_key, org_id::text,
                       instance_code, connector_type_code,
                       is_active, is_deleted
                FROM "15_sandbox"."20_fct_connector_instances"
                WHERE id = $1 AND org_id = $2 AND is_deleted = FALSE
                """,
                connector_instance_id,
                org_id,
            )
            if row is None:
                raise NotFoundError(
                    f"Connector instance '{connector_instance_id}' not found"
                )

            run = await self._repository.create_run(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                connector_instance_id=connector_instance_id,
                trigger_type="manual",
                triggered_by=triggered_by,
            )

            now = utc_now_sql()
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="collection_run",
                    entity_id=run.id,
                    event_type=SandboxAuditEventType.COLLECTION_STARTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "connector_instance_id": connector_instance_id,
                        "trigger_type": "manual",
                    },
                ),
            )

        # Kick off the background collection outside the DB transaction
        asyncio.create_task(
            self._run_collection_task(
                run_id=run.id,
                connector_instance_id=connector_instance_id,
                org_id=org_id,
                tenant_key=tenant_key,
                triggered_by=triggered_by,
                asset_types=asset_types,
            )
        )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return _run_response(run)

    async def list_runs(
        self,
        *,
        user_id: str,
        org_id: str,
        connector_id: str | None = None,
        status: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> CollectionRunListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(
                conn,
                user_id,
                "sandbox.view",
                scope_org_id=org_id,
            )
            records, total = await self._repository.list_runs(
                conn,
                org_id=org_id,
                connector_id=connector_id,
                status=status,
                offset=offset,
                limit=limit,
            )
        items = [_run_response(r) for r in records]
        return CollectionRunListResponse(items=items, total=total)

    async def get_run(
        self,
        *,
        user_id: str,
        run_id: str,
        org_id: str,
    ) -> CollectionRunResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            record = await self._repository.get_run(conn, run_id, org_id)
        if record is None:
            raise NotFoundError(f"Collection run '{run_id}' not found")
        return _run_response(record)

    async def cancel_run(
        self,
        *,
        user_id: str,
        run_id: str,
        org_id: str,
    ) -> CollectionRunResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            cancelled = await self._repository.cancel_run(conn, run_id, org_id)
            if not cancelled:
                # Either not found or already in a terminal state — fetch to disambiguate
                record = await self._repository.get_run(conn, run_id, org_id)
                if record is None:
                    raise NotFoundError(f"Collection run '{run_id}' not found")
                raise ConflictError(
                    f"Collection run '{run_id}' cannot be cancelled "
                    f"(current status: {record.status})"
                )
            record = await self._repository.get_run(conn, run_id, org_id)

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")
        return _run_response(record)

    async def list_run_snapshots(
        self,
        *,
        user_id: str,
        run_id: str,
        org_id: str,
        asset_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            # Verify run exists
            run = await self._repository.get_run(conn, run_id, org_id)
            if run is None:
                raise NotFoundError(f"Collection run '{run_id}' not found")

            # Query snapshots with asset info and properties
            type_filter = ""
            params: list = [run_id, limit, offset]
            if asset_type:
                type_filter = "AND a.asset_type_code = $4"
                params.append(asset_type)

            rows = await conn.fetch(
                f"""
                SELECT s.id as snapshot_id, s.asset_id, s.snapshot_number,
                       s.property_count, s.collected_at::text,
                       a.asset_type_code, a.asset_external_id, a.status_code,
                       COUNT(*) OVER() as _total
                FROM "15_sandbox"."34_fct_asset_snapshots" s
                JOIN "15_sandbox"."33_fct_assets" a ON a.id = s.asset_id
                WHERE s.collection_run_id = $1 {type_filter}
                ORDER BY a.asset_type_code, a.asset_external_id
                LIMIT $2 OFFSET $3
                """,
                *params,
            )
            total = rows[0]["_total"] if rows else 0

            # Get properties for each snapshot
            snapshot_ids = [str(r["snapshot_id"]) for r in rows]
            props_map: dict[str, dict[str, str]] = {}
            if snapshot_ids:
                prop_rows = await conn.fetch(
                    """
                    SELECT snapshot_id::text, property_key, property_value
                    FROM "15_sandbox"."55_dtl_asset_snapshot_properties"
                    WHERE snapshot_id = ANY($1::uuid[])
                    ORDER BY snapshot_id, property_key
                    """,
                    snapshot_ids,
                )
                for pr in prop_rows:
                    sid = pr["snapshot_id"]
                    if sid not in props_map:
                        props_map[sid] = {}
                    props_map[sid][pr["property_key"]] = pr["property_value"]

            # Get asset type summary
            type_rows = await conn.fetch(
                """
                SELECT a.asset_type_code, COUNT(*) as count
                FROM "15_sandbox"."34_fct_asset_snapshots" s
                JOIN "15_sandbox"."33_fct_assets" a ON a.id = s.asset_id
                WHERE s.collection_run_id = $1
                GROUP BY a.asset_type_code
                ORDER BY count DESC
                """,
                run_id,
            )

            items = []
            for r in rows:
                sid = str(r["snapshot_id"])
                items.append(
                    {
                        "snapshot_id": sid,
                        "asset_id": str(r["asset_id"]),
                        "asset_type_code": r["asset_type_code"],
                        "asset_external_id": r["asset_external_id"],
                        "status_code": r["status_code"],
                        "snapshot_number": r["snapshot_number"],
                        "property_count": r["property_count"],
                        "collected_at": r["collected_at"],
                        "properties": props_map.get(sid, {}),
                    }
                )

            return {
                "items": items,
                "total": total,
                "asset_type_summary": {
                    r["asset_type_code"]: r["count"] for r in type_rows
                },
            }

    # ------------------------------------------------------------------
    # Background collection task
    # ------------------------------------------------------------------

    async def _run_collection_task(
        self,
        *,
        run_id: str,
        connector_instance_id: str,
        org_id: str,
        tenant_key: str,
        triggered_by: str | None,
        asset_types: list[str] | None,
    ) -> None:
        logger = self._logger

        try:
            async with self._database_pool.acquire() as conn:
                await self._repository.set_run_started(conn, run_id)

            # ----------------------------------------------------------
            # 1. Load connector instance + provider definition
            # ----------------------------------------------------------
            async with self._database_pool.acquire() as conn:
                connector_row = await conn.fetchrow(
                    """
                    SELECT
                        id::text,
                        org_id::text,
                        instance_code,
                        connector_type_code,
                        provider_definition_code
                    FROM "15_sandbox"."20_fct_connector_instances"
                    WHERE id = $1 AND is_deleted = FALSE
                    """,
                    connector_instance_id,
                )
                if connector_row is None:
                    raise RuntimeError(
                        f"Connector '{connector_instance_id}' disappeared during collection"
                    )

                provider_code: str = (
                    connector_row["provider_definition_code"]
                    or connector_row["connector_type_code"]
                    or ""
                )
                if not provider_code:
                    raise RuntimeError(
                        f"Connector '{connector_instance_id}' has no provider code set"
                    )

                # ----------------------------------------------------------
                # 2. Resolve and decrypt credentials
                # ----------------------------------------------------------
                cred_rows = await conn.fetch(
                    """
                    SELECT credential_key, encrypted_value, encryption_key_id
                    FROM "15_sandbox"."41_dtl_connector_credentials"
                    WHERE connector_instance_id = $1
                    """,
                    connector_instance_id,
                )

            # Decrypt credentials outside the connection to avoid holding it
            credentials: dict[str, str] = {}
            if cred_rows:
                _crypto_module = import_module(
                    "backend.10_sandbox.02_connectors.crypto"
                )
                _settings_module = import_module("backend.00_config.settings")
                parse_encryption_key = _crypto_module.parse_encryption_key
                decrypt_value = _crypto_module.decrypt_value
                enc_key = parse_encryption_key(
                    self._settings.sandbox_encryption_key or ""
                )
                for cred_row in cred_rows:
                    try:
                        credentials[cred_row["credential_key"]] = decrypt_value(
                            cred_row["encrypted_value"], enc_key
                        )
                    except Exception as exc:
                        logger.warning(
                            "Failed to decrypt credential key '%s' for connector '%s': %s",
                            cred_row["credential_key"],
                            connector_instance_id,
                            exc,
                        )

            # ----------------------------------------------------------
            # 3. Build ConnectionConfig and run collection via Steampipe
            # ----------------------------------------------------------
            _substrate_base = import_module("backend.10_sandbox.19_steampipe.base")
            ConnectionConfig = _substrate_base.ConnectionConfig

            # Load non-credential connection_config JSONB + EAV properties from connector instance
            async with self._database_pool.acquire() as conn:
                config_row = await conn.fetchrow(
                    """
                    SELECT connection_config
                    FROM "15_sandbox"."20_fct_connector_instances"
                    WHERE id = $1
                    """,
                    connector_instance_id,
                )
                prop_rows = await conn.fetch(
                    """
                    SELECT property_key, property_value
                    FROM "15_sandbox"."40_dtl_connector_instance_properties"
                    WHERE connector_instance_id = $1
                    """,
                    connector_instance_id,
                )
            raw_config: dict = {}
            if config_row and config_row["connection_config"]:
                raw_config = dict(config_row["connection_config"])
            # Merge EAV properties (e.g. org_name, base_url) into config
            for prop in prop_rows:
                key = prop["property_key"]
                if key not in ("name", "description"):  # skip display-only props
                    raw_config.setdefault(key, prop["property_value"])

            connection_config = ConnectionConfig(
                connector_instance_id=connector_instance_id,
                provider_code=provider_code,
                provider_version_code=None,
                config=raw_config,
                credentials=credentials,
            )

            # Determine the API version used for this collection
            async with self._database_pool.acquire() as conn:
                prov_row = await conn.fetchrow(
                    'SELECT current_api_version FROM "15_sandbox"."16_dim_provider_definitions"'
                    " WHERE code = $1",
                    provider_code,
                )
            api_version: str | None = (
                prov_row["current_api_version"] if prov_row else None
            )
            if connection_config.provider_version_code:
                api_version = connection_config.provider_version_code

            # Use Steampipe for all asset collection
            _steampipe_module = import_module(
                "backend.10_sandbox.19_steampipe.steampipe"
            )
            SteampipeSubstrate = _steampipe_module.SteampipeSubstrate
            import shutil as _shutil

            steampipe_binary = _shutil.which("steampipe") or os.path.expanduser(
                "~/bin/steampipe"
            )

            if not os.path.isfile(steampipe_binary):
                raise RuntimeError(
                    f"Steampipe binary not found at '{steampipe_binary}'. "
                    "Install Steampipe: https://steampipe.io/downloads"
                )

            substrate = SteampipeSubstrate(
                binary_path=steampipe_binary,
                query_timeout_seconds=120,
            )
            if not substrate.supports_provider(provider_code):
                raise RuntimeError(
                    f"Steampipe does not support provider '{provider_code}'. "
                    "Install the plugin: steampipe plugin install {provider_code}"
                )

            logger.info(
                "collection_using_steampipe",
                extra={
                    "connector": connector_instance_id,
                    "provider": provider_code,
                },
            )
            collect_result = await substrate.collect_assets(
                connection_config,
                asset_types=asset_types,
            )

            # ----------------------------------------------------------
            # 4. Upsert discovered assets, properties, snapshots
            # ----------------------------------------------------------
            assets_discovered = 0
            assets_updated = 0
            logs_ingested = 0

            _asset_repo_module = import_module(
                "backend.10_sandbox.14_assets.repository"
            )
            AssetRepository = _asset_repo_module.AssetRepository
            asset_repo = AssetRepository()

            async with self._database_pool.acquire() as conn:
                for collected in collect_result.assets:
                    asset = await asset_repo.upsert_asset(
                        conn,
                        tenant_key=tenant_key,
                        org_id=org_id,
                        workspace_id=None,
                        connector_instance_id=connector_instance_id,
                        provider_code=provider_code,
                        asset_type_code=collected.asset_type_code,
                        asset_external_id=collected.external_id,
                        parent_asset_id=None,
                        created_by=triggered_by or "system",
                    )
                    is_new = asset.last_collected_at is None
                    assets_discovered += 1 if is_new else 0
                    assets_updated += 0 if is_new else 1

                    # Upsert current properties (overwritten each run)
                    str_props = {
                        k: str(v)
                        for k, v in (collected.properties or {}).items()
                        if v is not None
                    }
                    if str_props:
                        await asset_repo.upsert_asset_properties(
                            conn, asset.id, str_props
                        )

                    # Create a snapshot for every collection run so data is
                    # accessible per-run.  The fingerprint still tracks whether
                    # the underlying properties actually changed.
                    existing = await asset_repo.get_snapshots(conn, asset.id, limit=1)
                    new_fingerprint = _compute_fingerprint(str_props)
                    snapshot_number = (
                        (existing[0].snapshot_number + 1) if existing else 1
                    )
                    snapshot = await asset_repo.create_snapshot(
                        conn,
                        asset_id=asset.id,
                        collection_run_id=run_id,
                        snapshot_number=snapshot_number,
                        schema_fingerprint=new_fingerprint,
                        properties=str_props,
                    )
                    # Point asset at latest snapshot
                    await asset_repo.set_current_snapshot(conn, asset.id, snapshot.id)

                    # Stamp last_collected_at and asset_api_version
                    await conn.execute(
                        'UPDATE "15_sandbox"."33_fct_assets"'
                        " SET last_collected_at = NOW(),"
                        "     asset_api_version = $2,"
                        "     updated_at = NOW()"
                        " WHERE id = $1",
                        asset.id,
                        api_version,
                    )

                    # Audit per-asset discovery / update
                    audit_event = (
                        SandboxAuditEventType.ASSET_DISCOVERED
                        if is_new
                        else SandboxAuditEventType.ASSET_UPDATED
                    )
                    await self._audit_writer.write_entry(
                        conn,
                        AuditEntry(
                            id=str(uuid.uuid4()),
                            tenant_key=tenant_key,
                            entity_type="asset",
                            entity_id=asset.id,
                            event_type=audit_event.value,
                            event_category="asset_inventory",
                            occurred_at=utc_now_sql(),
                            actor_id=triggered_by or "system",
                            actor_type="system",
                            properties={
                                "asset_type": collected.asset_type_code,
                                "external_id": collected.external_id,
                                "collection_run_id": run_id,
                                "provider_code": provider_code,
                            },
                        ),
                    )

            # ----------------------------------------------------------
            # 5. Update connector health — success resets failures
            # ----------------------------------------------------------
            _ac_repo_module = import_module(
                "backend.10_sandbox.17_asset_connectors.repository"
            )
            ac_repo = _ac_repo_module.AssetConnectorRepository()
            async with self._database_pool.acquire() as conn:
                await ac_repo.update_health(
                    conn,
                    connector_instance_id,
                    health_status="healthy",
                    consecutive_failures=0,
                    last_collected_at=utc_now_sql(),
                )

            # ----------------------------------------------------------
            # 6. Mark run completed
            # ----------------------------------------------------------
            async with self._database_pool.acquire() as conn:
                await self._repository.set_run_completed(
                    conn,
                    run_id,
                    status="completed" if not collect_result.errors else "partial",
                    assets_discovered=assets_discovered,
                    assets_updated=assets_updated,
                    assets_deleted=0,
                    logs_ingested=0,
                )
                await self._audit_writer.write_entry(
                    conn,
                    AuditEntry(
                        id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        entity_type="collection_run",
                        entity_id=run_id,
                        event_type=SandboxAuditEventType.COLLECTION_COMPLETED.value,
                        event_category="asset_inventory",
                        occurred_at=utc_now_sql(),
                        actor_id=triggered_by or "system",
                        actor_type="user" if triggered_by else "system",
                        properties={
                            "assets_discovered": str(assets_discovered),
                            "assets_updated": str(assets_updated),
                            "api_version": api_version or "",
                        },
                    ),
                )

            # ----------------------------------------------------------
            # 7. Auto-run control tests linked to this connector
            # ----------------------------------------------------------
            try:
                await self._auto_run_control_tests(
                    connector_instance_id=connector_instance_id,
                    org_id=org_id,
                    tenant_key=tenant_key,
                    triggered_by=triggered_by,
                    collection_run_id=run_id,
                )
            except Exception as auto_run_exc:
                logger.error(
                    "Auto-run control tests failed for connector '%s': %s",
                    connector_instance_id,
                    auto_run_exc,
                    exc_info=True,
                )

        except Exception as exc:
            logger.error(
                "Collection run '%s' failed for connector '%s': %s",
                run_id,
                connector_instance_id,
                exc,
                exc_info=True,
            )
            is_auth_error = "401" in str(exc) or "auth" in str(exc).lower()
            try:
                _ac_repo_module = import_module(
                    "backend.10_sandbox.17_asset_connectors.repository"
                )
                ac_repo = _ac_repo_module.AssetConnectorRepository()
                async with self._database_pool.acquire() as conn:
                    # Increment consecutive_failures; degrade health
                    existing_row = await conn.fetchrow(
                        "SELECT consecutive_failures, health_status"
                        ' FROM "15_sandbox"."20_fct_connector_instances"'
                        " WHERE id = $1",
                        connector_instance_id,
                    )
                    prev_failures = (
                        existing_row["consecutive_failures"] if existing_row else 0
                    )
                    new_failures = prev_failures + 1
                    if is_auth_error:
                        new_health = "auth_failed"
                    elif new_failures >= 3:
                        new_health = "error"
                    else:
                        new_health = "degraded"
                    await ac_repo.update_health(
                        conn,
                        connector_instance_id,
                        health_status=new_health,
                        consecutive_failures=new_failures,
                    )

                    await self._repository.set_run_completed(
                        conn,
                        run_id,
                        status="failed",
                        error_message=str(exc)[:2000],
                    )
                    await self._audit_writer.write_entry(
                        conn,
                        AuditEntry(
                            id=str(uuid.uuid4()),
                            tenant_key=tenant_key,
                            entity_type="collection_run",
                            entity_id=run_id,
                            event_type=SandboxAuditEventType.COLLECTION_FAILED.value,
                            event_category="asset_inventory",
                            occurred_at=utc_now_sql(),
                            actor_id=triggered_by or "system",
                            actor_type="user" if triggered_by else "system",
                            properties={"error": str(exc)[:500], "health": new_health},
                        ),
                    )
            except Exception as inner_exc:
                logger.error(
                    "Failed to mark collection run '%s' as failed: %s",
                    run_id,
                    inner_exc,
                    exc_info=True,
                )
        finally:
            await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    # ── auto-run control tests after collection ────────────────────
    async def _auto_run_control_tests(
        self,
        *,
        connector_instance_id: str,
        org_id: str,
        tenant_key: str,
        triggered_by: str | None,
        collection_run_id: str,
    ) -> None:
        """Find all promoted tests linked to this connector and run their signals against collected assets."""
        logger = self._logger

        async with self._database_pool.acquire() as conn:
            # 1. Find promoted tests linked to this connector
            promoted_tests = await conn.fetch(
                """
                SELECT pt.id::text, pt.test_code, pt.source_signal_id::text,
                       pt.workspace_id::text, pt.org_id::text,
                       pp_name.property_value AS test_name
                FROM "15_sandbox"."35_fct_promoted_tests" pt
                LEFT JOIN "15_sandbox"."36_dtl_promoted_test_properties" pp_name
                    ON pp_name.test_id = pt.id AND pp_name.property_key = 'name'
                WHERE pt.linked_asset_id = $1
                  AND pt.is_active = TRUE
                  AND pt.source_signal_id IS NOT NULL
                """,
                connector_instance_id,
            )
            if not promoted_tests:
                logger.info(
                    "auto_run: no promoted tests linked to connector %s",
                    connector_instance_id,
                )
                return

            logger.info(
                "auto_run: found %d promoted tests for connector %s",
                len(promoted_tests),
                connector_instance_id,
            )

            # 2. Load assets for this connector
            _asset_repo_module = import_module(
                "backend.10_sandbox.14_assets.repository"
            )
            asset_repo = _asset_repo_module.AssetRepository()
            assets, _ = await asset_repo.list_assets(
                conn,
                org_id=org_id,
                connector_id=connector_instance_id,
                status="active",
                limit=200,
                offset=0,
            )
            if not assets:
                logger.info(
                    "auto_run: no active assets for connector %s, skipping",
                    connector_instance_id,
                )
                return

            # Build asset data dicts
            asset_data: list[dict] = []
            for asset in assets:
                props = await asset_repo.get_asset_properties(conn, asset.id)
                record: dict = {
                    "_asset_id": asset.id,
                    "_asset_type": asset.asset_type_code,
                    "_asset_external_id": asset.asset_external_id,
                    "_provider_code": asset.provider_code,
                }
                for prop in props:
                    record[prop.property_key] = prop.property_value
                asset_data.append(record)

            logger.info(
                "auto_run: loaded %d assets, running %d tests",
                len(asset_data),
                len(promoted_tests),
            )

        # 3. For each promoted test, load signal source and run
        _engine_module = import_module("backend.10_sandbox.07_execution.engine")
        engine = _engine_module.SignalExecutionEngine(
            timeout_ms=self._settings.sandbox_execution_timeout_ms,
            max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
            max_concurrent=5,
        )

        _issue_module = import_module("backend.09_issues.service")
        issue_service = _issue_module.IssueService(database_pool=self._database_pool)

        for pt in promoted_tests:
            signal_id = pt["source_signal_id"]
            test_code = pt["test_code"]
            test_name = pt["test_name"]

            async with self._database_pool.acquire() as conn:
                # Load signal python_source
                sig_props = await conn.fetch(
                    """SELECT property_key, property_value
                       FROM "15_sandbox"."45_dtl_signal_properties"
                       WHERE signal_id = $1::uuid""",
                    signal_id,
                )
                sig_props_dict = {
                    r["property_key"]: r["property_value"] for r in sig_props
                }
                python_source = sig_props_dict.get("python_source", "")
                if not python_source:
                    logger.warning(
                        "auto_run: signal %s has no python_source, skipping test %s",
                        signal_id,
                        test_code,
                    )
                    continue

                connector_type = (
                    sig_props_dict.get("connector_types", "").split(",")[0].strip()
                    if sig_props_dict.get("connector_types")
                    else None
                )

            # Run signal against each asset
            run_results: list[dict] = []
            for asset_record in asset_data:
                dataset = {
                    "records": [asset_record],
                    "items": [asset_record],
                    **asset_record,
                }
                try:
                    exec_result = await engine.execute(
                        python_source=python_source,
                        dataset=dataset,
                        timeout_ms=self._settings.sandbox_execution_timeout_ms,
                        max_memory_mb=self._settings.sandbox_execution_max_memory_mb,
                    )
                    if exec_result.status == "completed":
                        run_results.append(
                            {
                                "asset_id": asset_record["_asset_id"],
                                "asset_external_id": asset_record["_asset_external_id"],
                                "result": exec_result.result_code or "pass",
                                "summary": exec_result.result_summary or "",
                                "details": exec_result.result_details or [],
                                "execution_time_ms": exec_result.execution_time_ms,
                            }
                        )
                    else:
                        run_results.append(
                            {
                                "asset_id": asset_record["_asset_id"],
                                "asset_external_id": asset_record["_asset_external_id"],
                                "result": "error",
                                "summary": exec_result.error_message
                                or "Execution failed",
                                "details": [],
                                "execution_time_ms": exec_result.execution_time_ms,
                            }
                        )
                except Exception as e:
                    logger.error(
                        "auto_run: signal %s failed on asset %s: %s",
                        signal_id,
                        asset_record.get("_asset_id"),
                        e,
                    )
                    run_results.append(
                        {
                            "asset_id": asset_record["_asset_id"],
                            "asset_external_id": asset_record["_asset_external_id"],
                            "result": "error",
                            "summary": str(e)[:500],
                            "details": [],
                            "execution_time_ms": 0,
                        }
                    )

            # Aggregate results
            passed = sum(1 for r in run_results if r["result"] == "pass")
            failed = sum(1 for r in run_results if r["result"] == "fail")
            warnings = sum(1 for r in run_results if r["result"] == "warning")
            errors = sum(1 for r in run_results if r["result"] in ("error", "timeout"))
            overall = (
                "fail"
                if failed > 0
                else "warning"
                if warnings > 0
                else "error"
                if errors > 0
                else "pass"
            )
            summary = f"{passed} pass, {failed} fail, {warnings} warning, {errors} error across {len(asset_data)} assets"

            # 4. Record the run in sandbox runs table
            run_id = str(uuid.uuid4())
            total_time = sum(r["execution_time_ms"] for r in run_results)
            async with self._database_pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO "15_sandbox"."25_trx_sandbox_runs"
                        (id, tenant_key, org_id, signal_id,
                         execution_status_code, result_code, result_summary, result_details,
                         execution_time_ms, python_source_snapshot,
                         started_at, completed_at, created_at, created_by)
                    VALUES ($1, $2, $3::uuid, $4::uuid,
                            'completed', $5, $6, $7::jsonb,
                            $8, $9,
                            NOW(), NOW(), NOW(), $10)
                    """,
                    run_id,
                    tenant_key,
                    org_id,
                    signal_id,
                    overall,
                    summary,
                    json.dumps(run_results),
                    total_time,
                    python_source[:5000],
                    triggered_by or "system",
                )

            logger.info(
                "auto_run: test %s result=%s (%s) run_id=%s",
                test_code,
                overall,
                summary,
                run_id,
            )

            # 5. Create/update issue for failures (no duplicates)
            if overall in ("fail", "warning"):
                try:
                    issue_id = await issue_service.create_from_test_failure(
                        tenant_key=tenant_key,
                        org_id=org_id,
                        workspace_id=pt["workspace_id"],
                        promoted_test_id=pt["id"],
                        control_test_id=None,
                        execution_id=run_id,
                        connector_id=connector_instance_id,
                        test_code=test_code,
                        test_name=test_name,
                        result_summary=summary,
                        result_details=run_results,
                        connector_type_code=connector_type,
                        severity_code="high" if overall == "fail" else "medium",
                        created_by=triggered_by,
                    )
                    logger.info(
                        "auto_run: issue %s for test %s (result=%s)",
                        issue_id,
                        test_code,
                        overall,
                    )
                except Exception as issue_exc:
                    logger.error(
                        "auto_run: failed to create issue for test %s: %s",
                        test_code,
                        issue_exc,
                    )


def _run_response(r) -> CollectionRunResponse:
    return CollectionRunResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        connector_instance_id=r.connector_instance_id,
        status=r.status,
        trigger_type=r.trigger_type,
        started_at=r.started_at,
        completed_at=r.completed_at,
        assets_discovered=r.assets_discovered,
        assets_updated=r.assets_updated,
        assets_deleted=r.assets_deleted,
        logs_ingested=r.logs_ingested,
        error_message=r.error_message,
        triggered_by=r.triggered_by,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )
