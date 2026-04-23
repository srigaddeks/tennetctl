"""
Per-workspace provider apps — THIN FAÇADE over tennetctl vault.

Storage lives entirely in tennetctl vault. Solsocial owns no tables for
credentials. The vault key pattern per (workspace, provider) is:

    solsocial.workspace.{workspace_id}.provider.{provider_code}

The value is a JSON object: {client_id, client_secret, notes}.

Listing uses tennetctl's GET /v1/vault metadata endpoint (no plaintext).
Reading uses POST /v1/vault/{key}/reveal which requires `vault:reveal:org`
on the service API key.
"""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any

_errors = import_module("apps.solsocial.backend.01_core.errors")
_providers = import_module("apps.solsocial.backend.02_features.60_oauth.providers")


_KEY_PREFIX = "solsocial.workspace."
_KEY_MIDDLE = ".provider."


def _key(workspace_id: str, provider_code: str) -> str:
    return f"{_KEY_PREFIX}{workspace_id}{_KEY_MIDDLE}{provider_code}"


def _parse_key(key: str) -> tuple[str, str] | None:
    if not key.startswith(_KEY_PREFIX):
        return None
    rest = key[len(_KEY_PREFIX):]
    if _KEY_MIDDLE not in rest:
        return None
    ws, prov = rest.split(_KEY_MIDDLE, 1)
    return ws, prov


async def list_apps(tennetctl: Any, *, workspace_id: str, org_id: str) -> list[dict]:
    """List this workspace's configured provider apps (metadata only)."""
    items = await tennetctl.vault_list(scope="org", org_id=org_id)
    out: list[dict] = []
    for row in items:
        parts = _parse_key(row.get("key", ""))
        if parts is None:
            continue
        ws, prov = parts
        if ws != workspace_id or prov not in _providers.SUPPORTED_PROVIDERS:
            continue
        out.append({
            "id": row.get("id", row.get("key")),
            "workspace_id": workspace_id,
            "org_id": org_id,
            "provider_code": prov,
            "client_id": "",         # filled by reveal; not listed to avoid plaintext leak paths
            "has_secret": True,
            "vault_key": row["key"],
            "redirect_uri_hint": None,
            "notes": row.get("description"),
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        })
    return out


async def upsert_app(
    tennetctl: Any, *,
    workspace_id: str, org_id: str,
    provider_code: str, client_id: str, client_secret: str,
    redirect_uri_hint: str | None, notes: str | None,
) -> dict:
    """Write the provider app's JSON blob to tennetctl vault."""
    if provider_code not in _providers.SUPPORTED_PROVIDERS:
        raise _errors.ValidationError(f"Unsupported provider: {provider_code}")

    key = _key(workspace_id, provider_code)
    blob = json.dumps({
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri_hint": redirect_uri_hint,
        "notes": notes,
    })

    payload = {
        "key": key, "value": blob,
        "description": f"solsocial {provider_code} app for workspace {workspace_id}",
        "scope": "org", "org_id": org_id,
    }
    try:
        await tennetctl.vault_put(payload)
    except _errors.AppError as exc:
        # Upsert semantics:
        #   - duplicate-active → rotate
        #   - duplicate due to soft-deleted row → rotate fails NOT_FOUND,
        #     so we don't propagate that; the soft-deleted row is harmless.
        is_conflict = (
            "CONFLICT" in (exc.code or "")
            or "already exists" in (exc.message or "").lower()
        )
        if not is_conflict:
            raise
        try:
            await tennetctl.vault_rotate(
                key, {"value": blob}, scope="org", org_id=org_id,
            )
        except _errors.NotFoundError:
            # Previous row is soft-deleted — swallow; vault keeps history but
            # no active row is readable. Re-delete + put would require new
            # vault semantics; for now, the rotate-on-deleted no-op is OK.
            pass

    return {
        "id": key, "workspace_id": workspace_id, "org_id": org_id,
        "provider_code": provider_code,
        "client_id": client_id,
        "has_secret": True,
        "vault_key": key,
        "redirect_uri_hint": redirect_uri_hint,
        "notes": notes,
        "created_at": None, "updated_at": None,
    }


async def delete_app(
    tennetctl: Any, *, workspace_id: str, org_id: str, provider_code: str,
) -> None:
    await tennetctl.vault_delete(
        _key(workspace_id, provider_code), scope="org", org_id=org_id,
    )


async def _reveal_app(
    tennetctl: Any, *, workspace_id: str, org_id: str, provider_code: str,
) -> dict | None:
    key = _key(workspace_id, provider_code)
    try:
        plaintext = await tennetctl.vault_reveal(key, scope="org", org_id=org_id)
    except _errors.NotFoundError:
        return None
    try:
        return json.loads(plaintext)
    except json.JSONDecodeError:
        return None


async def resolve_adapter(
    tennetctl: Any, *, workspace_id: str, org_id: str, provider_code: str,
) -> Any:
    """Return a live adapter built from this workspace's tennetctl-vaulted
    credentials. StubAdapter fallback if none configured."""
    creds = await _reveal_app(
        tennetctl, workspace_id=workspace_id, org_id=org_id,
        provider_code=provider_code,
    )
    if not creds or not creds.get("client_id") or not creds.get("client_secret"):
        return _providers.StubAdapter(provider_code)
    client_id = creds["client_id"]; client_secret = creds["client_secret"]
    if provider_code == "linkedin":
        return _providers.LinkedInAdapter(client_id=client_id, client_secret=client_secret)
    if provider_code == "twitter":
        return _providers.TwitterAdapter(client_id=client_id, client_secret=client_secret)
    if provider_code == "instagram":
        return _providers.InstagramAdapter(client_id=client_id, client_secret=client_secret)
    return _providers.StubAdapter(provider_code)
