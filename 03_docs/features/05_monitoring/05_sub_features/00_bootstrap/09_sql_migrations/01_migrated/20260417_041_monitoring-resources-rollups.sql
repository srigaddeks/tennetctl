-- UP ====
-- Metric rollup tables (1m / 5m / 1h) — empty shells, populated by pg_cron in 13-07.
-- Plus v_monitoring_resources view (drops the BYTEA hash from the exposed surface).

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_resources" AS
SELECT
    id,
    org_id,
    service_name,
    service_instance_id,
    service_version,
    attributes,
    created_at
FROM "05_monitoring"."11_fct_monitoring_resources";
COMMENT ON VIEW "05_monitoring"."v_monitoring_resources" IS 'Passthrough view — drops BYTEA resource_hash from the exposed surface.';

-- Rollup: 1-minute buckets
CREATE TABLE IF NOT EXISTS "05_monitoring"."70_evt_monitoring_metric_points_1m" (
    metric_id         SMALLINT    NOT NULL,
    labels_hash       BYTEA       NOT NULL,
    labels            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    resource_id       BIGINT      NOT NULL,
    org_id            VARCHAR(36) NOT NULL,
    bucket            TIMESTAMP   NOT NULL,
    count             BIGINT      NOT NULL DEFAULT 0,
    sum               DOUBLE PRECISION NULL,
    min               DOUBLE PRECISION NULL,
    max               DOUBLE PRECISION NULL,
    last              DOUBLE PRECISION NULL,
    histogram_counts  BIGINT[]    NULL,
    CONSTRAINT pk_evt_monitoring_metric_points_1m PRIMARY KEY (metric_id, labels_hash, bucket)
) PARTITION BY RANGE (bucket);
COMMENT ON TABLE "05_monitoring"."70_evt_monitoring_metric_points_1m" IS 'Metric rollup at 1-minute resolution. Populated by pg_cron in 13-07; empty shell in 13-01.';

CREATE TABLE "05_monitoring"."70_evt_monitoring_metric_points_1m_p20260417"
    PARTITION OF "05_monitoring"."70_evt_monitoring_metric_points_1m"
    FOR VALUES FROM ('2026-04-17 00:00:00') TO ('2026-04-18 00:00:00');
CREATE TABLE "05_monitoring"."70_evt_monitoring_metric_points_1m_p20260418"
    PARTITION OF "05_monitoring"."70_evt_monitoring_metric_points_1m"
    FOR VALUES FROM ('2026-04-18 00:00:00') TO ('2026-04-19 00:00:00');
CREATE TABLE "05_monitoring"."70_evt_monitoring_metric_points_1m_p20260419"
    PARTITION OF "05_monitoring"."70_evt_monitoring_metric_points_1m"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');

CREATE INDEX idx_evt_monitoring_mp_1m_metric_bucket ON "05_monitoring"."70_evt_monitoring_metric_points_1m" (metric_id, bucket DESC);
CREATE INDEX idx_evt_monitoring_mp_1m_org_bucket    ON "05_monitoring"."70_evt_monitoring_metric_points_1m" (org_id, bucket DESC);

-- Rollup: 5-minute buckets
CREATE TABLE IF NOT EXISTS "05_monitoring"."71_evt_monitoring_metric_points_5m" (
    metric_id         SMALLINT    NOT NULL,
    labels_hash       BYTEA       NOT NULL,
    labels            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    resource_id       BIGINT      NOT NULL,
    org_id            VARCHAR(36) NOT NULL,
    bucket            TIMESTAMP   NOT NULL,
    count             BIGINT      NOT NULL DEFAULT 0,
    sum               DOUBLE PRECISION NULL,
    min               DOUBLE PRECISION NULL,
    max               DOUBLE PRECISION NULL,
    last              DOUBLE PRECISION NULL,
    histogram_counts  BIGINT[]    NULL,
    CONSTRAINT pk_evt_monitoring_metric_points_5m PRIMARY KEY (metric_id, labels_hash, bucket)
) PARTITION BY RANGE (bucket);
COMMENT ON TABLE "05_monitoring"."71_evt_monitoring_metric_points_5m" IS 'Metric rollup at 5-minute resolution. Empty shell in 13-01.';

CREATE TABLE "05_monitoring"."71_evt_monitoring_metric_points_5m_p20260417"
    PARTITION OF "05_monitoring"."71_evt_monitoring_metric_points_5m"
    FOR VALUES FROM ('2026-04-17 00:00:00') TO ('2026-04-18 00:00:00');
