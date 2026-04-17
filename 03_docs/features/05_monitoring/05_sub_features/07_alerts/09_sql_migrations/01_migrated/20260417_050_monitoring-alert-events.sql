-- UP ====
-- 13-08a Task 2 — Alert events (daily-partitioned append-only stream).
--
-- Written by the alert evaluator worker (13-08b) on firing/resolved
-- transitions. Retention is pre-seeded in 13-07 (code='alert_events',
-- table_name='60_evt_monitoring_alert_events', days_to_keep=90).

CREATE TABLE "05_monitoring"."60_evt_monitoring_alert_events" (
    id                 VARCHAR(36)       NOT NULL,
    rule_id            VARCHAR(36)       NOT NULL,
    fingerprint        TEXT              NOT NULL,
    state              TEXT              NOT NULL,
    value              DOUBLE PRECISION  NULL,
    threshold          DOUBLE PRECISION  NULL,
    org_id             UUID              NOT NULL,
    started_at         TIMESTAMP         NOT NULL,
    resolved_at        TIMESTAMP         NULL,
    last_notified_at   TIMESTAMP         NULL,
    notification_count INT               NOT NULL DEFAULT 0,
    silenced           BOOLEAN           NOT NULL DEFAULT FALSE,
    silence_id         VARCHAR(36)       NULL,
    labels             JSONB             NOT NULL DEFAULT '{}'::jsonb,
    annotations        JSONB             NOT NULL DEFAULT '{}'::jsonb,
    PRIMARY KEY (id, started_at),
    CONSTRAINT chk_monitoring_alert_events_state CHECK (state IN ('firing','resolved'))
) PARTITION BY RANGE (started_at);
COMMENT ON TABLE  "05_monitoring"."60_evt_monitoring_alert_events" IS 'Partitioned append-only alert event stream. One logical event per (rule_id, fingerprint) firing window; resolved transitions update the same row via PK.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".id IS 'UUID v7 — unique per alert instance.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".rule_id IS 'FK to fct_monitoring_alert_rules.id (not enforced — evt table).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".fingerprint IS 'sha256(rule_id || sorted(labels)) — dedupes repeated firings on the same dimension.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".state IS 'firing | resolved. Constrained by chk_monitoring_alert_events_state.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".value IS 'Observed value at last evaluation.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".threshold IS 'Rule threshold snapshot at firing time.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".org_id IS 'Owning org (denormalised for partition pruning + list queries).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".started_at IS 'First time the condition was sustained past for_duration. Partition key.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".resolved_at IS 'Timestamp of flip to resolved (NULL while firing).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".last_notified_at IS 'Last successful Notify emission for this fingerprint.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".notification_count IS 'Count of Notify fan-outs for this fingerprint (monotonic per firing window).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".silenced IS 'TRUE when a matching silence suppressed Notify delivery.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".silence_id IS 'FK to fct_monitoring_silences.id when silenced (not enforced).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".labels IS 'Resolved labels (rule.labels merged with query groupby dimensions).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_alert_events".annotations IS 'Optional free-form annotations (e.g. summary text rendered at firing time).';

-- Pre-create today + next 2 days of partitions. The partition manager (13-07)
-- will keep this rolling forward via monitoring_ensure_partitions().
SELECT "05_monitoring".monitoring_ensure_partitions('60_evt_monitoring_alert_events', 3);

CREATE INDEX idx_alert_events_rule_fingerprint_started
    ON "05_monitoring"."60_evt_monitoring_alert_events" (rule_id, fingerprint, started_at DESC);
CREATE INDEX idx_alert_events_org_state_started
    ON "05_monitoring"."60_evt_monitoring_alert_events" (org_id, state, started_at DESC);

CREATE VIEW "05_monitoring".v_monitoring_alert_events AS
SELECT e.id, e.rule_id, r.name AS rule_name, r.severity_id,
       s.code AS severity_code, s.label AS severity_label,
       e.fingerprint, e.state, e.value, e.threshold, e.org_id,
       e.started_at, e.resolved_at, e.last_notified_at, e.notification_count,
       e.silenced, e.silence_id, e.labels, e.annotations
  FROM "05_monitoring"."60_evt_monitoring_alert_events" e
  LEFT JOIN "05_monitoring"."12_fct_monitoring_alert_rules" r ON r.id = e.rule_id
  LEFT JOIN "05_monitoring"."01_dim_monitoring_alert_severity" s ON s.id = r.severity_id;
COMMENT ON VIEW "05_monitoring".v_monitoring_alert_events IS 'Alert events joined with rule name + severity for list/detail reads.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring".v_monitoring_alert_events;
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_alert_events" CASCADE;
