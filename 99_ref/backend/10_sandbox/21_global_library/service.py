"""
GlobalLibraryService — publish org libraries, subscribe orgs, clone-on-subscribe.
"""

from __future__ import annotations

import json
import uuid
from importlib import import_module

from .repository import GlobalLibraryRepository
from .schemas import (
    GlobalLibraryListResponse,
    GlobalLibraryResponse,
    PublishGlobalLibraryRequest,
    SubscribeRequest,
    SubscriptionListResponse,
    SubscriptionResponse,
)

_database_module = import_module("backend.01_core.database")
_logging_module = import_module("backend.01_core.logging_utils")
_errors_module = import_module("backend.01_core.errors")
_perm_check_module = import_module("backend.03_auth_manage._permission_check")

DatabasePool = _database_module.DatabasePool
get_logger = _logging_module.get_logger
NotFoundError = _errors_module.NotFoundError
ValidationError = _errors_module.ValidationError
require_permission = _perm_check_module.require_permission

_LIBS = '"15_sandbox"."29_fct_libraries"'
_LIB_PROPS = '"15_sandbox"."48_dtl_library_properties"'
_LIB_POLICIES = '"15_sandbox"."51_lnk_library_policies"'
_SIGNALS = '"15_sandbox"."22_fct_signals"'
_SIGNAL_PROPS = '"15_sandbox"."45_dtl_signal_properties"'
_THREAT_TYPES = '"15_sandbox"."23_fct_threat_types"'
_THREAT_PROPS = '"15_sandbox"."46_dtl_threat_type_properties"'
_POLICIES = '"15_sandbox"."24_fct_policies"'
_POLICY_PROPS = '"15_sandbox"."47_dtl_policy_properties"'
_CONN_TYPES = '"15_sandbox"."03_dim_connector_types"'


