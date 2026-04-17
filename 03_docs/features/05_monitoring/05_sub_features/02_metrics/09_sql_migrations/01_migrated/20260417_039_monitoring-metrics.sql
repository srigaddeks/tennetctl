-- UP ====
-- fct_monitoring_metrics (registry) + evt_monitoring_metric_points (partitioned).
-- Registry is carve-out per Phase 13 STATE.md decisions (catalog-style fct_*).

CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_metrics" (
    id                 SMALLINT GENERATED ALWAYS AS IDENTITY,
    org_id             VARCHAR(36) NOT NULL,
    key                TEXT        NOT NULL,
    kind_id            SMALLINT    NOT NULL,
    label_keys         TEXT[]      NOT NULL DEFAULT '{}',
    histogram_buckets  DOUBLE PRECISION[] NULL,
    max_cardinality    INT         NOT NULL DEFAULT 1000,
    description        TEXT        NOT NULL DEFAULT '',
    unit               TEXT        NOT NULL DEFAULT '',
    created_at         TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_metrics PRIMARY KEY (id),
    CONSTRAINT uq_fct_monitoring_metrics_org_key UNIQUE (org_id, key),
    CONSTRAINT fk_fct_monitoring_metrics_kind FOREIGN KEY (kind_id) REFERENCES "05_monitoring"."02_dim_monitoring_metric_kinds"(id),
    CONSTRAINT chk_fct_monitoring_metrics_histogram_buckets CHECK (
        kind_id <> 3
     OR (histogram_buckets IS NOT NULL AND array_length(histogram_buckets, 1) >= 1)
    )
);
COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_metrics" IS 'Metric registry: one row per (org, key). Carve-out: catalog-style fct_* with first-class columns for kind/buckets/cardinality. Used at every ingest row; SMALLINT id keeps evt rows compact.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_metrics".kind_id IS 'FK to dim_monitoring_metric_kinds (1=counter, 2=gauge, 3=histogram).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_metrics".label_keys IS 'Allowed label keys (tag names). Ingest path rejects labels not listed here (future 13-02).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_metrics".histogram_buckets IS 'Bucket upper bounds for histograms. CHECK enforces presence when kind=histogram.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_metrics".max_cardinality IS 'Max distinct label combinations. Increment is rejected once crossed.';

-- Metric points (partitioned)
CREATE TABLE IF NOT EXISTS "05_monitoring"."61_evt_monitoring_metric_points" (
    metric_id         SMALLINT    NOT NULL,
    resource_id       BIGINT      NOT NULL,
    org_id            VARCHAR(36) NOT NULL,
    workspace_id      VARCHAR(36) NULL,
    labels            JSONB       NOT NULL DEFAULT '{}'::jsonb,
    value             DOUBLE PRECISION NULL,
    histogram_counts  BIGINT[]    NULL,
    histogram_sum     DOUBLE PRECISION NULL,
    histogram_count   BIGINT      NULL,
    recorded_at       TIMESTAMP   NOT NULL,
    trace_id          TEXT        NULL,
    span_id           TEXT        NULL,
    CONSTRAINT pk_evt_monitoring_metric_points PRIMARY KEY (metric_id, recorded_at, resource_id),
    CONSTRAINT fk_evt_monitoring_metric_points_metric   FOREIGN KEY (metric_id)   REFERENCES "05_monitoring"."10_fct_monitoring_metrics"(id),
    CONSTRAINT fk_evt_monitoring_metric_points_resource FOREIGN KEY (resource_id) REFERENCES "05_monitoring"."11_fct_monitoring_resources"(id)
) PARTITION BY RANGE (recorded_at);
COMMENT ON TABLE "05_monitoring"."61_evt_monitoring_metric_points" IS 'Append-only metric point observations (counter inc, gauge set, histogram observe). Daily-partitioned.';

CREATE TABLE "05_monitoring"."61_evt_monitoring_metric_points_p20260417"
    PARTITION OF "05_monitoring"."61_evt_monitoring_metric_points"
    FOR VALUES FROM ('2026-04-17 00:00:00') TO ('2026-04-18 00:00:00');
CREATE TABLE "05_monitoring"."61_evt_monitoring_metric_points_p20260418"
    PARTITION OF "05_monitoring"."61_evt_monitoring_metric_points"
    FOR VALUES FROM ('2026-04-18 00:00:00') TO ('2026-04-19 00:00:00');
CREATE TABLE "05_monitoring"."61_evt_monitoring_metric_points_p20260419"
    PARTITION OF "05_monitoring"."61_evt_monitoring_metric_points"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');

CREATE INDEX idx_evt_monitoring_metric_points_metric_recorded ON "05_monitoring"."61_evt_monitoring_metric_points" (metric_id, recorded_at DESC);
CREATE INDEX idx_evt_monitoring_metric_points_org_recorded    ON "05_monitoring"."61_evt_monitoring_metric_points" (org_id, recorded_at DESC);
CREATE INDEX idx_evt_monitoring_metric_points_labels_gin      ON "05_monitoring"."61_evt_monitoring_metric_points" USING GIN (labels);

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_metrics" AS
SELECT
    m.id,
    m.org_id,
    m.key,
    m.kind_id,
    k.code AS kind_code,
    m.label_keys,
    m.histogram_buckets,
    m.max_cardinality,
    m.description,
    m.unit,
    m.created_at,
    m.updated_at
FROM "05_monitoring"."10_fct_monitoring_metrics" m
JOIN "05_monitoring"."02_dim_monitoring_metric_kinds" k ON k.id = m.kind_id;
COMMENT ON VIEW "05_monitoring"."v_monitoring_metrics" IS 'Read-model for metrics registry: resolves kind_code from dim.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_metrics";
DROP TABLE IF EXISTS "05_monitoring"."61_evt_monitoring_metric_points_p20260419";
DROP TABLE IF EXISTS "05_monitoring"."61_evt_monitoring_metric_points_p20260418";
DROP TABLE IF EXISTS "05_monitoring"."61_evt_monitoring_metric_points_p20260417";
DROP TABLE IF EXISTS "05_monitoring"."61_evt_monitoring_metric_points";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_metrics";
