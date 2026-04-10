"""kbio threat type catalog repository."""
from __future__ import annotations

import importlib


def list_threat_types(
    *,
    limit: int,
    offset: int,
    category: str | None = None,
    tag: str | None = None,
) -> tuple[list[dict], int]:
    _threats = importlib.import_module("03_kbio._threats._registry")
    all_threats = list(_threats.get_all_threat_types().values())
    if category:
        all_threats = [t for t in all_threats if t["category"] == category]
    if tag:
        all_threats = [t for t in all_threats if tag in t["tags"]]
    total = len(all_threats)
    all_threats.sort(key=lambda t: (-t["severity"], t["code"]))
    page = all_threats[offset : offset + limit]
    return page, total


def get_threat_type_by_code(code: str) -> dict | None:
    _threats = importlib.import_module("03_kbio._threats._registry")
    return _threats.get_threat_type(code)
