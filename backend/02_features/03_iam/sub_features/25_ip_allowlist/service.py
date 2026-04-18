"""iam.ip_allowlist — service layer.

IP allowlist enforcement: if an org has any CIDR entries,
all authenticated requests must come from a matching IP.
"""

from __future__ import annotations

import ipaddress
import re
from importlib import import_module
from typing import Any

_core_id: Any = import_module("backend.01_core.id")
_errors: Any = import_module("backend.01_core.errors")
_catalog: Any = import_module("backend.01_catalog")
_repo: Any = import_module(
    "backend.02_features.03_iam.sub_features.25_ip_allowlist.repository"
)

_AUDIT = "audit.events.emit"
_CIDR_RE = re.compile(r"^[\d.:a-fA-F/]+$")


def _validate_cidr(cidr: str) -> str:
    """Validate and normalize a CIDR block. Raises AppError on invalid."""
    if not _CIDR_RE.match(cidr):
        raise _errors.AppError("INVALID_CIDR", f"Invalid CIDR: {cidr!r}", 422)
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return str(network)
    except ValueError as exc:
        raise _errors.AppError("INVALID_CIDR", f"Invalid CIDR: {cidr!r} — {exc}", 422) from exc


def ip_in_allowlist(client_ip: str, cidrs: list[str]) -> bool:
    """Return True if client_ip falls within any of the CIDRs."""
    if not cidrs:
        return True  # no allowlist = allow all
    try:
        addr = ipaddress.ip_address(client_ip)
    except ValueError:
        return False
    for cidr in cidrs:
        try:
            if addr in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


async def _emit(pool: Any, ctx: Any, *, event_key: str, metadata: dict) -> None:
    try:
        await _catalog.run_node(pool, _AUDIT, ctx, {"event_key": event_key, "outcome": "success", "metadata": metadata})
    except Exception:
        pass


async def list_entries(conn: Any, org_id: str) -> list[dict]:
    return await _repo.list_entries(conn, org_id)


async def add_entry(
    pool: Any, conn: Any, ctx: Any, *, org_id: str, cidr: str, label: str,
) -> dict:
    normalized = _validate_cidr(cidr)
    entry = await _repo.insert_entry(
        conn, id=_core_id.uuid7(), org_id=org_id, cidr=normalized,
        label=label, created_by=ctx.user_id or "sys",
    )
    await _emit(pool, ctx, event_key="iam.ip_allowlist.entry_added", metadata={
        "org_id": org_id, "cidr": normalized,
    })
    return entry


async def remove_entry(
    pool: Any, conn: Any, ctx: Any, *, entry_id: str, org_id: str,
) -> None:
    deleted = await _repo.delete_entry(conn, entry_id=entry_id, org_id=org_id)
    if not deleted:
        raise _errors.NotFoundError(f"IP allowlist entry {entry_id!r} not found")
    await _emit(pool, ctx, event_key="iam.ip_allowlist.entry_removed", metadata={
        "org_id": org_id, "entry_id": entry_id,
    })


async def check_ip_gate(conn: Any, *, org_id: str, client_ip: str) -> bool:
    """Return True if request is allowed (no allowlist, or IP matches). False = block."""
    cidrs = await _repo.get_cidrs_for_org(conn, org_id)
    return ip_in_allowlist(client_ip, cidrs)
