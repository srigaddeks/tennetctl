-- ==========================================================
-- Migration: Create Table "01_dev_features"."01_schema_migration"
-- Generated: 2026-03-13 13:44:11
-- ==========================================================

CREATE TABLE IF NOT EXISTS "01_dev_features"."01_schema_migration" (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(255)  NOT NULL,
    sql_query       TEXT          NOT NULL,
    sql_text        TEXT          NOT NULL,
    status          VARCHAR(20)   NOT NULL DEFAULT 'pending',
    applied_at      TIMESTAMP     NULL,
    rolled_back_at  TIMESTAMP     NULL,
    execution_time  INT           NULL,
    error_message   TEXT          NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMP     NOT NULL DEFAULT NOW()
);

-- Index for quick status lookups
CREATE INDEX IF NOT EXISTS idx_01_schema_migration_status
    ON "01_dev_features"."01_schema_migration" (status);

-- Index for quick name lookups
CREATE INDEX IF NOT EXISTS idx_01_schema_migration_name
    ON "01_dev_features"."01_schema_migration" (name);