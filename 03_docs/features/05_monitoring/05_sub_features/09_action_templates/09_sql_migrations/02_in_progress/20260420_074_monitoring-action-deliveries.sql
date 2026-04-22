-- UP ====
-- 40-02 Task 2 — Action deliveries: audit log for template dispatch attempts
--
-- Append-only event log tracking each action delivery attempt. Partitioned daily
-- on started_at with 30-day retention policy. Stores payload hash for forensics,
-- response excerpt (truncated), error messages, and retry state.

-- ── Action deliveries (append-only, partitioned) ─────────────────────────────────
CREATE TABLE "05_monitoring"."65_evt_monitoring_action_deliveries" (
    id                      VARCHAR(36)   PRIMARY KEY,
    template_id             VARCHAR(36)   NOT NULL
                                          REFERENCES "05_monitoring"."14_fct_monitoring_action_templates"(id),
    alert_event_id          VARCHAR(36)   NULL
                                          REFERENCES "05_monitoring"."60_evt_monitoring_alert_events"(id),
    escalation_state_id     VARCHAR(36)   NULL
                                          REFERENCES "05_monitoring"."20_dtl_monitoring_alert_escalation_state"(alert_event_id),
    attempt                 SMALLINT      NOT NULL DEFAULT 1,
    status_code             INT           NULL,
    request_payload_hash    TEXT          NOT NULL,
    response_excerpt        TEXT          NULL,
    error_excerpt           TEXT          NULL,
    started_at              TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at            TIMESTAMP     NULL,
    succeeded_at            TIMESTAMP     NULL,
    CONSTRAINT chk_monitoring_action_deliveries_timing
        CHECK (completed_at IS NULL OR completed_at >= started_at),
    CONSTRAINT chk_monitoring_action_deliveries_success
        CHECK (succeeded_at IS NULL OR (completed_at IS NOT NULL AND status_code >= 200 AND status_code < 300))
);
COMMENT ON TABLE  "05_monitoring"."65_evt_monitoring_action_deliveries" IS 'Append-only delivery log. Partitioned daily on started_at. 30-day retention. Tracks each attempt, retry state, response, and outcome.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".template_id IS 'FK to fct_monitoring_action_templates.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".alert_event_id IS 'FK to alert event that triggered this delivery (optional — can be triggered by escalation or manual test).';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".escalation_state_id IS 'FK to escalation state if triggered by escalation step (optional).';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".attempt IS 'Attempt number (1-indexed). Retry logic increments this.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".status_code IS 'HTTP status code of response. NULL if network error or no response received.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".request_payload_hash IS 'SHA256 hash of rendered request body (for forensics/dedup).';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".response_excerpt IS 'First 4KB of response body (truncated). NULL if no response or network error.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".error_excerpt IS 'Error message (e.g., network timeout, render error). NULL on success.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".started_at IS 'Dispatch attempt start timestamp. Used for partitioning and retention.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".completed_at IS 'Timestamp when attempt finished (success or permanent failure). NULL until attempt completes.';
COMMENT ON COLUMN "05_monitoring"."65_evt_monitoring_action_deliveries".succeeded_at IS 'Set when delivery succeeds (2xx response). NULL if failed or pending retry.';

-- Indexes for common queries
CREATE INDEX idx_monitoring_action_deliveries_template_started
    ON "05_monitoring"."65_evt_monitoring_action_deliveries" (template_id, started_at DESC);
CREATE INDEX idx_monitoring_action_deliveries_alert_event
    ON "05_monitoring"."65_evt_monitoring_action_deliveries" (alert_event_id, started_at DESC)
    WHERE alert_event_id IS NOT NULL;
-- Partial index for retry scans (find pending attempts)
CREATE INDEX idx_monitoring_action_deliveries_pending
    ON "05_monitoring"."65_evt_monitoring_action_deliveries" (template_id, started_at DESC)
    WHERE succeeded_at IS NULL AND completed_at IS NULL;

-- ── View for action deliveries ──────────────────────────────────────────────────
CREATE VIEW "05_monitoring".v_monitoring_action_deliveries AS
SELECT d.id, d.template_id, d.alert_event_id, d.escalation_state_id, d.attempt,
       d.status_code, d.request_payload_hash, d.response_excerpt, d.error_excerpt,
       d.started_at, d.completed_at, d.succeeded_at,
       t.name AS template_name, t.kind_id,
       k.code AS kind_code, k.label AS kind_label,
       a.id IS NOT NULL AS has_alert_event,
       CASE
           WHEN d.succeeded_at IS NOT NULL THEN 'succeeded'
           WHEN d.completed_at IS NOT NULL THEN 'failed'
           ELSE 'pending'
       END AS status
  FROM "05_monitoring"."65_evt_monitoring_action_deliveries" d
  JOIN "05_monitoring"."14_fct_monitoring_action_templates" t ON t.id = d.template_id
  JOIN "05_monitoring"."03_dim_monitoring_action_kind" k ON k.id = t.kind_id
  LEFT JOIN "05_monitoring"."60_evt_monitoring_alert_events" a ON a.id = d.alert_event_id;
COMMENT ON VIEW "05_monitoring".v_monitoring_action_deliveries IS 'Action deliveries with template and kind info joined in. Status computed from completion/success timestamps.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring".v_monitoring_action_deliveries;
DROP TABLE IF EXISTS "05_monitoring"."65_evt_monitoring_action_deliveries";
