-- UP ====
-- evt_monitoring_logs — OTel-aligned, daily-partitioned on recorded_at.
-- 3 daily partitions pre-created. TIMESTAMP (UTC) per project convention.
-- OTel top-level columns carve-out: severity/trace/span/scope are first-class,
-- free-form fan-out in `attributes` JSONB.

CREATE TABLE IF NOT EXISTS "05_monitoring"."60_evt_monitoring_logs" (
    id                        VARCHAR(36) NOT NULL,
    org_id                    VARCHAR(36) NOT NULL,
    workspace_id              VARCHAR(36) NULL,
    resource_id               BIGINT      NOT NULL,
    recorded_at               TIMESTAMP   NOT NULL,
    observed_at               TIMESTAMP   NOT NULL,
    severity_id               SMALLINT    NOT NULL,
    severity_text             TEXT        NULL,
    body                      TEXT        NOT NULL,
    trace_id                  TEXT        NULL,
    span_id                   TEXT        NULL,
    trace_flags               SMALLINT    NULL,
    scope_name                TEXT        NULL,
    scope_version             TEXT        NULL,
    attributes                JSONB       NOT NULL DEFAULT '{}'::jsonb,
    dropped_attributes_count  INT         NOT NULL DEFAULT 0,
    CONSTRAINT pk_evt_monitoring_logs PRIMARY KEY (id, recorded_at),
    CONSTRAINT fk_evt_monitoring_logs_severity    FOREIGN KEY (severity_id) REFERENCES "05_monitoring"."01_dim_monitoring_severity"(id),
    CONSTRAINT fk_evt_monitoring_logs_resource    FOREIGN KEY (resource_id) REFERENCES "05_monitoring"."11_fct_monitoring_resources"(id)
) PARTITION BY RANGE (recorded_at);

COMMENT ON TABLE  "05_monitoring"."60_evt_monitoring_logs" IS 'Append-only OTel log records, daily-partitioned on recorded_at. No updated_at, no deleted_at.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".id IS 'UUID v7.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".recorded_at IS 'Timestamp the event was recorded by the producer. Partition key.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".observed_at IS 'Timestamp the collector observed the event.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".severity_id IS 'OTLP SeverityNumber FK to dim_monitoring_severity.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".severity_text IS 'Raw severity text from producer (free-form).';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".trace_id IS 'OTel trace_id (32 hex chars). Nullable.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".span_id IS 'OTel span_id (16 hex chars). Nullable.';
COMMENT ON COLUMN "05_monitoring"."60_evt_monitoring_logs".attributes IS 'OTel LogRecord attributes. JSONB.';

CREATE TABLE "05_monitoring"."60_evt_monitoring_logs_p20260417"
    PARTITION OF "05_monitoring"."60_evt_monitoring_logs"
    FOR VALUES FROM ('2026-04-17 00:00:00') TO ('2026-04-18 00:00:00');
CREATE TABLE "05_monitoring"."60_evt_monitoring_logs_p20260418"
    PARTITION OF "05_monitoring"."60_evt_monitoring_logs"
    FOR VALUES FROM ('2026-04-18 00:00:00') TO ('2026-04-19 00:00:00');
CREATE TABLE "05_monitoring"."60_evt_monitoring_logs_p20260419"
    PARTITION OF "05_monitoring"."60_evt_monitoring_logs"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');

CREATE INDEX idx_evt_monitoring_logs_org_recorded  ON "05_monitoring"."60_evt_monitoring_logs" (org_id, recorded_at DESC);
CREATE INDEX idx_evt_monitoring_logs_trace_id      ON "05_monitoring"."60_evt_monitoring_logs" (trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_evt_monitoring_logs_resource      ON "05_monitoring"."60_evt_monitoring_logs" (resource_id, recorded_at DESC);
CREATE INDEX idx_evt_monitoring_logs_attrs_gin     ON "05_monitoring"."60_evt_monitoring_logs" USING GIN (attributes jsonb_path_ops);

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_logs" AS
SELECT
    l.id,
    l.org_id,
    l.workspace_id,
    l.resource_id,
    r.service_name,
    r.service_instance_id,
    r.service_version,
    l.recorded_at,
    l.observed_at,
    l.severity_id,
    s.code        AS severity_code,
    l.severity_text,
    l.body,
    l.trace_id,
    l.span_id,
    l.trace_flags,
    l.scope_name,
    l.scope_version,
    l.attributes,
    l.dropped_attributes_count
FROM "05_monitoring"."60_evt_monitoring_logs" l
JOIN "05_monitoring"."01_dim_monitoring_severity" s ON s.id = l.severity_id
JOIN "05_monitoring"."11_fct_monitoring_resources" r ON r.id = l.resource_id;
COMMENT ON VIEW "05_monitoring"."v_monitoring_logs" IS 'Read-model for logs: resolves severity code + service_name from dim + resource intern.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_logs";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_logs_p20260419";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_logs_p20260418";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_logs_p20260417";
DROP TABLE IF EXISTS "05_monitoring"."60_evt_monitoring_logs";
