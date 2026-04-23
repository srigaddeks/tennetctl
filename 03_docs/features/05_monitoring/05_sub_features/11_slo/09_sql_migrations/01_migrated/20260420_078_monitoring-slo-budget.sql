-- SLO evaluations (event stream) and breach tracking
-- UP ====

CREATE TABLE "05_monitoring"."60_evt_monitoring_slo_evaluations" (
  id                VARCHAR(36) NOT NULL,
  slo_id            VARCHAR(36) NOT NULL REFERENCES "05_monitoring"."10_fct_monitoring_slos"(id),
  org_id            VARCHAR(36) NOT NULL,
  window_start      TIMESTAMP NOT NULL,
  window_end        TIMESTAMP NOT NULL,
  good_count        BIGINT NOT NULL,
  total_count       BIGINT NOT NULL,
  attainment_pct    NUMERIC(7, 5) NOT NULL,
  budget_remaining_pct NUMERIC(7, 5) NOT NULL,
  burn_rate_1h      NUMERIC NOT NULL,
  burn_rate_6h      NUMERIC NOT NULL,
  burn_rate_24h     NUMERIC NOT NULL,
  burn_rate_3d      NUMERIC NOT NULL,
  evaluated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id, evaluated_at)
) PARTITION BY RANGE (evaluated_at);

COMMENT ON TABLE "05_monitoring"."60_evt_monitoring_slo_evaluations" IS
  'Append-only event stream. One row per SLO per evaluation tick. Daily partitions, 90-day retention.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".window_start IS
  'Start of the SLO observation window (e.g., 30 days ago for rolling_30d).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".window_end IS
  'End of the SLO observation window (typically ~now).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".attainment_pct IS
  'Observed success ratio as a percentage (e.g., 99.95000).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".budget_remaining_pct IS
  'Percentage of the error budget remaining. Negative = over budget.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".burn_rate_1h IS
  'Multiplier of error rate over the past 1 hour relative to budget.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".burn_rate_6h IS
  'Multiplier of error rate over the past 6 hours relative to budget.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".burn_rate_24h IS
  'Multiplier of error rate over the past 24 hours relative to budget.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_slo_evaluations".burn_rate_3d IS
  'Multiplier of error rate over the past 3 days relative to budget.';

CREATE INDEX idx_evt_monitoring_slo_evaluations_slo_evaluated
  ON "05_monitoring"."60_evt_monitoring_slo_evaluations"(slo_id, evaluated_at DESC);

-- Create daily partitions for current month and future months (script populates)
CREATE TABLE "05_monitoring"."60_evt_monitoring_slo_evaluations_2026_04_20"
  PARTITION OF "05_monitoring"."60_evt_monitoring_slo_evaluations"
  FOR VALUES FROM ('2026-04-20') TO ('2026-04-21');

CREATE TABLE "05_monitoring"."60_evt_monitoring_slo_evaluations_2026_04_21"
  PARTITION OF "05_monitoring"."60_evt_monitoring_slo_evaluations"
  FOR VALUES FROM ('2026-04-21') TO ('2026-04-22');

CREATE TABLE "05_monitoring"."60_evt_monitoring_slo_evaluations_2026_04_22"
  PARTITION OF "05_monitoring"."60_evt_monitoring_slo_evaluations"
  FOR VALUES FROM ('2026-04-22') TO ('2026-04-23');


CREATE TABLE "05_monitoring"."61_evt_monitoring_slo_breaches" (
  id                VARCHAR(36) PRIMARY KEY,
  slo_id            VARCHAR(36) NOT NULL REFERENCES "05_monitoring"."10_fct_monitoring_slos"(id),
  org_id            VARCHAR(36) NOT NULL,
  breach_kind       TEXT NOT NULL CHECK (breach_kind IN ('budget_exhausted', 'fast_burn', 'slow_burn', 'target_missed')),
  burn_rate         NUMERIC,
  alert_event_id    VARCHAR(36),
  occurred_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  resolved_at       TIMESTAMP
);

COMMENT ON TABLE "05_monitoring"."61_evt_monitoring_slo_breaches" IS
  'Breach events: budget exhaustion, fast/slow burn threshold crossings.';
COMMENT ON COLUMN "05_monitoring"."61_evt_monitoring_slo_breaches".breach_kind IS
  'Type of breach: budget_exhausted (attainment < target), fast_burn (1h rate >= threshold), slow_burn (6h rate >= threshold), target_missed.';
COMMENT ON COLUMN "05_monitoring"."61_evt_monitoring_slo_breaches".burn_rate IS
  'Observed burn rate multiplier when fast/slow burn breach occurred.';
