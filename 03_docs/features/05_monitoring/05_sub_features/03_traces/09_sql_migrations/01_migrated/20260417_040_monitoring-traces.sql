-- UP ====
-- evt_monitoring_spans — OTel-aligned spans, daily-partitioned on recorded_at.
-- duration_ns is a generated column derived from start/end unix nanos.

CREATE TABLE IF NOT EXISTS "05_monitoring"."62_evt_monitoring_spans" (
    trace_id             TEXT        NOT NULL,
    span_id              TEXT        NOT NULL,
    parent_span_id       TEXT        NULL,
    org_id               VARCHAR(36) NOT NULL,
    workspace_id         VARCHAR(36) NULL,
    resource_id          BIGINT      NOT NULL,
    name                 TEXT        NOT NULL,
    kind_id              SMALLINT    NOT NULL,
    status_id            SMALLINT    NOT NULL,
    status_message       TEXT        NULL,
    recorded_at          TIMESTAMP   NOT NULL,
    start_time_unix_nano BIGINT      NOT NULL,
    end_time_unix_nano   BIGINT      NOT NULL,
    duration_ns          BIGINT      GENERATED ALWAYS AS (end_time_unix_nano - start_time_unix_nano) STORED,
    attributes           JSONB       NOT NULL DEFAULT '{}'::jsonb,
    events               JSONB       NOT NULL DEFAULT '[]'::jsonb,
    links                JSONB       NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT pk_evt_monitoring_spans PRIMARY KEY (trace_id, span_id, recorded_at),
    CONSTRAINT fk_evt_monitoring_spans_kind     FOREIGN KEY (kind_id)     REFERENCES "05_monitoring"."03_dim_monitoring_span_kinds"(id),
    CONSTRAINT fk_evt_monitoring_spans_status   FOREIGN KEY (status_id)   REFERENCES "05_monitoring"."04_dim_monitoring_span_status"(id),
    CONSTRAINT fk_evt_monitoring_spans_resource FOREIGN KEY (resource_id) REFERENCES "05_monitoring"."11_fct_monitoring_resources"(id)
) PARTITION BY RANGE (recorded_at);

COMMENT ON TABLE "05_monitoring"."62_evt_monitoring_spans" IS 'Append-only OTel spans, daily-partitioned on recorded_at. duration_ns is generated-stored.';
COMMENT ON COLUMN "05_monitoring"."62_evt_monitoring_spans".duration_ns IS 'Generated: end_time_unix_nano - start_time_unix_nano.';

CREATE TABLE "05_monitoring"."62_evt_monitoring_spans_p20260417"
    PARTITION OF "05_monitoring"."62_evt_monitoring_spans"
    FOR VALUES FROM ('2026-04-17 00:00:00') TO ('2026-04-18 00:00:00');
CREATE TABLE "05_monitoring"."62_evt_monitoring_spans_p20260418"
    PARTITION OF "05_monitoring"."62_evt_monitoring_spans"
    FOR VALUES FROM ('2026-04-18 00:00:00') TO ('2026-04-19 00:00:00');
CREATE TABLE "05_monitoring"."62_evt_monitoring_spans_p20260419"
    PARTITION OF "05_monitoring"."62_evt_monitoring_spans"
    FOR VALUES FROM ('2026-04-19 00:00:00') TO ('2026-04-20 00:00:00');

CREATE INDEX idx_evt_monitoring_spans_trace_id   ON "05_monitoring"."62_evt_monitoring_spans" (trace_id);
CREATE INDEX idx_evt_monitoring_spans_org_rec    ON "05_monitoring"."62_evt_monitoring_spans" (org_id, recorded_at DESC);
CREATE INDEX idx_evt_monitoring_spans_parent     ON "05_monitoring"."62_evt_monitoring_spans" (parent_span_id) WHERE parent_span_id IS NOT NULL;
CREATE INDEX idx_evt_monitoring_spans_attrs_gin  ON "05_monitoring"."62_evt_monitoring_spans" USING GIN (attributes jsonb_path_ops);

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_spans" AS
SELECT
    s.trace_id,
    s.span_id,
    s.parent_span_id,
    s.org_id,
    s.workspace_id,
    s.resource_id,
    r.service_name,
    r.service_instance_id,
    r.service_version,
    s.name,
    s.kind_id,
    k.code AS kind_code,
    s.status_id,
    st.code AS status_code,
    s.status_message,
    s.recorded_at,
    s.start_time_unix_nano,
    s.end_time_unix_nano,
    s.duration_ns,
    s.attributes,
    s.events,
    s.links
FROM "05_monitoring"."62_evt_monitoring_spans" s
JOIN "05_monitoring"."03_dim_monitoring_span_kinds"  k  ON k.id  = s.kind_id
JOIN "05_monitoring"."04_dim_monitoring_span_status" st ON st.id = s.status_id
JOIN "05_monitoring"."11_fct_monitoring_resources"   r  ON r.id  = s.resource_id;
COMMENT ON VIEW "05_monitoring"."v_monitoring_spans" IS 'Read-model for spans: resolves kind_code/status_code/service_name.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_spans";
DROP TABLE IF EXISTS "05_monitoring"."62_evt_monitoring_spans_p20260419";
DROP TABLE IF EXISTS "05_monitoring"."62_evt_monitoring_spans_p20260418";
DROP TABLE IF EXISTS "05_monitoring"."62_evt_monitoring_spans_p20260417";
DROP TABLE IF EXISTS "05_monitoring"."62_evt_monitoring_spans";
