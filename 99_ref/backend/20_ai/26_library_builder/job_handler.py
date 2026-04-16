"""
Job handler for library_builder jobs.

Input JSON:
  threat_type_ids — list of threat type UUIDs to bundle
  org_id
  workspace_id
  library_name    — optional override for the library name

Flow (policies-first):
  1. Group threat types by connector_type_code
  2. For each group:
     a. Create policies wrapping each threat type (action: alert, cooldown: 1h)
        — ON CONFLICT: use existing policy (idempotent)
     b. Create library for the group
     c. Link all policies to the library (with sort_order)
"""

from __future__ import annotations

import json
import uuid
from importlib import import_module

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.library_builder.job_handler")

_THREAT_TYPES = '"15_sandbox"."23_fct_threat_types"'
_THREAT_PROPS = '"15_sandbox"."46_dtl_threat_type_properties"'
_POLICIES = '"15_sandbox"."24_fct_policies"'
_POLICY_PROPS = '"15_sandbox"."47_dtl_policy_properties"'
_LIBRARIES = '"15_sandbox"."29_fct_libraries"'
_LIBRARY_PROPS = '"15_sandbox"."48_dtl_library_properties"'
_LIBRARY_POLICIES = '"15_sandbox"."51_lnk_library_policies"'


async def handle_library_builder_job(job, pool, settings) -> None:
    inp = job.input_json
    threat_type_ids = inp.get("threat_type_ids", [])
    org_id = getattr(job, "org_id", None) or inp.get("org_id")
    workspace_id = getattr(job, "workspace_id", None) or inp.get("workspace_id")
    tenant_key = getattr(job, "tenant_key", None) or inp.get("tenant_key", "")
    user_id = getattr(job, "user_id", None) or inp.get("user_id")
    library_name_override = inp.get("library_name")

    _logger.info(
        "library_builder.starting",
        extra={"threat_type_count": len(threat_type_ids)},
    )

    # Load threat type metadata + group by connector type
    threat_types = await _load_threat_types(pool, threat_type_ids, tenant_key)
    if not threat_types:
        raise ValueError("No threat types found")

    # Group by connector type
    groups: dict[str, list[dict]] = {}
    for tt in threat_types:
        connector = tt.get("connector_type_code") or "unknown"
        groups.setdefault(connector, []).append(tt)

    libraries_created = []
    policies_created = 0

    for connector_type, group_threats in groups.items():
        try:
            lib_name = library_name_override or f"AI Control Library — {connector_type.replace('_', ' ').title()}"
            lib_id, policy_count = await _create_library_with_policies(
                pool=pool,
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=org_id,
                workspace_id=workspace_id,
                connector_type_code=connector_type,
                threat_types=group_threats,
                library_name=lib_name,
            )
            libraries_created.append({"library_id": lib_id, "connector_type": connector_type})
            policies_created += policy_count
        except Exception as exc:
            _logger.warning(
                "library_builder.group_failed",
                extra={"connector_type": connector_type, "error": str(exc)[:200]},
            )

    _logger.info(
        "library_builder.complete",
        extra={
            "libraries_created": len(libraries_created),
            "policies_created": policies_created,
        },
    )


async def _load_threat_types(pool, threat_type_ids: list, tenant_key: str) -> list[dict]:
    result = []
    for tt_id in threat_type_ids:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    f"""
                    SELECT t.id::text, t.threat_code,
                           p_name.property_value AS name,
                           p_desc.property_value AS description,
                           p_conn.property_value AS connector_type_code
                    FROM {_THREAT_TYPES} t
                    LEFT JOIN {_THREAT_PROPS} p_name
                        ON p_name.threat_type_id = t.id AND p_name.property_key = 'name'
                    LEFT JOIN {_THREAT_PROPS} p_desc
                        ON p_desc.threat_type_id = t.id AND p_desc.property_key = 'description'
                    LEFT JOIN {_THREAT_PROPS} p_conn
                        ON p_conn.threat_type_id = t.id AND p_conn.property_key = 'connector_type_code'
                    WHERE t.id = $1::uuid AND t.tenant_key = $2
                    """,
                    tt_id, tenant_key,
                )
            if row:
                result.append(dict(row))
        except Exception as exc:
            _logger.warning("library_builder.threat_load_failed: %s", exc)
    return result


