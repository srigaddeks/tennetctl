-- UP ====
-- Monitoring feature bootstrap: schema + 4 dim tables + fct_monitoring_resources.
-- Resources table lives here so downstream event-table migrations (038-040) can FK it.
-- Rollup tables are added in 041.
-- All dim IDs are SMALLINT plain PKs (not IDENTITY) because statically seeded from YAML.

CREATE SCHEMA IF NOT EXISTS "05_monitoring";
COMMENT ON SCHEMA "05_monitoring" IS 'Self-hosted observability — OTel-aligned logs, metrics, spans. Postgres-backed with ClickHouse-swappable storage seam. Replaces Prometheus/Loki/Tempo.';

-- Severity (OTLP 8 levels; ids are the OTLP numeric codes themselves)
CREATE TABLE IF NOT EXISTS "05_monitoring"."01_dim_monitoring_severity" (
    id            SMALLINT  NOT NULL,
    code          TEXT      NOT NULL,
    label         TEXT      NOT NULL,
    description   TEXT      NOT NULL,
    deprecated_at TIMESTAMP NULL,
    CONSTRAINT pk_dim_monitoring_severity PRIMARY KEY (id),
    CONSTRAINT uq_dim_monitoring_severity_code UNIQUE (code)
);
COMMENT ON TABLE  "05_monitoring"."01_dim_monitoring_severity" IS 'OTLP severity levels. IDs match OTLP SeverityNumber (unspecified=0, trace=1, debug=5, info=9, info2=10, warn=13, error=17, fatal=21).';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_severity".id IS 'OTLP SeverityNumber. Permanent.';
COMMENT ON COLUMN "05_monitoring"."01_dim_monitoring_severity".code IS 'Lowercase code: trace|debug|info|warn|error|fatal.';

-- Metric kinds (counter / gauge / histogram)
CREATE TABLE IF NOT EXISTS "05_monitoring"."02_dim_monitoring_metric_kinds" (
    id            SMALLINT  NOT NULL,
    code          TEXT      NOT NULL,
    label         TEXT      NOT NULL,
    description   TEXT      NOT NULL,
    deprecated_at TIMESTAMP NULL,
    CONSTRAINT pk_dim_monitoring_metric_kinds PRIMARY KEY (id),
    CONSTRAINT uq_dim_monitoring_metric_kinds_code UNIQUE (code)
);
COMMENT ON TABLE  "05_monitoring"."02_dim_monitoring_metric_kinds" IS 'Metric kind enum: counter (monotonic), gauge (mutable state), histogram (bucketed distribution).';

-- Span kinds (OTLP 6 values)
CREATE TABLE IF NOT EXISTS "05_monitoring"."03_dim_monitoring_span_kinds" (
    id            SMALLINT  NOT NULL,
    code          TEXT      NOT NULL,
    label         TEXT      NOT NULL,
    description   TEXT      NOT NULL,
    deprecated_at TIMESTAMP NULL,
    CONSTRAINT pk_dim_monitoring_span_kinds PRIMARY KEY (id),
    CONSTRAINT uq_dim_monitoring_span_kinds_code UNIQUE (code)
);
COMMENT ON TABLE  "05_monitoring"."03_dim_monitoring_span_kinds" IS 'OTLP SpanKind enum: unspecified|internal|server|client|producer|consumer. IDs match the OTLP enum values.';

-- Span status (OTLP StatusCode: unset / ok / error)
CREATE TABLE IF NOT EXISTS "05_monitoring"."04_dim_monitoring_span_status" (
    id            SMALLINT  NOT NULL,
    code          TEXT      NOT NULL,
    label         TEXT      NOT NULL,
    description   TEXT      NOT NULL,
    deprecated_at TIMESTAMP NULL,
    CONSTRAINT pk_dim_monitoring_span_status PRIMARY KEY (id),
    CONSTRAINT uq_dim_monitoring_span_status_code UNIQUE (code)
);
COMMENT ON TABLE  "05_monitoring"."04_dim_monitoring_span_status" IS 'OTLP StatusCode enum: unset|ok|error.';

-- Resources (service intern table — hashed identity)
-- BIGINT IDENTITY PK: registry row referenced by every evt_monitoring_* row; carve-out per Phase 13 STATE.md decisions.
CREATE TABLE IF NOT EXISTS "05_monitoring"."11_fct_monitoring_resources" (
    id                  BIGINT      GENERATED ALWAYS AS IDENTITY,
    org_id              VARCHAR(36) NOT NULL,
    resource_hash       BYTEA       NOT NULL,
    service_name        TEXT        NOT NULL,
    service_instance_id TEXT        NULL,
    service_version     TEXT        NULL,
    attributes          JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_resources PRIMARY KEY (id),
    CONSTRAINT uq_fct_monitoring_resources_org_hash UNIQUE (org_id, resource_hash)
);
COMMENT ON TABLE  "05_monitoring"."11_fct_monitoring_resources" IS 'Interned OTel resource identities (service_name + instance + version + attributes). Hashed for idempotent upsert. Carve-out: registry table, no EAV pivot, no is_test/created_by/updated_by (machine-emitted).';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_resources".id IS 'BIGINT IDENTITY — FK target on evt_monitoring_*. 8 bytes vs 16 for UUID; critical at billions of rows/day.';
COMMENT ON COLUMN "05_monitoring"."11_fct_monitoring_resources".resource_hash IS 'SHA-256 of canonical_json(service_name, instance_id, version, sorted(attributes)). 32 bytes.';

-- DOWN ====
DROP TABLE IF EXISTS "05_monitoring"."11_fct_monitoring_resources";
DROP TABLE IF EXISTS "05_monitoring"."04_dim_monitoring_span_status";
DROP TABLE IF EXISTS "05_monitoring"."03_dim_monitoring_span_kinds";
DROP TABLE IF EXISTS "05_monitoring"."02_dim_monitoring_metric_kinds";
DROP TABLE IF EXISTS "05_monitoring"."01_dim_monitoring_severity";
DROP SCHEMA IF EXISTS "05_monitoring";
