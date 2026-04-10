"""Signal registry — decorator-based auto-registration.

Signals register themselves at import time via the @signal decorator.
The registry is the single source of truth; DB catalog is a sync target.
"""
from __future__ import annotations

from typing import Any, Callable

from ._types import SignalDef, SignalResult

_REGISTRY: dict[str, SignalDef] = {}


def signal(
    code: str,
    *,
    name: str,
    description: str,
    category: str,
    signal_type: str = "boolean",
    default_config: dict[str, Any] | None = None,
    severity: int = 50,
    tags: list[str] | None = None,
) -> Callable:
    """Decorator that registers a signal function.

    Usage::

        @signal(
            code="vpn_detected",
            name="VPN Detected",
            description="Session originates from a known VPN exit node",
            category="network",
            severity=40,
            tags=["network", "vpn"],
        )
        def compute_vpn_detected(ctx: dict, config: dict) -> SignalResult:
            ...
    """

    def decorator(
        fn: Callable[[dict[str, Any], dict[str, Any]], SignalResult],
    ) -> Callable[[dict[str, Any], dict[str, Any]], SignalResult]:
        _REGISTRY[code] = SignalDef(
            code=code,
            name=name,
            description=description,
            category=category,
            signal_type=signal_type,
            default_config=default_config or {},
            severity=severity,
            tags=tags or [],
            function=fn,
        )
        return fn

    return decorator


def get_all_signals() -> dict[str, SignalDef]:
    """Return a shallow copy of the full signal registry."""
    return dict(_REGISTRY)


def get_signal(code: str) -> SignalDef | None:
    """Look up a single signal definition by code."""
    return _REGISTRY.get(code)


def get_signals_by_category(category: str) -> dict[str, SignalDef]:
    """Return all signals matching a category."""
    return {k: v for k, v in _REGISTRY.items() if v["category"] == category}


def get_required_signals_for_threats(
    threat_codes: list[str],
    threat_registry: dict[str, Any],
) -> set[str]:
    """Extract the set of signal codes referenced by a list of threat types.

    Parses each threat type's ``conditions.rules[].field`` looking for
    ``signals.<code>`` references.
    """
    codes: set[str] = set()
    for tc in threat_codes:
        threat = threat_registry.get(tc)
        if not threat:
            continue
        conditions = threat.get("conditions", {})
        for rule in conditions.get("rules", []):
            field = rule.get("field", "")
            if field.startswith("signals."):
                codes.add(field.split(".", 1)[1])
    return codes
