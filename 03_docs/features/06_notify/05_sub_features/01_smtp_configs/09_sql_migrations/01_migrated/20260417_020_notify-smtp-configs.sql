-- UP ====
-- Notify SMTP configs: one config per sender identity, credentials stored in vault.

CREATE TABLE IF NOT EXISTS "06_notify"."10_fct_notify_smtp_configs" (
    id              VARCHAR(36)  NOT NULL,
    org_id          VARCHAR(36)  NOT NULL,
    key             TEXT         NOT NULL,
    label           TEXT         NOT NULL,
    host            TEXT         NOT NULL,
    port            SMALLINT     NOT NULL DEFAULT 587,
    tls             BOOLEAN      NOT NULL DEFAULT TRUE,
    username        TEXT         NOT NULL,
    auth_vault_key  TEXT         NOT NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP    NULL,
    created_by      VARCHAR(36)  NOT NULL,
    updated_by      VARCHAR(36)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_notify_smtp_configs PRIMARY KEY (id),
    CONSTRAINT uq_fct_notify_smtp_configs_key UNIQUE (org_id, key)
);
COMMENT ON TABLE  "06_notify"."10_fct_notify_smtp_configs" IS 'SMTP sender identities. auth_vault_key references vault secret holding SMTP password.';
COMMENT ON COLUMN "06_notify"."10_fct_notify_smtp_configs".auth_vault_key IS 'Key into vault secrets for the SMTP password. Never store plaintext here.';
COMMENT ON COLUMN "06_notify"."10_fct_notify_smtp_configs".key IS 'Stable human key per org — e.g. transactional, marketing.';

CREATE INDEX IF NOT EXISTS idx_fct_notify_smtp_configs_org
    ON "06_notify"."10_fct_notify_smtp_configs" (org_id)
    WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW "06_notify"."v_notify_smtp_configs" AS
SELECT
    id,
    org_id,
    key,
    label,
    host,
    port,
    tls,
    username,
    auth_vault_key,
    is_active,
    created_by,
    updated_by,
    created_at,
    updated_at
FROM "06_notify"."10_fct_notify_smtp_configs"
WHERE deleted_at IS NULL;
COMMENT ON VIEW "06_notify"."v_notify_smtp_configs" IS 'Active SMTP configs (excludes soft-deleted). Read path for all queries.';

-- DOWN ====
DROP VIEW  IF EXISTS "06_notify"."v_notify_smtp_configs";
DROP TABLE IF EXISTS "06_notify"."10_fct_notify_smtp_configs";
