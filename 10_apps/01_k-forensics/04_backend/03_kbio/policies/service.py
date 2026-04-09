"""kbio policies service.

Provides the predefined policy catalog with Valkey-first caching.

Cache keys:
  kbio:policies:list:{category}:{tag}:{limit}:{offset}  TTL: 600 s
  kbio:policy:{code}                                     TTL: 600 s
"""
from __future__ import annotations

import importlib
import json
from typing import Any

import asyncpg  # noqa: F401 — used by type annotations in repository callee

_errors = importlib.import_module("01_core.errors")
_valkey_mod = importlib.import_module("01_core.valkey")

from .repository import list_policies as _repo_list, get_policy_by_code, count_policies
from .schemas import PredefinedPolicyData, PredefinedPolicyListData

_CACHE_TTL = 600  # seconds — policies change rarely


def _list_cache_key(
    limit: int, offset: int, category: str | None, tag: str | None
) -> str:
    cat = category or ""
    tg = tag or ""
    return f"kbio:policies:list:{cat}:{tg}:{limit}:{offset}"


def _policy_cache_key(code: str) -> str:
    return f"kbio:policy:{code}"


def _row_to_policy(row: dict[str, Any]) -> PredefinedPolicyData:
    """Convert a v_predefined_policies row dict to the response schema."""
    return PredefinedPolicyData(
        id=str(row["id"]),
        code=row["code"],
        name=row["name"],
        description=row.get("description", ""),
        category=row.get("category", ""),
        default_action=row.get("default_action", "allow"),
        severity=int(row.get("severity", 0)),
        conditions=row.get("conditions") or {},
        default_config=row.get("default_config") or {},
        tags=row.get("tags", ""),
        version=row.get("version", "1.0.0"),
        is_active=bool(row.get("is_active", True)),
        created_at=str(row.get("created_at", "")),
    )


async def list_policies(
    conn: asyncpg.Connection,
    limit: int = 50,
    offset: int = 0,
    category: str | None = None,
    tag: str | None = None,
) -> PredefinedPolicyListData:
    """Return a paginated list of predefined policies.

    1. Try Valkey cache for the exact (limit, offset, category, tag) combo.
    2. On miss, query v_predefined_policies and count_policies.
    3. Write result to cache with 600 s TTL.

    Raises:
        AppError(VALIDATION_ERROR, 422) — if limit > 200 or limit < 1.
    """
    if not (1 <= limit <= 200):
        raise _errors.AppError(
            "VALIDATION_ERROR",
            "limit must be between 1 and 200.",
            422,
        )
    if offset < 0:
        raise _errors.AppError(
            "VALIDATION_ERROR",
            "offset must be >= 0.",
            422,
        )

    valkey = _valkey_mod.get_client()
    cache_key = _list_cache_key(limit, offset, category, tag)

    raw = await valkey.get(cache_key)
    if raw:
        try:
            data = json.loads(raw)
            return PredefinedPolicyListData(**data)
        except Exception:
            pass

    rows = await _repo_list(conn, limit=limit, offset=offset, category=category, tag=tag)
    total = await count_policies(conn, category=category, tag=tag)

    items = [_row_to_policy(r) for r in rows]
    result = PredefinedPolicyListData(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )

    try:
        await valkey.setex(cache_key, _CACHE_TTL, result.model_dump_json())
    except Exception:
        pass

    return result


async def get_policy(
    conn: asyncpg.Connection, code: str
) -> PredefinedPolicyData:
    """Return a single predefined policy by its unique code.

    1. Try Valkey cache (kbio:policy:{code}).
    2. On miss, query v_predefined_policies.
    3. Write result to cache with 600 s TTL.

    Raises:
        AppError(NOT_FOUND, 404) — if no active policy with that code exists.
    """
    valkey = _valkey_mod.get_client()
    cache_key = _policy_cache_key(code)

    raw = await valkey.get(cache_key)
    if raw:
        try:
            data = json.loads(raw)
            return PredefinedPolicyData(**data)
        except Exception:
            pass

    row = await get_policy_by_code(conn, code)
    if row is None:
        raise _errors.AppError(
            "NOT_FOUND",
            f"Policy '{code}' not found.",
            404,
        )

    policy = _row_to_policy(row)

    try:
        await valkey.setex(cache_key, _CACHE_TTL, policy.model_dump_json())
    except Exception:
        pass

    return policy
