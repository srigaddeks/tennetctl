"""Threat type registry — decorator-based auto-registration.

Threat types compose signals via JSON conditions evaluated by the
existing kprotect rule engine.  They register at import time.
"""
from __future__ import annotations

from typing import Any, Callable

from ._types import ThreatTypeDef

_REGISTRY: dict[str, ThreatTypeDef] = {}


def threat_type(
    code: str,
    *,
    name: str,
    description: str,
    category: str,
    severity: int,
    default_action: str,
    conditions: dict[str, Any],
    default_config: dict[str, Any] | None = None,
    reason_template: str = "",
    tags: list[str] | None = None,
) -> Callable:
    """Decorator that registers a threat type definition.

    The decorated function is a no-op marker — threat types are
    declarative, evaluated by the rule engine, not by calling the
    function.

    Usage::

        @threat_type(
            code="ato-new-device-high-drift",
            name="Account Takeover: New Device + High Drift",
            category="account_takeover",
            severity=90,
            default_action="block",
            conditions={
                "operator": "AND",
                "rules": [
                    {"field": "signals.critical_behavioral_drift",
                     "op": "==", "value": True},
                    {"field": "signals.new_device",
                     "op": "==", "value": True},
                ],
            },
            reason_template="ATO: critical drift on new device",
            tags=["ato", "fraud", "critical"],
        )
        def ato_new_device_high_drift():
            pass
    """

    def decorator(fn: Callable) -> Callable:
        _REGISTRY[code] = ThreatTypeDef(
            code=code,
            name=name,
            description=description,
            category=category,
            severity=severity,
            default_action=default_action,
            conditions=conditions,
            default_config=default_config or {},
            reason_template=reason_template,
            tags=tags or [],
        )
        return fn

    return decorator


def get_all_threat_types() -> dict[str, ThreatTypeDef]:
    """Return a shallow copy of the full threat type registry."""
    return dict(_REGISTRY)


def get_threat_type(code: str) -> ThreatTypeDef | None:
    """Look up a single threat type by code."""
    return _REGISTRY.get(code)


def get_threat_types_by_category(category: str) -> dict[str, ThreatTypeDef]:
    """Return all threat types matching a category."""
    return {k: v for k, v in _REGISTRY.items() if v["category"] == category}
