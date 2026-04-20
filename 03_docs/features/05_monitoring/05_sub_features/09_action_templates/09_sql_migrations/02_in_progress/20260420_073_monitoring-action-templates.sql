-- UP ====
-- 40-02 Task 1 — Action templates: webhooks + email + Slack integrations
--
-- Introduces reusable action templates: templates define kind (webhook|email|slack),
-- body template (Jinja2), headers, signing secret, and retry policy. Alert rules and
-- escalation steps reference templates by id. Renderer + dispatchers handle rendering
-- and delivery. Signing secret stored in Vault, referenced by vault ref.

-- ── Action kind dimension ───────────────────────────────────────────────────────
-- Seeded values: webhook=1, email=2, slack=3, ms_teams=4
CREATE TABLE "05_monitoring"."03_dim_monitoring_action_kind" (
    id              SMALLINT    NOT NULL,
    code            TEXT        NOT NULL UNIQUE,
    label           TEXT        NOT NULL,
    description     TEXT        NULL,
    deprecated_at   TIMESTAMP   NULL,
    CONSTRAINT pk_dim_monitoring_action_kind PRIMARY KEY (id)
);
COMMENT ON TABLE  "05_monitoring"."03_dim_monitoring_action_kind" IS 'Action delivery kind enum: webhook, email, slack, ms_teams. Seeded, never mutated.';
COMMENT ON COLUMN "05_monitoring"."03_dim_monitoring_action_kind".id IS 'Stable PK — never renumbered.';
COMMENT ON COLUMN "05_monitoring"."03_dim_monitoring_action_kind".code IS 'Machine code (webhook|email|slack|ms_teams).';
COMMENT ON COLUMN "05_monitoring"."03_dim_monitoring_action_kind".label IS 'Display label.';
COMMENT ON COLUMN "05_monitoring"."03_dim_monitoring_action_kind".description IS 'Kind behavior description.';
COMMENT ON COLUMN "05_monitoring"."03_dim_monitoring_action_kind".deprecated_at IS 'Soft-deprecation marker — never DELETE rows.';

-- ── Action templates ───────────────────────────────────────────────────────────
CREATE TABLE "05_monitoring"."14_fct_monitoring_action_templates" (
    id                              VARCHAR(36)   PRIMARY KEY,
    org_id                          UUID          NOT NULL,
    name                            TEXT          NOT NULL,
    description                     TEXT          NULL,
    kind_id                         SMALLINT      NOT NULL
                                                  REFERENCES "05_monitoring"."03_dim_monitoring_action_kind"(id),
    target_url                      TEXT          NULL,
    target_address                  TEXT          NULL,
    body_template                   TEXT          NOT NULL,
    headers_template                JSONB         NOT NULL DEFAULT '{}'::jsonb,
    signing_secret_vault_ref        TEXT          NULL,
    retry_policy                    JSONB         NOT NULL DEFAULT '{"max_attempts":3,"base_seconds":5,"max_seconds":300}'::jsonb,
    is_active                       BOOLEAN       NOT NULL DEFAULT TRUE,
    deleted_at                      TIMESTAMP     NULL,
    created_at                      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_monitoring_action_templates_webhook_has_url
        CHECK (kind_id NOT IN (1, 4) OR target_url IS NOT NULL),
    CONSTRAINT chk_monitoring_action_templates_email_has_address
        CHECK (kind_id <> 2 OR target_address IS NOT NULL)
);
COMMENT ON TABLE  "05_monitoring"."14_fct_monitoring_action_templates" IS 'Reusable action templates for webhook/email/Slack delivery. Body template uses Jinja2 (sandboxed). Signing secret ref points to vault secret.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".id IS 'UUID v7 primary key.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".org_id IS 'Owning org.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".name IS 'Human-readable template name.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".description IS 'Optional long-form description.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".kind_id IS 'FK to dim_monitoring_action_kind.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".target_url IS 'Webhook URL or Slack incoming webhook URL. Required for webhook/slack/ms_teams kinds.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".target_address IS 'Email address (or list). Required for email kind.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".body_template IS 'Jinja2 template string. Rendered with alert + rule context. For email, can use {% block subject %} / {% block text %} / {% block html %}.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".headers_template IS 'Optional JSONB object of headers (e.g., {"Authorization": "Bearer ..."}). Merged with defaults.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".signing_secret_vault_ref IS 'Vault secret reference (e.g., "vault://secret/team/webhook-secret"). Resolved at dispatch time for HMAC signing. Can be NULL if no signing required.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".retry_policy IS 'JSONB retry config: {max_attempts, base_seconds, max_seconds}. Exponential backoff applied to failed deliveries.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".is_active IS 'Soft toggle. Only active templates can be referenced by rules/escalations.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".deleted_at IS 'Soft-delete marker.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".created_at IS 'Creation timestamp.';
COMMENT ON COLUMN "05_monitoring"."14_fct_monitoring_action_templates".updated_at IS 'Last-updated timestamp.';

