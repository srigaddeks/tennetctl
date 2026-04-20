"""Grouper: pure logic for computing incident group keys and finding existing incidents."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from importlib import import_module

# Jinja2 sandboxed environment for custom_key strategy
try:
    from jinja2.sandbox import SandboxedEnvironment
    _sandbox_env = SandboxedEnvironment()
except ImportError:
    _sandbox_env = None


def compute_group_key(
    rule_id: str,
    alert_fingerprint: str,
    labels: dict[str, str],
    grouping_rule: dict | None = None,
) -> str:
    """Compute deterministic group key from rule + alert + grouping config.

    Strategies:
    - fingerprint: sha256(rule_id | alert_fingerprint)
    - label_set: sha256(rule_id | sorted(selected_label_keys))
    - custom_key: Jinja2 template rendered with rule_id, fingerprint, labels
    """
    if not grouping_rule or not grouping_rule.get("is_active"):
        # Default: fingerprint strategy
        canonical = f"{rule_id}|{alert_fingerprint}"
        return hashlib.sha256(canonical.encode()).hexdigest()

    strategy = grouping_rule.get("dedup_strategy", "fingerprint")

    if strategy == "fingerprint":
        canonical = f"{rule_id}|{alert_fingerprint}"
        return hashlib.sha256(canonical.encode()).hexdigest()

    elif strategy == "label_set":
        group_by = grouping_rule.get("group_by") or []
        if not group_by:
            # Empty group_by falls back to fingerprint
            canonical = f"{rule_id}|{alert_fingerprint}"
        else:
            # Extract selected labels, sort, and concatenate
            selected = []
            for key in sorted(group_by):
                val = labels.get(key, "")
                selected.append(f"{key}={val}")
            label_part = "|".join(selected)
            canonical = f"{rule_id}|{label_part}"
        return hashlib.sha256(canonical.encode()).hexdigest()

    elif strategy == "custom_key":
        template_str = grouping_rule.get("custom_template", "{rule_id}|{fingerprint}")
        if _sandbox_env:
            try:
                template = _sandbox_env.from_string(template_str)
                rendered = template.render(
                    rule_id=rule_id,
                    fingerprint=alert_fingerprint,
                    labels=labels,
                )
                canonical = rendered
            except Exception as e:
                # If template fails, fall back to fingerprint
                canonical = f"{rule_id}|{alert_fingerprint}"
        else:
            canonical = f"{rule_id}|{alert_fingerprint}"
        return hashlib.sha256(canonical.encode()).hexdigest()

    else:
        # Unknown strategy, default to fingerprint
        canonical = f"{rule_id}|{alert_fingerprint}"
        return hashlib.sha256(canonical.encode()).hexdigest()


async def find_open_incident(
    conn: Any,
    org_id: str,
    group_key: str,
    window_seconds: int = 300,
) -> dict | None:
    """Find open or acknowledged incident for (org_id, group_key) within window."""
    cutoff = f"CURRENT_TIMESTAMP - INTERVAL '{window_seconds} seconds'"
    row = await conn.fetchrow(
        f"""
        SELECT * FROM "05_monitoring".v_monitoring_incidents
        WHERE org_id = $1
          AND group_key = $2
          AND state_id IN (1, 2)
          AND opened_at >= {cutoff}
        ORDER BY opened_at DESC
        LIMIT 1
        """,
        org_id, group_key,
    )
    return dict(row) if row else None


__all__ = ["compute_group_key", "find_open_incident"]
