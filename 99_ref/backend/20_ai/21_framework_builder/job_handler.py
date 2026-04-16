"""
Job handlers for background Phase 3 jobs:
  - framework_build: write approved proposal to DB
  - framework_apply_changes: write accepted enhance changes to DB
  - framework_gap_analysis: compute gap report, store in job output_json
"""

from __future__ import annotations

import json
import re
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from importlib import import_module
from typing import AsyncIterator

import asyncpg

_logging_module = import_module("backend.01_core.logging_utils")
_logger = _logging_module.get_logger("backend.ai.framework_builder.job_handler")

_JOBS = '"20_ai"."45_fct_job_queue"'
_SESSIONS = '"20_ai"."60_fct_builder_sessions"'


def _utc_now_sql() -> datetime:
    return datetime.now(tz=UTC).replace(tzinfo=None)


class _PoolAdapter:
    """
    Thin adapter that wraps a raw asyncpg.Pool and exposes the same
    acquire() / transaction() interface as backend.01_core.database.DatabasePool.
    Used so the GRC services can be instantiated inside job handlers where
    we only have a raw pool (no full DatabasePool instance).
    """

    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[asyncpg.Connection]:
        async with self._pool.acquire() as conn:
            async with conn.transaction():
                yield conn


def _parse_sse_events(chunk: str) -> list[dict]:
    """Parse an SSE chunk into a list of data dicts with the event type injected.

    SSE format: ``event: <type>\\ndata: <json>\\n\\n``
    The event type lives on a separate line from the data payload.
    We capture it and merge ``{"event": "<type>"}`` into the parsed dict
    so downstream consumers (progress feed, frontend) can switch on ``ev.event``.
    """
    events: list[dict] = []
    current_event_type: str | None = None
    for line in chunk.strip().split("\n"):
        if line.startswith("event: "):
            current_event_type = line[7:].strip()
        elif line.startswith("data: "):
            try:
                data = json.loads(line[6:])
            except Exception:
                current_event_type = None
                continue
            if current_event_type and "event" not in data:
                data["event"] = current_event_type
            events.append(data)
            current_event_type = None
    return events


async def _append_progress(conn: asyncpg.Connection, job_id: str, event: dict) -> None:
    """Append a single progress event to output_json.creation_log."""
    import datetime

    event["ts"] = datetime.datetime.utcnow().isoformat()
    await conn.execute(
        f"""
        UPDATE {_JOBS}
        SET output_json = jsonb_set(
            COALESCE(output_json, '{{"creation_log":[]}}'),
            '{{creation_log}}',
            COALESCE(output_json->'creation_log', '[]') || $2::jsonb
        ),
        updated_at = NOW()
        WHERE id = $1
        """,
        job_id,
        event,
    )


async def _set_output(conn: asyncpg.Connection, job_id: str, output: dict) -> None:
    await conn.execute(
        f"""
        UPDATE {_JOBS}
        SET output_json = COALESCE(output_json, '{{}}'::jsonb) || $2::jsonb,
            updated_at = NOW()
        WHERE id = $1
        """,
        job_id,
        output,
    )


async def _fetch_session_scope(
    conn: asyncpg.Connection,
    *,
    session_id: str,
    tenant_key: str,
) -> tuple[str | None, str | None]:
    row = await conn.fetchrow(
        f"""
        SELECT scope_org_id::text AS scope_org_id,
               scope_workspace_id::text AS scope_workspace_id
        FROM {_SESSIONS}
        WHERE id = $1::uuid
          AND tenant_key = $2
        """,
        session_id,
        tenant_key,
    )
    if not row:
        return None, None
    return row.get("scope_org_id"), row.get("scope_workspace_id")


def _normalize_framework_code(value: object) -> str:
    raw = str(value or "").strip().lower()
    raw = re.sub(r"\s+", "_", raw)
    raw = raw.replace("-", "_")
    raw = re.sub(r"[^a-z0-9_]", "", raw).strip("_")
    if not raw:
        raw = "custom_framework"
    if len(raw) > 100:
        raw = raw[:100].rstrip("_")
    if not raw or not raw[0].isalnum():
        raw = f"f_{raw}".strip("_")
    if not raw[-1].isalnum():
        raw = f"{raw}0"
    return raw[:100]


def _normalize_entity_code(
    value: object, *, fallback: str, uppercase: bool = True
) -> str:
    raw = str(value or "").strip()
    if not raw:
        raw = fallback
    raw = re.sub(r"\s+", "_", raw)
    raw = re.sub(r"[^A-Za-z0-9._-]", "", raw)
    raw = re.sub(r"_+", "_", raw).strip("._-")
    if not raw:
        raw = re.sub(r"[^A-Za-z0-9]+", "_", fallback).strip("_") or "CODE"
    if uppercase:
        raw = raw.upper()
    if len(raw) > 100:
        raw = raw[:100].rstrip("._-")
    if not raw:
        raw = "CODE"
    return raw


def _normalize_risk_code(value: object, *, fallback_prefix: str = "RSK") -> str:
    raw = str(value or "").strip().upper()
    raw = re.sub(r"\s+", "_", raw)
    raw = re.sub(r"[^A-Z0-9_-]", "", raw)
    raw = raw.strip("_-")
    if not raw:
        fallback = re.sub(r"[^A-Z0-9]+", "", fallback_prefix.upper())[:6] or "RSK"
        raw = f"{fallback}-001"
    if len(raw) > 100:
        raw = raw[:100].rstrip("_-")
    if not raw or not raw[0].isalnum():
        raw = f"R{raw}".strip("_-")
    if not raw[-1].isalnum():
        raw = f"{raw}0"
    return raw[:100]


def _derive_risk_code_from_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return "RSK-001"
    tokens = re.findall(r"[A-Za-z0-9]+", text.upper())
    if not tokens:
        return "RSK-001"
    prefix = "".join(token[0] for token in tokens[:4])[:4] or "RSK"
    return f"{prefix}-001"


def _normalize_risk_title(value: object) -> str:
    raw = str(value or "").strip().lower()
    raw = re.sub(r"\s+", " ", raw)
    return raw


def _is_framework_code_unique_violation(exc: Exception) -> bool:
    message = str(exc)
    return "uq_10_fct_frameworks_code" in message or "framework code" in message.lower()


def _ensure_unique_code(code: str, used_codes: set[str], *, max_len: int = 100) -> str:
    candidate = code[:max_len]
    if candidate not in used_codes:
        used_codes.add(candidate)
        return candidate

    idx = 2
    while True:
        suffix = f"_{idx}"
        stem = candidate[: max_len - len(suffix)].rstrip("._-")
        if not stem:
            stem = "CODE"
        next_candidate = f"{stem}{suffix}"
        if next_candidate not in used_codes:
            used_codes.add(next_candidate)
            return next_candidate
        idx += 1


_VALID_CONTROL_CATEGORY_CODES = {
    "access_control",
    "asset_management",
    "business_continuity",
    "change_management",
    "compliance",
    "cryptography",
    "data_protection",
    "hr_security",
    "incident_response",
    "logging_monitoring",
    "network_security",
    "physical_security",
    "risk_management",
    "vendor_management",
}

_LEGACY_CONTROL_CATEGORY_MAP = {
    "configuration_management": "change_management",
    "human_resources": "hr_security",
    "incident_management": "incident_response",
    "information_security_policy": "compliance",
    "operations_security": "change_management",
    "privacy": "data_protection",
    "supplier_relationships": "vendor_management",
    "system_acquisition": "vendor_management",
    "vulnerability_management": "change_management",
}

_CONTROL_CATEGORY_KEYWORD_MAP: tuple[tuple[str, str], ...] = (
    ("access", "access_control"),
    ("identity", "access_control"),
    ("iam", "access_control"),
    ("auth", "access_control"),
    ("asset", "asset_management"),
    ("inventory", "asset_management"),
    ("business continuity", "business_continuity"),
    ("disaster", "business_continuity"),
    ("recovery", "business_continuity"),
    ("backup", "business_continuity"),
    ("change", "change_management"),
    ("configuration", "change_management"),
    ("patch", "change_management"),
    ("release", "change_management"),
    ("deploy", "change_management"),
    ("policy", "compliance"),
    ("governance", "compliance"),
    ("compliance", "compliance"),
    ("encrypt", "cryptography"),
    ("crypto", "cryptography"),
    ("key management", "cryptography"),
    ("data", "data_protection"),
    ("privacy", "data_protection"),
    ("retention", "data_protection"),
    ("personnel", "hr_security"),
    ("employee", "hr_security"),
    ("training", "hr_security"),
    ("awareness", "hr_security"),
    ("incident", "incident_response"),
    ("response", "incident_response"),
    ("log", "logging_monitoring"),
    ("monitor", "logging_monitoring"),
    ("alert", "logging_monitoring"),
    ("audit", "logging_monitoring"),
    ("network", "network_security"),
    ("firewall", "network_security"),
    ("segmentation", "network_security"),
    ("physical", "physical_security"),
    ("facility", "physical_security"),
    ("risk", "risk_management"),
    ("vendor", "vendor_management"),
    ("supplier", "vendor_management"),
    ("third party", "vendor_management"),
)


def _normalize_control_category_code(
    raw_value: object,
    *,
    name: object = None,
    description: object = None,
    guidance: object = None,
) -> str:
    raw = str(raw_value or "").strip().lower()
    raw = raw.replace("-", "_").replace(" ", "_")
    raw = re.sub(r"[^a-z0-9_]", "", raw)
    raw = re.sub(r"_+", "_", raw).strip("_")
    if raw in _VALID_CONTROL_CATEGORY_CODES:
        return raw
    if raw in _LEGACY_CONTROL_CATEGORY_MAP:
        return _LEGACY_CONTROL_CATEGORY_MAP[raw]

    text_parts = [
        raw.replace("_", " "),
        str(name or "").lower(),
        str(description or "").lower(),
        str(guidance or "").lower(),
    ]
    combined = " ".join(part for part in text_parts if part).strip()
    for needle, code in _CONTROL_CATEGORY_KEYWORD_MAP:
        if needle in combined:
            return code
    return "compliance"


def _to_risk_registry_link_type(mapping_type: object) -> str:
    value = str(mapping_type or "mitigating").strip().lower()
    if value in {"mitigating", "compensating", "related"}:
        return value
    if value in {"detecting", "detects", "monitors"}:
        return "related"
    return "mitigating"


def _to_global_risk_mapping_type(mapping_type: object) -> str:
    value = str(mapping_type or "mitigating").strip().lower()
    if value in {"mitigating", "compensating", "related", "detecting"}:
        return value
    if value in {"mitigates", "primary", "secondary"}:
        return "mitigating"
    if value in {"detects", "monitors"}:
        return "detecting"
    if value == "compensates":
        return "compensating"
    return "mitigating"


