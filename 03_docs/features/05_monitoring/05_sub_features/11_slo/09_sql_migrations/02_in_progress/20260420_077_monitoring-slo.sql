-- SLO definition, indicator details, and burn rate thresholds
-- UP ====

CREATE TABLE "05_monitoring"."01_dim_monitoring_slo_indicator_kind" (
  id                SMALLINT PRIMARY KEY,
  code              TEXT NOT NULL UNIQUE,
  label             TEXT NOT NULL,
  description       TEXT,
  deprecated_at     TIMESTAMP,
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by        VARCHAR(36),
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_by        VARCHAR(36)
);

COMMENT ON TABLE "05_monitoring"."01_dim_monitoring_slo_indicator_kind" IS
  'SLO indicator type: ratio, threshold, latency_pct.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_slo_indicator_kind".id IS
  'Permanent ID (never reused): 1=ratio, 2=threshold, 3=latency_pct.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_slo_indicator_kind".code IS
  'Machine code for this indicator type.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_slo_indicator_kind".label IS
  'Human-readable label.';


CREATE TABLE "05_monitoring"."02_dim_monitoring_slo_window_kind" (
  id                SMALLINT PRIMARY KEY,
  code              TEXT NOT NULL UNIQUE,
  label             TEXT NOT NULL,
  description       TEXT,
  deprecated_at     TIMESTAMP,
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by        VARCHAR(36),
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_by        VARCHAR(36)
);

COMMENT ON TABLE "05_monitoring"."02_dim_monitoring_slo_window_kind" IS
  'SLO evaluation window type: rolling 7d/28d/30d, or calendar month/quarter.';
COMMENT ON COLUMN "05_monitoring"."02_dim_monitoring_slo_window_kind".id IS
  'Permanent IDs: 1=rolling_7d, 2=rolling_28d, 3=rolling_30d, 4=calendar_month, 5=calendar_quarter.';


CREATE TABLE "05_monitoring"."10_fct_monitoring_slos" (
  id                VARCHAR(36) PRIMARY KEY,
  org_id            VARCHAR(36) NOT NULL,
  workspace_id      VARCHAR(36),
  name              TEXT NOT NULL,
  slug              TEXT NOT NULL,
  description       TEXT,
  indicator_kind_id SMALLINT NOT NULL REFERENCES "05_monitoring"."01_dim_monitoring_slo_indicator_kind"(id),
  window_kind_id    SMALLINT NOT NULL REFERENCES "05_monitoring"."02_dim_monitoring_slo_window_kind"(id),
  target_pct        NUMERIC(6, 4) NOT NULL CHECK (target_pct > 0 AND target_pct < 100),
  severity_id       SMALLINT NOT NULL REFERENCES "05_monitoring"."01_dim_monitoring_alert_severity"(id),
  owner_user_id     VARCHAR(36),
  is_active         BOOLEAN NOT NULL DEFAULT true,
  is_test           BOOLEAN NOT NULL DEFAULT false,
  deleted_at        TIMESTAMP,
  created_by        VARCHAR(36) NOT NULL,
  updated_by        VARCHAR(36) NOT NULL,
  created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_fct_monitoring_slos_org_deleted
  ON "05_monitoring"."10_fct_monitoring_slos"(org_id, deleted_at);
CREATE UNIQUE INDEX uq_fct_monitoring_slos_org_slug
  ON "05_monitoring"."10_fct_monitoring_slos"(org_id, slug) WHERE deleted_at IS NULL;

COMMENT ON TABLE "05_monitoring"."10_fct_monitoring_slos" IS
  'Service Level Objective definitions. Operators define target reliability and observation window.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_slos".slug IS
  'URL-safe unique name per org.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_slos".target_pct IS
  'Target attainment percentage (e.g. 99.9000 for "three nines").';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_slos".severity_id IS
  'Default alert severity when this SLO breaches.';


CREATE TABLE "05_monitoring"."20_dtl_monitoring_slo_indicator" (
  slo_id                VARCHAR(36) PRIMARY KEY REFERENCES "05_monitoring"."10_fct_monitoring_slos"(id) ON DELETE CASCADE,
  good_query            TEXT,
  total_query           TEXT,
  threshold_metric_id   VARCHAR(36),
  threshold_value       NUMERIC,
  threshold_op          TEXT CHECK (threshold_op IN ('lt', 'lte', 'gt', 'gte', 'eq')),
  latency_percentile    NUMERIC,
  created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE "05_monitoring"."20_dtl_monitoring_slo_indicator" IS
  'Fixed-detail indicator config per SLO. Fields populated by indicator_kind.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_slo_indicator".good_query IS
  'DSL or SQL query for success/good events. Used by ratio and latency indicators.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_slo_indicator".total_query IS
  'DSL or SQL query for total events. Used by ratio indicator.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_slo_indicator".threshold_metric_id IS
  'Metric ID for threshold-type SLO; metric value compared against threshold_value.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_slo_indicator".threshold_op IS
  'Comparison operator for threshold SLO (e.g., latency_p99 > 1000ms).';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_slo_indicator".latency_percentile IS
  'For latency_pct indicator, the percentile (e.g., 99.0 for p99).';


CREATE TABLE "05_monitoring"."21_dtl_monitoring_slo_burn_thresholds" (
  slo_id                VARCHAR(36) PRIMARY KEY REFERENCES "05_monitoring"."10_fct_monitoring_slos"(id) ON DELETE CASCADE,
  fast_window_seconds   INT NOT NULL DEFAULT 3600,
  fast_burn_rate        NUMERIC NOT NULL DEFAULT 14.4,
  slow_window_seconds   INT NOT NULL DEFAULT 21600,
  slow_burn_rate        NUMERIC NOT NULL DEFAULT 6.0,
  page_on_fast          BOOLEAN NOT NULL DEFAULT true,
  page_on_slow          BOOLEAN NOT NULL DEFAULT true,
  created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE "05_monitoring"."21_dtl_monitoring_slo_burn_thresholds" IS
  'Google SRE multi-window burn rate thresholds. Default: fast=14.4× over 1h, slow=6.0× over 6h.';


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
DROP TABLE IF EXISTS "05_monitoring"."21_dtl_monitoring_slo_burn_thresholds";
DROP TABLE IF EXISTS "05_monitoring"."20_dtl_monitoring_slo_indicator";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_slos";
DROP TABLE IF EXISTS "05_monitoring"."02_dim_monitoring_slo_window_kind";
DROP TABLE IF EXISTS "05_monitoring"."01_dim_monitoring_slo_indicator_kind";
