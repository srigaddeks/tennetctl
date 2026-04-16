from __future__ import annotations

import hashlib
import json
import uuid
from importlib import import_module

from .repository import GlobalControlTestRepository
from .schemas import (
    ControlTestBundle,
    DatasetTemplateBundle,
    DeployResultResponse,
    GlobalControlTestListResponse,
    GlobalControlTestResponse,
    GlobalControlTestStatsResponse,
    PolicyBundle,
    PublishGlobalControlTestRequest,
    SignalBundle,
    TestDatasetBundle,
    TestDatasetRecord,
    ThreatTypeBundle,
    UpdateGlobalControlTestRequest,
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

SCHEMA = '"15_sandbox"'
_CACHE_PREFIX = "sb:global_tests"

logger = get_logger(__name__)


def _record_to_response(rec) -> GlobalControlTestResponse:
    bundle_data = json.loads(rec.bundle) if isinstance(rec.bundle, str) else rec.bundle
    return GlobalControlTestResponse(
        id=rec.id,
        global_code=rec.global_code,
        connector_type_code=rec.connector_type_code,
        connector_type_name=rec.connector_type_name,
        version_number=rec.version_number,
        bundle=ControlTestBundle(**bundle_data) if bundle_data else ControlTestBundle(),
        source_signal_id=rec.source_signal_id,
        source_policy_id=rec.source_policy_id,
        source_library_id=rec.source_library_id,
        source_org_id=rec.source_org_id,
        linked_dataset_code=rec.linked_dataset_code,
        publish_status=rec.publish_status,
        is_featured=rec.is_featured,
        download_count=rec.download_count,
        signal_count=rec.signal_count,
        published_by=rec.published_by,
        published_at=rec.published_at,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        name=rec.name,
        description=rec.description,
        tags=rec.tags,
        category=rec.category,
        changelog=rec.changelog,
        compliance_references=rec.compliance_references,
    )


@instrument_class_methods(
    namespace="sandbox.global_control_tests.service",
    logger_name="backend.sandbox.global_control_tests.service.instrumentation",
)
class GlobalControlTestService:
    def __init__(
        self,
        *,
        settings: Settings,
        database_pool: DatabasePool,
        cache: CacheManager | NullCacheManager,
    ):
        self._settings = settings
        self._pool = database_pool
        self._cache = cache
        self._repo = GlobalControlTestRepository()

    async def _require_sandbox_permission(
        self, conn, *, user_id: str, permission_code: str, org_id: str
    ) -> None:
        await require_permission(conn, user_id, permission_code, scope_org_id=org_id)

    # ── publish ──────────────────────────────────────────────────────

    async def publish_control_test(
        self,
        request: PublishGlobalControlTestRequest,
        org_id: str,
        user_id: str,
    ) -> GlobalControlTestResponse:
        async with self._pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn, user_id=user_id, permission_code="sandbox.promote", org_id=org_id
            )

            # 1. Load source signal
            signal_row = await conn.fetchrow(
                f'SELECT * FROM {SCHEMA}."22_fct_signals" WHERE id = $1 AND is_deleted = FALSE',
                request.source_signal_id,
            )
            if not signal_row:
                raise NotFoundError("Source signal not found")

            # 2. Load signal properties
            prop_rows = await conn.fetch(
                f'SELECT property_key, property_value FROM {SCHEMA}."45_dtl_signal_properties" WHERE signal_id = $1',
                request.source_signal_id,
            )
            signal_props = {r["property_key"]: r["property_value"] for r in prop_rows}

            # 3. Load connector types
            ct_rows = await conn.fetch(
                f'SELECT connector_type_code FROM {SCHEMA}."50_lnk_signal_connector_types" WHERE signal_id = $1',
                request.source_signal_id,
            )
            connector_type_codes = [r["connector_type_code"] for r in ct_rows]
            connector_type_code = (
                connector_type_codes[0] if connector_type_codes else None
            )

            # Fallback: check EAV property 'connector_types'
            if not connector_type_code and signal_props.get("connector_types"):
                ct_csv = signal_props["connector_types"]
                connector_type_codes = [
                    c.strip() for c in ct_csv.split(",") if c.strip()
                ]
                connector_type_code = (
                    connector_type_codes[0] if connector_type_codes else None
                )

            # Fallback: infer from signal_spec's asset_types or connector_type_code
            if not connector_type_code and signal_props.get("signal_spec"):
                try:
                    import json as _json

                    spec = _json.loads(signal_props["signal_spec"])
                    spec_ct = spec.get("connector_type_code", "")
                    if spec_ct and spec_ct != "generic":
                        connector_type_code = spec_ct
                        connector_type_codes = [spec_ct]
                    # Infer from asset_types (e.g., github_repo → github)
                    if not connector_type_code:
                        asset_types = spec.get("asset_types", [])
                        for at in asset_types:
                            prefix = at.split("_")[0] if "_" in at else at
                            if prefix in (
                                "github",
                                "aws",
                                "azure",
                                "gcp",
                                "kubernetes",
                            ):
                                connector_type_code = prefix
                                connector_type_codes = [prefix]
                                break
                except Exception:
                    pass

            # Fallback: infer from connector linked to org
            if not connector_type_code:
                conn_row = await conn.fetchrow(
                    f'SELECT connector_type_code FROM {SCHEMA}."20_fct_connector_instances" WHERE org_id = $1::uuid AND is_deleted = FALSE LIMIT 1',
                    org_id,
                )
                if conn_row:
                    connector_type_code = conn_row["connector_type_code"]
                    connector_type_codes = [connector_type_code]

            if not connector_type_code:
                raise ValidationError(
                    "Could not determine connector type. Ensure the signal has a linked connector or signal spec with asset_types."
                )

            # 4. Build signal bundle
            signal_bundle = SignalBundle(
                signal_code=signal_row["signal_code"],
                name=signal_props.get("name", signal_row["signal_code"]),
                description=signal_props.get("description", ""),
                python_source=signal_props.get("python_source", ""),
                connector_type_codes=connector_type_codes,
                timeout_ms=signal_row["timeout_ms"],
                max_memory_mb=signal_row["max_memory_mb"],
                source_prompt=signal_props.get("source_prompt"),
            )

            # 5. Find linked threat type (searches for any threat type that references this signal)
            threat_bundle = None
            policy_bundle = None
            source_policy_id = None

            threat_rows = await conn.fetch(
                f"""
                SELECT tt.* FROM {SCHEMA}."23_fct_threat_types" tt
                WHERE tt.org_id = $1 AND tt.is_deleted = FALSE AND tt.is_active = TRUE
                  AND tt.expression_tree::text LIKE '%' || $2 || '%'
                ORDER BY tt.created_at DESC LIMIT 1
                """,
                signal_row["org_id"],
                signal_row["signal_code"],
            )
            if threat_rows:
                tt = threat_rows[0]
                tt_props = await conn.fetch(
                    f'SELECT property_key, property_value FROM {SCHEMA}."46_dtl_threat_type_properties" WHERE threat_type_id = $1',
                    tt["id"],
                )
                tt_props_dict = {
                    r["property_key"]: r["property_value"] for r in tt_props
                }
                expr_tree = tt["expression_tree"]
                if isinstance(expr_tree, str):
                    expr_tree = json.loads(expr_tree)

                threat_bundle = ThreatTypeBundle(
                    threat_code=tt["threat_code"],
                    name=tt_props_dict.get("name", tt["threat_code"]),
                    description=tt_props_dict.get("description", ""),
                    severity_code=tt["severity_code"],
                    expression_tree=expr_tree if isinstance(expr_tree, dict) else {},
                    mitigation_guidance=tt_props_dict.get("mitigation_guidance"),
                )

                # 6. Find linked policy for this threat type
                policy_rows = await conn.fetch(
                    f"""
                    SELECT p.* FROM {SCHEMA}."24_fct_policies" p
                    WHERE p.threat_type_id = $1 AND p.is_deleted = FALSE AND p.is_active = TRUE
                    ORDER BY p.created_at DESC LIMIT 1
                    """,
                    tt["id"],
                )
                if policy_rows:
                    pol = policy_rows[0]
                    source_policy_id = str(pol["id"])
                    pol_props = await conn.fetch(
                        f'SELECT property_key, property_value FROM {SCHEMA}."47_dtl_policy_properties" WHERE policy_id = $1',
                        pol["id"],
                    )
                    pol_props_dict = {
                        r["property_key"]: r["property_value"] for r in pol_props
                    }
                    actions = pol["actions"]
                    if isinstance(actions, str):
                        actions = json.loads(actions)

                    policy_bundle = PolicyBundle(
                        policy_code=pol["policy_code"],
                        name=pol_props_dict.get("name", pol["policy_code"]),
                        description=pol_props_dict.get("description", ""),
                        actions=actions if isinstance(actions, list) else [],
                        cooldown_minutes=pol["cooldown_minutes"],
                    )

            # 7. Load test dataset (linked via signal property 'test_dataset_id')
            test_dataset_bundle = None
            dataset_template_bundle = None
            test_dataset_id = signal_props.get("test_dataset_id")

            if test_dataset_id:
                td_rows = await conn.fetch(
                    f"""SELECT record_name, description, record_data
                        FROM {SCHEMA}."43_dtl_dataset_records"
                        WHERE dataset_id = $1::uuid
                        ORDER BY record_seq""",
                    test_dataset_id,
                )
                td_props_rows = await conn.fetch(
                    f"""SELECT property_key, property_value
                        FROM {SCHEMA}."42_dtl_dataset_properties"
                        WHERE dataset_id = $1::uuid""",
                    test_dataset_id,
                )
                td_props = {
                    r["property_key"]: r["property_value"] for r in td_props_rows
                }
                td_fact = await conn.fetchrow(
                    f'SELECT dataset_code, row_count FROM {SCHEMA}."21_fct_datasets" WHERE id = $1::uuid',
                    test_dataset_id,
                )
                td_records = []
                for tr in td_rows:
                    rd = tr["record_data"]
                    if isinstance(rd, str):
                        rd = json.loads(rd)
                    td_records.append(
                        TestDatasetRecord(
                            record_name=tr["record_name"],
                            description=tr["description"],
                            record_data=rd if isinstance(rd, dict) else {},
                            expected_result=rd.get("_expected_result")
                            if isinstance(rd, dict)
                            else None,
                            scenario_name=rd.get("_scenario_name")
                            if isinstance(rd, dict)
                            else None,
                        )
                    )
                json_schema_raw = td_props.get("json_schema")
                json_schema = json.loads(json_schema_raw) if json_schema_raw else None
                test_dataset_bundle = TestDatasetBundle(
                    dataset_code=td_fact["dataset_code"]
                    if td_fact
                    else f"test_{signal_row['signal_code']}",
                    name=td_props.get("name", ""),
                    description=td_props.get("description", ""),
                    record_count=td_fact["row_count"] if td_fact else len(td_records),
                    records=td_records,
                    json_schema=json_schema if isinstance(json_schema, dict) else None,
                )

            # 8. Build dataset template from source dataset (schema + sample records)
            source_dataset_id = signal_props.get("source_dataset_id")
            if not source_dataset_id and request.linked_dataset_code:
                # Try to find source dataset by code in same org
                ds_row = await conn.fetchrow(
                    f"""SELECT id::text FROM {SCHEMA}."21_fct_datasets"
                        WHERE org_id = $1 AND dataset_code = $2 AND is_active = TRUE
                        ORDER BY version_number DESC LIMIT 1""",
                    signal_row["org_id"],
                    request.linked_dataset_code,
                )
                if ds_row:
                    source_dataset_id = ds_row["id"]

            if source_dataset_id:
                ds_props_rows = await conn.fetch(
                    f"""SELECT property_key, property_value
                        FROM {SCHEMA}."42_dtl_dataset_properties"
                        WHERE dataset_id = $1::uuid""",
                    source_dataset_id,
                )
                ds_props = {
                    r["property_key"]: r["property_value"] for r in ds_props_rows
                }
                sample_rows = await conn.fetch(
                    f"""SELECT record_data
                        FROM {SCHEMA}."43_dtl_dataset_records"
                        WHERE dataset_id = $1::uuid
                        ORDER BY record_seq LIMIT 3""",
                    source_dataset_id,
                )
                sample_records = []
                for sr in sample_rows:
                    rd = sr["record_data"]
                    if isinstance(rd, str):
                        rd = json.loads(rd)
                    if isinstance(rd, dict):
                        sample_records.append(rd)

                schema_raw = ds_props.get("json_schema")
                ds_schema = json.loads(schema_raw) if schema_raw else {}
                if not ds_schema and sample_records:
                    # Auto-derive schema from first sample record
                    ds_schema = {
                        k: type(v).__name__ for k, v in sample_records[0].items()
                    }

                dataset_template_bundle = DatasetTemplateBundle(
                    connector_type_code=connector_type_code or "",
                    json_schema=ds_schema if isinstance(ds_schema, dict) else {},
                    sample_records=sample_records,
                    field_count=len(ds_schema) if isinstance(ds_schema, dict) else 0,
                )

            # 9. Build complete bundle
            bundle = ControlTestBundle(
                signals=[signal_bundle],
                threat_type=threat_bundle,
                policy=policy_bundle,
                test_dataset=test_dataset_bundle,
                dataset_template=dataset_template_bundle,
            )

            # 10. Determine version
            max_ver = await self._repo.get_max_version(conn, request.global_code)
            new_version = max_ver + 1

            # 11. Insert
            test_id = str(uuid.uuid4())
            await self._repo.create(
                conn,
                test_id=test_id,
                global_code=request.global_code,
                connector_type_code=connector_type_code,
                version_number=new_version,
                bundle=bundle.model_dump(),
                source_signal_id=request.source_signal_id,
                source_policy_id=source_policy_id,
                source_library_id=None,
                source_org_id=org_id,
                linked_dataset_code=request.linked_dataset_code,
                signal_count=len(bundle.signals),
                published_by=user_id,
            )

            # 12. Set properties
            props = dict(request.properties)
            if "name" not in props:
                props["name"] = signal_props.get("name", signal_bundle.signal_code)
            if "description" not in props:
                props["description"] = signal_props.get("description", "")
            if props:
                await self._repo.set_properties(conn, test_id, props)

            await self._cache.delete(f"{_CACHE_PREFIX}:list")
            await self._cache.delete(f"{_CACHE_PREFIX}:stats")

            rec = await self._repo.get_by_id(conn, test_id)
            if not rec:
                raise NotFoundError("Failed to read back published test")
            return _record_to_response(rec)

    # ── list ─────────────────────────────────────────────────────────

    async def list_tests(
        self,
        *,
        connector_type_code: str | None = None,
        category: str | None = None,
        search: str | None = None,
        linked_dataset_code: str | None = None,
        publish_status: str | None = None,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        limit: int = 100,
        offset: int = 0,
    ) -> GlobalControlTestListResponse:
        async with self._pool.acquire() as conn:
            records, total = await self._repo.list_tests(
                conn,
                connector_type_code=connector_type_code,
                category=category,
                search=search,
                linked_dataset_code=linked_dataset_code,
                publish_status=publish_status,
                sort_by=sort_by,
                sort_dir=sort_dir,
                limit=limit,
                offset=offset,
            )
            return GlobalControlTestListResponse(
                items=[_record_to_response(r) for r in records],
                total=total,
            )

    # ── get ───────────────────────────────────────────────────────────

    async def get_test(self, test_id: str) -> GlobalControlTestResponse:
        async with self._pool.acquire() as conn:
            rec = await self._repo.get_by_id(conn, test_id)
            if not rec:
                raise NotFoundError("Global control test not found")
            return _record_to_response(rec)

    # ── update ───────────────────────────────────────────────────────

    async def update_test(
        self,
        test_id: str,
        request: UpdateGlobalControlTestRequest,
        user_id: str,
        org_id: str,
    ) -> GlobalControlTestResponse:
        async with self._pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn, user_id=user_id, permission_code="sandbox.promote", org_id=org_id
            )
            rec = await self._repo.get_by_id(conn, test_id)
            if not rec:
                raise NotFoundError("Global control test not found")
            if request.properties:
                await self._repo.set_properties(conn, test_id, request.properties)
            if request.is_featured is not None:
                await self._repo.update_metadata(
                    conn, test_id, is_featured=request.is_featured
                )
            await self._cache.delete(f"{_CACHE_PREFIX}:list")
            await self._cache.delete(f"{_CACHE_PREFIX}:stats")
            updated = await self._repo.get_by_id(conn, test_id)
            return _record_to_response(updated)  # type: ignore[arg-type]

    # ── deprecate ────────────────────────────────────────────────────

    async def deprecate_test(
        self, test_id: str, user_id: str, org_id: str
    ) -> GlobalControlTestResponse:
        async with self._pool.acquire() as conn:
            await self._require_sandbox_permission(
                conn, user_id=user_id, permission_code="sandbox.promote", org_id=org_id
            )
            rec = await self._repo.get_by_id(conn, test_id)
            if not rec:
                raise NotFoundError("Global control test not found")
            await self._repo.update_metadata(conn, test_id, publish_status="deprecated")
            await self._cache.delete(f"{_CACHE_PREFIX}:list")
            await self._cache.delete(f"{_CACHE_PREFIX}:stats")
            updated = await self._repo.get_by_id(conn, test_id)
            return _record_to_response(updated)  # type: ignore[arg-type]

    # ── deploy to workspace ──────────────────────────────────────────

    async def deploy_to_workspace(
        self,
        test_id: str,
        org_id: str,
        workspace_id: str,
        connector_instance_id: str | None,
        user_id: str,
    ) -> DeployResultResponse:
        async with self._pool.acquire() as conn:
            # 1. Load global test
            rec = await self._repo.get_by_id(conn, test_id)
            if not rec:
                raise NotFoundError("Global control test not found")

            bundle_data = (
                json.loads(rec.bundle) if isinstance(rec.bundle, str) else rec.bundle
            )
            bundle = ControlTestBundle(**bundle_data)

            created_signal_ids: list[str] = []
            created_threat_id: str | None = None
            created_policy_id: str | None = None

            # 2. Create signals
            for sig in bundle.signals:
                signal_id = str(uuid.uuid4())
                python_hash = hashlib.sha256(sig.python_source.encode()).hexdigest()

                # Check for code conflict, append suffix if needed
                signal_code = sig.signal_code
                existing = await conn.fetchrow(
                    f'SELECT id FROM {SCHEMA}."22_fct_signals" WHERE org_id = $1::uuid AND signal_code = $2 AND is_deleted = FALSE',
                    org_id,
                    signal_code,
                )
                if existing:
                    signal_code = f"{signal_code}_{str(uuid.uuid4())[:8]}"

                await conn.execute(
                    f"""
                    INSERT INTO {SCHEMA}."22_fct_signals"
                        (id, tenant_key, org_id, workspace_id, signal_code, version_number,
                         signal_status_code, python_hash, timeout_ms, max_memory_mb,
                         is_active, created_by, updated_by)
                    VALUES ($1::uuid, 'default', $2::uuid, $3::uuid, $4, 1, 'validated', $5, $6, $7, TRUE, $8::uuid, $8::uuid)
                    """,
                    signal_id,
                    org_id,
                    workspace_id,
                    signal_code,
                    python_hash,
                    sig.timeout_ms,
                    sig.max_memory_mb,
                    user_id,
                )

                # Signal properties
                sig_props = {
                    "name": sig.name,
                    "description": sig.description,
                    "python_source": sig.python_source,
                    "global_test_id": rec.id,
                    "global_test_code": rec.global_code,
                    "global_test_version": str(rec.version_number),
                    "deploy_source": "global_library",
                }
                if sig.source_prompt:
                    sig_props["source_prompt"] = sig.source_prompt
                if sig.connector_type_codes:
                    sig_props["connector_types"] = ",".join(sig.connector_type_codes)

                for key, value in sig_props.items():
                    prop_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."45_dtl_signal_properties" (id, signal_id, property_key, property_value, created_by, updated_by)
                        VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $5::uuid)
                        """,
                        prop_id,
                        signal_id,
                        key,
                        value,
                        user_id,
                    )

                # Connector type links
                for ct_code in sig.connector_type_codes:
                    link_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."50_lnk_signal_connector_types" (id, signal_id, connector_type_code)
                        VALUES ($1::uuid, $2::uuid, $3)
                        ON CONFLICT (signal_id, connector_type_code) DO NOTHING
                        """,
                        link_id,
                        signal_id,
                        ct_code,
                    )

                created_signal_ids.append(signal_id)

            # 3. Create threat type
            if bundle.threat_type:
                tt = bundle.threat_type
                threat_id = str(uuid.uuid4())
                threat_code = tt.threat_code
                existing_tt = await conn.fetchrow(
                    f'SELECT id FROM {SCHEMA}."23_fct_threat_types" WHERE org_id = $1::uuid AND threat_code = $2 AND is_deleted = FALSE',
                    org_id,
                    threat_code,
                )
                if existing_tt:
                    threat_code = f"{threat_code}_{str(uuid.uuid4())[:8]}"

                await conn.execute(
                    f"""
                    INSERT INTO {SCHEMA}."23_fct_threat_types"
                        (id, tenant_key, org_id, workspace_id, threat_code, version_number,
                         severity_code, expression_tree, is_active, created_by, updated_by)
                    VALUES ($1::uuid, 'default', $2::uuid, $3::uuid, $4, 1, $5, $6::jsonb, TRUE, $7::uuid, $7::uuid)
                    """,
                    threat_id,
                    org_id,
                    workspace_id,
                    threat_code,
                    tt.severity_code,
                    json.dumps(tt.expression_tree),
                    user_id,
                )

                tt_props = {
                    "name": tt.name,
                    "description": tt.description,
                    "global_test_id": rec.id,
                    "deploy_source": "global_library",
                }
                if tt.mitigation_guidance:
                    tt_props["mitigation_guidance"] = tt.mitigation_guidance

                for key, value in tt_props.items():
                    prop_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."46_dtl_threat_type_properties" (id, threat_type_id, property_key, property_value, created_by, updated_by)
                        VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $5::uuid)
                        """,
                        prop_id,
                        threat_id,
                        key,
                        value,
                        user_id,
                    )

                created_threat_id = threat_id

                # 4. Create policy
                if bundle.policy:
                    pol = bundle.policy
                    policy_id = str(uuid.uuid4())
                    policy_code = pol.policy_code
                    existing_pol = await conn.fetchrow(
                        f'SELECT id FROM {SCHEMA}."24_fct_policies" WHERE org_id = $1::uuid AND policy_code = $2 AND is_deleted = FALSE',
                        org_id,
                        policy_code,
                    )
                    if existing_pol:
                        policy_code = f"{policy_code}_{str(uuid.uuid4())[:8]}"

                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."24_fct_policies"
                            (id, tenant_key, org_id, workspace_id, policy_code, version_number,
                             threat_type_id, actions, is_enabled, cooldown_minutes,
                             is_active, created_by, updated_by)
                        VALUES ($1::uuid, 'default', $2::uuid, $3::uuid, $4, 1, $5::uuid, $6::jsonb, TRUE, $7, TRUE, $8::uuid, $8::uuid)
                        """,
                        policy_id,
                        org_id,
                        workspace_id,
                        policy_code,
                        threat_id,
                        json.dumps(pol.actions),
                        pol.cooldown_minutes,
                        user_id,
                    )

                    pol_props = {
                        "name": pol.name,
                        "description": pol.description,
                        "global_test_id": rec.id,
                        "deploy_source": "global_library",
                    }
                    for key, value in pol_props.items():
                        prop_id = str(uuid.uuid4())
                        await conn.execute(
                            f"""
                            INSERT INTO {SCHEMA}."47_dtl_policy_properties" (id, policy_id, property_key, property_value, created_by, updated_by)
                            VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $5::uuid)
                            """,
                            prop_id,
                            policy_id,
                            key,
                            value,
                            user_id,
                        )

                    created_policy_id = policy_id

            # 5. Create test dataset from bundle
            created_test_dataset_id: str | None = None
            if bundle.test_dataset and bundle.test_dataset.records:
                td = bundle.test_dataset
                test_ds_id = str(uuid.uuid4())
                test_ds_code = f"global_{td.dataset_code}"

                # Check for code conflict
                existing_ds = await conn.fetchrow(
                    f'SELECT id FROM {SCHEMA}."21_fct_datasets" WHERE org_id = $1::uuid AND dataset_code = $2 AND is_active = TRUE',
                    org_id,
                    test_ds_code,
                )
                if existing_ds:
                    test_ds_code = f"{test_ds_code}_{str(uuid.uuid4())[:8]}"

                await conn.execute(
                    f"""
                    INSERT INTO {SCHEMA}."21_fct_datasets"
                        (id, tenant_key, org_id, workspace_id, dataset_code, version_number,
                         dataset_source_code, row_count, is_locked, is_active,
                         created_by, updated_by)
                    VALUES ($1::uuid, 'default', $2::uuid, $3::uuid, $4, 1,
                            'global_library', $5, TRUE, TRUE,
                            $6::uuid, $6::uuid)
                    """,
                    test_ds_id,
                    org_id,
                    workspace_id,
                    test_ds_code,
                    len(td.records),
                    user_id,
                )

                # Dataset properties
                ds_props = {
                    "name": td.name or f"Test dataset for {rec.global_code}",
                    "description": td.description
                    or f"Test dataset deployed from global library {rec.global_code}",
                    "is_ai_test_dataset": "true",
                    "global_test_id": rec.id,
                    "global_test_code": rec.global_code,
                    "deploy_source": "global_library",
                }
                if td.json_schema:
                    ds_props["json_schema"] = json.dumps(td.json_schema)
                # Link to first created signal
                if created_signal_ids:
                    ds_props["linked_signal_id"] = created_signal_ids[0]

                for key, value in ds_props.items():
                    prop_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."42_dtl_dataset_properties"
                            (id, dataset_id, property_key, property_value, created_by, updated_by)
                        VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $5::uuid)
                        """,
                        prop_id,
                        test_ds_id,
                        key,
                        value,
                        user_id,
                    )

                # Insert test records
                for seq, tr in enumerate(td.records):
                    rec_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."43_dtl_dataset_records"
                            (id, dataset_id, record_seq, record_data)
                        VALUES ($1::uuid, $2::uuid, $3, $4::jsonb)
                        """,
                        rec_id,
                        test_ds_id,
                        seq,
                        json.dumps(
                            {
                                **tr.record_data,
                                "_record_name": tr.record_name,
                                "_description": tr.description,
                            }
                        ),
                    )

                created_test_dataset_id = test_ds_id

                # Link test dataset to signal
                if created_signal_ids:
                    prop_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."45_dtl_signal_properties"
                            (id, signal_id, property_key, property_value, created_by, updated_by)
                        VALUES ($1::uuid, $2::uuid, 'test_dataset_id', $3, $4::uuid, $4::uuid)
                        """,
                        prop_id,
                        created_signal_ids[0],
                        test_ds_id,
                        user_id,
                    )

            # 6. Create dataset template from bundle
            created_dataset_template_id: str | None = None
            if bundle.dataset_template and bundle.dataset_template.sample_records:
                dt = bundle.dataset_template
                template_ds_id = str(uuid.uuid4())
                template_ds_code = f"template_{rec.global_code}"

                existing_tpl = await conn.fetchrow(
                    f'SELECT id FROM {SCHEMA}."21_fct_datasets" WHERE org_id = $1::uuid AND dataset_code = $2 AND is_active = TRUE',
                    org_id,
                    template_ds_code,
                )
                if existing_tpl:
                    template_ds_code = f"{template_ds_code}_{str(uuid.uuid4())[:8]}"

                await conn.execute(
                    f"""
                    INSERT INTO {SCHEMA}."21_fct_datasets"
                        (id, tenant_key, org_id, workspace_id, dataset_code, version_number,
                         dataset_source_code, row_count, is_locked, is_active,
                         created_by, updated_by)
                    VALUES ($1::uuid, 'default', $2::uuid, $3::uuid, $4, 1,
                            'global_library', $5, TRUE, TRUE,
                            $6::uuid, $6::uuid)
                    """,
                    template_ds_id,
                    org_id,
                    workspace_id,
                    template_ds_code,
                    len(dt.sample_records),
                    user_id,
                )

                tpl_props = {
                    "name": f"Dataset template for {rec.global_code}",
                    "description": f"Data schema template from global library — shows expected record shape",
                    "connector_type_code": dt.connector_type_code,
                    "global_test_id": rec.id,
                    "deploy_source": "global_library",
                }
                if dt.json_schema:
                    tpl_props["json_schema"] = json.dumps(dt.json_schema)

                for key, value in tpl_props.items():
                    prop_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."42_dtl_dataset_properties"
                            (id, dataset_id, property_key, property_value, created_by, updated_by)
                        VALUES ($1::uuid, $2::uuid, $3, $4, $5::uuid, $5::uuid)
                        """,
                        prop_id,
                        template_ds_id,
                        key,
                        value,
                        user_id,
                    )

                for seq, sample in enumerate(dt.sample_records):
                    rec_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."43_dtl_dataset_records"
                            (id, dataset_id, record_seq, record_data)
                        VALUES ($1::uuid, $2::uuid, $3, $4::jsonb)
                        """,
                        rec_id,
                        template_ds_id,
                        seq,
                        json.dumps({**sample, "_record_name": f"sample_{seq}"}),
                    )

                created_dataset_template_id = template_ds_id

            # 7. Record deployment
            pull_id = str(uuid.uuid4())
            await self._repo.record_pull(
                conn,
                pull_id=pull_id,
                global_test_id=test_id,
                pulled_version=rec.version_number,
                target_org_id=org_id,
                target_workspace_id=workspace_id,
                deploy_type="workspace",
                created_signal_ids=created_signal_ids,
                created_threat_id=created_threat_id,
                created_policy_id=created_policy_id,
                pulled_by=user_id,
            )
            await self._repo.increment_download_count(conn, test_id)

            # 8. Create promoted test record (so it appears on kcontrol Tests page)
            promoted_test_id = str(uuid.uuid4())
            promoted_test_code = f"gl_{rec.global_code}"
            # Root Cause: The DB constraint is (tenant_key, test_code, version_number).
            # The previous check was scoped to org_id and is_deleted=FALSE, causing 500 errors
            # when another org in the same tenant (default) had already used the code.
            existing_pt = await conn.fetchrow(
                f'SELECT id FROM {SCHEMA}."35_fct_promoted_tests" WHERE tenant_key = $1 AND test_code = $2 AND version_number = 1',
                "default",
                promoted_test_code,
            )
            if existing_pt:
                promoted_test_code = f"{promoted_test_code}_{str(uuid.uuid4())[:8]}"

            await conn.execute(
                f"""
                INSERT INTO {SCHEMA}."35_fct_promoted_tests" (
                    id, tenant_key, org_id, workspace_id,
                    promotion_id, source_signal_id, source_policy_id, source_library_id,
                    test_code, test_type_code, monitoring_frequency,
                    linked_asset_id, version_number, is_active,
                    promoted_by, promoted_at, created_at, updated_at
                ) VALUES (
                    $1::uuid, 'default', $2::uuid, $8::uuid,
                    NULL, $3::uuid, $4::uuid, NULL,
                    $5, 'automated', 'on_collection',
                    $6::uuid, 1, TRUE,
                    $7::uuid, NOW(), NOW(), NOW()
                )
                """,
                promoted_test_id,
                org_id,
                created_signal_ids[0] if created_signal_ids else None,
                created_policy_id,
                promoted_test_code,
                connector_instance_id,
                user_id,
                workspace_id,
            )

            # Promoted test properties
            pt_props = {
                "name": rec.name or rec.global_code,
                "description": rec.description or "",
                "global_test_id": rec.id,
                "global_test_code": rec.global_code,
                "deploy_source": "global_library",
                "connector_type_code": rec.connector_type_code,
            }

            # Map signal properties to test properties (required for execution/engine)
            if bundle.signals:
                first_sig = bundle.signals[0]
                pt_props["evaluation_rule"] = first_sig.python_source
                if first_sig.connector_type_codes:
                    pt_props["signal_type"] = first_sig.connector_type_codes[0]
                if first_sig.source_prompt:
                    pt_props["integration_guide"] = first_sig.source_prompt

            for key, value in pt_props.items():
                if value:
                    await conn.execute(
                        f"""
                        INSERT INTO {SCHEMA}."36_dtl_promoted_test_properties"
                            (test_id, property_key, property_value, created_by, created_at, updated_at)
                        VALUES ($1::uuid, $2, $3, $4::uuid, NOW(), NOW())
                        ON CONFLICT (test_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                        """,
                        promoted_test_id,
                        key,
                        value,
                        user_id,
                    )

            # 9. Invalidate caches
            await self._cache.delete(f"sb:signals:{org_id}")
            await self._cache.delete(f"sb:threats:{org_id}")
            await self._cache.delete(f"sb:policies:{org_id}")
            await self._cache.delete(f"sb:datasets:{org_id}")

            return DeployResultResponse(
                created_signal_ids=created_signal_ids,
                created_threat_type_id=created_threat_id,
                created_policy_id=created_policy_id,
                created_test_dataset_id=created_test_dataset_id,
                created_dataset_template_id=created_dataset_template_id,
                promoted_test_id=promoted_test_id,
                signal_count=len(created_signal_ids),
                global_source_code=rec.global_code,
                global_source_version=rec.version_number,
            )

    # ── deployed test ids ────────────────────────────────────────────

    async def list_deployed_ids(
        self,
        *,
        org_id: str,
        workspace_id: str | None = None,
    ) -> list[str]:
        async with self._pool.acquire() as conn:
            return await self._repo.list_deployed_global_test_ids(
                conn,
                org_id=org_id,
                workspace_id=workspace_id,
            )

    # ── stats ────────────────────────────────────────────────────────

    async def get_stats(self) -> GlobalControlTestStatsResponse:
        async with self._pool.acquire() as conn:
            data = await self._repo.get_stats(conn)
            return GlobalControlTestStatsResponse(**data)
