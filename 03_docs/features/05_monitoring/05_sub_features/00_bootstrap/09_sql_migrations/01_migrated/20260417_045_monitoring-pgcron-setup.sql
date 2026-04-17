-- UP ====
-- 13-07 Task 1 — pg_cron setup (best-effort) + retention policy table.
--
-- pg_cron is unavailable on postgres:16-alpine (no package in apk), so this
-- migration attempts CREATE EXTENSION inside a DO block and falls through if
-- the extension is missing. All rollup/partition scheduling is done by asyncio
-- workers in the Python runtime (see workers/rollup_scheduler.py, partition_manager.py).
--
-- The retention policy table is created unconditionally — both pg_cron and the
-- asyncio partition manager read from it.

DO $$
BEGIN
    BEGIN
        CREATE EXTENSION IF NOT EXISTS pg_cron;
        RAISE NOTICE 'pg_cron extension installed';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE 'pg_cron unavailable (%) — asyncio worker fallback will drive rollups/partitions', SQLERRM;
    END;
END
$$;

-- Ensure pgcrypto for digest() used by rollup procs (labels_hash).
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- Retention policies — drives partition manager + query compiler cold-check.
CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_retention_policies" (
    id              SMALLINT      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code            TEXT          NOT NULL UNIQUE,
    table_name      TEXT          NOT NULL,
    days_to_keep    SMALLINT      NOT NULL CHECK (days_to_keep > 0),
    tier            TEXT          NOT NULL DEFAULT 'hot'
                                  CHECK (tier IN ('hot','warm','cold')),
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP     NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_retention_policies" IS 'Per-table retention policy — drives partition manager + query compiler cold-range check.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_retention_policies".code IS 'Stable machine code for the policy (e.g. logs_hot).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_retention_policies".table_name IS 'Fully-qualified or unqualified partitioned parent table name (without schema prefix).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_retention_policies".days_to_keep IS 'Partitions older than CURRENT_DATE - days_to_keep are dropped.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_retention_policies".tier IS 'Informational tier: hot/warm/cold.';

CREATE INDEX IF NOT EXISTS idx_fct_monitoring_retention_policies_active
    ON "05_monitoring"."10_fct_monitoring_retention_policies" (is_active) WHERE deleted_at IS NULL;

-- View
CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_retention_policies" AS
SELECT
    id, code, table_name, days_to_keep, tier, is_active,
    deleted_at, created_at, updated_at,
    (deleted_at IS NOT NULL) AS is_deleted
  FROM "05_monitoring"."10_fct_monitoring_retention_policies";
COMMENT ON VIEW "05_monitoring"."v_monitoring_retention_policies" IS 'Read view over retention policies.';

-- Seed defaults
INSERT INTO "05_monitoring"."10_fct_monitoring_retention_policies"
    (code, table_name, days_to_keep, tier)
VALUES
    ('logs_hot',             '60_evt_monitoring_logs',               14,  'hot'),
    ('spans_hot',            '62_evt_monitoring_spans',               7,  'hot'),
    ('metric_points_hot',    '61_evt_monitoring_metric_points',       7,  'hot'),
    ('metric_points_1m',     '70_evt_monitoring_metric_points_1m',   30,  'warm'),
    ('metric_points_5m',     '71_evt_monitoring_metric_points_5m',   90,  'warm'),
    ('metric_points_1h',     '72_evt_monitoring_metric_points_1h',  365,  'cold'),
    ('alert_events',         '60_evt_monitoring_alert_events',       90,  'hot')
ON CONFLICT (code) DO NOTHING;

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_retention_policies";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_retention_policies";
-- leaving pgcrypto / pg_cron extensions in place intentionally (other features may use them)
