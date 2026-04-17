-- UP ====
-- 13-08a Task 1 — Alert rules + silences + rule state.
--
-- Introduces threshold-based alert rules that reuse the monitoring Query DSL
-- (compiled via 13-05 compile_metrics_query / compile_logs_query). The
-- evaluator worker (13-08b) reads fct_monitoring_alert_rules and writes
-- evt_monitoring_alert_events (migration 050). Silences suppress Notify
-- delivery for matching alerts without dropping the audit trail.

-- Severity lookup (seeded inline — small, stable, never deprecated).
CREATE TABLE "05_monitoring"."01_dim_monitoring_alert_severity" (
    id              SMALLINT    PRIMARY KEY,
    code            TEXT        NOT NULL UNIQUE,
    label           TEXT        NOT NULL,
    deprecated_at   TIMESTAMP   NULL
);
COMMENT ON TABLE  "05_monitoring"."01_dim_monitoring_alert_severity" IS 'Alert severity enum. 1=info 2=warn 3=error 4=critical. Seeded, never mutated.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_alert_severity".id IS 'Stable PK — never renumbered.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_alert_severity".code IS 'Machine code (info/warn/error/critical).';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_alert_severity".label IS 'Display label.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_alert_severity".deprecated_at IS 'Soft-deprecation marker — never DELETE rows.';

INSERT INTO "05_monitoring"."01_dim_monitoring_alert_severity" (id, code, label) VALUES
    (1, 'info',     'Info'),
    (2, 'warn',     'Warn'),
    (3, 'error',    'Error'),
    (4, 'critical', 'Critical');

-- Alert rules — DSL-backed threshold rules with for-duration gating.
CREATE TABLE "05_monitoring"."12_fct_monitoring_alert_rules" (
    id                   VARCHAR(36)   PRIMARY KEY,
    org_id               UUID          NOT NULL,
    name                 TEXT          NOT NULL,
    description          TEXT          NULL,
    target               TEXT          NOT NULL,
    dsl                  JSONB         NOT NULL,
    condition            JSONB         NOT NULL,
    severity_id          SMALLINT      NOT NULL
                                       REFERENCES "05_monitoring"."01_dim_monitoring_alert_severity"(id),
    notify_template_key  TEXT          NOT NULL,
    labels               JSONB         NOT NULL DEFAULT '{}'::jsonb,
    is_active            BOOLEAN       NOT NULL DEFAULT TRUE,
    paused_until         TIMESTAMP     NULL,
    deleted_at           TIMESTAMP     NULL,
    created_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monitoring_alert_rules_target CHECK (target IN ('metrics','logs'))
);
COMMENT ON TABLE  "05_monitoring"."12_fct_monitoring_alert_rules" IS 'Alert rules — JSON DSL queries evaluated every 30s by the monitoring alert worker (13-08b). Fires on condition breach sustained for condition.for_duration_seconds.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".org_id IS 'Owning org — all queries are org-scoped.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".name IS 'Human-readable rule name, unique per org among active rules.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".description IS 'Optional long-form description.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".target IS 'DSL target: metrics|logs. Checked against chk_monitoring_alert_rules_target.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".dsl IS 'Monitoring Query DSL body (13-05). Compiled per-evaluation via compile_metrics_query/compile_logs_query.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".condition IS 'Threshold condition: {op: gt|gte|lt|lte|eq|ne, threshold: number, for_duration_seconds: int>=0}.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".severity_id IS 'FK to dim_monitoring_alert_severity.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".notify_template_key IS 'Notify template key invoked on firing/resolved transitions.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".labels IS 'Arbitrary labels merged into fingerprint + notify variables.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".is_active IS 'Only active rules are evaluated.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".paused_until IS 'Temporary pause — skipped until this timestamp. NULL means not paused.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".deleted_at IS 'Soft-delete marker.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".created_at IS 'Creation timestamp (UTC, naive).';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".updated_at IS 'Last-updated timestamp — set by application on every UPDATE.';

CREATE UNIQUE INDEX uq_monitoring_alert_rules_org_name_active
    ON "05_monitoring"."12_fct_monitoring_alert_rules" (org_id, name)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_monitoring_alert_rules_org_active
    ON "05_monitoring"."12_fct_monitoring_alert_rules" (org_id, is_active)
    WHERE deleted_at IS NULL;