async def _sync_workspace_risk_registry_links(
    *,
    pool: asyncpg.Pool,
    tenant_key: str,
    user_id: str,
    framework_id: str,
    scope_org_id: str | None,
    scope_workspace_id: str | None,
) -> dict[str, int]:
    """
    Mirror framework global risk-control links into risk registry workspace risks.
    This keeps framework control risk associations visible in RR-backed UI surfaces.
    """
    if not scope_org_id or not scope_workspace_id:
        return {"risk_count": 0, "link_count": 0}

    risk_id_by_global: dict[str, str] = {}
    link_count = 0
    workspace_code_suffix = scope_workspace_id.replace("-", "")[:8].lower()

    async def _upsert_workspace_risk_property(
        conn: asyncpg.Connection,
        *,
        workspace_risk_id: str,
        key: str,
        value: str,
    ) -> None:
        await conn.execute(
            """
            INSERT INTO "14_risk_registry"."20_dtl_risk_properties" (
                id, risk_id, property_key, property_value,
                created_at, updated_at, created_by, updated_by
            ) VALUES (
                gen_random_uuid(), $1::uuid, $2, $3, NOW(), NOW(), $4::uuid, $4::uuid
            )
            ON CONFLICT (risk_id, property_key) DO UPDATE
            SET property_value = EXCLUDED.property_value,
                updated_at = EXCLUDED.updated_at,
                updated_by = EXCLUDED.updated_by
            """,
            workspace_risk_id,
            key,
            value,
            user_id,
        )

    async def _ensure_workspace_risk_from_global(
        conn: asyncpg.Connection,
        *,
        global_risk_id: str,
        risk_code: str,
        risk_category_code: str | None,
        risk_level_code: str | None,
        title: str | None,
        description: str | None,
    ) -> str:
        deployment = await conn.fetchrow(
            """
            SELECT workspace_risk_id::text AS workspace_risk_id
            FROM "05_grc_library"."17_fct_risk_library_deployments"
            WHERE tenant_key = $1
              AND org_id = $2::uuid
              AND workspace_id = $3::uuid
              AND global_risk_id = $4::uuid
              AND deployment_status = 'active'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            tenant_key,
            scope_org_id,
            scope_workspace_id,
            global_risk_id,
        )
        if deployment and deployment["workspace_risk_id"]:
            return deployment["workspace_risk_id"]

        workspace_risk_code = f"{risk_code}__ws_{workspace_code_suffix}"
        existing = await conn.fetchrow(
            """
            SELECT id::text
            FROM "14_risk_registry"."10_fct_risks"
            WHERE tenant_key = $1
              AND risk_code = $2
            LIMIT 1
            """,
            tenant_key,
            workspace_risk_code,
        )
        if existing:
            workspace_risk_id = existing["id"]
            await conn.execute(
                """
                UPDATE "14_risk_registry"."10_fct_risks"
                SET org_id = $1::uuid,
                    workspace_id = $2::uuid,
                    risk_category_code = COALESCE($3, risk_category_code),
                    risk_level_code = COALESCE($4, risk_level_code),
                    is_active = TRUE,
                    is_disabled = FALSE,
                    is_deleted = FALSE,
                    updated_at = NOW(),
                    updated_by = $5::uuid
                WHERE id = $6::uuid
                """,
                scope_org_id,
                scope_workspace_id,
                risk_category_code,
                risk_level_code,
                user_id,
                workspace_risk_id,
            )
        else:
            workspace_risk_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO "14_risk_registry"."10_fct_risks" (
                    id, tenant_key, risk_code, org_id, workspace_id,
                    risk_category_code, risk_level_code, treatment_type_code,
                    source_type, risk_status,
                    is_active, is_disabled, is_deleted, is_test, is_system, is_locked,
                    created_at, updated_at, created_by, updated_by
                ) VALUES (
                    $1::uuid, $2, $3, $4::uuid, $5::uuid,
                    $6, $7, 'mitigate',
                    'manual', 'identified',
                    TRUE, FALSE, FALSE, FALSE, FALSE, FALSE,
                    NOW(), NOW(), $8::uuid, $8::uuid
                )
                """,
                workspace_risk_id,
                tenant_key,
                workspace_risk_code,
                scope_org_id,
                scope_workspace_id,
                risk_category_code or "operational",
                risk_level_code or "medium",
                user_id,
            )

        title_value = str(title or "").strip() or risk_code
        await _upsert_workspace_risk_property(
            conn,
            workspace_risk_id=workspace_risk_id,
            key="title",
            value=title_value,
        )
        description_value = str(description or "").strip()
        if description_value:
            await _upsert_workspace_risk_property(
                conn,
                workspace_risk_id=workspace_risk_id,
                key="description",
                value=description_value,
            )

        await conn.execute(
            """
            INSERT INTO "05_grc_library"."17_fct_risk_library_deployments" (
                id, tenant_key, org_id, workspace_id, global_risk_id, workspace_risk_id,
                deployment_status, is_active, created_at, updated_at, created_by, updated_by
            ) VALUES (
                gen_random_uuid(), $1, $2::uuid, $3::uuid, $4::uuid, $5::uuid,
                'active', TRUE, NOW(), NOW(), $6::uuid, $6::uuid
            )
            ON CONFLICT (org_id, workspace_id, global_risk_id)
            DO UPDATE SET workspace_risk_id = EXCLUDED.workspace_risk_id,
                          deployment_status = 'active',
                          updated_at = NOW(),
                          updated_by = EXCLUDED.updated_by
            """,
            tenant_key,
            scope_org_id,
            scope_workspace_id,
            global_risk_id,
            workspace_risk_id,
            user_id,
        )
        return workspace_risk_id

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                gr.id::text AS global_risk_id,
                gr.risk_code,
                gr.risk_category_code,
                gr.risk_level_code,
                gt.property_value AS title,
                gd.property_value AS description,
                lnk.control_id::text AS control_id,
                lnk.mapping_type
            FROM "05_grc_library"."61_lnk_global_risk_control_mappings" lnk
            JOIN "05_grc_library"."13_fct_controls" c
              ON c.id = lnk.control_id
             AND c.framework_id = $1::uuid
             AND c.tenant_key = $2
             AND c.is_deleted = FALSE
            JOIN "05_grc_library"."50_fct_global_risks" gr
              ON gr.id = lnk.global_risk_id
             AND gr.tenant_key = $2
             AND gr.is_deleted = FALSE
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" gt
              ON gt.global_risk_id = gr.id
             AND gt.property_key = 'title'
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" gd
              ON gd.global_risk_id = gr.id
             AND gd.property_key = 'description'
            ORDER BY gr.risk_code, lnk.control_id
            """,
            framework_id,
            tenant_key,
        )

        for row in rows:
            risk_code = str(row["risk_code"] or "").strip()
            if not risk_code:
                continue
            global_risk_id = str(row["global_risk_id"] or "").strip()
            if not global_risk_id:
                continue
            risk_id = risk_id_by_global.get(global_risk_id)
            if not risk_id:
                risk_id = await _ensure_workspace_risk_from_global(
                    conn,
                    global_risk_id=global_risk_id,
                    risk_code=risk_code,
                    risk_category_code=row["risk_category_code"],
                    risk_level_code=row["risk_level_code"],
                    title=row["title"],
                    description=row["description"],
                )
                risk_id_by_global[global_risk_id] = risk_id

            link_type = _to_risk_registry_link_type(row["mapping_type"])
            await conn.execute(
                """
                INSERT INTO "14_risk_registry"."30_lnk_risk_control_mappings" (
                    id, risk_id, control_id, link_type, notes, created_at, created_by
                ) VALUES (
                    gen_random_uuid(), $1::uuid, $2::uuid, $3, NULL, NOW(), $4::uuid
                )
                ON CONFLICT (risk_id, control_id) DO UPDATE
                SET link_type = EXCLUDED.link_type
                """,
                risk_id,
                row["control_id"],
                link_type,
                user_id,
            )
            link_count += 1

    return {"risk_count": len(risk_id_by_global), "link_count": link_count}


# ── Framework Build (Phase 3) ─────────────────────────────────────────────────


async def handle_framework_build_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Writes the approved proposal (hierarchy + controls + risks) to DB.

    job.input_json must contain:
      session_id, user_id, tenant_key,
      framework_name, framework_code, framework_type_code, framework_category_code,
      user_context,
      hierarchy (full tree),
      controls (flat list),
      new_risks (list),
      risk_mappings (list of {control_code, risk_code, coverage_type})
    """
    inp = job.input_json
    session_id = inp["session_id"]
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    scope_org_id = (
        str(inp.get("scope_org_id") or getattr(job, "org_id", "") or "").strip() or None
    )
    scope_workspace_id = (
        str(
            inp.get("scope_workspace_id") or getattr(job, "workspace_id", "") or ""
        ).strip()
        or None
    )
    if not scope_org_id or not scope_workspace_id:
        async with pool.acquire() as conn:
            (
                session_scope_org_id,
                session_scope_workspace_id,
            ) = await _fetch_session_scope(
                conn,
                session_id=session_id,
                tenant_key=tenant_key,
            )
        scope_org_id = scope_org_id or session_scope_org_id
        scope_workspace_id = scope_workspace_id or session_scope_workspace_id
    if not scope_org_id or not scope_workspace_id:
        raise ValueError(
            "Framework build requires scope_org_id and scope_workspace_id from the approved session"
        )
    framework_id: str | None = None
    created_risk_ids: list[str] = []

    # Import services lazily (avoid circular imports at module load)
    _fw_repo_mod = import_module("backend.05_grc_library.02_frameworks.repository")
    _fw_svc_mod = import_module("backend.05_grc_library.02_frameworks.service")
    _req_svc_mod = import_module("backend.05_grc_library.04_requirements.service")
    _ctrl_svc_mod = import_module("backend.05_grc_library.05_controls.service")
    _risk_svc_mod = import_module("backend.05_grc_library.12_global_risks.service")
    _cache_mod = import_module("backend.01_core.cache")

    cache = _cache_mod.NullCacheManager()
    fw_repo = _fw_repo_mod.FrameworkRepository()

    fw_service = _fw_svc_mod.FrameworkService(
        settings=settings, database_pool=pool, cache=cache
    )
    req_service = _req_svc_mod.RequirementService(
        settings=settings, database_pool=pool, cache=cache
    )
    ctrl_service = _ctrl_svc_mod.ControlService(
        settings=settings, database_pool=pool, cache=cache
    )
    risk_service = _risk_svc_mod.GlobalRiskService(
        settings=settings, database_pool=pool, cache=cache
    )

    _fw_schemas = import_module("backend.05_grc_library.02_frameworks.schemas")
    _req_schemas = import_module("backend.05_grc_library.04_requirements.schemas")
    _ctrl_schemas = import_module("backend.05_grc_library.05_controls.schemas")

    async def _lookup_existing_risk_id(
        conn: asyncpg.Connection, risk_code: str
    ) -> str | None:
        row = await conn.fetchrow(
            """
            SELECT id::text
            FROM "05_grc_library"."50_fct_global_risks"
            WHERE risk_code = $1
              AND tenant_key = $2
              AND is_active = TRUE
              AND is_deleted = FALSE
            """,
            risk_code,
            tenant_key,
        )
        return row["id"] if row else None

    async def _lookup_existing_risk_by_title(
        conn: asyncpg.Connection, title: str
    ) -> tuple[str, str] | None:
        normalized_title = _normalize_risk_title(title)
        if not normalized_title:
            return None
        row = await conn.fetchrow(
            """
            SELECT gr.id::text AS id, gr.risk_code
            FROM "05_grc_library"."50_fct_global_risks" gr
            JOIN "05_grc_library"."56_dtl_global_risk_properties" rp
              ON rp.global_risk_id = gr.id
             AND rp.property_key = 'title'
            WHERE gr.tenant_key = $1
              AND gr.is_active = TRUE
              AND gr.is_deleted = FALSE
              AND lower(regexp_replace(trim(rp.property_value), '\\s+', ' ', 'g')) = $2
            ORDER BY gr.updated_at DESC
            LIMIT 1
            """,
            tenant_key,
            normalized_title,
        )
        if not row:
            return None
        return row["id"], row["risk_code"]

    async def _resolve_unique_framework_code(
        conn: asyncpg.Connection, proposed_code: str
    ) -> str:
        existing_rows = await conn.fetch(
            """
            SELECT framework_code
            FROM "05_grc_library"."10_fct_frameworks"
            WHERE tenant_key = $1
              AND framework_code = $2
                 OR (
                    tenant_key = $1
                    AND framework_code LIKE $3
                 )
            """,
            tenant_key,
            proposed_code,
            f"{proposed_code}_%",
        )
        used_codes = {
            str(row["framework_code"]) for row in existing_rows if row["framework_code"]
        }
        if not used_codes:
            return proposed_code
        return _ensure_unique_code(proposed_code, used_codes)

    try:
        # 1. Create framework
        async with pool.acquire() as conn:
            await _append_progress(
                conn,
                job.id,
                {
                    "event": "creating_framework",
                    "framework_code": inp.get("framework_code", ""),
                },
            )

        fw_code = _normalize_framework_code(
            inp.get("framework_code", "custom_framework")
        )
        async with pool.acquire() as conn:
            resolved_fw_code = await _resolve_unique_framework_code(conn, fw_code)
            if resolved_fw_code != fw_code:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "framework_code_adjusted",
                        "requested_framework_code": fw_code,
                        "framework_code": resolved_fw_code,
                    },
                )
            fw_code = resolved_fw_code

        # Normalize framework_type_code to valid dimension values
        _TYPE_MAP = {
            "soc2": "compliance_standard",
            "soc 2": "compliance_standard",
            "iso27001": "compliance_standard",
            "iso 27001": "compliance_standard",
            "pci_dss": "compliance_standard",
            "pci dss": "compliance_standard",
            "hipaa": "compliance_standard",
            "gdpr": "privacy_regulation",
            "ccpa": "privacy_regulation",
            "nist": "security_framework",
            "nist_csf": "security_framework",
            "cis": "security_framework",
            "cis_controls": "security_framework",
            "iso_27001": "compliance_standard",
            "security": "security_framework",
        }
        _VALID_TYPES = {
            "compliance_standard",
            "custom",
            "industry_standard",
            "internal_policy",
            "privacy_regulation",
            "security_framework",
        }
        raw_type = inp.get("framework_type_code", "custom")
        fw_type_code = (
            raw_type
            if raw_type in _VALID_TYPES
            else _TYPE_MAP.get(raw_type.lower(), "custom")
        )

        fw_req = _fw_schemas.CreateFrameworkRequest(
            framework_code=fw_code,
            framework_type_code=fw_type_code,
            framework_category_code=inp["framework_category_code"],
            scope_org_id=scope_org_id,
            scope_workspace_id=scope_workspace_id,
            name=inp["framework_name"],
            description=inp.get("user_context", ""),
            short_description=inp.get("framework_name", ""),
            publisher_type="internal",
        )
        try:
            framework = await fw_service.create_framework(
                user_id=user_id, tenant_key=tenant_key, request=fw_req
            )
        except Exception as exc:
            if not _is_framework_code_unique_violation(exc):
                raise
            async with pool.acquire() as conn:
                resolved_fw_code = await _resolve_unique_framework_code(conn, fw_code)
                if resolved_fw_code == fw_code:
                    raise
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "framework_code_adjusted",
                        "requested_framework_code": fw_code,
                        "framework_code": resolved_fw_code,
                        "reason": "duplicate_code_retry",
                    },
                )
            fw_code = resolved_fw_code
            fw_req = _fw_schemas.CreateFrameworkRequest(
                framework_code=fw_code,
                framework_type_code=fw_type_code,
                framework_category_code=inp["framework_category_code"],
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
                name=inp["framework_name"],
                description=inp.get("user_context", ""),
                short_description=inp.get("framework_name", ""),
                publisher_type="internal",
            )
            framework = await fw_service.create_framework(
                user_id=user_id, tenant_key=tenant_key, request=fw_req
            )
        framework_id = framework.id

        # Defensive scope enforcement:
        # if upstream model/repository paths ever regress, force scope on the created row.
        async with pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE "05_grc_library"."10_fct_frameworks"
                SET scope_org_id = $2::uuid,
                    scope_workspace_id = $3::uuid,
                    updated_at = NOW(),
                    updated_by = $4::uuid
                WHERE id = $1::uuid
                """,
                framework_id,
                scope_org_id,
                scope_workspace_id,
                user_id,
            )

        async with pool.acquire() as conn:
            await _append_progress(
                conn,
                job.id,
                {
                    "event": "framework_created",
                    "framework_code": fw_code,
                    "id": framework_id,
                },
            )

        # 2. Create requirements (BFS order — parents before children)
        hierarchy = inp.get("hierarchy", {})
        all_reqs = _flatten_hierarchy_bfs(hierarchy.get("requirements", []))
        used_requirement_codes: set[str] = set()
        requirement_code_alias: dict[str, str] = {}
        for idx, req_node in enumerate(all_reqs):
            original_code = str(req_node.get("code", "")).strip()
            fallback_code = f"REQ_{idx + 1:03d}"
            normalized_code = _normalize_entity_code(
                original_code, fallback=fallback_code, uppercase=True
            )
            normalized_code = _ensure_unique_code(
                normalized_code, used_requirement_codes
            )
            req_node["normalized_code"] = normalized_code
            if original_code:
                requirement_code_alias[original_code] = normalized_code
                requirement_code_alias[original_code.upper()] = normalized_code
            requirement_code_alias[normalized_code] = normalized_code

        # Build code → id map for parent lookups
        req_id_map: dict[str, str] = {}
        for req_node in all_reqs:
            parent_code_raw = str(req_node.get("parent_code") or "").strip()
            parent_code = requirement_code_alias.get(
                parent_code_raw
            ) or requirement_code_alias.get(parent_code_raw.upper())
            parent_req_id = req_id_map.get(parent_code) if parent_code else None
            req_request = _req_schemas.CreateRequirementRequest(
                requirement_code=str(req_node["normalized_code"]),
                name=req_node["name"],
                description=req_node.get("description", ""),
                sort_order=req_node.get("sort_order", 0),
                parent_requirement_id=parent_req_id,
            )
            req_resp = await req_service.create_requirement(
                user_id=user_id,
                tenant_key=tenant_key,
                framework_id=framework_id,
                request=req_request,
            )
            req_id_map[str(req_node["normalized_code"])] = req_resp.id
            async with pool.acquire() as conn:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "requirement_created",
                        "code": req_node["normalized_code"],
                        "id": req_resp.id,
                    },
                )

        # 3. Create controls
        _VALID_CTRL_TYPES = {"preventive", "detective", "corrective", "compensating"}
        _VALID_AUTO = {"full", "partial", "manual"}
        _VALID_CRIT = {"critical", "high", "medium", "low"}

        controls = inp.get("controls") or []
        if not controls:
            raise ValueError(
                "No controls provided; framework creation requires a full control set"
            )
        ctrl_id_map: dict[str, str] = {}
        used_control_codes: set[str] = set()
        control_code_alias: dict[str, str] = {}
        for idx, ctrl in enumerate(controls):
            raw_req_code = str(ctrl.get("requirement_code", "")).strip()
            normalized_req_code = requirement_code_alias.get(
                raw_req_code
            ) or requirement_code_alias.get(raw_req_code.upper())
            req_id = req_id_map.get(normalized_req_code or raw_req_code)
            if not req_id:
                raise ValueError(
                    f"Control '{ctrl.get('control_code', '(unknown)')}' references unknown requirement_code "
                    f"'{ctrl.get('requirement_code', '(missing)')}'"
                )
            raw_ctrl_code = str(
                ctrl.get("control_code") or ctrl.get("code") or ""
            ).strip()
            fallback_ctrl_code = f"{normalized_req_code or 'CTRL'}-{idx + 1:02d}"
            normalized_ctrl_code = _normalize_entity_code(
                raw_ctrl_code, fallback=fallback_ctrl_code, uppercase=True
            )
            normalized_ctrl_code = _ensure_unique_code(
                normalized_ctrl_code, used_control_codes
            )
            if raw_ctrl_code:
                control_code_alias[raw_ctrl_code] = normalized_ctrl_code
                control_code_alias[raw_ctrl_code.upper()] = normalized_ctrl_code
            control_code_alias[normalized_ctrl_code] = normalized_ctrl_code

            ctrl_cat = _normalize_control_category_code(
                ctrl.get("control_category_code", "compliance"),
                name=ctrl.get("name"),
                description=ctrl.get("description"),
                guidance=ctrl.get("guidance"),
            )
            raw_crit = ctrl.get("criticality", "medium")
            ctrl_crit = raw_crit if raw_crit in _VALID_CRIT else "medium"
            raw_type = ctrl.get("control_type", "preventive")
            ctrl_type = raw_type if raw_type in _VALID_CTRL_TYPES else "preventive"
            raw_auto = ctrl.get("automation_potential", "manual")
            ctrl_auto = raw_auto if raw_auto in _VALID_AUTO else "manual"
            ctrl_request = _ctrl_schemas.CreateControlRequest(
                control_code=normalized_ctrl_code,
                control_category_code=ctrl_cat,
                criticality_code=ctrl_crit,
                control_type=ctrl_type,
                automation_potential=ctrl_auto,
                requirement_id=req_id,
                sort_order=ctrl.get("sort_order", 0),
                name=ctrl["name"],
                description=ctrl.get("description", ""),
                guidance=ctrl.get("guidance", ""),
                implementation_guidance=ctrl.get("implementation_guidance"),
            )
            ctrl_resp = await ctrl_service.create_control(
                user_id=user_id,
                tenant_key=tenant_key,
                framework_id=framework_id,
                request=ctrl_request,
            )
            ctrl_id_map[normalized_ctrl_code] = ctrl_resp.id
            async with pool.acquire() as conn:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "control_created",
                        "code": normalized_ctrl_code,
                        "id": ctrl_resp.id,
                    },
                )

        # 4. Create new risks
        _VALID_RISK_CATS = {
            "compliance",
            "financial",
            "legal",
            "operational",
            "reputational",
            "strategic",
            "technology",
            "vendor",
        }
        _RISK_CAT_MAP = {
            "technology_risk": "technology",
            "tech": "technology",
            "security": "technology",
            "cyber": "technology",
            "data_breach": "technology",
            "privacy": "compliance",
            "regulatory": "compliance",
            "legal_risk": "legal",
            "financial_risk": "financial",
            "vendor_risk": "vendor",
            "supply_chain": "vendor",
            "reputation": "reputational",
        }
        _VALID_RISK_LEVELS = {"critical", "high", "medium", "low"}

        new_risks = inp.get("new_risks") or []
        risk_id_map: dict[str, str] = {}
        risk_code_alias: dict[str, str] = {}
        used_risk_codes: set[str] = set()
        for risk in new_risks:
            original_risk_code = str(risk.get("risk_code") or "").strip().upper()
            title_for_code = (
                risk.get("title")
                or risk.get("short_description")
                or risk.get("description")
            )
            fallback_risk_code = _derive_risk_code_from_text(title_for_code)
            normalized_risk_code = _normalize_risk_code(
                original_risk_code or fallback_risk_code
            )
            if original_risk_code:
                risk_code_alias[original_risk_code] = normalized_risk_code
            risk_code_alias[normalized_risk_code] = normalized_risk_code
            raw_cat = risk.get("risk_category_code", "operational")
            risk_cat = (
                raw_cat
                if raw_cat in _VALID_RISK_CATS
                else _RISK_CAT_MAP.get(raw_cat.lower(), "operational")
            )
            raw_level = (
                risk.get("risk_level_code") or risk.get("risk_level") or "medium"
            )
            risk_level = raw_level if raw_level in _VALID_RISK_LEVELS else "medium"

            if normalized_risk_code in used_risk_codes:
                existing_id = risk_id_map.get(normalized_risk_code)
                if existing_id:
                    continue
            else:
                used_risk_codes.add(normalized_risk_code)

            existing_id: str | None = None
            async with pool.acquire() as conn:
                existing_id = await _lookup_existing_risk_id(conn, normalized_risk_code)
            if existing_id:
                risk_id_map[normalized_risk_code] = existing_id
                async with pool.acquire() as conn:
                    await _append_progress(
                        conn,
                        job.id,
                        {
                            "event": "risk_reused",
                            "code": normalized_risk_code,
                            "reason": "code_match",
                        },
                    )
                continue

            title = str(risk.get("title") or "").strip()
            if title:
                async with pool.acquire() as conn:
                    by_title = await _lookup_existing_risk_by_title(conn, title)
                if by_title:
                    existing_id, existing_code = by_title
                    risk_id_map[normalized_risk_code] = existing_id
                    risk_id_map[existing_code] = existing_id
                    risk_code_alias[existing_code] = existing_code
                    async with pool.acquire() as conn:
                        await _append_progress(
                            conn,
                            job.id,
                            {
                                "event": "risk_reused",
                                "code": existing_code,
                                "reason": "title_match",
                            },
                        )
                    continue

            try:
                async with pool.acquire() as conn:
                    risk_id, created = await fw_repo.upsert_global_risk(
                        conn,
                        global_risk_id=str(uuid.uuid4()),
                        tenant_key=tenant_key,
                        risk_code=normalized_risk_code,
                        risk_category_code=risk_cat,
                        risk_level_code=risk_level,
                        inherent_likelihood=risk.get("inherent_likelihood", 3),
                        inherent_impact=risk.get("inherent_impact", 3),
                        title=risk.get("title", normalized_risk_code),
                        description=risk.get("description", ""),
                        short_description=risk.get("short_description", ""),
                        mitigation_guidance=risk.get("mitigation_guidance", ""),
                        detection_guidance=risk.get("detection_guidance", ""),
                        created_by=user_id,
                        now=_utc_now_sql(),
                    )
                risk_id_map[normalized_risk_code] = risk_id
                if created:
                    created_risk_ids.append(risk_id)
            except Exception as e:
                if "already exists" in str(e):
                    # Reuse existing risk
                    async with pool.acquire() as conn:
                        row = await conn.fetchrow(
                            """
                            SELECT id::text
                            FROM "05_grc_library"."50_fct_global_risks"
                            WHERE risk_code=$1 AND tenant_key=$2
                              AND is_active = TRUE AND is_deleted = FALSE
                            """,
                            normalized_risk_code,
                            tenant_key,
                        )
                    if row:
                        risk_id_map[normalized_risk_code] = row["id"]
                    continue
                raise
            async with pool.acquire() as conn:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "risk_created",
                        "code": normalized_risk_code,
                        "id": risk_id,
                    },
                )

        # 5. Link controls to risks
        risk_mappings = inp.get("risk_mappings") or []
        if not risk_mappings:
            raise ValueError(
                "No risk mappings provided; every control must map to at least one risk"
            )
        linked_control_codes: set[str] = set()
        for mapping in risk_mappings:
            raw_ctrl_code = str(mapping.get("control_code", "")).strip()
            resolved_ctrl_code = (
                control_code_alias.get(raw_ctrl_code)
                or control_code_alias.get(raw_ctrl_code.upper())
                or raw_ctrl_code
            )
            raw_risk_code = str(mapping.get("risk_code", "")).strip().upper()
            resolved_risk_code = (
                risk_code_alias.get(raw_risk_code)
                or _normalize_risk_code(raw_risk_code, fallback_prefix="RSK")
                if raw_risk_code
                else ""
            )

            ctrl_id = ctrl_id_map.get(resolved_ctrl_code) or ctrl_id_map.get(
                raw_ctrl_code
            )
            risk_id = risk_id_map.get(resolved_risk_code) or risk_id_map.get(
                raw_risk_code
            )
            if not risk_id and (resolved_risk_code or raw_risk_code):
                async with pool.acquire() as conn:
                    risk_id = await _lookup_existing_risk_id(
                        conn, resolved_risk_code or raw_risk_code
                    )
                if risk_id:
                    risk_id_map[resolved_risk_code or raw_risk_code] = risk_id
            if not ctrl_id or not risk_id:
                continue
            raw_mtype = (
                mapping.get("coverage_type")
                or mapping.get("mapping_type")
                or "mitigating"
            )
            db_mapping_type = _to_global_risk_mapping_type(raw_mtype)
            try:
                async with pool.acquire() as conn:
                    await fw_repo.link_global_risk_to_control(
                        conn,
                        global_risk_id=risk_id,
                        control_id=ctrl_id,
                        mapping_type=db_mapping_type,
                        created_by=user_id,
                        now=_utc_now_sql(),
                    )
            except Exception as e:
                if "already exists" in str(e) or "duplicate" in str(e).lower():
                    linked_control_codes.add(resolved_ctrl_code or raw_ctrl_code)
                    continue
                raise
            linked_control_codes.add(resolved_ctrl_code or raw_ctrl_code)
            async with pool.acquire() as conn:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "risk_linked",
                        "control_code": resolved_ctrl_code or raw_ctrl_code,
                        "risk_code": resolved_risk_code or raw_risk_code,
                    },
                )

        missing_control_links: list[str] = []
        for ctrl in controls:
            if not isinstance(ctrl, dict):
                continue
            original_code = str(
                ctrl.get("control_code") or ctrl.get("code") or ""
            ).strip()
            if not original_code:
                continue
            normalized_code = (
                control_code_alias.get(original_code)
                or control_code_alias.get(original_code.upper())
                or original_code
            )
            if normalized_code not in linked_control_codes:
                missing_control_links.append(normalized_code)
        if missing_control_links:
            preview = ", ".join(missing_control_links[:15])
            raise ValueError(
                f"Some controls are not linked to risks ({len(missing_control_links)}): {preview}"
            )

        if scope_org_id and scope_workspace_id:
            global_risk_ids = sorted(
                {
                    risk_id
                    for risk_id in risk_id_map.values()
                    if isinstance(risk_id, str) and risk_id
                }
            )
            if global_risk_ids:
                try:
                    deploy_result = await risk_service.deploy_global_risks(
                        user_id=user_id,
                        tenant_key=tenant_key,
                        org_id=scope_org_id,
                        workspace_id=scope_workspace_id,
                        global_risk_ids=global_risk_ids,
                    )
                    async with pool.acquire() as conn:
                        await _append_progress(
                            conn,
                            job.id,
                            {
                                "event": "risk_library_deployed",
                                "org_id": scope_org_id,
                                "workspace_id": scope_workspace_id,
                                "deployed": deploy_result.get("deployed", 0),
                                "inserted": deploy_result.get("inserted", 0),
                                "skipped": deploy_result.get("skipped", 0),
                            },
                        )
                except Exception as exc:
                    async with pool.acquire() as conn:
                        await _append_progress(
                            conn,
                            job.id,
                            {
                                "event": "risk_library_deploy_warning",
                                "message": str(exc)[:300],
                            },
                        )

            rr_sync = await _sync_workspace_risk_registry_links(
                pool=pool,
                tenant_key=tenant_key,
                user_id=user_id,
                framework_id=framework_id,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            async with pool.acquire() as conn:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "risk_registry_synced",
                        "org_id": scope_org_id,
                        "workspace_id": scope_workspace_id,
                        "risk_count": rr_sync.get("risk_count", 0),
                        "link_count": rr_sync.get("link_count", 0),
                    },
                )

        # 6. Update session + finalize
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_SESSIONS}
                SET result_framework_id = $2::uuid,
                    status = 'complete',
                    error_message = NULL,
                    updated_at = NOW()
                WHERE id = $1 AND tenant_key = $3
                """,
                session_id,
                framework_id,
                tenant_key,
            )
            stats = {
                "requirement_count": len(all_reqs),
                "control_count": len(controls),
                "risk_count": len(new_risks),
                "risk_link_count": len(risk_mappings),
            }
            await _append_progress(
                conn,
                job.id,
                {
                    "event": "creation_complete",
                    "framework_id": framework_id,
                    **stats,
                },
            )
            await _set_output(
                conn,
                job.id,
                {
                    "framework_id": framework_id,
                    "stats": stats,
                },
            )

        _logger.info(
            "framework_build.done",
            extra={"job_id": job.id, "framework_id": framework_id},
        )

    except Exception as exc:
        _logger.exception("framework_build.failed: %s", exc)
        async with pool.acquire() as conn:
            await _append_progress(
                conn, job.id, {"event": "creation_error", "message": str(exc)}
            )
            await conn.execute(
                f"UPDATE {_SESSIONS} SET status = 'failed', error_message = $2, updated_at = NOW() "
                f"WHERE id = $1 AND tenant_key = $3",
                session_id,
                str(exc)[:500],
                tenant_key,
            )
        if framework_id:
            try:
                async with pool.acquire() as conn:
                    await conn.execute(
                        'DELETE FROM "05_grc_library"."13_fct_controls" WHERE framework_id = $1::uuid',
                        framework_id,
                    )
                    await conn.execute(
                        'DELETE FROM "05_grc_library"."12_fct_requirements" WHERE framework_id = $1::uuid',
                        framework_id,
                    )
                    await conn.execute(
                        'DELETE FROM "05_grc_library"."10_fct_frameworks" WHERE id = $1::uuid',
                        framework_id,
                    )
                    if created_risk_ids:
                        await conn.execute(
                            'DELETE FROM "05_grc_library"."50_fct_global_risks" WHERE id = ANY($1::uuid[])',
                            created_risk_ids,
                        )
                    await _append_progress(
                        conn,
                        job.id,
                        {
                            "event": "creation_cleanup_complete",
                            "framework_id": framework_id,
                        },
                    )
            except Exception as cleanup_exc:
                _logger.exception("framework_build.cleanup_failed: %s", cleanup_exc)
                async with pool.acquire() as conn:
                    await _append_progress(
                        conn,
                        job.id,
                        {
                            "event": "creation_cleanup_failed",
                            "framework_id": framework_id,
                            "message": str(cleanup_exc),
                        },
                    )
        raise


