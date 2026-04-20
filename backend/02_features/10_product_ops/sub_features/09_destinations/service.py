"""Destination service: CRUD + outbound HTTP fan-out + HMAC sign + delivery log."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import logging
import time
from importlib import import_module
from typing import Any

import httpx

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.09_destinations.repository"
)
_eligibility: Any = import_module(
    "backend.02_features.10_product_ops.sub_features.05_promos.eligibility"
)

logger = logging.getLogger("tennetctl.product_ops.destinations")

DEFAULT_TIMEOUT_S = 2.0
RESPONSE_BODY_MAX_BYTES = 1024


# ── CRUD ───────────────────────────────────────────────────────────

async def create_destination(
    pool: Any, conn: Any, ctx: Any, *,
    body: Any, org_id: str, workspace_id: str, created_by: str,
) -> dict:
    try:
        row = await _repo.insert_destination(
            conn,
            dest_id=_core_id.uuid7(),
            slug=body.slug, name=body.name, description=body.description,
            org_id=org_id, workspace_id=workspace_id,
            kind=body.kind, url=body.url, secret=body.secret,
            headers=body.headers or {}, filter_rule=body.filter_rule or {},
            retry_policy=body.retry_policy or {"max_attempts": 1, "backoff_ms": 1000},
            created_by=created_by,
        )
    except Exception as e:
        if "uq_fct_destinations_workspace_slug" in str(e):
            raise _errors.AppError(
                "PRODUCT_OPS.DESTINATION_SLUG_TAKEN",
                f"Destination slug {body.slug!r} already exists.", status_code=409,
            ) from e
        raise

    try:
        await _catalog.run_node(
            pool, "audit.events.emit", ctx,
            {"event_key": "product_ops.destinations.created", "outcome": "success",
             "metadata": {"destination_id": row["id"], "slug": body.slug, "kind": body.kind}},
        )
    except Exception:
        logger.info("audit emit failed for destination create", exc_info=True)
    return row


async def update_destination(
    pool: Any, conn: Any, ctx: Any, *, dest_id: str, body: Any,
) -> dict | None:
    fields: dict[str, Any] = {}
    for k in ("name", "description", "url", "secret", "headers",
              "filter_rule", "retry_policy", "is_active", "deleted_at"):
        v = getattr(body, k)
        if v is not None:
            fields[k] = v
    row = await _repo.update_destination(conn, dest_id=dest_id, fields=fields)
    if row:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.destinations.updated", "outcome": "success",
                 "metadata": {"destination_id": dest_id, "fields": list(fields.keys())}},
            )
        except Exception:
            logger.info("audit emit failed for destination update", exc_info=True)
    return row


async def delete_destination(pool: Any, conn: Any, ctx: Any, *, dest_id: str) -> bool:
    ok = await _repo.soft_delete_destination(conn, dest_id)
    if ok:
        try:
            await _catalog.run_node(
                pool, "audit.events.emit", ctx,
                {"event_key": "product_ops.destinations.deleted", "outcome": "success",
                 "metadata": {"destination_id": dest_id}},
            )
        except Exception:
            logger.info("audit emit failed for destination delete", exc_info=True)
    return ok


# ── Fan-out ────────────────────────────────────────────────────────

def _sign(secret: str, body_bytes: bytes) -> str:
    """HMAC-SHA256 of the request body, hex-encoded."""
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


def _passes_filter(filter_rule: dict, event: dict) -> bool:
    """Apply the destination's filter_rule to a single event using the
    eligibility evaluator. Empty rule = all events pass."""
    if not filter_rule:
        return True
    ctx = {"event": event}
    return bool(_eligibility.evaluate(filter_rule, ctx))


def _stringify(v: Any) -> Any:
    """Recursively convert datetimes to ISO strings so json.dumps doesn't choke."""
    from datetime import datetime, date
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, dict):
        return {k: _stringify(x) for k, x in v.items()}
    if isinstance(v, list):
        return [_stringify(x) for x in v]
    return v


def _format_payload(dest: dict, event: dict) -> dict:
    """Build the payload that gets POSTed. Slack gets a special shape; others
    get the raw event. All datetime values are ISO-stringified."""
    if dest["kind"] == "slack":
        text = (
            f"*{event.get('event_name') or event.get('event_kind', 'event')}* "
            f"from `{(event.get('visitor_id') or '?')[:12]}`\n"
            f"```{json.dumps(_stringify(event.get('metadata') or {}), indent=2)[:800]}```"
        )
        return {"text": text}
    return _stringify({
        "event": {
            "id": event.get("id"),
            "kind": event.get("event_kind") or event.get("event_kind_id"),
            "name": event.get("event_name"),
            "occurred_at": event.get("occurred_at"),
            "visitor_id": event.get("visitor_id"),
            "user_id": event.get("user_id"),
            "workspace_id": event.get("workspace_id"),
            "page_url": event.get("page_url"),
            "referrer": event.get("referrer"),
            "metadata": event.get("metadata") or {},
        },
        "destination": {"slug": dest["slug"], "kind": dest["kind"]},
    })