-- Evaluator state — written by 13-08b worker, created now so the worker plan
-- doesn't need its own schema migration.
CREATE TABLE "05_monitoring"."20_dtl_monitoring_rule_state" (
    rule_id                VARCHAR(36)  PRIMARY KEY
                                        REFERENCES "05_monitoring"."12_fct_monitoring_alert_rules"(id) ON DELETE CASCADE,
    last_eval_at           TIMESTAMP    NULL,
    last_eval_duration_ms  INT          NULL,
    last_error             TEXT         NULL,
    pending_fingerprints   JSONB        NOT NULL DEFAULT '{}'::jsonb,
    updated_at             TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE  "05_monitoring"."20_dtl_monitoring_rule_state" IS 'Per-rule evaluator state. pending_fingerprints maps fingerprint -> first_breach_at timestamp, driving for_duration gating.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_rule_state".rule_id IS 'FK to fct_monitoring_alert_rules. Cascade on delete.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_rule_state".last_eval_at IS 'Timestamp of most recent evaluation.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_rule_state".last_eval_duration_ms IS 'Wall-clock duration of the last evaluation.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_rule_state".last_error IS 'Last error string if evaluation failed.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_rule_state".pending_fingerprints IS 'JSON map {fingerprint: first_breach_iso}. Rows graduate to firing once now - first_breach_at >= for_duration_seconds.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_rule_state".updated_at IS 'Last-updated timestamp.';

-- Silences — suppress notify fan-out for matching fingerprints.
CREATE TABLE "05_monitoring"."13_fct_monitoring_silences" (
    id           VARCHAR(36)  PRIMARY KEY,
    org_id       UUID         NOT NULL,
    matcher      JSONB        NOT NULL,
    starts_at    TIMESTAMP    NOT NULL,
    ends_at      TIMESTAMP    NOT NULL,
    reason       TEXT         NOT NULL,
    created_by   UUID         NOT NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at   TIMESTAMP    NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monitoring_silences_time CHECK (ends_at > starts_at)
);
COMMENT ON TABLE  "05_monitoring"."13_fct_monitoring_silences" IS 'Silence windows — alerts whose labels match a silence during [starts_at, ends_at) fire into evt_monitoring_alert_events but bypass Notify.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".org_id IS 'Owning org.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".matcher IS 'JSON matcher: {rule_id?, labels?: {k: v}}. Empty object matches nothing.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".starts_at IS 'Silence window start (UTC, naive).';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".ends_at IS 'Silence window end (UTC, naive). Must be strictly greater than starts_at.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".reason IS 'Human-readable reason.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".created_by IS 'User who created the silence.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".is_active IS 'Soft toggle.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".deleted_at IS 'Soft-delete marker.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".created_at IS 'Creation timestamp.';
COMMENT ON COLUMN "05_monitoring"."13_fct_monitoring_silences".updated_at IS 'Last-updated timestamp.';

CREATE INDEX idx_monitoring_silences_org_active
    ON "05_monitoring"."13_fct_monitoring_silences" (org_id, is_active, ends_at)
    WHERE deleted_at IS NULL;

-- Views
CREATE VIEW "05_monitoring".v_monitoring_alert_rules AS
SELECT r.id, r.org_id, r.name, r.description, r.target, r.dsl, r.condition,
       r.severity_id, s.code AS severity_code, s.label AS severity_label,
       r.notify_template_key, r.labels, r.is_active, r.paused_until,
       r.deleted_at, r.created_at, r.updated_at,
       (r.deleted_at IS NOT NULL) AS is_deleted
  FROM "05_monitoring"."12_fct_monitoring_alert_rules" r
  JOIN "05_monitoring"."01_dim_monitoring_alert_severity" s ON s.id = r.severity_id
 WHERE r.deleted_at IS NULL;
COMMENT ON VIEW "05_monitoring".v_monitoring_alert_rules IS 'Active alert rules with severity code/label joined in.';

CREATE VIEW "05_monitoring".v_monitoring_silences AS
SELECT id, org_id, matcher, starts_at, ends_at, reason, created_by,
       is_active, deleted_at, created_at, updated_at,
       (deleted_at IS NOT NULL) AS is_deleted
  FROM "05_monitoring"."13_fct_monitoring_silences"
 WHERE deleted_at IS NULL;
COMMENT ON VIEW "05_monitoring".v_monitoring_silences IS 'Active silences.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring".v_monitoring_silences;
DROP VIEW  IF EXISTS "05_monitoring".v_monitoring_alert_rules;
DROP TABLE IF EXISTS "05_monitoring"."13_fct_monitoring_silences";
DROP TABLE IF EXISTS "05_monitoring"."20_dtl_monitoring_rule_state";
DROP TABLE IF EXISTS "05_monitoring"."12_fct_monitoring_alert_rules";
DROP TABLE IF EXISTS "05_monitoring"."01_dim_monitoring_alert_severity";
