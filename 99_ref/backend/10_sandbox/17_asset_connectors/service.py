from __future__ import annotations

import uuid
from importlib import import_module

from .repository import AssetConnectorRepository
from .schemas import (
    AssetConnectorListResponse,
    AssetConnectorResponse,
    CreateAssetConnectorRequest,
    TestConnectionResponse,
    UpdateAssetConnectorRequest,
)

_database_module = import_module("backend.01_core.database")
_cache_module = import_module("backend.01_core.cache")
_logging_module = import_module("backend.01_core.logging_utils")
_telemetry_module = import_module("backend.01_core.telemetry")
_errors_module = import_module("backend.01_core.errors")
_audit_module = import_module("backend.01_core.audit")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")
_constants_module = import_module("backend.10_sandbox.constants")

get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
require_permission = _perm_check_module.require_permission
SandboxAuditEventType = _constants_module.SandboxAuditEventType

_CACHE_PREFIX = "sb:asset_connectors"
_CACHE_TTL = 300  # 5 min


@instrument_class_methods(
    namespace="sandbox.asset_connectors.service",
    logger_name="backend.sandbox.asset_connectors.service.instrumentation",
)
class AssetConnectorService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._pool = database_pool
        self._cache = cache
        self._repo = AssetConnectorRepository()
        self._audit = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.asset_connectors")

    # ─────────────────────────────────────────────────────────────────────
    # LIST
    # ─────────────────────────────────────────────────────────────────────

    async def list_connectors(
        self,
        *,
        user_id: str,
        org_id: str,
        provider_code: str | None = None,
        offset: int = 0,
        limit: int = 50,
    ) -> AssetConnectorListResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            items = await self._repo.list_connectors(
                conn,
                org_id=org_id,
                provider_code=provider_code,
                offset=offset,
                limit=limit,
            )
            total = await self._repo.count_connectors(
                conn,
                org_id=org_id,
                provider_code=provider_code,
            )
        return AssetConnectorListResponse(
            items=[_to_response(c) for c in items],
            total=total,
        )

    # ─────────────────────────────────────────────────────────────────────
    # GET
    # ─────────────────────────────────────────────────────────────────────

    async def get_connector(
        self,
        *,
        user_id: str,
        connector_id: str,
        org_id: str,
    ) -> AssetConnectorResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            record = await self._repo.get_connector(conn, connector_id, org_id)
        if record is None:
            raise NotFoundError(f"Asset connector '{connector_id}' not found")
        return _to_response(record)

    # ─────────────────────────────────────────────────────────────────────
    # CREATE
    # ─────────────────────────────────────────────────────────────────────

    async def create_connector(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        body: CreateAssetConnectorRequest,
    ) -> AssetConnectorResponse:
        # Validate config against provider schema first (no DB needed)
        await self._validate_config(
            body.provider_code, body.connection_config, body.provider_version_code
        )

        enc_key = self._get_enc_key()

        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")

            # Verify provider exists
            row = await conn.fetchrow(
                'SELECT code, is_coming_soon FROM "15_sandbox"."16_dim_provider_definitions"'
                " WHERE code = $1 AND is_active = TRUE",
                body.provider_code,
            )
            if row is None:
                raise NotFoundError(f"Provider '{body.provider_code}' not found")
            if row["is_coming_soon"]:
                raise ValidationError(
                    f"Provider '{body.provider_code}' is not yet available"
                )

            instance_code = f"{body.provider_code}_{str(uuid.uuid4())[:8]}"

            # Encrypt credential fields
            encrypted_creds = _encrypt_credentials(body.credentials, enc_key)

            connector_id = await self._repo.create_connector(
                conn,
                tenant_key=tenant_key,
                org_id=org_id,
                instance_code=instance_code,
                provider_definition_code=body.provider_code,
                provider_version_code=body.provider_version_code,
                connection_config=body.connection_config,
                collection_schedule=body.collection_schedule,
                created_by=user_id,
            )
            if encrypted_creds:
                await self._repo.upsert_credentials(conn, connector_id, encrypted_creds)
            if body.name:
                await self._repo.upsert_property(conn, connector_id, "name", body.name)
            if body.description:
                await self._repo.upsert_property(
                    conn, connector_id, "description", body.description
                )

            await self._audit.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset_connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_CREATED,
                    event_category="asset_inventory",
                    occurred_at="NOW()",
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "provider_code": body.provider_code,
                        "schedule": body.collection_schedule,
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_PREFIX}:{org_id}")

        async with self._pool.acquire() as conn:
            record = await self._repo.get_connector(conn, connector_id, org_id)
        return _to_response(record)

    # ─────────────────────────────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────────────────────────────

    async def update_connector(
        self,
        *,
        user_id: str,
        connector_id: str,
        org_id: str,
        tenant_key: str,
        body: UpdateAssetConnectorRequest,
    ) -> AssetConnectorResponse:
        enc_key = self._get_enc_key()

        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.update")
            record = await self._repo.get_connector(conn, connector_id, org_id)
            if record is None:
                raise NotFoundError(f"Asset connector '{connector_id}' not found")

            # Validate new config if provided
            if body.connection_config is not None:
                provider_code = record.provider_definition_code or ""
                version = body.provider_version_code or record.provider_version_code
                await self._validate_config(
                    provider_code, body.connection_config, version
                )

            await self._repo.update_connector(
                conn,
                connector_id,
                org_id,
                connection_config=body.connection_config,
                collection_schedule=body.collection_schedule,
                provider_version_code=body.provider_version_code,
                is_active=body.is_active,
                updated_by=user_id,
            )

            if body.credentials:
                encrypted_creds = _encrypt_credentials(body.credentials, enc_key)
                await self._repo.upsert_credentials(conn, connector_id, encrypted_creds)

            if body.name is not None:
                await self._repo.upsert_property(conn, connector_id, "name", body.name)
            if body.description is not None:
                await self._repo.upsert_property(
                    conn, connector_id, "description", body.description
                )

            await self._audit.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset_connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_UPDATED,
                    event_category="asset_inventory",
                    occurred_at="NOW()",
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "schedule": body.collection_schedule
                        or record.collection_schedule
                    },
                ),
            )

        await self._cache.delete(f"{_CACHE_PREFIX}:{org_id}")

        async with self._pool.acquire() as conn:
            updated = await self._repo.get_connector(conn, connector_id, org_id)
        return _to_response(updated)

    # ─────────────────────────────────────────────────────────────────────
    # DELETE
    # ─────────────────────────────────────────────────────────────────────

    async def delete_connector(
        self,
        *,
        user_id: str,
        connector_id: str,
        org_id: str,
        tenant_key: str,
    ) -> None:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.delete")

            # Refuse if active assets exist
            count_row = await conn.fetchrow(
                'SELECT COUNT(*)::int AS total FROM "15_sandbox"."33_fct_assets"'
                " WHERE connector_instance_id = $1 AND is_deleted = FALSE",
                connector_id,
            )
            active_assets = count_row["total"] if count_row else 0
            if active_assets > 0:
                raise ConflictError(
                    f"Cannot delete connector with {active_assets} active asset(s). "
                    "Delete or reassign assets first."
                )

            deleted = await self._repo.delete_connector(
                conn, connector_id, org_id, user_id
            )
            if not deleted:
                raise NotFoundError(f"Asset connector '{connector_id}' not found")

            await self._audit.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset_connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.CONNECTOR_DELETED,
                    event_category="asset_inventory",
                    occurred_at="NOW()",
                    actor_id=user_id,
                    actor_type="user",
                    properties={},
                ),
            )

        await self._cache.delete(f"{_CACHE_PREFIX}:{org_id}")

    # ─────────────────────────────────────────────────────────────────────
    # TEST CONNECTION
    # ─────────────────────────────────────────────────────────────────────

    async def test_connection(
        self,
        *,
        user_id: str,
        connector_id: str,
        org_id: str,
        tenant_key: str,
    ) -> TestConnectionResponse:
        async with self._pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.execute")
            record = await self._repo.get_connector(conn, connector_id, org_id)
            if record is None:
                raise NotFoundError(f"Asset connector '{connector_id}' not found")
            cred_rows = await self._repo.get_credentials_raw(conn, connector_id)

        provider_code = record.provider_definition_code or ""
        enc_key = self._get_enc_key()
        credentials = _decrypt_credentials(cred_rows, enc_key)

        _substrate_base = import_module("backend.10_sandbox.19_steampipe.base")
        ConnectionConfig = _substrate_base.ConnectionConfig
        config = ConnectionConfig(
            connector_instance_id=connector_id,
            provider_code=provider_code,
            provider_version_code=record.provider_version_code,
            config=record.connection_config or {},
            credentials=credentials,
        )

        _drivers = import_module("backend.10_sandbox.18_drivers")
        try:
            driver = _drivers.get_driver(provider_code)
            result = await driver.test_connection(config)
        except ValueError as e:
            return TestConnectionResponse(success=False, message=str(e))

        # Update health status based on test result
        new_health = "healthy" if result.success else "error"
        async with self._pool.acquire() as conn:
            await self._repo.update_health(
                conn,
                connector_id,
                health_status=new_health,
                consecutive_failures=0
                if result.success
                else record.consecutive_failures,
            )
            await self._audit.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="asset_connector",
                    entity_id=connector_id,
                    event_type=SandboxAuditEventType.PROVIDER_CONNECTION_TESTED,
                    event_category="asset_inventory",
                    occurred_at="NOW()",
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "success": str(result.success),
                        "provider": provider_code,
                    },
                ),
            )

        return TestConnectionResponse(
            success=result.success,
            message=result.message,
            details=result.details,
            latency_ms=result.latency_ms,
        )

    # ─────────────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────────────

    def _get_enc_key(self) -> bytes:
        _crypto = import_module("backend.10_sandbox.02_connectors.crypto")
        raw = self._settings.sandbox_encryption_key or ""
        if not raw:
            raise RuntimeError("SANDBOX_ENCRYPTION_KEY is not configured")
        return _crypto.parse_encryption_key(raw)

    async def _validate_config(
        self,
        provider_code: str,
        config: dict,
        version_code: str | None,
    ) -> None:
        _provider_svc_mod = import_module("backend.10_sandbox.16_providers.service")
        async with self._pool.acquire() as conn:
            repo = import_module("backend.10_sandbox.16_providers.repository")
            provider = await repo.ProviderRepository().get_provider(conn, provider_code)
            version = None
            if version_code:
                version = await repo.ProviderRepository().get_provider_version(
                    conn, provider_code, version_code
                )
        if provider is None:
            raise NotFoundError(f"Provider '{provider_code}' not found")
        version_override = version.config_schema_override if version else None
        errors = _provider_svc_mod.ProviderService.validate_config_sync(
            provider, version_override, config
        )
        if errors:
            raise ValidationError(f"Invalid connection config: {'; '.join(errors)}")


