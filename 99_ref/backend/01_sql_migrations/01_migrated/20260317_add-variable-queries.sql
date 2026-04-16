-- ============================================================================
-- Custom Variable Queries for Notification Templates
-- ============================================================================
-- Allows admins to define SQL queries that resolve to template variables
-- at notification dispatch time. Each query accepts bind parameters
-- (user_id mandatory, plus optional context IDs) and returns columns
-- that become {{ custom.<query_code>.<column> }} template variables.
-- ============================================================================

-- 31_fct_variable_queries: User-defined SQL queries for custom template variables
CREATE TABLE IF NOT EXISTS "03_notifications"."31_fct_variable_queries" (
    id                UUID         NOT NULL,
    tenant_key        VARCHAR(50)  NOT NULL,
    code              VARCHAR(100) NOT NULL,
    name              VARCHAR(200) NOT NULL,
    description       TEXT,
    sql_template      TEXT         NOT NULL,
    bind_params       JSONB        NOT NULL DEFAULT '[]'::jsonb,
    result_columns    JSONB        NOT NULL DEFAULT '[]'::jsonb,
    timeout_ms        INTEGER      NOT NULL DEFAULT 3000,
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,
    is_deleted        BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by        UUID,
    CONSTRAINT pk_31_fct_variable_queries      PRIMARY KEY (id),
    CONSTRAINT uq_31_fct_variable_queries_code UNIQUE (tenant_key, code),
    CONSTRAINT ck_31_fct_variable_queries_timeout
        CHECK (timeout_ms >= 100 AND timeout_ms <= 10000),
    CONSTRAINT ck_31_fct_variable_queries_code_fmt
        CHECK (code ~ '^[a-z][a-z0-9_]*$')
);

CREATE INDEX IF NOT EXISTS idx_31_fct_variable_queries_tenant
    ON "03_notifications"."31_fct_variable_queries" (tenant_key)
    WHERE is_active = TRUE AND is_deleted = FALSE;

-- ── Extend 08_dim_template_variable_keys ──────────────────────────────────

-- Add query_id FK column (NULL for built-in variables, set for custom query vars)
ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    ADD COLUMN IF NOT EXISTS query_id UUID;

-- Drop old CHECK constraint and re-add with 'custom_query' included
ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    DROP CONSTRAINT IF EXISTS ck_08_dim_template_variable_keys_source;

ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    ADD CONSTRAINT ck_08_dim_template_variable_keys_source
    CHECK (resolution_source IN (
        'audit_property', 'user_property', 'actor_property',
        'user_group', 'tenant', 'org', 'workspace',
        'settings', 'computed', 'custom_query'
    ));

-- FK from variable key → query definition
ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    ADD CONSTRAINT fk_08_dim_variable_keys_query
    FOREIGN KEY (query_id)
    REFERENCES "03_notifications"."31_fct_variable_queries" (id)
    ON DELETE SET NULL;

-- Index for looking up variable keys by query_id
CREATE INDEX IF NOT EXISTS idx_08_dim_variable_keys_query_id
    ON "03_notifications"."08_dim_template_variable_keys" (query_id)
    WHERE query_id IS NOT NULL;
