from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LiveSessionRecord:
    id: str
    tenant_key: str
    org_id: str
    workspace_id: str | None
    connector_instance_id: str
    session_status: str
    duration_minutes: int
    started_at: str | None
    expires_at: str | None
    paused_at: str | None
    completed_at: str | None
    data_points_received: int
    bytes_received: int
    signals_executed: int
    threats_evaluated: int
    created_at: str
    created_by: str


@dataclass(frozen=True)
class LiveSessionSignalRecord:
    id: str
    live_session_id: str
    signal_id: str
    signal_code: str | None
    signal_name: str | None


@dataclass(frozen=True)
class LiveSessionThreatRecord:
    id: str
    live_session_id: str
    threat_type_id: str
    threat_code: str | None
    threat_name: str | None