# ─────────────────────────────────────────────────────────────────────────────
# Module-level helpers
# ─────────────────────────────────────────────────────────────────────────────


def _encrypt_credentials(raw: dict[str, str], enc_key: bytes) -> dict[str, str]:
    _crypto = import_module("backend.10_sandbox.02_connectors.crypto")
    return {k: _crypto.encrypt_value(v, enc_key) for k, v in raw.items()}


def _decrypt_credentials(rows: list, enc_key: bytes) -> dict[str, str]:
    _crypto = import_module("backend.10_sandbox.02_connectors.crypto")
    result: dict[str, str] = {}
    for r in rows:
        try:
            result[r["credential_key"]] = _crypto.decrypt_value(
                r["encrypted_value"], enc_key
            )
        except Exception:
            pass
    return result


def _to_response(c) -> AssetConnectorResponse:
    from .schemas import AssetConnectorResponse as R

    return R(
        id=c.id,
        org_id=c.org_id,
        provider_code=c.provider_definition_code,
        provider_version_code=c.provider_version_code,
        connection_config=c.connection_config,
        collection_schedule=c.collection_schedule,
        last_collected_at=c.last_collected_at,
        health_status=c.health_status,
        consecutive_failures=c.consecutive_failures,
        cooldown_until=c.cooldown_until,
        is_active=c.is_active,
        created_at=c.created_at,
        updated_at=c.updated_at,
        name=c.name,
        description=c.description,
    )
