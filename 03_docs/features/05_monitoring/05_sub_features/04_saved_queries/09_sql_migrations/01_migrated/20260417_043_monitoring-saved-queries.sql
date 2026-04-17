-- UP ====
-- fct_monitoring_saved_queries — saved/shared DSL queries per-org, per-owner.
-- Carve-out: fct_* with JSONB for the DSL body. Saved queries are a catalog-
-- style object (small, rarely written, frequently read); the DSL is JSON by
-- design so it travels through API + UI + alerts unchanged. JSONB here is
-- acceptable per the monitoring-metrics precedent (registry-style fct_*).

CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_saved_queries" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    owner_user_id   VARCHAR(36) NOT NULL,
    name            TEXT        NOT NULL,
    description     TEXT        NULL,
    target          TEXT        NOT NULL,
    dsl             JSONB       NOT NULL,
    shared          BOOLEAN     NOT NULL DEFAULT FALSE,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP   NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_saved_queries PRIMARY KEY (id),
    CONSTRAINT chk_fct_monitoring_saved_queries_target
        CHECK (target IN ('logs','metrics','traces')),
    CONSTRAINT chk_fct_monitoring_saved_queries_name_nonempty
        CHECK (length(name) >= 1)
);

COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_saved_queries" IS 'Saved monitoring queries (DSL). Per-org, per-owner. shared=true allows same-org visibility.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".id IS 'UUID v7.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".org_id IS 'Scope owner.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".owner_user_id IS 'User who created the saved query.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".name IS 'Display name (unique per owner+org).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".description IS 'Free-form description.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".target IS 'Query target: logs | metrics | traces.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".dsl IS 'DSL body — stored as JSONB.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".shared IS 'When true, visible to all users in the same org.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".is_active IS 'Soft-disable flag.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".deleted_at IS 'Soft-delete marker. NULL = live.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".created_at IS 'Creation timestamp (UTC).';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_saved_queries".updated_at IS 'Last-update timestamp (UTC).';

CREATE UNIQUE INDEX uq_fct_monitoring_saved_queries_owner_name
    ON "05_monitoring"."10_fct_monitoring_saved_queries" (org_id, owner_user_id, name)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_fct_monitoring_saved_queries_org
    ON "05_monitoring"."10_fct_monitoring_saved_queries" (org_id)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_fct_monitoring_saved_queries_shared
    ON "05_monitoring"."10_fct_monitoring_saved_queries" (org_id)
    WHERE deleted_at IS NULL AND shared = TRUE;

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_saved_queries" AS
SELECT
    id,
    org_id,
    owner_user_id,
    name,
    description,
    target,
    dsl,
    shared,
    is_active,
    (deleted_at IS NOT NULL) AS is_deleted,
    deleted_at,
    created_at,
    updated_at
FROM "05_monitoring"."10_fct_monitoring_saved_queries";

COMMENT ON VIEW "05_monitoring"."v_monitoring_saved_queries" IS 'Read-model for saved monitoring queries. Derives is_deleted; callers filter deleted_at IS NULL as needed.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_saved_queries";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_saved_queries_shared";
DROP INDEX IF EXISTS "05_monitoring"."idx_fct_monitoring_saved_queries_org";
DROP INDEX IF EXISTS "05_monitoring"."uq_fct_monitoring_saved_queries_owner_name";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_saved_queries";