async def deliver_one(
    conn: Any, *, dest: dict, event: dict, http_client: httpx.AsyncClient,
) -> str:
    """Send a single event to a single destination. Always logs a delivery row.
    Returns the final status."""
    started = time.perf_counter()
    delivery_id = _core_id.uuid7()

    if not _passes_filter(dest["filter_rule"], event):
        await _repo.insert_delivery(
            conn,
            delivery_id=delivery_id, destination_id=dest["id"],
            event_id=event.get("id"),
            org_id=dest["org_id"], workspace_id=dest["workspace_id"],
            status="rejected_filter", attempt=1,
            response_code=None, response_body=None, duration_ms=0,
            error_message=None, metadata={},
        )
        return "rejected_filter"

    payload = _format_payload(dest, event)
    body_bytes = json.dumps(payload).encode("utf-8")

    headers: dict[str, str] = {"Content-Type": "application/json"}
    headers.update(dest.get("headers") or {})
    if dest.get("secret"):
        headers["X-TennetCTL-Signature"] = _sign(dest["secret"], body_bytes)
    headers["X-TennetCTL-Delivery"] = delivery_id

    timeout_s = float((dest.get("retry_policy") or {}).get("timeout_ms", 2000)) / 1000.0
    if timeout_s <= 0 or timeout_s > 30:
        timeout_s = DEFAULT_TIMEOUT_S

    status: str
    response_code: int | None = None
    response_body: str | None = None
    error_message: str | None = None
    try:
        resp = await http_client.post(
            dest["url"], content=body_bytes, headers=headers, timeout=timeout_s,
        )
        response_code = resp.status_code
        response_body = (resp.text or "")[:RESPONSE_BODY_MAX_BYTES]
        status = "success" if 200 <= resp.status_code < 300 else "failure"
    except httpx.TimeoutException as e:
        status = "timeout"; error_message = str(e)
    except Exception as e:
        status = "failure"; error_message = str(e)

    duration_ms = int((time.perf_counter() - started) * 1000)
    await _repo.insert_delivery(
        conn,
        delivery_id=delivery_id, destination_id=dest["id"],
        event_id=event.get("id"),
        org_id=dest["org_id"], workspace_id=dest["workspace_id"],
        status=status, attempt=1,
        response_code=response_code, response_body=response_body,
        duration_ms=duration_ms, error_message=error_message,
        metadata={},
    )
    return status


async def fan_out_event(
    pool: Any, *,
    workspace_id: str, event: dict, http_client: httpx.AsyncClient | None = None,
) -> dict:
    """Send one event to ALL active destinations for the workspace. Used by:
      - product_ops.events.ingest (called per-event after the batch lands)
      - manual replay endpoints

    Returns: {sent, success, failure, timeout, rejected_filter}.
    """
    counters = {"sent": 0, "success": 0, "failure": 0, "timeout": 0, "rejected_filter": 0}
    client: httpx.AsyncClient = http_client if http_client is not None else httpx.AsyncClient()
    own_client = http_client is None
    try:
        async with pool.acquire() as conn:
            destinations = await _repo.list_active_destinations_for_workspace(conn, workspace_id)
            if not destinations:
                return counters
            counters["sent"] = len(destinations)
            # Run all destinations concurrently to keep ingest latency bounded
            results = await asyncio.gather(
                *[deliver_one(conn, dest=d, event=event, http_client=client)
                  for d in destinations],
                return_exceptions=True,
            )
            for r in results:
                if isinstance(r, BaseException):
                    counters["failure"] += 1
                else:
                    key = str(r)
                    counters[key] = counters.get(key, 0) + 1
    finally:
        if own_client:
            await client.aclose()
    return counters


async def test_destination(
    pool: Any, conn: Any, *, dest_id: str, sample_event: dict | None = None,
) -> dict:
    """Send a synthetic event to a destination — operator-triggered via UI."""
    del pool  # kept for signature uniformity; uses caller's conn directly
    dest = await _repo.get_destination_with_secret(conn, dest_id)
    if not dest:
        raise _errors.AppError("PRODUCT_OPS.DESTINATION_NOT_FOUND", "not found", status_code=404)
    event = sample_event or {
        "id": _core_id.uuid7(),
        "event_kind": "custom", "event_name": "tennetctl.test_event",
        "occurred_at": "2026-04-19T00:00:00Z",
        "visitor_id": "v_test_synthetic",
        "workspace_id": dest["workspace_id"],
        "metadata": {"test": True, "source": "operator_ui_test_button"},
    }
    async with httpx.AsyncClient() as client:
        status = await deliver_one(conn, dest=dest, event=event, http_client=client)
    return {"destination_id": dest_id, "status": status}
