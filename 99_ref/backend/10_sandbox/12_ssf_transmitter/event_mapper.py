from __future__ import annotations

CAEP_BASE = "https://schemas.openid.net/secevent/caep/event-type/"
RISC_BASE = "https://schemas.openid.net/secevent/risc/event-type/"
KCONTROL_BASE = "https://schemas.kcontrol.io/secevent/sandbox/event-type/"

CAEP_EVENT_TYPES: set[str] = {
    "session-revoked",
    "token-claims-change",
    "credential-change",
    "assurance-level-change",
    "device-compliance-change",
    "session-established",
    "session-presented",
}

RISC_EVENT_TYPES: set[str] = {
    "credential-compromise",
    "account-disabled",
    "account-enabled",
    "account-credential-change-required",
    "account-purged",
    "identifier-changed",
    "identifier-recycled",
    "recovery-activated",
    "recovery-information-changed",
    "sessions-revoked",
}


def resolve_event_uri(
    *,
    caep_event_type: str | None = None,
    risc_event_type: str | None = None,
    signal_code: str,
) -> str:
    """Resolve a signal code to the appropriate event URI (CAEP, RISC, or custom)."""
    if caep_event_type and caep_event_type in CAEP_EVENT_TYPES:
        return CAEP_BASE + caep_event_type
    if risc_event_type and risc_event_type in RISC_EVENT_TYPES:
        return RISC_BASE + risc_event_type
    return KCONTROL_BASE + signal_code


def get_all_caep_event_types() -> list[dict]:
    """Return all supported CAEP event types with their URIs."""
    return [
        {"event_type": et, "uri": CAEP_BASE + et, "family": "caep"}
        for et in sorted(CAEP_EVENT_TYPES)
    ]


def get_all_risc_event_types() -> list[dict]:
    """Return all supported RISC event types with their URIs."""
    return [
        {"event_type": et, "uri": RISC_BASE + et, "family": "risc"}
        for et in sorted(RISC_EVENT_TYPES)
    ]
