from __future__ import annotations

import uuid
from importlib import import_module

from .crypto import encrypt_value, parse_encryption_key
from .repository import ConnectorRepository
from .schemas import (
    CollectResponse,
    ConnectorListResponse,
    ConnectorResponse,
    CreateConnectorRequest,
    PreflightTestRequest,
    TestConnectionResponse,
    UpdateConnectorRequest,
    UpdateCredentialsRequest,
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
_lifecycle_module = import_module("backend.10_sandbox.lifecycle")

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
write_lifecycle_event = _lifecycle_module.write_lifecycle_event

_CACHE_KEY_PREFIX = "sb:connectors"
_CACHE_TTL = 300


@instrument_class_methods(
    namespace="sandbox.connectors.service",
    logger_name="backend.sandbox.connectors.instrumentation",
)
class ConnectorService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = ConnectorRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.connectors")

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

    async def _get_connector_or_not_found(self, conn, connector_id: str):
        record = await self._repository.get_connector_by_id(conn, connector_id)
        if record is None:
            raise NotFoundError(f"Connector '{connector_id}' not found")
        return record

    async def list_connectors(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str | None = None,
        connector_type_code: str | None = None,
        category_code: str | None = None,
        health_status: str | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> ConnectorListResponse:
        cache_key = f"{_CACHE_KEY_PREFIX}:{org_id}"
        # Only use cache for unfiltered first-page requests
        if (
            not any([connector_type_code, category_code, health_status, is_active])
            and offset == 0
            and limit == 100
        ):
            cached = await self._cache.get_json(cache_key)
            if cached is not None:
                return ConnectorListResponse(**cached)

        async with self._database_pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=org_id,
            )
            records, total = await self._repository.list_connectors(
                conn,
                org_id,
                workspace_id=workspace_id,
                connector_type_code=connector_type_code,
                category_code=category_code,
                health_status=health_status,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )

        items = [_connector_response(r) for r in records]
        result = ConnectorListResponse(items=items, total=total)

        if (
            not any([connector_type_code, category_code, health_status, is_active])
            and offset == 0
            and limit == 100
        ):
            await self._cache.set_json(
                cache_key, result.model_dump(), ttl_seconds=_CACHE_TTL
            )

        return result

    async def get_connector(
        self, *, user_id: str, connector_id: str
    ) -> ConnectorResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
        return _connector_response(record)

    async def get_connector_properties(
        self, *, user_id: str, connector_id: str
    ) -> dict[str, str]:
        async with self._database_pool.acquire() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.view",
                org_id=record.org_id,
            )
            return await self._repository.get_properties(conn, connector_id)

    async def create_connector(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: CreateConnectorRequest,
    ) -> ConnectorResponse:
        now = utc_now_sql()
        connector_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=org_id,
            )
            await self._repository.create_connector(
                conn,
                id=connector_id,
                tenant_key=tenant_key,
                org_id=org_id,
                workspace_id=request.workspace_id,
                instance_code=request.instance_code,
                connector_type_code=request.connector_type_code,
                asset_version_id=request.asset_version_id,
                collection_schedule=request.collection_schedule,
                is_draft=request.is_draft,
                created_by=user_id,
                now=now,
            )
            # Upsert properties (name, description, and custom properties)
            props: dict[str, str] = {}
            if request.name:
                props["name"] = request.name
            if request.description:
                props["description"] = request.description
            if request.properties:
                props.update(request.properties)
            if props:
                await self._repository.upsert_properties(
                    conn,
                    connector_id,
                    props,
                    created_by=user_id,
                    now=now,
                )
            # Encrypt and upsert credentials
            if request.credentials:
                enc_key = self._get_encryption_key()
                encrypted = {
                    k: encrypt_value(v, enc_key) for k, v in request.credentials.items()
                }
                await self._repository.upsert_credentials(
                    conn,
                    connector_id,
                    encrypted,
                    encryption_key_id="default",
                    created_by=user_id,
                    now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_CREATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "instance_code": request.instance_code,
                        "connector_type_code": request.connector_type_code,
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="connector",
                entity_id=connector_id,
                event_type="created",
                actor_id=user_id,
                properties={"instance_code": request.instance_code},
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_connector_by_id(conn, connector_id)
        return _connector_response(record)

    async def update_connector(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        connector_id: str,
        request: UpdateConnectorRequest,
    ) -> ConnectorResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            updated = await self._repository.update_connector(
                conn,
                connector_id,
                collection_schedule=request.collection_schedule,
                asset_version_id=request.asset_version_id,
                is_active=request.is_active,
                updated_by=user_id,
                now=now,
            )
            if not updated:
                raise NotFoundError(f"Connector '{connector_id}' not found")
            props: dict[str, str] = {}
            if request.name is not None:
                props["name"] = request.name
            if request.description is not None:
                props["description"] = request.description
            if request.properties:
                props.update(request.properties)
            if props:
                await self._repository.upsert_properties(
                    conn,
                    connector_id,
                    props,
                    created_by=user_id,
                    now=now,
                )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_connector_by_id(conn, connector_id)
        return _connector_response(record)

    async def update_credentials(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        connector_id: str,
        request: UpdateCredentialsRequest,
    ) -> None:
        now = utc_now_sql()
        enc_key = self._get_encryption_key()
        encrypted = {
            k: encrypt_value(v, enc_key) for k, v in request.credentials.items()
        }

        async with self._database_pool.transaction() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )
            await self._repository.upsert_credentials(
                conn,
                connector_id,
                encrypted,
                encryption_key_id="default",
                created_by=user_id,
                now=now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_CREDENTIALS_UPDATED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"credential_count": str(len(request.credentials))},
                ),
            )

    async def delete_connector(
        self, *, user_id: str, tenant_key: str, org_id: str, connector_id: str
    ) -> None:
        SCHEMA = '"15_sandbox"'
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.delete",
                org_id=record.org_id,
            )
            # Check for datasets referencing this connector
            ref_count = await conn.fetchval(
                f"""SELECT count(*) FROM {SCHEMA}."21_fct_datasets"
                    WHERE connector_instance_id = $1 AND is_deleted = FALSE""",
                connector_id,
            )
            if ref_count > 0:
                raise ConflictError(
                    f"Connector has {ref_count} dataset(s). "
                    "Delete datasets before removing connector."
                )
            deleted = await self._repository.soft_delete_connector(
                conn,
                connector_id,
                deleted_by=user_id,
                now=now,
            )
            if not deleted:
                raise NotFoundError(f"Connector '{connector_id}' not found")
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_DELETED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                entity_type="connector",
                entity_id=connector_id,
                event_type="deleted",
                actor_id=user_id,
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

    async def preflight_test(
        self, *, user_id: str, request: PreflightTestRequest
    ) -> TestConnectionResponse:
        """Stateless connection test — no connector ID required, nothing is persisted."""
        now = utc_now_sql()
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            row = await conn.fetchrow(
                'SELECT code FROM "15_sandbox"."03_dim_connector_types" WHERE code = $1 AND is_active = TRUE',
                request.connector_type_code,
            )
            if not row:
                raise NotFoundError(
                    f"Connector type '{request.connector_type_code}' not found"
                )

        if not request.credentials:
            return TestConnectionResponse(
                health_status="degraded",
                message="No credentials provided — cannot verify connection.",
                tested_at=str(now),
            )

        # Use Steampipe to test connection
        provider_code = request.connector_type_code
        try:
            _steampipe_module = import_module(
                "backend.10_sandbox.19_steampipe.steampipe"
            )
            _substrate_base = import_module("backend.10_sandbox.19_steampipe.base")
            SteampipeSubstrate = _steampipe_module.SteampipeSubstrate
            ConnectionConfig = _substrate_base.ConnectionConfig
            import shutil as _shutil, os as _os

            steampipe_binary = _shutil.which("steampipe") or _os.path.expanduser(
                "~/bin/steampipe"
            )
            substrate = SteampipeSubstrate(
                binary_path=steampipe_binary, query_timeout_seconds=30
            )
            connection_config = ConnectionConfig(
                connector_instance_id="preflight",
                provider_code=provider_code,
                provider_version_code=None,
                config=request.properties,
                credentials=request.credentials,
            )
            test_result = await substrate.test_connection(connection_config)
            health_status = "healthy" if test_result.success else "degraded"
            message = test_result.message
        except Exception as e:
            health_status = "degraded"
            error_detail = str(e) or repr(e) or type(e).__name__
            self._logger.warning(
                "preflight_test_failed",
                extra={
                    "provider": provider_code,
                    "error_type": type(e).__name__,
                    "error": error_detail,
                },
            )
            message = f"Connection test failed: {error_detail}"

        return TestConnectionResponse(
            health_status=health_status,
            message=message,
            tested_at=str(now),
        )

    async def test_connection(
        self, *, user_id: str, tenant_key: str, connector_id: str
    ) -> TestConnectionResponse:
        now = utc_now_sql()

        # Load connector + credentials outside the transaction so we don't hold it during network I/O
        async with self._database_pool.acquire() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.update",
                org_id=record.org_id,
            )

            cred_rows = await conn.fetch(
                'SELECT credential_key, encrypted_value, encryption_key_id FROM "15_sandbox"."41_dtl_connector_credentials" WHERE connector_instance_id = $1',
                connector_id,
            )
            config_row = await conn.fetchrow(
                'SELECT connection_config, provider_definition_code FROM "15_sandbox"."20_fct_connector_instances" WHERE id = $1',
                connector_id,
            )
            prop_rows = await conn.fetch(
                'SELECT property_key, property_value FROM "15_sandbox"."40_dtl_connector_instance_properties" WHERE connector_instance_id = $1',
                connector_id,
            )

        if not cred_rows:
            health_status = "degraded"
            message = "No credentials configured — cannot verify connection."
        else:
            # Decrypt credentials
            _crypto_module = import_module("backend.10_sandbox.02_connectors.crypto")
            parse_encryption_key = _crypto_module.parse_encryption_key
            decrypt_value = _crypto_module.decrypt_value
            enc_key = parse_encryption_key(self._settings.sandbox_encryption_key or "")
            credentials: dict[str, str] = {}
            for row in cred_rows:
                try:
                    credentials[row["credential_key"]] = decrypt_value(
                        row["encrypted_value"], enc_key
                    )
                except Exception:
                    pass

            # Build config from JSONB + EAV properties
            raw_config: dict = {}
            if config_row and config_row["connection_config"]:
                raw_config = dict(config_row["connection_config"])
            for prop in prop_rows:
                key = prop["property_key"]
                if key not in ("name", "description"):
                    raw_config.setdefault(key, prop["property_value"])

            provider_code = (
                config_row["provider_definition_code"] if config_row else None
            ) or record.connector_type_code

            try:
                _steampipe_module = import_module(
                    "backend.10_sandbox.19_steampipe.steampipe"
                )
                _substrate_base = import_module("backend.10_sandbox.19_steampipe.base")
                SteampipeSubstrate = _steampipe_module.SteampipeSubstrate
                ConnectionConfig = _substrate_base.ConnectionConfig
                import shutil as _shutil, os as _os

                steampipe_binary = _shutil.which("steampipe") or _os.path.expanduser(
                    "~/bin/steampipe"
                )
                substrate = SteampipeSubstrate(
                    binary_path=steampipe_binary, query_timeout_seconds=30
                )
                connection_config = ConnectionConfig(
                    connector_instance_id=connector_id,
                    provider_code=provider_code,
                    provider_version_code=None,
                    config=raw_config,
                    credentials=credentials,
                )
                test_result = await substrate.test_connection(connection_config)
                health_status = "healthy" if test_result.success else "degraded"
                message = test_result.message
            except Exception as e:
                health_status = "degraded"
                error_detail = str(e) or repr(e) or type(e).__name__
                self._logger.warning(
                    "connector_test_failed",
                    extra={
                        "connector_id": connector_id,
                        "provider": provider_code,
                        "error_type": type(e).__name__,
                        "error": error_detail,
                    },
                )
                message = f"Connection test failed: {error_detail}"

        # Persist health status
        async with self._database_pool.transaction() as conn:
            clear_draft = health_status == "healthy"
            await self._repository.update_health_status(
                conn,
                connector_id,
                health_status,
                now,
                clear_draft=clear_draft,
            )
            old_health = record.health_status or "unknown"
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_TESTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"health_status": health_status},
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=record.org_id,
                entity_type="connector",
                entity_id=connector_id,
                event_type="health_changed",
                actor_id=user_id,
                old_value=old_health,
                new_value=health_status,
            )

        return TestConnectionResponse(
            health_status=health_status,
            message=message,
            tested_at=str(now),
        )

    async def trigger_collection(
        self, *, user_id: str, tenant_key: str, org_id: str, connector_id: str
    ) -> CollectResponse:
        now = utc_now_sql()
        async with self._database_pool.transaction() as conn:
            record = await self._get_connector_or_not_found(conn, connector_id)
            await self._require_sandbox_permission(
                conn,
                user_id=user_id,
                permission_code="sandbox.create",
                org_id=record.org_id,
            )
            # Mock result — real collection will be implemented later
            dataset_id = str(uuid.uuid4())
            dataset_code = f"{record.instance_code}-collection"
            await self._repository.update_health_status(
                conn,
                connector_id,
                "healthy",
                now,
            )
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_COLLECTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={"dataset_id": dataset_id},
                ),
            )

        await self._cache.delete(f"{_CACHE_KEY_PREFIX}:{org_id}")

        return CollectResponse(
            dataset_id=dataset_id,
            dataset_code=dataset_code,
            version_number=1,
            collected_at=str(now),
        )

    def _get_encryption_key(self) -> bytes:
        key_str = self._settings.sandbox_encryption_key
        if not key_str:
            raise ValidationError("Sandbox encryption key is not configured")
        return parse_encryption_key(key_str)


def _connector_response(r) -> ConnectorResponse:
    return ConnectorResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        org_id=r.org_id,
        workspace_id=r.workspace_id,
        instance_code=r.instance_code,
        connector_type_code=r.connector_type_code,
        connector_type_name=r.connector_type_name,
        connector_category_code=r.connector_category_code,
        connector_category_name=r.connector_category_name,
        asset_version_id=r.asset_version_id,
        collection_schedule=r.collection_schedule,
        last_collected_at=r.last_collected_at,
        health_status=r.health_status,
        is_active=r.is_active,
        is_draft=r.is_draft,
        created_at=r.created_at,
        updated_at=r.updated_at,
        name=r.name,
        description=r.description,
    )
