"""kbio ingest schemas.

Request/response models for the behavioral batch ingest pipeline.
Mirrors the SDK wire protocol types from behaviour_biometrics.md.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class BatchHeader(BaseModel):
    batch_id: str
    session_id: str
    user_hash: str
    device_uuid: str
    sdk_version: str = ""
    sdk_platform: str = "web"
    sent_at: int  # epoch ms
    pulse_number: int = 0


class IngestRequest(BaseModel):
    """Behavioral batch from SDK. Supports all batch types."""
    type: str = Field(description="behavioral|critical_action|keepalive|session_start|session_end|device_fingerprint")
    header: BatchHeader
    context: dict[str, Any] = Field(default_factory=dict)
    signals: dict[str, Any] = Field(default_factory=dict)
    keystroke_windows: list[dict[str, Any]] = Field(default_factory=list)
    pointer_windows: list[dict[str, Any]] = Field(default_factory=list)
    touch_windows: list[dict[str, Any]] = Field(default_factory=list)
    sensor_windows: list[dict[str, Any]] = Field(default_factory=list)
    scroll_windows: list[dict[str, Any]] = Field(default_factory=list)
    credential_fields: list[dict[str, Any]] = Field(default_factory=list)
    required_signals: list[str] | None = None
    required_threats: list[str] | None = None
    signal_configs: dict[str, dict[str, Any]] | None = None


class DriftScoreData(BaseModel):
    """Drift score response returned to kprotect/SDK."""
    batch_id: str
    processed_at: int  # epoch ms
    drift_score: float = -1.0
    confidence: float = 0.0
    signal_scores: dict[str, float] = Field(default_factory=dict)
    fusion_weights: dict[str, float] = Field(default_factory=dict)
    action: str = "allow"
    bot_score: float = 0.0
    anomaly_score: float = -1.0
    trust_score: float = -1.0
    device_drift: float = -1.0
    network_drift: float = -1.0
    credential_drift: float | None = None
    composite_score: float = -1.0
    auth_state: dict[str, Any] = Field(default_factory=dict)
    drift_trend: dict[str, Any] = Field(default_factory=dict)
    alerts: list[dict[str, Any]] = Field(default_factory=list)


class ScoringResponseV2(BaseModel):
    """V2 22-score response from scoring pipeline."""
    identity: dict[str, Any] = Field(default_factory=dict)
    anomaly: dict[str, Any] = Field(default_factory=dict)
    humanness: dict[str, Any] = Field(default_factory=dict)
    threat: dict[str, Any] = Field(default_factory=dict)
    trust: dict[str, Any] = Field(default_factory=dict)
    session: dict[str, Any] = Field(default_factory=dict)
    meta: dict[str, Any] = Field(default_factory=dict)
    verdict: dict[str, Any] = Field(default_factory=dict)
    factors: list[dict[str, Any]] = Field(default_factory=list)
    alerts: list[dict[str, Any]] = Field(default_factory=list)
    signals: dict[str, Any] | None = None
    threats_detected: list[dict[str, Any]] | None = None
    processing_ms: float = 0.0


class ScoreRequest(BaseModel):
    """On-demand composite score request from kprotect."""
    session_id: str
    user_hash: str
    include_device: bool = True
    include_network: bool = True
    include_behavioral: bool = True
