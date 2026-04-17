-- UP ====
-- 13-07 Task 4 — Synthetic checks sub-feature + LISTEN/NOTIFY trigger on logs.

-- Synthetic check definition
CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_synthetic_checks" (
    id                VARCHAR(36) PRIMARY KEY,
    org_id            VARCHAR(36) NOT NULL,
    name              TEXT        NOT NULL,
    target_url        TEXT        NOT NULL,
    method            TEXT        NOT NULL DEFAULT 'GET',
    expected_status   SMALLINT    NOT NULL DEFAULT 200,
    timeout_ms        INT         NOT NULL DEFAULT 5000 CHECK (timeout_ms BETWEEN 100 AND 60000),
    interval_seconds  INT         NOT NULL DEFAULT 60   CHECK (interval_seconds >= 30),
    headers           JSONB       NOT NULL DEFAULT '{}'::jsonb,
    body              TEXT        NULL,
    assertions        JSONB       NOT NULL DEFAULT '[]'::jsonb,
    is_active         BOOLEAN     NOT NULL DEFAULT TRUE,
    deleted_at        TIMESTAMP   NULL,
    created_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_synthetic_method CHECK (method IN ('GET','POST','PUT','PATCH','DELETE','HEAD'))
);
COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_synthetic_checks" IS 'Configured HTTP synthetic checks. Runner executes them at interval_seconds and emits up/duration metrics.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_synthetic_checks".assertions IS 'Array of simple assertions, e.g. [{"op":"contains","field":"body","value":"ok"}]';

CREATE UNIQUE INDEX uq_synthetic_checks_org_name
    ON "05_monitoring"."10_fct_monitoring_synthetic_checks" (org_id, name)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_synthetic_checks_active
    ON "05_monitoring"."10_fct_monitoring_synthetic_checks" (is_active, deleted_at)
    WHERE deleted_at IS NULL;

-- Runtime state
CREATE TABLE IF NOT EXISTS "05_monitoring"."20_dtl_monitoring_synthetic_state" (
    check_id              VARCHAR(36) PRIMARY KEY REFERENCES "05_monitoring"."10_fct_monitoring_synthetic_checks"(id) ON DELETE CASCADE,
    consecutive_failures  INT         NOT NULL DEFAULT 0,
    last_ok_at            TIMESTAMP   NULL,
    last_fail_at          TIMESTAMP   NULL,
    last_run_at           TIMESTAMP   NULL,
    last_status_code      SMALLINT    NULL,
    last_duration_ms      INT         NULL,
    last_error            TEXT        NULL,
    updated_at            TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE "05_monitoring"."20_dtl_monitoring_synthetic_state" IS 'Runtime state per synthetic check — updated every run.';

-- Read view
CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_synthetic_checks" AS
SELECT
    c.id, c.org_id, c.name, c.target_url, c.method, c.expected_status,
    c.timeout_ms, c.interval_seconds, c.headers, c.body, c.assertions,
    c.is_active, c.deleted_at, c.created_at, c.updated_at,
    s.consecutive_failures, s.last_ok_at, s.last_fail_at, s.last_run_at,
    s.last_status_code, s.last_duration_ms, s.last_error,
    (c.deleted_at IS NOT NULL) AS is_deleted
  FROM "05_monitoring"."10_fct_monitoring_synthetic_checks" c
  LEFT JOIN "05_monitoring"."20_dtl_monitoring_synthetic_state" s
         ON s.check_id = c.id;
COMMENT ON VIEW "05_monitoring"."v_monitoring_synthetic_checks" IS 'Synthetic checks joined with runtime state.';

-- LISTEN/NOTIFY trigger on logs — fires on every INSERT to any partition.
-- Payload kept small: {id, recorded_at, org_id} (well under 3KB NOTIFY safe limit).
CREATE OR REPLACE FUNCTION "05_monitoring".monitoring_notify_logs()
RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify(
        'monitoring_logs_new',
        json_build_object(
            'id',          NEW.id,
            'recorded_at', NEW.recorded_at,
            'org_id',      NEW.org_id
        )::text
    );
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;
COMMENT ON FUNCTION "05_monitoring".monitoring_notify_logs() IS 'AFTER INSERT trigger on evt_monitoring_logs — publishes minimal payload to monitoring_logs_new channel.';

-- Trigger on parent partitioned table — PG13+ propagates to partitions.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_trigger
         WHERE tgname = 'trg_monitoring_logs_notify'
    ) THEN
        EXECUTE 'CREATE TRIGGER trg_monitoring_logs_notify
                 AFTER INSERT ON "05_monitoring"."60_evt_monitoring_logs"
                 FOR EACH ROW EXECUTE FUNCTION "05_monitoring".monitoring_notify_logs()';
    END IF;
END $$;

-- DOWN ====
DROP TRIGGER   IF EXISTS trg_monitoring_logs_notify ON "05_monitoring"."60_evt_monitoring_logs";
DROP FUNCTION  IF EXISTS "05_monitoring".monitoring_notify_logs();
DROP VIEW      IF EXISTS "05_monitoring"."v_monitoring_synthetic_checks";
DROP TABLE     IF EXISTS "05_monitoring"."20_dtl_monitoring_synthetic_state";
DROP TABLE     IF EXISTS "05_monitoring"."10_fct_monitoring_synthetic_checks";