def _flatten_hierarchy_bfs(nodes: list) -> list[dict]:
    """BFS flatten so parents always come before children.

    Enforces strict 2-level hierarchy: domain (depth 0) → category (depth 1).
    Any deeper nesting from the LLM is silently dropped.
    """
    result = []
    # Queue entries: (node, parent_code, depth)
    queue = [(node, None, 0) for node in nodes]
    i = 0
    while i < len(queue):
        node, parent_code, depth = queue[i]
        result.append(
            {
                "code": node["code"],
                "name": node["name"],
                "description": node.get("description", ""),
                "sort_order": node.get("sort_order", i),
                "parent_code": parent_code,
            }
        )
        # Only recurse from domain (0) to category (1), never deeper
        if depth == 0:
            for child in node.get("children", []):
                queue.append((child, node["code"], depth + 1))
        i += 1
    return result


# ── Apply Enhancements (Phase 3 Enhance Mode) ─────────────────────────────────


async def handle_apply_changes_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Applies accepted enhance-mode changes to an existing framework.

    job.input_json must contain:
      session_id, user_id, tenant_key, framework_id, accepted_changes (list)
    """
    inp = job.input_json
    session_id = inp["session_id"]
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    framework_id = inp["framework_id"]
    scope_org_id = (
        str(inp.get("scope_org_id") or getattr(job, "org_id", "") or "").strip() or None
    )
    scope_workspace_id = (
        str(
            inp.get("scope_workspace_id") or getattr(job, "workspace_id", "") or ""
        ).strip()
        or None
    )
    if not scope_org_id or not scope_workspace_id:
        async with pool.acquire() as conn:
            (
                session_scope_org_id,
                session_scope_workspace_id,
            ) = await _fetch_session_scope(
                conn,
                session_id=session_id,
                tenant_key=tenant_key,
            )
        scope_org_id = scope_org_id or session_scope_org_id
        scope_workspace_id = scope_workspace_id or session_scope_workspace_id
    if not scope_org_id or not scope_workspace_id:
        raise ValueError(
            "Framework enhance apply requires scope_org_id and scope_workspace_id from the approved session"
        )
    accepted_changes = inp.get("accepted_changes", [])

    _fw_repo_mod = import_module("backend.05_grc_library.02_frameworks.repository")
    _req_svc_mod = import_module("backend.05_grc_library.04_requirements.service")
    _ctrl_svc_mod = import_module("backend.05_grc_library.05_controls.service")
    _cache_mod = import_module("backend.01_core.cache")

    cache = _cache_mod.NullCacheManager()
    fw_repo = _fw_repo_mod.FrameworkRepository()
    req_service = _req_svc_mod.RequirementService(
        settings=settings, database_pool=pool, cache=cache
    )
    ctrl_service = _ctrl_svc_mod.ControlService(
        settings=settings, database_pool=pool, cache=cache
    )

    _req_schemas = import_module("backend.05_grc_library.04_requirements.schemas")
    _ctrl_schemas = import_module("backend.05_grc_library.05_controls.schemas")

    _fw_svc_mod = import_module("backend.05_grc_library.02_frameworks.service")
    _fw_schemas = import_module("backend.05_grc_library.02_frameworks.schemas")
    fw_service = _fw_svc_mod.FrameworkService(
        settings=settings, database_pool=pool, cache=cache
    )

    _VALID_RISK_CATS = {
        "compliance",
        "financial",
        "legal",
        "operational",
        "reputational",
        "strategic",
        "technology",
        "vendor",
    }
    _RISK_CAT_MAP = {
        "technology_risk": "technology",
        "tech": "technology",
        "security": "technology",
        "cyber": "technology",
        "data_breach": "technology",
        "privacy": "compliance",
        "regulatory": "compliance",
        "legal_risk": "legal",
        "financial_risk": "financial",
        "vendor_risk": "vendor",
        "supply_chain": "vendor",
        "reputation": "reputational",
    }
    _VALID_RISK_LEVELS = {"critical", "high", "medium", "low"}

    def _to_clean_list(value: object) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            out = [str(v).strip() for v in value if str(v).strip()]
            return out
        if isinstance(value, str):
            txt = value.strip()
            if not txt:
                return []
            if txt.startswith("[") and txt.endswith("]"):
                try:
                    parsed = json.loads(txt)
                    if isinstance(parsed, list):
                        return [str(v).strip() for v in parsed if str(v).strip()]
                except Exception:
                    pass
            out = [
                line.strip("- ").strip() for line in txt.splitlines() if line.strip()
            ]
            return out
        return [str(value).strip()] if str(value).strip() else []

    def _normalize_criteria(value: object) -> list[str] | None:
        return _to_clean_list(value)

    async def _lookup_requirement_id_by_code(
        conn: asyncpg.Connection, requirement_code: str
    ) -> str | None:
        row = await conn.fetchrow(
            """
            SELECT r.id::text
            FROM "05_grc_library"."12_fct_requirements" r
            JOIN "05_grc_library"."10_fct_frameworks" f ON f.id = r.framework_id
            WHERE r.framework_id = $1::uuid
              AND r.requirement_code = $2
              AND r.is_active = TRUE
              AND r.is_deleted = FALSE
              AND f.tenant_key = $3
              AND f.is_deleted = FALSE
            LIMIT 1
            """,
            framework_id,
            requirement_code,
            tenant_key,
        )
        return row["id"] if row else None

    async def _lookup_risk_id_by_code(
        conn: asyncpg.Connection, risk_code: str
    ) -> str | None:
        row = await conn.fetchrow(
            """
            SELECT id::text
            FROM "05_grc_library"."50_fct_global_risks"
            WHERE risk_code = $1
              AND tenant_key = $2
              AND is_active = TRUE
              AND is_deleted = FALSE
            """,
            risk_code,
            tenant_key,
        )
        return row["id"] if row else None

    async def _lookup_risk_by_title(
        conn: asyncpg.Connection, title: str
    ) -> tuple[str, str] | None:
        normalized_title = _normalize_risk_title(title)
        if not normalized_title:
            return None
        row = await conn.fetchrow(
            """
            SELECT gr.id::text AS id, gr.risk_code
            FROM "05_grc_library"."50_fct_global_risks" gr
            JOIN "05_grc_library"."56_dtl_global_risk_properties" rp
              ON rp.global_risk_id = gr.id
             AND rp.property_key = 'title'
            WHERE gr.tenant_key = $1
              AND gr.is_active = TRUE
              AND gr.is_deleted = FALSE
              AND lower(regexp_replace(trim(rp.property_value), '\\s+', ' ', 'g')) = $2
            ORDER BY gr.updated_at DESC
            LIMIT 1
            """,
            tenant_key,
            normalized_title,
        )
        if not row:
            return None
        return row["id"], row["risk_code"]

    async def _first_control_for_requirement(
        conn: asyncpg.Connection, requirement_id: str
    ) -> str | None:
        row = await conn.fetchrow(
            """
            SELECT c.id::text
            FROM "05_grc_library"."13_fct_controls" c
            JOIN "05_grc_library"."12_fct_requirements" r ON r.id = c.requirement_id
            WHERE c.requirement_id = $1::uuid
              AND c.framework_id = $2::uuid
              AND c.tenant_key = $3
              AND c.is_active = TRUE
              AND c.is_deleted = FALSE
              AND r.is_deleted = FALSE
            ORDER BY c.sort_order, c.created_at
            LIMIT 1
            """,
            requirement_id,
            framework_id,
            tenant_key,
        )
        return row["id"] if row else None

    async def _lookup_control_id_by_code(
        conn: asyncpg.Connection, control_code: str
    ) -> str | None:
        row = await conn.fetchrow(
            """
            SELECT id::text
            FROM "05_grc_library"."13_fct_controls"
            WHERE framework_id = $1::uuid
              AND tenant_key = $2
              AND control_code = $3
              AND is_active = TRUE
              AND is_deleted = FALSE
            LIMIT 1
            """,
            framework_id,
            tenant_key,
            control_code,
        )
        return row["id"] if row else None

    async def _next_available_requirement_code(base_code: str) -> str:
        base_candidate = _normalize_entity_code(
            base_code, fallback="REQ_001", uppercase=True
        )
        candidate = base_candidate
        attempt = 2
        while True:
            async with pool.acquire() as conn:
                existing = await _lookup_requirement_id_by_code(conn, candidate)
            if not existing:
                return candidate
            suffix = f"_{attempt}"
            stem = base_candidate[: 100 - len(suffix)].rstrip("._-") or "REQ"
            candidate = f"{stem}{suffix}"
            attempt += 1

    async def _next_available_control_code(base_code: str) -> str:
        base_candidate = _normalize_entity_code(
            base_code, fallback="CTRL_001", uppercase=True
        )
        candidate = base_candidate
        attempt = 2
        while True:
            async with pool.acquire() as conn:
                existing = await _lookup_control_id_by_code(conn, candidate)
            if not existing:
                return candidate
            suffix = f"_{attempt}"
            stem = base_candidate[: 100 - len(suffix)].rstrip("._-") or "CTRL"
            candidate = f"{stem}{suffix}"
            attempt += 1

    async def _upsert_requirement_property(
        requirement_id: str, key: str, value: str
    ) -> None:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO "05_grc_library"."22_dtl_requirement_properties"
                    (id, requirement_id, property_key, property_value, created_at, updated_at, created_by, updated_by)
                VALUES (gen_random_uuid(), $1::uuid, $2, $3, NOW(), NOW(), $4::uuid, $4::uuid)
                ON CONFLICT (requirement_id, property_key) DO UPDATE
                SET property_value = EXCLUDED.property_value,
                    updated_at = EXCLUDED.updated_at,
                    updated_by = EXCLUDED.updated_by
                """,
                requirement_id,
                key,
                value,
                user_id,
            )

    def _build_new_risk_payload(
        candidate: dict, fallback_risk_code: str
    ) -> dict | None:
        fallback = fallback_risk_code or _derive_risk_code_from_text(
            candidate.get("title")
        )
        candidate_code = _normalize_risk_code(candidate.get("risk_code") or fallback)
        if not candidate_code:
            return None
        raw_cat = str(candidate.get("risk_category_code", "operational"))
        risk_cat = (
            raw_cat
            if raw_cat in _VALID_RISK_CATS
            else _RISK_CAT_MAP.get(raw_cat.lower(), "operational")
        )
        raw_level = str(
            candidate.get("risk_level_code") or candidate.get("risk_level") or "medium"
        )
        risk_level = raw_level if raw_level in _VALID_RISK_LEVELS else "medium"
        return {
            "risk_code": candidate_code,
            "risk_category_code": risk_cat,
            "risk_level_code": risk_level,
            "inherent_likelihood": candidate.get("inherent_likelihood", 3),
            "inherent_impact": candidate.get("inherent_impact", 3),
            "title": candidate.get("title", candidate_code),
            "description": candidate.get("description", ""),
            "short_description": candidate.get("short_description", ""),
            "mitigation_guidance": candidate.get("mitigation_guidance", ""),
            "detection_guidance": candidate.get("detection_guidance", ""),
        }

    async def _apply_risk_mapping(
        mapping: dict,
        *,
        fallback_control_id: str | None = None,
        fallback_requirement_id: str | None = None,
    ) -> None:
        fallback_code = _derive_risk_code_from_text(
            mapping.get("risk_title")
            or mapping.get("title")
            or mapping.get("description")
        )
        risk_code = _normalize_risk_code(
            mapping.get("risk_code"), fallback_prefix=fallback_code.split("-", 1)[0]
        )
        ctrl_id = mapping.get("control_id") or fallback_control_id
        if not ctrl_id and mapping.get("control_code"):
            async with pool.acquire() as conn:
                ctrl_code = _normalize_entity_code(
                    mapping.get("control_code"), fallback="CTRL_001", uppercase=True
                )
                ctrl_id = await _lookup_control_id_by_code(conn, ctrl_code)
        if not ctrl_id and mapping.get("requirement_id"):
            async with pool.acquire() as conn:
                ctrl_id = await _first_control_for_requirement(
                    conn, str(mapping.get("requirement_id"))
                )
        if not ctrl_id and mapping.get("requirement_code"):
            async with pool.acquire() as conn:
                req_code = _normalize_entity_code(
                    mapping.get("requirement_code"), fallback="REQ_001", uppercase=True
                )
                req_id = await _lookup_requirement_id_by_code(conn, req_code)
                if req_id:
                    ctrl_id = await _first_control_for_requirement(conn, req_id)
        if not ctrl_id and fallback_requirement_id:
            async with pool.acquire() as conn:
                ctrl_id = await _first_control_for_requirement(
                    conn, fallback_requirement_id
                )

        risk_id: str | None = None
        if risk_code:
            async with pool.acquire() as conn:
                risk_id = await _lookup_risk_id_by_code(conn, risk_code)
            if risk_id:
                async with pool.acquire() as conn:
                    await _append_progress(
                        conn,
                        job.id,
                        {
                            "event": "risk_reused",
                            "code": risk_code,
                            "reason": "code_match",
                        },
                    )

        candidate = (
            mapping.get("new_risk")
            if isinstance(mapping.get("new_risk"), dict)
            else mapping
        )
        if not isinstance(candidate, dict):
            candidate = {}
        risk_title = str(
            candidate.get("title") or candidate.get("risk_title") or ""
        ).strip()
        if not risk_id and risk_title:
            async with pool.acquire() as conn:
                by_title = await _lookup_risk_by_title(conn, risk_title)
            if by_title:
                risk_id, matched_code = by_title
                risk_code = matched_code
                async with pool.acquire() as conn:
                    await _append_progress(
                        conn,
                        job.id,
                        {
                            "event": "risk_reused",
                            "code": matched_code,
                            "reason": "title_match",
                        },
                    )

        if not risk_id:
            create_risk_payload = _build_new_risk_payload(candidate, risk_code)
            if create_risk_payload:
                try:
                    async with pool.acquire() as conn:
                        risk_id, _ = await fw_repo.upsert_global_risk(
                            conn,
                            global_risk_id=str(uuid.uuid4()),
                            tenant_key=tenant_key,
                            risk_code=str(create_risk_payload["risk_code"]),
                            risk_category_code=create_risk_payload.get(
                                "risk_category_code"
                            ),
                            risk_level_code=create_risk_payload.get("risk_level_code"),
                            inherent_likelihood=create_risk_payload.get(
                                "inherent_likelihood"
                            ),
                            inherent_impact=create_risk_payload.get("inherent_impact"),
                            title=create_risk_payload.get("title"),
                            description=create_risk_payload.get("description"),
                            short_description=create_risk_payload.get(
                                "short_description"
                            ),
                            mitigation_guidance=create_risk_payload.get(
                                "mitigation_guidance"
                            ),
                            detection_guidance=create_risk_payload.get(
                                "detection_guidance"
                            ),
                            created_by=user_id,
                            now=_utc_now_sql(),
                        )
                    risk_code = str(create_risk_payload["risk_code"])
                    async with pool.acquire() as conn:
                        await _append_progress(
                            conn,
                            job.id,
                            {
                                "event": "risk_created",
                                "code": risk_code,
                                "id": risk_id,
                            },
                        )
                except Exception:
                    async with pool.acquire() as conn:
                        risk_id = await _lookup_risk_id_by_code(
                            conn, create_risk_payload["risk_code"]
                        )
                    if risk_id:
                        risk_code = str(create_risk_payload["risk_code"])
                        async with pool.acquire() as conn:
                            await _append_progress(
                                conn,
                                job.id,
                                {
                                    "event": "risk_reused",
                                    "code": risk_code,
                                    "reason": "existing_after_conflict",
                                },
                            )

        if not risk_id or not ctrl_id:
            raise ValueError(
                f"Cannot apply risk mapping: risk_id={risk_id}, ctrl_id={ctrl_id}"
            )

        _raw_mt = str(
            mapping.get("coverage_type") or mapping.get("mapping_type") or "mitigating"
        )
        db_mapping_type = _to_global_risk_mapping_type(_raw_mt)
        try:
            async with pool.acquire() as conn:
                await fw_repo.link_global_risk_to_control(
                    conn,
                    global_risk_id=risk_id,
                    control_id=ctrl_id,
                    mapping_type=db_mapping_type,
                    created_by=user_id,
                    now=_utc_now_sql(),
                )
        except Exception as exc:
            message = str(exc).lower()
            if "already exists" not in message and "duplicate" not in message:
                raise
        async with pool.acquire() as conn:
            await _append_progress(
                conn,
                job.id,
                {
                    "event": "risk_linked",
                    "control_id": ctrl_id,
                    "risk_code": risk_code,
                    "coverage_type": _raw_mt,
                },
            )

    applied = 0
    failed = 0
    requested = len(accepted_changes)
    async with pool.acquire() as conn:
        await conn.execute(
            """
            UPDATE "05_grc_library"."10_fct_frameworks"
            SET scope_org_id = $2::uuid,
                scope_workspace_id = $3::uuid,
                updated_at = NOW(),
                updated_by = $4::uuid
            WHERE id = $1::uuid
              AND tenant_key = $5
              AND (
                  scope_org_id IS DISTINCT FROM $2::uuid
                  OR scope_workspace_id IS DISTINCT FROM $3::uuid
              )
            """,
            framework_id,
            scope_org_id,
            scope_workspace_id,
            user_id,
            tenant_key,
        )
    try:
        for change in accepted_changes:
            change_type = str(change.get("change_type", "") or "")
            entity_type = str(change.get("entity_type", "") or "")
            entity_id = change.get("entity_id")
            entity_code = str(change.get("entity_code", "") or "")
            field = str(change.get("field", "") or "")
            proposed_value = change.get("proposed_value")
            structured = proposed_value if isinstance(proposed_value, dict) else {}

            try:
                applied_this_change = False

                if entity_type == "framework" and change_type in {
                    "enrich_description",
                    "enrich_guidance",
                    "enrich_detail",
                    "enrich_acceptance_criteria",
                }:
                    fw_id = str(entity_id or framework_id)
                    fw_update: dict = {}
                    fw_props: dict[str, str] = {}
                    if isinstance(structured, dict) and structured:
                        if "name" in structured:
                            fw_update["name"] = structured.get("name")
                        if "description" in structured:
                            fw_update["description"] = structured.get("description")
                        if "short_description" in structured:
                            fw_update["short_description"] = structured.get(
                                "short_description"
                            )
                        criteria = _normalize_criteria(
                            structured.get("acceptance_criteria")
                        )
                        if criteria is not None:
                            fw_props["acceptance_criteria"] = json.dumps(criteria)
                    else:
                        if field in {"name", "description", "short_description"}:
                            fw_update[field] = proposed_value
                        elif field == "acceptance_criteria":
                            criteria = _normalize_criteria(proposed_value)
                            if criteria is not None:
                                fw_props["acceptance_criteria"] = json.dumps(criteria)
                        elif isinstance(proposed_value, str):
                            fw_update["description"] = proposed_value
                    if fw_props:
                        fw_update["properties"] = fw_props
                    if fw_update:
                        await fw_service.update_framework(
                            user_id=user_id,
                            framework_id=fw_id,
                            request=_fw_schemas.UpdateFrameworkRequest(**fw_update),
                        )
                        applied_this_change = True

                elif entity_type == "requirement" and change_type in {
                    "enrich_description",
                    "enrich_guidance",
                    "enrich_detail",
                    "enrich_acceptance_criteria",
                }:
                    req_id = str(entity_id) if entity_id else None
                    if not req_id and entity_code:
                        async with pool.acquire() as conn:
                            req_id = await _lookup_requirement_id_by_code(
                                conn, entity_code
                            )
                    if not req_id:
                        raise ValueError(
                            "Requirement proposal missing resolvable entity_id/entity_code"
                        )

                    req_update: dict = {}
                    if isinstance(structured, dict) and structured:
                        if "name" in structured:
                            req_update["name"] = structured.get("name")
                        if "description" in structured:
                            req_update["description"] = structured.get("description")
                    else:
                        if field in {"name", "description"}:
                            req_update[field] = proposed_value
                        elif isinstance(proposed_value, str):
                            req_update["description"] = proposed_value

                    if req_update:
                        await req_service.update_requirement(
                            user_id=user_id,
                            tenant_key=tenant_key,
                            framework_id=framework_id,
                            requirement_id=req_id,
                            request=_req_schemas.UpdateRequirementRequest(**req_update),
                        )
                        applied_this_change = True

                    criteria_source = (
                        structured.get("acceptance_criteria")
                        if isinstance(structured, dict)
                        else None
                    )
                    if criteria_source is None and field == "acceptance_criteria":
                        criteria_source = proposed_value
                    criteria = _normalize_criteria(criteria_source)
                    if criteria is not None:
                        await _upsert_requirement_property(
                            req_id, "acceptance_criteria", json.dumps(criteria)
                        )
                        applied_this_change = True

                elif entity_type == "control" and change_type in {
                    "enrich_description",
                    "enrich_guidance",
                    "enrich_detail",
                    "enrich_acceptance_criteria",
                    "fix_criticality",
                    "fix_control_type",
                    "fix_automation",
                    "enrich_tags",
                }:
                    ctrl_id = str(entity_id) if entity_id else None
                    if not ctrl_id and entity_code:
                        async with pool.acquire() as conn:
                            ctrl_id = await _lookup_control_id_by_code(
                                conn, entity_code
                            )
                    if not ctrl_id:
                        raise ValueError(
                            "Control proposal missing resolvable entity_id/entity_code"
                        )

                    ctrl_update: dict = {}
                    if isinstance(structured, dict) and structured:
                        if "name" in structured:
                            ctrl_update["name"] = structured.get("name")
                        if "description" in structured:
                            ctrl_update["description"] = structured.get("description")
                        if "guidance" in structured:
                            ctrl_update["guidance"] = structured.get("guidance")
                        if "implementation_guidance" in structured:
                            ctrl_update["implementation_guidance"] = (
                                _to_clean_list(
                                    structured.get("implementation_guidance")
                                )
                                or []
                            )
                        if "tags" in structured:
                            ctrl_update["tags"] = (
                                _to_clean_list(structured.get("tags")) or []
                            )
                        if "control_type" in structured:
                            ctrl_update["control_type"] = structured.get("control_type")
                        if (
                            "criticality" in structured
                            and "criticality_code" not in structured
                        ):
                            ctrl_update["criticality_code"] = structured.get(
                                "criticality"
                            )
                        if "criticality_code" in structured:
                            ctrl_update["criticality_code"] = structured.get(
                                "criticality_code"
                            )
                        if "automation_potential" in structured:
                            ctrl_update["automation_potential"] = structured.get(
                                "automation_potential"
                            )
                        if "control_category_code" in structured:
                            ctrl_update["control_category_code"] = (
                                _normalize_control_category_code(
                                    structured.get("control_category_code"),
                                    name=structured.get("name"),
                                    description=structured.get("description"),
                                    guidance=structured.get("guidance"),
                                )
                            )
                    else:
                        if field in ("description", "guidance"):
                            ctrl_update[field] = proposed_value
                        elif field == "implementation_guidance":
                            ctrl_update["implementation_guidance"] = (
                                _to_clean_list(proposed_value) or []
                            )
                        elif field == "tags":
                            ctrl_update["tags"] = _to_clean_list(proposed_value) or []
                        elif field in ("criticality", "criticality_code"):
                            ctrl_update["criticality_code"] = proposed_value
                        elif field == "control_type":
                            ctrl_update["control_type"] = proposed_value
                        elif field == "automation_potential":
                            ctrl_update["automation_potential"] = proposed_value
                        elif field == "control_category_code":
                            ctrl_update["control_category_code"] = (
                                _normalize_control_category_code(proposed_value)
                            )

                    criteria_source = (
                        structured.get("acceptance_criteria")
                        if isinstance(structured, dict)
                        else None
                    )
                    if criteria_source is None and field == "acceptance_criteria":
                        criteria_source = proposed_value
                    criteria = _normalize_criteria(criteria_source)
                    if criteria is not None:
                        props = dict(ctrl_update.get("properties", {}))
                        props["acceptance_criteria"] = json.dumps(criteria)
                        ctrl_update["properties"] = props

                    if ctrl_update:
                        await ctrl_service.update_control(
                            user_id=user_id,
                            tenant_key=tenant_key,
                            framework_id=framework_id,
                            control_id=ctrl_id,
                            request=_ctrl_schemas.UpdateControlRequest(**ctrl_update),
                        )
                        applied_this_change = True

                elif change_type == "add_requirement" and isinstance(
                    proposed_value, dict
                ):
                    req_data = dict(proposed_value)
                    if "code" in req_data and "requirement_code" not in req_data:
                        req_data["requirement_code"] = req_data.pop("code")
                    base_req_code = (
                        req_data.get("requirement_code")
                        or req_data.get("name")
                        or "REQ_001"
                    )
                    normalized_req_code = _normalize_entity_code(
                        base_req_code, fallback="REQ_001", uppercase=True
                    )
                    req_data[
                        "requirement_code"
                    ] = await _next_available_requirement_code(normalized_req_code)
                    req_data["name"] = str(
                        req_data.get("name") or req_data["requirement_code"]
                    )
                    criteria = _normalize_criteria(
                        req_data.pop("acceptance_criteria", None)
                    )
                    allowed_req = {
                        f for f in _req_schemas.CreateRequirementRequest.model_fields
                    }
                    req_data = {k: v for k, v in req_data.items() if k in allowed_req}
                    req_resp = await req_service.create_requirement(
                        user_id=user_id,
                        tenant_key=tenant_key,
                        framework_id=framework_id,
                        request=_req_schemas.CreateRequirementRequest(**req_data),
                    )
                    if criteria is not None:
                        await _upsert_requirement_property(
                            req_resp.id, "acceptance_criteria", json.dumps(criteria)
                        )
                    applied_this_change = True

                elif change_type == "add_control" and isinstance(proposed_value, dict):
                    ctrl_data = dict(proposed_value)
                    risk_mappings = ctrl_data.pop("risk_mappings", None)
                    risk_mapping = ctrl_data.pop("risk_mapping", None)
                    if risk_mappings is None and isinstance(risk_mapping, dict):
                        risk_mappings = [risk_mapping]
                    if not isinstance(risk_mappings, list):
                        risk_mappings = []

                    if "code" in ctrl_data and "control_code" not in ctrl_data:
                        ctrl_data["control_code"] = ctrl_data.pop("code")
                    if (
                        "criticality" in ctrl_data
                        and "criticality_code" not in ctrl_data
                    ):
                        ctrl_data["criticality_code"] = ctrl_data.pop("criticality")

                    req_id = ctrl_data.get("requirement_id")
                    req_code = ctrl_data.get("requirement_code")
                    if not req_id and req_code:
                        async with pool.acquire() as conn:
                            normalized_req_code = _normalize_entity_code(
                                req_code, fallback="REQ_001", uppercase=True
                            )
                            req_id = await _lookup_requirement_id_by_code(
                                conn, normalized_req_code
                            )
                    if not req_id and entity_type == "requirement" and entity_id:
                        req_id = str(entity_id)
                    if req_id:
                        ctrl_data["requirement_id"] = req_id

                    base_ctrl_code = ctrl_data.get("control_code")
                    if not base_ctrl_code and req_code:
                        req_prefix = _normalize_entity_code(
                            req_code, fallback="CTRL", uppercase=True
                        )
                        base_ctrl_code = f"{req_prefix}-01"
                    if not base_ctrl_code:
                        base_ctrl_code = ctrl_data.get("name") or "CTRL_001"
                    normalized_ctrl_code = _normalize_entity_code(
                        base_ctrl_code, fallback="CTRL_001", uppercase=True
                    )
                    ctrl_data["control_code"] = await _next_available_control_code(
                        normalized_ctrl_code
                    )
                    ctrl_data["name"] = str(
                        ctrl_data.get("name") or ctrl_data["control_code"]
                    )

                    criteria = _normalize_criteria(
                        ctrl_data.pop("acceptance_criteria", None)
                    )
                    props = (
                        dict(ctrl_data.get("properties", {}))
                        if isinstance(ctrl_data.get("properties"), dict)
                        else {}
                    )
                    if criteria is not None:
                        props["acceptance_criteria"] = json.dumps(criteria)
                    if props:
                        ctrl_data["properties"] = props

                    ctrl_data["control_category_code"] = (
                        _normalize_control_category_code(
                            ctrl_data.get("control_category_code", "risk_management"),
                            name=ctrl_data.get("name"),
                            description=ctrl_data.get("description"),
                            guidance=ctrl_data.get("guidance"),
                        )
                    )
                    ctrl_data.setdefault("criticality_code", "medium")
                    allowed_ctrl = {
                        f for f in _ctrl_schemas.CreateControlRequest.model_fields
                    }
                    ctrl_data = {
                        k: v for k, v in ctrl_data.items() if k in allowed_ctrl
                    }
                    ctrl_resp = await ctrl_service.create_control(
                        user_id=user_id,
                        tenant_key=tenant_key,
                        framework_id=framework_id,
                        request=_ctrl_schemas.CreateControlRequest(**ctrl_data),
                    )

                    for mapping in risk_mappings:
                        if isinstance(mapping, dict):
                            await _apply_risk_mapping(
                                mapping,
                                fallback_control_id=ctrl_resp.id,
                                fallback_requirement_id=ctrl_resp.requirement_id,
                            )
                    applied_this_change = True

                elif change_type == "add_risk_mapping" and isinstance(
                    proposed_value, dict
                ):
                    fallback_req_id = (
                        str(entity_id)
                        if entity_type == "requirement" and entity_id
                        else None
                    )
                    fallback_ctrl_id = (
                        str(entity_id)
                        if entity_type == "control" and entity_id
                        else None
                    )
                    await _apply_risk_mapping(
                        proposed_value,
                        fallback_control_id=fallback_ctrl_id,
                        fallback_requirement_id=fallback_req_id,
                    )
                    applied_this_change = True

                if applied_this_change:
                    applied += 1
                    async with pool.acquire() as conn:
                        await _append_progress(
                            conn,
                            job.id,
                            {
                                "event": "change_applied",
                                "change_type": change_type,
                                "entity_code": change.get("entity_code"),
                            },
                        )
                else:
                    raise ValueError(
                        f"Unsupported or empty change payload: {change_type}"
                    )

            except Exception as exc:
                failed += 1
                _logger.warning("apply_change.failed: %s change=%s", exc, change_type)
                async with pool.acquire() as conn:
                    await _append_progress(
                        conn,
                        job.id,
                        {
                            "event": "change_failed",
                            "change_type": change_type,
                            "entity_code": change.get("entity_code"),
                            "error": str(exc)[:200],
                        },
                    )

        if scope_org_id and scope_workspace_id:
            rr_sync = await _sync_workspace_risk_registry_links(
                pool=pool,
                tenant_key=tenant_key,
                user_id=user_id,
                framework_id=framework_id,
                scope_org_id=scope_org_id,
                scope_workspace_id=scope_workspace_id,
            )
            async with pool.acquire() as conn:
                await _append_progress(
                    conn,
                    job.id,
                    {
                        "event": "risk_registry_synced",
                        "org_id": scope_org_id,
                        "workspace_id": scope_workspace_id,
                        "risk_count": rr_sync.get("risk_count", 0),
                        "link_count": rr_sync.get("link_count", 0),
                    },
                )

        async with pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {_SESSIONS} SET status = 'complete', error_message = NULL, updated_at = NOW() "
                f"WHERE id = $1 AND tenant_key = $2",
                session_id,
                tenant_key,
            )
            await _set_output(
                conn,
                job.id,
                {
                    "requested_count": requested,
                    "applied_count": applied,
                    "failed_count": failed,
                    "framework_id": framework_id,
                },
            )

    except Exception as exc:
        _logger.exception("apply_changes.failed: %s", exc)
        async with pool.acquire() as conn:
            await conn.execute(
                f"UPDATE {_SESSIONS} SET status = 'failed', error_message = $2, updated_at = NOW() "
                f"WHERE id = $1 AND tenant_key = $3",
                session_id,
                str(exc)[:500],
                tenant_key,
            )
        raise