async def _create_library_with_policies(
    pool, *, tenant_key: str, user_id: str, org_id: str, workspace_id: str,
    connector_type_code: str, threat_types: list[dict], library_name: str,
) -> tuple[str, int]:
    """Creates policies for each threat type then creates a library and links them."""
    policy_ids = []

    for tt in threat_types:
        try:
            policy_id = await _get_or_create_policy(
                pool=pool,
                tenant_key=tenant_key,
                user_id=user_id,
                org_id=org_id,
                workspace_id=workspace_id,
                threat_type=tt,
            )
            policy_ids.append(policy_id)
        except Exception as exc:
            _logger.warning(
                "library_builder.policy_create_failed",
                extra={"threat_code": tt.get("threat_type_code"), "error": str(exc)[:200]},
            )

    # Create library
    library_id = str(uuid.uuid4())
    library_code = f"ai_lib_{library_id[:8]}"

    async with pool.acquire() as conn:
        # Get library type dim
        lib_type_row = await conn.fetchrow(
            'SELECT id FROM "15_sandbox"."10_dim_library_types" WHERE code = $1',
            "control_test",
        )
        lib_type_id = lib_type_row["id"] if lib_type_row else None

        await conn.execute(
            f"""
            INSERT INTO {_LIBRARIES} (
                id, tenant_key, org_id, workspace_id,
                library_code, version_number,
                library_type_id, is_published, is_active,
                created_by, created_at, updated_at
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid,
                $5, 1,
                $6, false, true,
                $7::uuid, NOW(), NOW()
            )
            """,
            library_id, tenant_key, org_id, workspace_id,
            library_code, lib_type_id, user_id,
        )

        for key, val in [
            ("name", library_name),
            ("connector_type_code", connector_type_code),
            ("ai_generated", "true"),
        ]:
            await conn.execute(
                f"""
                INSERT INTO {_LIBRARY_PROPS} (library_id, property_key, property_value)
                VALUES ($1::uuid, $2, $3)
                ON CONFLICT (library_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                library_id, key, val,
            )

        # Link policies to library with sort_order
        for i, policy_id in enumerate(policy_ids):
            await conn.execute(
                f"""
                INSERT INTO {_LIBRARY_POLICIES} (library_id, policy_id, sort_order)
                VALUES ($1::uuid, $2::uuid, $3)
                ON CONFLICT DO NOTHING
                """,
                library_id, policy_id, i,
            )

    return library_id, len(policy_ids)


async def _get_or_create_policy(
    pool, *, tenant_key: str, user_id: str, org_id: str, workspace_id: str, threat_type: dict,
) -> str:
    """Create a policy wrapping a threat type, or return existing one (idempotent)."""
    threat_code = threat_type.get("threat_code", "")
    policy_code = f"{threat_code}_policy"
    policy_name = f"Alert: {threat_type.get('name', threat_code)}"

    async with pool.acquire() as conn:
        # Check if policy already exists for this threat type + org
        existing = await conn.fetchrow(
            f"""
            SELECT p.id::text FROM {_POLICIES} p
            WHERE p.tenant_key = $1 AND p.org_id = $2::uuid
              AND p.policy_code = $3
              AND p.is_active = true
              AND p.is_deleted = false
            ORDER BY p.version_number DESC
            LIMIT 1
            """,
            tenant_key, org_id, policy_code,
        )
        if existing:
            return existing["id"]

        # Get threat type fact id
        threat_row = await conn.fetchrow(
            f'SELECT id FROM {_THREAT_TYPES} WHERE id = $1::uuid',
            threat_type["id"],
        )
        if not threat_row:
            raise ValueError(f"Threat type {threat_type['id']} not found")

        policy_id = str(uuid.uuid4())
        actions = json.dumps([{
            "action_type": "notification",
            "config": {
                "channel": "in_app",
                "message": f"Threat detected: {threat_type.get('name', threat_code)}",
            },
        }])

        await conn.execute(
            f"""
            INSERT INTO {_POLICIES} (
                id, tenant_key, org_id, workspace_id,
                policy_code, version_number,
                threat_type_id, actions,
                is_enabled, cooldown_minutes, is_active, is_deleted,
                created_at, updated_at, created_by, updated_by, deleted_at, deleted_by
            ) VALUES (
                $1::uuid, $2, $3::uuid, $4::uuid,
                $5, 1,
                $6::uuid, $7::jsonb,
                false, 60, true, false,
                NOW(), NOW(), $8::uuid, $8::uuid, NULL, NULL
            )
            """,
            policy_id, tenant_key, org_id, workspace_id,
            policy_code, threat_type["id"],
            actions, user_id,
        )

        for key, val in [
            ("name", policy_name),
            ("ai_generated", "true"),
        ]:
            await conn.execute(
                f"""
                INSERT INTO {_POLICY_PROPS} (policy_id, property_key, property_value)
                VALUES ($1::uuid, $2, $3)
                ON CONFLICT (policy_id, property_key) DO UPDATE SET property_value = EXCLUDED.property_value
                """,
                policy_id, key, val,
            )

    return policy_id
