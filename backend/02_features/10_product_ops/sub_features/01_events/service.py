"""
product_ops.events — service layer.

ingest_batch is the heart of the module:
  1. Resolve project_key → (org_id, workspace_id) via vault.secrets.get
  2. Drop all events if DNT requested
  3. Enforce cardinality cap (default 500 distinct event_names per workspace per day)
  4. Validate UTM length (256 chars)
  5. Truncate client IP per privacy contract
  6. Upsert visitor with first/last touch
  7. Bulk insert events + touches
  8. Emit ONE audit summary per batch (per-event audit bypassed per ADR-030)

All cross-feature calls go through run_node (NCP v1).
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any
from importlib import import_module
from urllib.parse import parse_qs, urlparse

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.repository"
)
_schemas: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.01_events.schemas"
)

logger = logging.getLogger("tennetctl.product_ops")

DEFAULT_DISTINCT_EVENT_NAME_CAP = 500
CARDINALITY_VAULT_KEY = "product_ops.limits.distinct_event_names_per_day"
PROJECT_KEY_VAULT_PREFIX = "product_ops.project_keys."


# ── Helpers ──────────────────────────────────────────────────────────

def _strip_tz(dt: datetime) -> datetime:
    """DB columns are TIMESTAMP (tz-naive UTC). Strip incoming tzinfo."""
    if dt.tzinfo is None:
        return dt
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def _truncate_ip(raw_ip: str | None) -> str | None:
    """
    Privacy default: truncate IPv4 to /24, IPv6 to /48. Hard-coded for v1;
    raw-IP workspace toggle is deferred to a 45-x follow-up.
    """
    if not raw_ip:
        return None
    if ":" in raw_ip:  # IPv6
        parts = raw_ip.split(":")
        # Keep first 3 hextets (≈ /48), zero the rest
        kept = parts[:3] + ["0"] * max(0, len(parts) - 3)
        return ":".join(kept)
    parts = raw_ip.split(".")
    if len(parts) != 4:
        return None
    return ".".join(parts[:3] + ["0"]) + "/24"


def _extract_utm_from_url(page_url: str | None) -> dict[str, str | None]:
    """
    Pull utm_source/medium/campaign/term/content from the page_url query string.
    Explicit utm_* fields on the event take precedence; this is the fallback.
    """
    if not page_url:
        return {k: None for k in ("source", "medium", "campaign", "term", "content")}
    try:
        qs = parse_qs(urlparse(page_url).query)
    except Exception:
        return {k: None for k in ("source", "medium", "campaign", "term", "content")}
    return {
        "source":   (qs.get("utm_source") or [None])[0],
        "medium":   (qs.get("utm_medium") or [None])[0],
        "campaign": (qs.get("utm_campaign") or [None])[0],
        "term":     (qs.get("utm_term") or [None])[0],
        "content":  (qs.get("utm_content") or [None])[0],
    }


# ── Project key resolution ──────────────────────────────────────────

async def _resolve_project_key(pool: Any, ctx: Any, project_key: str) -> tuple[str, str]:
    """
    Resolve project_key → (org_id, workspace_id) via vault.secrets.get.

    The vault entry stores a JSON blob: {"org_id": "...", "workspace_id": "..."}.
    Project keys are workspace-scoped and operator-provisioned.

    Returns (org_id, workspace_id). Raises AppError on miss/malformed.
    """
    vault_key = f"{PROJECT_KEY_VAULT_PREFIX}{project_key}"
    try:
        result = await _catalog.run_node(
            pool, "vault.secrets.get", ctx, {"key": vault_key},
        )
    except Exception as e:
        # Don't leak vault internals to the client; log + surface UNAUTHORIZED.
        logger.info("project_key resolution failed for %s: %s", project_key, e)
        raise _errors.AppError(
            "PRODUCT_OPS.UNKNOWN_PROJECT_KEY",
            "Unknown or invalid project_key.",
            status_code=401,
        ) from e

    plaintext = result.get("plaintext") or result.get("value")
    if not plaintext:
        raise _errors.AppError(
            "PRODUCT_OPS.UNKNOWN_PROJECT_KEY",
            "Unknown or invalid project_key.",
            status_code=401,
        )
    try:
        parsed = json.loads(plaintext)
        return parsed["org_id"], parsed["workspace_id"]
    except (json.JSONDecodeError, KeyError) as e:
        raise _errors.AppError(
            "PRODUCT_OPS.MALFORMED_PROJECT_KEY",
            "Project key resolves to malformed config.",
            status_code=500,
        ) from e


async def _get_cardinality_cap(pool: Any, ctx: Any) -> int:
    """Read distinct-event-name cap from vault; default to 500 if absent."""
    try:
        result = await _catalog.run_node(
            pool, "vault.secrets.get", ctx, {"key": CARDINALITY_VAULT_KEY},
        )
        plaintext = result.get("plaintext") or result.get("value")
        return int(plaintext)
    except Exception:
        return DEFAULT_DISTINCT_EVENT_NAME_CAP


# ── Main entry point ────────────────────────────────────────────────

async def ingest_batch(
    pool: Any,
    conn: Any,
    ctx: Any,
    batch: Any,
    *,
    client_ip: str | None = None,
) -> dict:
    """
    Process a TrackBatchIn. conn is the caller's transactional connection
    (the ingest node runs tx=own — runner provides a fresh conn in its own tx).

    Returns {"accepted": int, "dropped_dnt": int, "dropped_capped": int}.
    Raises AppError for client-correctable errors (bad project_key, cap exceeded).
    """
    # 1. DNT short-circuit BEFORE any work.
    if batch.dnt:
        return {"accepted": 0, "dropped_dnt": len(batch.events), "dropped_capped": 0}

    # 2. Resolve project_key.
    org_id, workspace_id = await _resolve_project_key(pool, ctx, batch.project_key)

    # 3. Pre-flight UTM validation (whole-batch atomic — reject all on any violation).
    for ev in batch.events:
        for utm_field in ("utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content"):
            v = getattr(ev, utm_field, None)
            if v is not None and len(v) > 256:
                raise _errors.AppError(
                    "PRODUCT_OPS.UTM_TOO_LONG",
                    f"{utm_field} exceeds 256 characters; reject batch.",
                    status_code=400,
                )

    # 4. Cardinality cap pre-check. If the batch contains a new distinct event_name
    # that would push us over the cap, reject the batch.
    cap = await _get_cardinality_cap(pool, ctx)
    distinct_now = await _repo.count_distinct_event_names_today(conn, workspace_id)
    incoming_names = {e.event_name for e in batch.events if e.event_name}
    # We can't know in advance which names are already counted vs new without
    # an extra query; conservative check: if (current count + names in batch) > cap,
    # query precisely. Cheap path first.
    if distinct_now + len(incoming_names) > cap:
        # Precise check: which incoming names are already in today's partition?
        rows = await conn.fetch(
            """
            SELECT DISTINCT event_name
              FROM "10_product_ops"."60_evt_product_events"
             WHERE workspace_id = $1
               AND event_name = ANY($2::text[])
               AND occurred_at >= CURRENT_DATE
               AND occurred_at <  CURRENT_DATE + INTERVAL '1 day'
            """,
            workspace_id, list(incoming_names),
        )
        already_seen = {r["event_name"] for r in rows}
        new_names = incoming_names - already_seen
        if distinct_now + len(new_names) > cap:
            raise _errors.AppError(
                "PRODUCT_OPS.EVENT_NAME_CAP_EXCEEDED",
                f"Workspace exceeded distinct event_name cap ({cap}/day). Adjust event taxonomy or raise the cap via vault.",
                status_code=429,
            )

    # 5. Truncate client IP (added to event metadata).
    truncated_ip = _truncate_ip(client_ip)

    # 6. Build event + touch rows. Visitor upsert per anonymous_id (dedupe within batch).
    visitors_seen: dict[str, str] = {}  # anonymous_id → visitor_id
    event_rows: list[dict] = []
    touch_rows: list[dict] = []

    for ev in batch.events:
        # Resolve UTM (explicit > URL-extracted)
        url_utm = _extract_utm_from_url(ev.page_url)
        utm_source   = ev.utm_source   or url_utm["source"]
        utm_medium   = ev.utm_medium   or url_utm["medium"]
        utm_campaign = ev.utm_campaign or url_utm["campaign"]
        utm_term     = ev.utm_term     or url_utm["term"]
        utm_content  = ev.utm_content  or url_utm["content"]

        utm_source_id: int | None = None
        if utm_source:
            utm_source_id = await _repo.intern_attribution_source(conn, utm_source)

        first_touch = None
        if utm_source or ev.referrer:
            first_touch = {
                "utm_source_id": utm_source_id,
                "utm_medium": utm_medium,
                "utm_campaign": utm_campaign,
                "utm_term": utm_term,
                "utm_content": utm_content,
                "referrer": ev.referrer,
                "landing_url": ev.page_url,
            }

        occurred_at = _strip_tz(ev.occurred_at)

        # Upsert visitor (sticky first-touch via INSERT … ON CONFLICT)
        if ev.anonymous_id not in visitors_seen:
            new_visitor_id = _core_id.uuid7()
            visitor_id = await _repo.upsert_visitor(
                conn,
                visitor_id=new_visitor_id,
                anonymous_id=ev.anonymous_id,
                workspace_id=workspace_id,
                org_id=org_id,
                occurred_at=occurred_at,
                first_touch=first_touch,
            )
            visitors_seen[ev.anonymous_id] = visitor_id
        else:
            visitor_id = visitors_seen[ev.anonymous_id]

        # Build event row. SDK contract: caller's "properties" → DB column "metadata".
        # If we have a truncated IP, attach it under a sentinel key.
        metadata = dict(ev.properties)
        if truncated_ip:
            metadata.setdefault("_ip_truncated", truncated_ip)

        event_rows.append({
            "id": _core_id.uuid7(),
            "visitor_id": visitor_id,
            "user_id": None,           # 45-02 will resolve via identify
            "session_id": None,        # 45-02 will introduce session boundaries
            "org_id": org_id,
            "workspace_id": workspace_id,
            "event_kind_id": _schemas.EVENT_KIND_ID[ev.kind],
            "event_name": ev.event_name,
            "occurred_at": occurred_at,
            "page_url": ev.page_url,
            "referrer": ev.referrer,
            "metadata": metadata,
        })

        # Touch row only when there's actual attribution signal.
        if utm_source or ev.referrer:
            touch_rows.append({
                "id": _core_id.uuid7(),
                "visitor_id": visitor_id,
                "org_id": org_id,
                "workspace_id": workspace_id,
                "occurred_at": occurred_at,
                "utm_source_id": utm_source_id,
                "utm_medium": utm_medium,
                "utm_campaign": utm_campaign,
                "utm_term": utm_term,
                "utm_content": utm_content,
                "referrer": ev.referrer,
                "landing_url": ev.page_url,
            })

    # 7. Bulk inserts.
    accepted = await _repo.bulk_insert_events(conn, event_rows)
    await _repo.bulk_insert_touches(conn, touch_rows)

    # 7a. Side-effect of identify/alias kinds: mutate visitor identity.
    # Done after the event row lands so the audit summary's count includes them.
    for ev in batch.events:
        if ev.kind == "identify":
            user_id = (ev.properties or {}).get("user_id")
            if isinstance(user_id, str) and user_id:
                vid = visitors_seen.get(ev.anonymous_id)
                if vid:
                    await _repo.set_visitor_user_id(
                        conn, visitor_id=vid, user_id=user_id,
                    )
        elif ev.kind == "alias":
            alias_aid = (ev.properties or {}).get("alias_anonymous_id")
            if isinstance(alias_aid, str) and alias_aid:
                vid = visitors_seen.get(ev.anonymous_id)
                if vid:
                    await _repo.add_visitor_alias(
                        conn, visitor_id=vid, alias_anonymous_id=alias_aid, org_id=org_id,
                    )

    # 7b. Fan out each event to active destinations (Phase 55).
    # Imported lazily to keep cohort/destination optional; failures never
    # affect ingest (try/except wraps the whole fan-out).
    try:
        from importlib import import_module as _im
        _dest_svc: Any = _im(
            "backend.02_features.10_product_ops.sub_features.09_destinations.service"
        )
        for r in event_rows:
            await _dest_svc.fan_out_event(pool, workspace_id=workspace_id, event=r)
    except Exception:
        logger.info("destination fan-out failed; ingest continues", exc_info=True)

    # 8. ONE audit summary per batch (ADR-030 hot-path bypass).
    # We need a scoped ctx for audit emission. Use the resolved org/workspace,
    # mark category=integration (system-to-system event with no human actor),
    # outcome=success. The audit CHECK accepts setup OR failure as scope bypass;
    # for integration we still need user_id+session_id+org_id+workspace_id.
    # Anonymous browser ingest has no user/session. Solution: emit at category=
    # 'integration' with outcome='failure' is wrong (it's a success). Cleanest:
    # emit at category='setup' which bypasses scope CHECK entirely. setup is for
    # system-internal events that happen outside a user session — fits exactly.
    from dataclasses import replace as _replace
    audit_ctx = _replace(
        ctx,
        org_id=org_id,
        workspace_id=workspace_id,
        audit_category="setup",  # scope-bypass: anonymous ingest has no user/session
    )
    try:
        await _catalog.run_node(
            pool, "audit.events.emit", audit_ctx,
            {
                "event_key": "product_ops.events.ingested",
                "outcome": "success",
                "metadata": {
                    "batch_size": accepted,
                    "workspace_id": workspace_id,
                    "touches": len(touch_rows),
                    "distinct_visitors": len(visitors_seen),
                },
            },
        )
    except Exception:
        # Audit failure must not fail the ingest write — same contract as
        # vault audit-of-reads (Phase 7 Plan 01 precedent).
        logger.info("product_ops.events.ingested audit emit failed", exc_info=True)

    return {
        "accepted": accepted,
        "dropped_dnt": 0,
        "dropped_capped": 0,
    }


async def identify_visitor(
    conn: Any,
    *,
    anonymous_id: str,
    user_id: str,
    org_id: str,
    workspace_id: str,
) -> dict:
    """
    Resolve an anonymous visitor to an IAM user. Two paths:
      1. Visitor row exists for this anonymous_id → set user_id.
      2. Visitor row doesn't exist → create one with user_id pre-set.
    Returns {visitor_id, was_new}.
    """
    # Best-effort visitor upsert (no first-touch — identify is downstream of first event)
    visitor_id = await _repo.upsert_visitor(
        conn,
        visitor_id=_core_id.uuid7(),
        anonymous_id=anonymous_id,
        workspace_id=workspace_id,
        org_id=org_id,
        occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
        first_touch=None,
    )
    await _repo.set_visitor_user_id(conn, visitor_id=visitor_id, user_id=user_id)
    return {"visitor_id": visitor_id, "user_id": user_id}


async def add_alias(
    conn: Any,
    *,
    primary_anonymous_id: str,
    alias_anonymous_id: str,
    org_id: str,
    workspace_id: str,
) -> dict:
    """
    Attach a secondary anonymous_id to the canonical visitor. Many-to-one.
    No race-resolution: if both anonymous_ids resolve to different visitors
    (cross-device), we keep the alias row pointing at the older visitor.
    """
    visitor_id = await _repo.upsert_visitor(
        conn,
        visitor_id=_core_id.uuid7(),
        anonymous_id=primary_anonymous_id,
        workspace_id=workspace_id,
        org_id=org_id,
        occurred_at=datetime.now(timezone.utc).replace(tzinfo=None),
        first_touch=None,
    )
    await _repo.add_visitor_alias(
        conn, visitor_id=visitor_id, alias_anonymous_id=alias_anonymous_id, org_id=org_id,
    )
    return {"visitor_id": visitor_id, "alias_anonymous_id": alias_anonymous_id}


async def list_events(
    conn: Any,
    *,
    workspace_id: str,
    limit: int = 100,
    cursor: str | None = None,
) -> dict:
    """Read-path service. Returns {events, cursor}."""
    rows = await _repo.list_events(
        conn, workspace_id=workspace_id, limit=limit, cursor=cursor,
    )
    next_cursor = None
    if len(rows) == limit:
        next_cursor = rows[-1]["occurred_at"].isoformat()
    return {"events": rows, "cursor": next_cursor}


async def resolve_attribution(
    conn: Any,
    *,
    visitor_id: str,
) -> dict:
    """Return {first_touch, last_touch} for a visitor. Used by Phase 48 funnels."""
    visitor = await _repo.get_visitor_by_id(conn, visitor_id)
    if not visitor:
        return {"visitor_id": visitor_id, "first_touch": None, "last_touch": None}

    first_touch = None
    if visitor.get("first_utm_source") or visitor.get("first_referrer"):
        first_touch = {
            "occurred_at": visitor["first_seen"],
            "utm_source": visitor.get("first_utm_source"),
            "utm_medium": visitor.get("first_utm_medium"),
            "utm_campaign": visitor.get("first_utm_campaign"),
            "utm_term": visitor.get("first_utm_term"),
            "utm_content": visitor.get("first_utm_content"),
            "referrer": visitor.get("first_referrer"),
            "landing_url": visitor.get("first_landing_url"),
        }

    last_row = await _repo.get_last_touch_for_visitor(conn, visitor_id)
    last_touch = None
    if last_row:
        last_touch = {
            "occurred_at": last_row["occurred_at"],
            "utm_source": last_row.get("utm_source"),
            "utm_medium": last_row.get("utm_medium"),
            "utm_campaign": last_row.get("utm_campaign"),
            "utm_term": last_row.get("utm_term"),
            "utm_content": last_row.get("utm_content"),
            "referrer": last_row.get("referrer"),
            "landing_url": last_row.get("landing_url"),
        }

    return {
        "visitor_id": visitor_id,
        "first_touch": first_touch,
        "last_touch": last_touch,
    }