# ── Gap Analysis Job ──────────────────────────────────────────────────────────


async def handle_gap_analysis_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Runs gap analysis for a framework, stores report in job output_json.

    job.input_json must contain: framework_id, user_id, tenant_key
    Optional: user_context (str), attachment_ids (list[str])
    """
    inp = job.input_json
    framework_id = inp["framework_id"]
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    user_context = inp.get("user_context") or ""
    attachment_ids = inp.get("attachment_ids") or []

    # Load full framework data for analysis
    async with pool.acquire() as conn:
        fw_row = await conn.fetchrow(
            """
            SELECT f.id::text, f.framework_code, f.framework_type_code, f.framework_category_code,
                   p_name.property_value AS name
            FROM "05_grc_library"."10_fct_frameworks" f
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
                ON p_name.framework_id = f.id AND p_name.property_key = 'name'
            WHERE f.id = $1 AND f.tenant_key = $2
            """,
            framework_id,
            tenant_key,
        )
        if not fw_row:
            raise ValueError(f"Framework {framework_id} not found")

        reqs = await conn.fetch(
            """
            SELECT r.id::text, r.requirement_code AS code, r.parent_requirement_id::text AS parent_id,
                   p_name.property_value AS name, p_desc.property_value AS description
            FROM "05_grc_library"."12_fct_requirements" r
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_name
                ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_desc
                ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            WHERE r.framework_id = $1
            ORDER BY r.sort_order
            """,
            framework_id,
        )
        ctrls = await conn.fetch(
            """
            SELECT c.id::text, c.control_code AS code, c.requirement_id::text,
                   c.control_type, c.criticality_code, c.automation_potential,
                   p_name.property_value AS name,
                   p_ig.property_value AS implementation_guidance
            FROM "05_grc_library"."13_fct_controls" c
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_ig
                ON p_ig.control_id = c.id AND p_ig.property_key = 'implementation_guidance'
            WHERE c.framework_id = $1
            """,
            framework_id,
        )
        risk_links = await conn.fetch(
            """
            SELECT lrc.control_id::text, lrc.global_risk_id::text, lrc.mapping_type AS coverage_type,
                   gr.risk_code, p_title.property_value AS risk_title
            FROM "05_grc_library"."61_lnk_global_risk_control_mappings" lrc
            JOIN "05_grc_library"."50_fct_global_risks" gr ON gr.id = lrc.global_risk_id
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
                ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
            WHERE lrc.control_id = ANY(SELECT id FROM "05_grc_library"."13_fct_controls" WHERE framework_id = $1)
            """,
            framework_id,
        )

    framework_data = {
        "id": fw_row["id"],
        "name": fw_row["name"] or fw_row["framework_code"],
        "framework_code": fw_row["framework_code"],
        "framework_type_code": fw_row["framework_type_code"],
        "framework_category_code": fw_row["framework_category_code"],
        "requirements": [dict(r) for r in reqs],
        "controls": [dict(c) for c in ctrls],
        "risk_mappings": [dict(r) for r in risk_links],
    }

    # Resolve LLM config
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    config_repo = _repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(
        agent_type_code="framework_builder", org_id=None
    )

    async def _log(event: dict) -> None:
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, event)

    agent = (
        import_module("backend.20_ai.21_framework_builder.agent")
    ).FrameworkBuilderAgent(
        llm_config=llm_config,
        settings=settings,
        pool=pool,
    )

    await _log({"event": "stage_start", "stage": "gap_analysis", "label": "Gap Analysis"})
    await _log({"event": "analyzing_framework", "message": f"Loaded framework: {framework_data['name']}"})
    await _log({"event": "analyzing_framework",
                "message": f"Framework has {len(reqs)} requirements, {len(ctrls)} controls, {len(risk_links)} risk mappings"})

    if attachment_ids:
        await _log({"event": "indexing_documents",
                    "message": f"Indexing {len(attachment_ids)} reference document(s) via RAG…"})

    await _log({"event": "llm_call_start", "stage": "gap_analysis",
                "message": "Running gap analysis…",
                "model": getattr(llm_config, "model_id", "unknown")})

    report = await agent.run_gap_analysis(
        framework_data=framework_data,
        user_context=user_context,
        attachment_ids=attachment_ids if attachment_ids else None,
    )

    # Log LLM response meta from the agent
    meta = getattr(agent, "_last_llm_meta", None) or {}
    await _log({"event": "llm_call_complete", "stage": "gap_analysis",
                "message": "Gap analysis complete",
                "model": meta.get("model"),
                "prompt_tokens": meta.get("prompt_tokens"),
                "completion_tokens": meta.get("completion_tokens"),
                "total_tokens": meta.get("total_tokens"),
                "system_chars": meta.get("system_chars"),
                "user_chars": meta.get("user_chars"),
                "response_chars": meta.get("response_chars")})
    await _log({"event": "llm_response_preview", "stage": "gap_analysis",
                "preview": meta.get("response_preview", ""),
                "total_chars": meta.get("response_chars", 0)})

    report["framework_id"] = framework_id
    report["framework_name"] = framework_data["name"]

    import datetime

    report["generated_at"] = datetime.datetime.utcnow().isoformat()
    report.setdefault("requirement_count", len(reqs))
    report.setdefault("control_count", len(ctrls))
    report.setdefault("risk_count", len(risk_links))

    findings_count = len(report.get("findings", []))
    health_score = report.get("health_score", 0)
    await _log({"event": "gap_analysis_complete",
                "message": f"Found {findings_count} findings — health score: {health_score}/100",
                "health_score": health_score,
                "findings_count": findings_count})

    async with pool.acquire() as conn:
        await _set_output(conn, job.id, {"stats": report, "framework_id": framework_id})

    _logger.info(
        "gap_analysis.done", extra={"job_id": job.id, "framework_id": framework_id}
    )


# ── Enhance Diff Generation Job ───────────────────────────────────────────────


async def handle_enhance_diff_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Runs enhance diff analysis as a background job (no SSE connection required).

    Reads the existing framework, runs the LLM analysis, saves proposals to the
    session's enhance_diff column, then sets session status to phase2_review
    so the user can review proposals when they return.

    job.input_json must contain:
      session_id, user_id, tenant_key, framework_id,
      scope_org_id, scope_workspace_id,
      user_context (optional), attachment_ids (optional list)
    """
    inp = job.input_json
    session_id = inp["session_id"]
    user_id = inp["user_id"]
    tenant_key = inp["tenant_key"]
    framework_id = inp["framework_id"]
    scope_org_id = str(inp.get("scope_org_id") or "").strip() or None
    scope_workspace_id = str(inp.get("scope_workspace_id") or "").strip() or None
    user_context = inp.get("user_context") or ""
    attachment_ids = inp.get("attachment_ids") or []

    _SESSIONS = '"20_ai"."60_fct_builder_sessions"'

    async def _log(event: dict) -> None:
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, event)

    await _log({"event": "stage_start", "stage": "enhance_diff", "label": "Framework Evolution Analysis"})
    await _log({"event": "analyzing_framework", "message": "Loading framework data…"})

    # ── 1. Load full framework ─────────────────────────────────────────────────
    async with pool.acquire() as conn:
        fw_row = await conn.fetchrow(
            """
            SELECT f.id::text, f.framework_code, f.framework_type_code, f.framework_category_code,
                   p_name.property_value AS name, p_desc.property_value AS description,
                   p_accept.property_value AS acceptance_criteria
            FROM "05_grc_library"."10_fct_frameworks" f
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
                ON p_name.framework_id = f.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_desc
                ON p_desc.framework_id = f.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_accept
                ON p_accept.framework_id = f.id AND p_accept.property_key = 'acceptance_criteria'
            WHERE f.id = $1::uuid AND f.tenant_key = $2
              AND f.is_active = TRUE AND f.is_deleted = FALSE
            """,
            framework_id, tenant_key,
        )
        if not fw_row:
            raise ValueError(f"Framework {framework_id} not found or inactive")

        reqs = await conn.fetch(
            """
            SELECT r.requirement_code AS code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_acc.property_value  AS acceptance_criteria
            FROM "05_grc_library"."12_fct_requirements" r
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_name
                ON p_name.requirement_id = r.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_desc
                ON p_desc.requirement_id = r.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" p_acc
                ON p_acc.requirement_id = r.id AND p_acc.property_key = 'acceptance_criteria'
            WHERE r.framework_id = $1::uuid
            ORDER BY r.sort_order
            """,
            framework_id,
        )
        ctrls = await conn.fetch(
            """
            SELECT c.control_code AS code, c.control_type, c.criticality_code,
                   c.automation_potential, r.requirement_code AS requirement_code,
                   p_name.property_value AS name,
                   p_desc.property_value AS description,
                   p_guid.property_value AS guidance,
                   p_ig.property_value   AS implementation_guidance,
                   p_acc.property_value  AS acceptance_criteria
            FROM "05_grc_library"."13_fct_controls" c
            JOIN  "05_grc_library"."12_fct_requirements" r ON r.id = c.requirement_id
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
                ON p_name.control_id = c.id AND p_name.property_key = 'name'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
                ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guid
                ON p_guid.control_id = c.id AND p_guid.property_key = 'guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_ig
                ON p_ig.control_id = c.id AND p_ig.property_key = 'implementation_guidance'
            LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_acc
                ON p_acc.control_id = c.id AND p_acc.property_key = 'acceptance_criteria'
            WHERE c.framework_id = $1::uuid
            """,
            framework_id,
        )
        existing_risks = await conn.fetch(
            """
            SELECT gr.id::text, gr.risk_code, gr.risk_category_code,
                   p_title.property_value AS title
            FROM "05_grc_library"."50_fct_global_risks" gr
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
                ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
            WHERE gr.tenant_key = $1 AND gr.is_active = TRUE AND gr.is_deleted = FALSE
            ORDER BY gr.risk_code
            LIMIT 200
            """,
            tenant_key,
        )

    framework_data = {
        "id": fw_row["id"],
        "name": fw_row["name"] or fw_row["framework_code"],
        "framework_code": fw_row["framework_code"],
        "framework_type_code": fw_row["framework_type_code"],
        "framework_category_code": fw_row["framework_category_code"],
        "description": fw_row["description"] or "",
        "acceptance_criteria": fw_row["acceptance_criteria"] or "",
        "requirements": [dict(r) for r in reqs],
        "controls": [dict(c) for c in ctrls],
    }

    await _log({
        "event": "analyzing_framework",
        "message": f"Loaded {len(reqs)} requirements, {len(ctrls)} controls — starting AI analysis…",
    })

    # ── 2. Resolve LLM config + build agent ───────────────────────────────────
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    config_repo = _repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo,
        database_pool=pool,
        settings=settings,
    )
    llm_config = await resolver.resolve(agent_type_code="framework_builder", org_id=None)

    agent = (
        import_module("backend.20_ai.21_framework_builder.agent")
    ).FrameworkBuilderAgent(llm_config=llm_config, settings=settings, pool=pool)

    # ── 3. Stream enhance diff, writing progress events to job log ────────────
    await _log({"event": "llm_call_start", "stage": "enhance_analysis",
                "message": "AI analyzing framework for enhancements…",
                "model": getattr(llm_config, "model_id", "unknown")})

    proposals = []
    async for chunk in agent.stream_enhance_diff(
        framework_data=framework_data,
        existing_risks=[dict(r) for r in existing_risks],
        user_context=user_context,
        attachment_ids=attachment_ids,
    ):
        for data in _parse_sse_events(chunk):
            await _log(data)
            if data.get("event") == "enhance_complete":
                proposals = data.get("proposals", [])

    # ── 4. Persist proposals to session ───────────────────────────────────────
    import json as _json2
    async with pool.acquire() as conn:
        await conn.execute(
            f"""
            UPDATE {_SESSIONS}
            SET enhance_diff = $1::jsonb,
                status       = 'phase2_review',
                job_id       = $2::uuid,
                updated_at   = NOW()
            WHERE id = $3::uuid AND tenant_key = $4
            """,
            _json2.dumps(proposals),
            job.id,
            session_id,
            tenant_key,
        )

    await _log({
        "event": "enhance_complete",
        "proposal_count": len(proposals),
        "message": f"Analysis complete — {len(proposals)} enhancement proposals ready for review",
    })

    async with pool.acquire() as conn:
        await _set_output(conn, job.id, {
            "proposal_count": len(proposals),
            "session_id": session_id,
        })

    _logger.info(
        "enhance_diff.done",
        extra={"job_id": job.id, "session_id": session_id, "proposal_count": len(proposals)},
    )


