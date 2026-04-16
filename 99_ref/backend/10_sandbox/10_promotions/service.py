from __future__ import annotations

import uuid
from importlib import import_module

from .repository import PromotionRepository
from .schemas import (
    PromoteLibraryRequest,
    PromotePolicyRequest,
    PromoteSignalRequest,
    PromotionListResponse,
    PromotionResponse,
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
_policy_container_module = import_module("backend.10_sandbox.policy_container")

Settings = _settings_module.Settings
DatabasePool = _database_module.DatabasePool
CacheManager = _cache_module.CacheManager
NullCacheManager = _cache_module.NullCacheManager
get_logger = _logging_module.get_logger
instrument_class_methods = _telemetry_module.instrument_class_methods
NotFoundError = _errors_module.NotFoundError
AuthorizationError = _errors_module.AuthorizationError
ConflictError = _errors_module.ConflictError
ValidationError = _errors_module.ValidationError
AuditEntry = _audit_module.AuditEntry
AuditWriter = _audit_module.AuditWriter
SandboxAuditEventType = _constants_module.SandboxAuditEventType
require_permission = _perm_check_module.require_permission
utc_now_sql = _time_module.utc_now_sql
write_lifecycle_event = _lifecycle_module.write_lifecycle_event
POLICY_CONTAINER_CODE_PROPERTY = _policy_container_module.POLICY_CONTAINER_CODE_PROPERTY
POLICY_CONTAINER_NAME_PROPERTY = _policy_container_module.POLICY_CONTAINER_NAME_PROPERTY


@instrument_class_methods(
    namespace="sandbox.promotions.service",
    logger_name="backend.sandbox.promotions.instrumentation",
)
class PromotionService:
    def __init__(self, *, settings, database_pool, cache) -> None:
        self._settings = settings
        self._database_pool = database_pool
        self._cache = cache
        self._repository = PromotionRepository()
        self._audit_writer = AuditWriter(schema_name="03_auth_manage")
        self._logger = get_logger("backend.sandbox.promotions")

    # ── promote signal ────────────────────────────────────────

    async def promote_signal(
        self,
        *,
        user_id: str,
        tenant_key: str,
        signal_id: str,
        request: PromoteSignalRequest,
    ) -> PromotionResponse:
        now = utc_now_sql()
        promotion_id = str(uuid.uuid4())
        test_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.promote")

            # Load signal
            signal = await self._repository.get_signal_for_promotion(conn, signal_id)
            if signal is None:
                raise NotFoundError(f"Signal '{signal_id}' not found")

            if signal["signal_status_code"] != "validated":
                raise ValidationError(
                    f"Signal must be in 'validated' status to promote (current: '{signal['signal_status_code']}')"
                )

            # Determine test code
            test_code = request.target_test_code or f"sb_{signal['signal_code']}"

            # Load signal properties
            signal_props = await self._repository.get_signal_properties(conn, signal_id)

            # Create GRC control test (returns actual id — may differ if ON CONFLICT occurred)
            test_id = await self._repository.create_control_test(
                conn,
                id=test_id,
                tenant_key=tenant_key,
                test_code=test_code,
                test_type_code="automated",
                integration_type=signal.get("connector_type_code"),
                monitoring_frequency="manual",
                created_by=user_id,
                now=now,
            )

            # Map signal properties to test properties
            test_props: dict[str, str] = {}
            if signal.get("name"):
                test_props["name"] = signal["name"]
            if signal.get("description"):
                test_props["description"] = signal["description"]
            if signal.get("python_source"):
                test_props["evaluation_rule"] = signal["python_source"]
            if signal.get("connector_type_code"):
                test_props["signal_type"] = signal["connector_type_code"]
            if signal.get("source_prompt"):
                test_props["integration_guide"] = signal["source_prompt"]
            # Copy additional signal properties
            for key, value in signal_props.items():
                if key not in test_props:
                    test_props[key] = value

            if test_props:
                await self._repository.upsert_control_test_properties(
                    conn,
                    test_id,
                    test_props,
                    created_by=user_id,
                    now=now,
                )

            # Update signal status to promoted
            await self._repository.update_signal_status(
                conn,
                signal_id,
                "promoted",
                updated_by=user_id,
                now=now,
            )

            # Record promotion FIRST (FK parent for promoted test)
            await self._repository.insert_promotion(
                conn,
                id=promotion_id,
                tenant_key=tenant_key,
                signal_id=signal_id,
                target_test_id=test_id,
                promotion_status="promoted",
                promoted_at=now,
                promoted_by=user_id,
                created_by=user_id,
                now=now,
            )

            # Dual-write: create promoted test record (versioned, asset-linked)
            next_version = await self._repository.get_next_promoted_version(
                conn, tenant_key, test_code
            )
            await self._repository.deactivate_promoted_versions(
                conn, tenant_key, test_code
            )
            promoted_test_id = str(uuid.uuid4())
            await self._repository.create_promoted_test(
                conn,
                id=promoted_test_id,
                tenant_key=tenant_key,
                org_id=signal["org_id"],
                workspace_id=request.workspace_id or signal.get("workspace_id"),
                promotion_id=promotion_id,
                source_signal_id=signal_id,
                test_code=test_code,
                test_type_code="automated",
                monitoring_frequency="manual",
                linked_asset_id=request.linked_asset_id,
                version_number=next_version,
                promoted_by=user_id,
                now=now,
            )
            if test_props:
                await self._repository.upsert_promoted_test_properties(
                    conn,
                    promoted_test_id,
                    test_props,
                    user_id,
                    now,
                )

            # Audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="promotion",
                    entity_id=promotion_id,
                    event_type=SandboxAuditEventType.SIGNAL_PROMOTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "signal_id": signal_id,
                        "signal_code": signal["signal_code"],
                        "target_test_id": test_id,
                        "target_test_code": test_code,
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=signal["org_id"],
                entity_type="signal",
                entity_id=signal_id,
                event_type="promoted",
                actor_id=user_id,
                new_value="promoted",
                properties={"target_test_id": test_id, "target_test_code": test_code},
            )

        return _promotion_response(await self._get_promotion(promotion_id))

    # ── promote policy ────────────────────────────────────────

    async def promote_policy(
        self,
        *,
        user_id: str,
        tenant_key: str,
        policy_id: str,
        request: PromotePolicyRequest,
    ) -> PromotionResponse:
        now = utc_now_sql()
        promotion_id = str(uuid.uuid4())
        test_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.promote")

            # Load policy
            policy = await self._repository.get_policy_for_promotion(conn, policy_id)
            if policy is None:
                raise NotFoundError(f"Policy '{policy_id}' not found")

            # Validate that the policy's linked threat type has been evaluated
            if policy.get("threat_type_id"):
                eval_row = await conn.fetchrow(
                    f"""SELECT id FROM "15_sandbox"."26_trx_threat_evaluations"
                        WHERE threat_type_id = $1 LIMIT 1""",
                    policy["threat_type_id"],
                )
                if eval_row is None:
                    raise ValidationError(
                        f"Cannot promote policy: linked threat type '{policy.get('threat_code', policy['threat_type_id'])}' "
                        f"has never been evaluated. Run at least one evaluation first."
                    )

            # Determine test code
            test_code = request.target_test_code or f"sb_{policy['policy_code']}"

            # Create GRC control test (returns actual id — may differ if ON CONFLICT occurred)
            test_id = await self._repository.create_control_test(
                conn,
                id=test_id,
                tenant_key=tenant_key,
                test_code=test_code,
                test_type_code="automated",
                integration_type=policy.get("policy_container_code"),
                monitoring_frequency="manual",
                created_by=user_id,
                now=now,
            )

            # Map policy to test properties
            test_props: dict[str, str] = {}
            if policy.get("name"):
                test_props["name"] = policy["name"]
            if policy.get("description"):
                test_props["description"] = policy["description"]
            if policy.get("threat_code"):
                test_props["signal_type"] = policy["threat_code"]
            if policy.get("policy_container_code"):
                test_props[POLICY_CONTAINER_CODE_PROPERTY] = policy[
                    "policy_container_code"
                ]
            if policy.get("policy_container_name"):
                test_props[POLICY_CONTAINER_NAME_PROPERTY] = policy[
                    "policy_container_name"
                ]

            # Load the signal's python_source and add to test_props for execution
            if policy.get("threat_type_id"):
                signal_props = (
                    await self._repository.get_signal_properties_for_threat_type(
                        conn, policy["threat_type_id"]
                    )
                )
                if signal_props and signal_props.get("python_source"):
                    test_props["evaluation_rule"] = signal_props["python_source"]
                    if signal_props.get("connector_types"):
                        test_props["signal_type"] = signal_props[
                            "connector_types"
                        ].split(",")[0]

            if test_props:
                await self._repository.upsert_control_test_properties(
                    conn,
                    test_id,
                    test_props,
                    created_by=user_id,
                    now=now,
                )

            # Record promotion before creating the promoted test so the FK parent exists.
            await self._repository.insert_promotion(
                conn,
                id=promotion_id,
                tenant_key=tenant_key,
                policy_id=policy_id,
                target_test_id=test_id,
                promotion_status="promoted",
                promoted_at=now,
                promoted_by=user_id,
                created_by=user_id,
                now=now,
            )

            # Dual-write: create promoted test record (versioned, asset-linked)
            next_version = await self._repository.get_next_promoted_version(
                conn, tenant_key, test_code
            )
            await self._repository.deactivate_promoted_versions(
                conn, tenant_key, test_code
            )
            promoted_test_id = str(uuid.uuid4())
            await self._repository.create_promoted_test(
                conn,
                id=promoted_test_id,
                tenant_key=tenant_key,
                org_id=policy["org_id"],
                workspace_id=request.workspace_id or policy.get("workspace_id"),
                promotion_id=promotion_id,
                source_policy_id=policy_id,
                test_code=test_code,
                test_type_code="automated",
                monitoring_frequency="manual",
                linked_asset_id=request.linked_asset_id,
                version_number=next_version,
                promoted_by=user_id,
                now=now,
            )
            if test_props:
                await self._repository.upsert_promoted_test_properties(
                    conn,
                    promoted_test_id,
                    test_props,
                    user_id,
                    now,
                )

            # Audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="promotion",
                    entity_id=promotion_id,
                    event_type=SandboxAuditEventType.POLICY_PROMOTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "policy_id": policy_id,
                        "policy_code": policy["policy_code"],
                        "target_test_id": test_id,
                        "target_test_code": test_code,
                    },
                ),
            )
            await write_lifecycle_event(
                conn,
                tenant_key=tenant_key,
                org_id=policy["org_id"],
                entity_type="policy",
                entity_id=policy_id,
                event_type="promoted",
                actor_id=user_id,
                properties={"target_test_id": test_id, "target_test_code": test_code},
            )

        return _promotion_response(await self._get_promotion(promotion_id))

    # ── promote library (bulk) ────────────────────────────────

    async def promote_library(
        self,
        *,
        user_id: str,
        tenant_key: str,
        library_id: str,
        request: PromoteLibraryRequest,
    ) -> PromotionResponse:
        now = utc_now_sql()
        promotion_id = str(uuid.uuid4())

        async with self._database_pool.transaction() as conn:
            await require_permission(conn, user_id, "sandbox.promote")

            # Get all policy IDs in the library
            policy_ids = await self._repository.get_library_policy_ids(conn, library_id)
            if not policy_ids:
                raise ValidationError(
                    f"Library '{library_id}' has no policies to promote"
                )

            prefix = request.target_test_code_prefix or "sb_lib"
            promoted_test_ids: list[str] = []

            for idx, pid in enumerate(policy_ids):
                policy = await self._repository.get_policy_for_promotion(conn, pid)
                if policy is None:
                    continue

                test_id = str(uuid.uuid4())
                test_code = f"{prefix}_{policy['policy_code']}"

                await self._repository.create_control_test(
                    conn,
                    id=test_id,
                    tenant_key=tenant_key,
                    test_code=test_code,
                    test_type_code="automated",
                    integration_type=None,
                    monitoring_frequency="manual",
                    created_by=user_id,
                    now=now,
                )

                test_props: dict[str, str] = {}
                if policy.get("name"):
                    test_props["name"] = policy["name"]
                if policy.get("description"):
                    test_props["description"] = policy["description"]
                if policy.get("threat_code"):
                    test_props["signal_type"] = policy["threat_code"]

                if test_props:
                    await self._repository.upsert_control_test_properties(
                        conn,
                        test_id,
                        test_props,
                        created_by=user_id,
                        now=now,
                    )

                # Create promoted test record for each policy
                promoted_test_id = str(uuid.uuid4())
                next_version = await self._repository.get_next_promoted_version(
                    conn, tenant_key, test_code
                )
                await self._repository.create_promoted_test(
                    conn,
                    id=promoted_test_id,
                    tenant_key=tenant_key,
                    org_id=policy["org_id"],
                    workspace_id=request.workspace_id or policy.get("workspace_id"),
                    promotion_id=promotion_id,
                    source_policy_id=pid,
                    source_library_id=library_id,
                    test_code=test_code,
                    test_type_code="automated",
                    monitoring_frequency="manual",
                    linked_asset_id=request.linked_asset_id,
                    version_number=next_version,
                    promoted_by=user_id,
                    now=now,
                )
                if test_props:
                    await self._repository.upsert_promoted_test_properties(
                        conn,
                        promoted_test_id,
                        test_props,
                        user_id,
                        now,
                    )
                promoted_test_ids.append(promoted_test_id)

            # Record a single promotion entry for the library
            await self._repository.insert_promotion(
                conn,
                id=promotion_id,
                tenant_key=tenant_key,
                library_id=library_id,
                target_test_id=promoted_test_ids[0] if promoted_test_ids else None,
                promotion_status="promoted",
                promoted_at=now,
                promoted_by=user_id,
                review_notes=f"Promoted {len(promoted_test_ids)} policies from library",
                created_by=user_id,
                now=now,
            )

            # Audit
            await self._audit_writer.write_entry(
                conn,
                AuditEntry(
                    id=str(uuid.uuid4()),
                    tenant_key=tenant_key,
                    entity_type="promotion",
                    entity_id=promotion_id,
                    event_type=SandboxAuditEventType.LIBRARY_PROMOTED.value,
                    event_category="sandbox",
                    occurred_at=now,
                    actor_id=user_id,
                    actor_type="user",
                    properties={
                        "library_id": library_id,
                        "policy_count": str(len(policy_ids)),
                        "promoted_test_count": str(len(promoted_test_ids)),
                    },
                ),
            )
            # Determine org_id from the first promoted policy for lifecycle event
            first_policy = (
                await self._repository.get_policy_for_promotion(conn, policy_ids[0])
                if policy_ids
                else None
            )
            if first_policy:
                await write_lifecycle_event(
                    conn,
                    tenant_key=tenant_key,
                    org_id=first_policy["org_id"],
                    entity_type="library",
                    entity_id=library_id,
                    event_type="promoted",
                    actor_id=user_id,
                    properties={
                        "promoted_test_count": str(len(promoted_test_ids)),
                    },
                )

        return _promotion_response(await self._get_promotion(promotion_id))

    # ── list promotions ───────────────────────────────────────

    async def list_promotions(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str | None = None,
        signal_id: str | None = None,
        policy_id: str | None = None,
        library_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> PromotionListResponse:
        async with self._database_pool.acquire() as conn:
            if org_id:
                await require_permission(
                    conn,
                    user_id,
                    "sandbox.view",
                    scope_org_id=org_id,
                )
            records = await self._repository.list_promotions(
                conn,
                tenant_key,
                org_id=org_id,
                signal_id=signal_id,
                policy_id=policy_id,
                library_id=library_id,
                limit=limit,
                offset=offset,
            )
            if not org_id:
                authorized_records = []
                for record in records:
                    try:
                        await require_permission(
                            conn,
                            user_id,
                            "sandbox.view",
                            scope_org_id=record.source_org_id,
                        )
                    except AuthorizationError:
                        continue
                    authorized_records.append(record)
                records = authorized_records
            total = await self._repository.count_promotions(
                conn,
                tenant_key,
                org_id=org_id,
                signal_id=signal_id,
                policy_id=policy_id,
                library_id=library_id,
            )
            if not org_id:
                total = len(records)

        items = [_promotion_response(r) for r in records]
        return PromotionListResponse(items=items, total=total)

    # ── get promotion ─────────────────────────────────────────

    async def get_promotion_detail(
        self, *, user_id: str, promotion_id: str
    ) -> PromotionResponse:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_promotion(conn, promotion_id)
            if record:
                await require_permission(
                    conn,
                    user_id,
                    "sandbox.view",
                    scope_org_id=record.source_org_id,
                )
        if record is None:
            raise NotFoundError(f"Promotion '{promotion_id}' not found")
        return _promotion_response(record)

    # ── internal helper ───────────────────────────────────────

    async def _get_promotion(self, promotion_id: str) -> PromotionRecord:
        async with self._database_pool.acquire() as conn:
            record = await self._repository.get_promotion(conn, promotion_id)
        if record is None:
            raise NotFoundError(f"Promotion '{promotion_id}' not found")
        return record


def _promotion_response(r) -> PromotionResponse:
    return PromotionResponse(
        id=r.id,
        tenant_key=r.tenant_key,
        signal_id=r.signal_id,
        policy_id=r.policy_id,
        library_id=r.library_id,
        target_test_id=r.target_test_id,
        target_test_code=r.target_test_code,
        source_name=r.source_name,
        source_code=r.source_code,
        promotion_status=r.promotion_status,
        promoted_at=r.promoted_at,
        promoted_by=r.promoted_by,
        review_notes=r.review_notes,
        created_at=r.created_at,
        created_by=r.created_by,
    )