class GlobalLibraryService:
    def __init__(self, *, database_pool: DatabasePool) -> None:
        self._database_pool = database_pool
        self._repository = GlobalLibraryRepository()
        self._logger = get_logger("backend.sandbox.global_library")

    async def list_global_libraries(
        self,
        *,
        user_id: str,
        category_code: str | None = None,
        connector_type_code: str | None = None,
        is_featured: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> GlobalLibraryListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            rows, total = await self._repository.list_published(
                conn,
                category_code=category_code,
                connector_type_code=connector_type_code,
                is_featured=is_featured,
                search=search,
                page=page,
                page_size=page_size,
            )
        return GlobalLibraryListResponse(
            items=[_gl_response(r) for r in rows],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def publish_global_library(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        request: PublishGlobalLibraryRequest,
    ) -> GlobalLibraryResponse:
        """Publish an org library to the global catalog (platform admin only)."""
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.publish_global")

            # Verify source library exists and belongs to this org
            lib_row = await conn.fetchrow(
                f"""
                SELECT l.id::text, l.tenant_key
                FROM {_LIBS} l
                WHERE l.id = $1::uuid AND l.org_id = $2::uuid AND l.is_active = true
                """,
                request.source_library_id, org_id,
            )
            if not lib_row:
                raise NotFoundError(f"Library '{request.source_library_id}' not found in org '{org_id}'")

            # Load entities to extract connector types
            entities = await self._repository.load_source_library_entities(
                conn, source_library_id=request.source_library_id
            )

        connector_type_codes = list({
            s.get("connector_type_code") for s in entities["signals"]
            if s.get("connector_type_code")
        })

        global_library_id = str(uuid.uuid4())
        async with self._database_pool.acquire() as conn:
            await self._repository.create_global_library(
                conn,
                global_library_id=global_library_id,
                source_library_id=request.source_library_id,
                source_org_id=org_id,
                global_code=request.global_code,
                global_name=request.global_name,
                description=request.description,
                category_code=request.category_code,
                connector_type_codes=connector_type_codes,
                curator_user_id=user_id,
                is_featured=request.is_featured,
            )
            row = await self._repository.get_by_id(conn, global_library_id)

        self._logger.info(
            "global_library.published",
            extra={
                "global_library_id": global_library_id,
                "global_code": request.global_code,
                "signal_count": len(entities["signals"]),
            },
        )

        return _gl_response(row, entities=entities)

    async def subscribe(
        self,
        *,
        user_id: str,
        tenant_key: str,
        org_id: str,
        workspace_id: str,
        global_library_id: str,
        request: SubscribeRequest,
    ) -> SubscriptionResponse:
        """Subscribe an org to a global library — clones all entities locally."""
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.create")
            gl_row = await self._repository.get_by_id(conn, global_library_id)
            if not gl_row:
                raise NotFoundError(f"Global library '{global_library_id}' not found")
            if gl_row.get("publish_status") != "published":
                raise ValidationError("Global library is not published")

            entities = await self._repository.load_source_library_entities(
                conn, source_library_id=gl_row["source_library_id"]
            )

        # Clone-on-subscribe
        local_library_id = await self._clone_library(
            tenant_key=tenant_key,
            user_id=user_id,
            org_id=org_id,
            workspace_id=workspace_id,
            gl_row=gl_row,
            entities=entities,
        )

        async with self._database_pool.acquire() as conn:
            sub_id = await self._repository.create_subscription(
                conn,
                org_id=org_id,
                global_library_id=global_library_id,
                subscribed_by=user_id,
                subscribed_version=gl_row["version_number"],
                local_library_id=local_library_id,
                auto_update=request.auto_update,
            )
            await self._repository.increment_download_count(conn, global_library_id)

        self._logger.info(
            "global_library.subscribed",
            extra={
                "global_library_id": global_library_id,
                "org_id": org_id,
                "local_library_id": local_library_id,
            },
        )

        return SubscriptionResponse(
            id=sub_id,
            org_id=org_id,
            global_library_id=global_library_id,
            global_code=gl_row["global_code"],
            global_name=gl_row["global_name"],
            subscribed_version=gl_row["version_number"],
            latest_version=gl_row["version_number"],
            has_update=False,
            local_library_id=local_library_id,
            auto_update=request.auto_update,
            subscribed_at="",
        )

    async def list_subscriptions(
        self, *, user_id: str, org_id: str
    ) -> SubscriptionListResponse:
        async with self._database_pool.acquire() as conn:
            await require_permission(conn, user_id, "sandbox.view")
            rows = await self._repository.list_subscriptions(conn, org_id=org_id)
        return SubscriptionListResponse(
            items=[
                SubscriptionResponse(
                    id=r["id"],
                    org_id=r["org_id"],
                    global_library_id=r["global_library_id"],
                    global_code=r["global_code"],
                    global_name=r["global_name"],
                    subscribed_version=r["subscribed_version"],
                    latest_version=r["latest_version"],
                    has_update=r["latest_version"] > r["subscribed_version"],
                    local_library_id=r.get("local_library_id"),
                    auto_update=r["auto_update"],
                    subscribed_at=r["subscribed_at"],
                )
                for r in rows
            ]
        )

    async def _clone_library(
        self,
        *,
        tenant_key: str,
        user_id: str,
        org_id: str,
        workspace_id: str,
        gl_row: dict,
        entities: dict,
    ) -> str:
        """Clone all signals, threat types, policies into the org, then create a local library."""
        # Map: original signal_code → new signal_id (cloned)
        signal_code_map: dict[str, str] = {}

        async with self._database_pool.acquire() as conn:
            # 1. Clone signals
            for sig in entities["signals"]:
                new_signal_id = str(uuid.uuid4())
                new_code = sig["signal_code"]

                # Get connector type id
                connector_row = await conn.fetchrow(
                    f"SELECT id FROM {_CONN_TYPES} WHERE code = $1",
                    sig.get("connector_type_code", ""),
                )
                status_row = await conn.fetchrow(
                    'SELECT id FROM "15_sandbox"."04_dim_signal_statuses" WHERE code = $1',
                    "validated",
                )

                await conn.execute(
                    f"""
                    INSERT INTO {_SIGNALS} (
                        id, tenant_key, org_id, workspace_id,
                        signal_code, version_number,
                        signal_status_id, connector_type_id,
                        is_active, timeout_ms, max_memory_mb,
                        created_by, created_at, updated_at
                    ) VALUES (
                        $1::uuid, $2, $3::uuid, $4::uuid,
                        $5, 1, $6, $7,
                        true, 10000, 256,
                        $8::uuid, NOW(), NOW()
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    new_signal_id, tenant_key, org_id, workspace_id,
                    new_code, status_row["id"] if status_row else None,
                    connector_row["id"] if connector_row else None,
                    user_id,
                )

                # Copy EAV + mark as cloned
                props = [
                    ("name", sig.get("name") or new_code),
                    ("python_source", sig.get("python_source") or ""),
                    ("cloned_from_global", gl_row["id"]),
                    ("cloned_from_global_code", gl_row["global_code"]),
                ]
                if sig.get("signal_args_schema"):
                    props.append(("signal_args_schema", sig["signal_args_schema"]))

                for key, val in props:
                    if val:
                        await conn.execute(
                            f"""
                            INSERT INTO {_SIGNAL_PROPS} (signal_id, property_key, property_value)
                            VALUES ($1::uuid, $2, $3)
                            ON CONFLICT (signal_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                            """,
                            new_signal_id, key, val,
                        )

                signal_code_map[new_code] = new_signal_id

            # 2. Clone threat types
            tt_id_map: dict[str, str] = {}
            for tt in entities["threat_types"]:
                new_tt_id = str(uuid.uuid4())
                expression_tree = tt.get("expression_tree") or "{}"

                severity_row = await conn.fetchrow(
                    'SELECT id FROM "15_sandbox"."08_dim_threat_severities" WHERE code = $1',
                    "medium",
                )
                connector_row = await conn.fetchrow(
                    f"SELECT id FROM {_CONN_TYPES} WHERE code = $1",
                    tt.get("connector_type_code", ""),
                )

                await conn.execute(
                    f"""
                    INSERT INTO {_THREAT_TYPES} (
                        id, tenant_key, org_id, workspace_id,
                        threat_type_code, version_number,
                        threat_severity_id, connector_type_id,
                        expression_tree, is_active,
                        created_by, created_at, updated_at
                    ) VALUES (
                        $1::uuid, $2, $3::uuid, $4::uuid,
                        $5, 1, $6, $7,
                        $8::jsonb, true,
                        $9::uuid, NOW(), NOW()
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    new_tt_id, tenant_key, org_id, workspace_id,
                    tt["threat_type_code"], severity_row["id"] if severity_row else None,
                    connector_row["id"] if connector_row else None,
                    expression_tree,
                    user_id,
                )

                for key, val in [
                    ("name", tt.get("name") or tt["threat_type_code"]),
                    ("description", tt.get("description") or ""),
                    ("cloned_from_global", gl_row["id"]),
                ]:
                    if val:
                        await conn.execute(
                            f"""
                            INSERT INTO {_THREAT_PROPS} (threat_type_id, property_key, property_value)
                            VALUES ($1::uuid, $2, $3)
                            ON CONFLICT (threat_type_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                            """,
                            new_tt_id, key, val,
                        )

                tt_id_map[tt["id"]] = new_tt_id

            # 3. Clone policies
            policy_id_list = []
            for pol in entities["policies"]:
                new_pol_id = str(uuid.uuid4())
                original_tt_id = pol.get("threat_type_id")
                new_tt_id = tt_id_map.get(original_tt_id, original_tt_id)

                await conn.execute(
                    f"""
                    INSERT INTO {_POLICIES} (
                        id, tenant_key, org_id, workspace_id,
                        policy_code, version_number,
                        threat_type_id, actions,
                        is_enabled, is_active,
                        created_by, created_at, updated_at
                    ) VALUES (
                        $1::uuid, $2, $3::uuid, $4::uuid,
                        $5, 1, $6::uuid, $7::jsonb,
                        true, true,
                        $8::uuid, NOW(), NOW()
                    )
                    ON CONFLICT DO NOTHING
                    """,
                    new_pol_id, tenant_key, org_id, workspace_id,
                    pol["policy_code"], new_tt_id,
                    pol.get("actions") or "[]",
                    user_id,
                )

                for key, val in [
                    ("name", pol.get("name") or pol["policy_code"]),
                    ("cloned_from_global", gl_row["id"]),
                ]:
                    if val:
                        await conn.execute(
                            f"""
                            INSERT INTO {_POLICY_PROPS} (policy_id, property_key, property_value)
                            VALUES ($1::uuid, $2, $3)
                            ON CONFLICT (policy_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                            """,
                            new_pol_id, key, val,
                        )

                policy_id_list.append(new_pol_id)

            # 4. Create local library
            local_lib_id = str(uuid.uuid4())
            local_lib_code = f"global_clone_{local_lib_id[:8]}"

            lib_type_row = await conn.fetchrow(
                'SELECT id FROM "15_sandbox"."10_dim_library_types" WHERE code = $1',
                "control_test",
            )

            await conn.execute(
                f"""
                INSERT INTO {_LIBS} (
                    id, tenant_key, org_id, workspace_id,
                    library_code, version_number,
                    library_type_id, is_published, is_active,
                    created_by, created_at, updated_at
                ) VALUES (
                    $1::uuid, $2, $3::uuid, $4::uuid,
                    $5, 1, $6, false, true,
                    $7::uuid, NOW(), NOW()
                )
                """,
                local_lib_id, tenant_key, org_id, workspace_id,
                local_lib_code, lib_type_row["id"] if lib_type_row else None,
                user_id,
            )

            for key, val in [
                ("name", gl_row["global_name"]),
                ("cloned_from_global", gl_row["id"]),
                ("cloned_from_global_code", gl_row["global_code"]),
            ]:
                await conn.execute(
                    f"""
                    INSERT INTO {_LIB_PROPS} (library_id, property_key, property_value)
                    VALUES ($1::uuid, $2, $3)
                    ON CONFLICT (library_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                    """,
                    local_lib_id, key, val,
                )

            # Link policies to local library
            for i, pol_id in enumerate(policy_id_list):
                await conn.execute(
                    f"""
                    INSERT INTO {_LIB_POLICIES} (library_id, policy_id, sort_order)
                    VALUES ($1::uuid, $2::uuid, $3)
                    ON CONFLICT DO NOTHING
                    """,
                    local_lib_id, pol_id, i,
                )

        return local_lib_id


def _gl_response(row: dict, entities: dict | None = None) -> GlobalLibraryResponse:
    signal_count = len(entities["signals"]) if entities else 0
    threat_type_count = len(entities["threat_types"]) if entities else 0
    policy_count = len(entities["policies"]) if entities else 0
    return GlobalLibraryResponse(
        id=row["id"],
        global_code=row["global_code"],
        global_name=row["global_name"],
        description=row.get("description"),
        category_code=row.get("category_code"),
        connector_type_codes=row.get("connector_type_codes") or [],
        publish_status=row.get("publish_status", "published"),
        is_featured=row.get("is_featured", False),
        download_count=row.get("download_count", 0),
        version_number=row.get("version_number", 1),
        signal_count=signal_count,
        threat_type_count=threat_type_count,
        policy_count=policy_count,
        published_at=row.get("published_at"),
        created_at=row.get("created_at", ""),
        updated_at=row.get("updated_at", ""),
    )
