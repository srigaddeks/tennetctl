"""Service layer for notify.preferences.

Business rules:
  - critical category (id=2) cannot be opted out. Any attempt to set
    is_opted_in=False for category_code='critical' is silently forced to True.
  - All other channel/category combinations can be toggled freely.
  - GET preferences returns all 16 combinations (4 channels × 4 categories)
    with sensible defaults (opted in) for any missing rows.
  - Worker calls is_opted_in() to gate delivery creation for non-critical
    category templates.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

_repo: Any = import_module(
    "backend.02_features.06_notify.sub_features.09_preferences.repository"
)
_core_id: Any = import_module("backend.01_core.id")

# Dimension data embedded to avoid DB round-trips on list-all.
# These must stay in sync with the seed files.
_CHANNELS = [
    {"id": 1, "code": "email",   "label": "Email"},
    {"id": 2, "code": "webpush", "label": "Web Push"},
    {"id": 3, "code": "in_app",  "label": "In-App"},
    {"id": 4, "code": "sms",     "label": "SMS"},
]
_CATEGORIES = [
    {"id": 1, "code": "transactional", "label": "Transactional"},
    {"id": 2, "code": "critical",      "label": "Critical"},
    {"id": 3, "code": "marketing",     "label": "Marketing"},
    {"id": 4, "code": "digest",        "label": "Digest"},
]
_CRITICAL_CATEGORY_ID = 2


def _channel_by_code(code: str) -> dict | None:
    return next((c for c in _CHANNELS if c["code"] == code), None)


def _category_by_code(code: str) -> dict | None:
    return next((c for c in _CATEGORIES if c["code"] == code), None)


async def list_preferences(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
) -> list[dict]:
    """
    Return all 16 (channel × category) preference rows for the user.
    Missing rows default to is_opted_in=True. critical rows are marked
    is_locked=True regardless of stored value.
    """
    stored = await _repo.list_preferences(conn, user_id=user_id, org_id=org_id)
    stored_index = {
        (r["channel_id"], r["category_id"]): r["is_opted_in"]
        for r in stored
    }

    result = []
    for ch in _CHANNELS:
        for cat in _CATEGORIES:
            is_critical = cat["id"] == _CRITICAL_CATEGORY_ID
            stored_val = stored_index.get((ch["id"], cat["id"]))
            is_opted_in = True if stored_val is None else stored_val
            # Critical is always opted in, regardless of stored value
            if is_critical:
                is_opted_in = True
            result.append({
                "channel_id":    ch["id"],
                "channel_code":  ch["code"],
                "channel_label": ch["label"],
                "category_id":    cat["id"],
                "category_code":  cat["code"],
                "category_label": cat["label"],
                "is_opted_in":   is_opted_in,
                "is_locked":     is_critical,
            })
    return result


async def upsert_preference(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    channel_code: str,
    category_code: str,
    is_opted_in: bool,
    updated_by: str,
) -> dict:
    """
    Upsert one preference row. Raises ValidationError for unknown codes.
    Critical category is silently forced to is_opted_in=True.
    """
    _errors: Any = import_module("backend.01_core.errors")

    ch = _channel_by_code(channel_code)
    if ch is None:
        raise _errors.ValidationError(f"unknown channel_code {channel_code!r}")
    cat = _category_by_code(category_code)
    if cat is None:
        raise _errors.ValidationError(f"unknown category_code {category_code!r}")

    if cat["id"] == _CRITICAL_CATEGORY_ID:
        is_opted_in = True  # Cannot opt out of critical

    pref_id = _core_id.uuid7()
    row = await _repo.upsert_preference(
        conn,
        pref_id=pref_id,
        org_id=org_id,
        user_id=user_id,
        channel_id=ch["id"],
        category_id=cat["id"],
        is_opted_in=is_opted_in,
        updated_by=updated_by,
    )
    return {**row, "is_locked": cat["id"] == _CRITICAL_CATEGORY_ID}


async def is_opted_in(
    conn: Any,
    *,
    user_id: str,
    org_id: str,
    channel_id: int,
    category_id: int,
) -> bool:
    """
    Returns True if the user has opted in for this (channel, category) pair.
    Absence of a row = opted in. critical category always returns True.
    Called by the worker before creating non-critical deliveries.
    """
    if category_id == _CRITICAL_CATEGORY_ID:
        return True
    stored = await _repo.get_opt_in(
        conn,
        user_id=user_id,
        org_id=org_id,
        channel_id=channel_id,
        category_id=category_id,
    )
    return True if stored is None else stored
