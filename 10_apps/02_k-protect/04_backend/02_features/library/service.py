"""kprotect library service — proxy to kbio policy catalog with Valkey caching."""

from __future__ import annotations

import importlib
import json
from typing import Any

_kbio = importlib.import_module("02_features.evaluate.kbio_client")
_config_mod = importlib.import_module("01_core.config")
_valkey_mod = importlib.import_module("01_core.valkey")
_errors_mod = importlib.import_module("01_core.errors")

AppError = _errors_mod.AppError

_CACHE_KEY_LIST = "kp:library:catalog"
_CACHE_KEY_ITEM = "kp:library:policy:{code}"
_CACHE_TTL_SECONDS = 300  # 5 minutes


def _cache_client():
    return _valkey_mod.get_client()


async def list_policies(
    *,
    limit: int,
    offset: int,
    category: str | None,
    tag: str | None,
) -> dict[str, Any]:
    """Return a paginated + filtered slice of the kbio policy catalog.

    Catalog is cached in Valkey for 5 minutes to avoid hammering kbio.
    """
    cache_key = _CACHE_KEY_LIST
    client = _cache_client()

    # Try cache first
    cached = await client.get(cache_key)
    if cached is not None:
        all_policies: list[dict] = json.loads(cached)
    else:
        all_policies = await _kbio.get_policy_catalog()
        await client.setex(cache_key, _CACHE_TTL_SECONDS, json.dumps(all_policies))

    # Apply in-memory filters
    filtered = all_policies
    if category is not None:
        filtered = [p for p in filtered if p.get("category") == category]
    if tag is not None:
        filtered = [p for p in filtered if tag in (p.get("tags") or [])]

    total = len(filtered)
    page = filtered[offset: offset + limit]

    return {"items": page, "total": total, "limit": limit, "offset": offset}


async def get_policy(code: str) -> dict[str, Any]:
    """Fetch a single predefined policy by code from kbio.

    Tries a per-item cache key first, then falls back to the full catalog.
    """
    item_key = _CACHE_KEY_ITEM.format(code=code)
    client = _cache_client()

    cached = await client.get(item_key)
    if cached is not None:
        return json.loads(cached)

    # Fall back: pull full catalog and search
    catalog_cached = await client.get(_CACHE_KEY_LIST)
    if catalog_cached is not None:
        all_policies: list[dict] = json.loads(catalog_cached)
        for p in all_policies:
            if p.get("code") == code:
                await client.setex(item_key, _CACHE_TTL_SECONDS, json.dumps(p))
                return p

    # Direct kbio call — smaller catalogs are likely <1 s
    all_policies = await _kbio.get_policy_catalog()
    await client.setex(_CACHE_KEY_LIST, _CACHE_TTL_SECONDS, json.dumps(all_policies))

    for p in all_policies:
        if p.get("code") == code:
            await client.setex(item_key, _CACHE_TTL_SECONDS, json.dumps(p))
            return p

    raise AppError("POLICY_NOT_FOUND", f"Predefined policy '{code}' not found in catalog.", 404)