CREATE UNIQUE INDEX uq_monitoring_action_templates_org_name
    ON "05_monitoring"."14_fct_monitoring_action_templates" (org_id, name)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_monitoring_action_templates_org_active
    ON "05_monitoring"."14_fct_monitoring_action_templates" (org_id, is_active)
    WHERE deleted_at IS NULL;

-- ── Extend alert rules with action_template_ids ─────────────────────────────────
ALTER TABLE "05_monitoring"."12_fct_monitoring_alert_rules"
    ADD COLUMN IF NOT EXISTS action_template_ids UUID[] NOT NULL DEFAULT '{}';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_alert_rules".action_template_ids IS 'Array of action template UUIDs to fire on rule transitions (firing/resolved).';

-- ── Extend escalation step kind dimension ─────────────────────────────────────
-- The dim table is created in 071; we add the notify_action kind here if not already present
INSERT INTO "05_monitoring"."02_dim_escalation_step_kind" (id, code, label, description)
    VALUES (6, 'notify_action', 'Notify Action', 'Dispatch a named action template (webhook/email/Slack).')
    ON CONFLICT (id) DO NOTHING;

-- ── View for action templates ───────────────────────────────────────────────────
CREATE VIEW "05_monitoring".v_monitoring_action_templates AS
SELECT t.id, t.org_id, t.name, t.description,
       t.kind_id, k.code AS kind_code, k.label AS kind_label,
       t.target_url, t.target_address, t.body_template, t.headers_template,
       t.signing_secret_vault_ref, t.retry_policy, t.is_active,
       t.deleted_at, t.created_at, t.updated_at,
       (t.deleted_at IS NOT NULL) AS is_deleted,
       -- 24h success rate (derived from evt_monitoring_action_deliveries)
       COALESCE(ROUND(
           100.0 * (SELECT COUNT(*) FROM "05_monitoring"."65_evt_monitoring_action_deliveries"
                     WHERE template_id = t.id
                     AND started_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                     AND succeeded_at IS NOT NULL)
           / NULLIF(
               (SELECT COUNT(*) FROM "05_monitoring"."65_evt_monitoring_action_deliveries"
                WHERE template_id = t.id
                AND started_at >= CURRENT_TIMESTAMP - INTERVAL '24 hours'),
               0)
       , 2), 0) AS success_rate_24h,
       (SELECT MAX(completed_at) FROM "05_monitoring"."65_evt_monitoring_action_deliveries"
        WHERE template_id = t.id AND succeeded_at IS NOT NULL) AS last_delivered_at
  FROM "05_monitoring"."14_fct_monitoring_action_templates" t
  JOIN "05_monitoring"."03_dim_monitoring_action_kind" k ON k.id = t.kind_id
 WHERE t.deleted_at IS NULL;
COMMENT ON VIEW "05_monitoring".v_monitoring_action_templates IS 'Active action templates with kind label and 24h success rate.';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring".v_monitoring_action_templates;
ALTER TABLE "05_monitoring"."12_fct_monitoring_alert_rules"
    DROP COLUMN IF EXISTS action_template_ids;
DELETE FROM "05_monitoring"."02_dim_escalation_step_kind" WHERE id = 6;
DROP TABLE IF EXISTS "05_monitoring"."14_fct_monitoring_action_templates";
DROP TABLE IF EXISTS "05_monitoring"."03_dim_monitoring_action_kind";
