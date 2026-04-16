from __future__ import annotations

from enum import StrEnum


class SandboxAuditEventType(StrEnum):
    # Connectors
    CONNECTOR_CREATED = "connector_created"
    CONNECTOR_UPDATED = "connector_updated"
    CONNECTOR_DELETED = "connector_deleted"
    CONNECTOR_TESTED = "connector_tested"
    CONNECTOR_COLLECTED = "connector_collected"
    CONNECTOR_CREDENTIALS_UPDATED = "connector_credentials_updated"
    CONNECTOR_HEALTH_CHANGED = "connector_health_changed"
    # Datasets
    DATASET_CREATED = "dataset_created"
    DATASET_UPDATED = "dataset_updated"
    DATASET_DELETED = "dataset_deleted"
    DATASET_LOCKED = "dataset_locked"
    DATASET_CLONED = "dataset_cloned"
    # Signals
    SIGNAL_CREATED = "signal_created"
    SIGNAL_UPDATED = "signal_updated"
    SIGNAL_DELETED = "signal_deleted"
    SIGNAL_GENERATED = "signal_generated"
    SIGNAL_EXECUTED = "signal_executed"
    SIGNAL_VALIDATED = "signal_validated"
    SIGNAL_STATUS_CHANGED = "signal_status_changed"
    # Threat types
    THREAT_TYPE_CREATED = "threat_type_created"
    THREAT_TYPE_UPDATED = "threat_type_updated"
    THREAT_TYPE_DELETED = "threat_type_deleted"
    # Policies
    POLICY_CREATED = "policy_created"
    POLICY_UPDATED = "policy_updated"
    POLICY_DELETED = "policy_deleted"
    POLICY_ENABLED = "policy_enabled"
    POLICY_DISABLED = "policy_disabled"
    # Execution
    SANDBOX_RUN_EXECUTED = "sandbox_run_executed"
    THREAT_EVALUATED = "threat_evaluated"
    POLICY_EXECUTED = "policy_executed"
    # Live sessions
    LIVE_SESSION_STARTED = "live_session_started"
    LIVE_SESSION_PAUSED = "live_session_paused"
    LIVE_SESSION_RESUMED = "live_session_resumed"
    LIVE_SESSION_STOPPED = "live_session_stopped"
    LIVE_SESSION_EXPIRED = "live_session_expired"
    # Libraries
    LIBRARY_CREATED = "library_created"
    LIBRARY_UPDATED = "library_updated"
    LIBRARY_DELETED = "library_deleted"
    LIBRARY_PUBLISHED = "library_published"
    LIBRARY_CLONED = "library_cloned"
    # Promotions
    SIGNAL_PROMOTED = "signal_promoted"
    POLICY_PROMOTED = "policy_promoted"
    LIBRARY_PROMOTED = "library_promoted"
    # Asset Inventory
    ASSET_DISCOVERED = "asset_discovered"
    ASSET_UPDATED = "asset_updated"
    ASSET_DELETED = "asset_deleted"
    ASSET_STATUS_CHANGED = "asset_status_changed"
    ASSET_ACCESS_GRANTED = "asset_access_granted"
    ASSET_ACCESS_REVOKED = "asset_access_revoked"
    COLLECTION_STARTED = "collection_started"
    COLLECTION_COMPLETED = "collection_completed"
    COLLECTION_FAILED = "collection_failed"
    LOG_SOURCE_CREATED = "log_source_created"
    LOG_SOURCE_UPDATED = "log_source_updated"
    PROVIDER_CONNECTION_TESTED = "provider_connection_tested"
    # SSF Transmitter
    SSF_STREAM_CREATED = "ssf_stream_created"
    SSF_STREAM_UPDATED = "ssf_stream_updated"
    SSF_STREAM_DELETED = "ssf_stream_deleted"
    SSF_STREAM_STATUS_CHANGED = "ssf_stream_status_changed"
    SSF_STREAM_VERIFIED = "ssf_stream_verified"
    SSF_SUBJECT_ADDED = "ssf_subject_added"
    SSF_SUBJECT_REMOVED = "ssf_subject_removed"
    SSF_SET_EMITTED = "ssf_set_emitted"