COMMENT ON COLUMN "05_monitoring"."61_evt_monitoring_slo_breaches".alert_event_id IS
  'Links to the synthetic alert event emitted by monitoring.slo.burn_alert node.';
COMMENT ON COLUMN "05_monitoring"."61_evt_monitoring_slo_breaches".resolved_at IS
  'When the breach condition cleared (filled on next evaluator tick).';

CREATE UNIQUE INDEX uq_evt_monitoring_slo_breaches_open
  ON "05_monitoring"."61_evt_monitoring_slo_breaches"(slo_id, breach_kind)
  WHERE resolved_at IS NULL;

COMMENT ON INDEX "05_monitoring".uq_evt_monitoring_slo_breaches_open IS
  'Prevent duplicate open breaches of the same kind per SLO.';

CREATE INDEX idx_evt_monitoring_slo_breaches_slo_occurred
  ON "05_monitoring"."61_evt_monitoring_slo_breaches"(slo_id, occurred_at DESC);


-- ── View for SLOs (moved from 077 so evt_monitoring_slo_evaluations exists) ──
CREATE OR REPLACE VIEW "05_monitoring".v_monitoring_slos AS
SELECT
  s.id,
  s.org_id,
  s.workspace_id,
  s.name,
  s.slug,
  s.description,
  ik.id AS indicator_kind_id,
  ik.code AS indicator_kind_code,
  wk.id AS window_kind_id,
  wk.code AS window_kind_code,
  s.target_pct,
  s.severity_id,
  sv.code AS severity_code,
  s.owner_user_id,
  s.is_active,
  s.created_by,
  s.created_at,
  s.updated_at,
  i.good_query,
  i.total_query,
  i.threshold_metric_id,
  i.threshold_value,
  i.threshold_op,
  i.latency_percentile,
  b.fast_window_seconds,
  b.fast_burn_rate,
  b.slow_window_seconds,
  b.slow_burn_rate,
  b.page_on_fast,
  b.page_on_slow,
  COALESCE(latest_eval.attainment_pct, 0) AS attainment_pct,
  COALESCE(latest_eval.budget_remaining_pct, 100) AS budget_remaining_pct,
  COALESCE(latest_eval.burn_rate_1h, 0) AS burn_rate_1h,
  COALESCE(latest_eval.burn_rate_6h, 0) AS burn_rate_6h,
  COALESCE(latest_eval.burn_rate_24h, 0) AS burn_rate_24h,
  COALESCE(latest_eval.burn_rate_3d, 0) AS burn_rate_3d,
  CASE
    WHEN COALESCE(latest_eval.attainment_pct, 100) < s.target_pct THEN 'breaching'
    WHEN COALESCE(latest_eval.burn_rate_1h, 0) >= b.fast_burn_rate THEN 'warning'
    WHEN COALESCE(latest_eval.burn_rate_6h, 0) >= b.slow_burn_rate THEN 'warning'
    ELSE 'healthy'
  END AS status
FROM "05_monitoring"."10_fct_monitoring_slos" s
LEFT JOIN "05_monitoring"."01_dim_monitoring_slo_indicator_kind" ik
  ON s.indicator_kind_id = ik.id
LEFT JOIN "05_monitoring"."02_dim_monitoring_slo_window_kind" wk
  ON s.window_kind_id = wk.id
LEFT JOIN "05_monitoring"."01_dim_monitoring_alert_severity" sv
  ON s.severity_id = sv.id
LEFT JOIN "05_monitoring"."20_dtl_monitoring_slo_indicator" i
  ON s.id = i.slo_id
LEFT JOIN "05_monitoring"."21_dtl_monitoring_slo_burn_thresholds" b
  ON s.id = b.slo_id
LEFT JOIN LATERAL (
  SELECT DISTINCT ON (slo_id)
    slo_id, attainment_pct, budget_remaining_pct,
    burn_rate_1h, burn_rate_6h, burn_rate_24h, burn_rate_3d
  FROM "05_monitoring"."60_evt_monitoring_slo_evaluations"
  WHERE slo_id = s.id AND evaluated_at IS NOT NULL
  ORDER BY slo_id, evaluated_at DESC
  LIMIT 1
) latest_eval ON true
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW "05_monitoring".v_monitoring_slos IS
  'SLO list with latest evaluation metrics and computed status.';


-- DOWN ====

DROP VIEW IF EXISTS "05_monitoring".v_monitoring_slos;
DROP TABLE IF EXISTS "05_monitoring"."61_evt_monitoring_slo_breaches";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_slo_evaluations_2026_04_22";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_slo_evaluations_2026_04_21";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_slo_evaluations_2026_04_20";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_slo_evaluations";
