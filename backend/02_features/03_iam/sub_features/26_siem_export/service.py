"""iam.siem_export — service layer."""

from __future__ import annotations

import asyncio
import logging
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module("backend.02_features.03_iam.sub_features.26_siem_export.repository")
_outbox_repo: Any = import_module("backend.02_features.04_audit.sub_features.03_outbox.repository")

_log = logging.getLogger(__name__)
_VALID_KINDS = frozenset({"webhook", "splunk_hec", "datadog", "s3"})
_MAX_FAILURES = 5
_WORKER_SLEEP = 60  # seconds between sweeps


async def _emit(pool: Any, ctx: Any, event_key: str, metadata: dict) -> None:
    try:
        await _catalog.run_node(pool, "audit.events.emit", ctx, {
            "event_key": event_key, "outcome": "success", "metadata": metadata,
        })
    except Exception:
        pass


async def list_destinations(conn: Any, org_id: str) -> list[dict]:
    return await _repo.list_destinations(conn, org_id)


async def create_destination(
    pool: Any, conn: Any, ctx: Any, *, org_id: str, kind: str, label: str,
    config_jsonb: dict, credentials_vault_key: str | None,
) -> dict:
    if kind not in _VALID_KINDS:
        raise _errors.AppError("INVALID_SIEM_KIND", f"Kind must be one of {sorted(_VALID_KINDS)}", 422)
    dest = await _repo.insert_destination(
        conn, id=_core_id.uuid7(), org_id=org_id, kind=kind, label=label,
        config_jsonb=config_jsonb, credentials_vault_key=credentials_vault_key,
        created_by=ctx.user_id or "sys",
    )
    await _emit(pool, ctx, "iam.siem.destination_created", {"org_id": org_id, "kind": kind})
    return dest


async def update_destination(
    pool: Any, conn: Any, ctx: Any, *, dest_id: str, org_id: str,
    label: str | None = None, config_jsonb: dict | None = None, is_active: bool | None = None,
) -> dict:
    dest = await _repo.update_destination(
        conn, dest_id=dest_id, org_id=org_id, label=label,
        config_jsonb=config_jsonb, is_active=is_active, updated_by=ctx.user_id or "sys",
    )
    if dest is None:
        raise _errors.NotFoundError(f"SIEM destination {dest_id!r} not found")
    changed = sorted(
        k for k, v in (
            ("label", label), ("config_jsonb", config_jsonb), ("is_active", is_active),
        ) if v is not None
    )
    await _emit(pool, ctx, "iam.siem.destination_updated", {
        "org_id": org_id, "dest_id": dest_id, "changed": changed,
    })
    return dest


async def delete_destination(pool: Any, conn: Any, ctx: Any, *, dest_id: str, org_id: str) -> None:
    deleted = await _repo.soft_delete_destination(conn, dest_id=dest_id, org_id=org_id)
    if not deleted:
        raise _errors.NotFoundError(f"SIEM destination {dest_id!r} not found")
    await _emit(pool, ctx, "iam.siem.destination_deleted", {"org_id": org_id, "dest_id": dest_id})


async def _dispatch_webhook(dest: dict, events: list[dict]) -> bool:
    import urllib.request
    import urllib.error
    import json as _json

    url = dest["config_jsonb"].get("url", "")
    if not url:
        return False
    payload = _json.dumps({"events": events}).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception:
        return False


async def _dispatch(dest: dict, events: list[dict]) -> bool:
    kind = dest["kind"]
    if kind == "webhook":
        return await asyncio.get_event_loop().run_in_executor(None, lambda: _dispatch_webhook_sync(dest, events))
    # splunk_hec, datadog, s3 — implement as needed; stub True for now
    return True


def _dispatch_webhook_sync(dest: dict, events: list[dict]) -> bool:
    import urllib.request
    import json as _json

    url = dest["config_jsonb"].get("url", "")
    if not url:
        return False
    payload = _json.dumps({"events": events}).encode()
    req = urllib.request.Request(url, data=payload, method="POST",
                                  headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status < 400
    except Exception:
        return False


async def run_worker_once(pool: Any) -> None:
    """Export new audit events to all active SIEM destinations."""
    async with pool.acquire() as conn:
        destinations = await _repo.list_active_destinations(conn)

    for dest in destinations:
        if dest["failure_count"] >= _MAX_FAILURES:
            continue  # skip DLQ'd destination
        try:
            async with pool.acquire() as conn:
                events = await _outbox_repo.poll_outbox(
                    conn, since_id=dest["last_cursor"], limit=100,
                    org_id=dest["org_id"],
                )
            if not events:
                continue

            success = await _dispatch(dest, events)
            new_cursor = events[-1]["outbox_id"] if success else dest["last_cursor"]

            async with pool.acquire() as conn:
                await _repo.advance_cursor(conn, dest_id=dest["id"], cursor=new_cursor, success=success)
        except Exception as exc:
            _log.warning("siem_worker: dest %s error: %s", dest["id"], exc)
            async with pool.acquire() as conn:
                await _repo.advance_cursor(conn, dest_id=dest["id"], cursor=dest["last_cursor"], success=False)


async def start_worker(pool: Any) -> None:
    while True:
        try:
            await run_worker_once(pool)
        except Exception as exc:
            _log.warning("siem_worker error: %s", exc)
        await asyncio.sleep(_WORKER_SLEEP)
