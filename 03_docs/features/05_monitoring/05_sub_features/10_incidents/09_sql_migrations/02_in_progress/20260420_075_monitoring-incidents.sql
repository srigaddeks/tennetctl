-- UP ====
-- Incidents sub-feature: incident aggregation, grouping, state machine, timeline audit trail

-- Dimension: incident states (open, acknowledged, resolved, closed)
CREATE TABLE "05_monitoring"."01_dim_incident_state" (
    id SMALLINT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE "05_monitoring"."01_dim_incident_state" IS 'Incident lifecycle states: open, acknowledged, resolved, closed';
COMMENT ON COLUMN "05_monitoring"."01_dim_incident_state".id IS 'State ID: 1=open, 2=acknowledged, 3=resolved, 4=closed';

-- Dimension: incident timeline event kinds
CREATE TABLE "05_monitoring"."02_dim_incident_event_kind" (
    id SMALLINT PRIMARY KEY,
    code TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE "05_monitoring"."02_dim_incident_event_kind" IS 'Incident timeline event kinds: created, alert_joined, acknowledged, escalated, action_dispatched, comment_added, resolved, closed, reopened';

-- Fact: incidents
CREATE TABLE "05_monitoring"."10_fct_monitoring_incidents" (
    id VARCHAR(36) PRIMARY KEY,
    org_id VARCHAR(36) NOT NULL,
    group_key TEXT NOT NULL,
    title TEXT NOT NULL,
    severity_id SMALLINT NOT NULL,
    state_id SMALLINT NOT NULL REFERENCES "05_monitoring"."01_dim_incident_state"(id),
    opened_at TIMESTAMP NOT NULL,
    acknowledged_at TIMESTAMP NULL,
    resolved_at TIMESTAMP NULL,
    closed_at TIMESTAMP NULL,
    ack_user_id VARCHAR(36) NULL,
    resolved_by_user_id VARCHAR(36) NULL,
    summary TEXT NULL,
    root_cause TEXT NULL,
    postmortem_ref TEXT NULL,
    escalation_state_id VARCHAR(36) NULL,
    action_count INT NOT NULL DEFAULT 0,
    deleted_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX "idx_fct_incidents_org_id" ON "05_monitoring"."10_fct_monitoring_incidents"(org_id) WHERE deleted_at IS NULL;
CREATE INDEX "idx_fct_incidents_group_key" ON "05_monitoring"."10_fct_monitoring_incidents"(org_id, group_key) WHERE deleted_at IS NULL;
CREATE INDEX "idx_fct_incidents_state" ON "05_monitoring"."10_fct_monitoring_incidents"(state_id) WHERE deleted_at IS NULL;
CREATE INDEX "idx_fct_incidents_severity" ON "05_monitoring"."10_fct_monitoring_incidents"(severity_id) WHERE deleted_at IS NULL;
CREATE INDEX "idx_fct_incidents_opened_at" ON "05_monitoring"."10_fct_monitoring_incidents"(opened_at DESC) WHERE deleted_at IS NULL;

-- Unique partial index: one open/acknowledged incident per (org_id, group_key)
CREATE UNIQUE INDEX "uq_fct_incidents_open_per_group"
    ON "05_monitoring"."10_fct_monitoring_incidents"(org_id, group_key)
    WHERE state_id IN (1, 2) AND deleted_at IS NULL;

COMMENT ON TABLE "05_monitoring"."10_fct_monitoring_incidents" IS 'Incidents: aggregated alert groupings with state machine (open → acknowledged → resolved → closed)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".id IS 'Incident ID (UUID v7)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".org_id IS 'Organization ID (FK)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".group_key IS 'Deterministic group key derived from rule + grouping strategy (fingerprint/label_set/custom_key)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".title IS 'Human-readable incident title (rule name + label snippet)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".severity_id IS 'FK to dim_monitoring_alert_severity';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".state_id IS 'FK to dim_incident_state';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".opened_at IS 'When the incident was first created (from first alert)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".acknowledged_at IS 'When incident was manually acknowledged (propagates to escalation_state)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".resolved_at IS 'When incident was resolved (all linked alerts resolved OR manual resolve)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".closed_at IS 'When incident was manually closed (after retention period)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".ack_user_id IS 'User who acknowledged the incident (NULL if system-set)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".resolved_by_user_id IS 'User who resolved, if manual (NULL if system-triggered)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".summary IS 'Post-incident summary (populated on close)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".root_cause IS 'Root cause analysis (populated on close)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".postmortem_ref IS 'Link to postmortem (URL or doc reference)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".escalation_state_id IS 'FK to dtl_monitoring_alert_escalation_state (for back-compat link)';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_incidents".action_count IS 'Total number of actions dispatched for this incident';

-- Link: incident to alert events (immutable many-to-many)
CREATE TABLE "05_monitoring"."40_lnk_monitoring_incident_alerts" (
    incident_id VARCHAR(36) NOT NULL REFERENCES "05_monitoring"."10_fct_monitoring_incidents"(id) ON DELETE CASCADE,
    -- No FK: 60_evt_monitoring_alert_events is partitioned; its unique
    -- constraint is (id, started_at) so a single-column FK cannot target it.
    alert_event_id VARCHAR(36) NOT NULL,
    joined_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (incident_id, alert_event_id)
);

CREATE INDEX "idx_lnk_incident_alerts_alert_event" ON "05_monitoring"."40_lnk_monitoring_incident_alerts"(alert_event_id);

COMMENT ON TABLE "05_monitoring"."40_lnk_monitoring_incident_alerts" IS 'Immutable link between incidents and alert events (one incident may contain many alert events)';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_incident_alerts".incident_id IS 'FK to incident';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_incident_alerts".alert_event_id IS 'FK to alert event';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_incident_alerts".joined_at IS 'When the alert was joined to this incident';

-- Event: incident timeline (append-only, partitioned daily, 365-day retention)
CREATE TABLE "05_monitoring"."60_evt_monitoring_incident_timeline" (
    id VARCHAR(36) NOT NULL,
    incident_id VARCHAR(36) NOT NULL REFERENCES "05_monitoring"."10_fct_monitoring_incidents"(id) ON DELETE CASCADE,
    kind_id SMALLINT NOT NULL REFERENCES "05_monitoring"."02_dim_incident_event_kind"(id),
    actor_user_id VARCHAR(36) NULL,
    payload JSONB NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id, occurred_at)
) PARTITION BY RANGE (occurred_at);

-- Create initial partition for current date
CREATE TABLE "05_monitoring"."60_evt_monitoring_incident_timeline_20260420" PARTITION OF "05_monitoring"."60_evt_monitoring_incident_timeline"
    FOR VALUES FROM ('2026-04-20') TO ('2026-04-21');

CREATE INDEX "idx_evt_incident_timeline_incident" ON "05_monitoring"."60_evt_monitoring_incident_timeline"(incident_id) INCLUDE (kind_id, occurred_at);
CREATE INDEX "idx_evt_incident_timeline_occurred" ON "05_monitoring"."60_evt_monitoring_incident_timeline"(occurred_at DESC);

COMMENT ON TABLE "05_monitoring"."60_evt_monitoring_incident_timeline" IS 'Append-only incident timeline: state transitions, alert joins, comments, actions dispatched. Partitioned daily, 365-day retention.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_incident_timeline".id IS 'Event ID (UUID v7)';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_incident_timeline".incident_id IS 'FK to incident';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_incident_timeline".kind_id IS 'FK to dim_incident_event_kind';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_incident_timeline".actor_user_id IS 'User who triggered (NULL for system events)';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_incident_timeline".payload IS 'Event-specific data (varies by kind)';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_incident_timeline".occurred_at IS 'When the event occurred';

-- View: incidents with resolved state, severity, linked alert count, escalation user
CREATE OR REPLACE VIEW "05_monitoring".v_monitoring_incidents AS
SELECT
    i.id,
    i.org_id,
    i.group_key,
    i.title,
    i.severity_id,
    s.code AS severity_code,
    s.label AS severity_label,
    i.state_id,
    st.code AS state_code,
    st.label AS state_label,
    i.opened_at,
    i.acknowledged_at,
    i.resolved_at,
    i.closed_at,
    i.ack_user_id,
    i.resolved_by_user_id,
    i.summary,
    i.root_cause,
    i.postmortem_ref,
    i.escalation_state_id,
    i.action_count,
    COALESCE(alert_count.cnt, 0) AS linked_alert_count,
    i.created_at,
    i.updated_at,
    i.deleted_at
FROM "05_monitoring"."10_fct_monitoring_incidents" i
LEFT JOIN "05_monitoring"."01_dim_monitoring_alert_severity" s ON i.severity_id = s.id
LEFT JOIN "05_monitoring"."01_dim_incident_state" st ON i.state_id = st.id
LEFT JOIN (
    SELECT incident_id, COUNT(*) AS cnt
    FROM "05_monitoring"."40_lnk_monitoring_incident_alerts"
    GROUP BY incident_id
) alert_count ON i.id = alert_count.incident_id
WHERE i.deleted_at IS NULL;

COMMENT ON VIEW "05_monitoring".v_monitoring_incidents IS 'Read view: incidents with state labels, severity labels, linked alert counts';

-- DOWN ====
DROP VIEW IF EXISTS "05_monitoring".v_monitoring_incidents;
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_incident_timeline" CASCADE;
DROP TABLE IF EXISTS "05_monitoring"."40_lnk_monitoring_incident_alerts";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_incidents";
DROP TABLE IF EXISTS "05_monitoring"."02_dim_incident_event_kind";
DROP TABLE IF EXISTS "05_monitoring"."01_dim_incident_state";
