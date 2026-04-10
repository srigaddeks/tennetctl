"""Type definitions for the kbio V2 scoring engine.

TypedDicts for the complete 22-score system including profiles,
clusters, sessions, and the full scoring response.
"""
from __future__ import annotations

from typing import Any, TypedDict


class IntraStats(TypedDict):
    mean: float
    stdev: float
    p95: float
    p99: float
    sample_count: int


class ContextPrototype(TypedDict):
    platform: str
    input_method: str
    time_bucket: str
    screen_class: str
    locale: str


class ContextCluster(TypedDict):
    cluster_id: str
    general_centroid: list[float]
    keystroke_centroid: list[float]
    pointer_centroid: list[float]
    touch_centroid: list[float]
    sensor_centroid: list[float]
    intra_distance: IntraStats
    per_modality_intra: dict[str, IntraStats]
    context_prototype: ContextPrototype
    weight: float
    session_count: int
    last_used_at: int


class CredentialProfile(TypedDict):
    field_type: str
    zone_sequence_template: list[dict[str, Any]]
    flight_mean: list[float]
    flight_stdev: list[float]
    dwell_mean: list[float]
    dwell_stdev: list[float]
    hesitation_pattern: list[int]
    timing_stats: dict[str, float]
    sample_count: int


class UserProfile(TypedDict):
    id: str
    user_hash: str
    baseline_quality: str
    profile_maturity: float
    total_sessions: int
    total_genuine_sessions: int
    encoder_version: str
    user_trust_ema: float
    clusters: list[ContextCluster]
    credential_profiles: list[CredentialProfile]
    device_uuids: list[str]


class ModalityDrift(TypedDict):
    drift: float
    confidence: float
    z_score: float
    top_factors: list[str]


class IdentityScores(TypedDict):
    behavioral_drift: float
    credential_drift: float | None
    identity_confidence: float
    familiarity_score: float
    cognitive_load: float
    modality_drifts: dict[str, ModalityDrift]
    fusion_weights: dict[str, float]
    matched_cluster: dict[str, Any] | None


class AnomalyScores(TypedDict):
    session_anomaly: float
    velocity_anomaly: float
    takeover_probability: float
    pattern_break: float
    consistency_score: float


class HumannessScores(TypedDict):
    bot_score: float
    replay_score: float
    automation_score: float
    population_anomaly: float
    is_human: bool


class ThreatScores(TypedDict):
    coercion_score: float
    impersonation_score: float


class TrustScores(TypedDict):
    session_trust: float
    user_trust: float
    device_trust: float


class MetaScores(TypedDict):
    confidence: float
    signal_richness: float
    profile_maturity: float
    profile_status: str


class VerdictResult(TypedDict):
    action: str
    risk_level: str
    primary_reason: str


class ExplainabilityFactor(TypedDict):
    rank: int
    source: str
    modality: str
    feature: str
    contribution: float
    direction: str
    baseline_value: float
    observed_value: float
    deviation_sigma: float
    human_readable: str


class SessionState(TypedDict, total=False):
    id: str
    sdk_session_id: str
    user_hash: str
    device_uuid: str
    status: str
    pulse_count: int
    cluster_id: str | None
    cluster_confidence: float
    grace_period_remaining: int
    drift_history: list[float]
    modality_drifts: dict[str, float]
    bot_score: float
    anomaly_score: float
    trust_score: float
    credential_drift: float | None
    slope: float
    acceleration: float
    cusum_value: float
    cusum_threshold: float
    sequence_hashes: list[str]
    started_at: int
    last_active_at: int


class ScoringResponse(TypedDict):
    session_id: str
    batch_seq: int
    ts: int
    processing_ms: float
    identity: IdentityScores
    anomaly: AnomalyScores
    humanness: HumannessScores
    threat: ThreatScores
    trust: TrustScores
    meta: MetaScores
    session: dict[str, Any]
    verdict: VerdictResult
    factors: list[ExplainabilityFactor]
    alerts: list[dict[str, Any]]
