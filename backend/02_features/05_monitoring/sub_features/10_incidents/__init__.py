"""Monitoring sub-feature: Incident aggregation and state machine.

Incidents group firing alert events by configurable keys (fingerprint, label_set, custom)
into durable, long-lived entities with their own lifecycle (open → acknowledged → resolved → closed).
Escalation and actions fire at incident granularity, not per alert.
"""