# ── Phase 1: Hierarchy Generation (background job) ──────────────────────────

async def handle_hierarchy_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Runs Phase 1 hierarchy generation as a background job (no SSE connection).
    Calls agent.stream_hierarchy(), parses chunks, writes progress to both the
    job's output_json.creation_log and the session's activity_log, then saves
    the hierarchy to the session's proposed_hierarchy column.
    """
    inp = job.input_json
    session_id = inp["session_id"]
    tenant_key = inp["tenant_key"]

    async def _log(event: dict) -> None:
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, event)

    async def _log_to_session(events: list[dict]) -> None:
        if not events:
            return
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE {_SESSIONS}
                    SET activity_log = COALESCE(activity_log, '[]'::jsonb) || $1::jsonb,
                        updated_at = NOW()
                    WHERE id = $2::uuid AND tenant_key = $3
                    """,
                    json.dumps(events),
                    session_id,
                    tenant_key,
                )
        except Exception as exc:
            _logger.warning("hierarchy_job: flush_session_activity failed: %s", exc)

    await _log({"event": "stage_start", "stage": "hierarchy", "label": "Requirement Hierarchy Generation"})

    # ── 1. Fetch existing risks for context ──────────────────────────────────
    async with pool.acquire() as conn:
        risk_rows = await conn.fetch(
            """
            SELECT gr.id::text, gr.risk_code, gr.risk_category_code,
                   p_title.property_value AS title
            FROM "05_grc_library"."50_fct_global_risks" gr
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
                ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
            WHERE gr.tenant_key = $1 AND gr.is_active = TRUE AND gr.is_deleted = FALSE
            ORDER BY gr.risk_code LIMIT 200
            """,
            tenant_key,
        )
    existing_risks = [dict(r) for r in risk_rows]

    # ── 2. Resolve LLM config + build agent ──────────────────────────────────
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    config_repo = _repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo, database_pool=pool, settings=settings,
    )
    llm_config = await resolver.resolve(agent_type_code="framework_builder", org_id=None)
    agent = (
        import_module("backend.20_ai.21_framework_builder.agent")
    ).FrameworkBuilderAgent(llm_config=llm_config, settings=settings, pool=pool)

    await _log({"event": "llm_call_start", "stage": "hierarchy",
                "message": "Generating requirement hierarchy…",
                "model": getattr(llm_config, "model_id", "unknown")})

    # ── 3. Stream hierarchy, capturing events ────────────────────────────────
    hierarchy_data = None
    session_log_buffer: list[dict] = []
    async for chunk in agent.stream_hierarchy(
        framework_name=inp.get("framework_name", ""),
        framework_type_code=inp.get("framework_type_code", "custom"),
        framework_category_code=inp.get("framework_category_code", "security"),
        user_context=inp.get("user_context", ""),
        attachment_ids=inp.get("attachment_ids", []),
        existing_risks=existing_risks,
    ):
        for data in _parse_sse_events(chunk):
            await _log(data)
            session_log_buffer.append(data)
            if len(session_log_buffer) >= 5:
                await _log_to_session(session_log_buffer)
                session_log_buffer.clear()
            if data.get("event") == "phase1_complete":
                hierarchy_data = data.get("hierarchy")

    # Final flush
    if session_log_buffer:
        await _log_to_session(session_log_buffer)

    # ── 4. Persist hierarchy to session ──────────────────────────────────────
    if hierarchy_data:
        # If hierarchy includes embedded controls/risks (unified call), skip straight
        # to phase2_review so the user doesn't see a manual "Construct Controls" step.
        controls = hierarchy_data.get("controls", [])
        risks = hierarchy_data.get("risks", [])
        risk_mappings = hierarchy_data.get("risk_mappings", [])
        target_status = "phase2_review" if controls else "phase1_review"

        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_SESSIONS}
                SET proposed_hierarchy = $1::jsonb,
                    status = $2,
                    job_id = $3::uuid,
                    updated_at = NOW()
                WHERE id = $4::uuid AND tenant_key = $5
                """,
                json.dumps(hierarchy_data),
                target_status,
                job.id,
                session_id,
                tenant_key,
            )
        if controls:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE {_SESSIONS}
                    SET proposed_controls = $1::jsonb,
                        proposed_risks = $2::jsonb,
                        proposed_risk_mappings = $3::jsonb,
                        updated_at = NOW()
                    WHERE id = $4::uuid AND tenant_key = $5
                    """,
                    json.dumps(controls),
                    json.dumps(risks),
                    json.dumps(risk_mappings),
                    session_id,
                    tenant_key,
                )
    else:
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_SESSIONS}
                SET status = 'failed', job_id = $1::uuid, updated_at = NOW()
                WHERE id = $2::uuid AND tenant_key = $3
                """,
                job.id, session_id, tenant_key,
            )

    req_count = len((hierarchy_data or {}).get("requirements", []))
    await _log({"event": "phase1_complete", "requirement_count": req_count,
                "message": f"Hierarchy complete — {req_count} requirements proposed"})

    async with pool.acquire() as conn:
        await _set_output(conn, job.id, {"requirement_count": req_count, "session_id": session_id})

    _logger.info("hierarchy_job.done",
                 extra={"job_id": job.id, "session_id": session_id, "req_count": req_count})


# ── Phase 2: Control Generation (background job) ────────────────────────────

async def handle_controls_job(*, job, pool: asyncpg.Pool, settings) -> None:
    """
    Runs Phase 2 control generation as a background job (no SSE connection).
    Reads the session's proposed_hierarchy, calls agent.stream_controls_and_risks(),
    writes progress to job log + session activity_log, then saves controls/risks/mappings.
    """
    inp = job.input_json
    session_id = inp["session_id"]
    tenant_key = inp["tenant_key"]

    async def _log(event: dict) -> None:
        async with pool.acquire() as conn:
            await _append_progress(conn, job.id, event)

    async def _log_to_session(events: list[dict]) -> None:
        if not events:
            return
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    f"""
                    UPDATE {_SESSIONS}
                    SET activity_log = COALESCE(activity_log, '[]'::jsonb) || $1::jsonb,
                        updated_at = NOW()
                    WHERE id = $2::uuid AND tenant_key = $3
                    """,
                    json.dumps(events),
                    session_id,
                    tenant_key,
                )
        except Exception as exc:
            _logger.warning("controls_job: flush_session_activity failed: %s", exc)

    await _log({"event": "stage_start", "stage": "controls", "label": "Control & Risk Generation"})

    # ── 1. Load session hierarchy + existing risks ───────────────────────────
    async with pool.acquire() as conn:
        session_row = await conn.fetchrow(
            f"""
            SELECT proposed_hierarchy, node_overrides
            FROM {_SESSIONS}
            WHERE id = $1::uuid AND tenant_key = $2
            """,
            session_id, tenant_key,
        )
        if not session_row or not session_row["proposed_hierarchy"]:
            raise ValueError(f"Session {session_id} has no proposed hierarchy")

        hierarchy = json.loads(session_row["proposed_hierarchy"]) if isinstance(
            session_row["proposed_hierarchy"], str) else session_row["proposed_hierarchy"]
        node_overrides = json.loads(session_row["node_overrides"]) if isinstance(
            session_row["node_overrides"], str) else (session_row["node_overrides"] or {})

        risk_rows = await conn.fetch(
            """
            SELECT gr.id::text, gr.risk_code, gr.risk_category_code,
                   p_title.property_value AS title
            FROM "05_grc_library"."50_fct_global_risks" gr
            LEFT JOIN "05_grc_library"."56_dtl_global_risk_properties" p_title
                ON p_title.global_risk_id = gr.id AND p_title.property_key = 'title'
            WHERE gr.tenant_key = $1 AND gr.is_active = TRUE AND gr.is_deleted = FALSE
            ORDER BY gr.risk_code LIMIT 200
            """,
            tenant_key,
        )
    existing_risks = [dict(r) for r in risk_rows]

    # ── 2. Resolve LLM config + build agent ──────────────────────────────────
    _resolver_mod = import_module("backend.20_ai.12_agent_config.resolver")
    _repo_mod = import_module("backend.20_ai.12_agent_config.repository")
    config_repo = _repo_mod.AgentConfigRepository()
    resolver = _resolver_mod.AgentConfigResolver(
        repository=config_repo, database_pool=pool, settings=settings,
    )
    llm_config = await resolver.resolve(agent_type_code="framework_builder", org_id=None)
    agent = (
        import_module("backend.20_ai.21_framework_builder.agent")
    ).FrameworkBuilderAgent(llm_config=llm_config, settings=settings, pool=pool)

    await _log({"event": "llm_call_start", "stage": "controls",
                "message": "Generating controls and risk mappings…",
                "model": getattr(llm_config, "model_id", "unknown")})

    # ── 3. Stream controls, capturing events ─────────────────────────────────
    all_controls: list = []
    new_risks: list = []
    risk_mappings: list = []
    session_log_buffer: list[dict] = []

    async for chunk in agent.stream_controls_and_risks(
        framework_name=inp.get("framework_name", ""),
        framework_type_code=inp.get("framework_type_code", "custom"),
        hierarchy=hierarchy,
        node_overrides=inp.get("node_overrides", {}),
        user_context=inp.get("user_context", ""),
        attachment_ids=inp.get("attachment_ids", []),
        existing_risks=existing_risks,
    ):
        for data in _parse_sse_events(chunk):
            await _log(data)
            session_log_buffer.append(data)
            if len(session_log_buffer) >= 5:
                await _log_to_session(session_log_buffer)
                session_log_buffer.clear()
            if data.get("event") == "phase2_complete":
                all_controls = data.get("all_controls", [])
                new_risks = data.get("new_risks", [])
                risk_mappings = data.get("risk_mappings", [])

    if session_log_buffer:
        await _log_to_session(session_log_buffer)

    # ── 4. Persist results to session ────────────────────────────────────────
    if all_controls:
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_SESSIONS}
                SET proposed_controls = $1::jsonb,
                    proposed_risks = $2::jsonb,
                    proposed_risk_mappings = $3::jsonb,
                    status = 'phase2_review',
                    job_id = $4::uuid,
                    updated_at = NOW()
                WHERE id = $5::uuid AND tenant_key = $6
                """,
                json.dumps(all_controls),
                json.dumps(new_risks),
                json.dumps(risk_mappings),
                job.id,
                session_id,
                tenant_key,
            )
    else:
        async with pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {_SESSIONS}
                SET status = 'failed', job_id = $1::uuid, updated_at = NOW()
                WHERE id = $2::uuid AND tenant_key = $3
                """,
                job.id, session_id, tenant_key,
            )

    await _log({"event": "phase2_complete", "control_count": len(all_controls),
                "risk_count": len(new_risks), "risk_mapping_count": len(risk_mappings),
                "message": f"Controls complete — {len(all_controls)} controls, {len(new_risks)} risks"})

    async with pool.acquire() as conn:
        await _set_output(conn, job.id, {
            "control_count": len(all_controls), "risk_count": len(new_risks),
            "risk_mapping_count": len(risk_mappings), "session_id": session_id,
        })

    _logger.info("controls_job.done",
                 extra={"job_id": job.id, "session_id": session_id,
                        "control_count": len(all_controls)})