CREATE TABLE "05_monitoring"."71_evt_monitoring_metric_points_5m_p20260418"
    PARTITION OF "05_monitoring"."71_evt_monitoring_metric_points_5m"
    FOR VALUES FROM ('2026-04-18 00:00:00') TO ('2026-04-19 00:00:00');
CREATE TABLE "05_monitoring"."71_evt_monitoring_metric_points_5m_p20260419"
    PARTITION OF "05_monitoring"."71_evt_monitoring_metric_points_5m"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');

CREATE INDEX idx_evt_monitoring_mp_5m_metric_bucket ON "05_monitoring"."71_evt_monitoring_metric_points_5m" (metric_id, bucket DESC);
CREATE INDEX idx_evt_monitoring_mp_5m_org_bucket    ON "05_monitoring"."71_evt_monitoring_metric_points_5m" (org_id, bucket DESC);

-- Rollup: 1-hour buckets
CREATE TABLE IF NOT EXISTS "05_monitoring"."72_evt_monitoring_metric_points_1h" (
    metric_id         SMALLINT    NOT NULL,
    labels_hash       BYTEA       NOT NULL,
    labels            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    resource_id       BIGINT      NOT NULL,
    org_id            VARCHAR(36) NOT NULL,
    bucket            TIMESTAMP   NOT NULL,
    count             BIGINT      NOT NULL DEFAULT 0,
    sum               DOUBLE PRECISION NULL,
    min               DOUBLE PRECISION NULL,
    max               DOUBLE PRECISION NULL,
    last              DOUBLE PRECISION NULL,
    histogram_counts  BIGINT[]    NULL,
    CONSTRAINT pk_evt_monitoring_metric_points_1h PRIMARY KEY (metric_id, labels_hash, bucket)
) PARTITION BY RANGE (bucket);
COMMENT ON TABLE "05_monitoring"."72_evt_monitoring_metric_points_1h" IS 'Metric rollup at 1-hour resolution. Empty shell in 13-01.';

CREATE TABLE "05_monitoring"."72_evt_monitoring_metric_points_1h_p20260417"
    PARTITION OF "05_monitoring"."72_evt_monitoring_metric_points_1h"
    FOR VALUES FROM ('2026-04-17 00:00:00') TO ('2026-04-18 00:00:00');
CREATE TABLE "05_monitoring"."72_evt_monitoring_metric_points_1h_p20260418"
    PARTITION OF "05_monitoring"."72_evt_monitoring_metric_points_1h"
    FOR VALUES FROM ('2026-04-18 00:00:00') TO ('2026-04-19 00:00:00');
CREATE TABLE "05_monitoring"."72_evt_monitoring_metric_points_1h_p20260419"
    PARTITION OF "05_monitoring"."72_evt_monitoring_metric_points_1h"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');

CREATE INDEX idx_evt_monitoring_mp_1h_metric_bucket ON "05_monitoring"."72_evt_monitoring_metric_points_1h" (metric_id, bucket DESC);
CREATE INDEX idx_evt_monitoring_mp_1h_org_bucket    ON "05_monitoring"."72_evt_monitoring_metric_points_1h" (org_id, bucket DESC);

-- DOWN ====
DROP TABLE IF EXISTS "05_monitoring"."72_evt_monitoring_metric_points_1h_p20260419";
DROP TABLE IF EXISTS "05_monitoring"."72_evt_monitoring_metric_points_1h_p20260418";
DROP TABLE IF EXISTS "05_monitoring"."72_evt_monitoring_metric_points_1h_p20260417";
DROP TABLE IF EXISTS "05_monitoring"."72_evt_monitoring_metric_points_1h";
DROP TABLE IF EXISTS "05_monitoring"."71_evt_monitoring_metric_points_5m_p20260419";
DROP TABLE IF EXISTS "05_monitoring"."71_evt_monitoring_metric_points_5m_p20260418";
DROP TABLE IF EXISTS "05_monitoring"."71_evt_monitoring_metric_points_5m_p20260417";
DROP TABLE IF EXISTS "05_monitoring"."71_evt_monitoring_metric_points_5m";
DROP TABLE IF EXISTS "05_monitoring"."70_evt_monitoring_metric_points_1m_p20260419";
DROP TABLE IF EXISTS "05_monitoring"."70_evt_monitoring_metric_points_1m_p20260418";
DROP TABLE IF EXISTS "05_monitoring"."70_evt_monitoring_metric_points_1m_p20260417";
DROP TABLE IF EXISTS "05_monitoring"."70_evt_monitoring_metric_points_1m";
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_resources";
