-- UP ====
-- Incident grouping rules and back-compat columns for escalation + actions

-- Detail: incident grouping rules per alert rule
CREATE TABLE "05_monitoring"."20_dtl_monitoring_incident_grouping_rules" (
    rule_id VARCHAR(36) PRIMARY KEY REFERENCES "05_monitoring"."12_fct_monitoring_alert_rules"(id) ON DELETE CASCADE,
    group_by JSONB NOT NULL DEFAULT '[]'::jsonb,
    group_window_seconds INT NOT NULL DEFAULT 300,
    dedup_strategy TEXT NOT NULL DEFAULT 'fingerprint' CHECK (dedup_strategy IN ('fingerprint', 'label_set', 'custom_key')),
    custom_template TEXT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX "idx_dtl_incident_grouping_active" ON "05_monitoring"."20_dtl_monitoring_incident_grouping_rules"(is_active);

COMMENT ON TABLE "05_monitoring"."20_dtl_monitoring_incident_grouping_rules" IS 'Grouping rules per alert rule: dedup strategy, group_by keys, windows';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_incident_grouping_rules".rule_id IS 'FK to alert rule (PK)';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_incident_grouping_rules".group_by IS 'Array of label keys to group by (for label_set strategy). Empty array defaults to fingerprint strategy.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_incident_grouping_rules".group_window_seconds IS 'Window within which new alerts are grouped into existing incident (default 300s). Older incidents do not accept new joins.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_incident_grouping_rules".dedup_strategy IS 'Strategy: fingerprint (rule_id+alert fingerprint), label_set (rule_id+selected labels), custom_key (Jinja2 template)';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_incident_grouping_rules".custom_template IS 'Jinja2 sandboxed template for custom_key strategy (receives rule_id, fingerprint, labels as context)';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_incident_grouping_rules".is_active IS 'Enable/disable grouping for this rule without deleting config';

-- Back-compat: add incident_id FK to escalation state table
ALTER TABLE "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
ADD COLUMN incident_id VARCHAR(36) NULL REFERENCES "05_monitoring"."10_fct_monitoring_incidents"(id) ON DELETE CASCADE;

CREATE INDEX "idx_dtl_escalation_state_incident" ON "05_monitoring"."20_dtl_monitoring_alert_escalation_state"(incident_id) WHERE incident_id IS NOT NULL;

COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".incident_id IS 'New: FK to incident (used when grouping enabled). Legacy rows with alert_event_id-only continue draining.';

-- Back-compat: add incident_id FK to action deliveries table
ALTER TABLE "05_monitoring"."40_lnk_monitoring_action_deliveries"
ADD COLUMN incident_id VARCHAR(36) NULL REFERENCES "05_monitoring"."10_fct_monitoring_incidents"(id) ON DELETE CASCADE;

CREATE INDEX "idx_lnk_action_deliveries_incident" ON "05_monitoring"."40_lnk_monitoring_action_deliveries"(incident_id) WHERE incident_id IS NOT NULL;

COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_action_deliveries".incident_id IS 'New: FK to incident (used when actions dispatched on incident transitions). Legacy rows with alert_event_id-only continue draining.';

-- DOWN ====
DROP INDEX IF EXISTS "05_monitoring"."idx_lnk_action_deliveries_incident";
ALTER TABLE "05_monitoring"."40_lnk_monitoring_action_deliveries"
DROP COLUMN incident_id;

DROP INDEX IF EXISTS "05_monitoring"."idx_dtl_escalation_state_incident";
ALTER TABLE "05_monitoring"."20_dtl_monitoring_alert_escalation_state"
DROP COLUMN incident_id;

DROP INDEX IF EXISTS "05_monitoring"."idx_dtl_incident_grouping_active";
DROP TABLE IF EXISTS "05_monitoring"."20_dtl_monitoring_incident_grouping_rules";
