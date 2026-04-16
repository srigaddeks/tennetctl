-- ─────────────────────────────────────────────────────────────────────────────
-- SMTP CONFIGURATION TABLE
-- Stores admin-managed SMTP settings in the DB so they can be configured via UI
-- without requiring env var changes or server restarts.
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_notifications"."30_fct_smtp_config" (
    id             UUID         NOT NULL DEFAULT gen_random_uuid(),
    tenant_key     VARCHAR(100) NOT NULL DEFAULT 'default',
    host           VARCHAR(253) NOT NULL,
    port           INTEGER      NOT NULL DEFAULT 587,
    username       VARCHAR(200) NULL,
    password       TEXT         NULL,        -- stored as-is (no encryption for now; secrets in env for prod)
    from_email     VARCHAR(254) NOT NULL,
    from_name      VARCHAR(100) NOT NULL DEFAULT 'K-Control',
    use_tls        BOOLEAN      NOT NULL DEFAULT FALSE,
    start_tls      BOOLEAN      NOT NULL DEFAULT TRUE,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMP    NOT NULL DEFAULT NOW(),
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_30_fct_smtp_config PRIMARY KEY (id),
    CONSTRAINT uq_30_fct_smtp_config_tenant UNIQUE (tenant_key)
);

COMMENT ON TABLE "03_notifications"."30_fct_smtp_config" IS 'Admin-managed SMTP configuration per tenant. Takes precedence over environment variables.';
