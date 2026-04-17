-- UP ====
-- Notify templates: Jinja2 templates with per-channel bodies.

CREATE TABLE IF NOT EXISTS "06_notify"."12_fct_notify_templates" (
    id              VARCHAR(36)  NOT NULL,
    org_id          VARCHAR(36)  NOT NULL,
    key             TEXT         NOT NULL,
    group_id        VARCHAR(36)  NOT NULL,
    subject         TEXT         NOT NULL,
    reply_to        TEXT         NULL,
    priority_id     SMALLINT     NOT NULL DEFAULT 2,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP    NULL,
    created_by      VARCHAR(36)  NOT NULL,
    updated_by      VARCHAR(36)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_notify_templates PRIMARY KEY (id),
    CONSTRAINT uq_fct_notify_templates_key UNIQUE (org_id, key),
    CONSTRAINT fk_fct_notify_templates_group
        FOREIGN KEY (group_id) REFERENCES "06_notify"."11_fct_notify_template_groups" (id),
    CONSTRAINT fk_fct_notify_templates_priority
        FOREIGN KEY (priority_id) REFERENCES "06_notify"."04_dim_notify_priorities" (id)
);
COMMENT ON TABLE  "06_notify"."12_fct_notify_templates" IS 'Notify templates. Subject is Jinja2; bodies live in dtl_notify_template_bodies per channel.';
COMMENT ON COLUMN "06_notify"."12_fct_notify_templates".key IS 'Stable human key per org — e.g. signup_welcome, password_reset.';
COMMENT ON COLUMN "06_notify"."12_fct_notify_templates".priority_id IS 'Default 2 = normal. critical(4) bypasses throttling.';

CREATE INDEX IF NOT EXISTS idx_fct_notify_templates_org
    ON "06_notify"."12_fct_notify_templates" (org_id)
    WHERE deleted_at IS NULL;

CREATE INDEX IF NOT EXISTS idx_fct_notify_templates_group
    ON "06_notify"."12_fct_notify_templates" (group_id)
    WHERE deleted_at IS NULL;

-- Per-channel body content (HTML + text + preheader)
CREATE TABLE IF NOT EXISTS "06_notify"."20_dtl_notify_template_bodies" (
    id          VARCHAR(36)  NOT NULL,
    template_id VARCHAR(36)  NOT NULL,
    channel_id  SMALLINT     NOT NULL,
    body_html   TEXT         NOT NULL,
    body_text   TEXT         NOT NULL DEFAULT '',
    preheader   TEXT         NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_notify_template_bodies PRIMARY KEY (id),
    CONSTRAINT uq_dtl_notify_template_bodies_tmpl_chan UNIQUE (template_id, channel_id),
    CONSTRAINT fk_dtl_notify_template_bodies_tmpl
        FOREIGN KEY (template_id) REFERENCES "06_notify"."12_fct_notify_templates" (id) ON DELETE CASCADE,
    CONSTRAINT fk_dtl_notify_template_bodies_channel
        FOREIGN KEY (channel_id) REFERENCES "06_notify"."01_dim_notify_channels" (id)
);
COMMENT ON TABLE  "06_notify"."20_dtl_notify_template_bodies" IS 'Per-channel Jinja2 body content for each template. One row per (template, channel).';
COMMENT ON COLUMN "06_notify"."20_dtl_notify_template_bodies".body_html IS 'Jinja2 HTML body. Required for email; optional for other channels.';
COMMENT ON COLUMN "06_notify"."20_dtl_notify_template_bodies".body_text IS 'Plain-text fallback. Defaults to empty string; should mirror HTML content.';

CREATE INDEX IF NOT EXISTS idx_dtl_notify_template_bodies_tmpl
    ON "06_notify"."20_dtl_notify_template_bodies" (template_id);

-- Main template view: joins group + category + priority, aggregates bodies
CREATE OR REPLACE VIEW "06_notify"."v_notify_templates" AS
SELECT
    t.id,
    t.org_id,
    t.key,
    t.group_id,
    g.key           AS group_key,
    g.category_id,
    g.category_code,
    g.category_label,
    t.subject,
    t.reply_to,
    t.priority_id,
    p.code          AS priority_code,
    p.label         AS priority_label,
    t.is_active,
    t.created_by,
    t.updated_by,
    t.created_at,
    t.updated_at,
    COALESCE(
        json_agg(
            json_build_object(
                'id',         b.id,
                'channel_id', b.channel_id,
                'body_html',  b.body_html,
                'body_text',  b.body_text,
                'preheader',  b.preheader
            ) ORDER BY b.channel_id
        ) FILTER (WHERE b.id IS NOT NULL),
        '[]'::json
    ) AS bodies
FROM "06_notify"."12_fct_notify_templates"          t
JOIN "06_notify"."v_notify_template_groups"          g ON g.id = t.group_id
JOIN "06_notify"."04_dim_notify_priorities"          p ON p.id = t.priority_id
LEFT JOIN "06_notify"."20_dtl_notify_template_bodies" b ON b.template_id = t.id
WHERE t.deleted_at IS NULL
GROUP BY
    t.id, t.org_id, t.key, t.group_id,
    g.key, g.category_id, g.category_code, g.category_label,
    t.subject, t.reply_to, t.priority_id,
    p.code, p.label,
    t.is_active, t.created_by, t.updated_by, t.created_at, t.updated_at;
COMMENT ON VIEW "06_notify"."v_notify_templates" IS 'Active templates with resolved group, category, priority, and aggregated per-channel bodies.';

-- DOWN ====
DROP VIEW  IF EXISTS "06_notify"."v_notify_templates";
DROP TABLE IF EXISTS "06_notify"."20_dtl_notify_template_bodies";
DROP TABLE IF EXISTS "06_notify"."12_fct_notify_templates";
