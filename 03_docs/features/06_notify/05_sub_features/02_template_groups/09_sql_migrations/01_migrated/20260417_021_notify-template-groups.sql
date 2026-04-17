-- UP ====
-- Notify template groups: groups templates by category + SMTP config.

CREATE TABLE IF NOT EXISTS "06_notify"."11_fct_notify_template_groups" (
    id              VARCHAR(36)  NOT NULL,
    org_id          VARCHAR(36)  NOT NULL,
    key             TEXT         NOT NULL,
    label           TEXT         NOT NULL,
    category_id     SMALLINT     NOT NULL,
    smtp_config_id  VARCHAR(36)  NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP    NULL,
    created_by      VARCHAR(36)  NOT NULL,
    updated_by      VARCHAR(36)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_notify_template_groups PRIMARY KEY (id),
    CONSTRAINT uq_fct_notify_template_groups_key UNIQUE (org_id, key),
    CONSTRAINT fk_fct_notify_template_groups_category
        FOREIGN KEY (category_id) REFERENCES "06_notify"."02_dim_notify_categories" (id),
    CONSTRAINT fk_fct_notify_template_groups_smtp
        FOREIGN KEY (smtp_config_id) REFERENCES "06_notify"."10_fct_notify_smtp_configs" (id)
);
COMMENT ON TABLE  "06_notify"."11_fct_notify_template_groups" IS 'Template groups: logical buckets that share a category and optional SMTP config. Critical group => multi-channel fan-out.';
COMMENT ON COLUMN "06_notify"."11_fct_notify_template_groups".category_id IS 'FK to dim_notify_categories: transactional(1), critical(2), marketing(3), digest(4).';
COMMENT ON COLUMN "06_notify"."11_fct_notify_template_groups".smtp_config_id IS 'Optional: inherit SMTP config for all templates in this group. Null = system default or per-template override.';

CREATE INDEX IF NOT EXISTS idx_fct_notify_template_groups_org
    ON "06_notify"."11_fct_notify_template_groups" (org_id)
    WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW "06_notify"."v_notify_template_groups" AS
SELECT
    g.id,
    g.org_id,
    g.key,
    g.label,
    g.category_id,
    c.code  AS category_code,
    c.label AS category_label,
    g.smtp_config_id,
    s.key   AS smtp_config_key,
    g.is_active,
    g.created_by,
    g.updated_by,
    g.created_at,
    g.updated_at
FROM "06_notify"."11_fct_notify_template_groups" g
JOIN "06_notify"."02_dim_notify_categories"       c ON c.id = g.category_id
LEFT JOIN "06_notify"."v_notify_smtp_configs"     s ON s.id = g.smtp_config_id
WHERE g.deleted_at IS NULL;
COMMENT ON VIEW "06_notify"."v_notify_template_groups" IS 'Active template groups with resolved category and SMTP config labels.';

-- DOWN ====
DROP VIEW  IF EXISTS "06_notify"."v_notify_template_groups";
DROP TABLE IF EXISTS "06_notify"."11_fct_notify_template_groups";
