-- Migration 028: notify campaigns + campaign_id on deliveries
--
-- Campaigns allow sending a template to a filtered audience of users on a
-- schedule. The runner polls for scheduled campaigns, resolves the audience,
-- and creates deliveries with throttling.
--
-- Status lifecycle: draft → scheduled → running → completed | failed | cancelled
-- Paused is supported for future throttle-hold; not exposed in v0.1 runner.
--
-- audience_query JSONB DSL:
--   {}                                          → all active org users
--   {"account_type_codes": ["email_password"]}  → filter by account type
--
-- Depends on: 06_notify schema (019), templates (022), channels/priorities (019)

-- UP ====

-- ── Campaign status dim ──────────────────────────────────────────────────────

CREATE TABLE "06_notify"."05_dim_notify_campaign_statuses" (
    id            SMALLINT    NOT NULL,
    code          TEXT        NOT NULL,
    label         TEXT        NOT NULL,
    description   TEXT        NOT NULL,
    deprecated_at TIMESTAMP   NULL,
    CONSTRAINT pk_dim_notify_campaign_statuses PRIMARY KEY (id),
    CONSTRAINT uq_dim_notify_campaign_statuses_code UNIQUE (code)
);

COMMENT ON TABLE  "06_notify"."05_dim_notify_campaign_statuses" IS
    'Campaign lifecycle states. draft → scheduled → running → completed | failed | cancelled.';
COMMENT ON COLUMN "06_notify"."05_dim_notify_campaign_statuses".id IS
    'Permanent SMALLINT PK — never renumber.';
COMMENT ON COLUMN "06_notify"."05_dim_notify_campaign_statuses".code IS
    'Stable code: draft | scheduled | running | paused | completed | cancelled | failed.';

-- ── Campaigns ────────────────────────────────────────────────────────────────

CREATE TABLE "06_notify"."18_fct_notify_campaigns" (
    id                  VARCHAR(36)  NOT NULL,
    org_id              VARCHAR(36)  NOT NULL,
    name                TEXT         NOT NULL,
    template_id         VARCHAR(36)  NOT NULL,
    channel_id          SMALLINT     NOT NULL,
    audience_query      JSONB        NOT NULL DEFAULT '{}',
    scheduled_at        TIMESTAMP,
    throttle_per_minute INT          NOT NULL DEFAULT 60,
    status_id           SMALLINT     NOT NULL DEFAULT 1,
    deleted_at          TIMESTAMP,
    created_by          VARCHAR(36)  NOT NULL,
    updated_by          VARCHAR(36)  NOT NULL,
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_campaigns PRIMARY KEY (id),
    CONSTRAINT fk_notify_campaigns_template FOREIGN KEY (template_id)
        REFERENCES "06_notify"."12_fct_notify_templates"(id),
    CONSTRAINT fk_notify_campaigns_channel FOREIGN KEY (channel_id)
        REFERENCES "06_notify"."01_dim_notify_channels"(id),
    CONSTRAINT fk_notify_campaigns_status FOREIGN KEY (status_id)
        REFERENCES "06_notify"."05_dim_notify_campaign_statuses"(id),
    CONSTRAINT chk_notify_campaigns_throttle CHECK (throttle_per_minute BETWEEN 1 AND 10000)
);

COMMENT ON TABLE  "06_notify"."18_fct_notify_campaigns" IS
    'Campaign records. Runner picks up rows with status=scheduled and scheduled_at <= NOW().';
COMMENT ON COLUMN "06_notify"."18_fct_notify_campaigns".org_id IS
    'Organisation scope — campaigns are per-org.';
COMMENT ON COLUMN "06_notify"."18_fct_notify_campaigns".channel_id IS
    'Target channel. Critical category templates override this and fan out to all channels.';
COMMENT ON COLUMN "06_notify"."18_fct_notify_campaigns".audience_query IS
    'Filter DSL: {} = all org users. {"account_type_codes": [...]} = filter by account type.';
COMMENT ON COLUMN "06_notify"."18_fct_notify_campaigns".scheduled_at IS
    'When to run. NULL = not yet scheduled. Runner picks up when status=scheduled AND scheduled_at <= NOW().';
COMMENT ON COLUMN "06_notify"."18_fct_notify_campaigns".throttle_per_minute IS
    'Max deliveries created per minute. Default 60. Range 1–10000.';
COMMENT ON COLUMN "06_notify"."18_fct_notify_campaigns".status_id IS
    'FK to 05_dim_notify_campaign_statuses. Default draft(1).';

CREATE INDEX idx_notify_campaigns_org
    ON "06_notify"."18_fct_notify_campaigns" (org_id)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_notify_campaigns_scheduled
    ON "06_notify"."18_fct_notify_campaigns" (scheduled_at, status_id)
    WHERE deleted_at IS NULL;

-- ── Add campaign_id to deliveries ─────────────────────────────────────────────

ALTER TABLE "06_notify"."15_fct_notify_deliveries"
    ADD COLUMN campaign_id VARCHAR(36);

COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".campaign_id IS
    'FK-ish to fct_notify_campaigns.id. NULL for subscription-triggered and transactional deliveries. Not a DB FK to avoid cross-plan dependency ordering.';

CREATE INDEX idx_notify_deliveries_campaign
    ON "06_notify"."15_fct_notify_deliveries" (campaign_id)
    WHERE campaign_id IS NOT NULL;

-- Partial unique index for idempotent campaign delivery creation.
-- Prevents double-send if runner restarts mid-campaign.
CREATE UNIQUE INDEX uq_notify_deliveries_campaign_user_channel
    ON "06_notify"."15_fct_notify_deliveries" (campaign_id, recipient_user_id, channel_id)
    WHERE campaign_id IS NOT NULL;

-- ── Recreate v_notify_deliveries with campaign_id ──────────────────────────────

DROP VIEW IF EXISTS "06_notify"."v_notify_deliveries";

CREATE VIEW "06_notify"."v_notify_deliveries" AS
SELECT
    d.id, d.org_id, d.subscription_id, d.campaign_id, d.template_id,
    d.recipient_user_id,
    d.channel_id, ch.code AS channel_code, ch.label AS channel_label,
    d.priority_id, pr.code AS priority_code, pr.label AS priority_label,
    d.status_id, st.code AS status_code, st.label AS status_label,
    d.resolved_variables, d.audit_outbox_id,
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels" ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses" st ON st.id = d.status_id;

COMMENT ON VIEW "06_notify"."v_notify_deliveries" IS
    'Read path for deliveries: joins channel/priority/status dims. Includes campaign_id.';

-- ── Campaign view ────────────────────────────────────────────────────────────

CREATE VIEW "06_notify"."v_notify_campaigns" AS
SELECT
    c.id, c.org_id, c.name, c.template_id, c.channel_id,
    ch.code  AS channel_code,
    ch.label AS channel_label,
    c.audience_query, c.scheduled_at, c.throttle_per_minute,
    c.status_id, cs.code AS status_code, cs.label AS status_label,
    c.deleted_at, c.created_by, c.updated_by, c.created_at, c.updated_at
FROM "06_notify"."18_fct_notify_campaigns" c
JOIN "06_notify"."01_dim_notify_channels"           ch ON ch.id = c.channel_id
JOIN "06_notify"."05_dim_notify_campaign_statuses"  cs ON cs.id = c.status_id
WHERE c.deleted_at IS NULL;

COMMENT ON VIEW "06_notify"."v_notify_campaigns" IS
    'Read path for campaigns: joins channel and status dims. Excludes soft-deleted rows.';

-- DOWN ====

DROP VIEW  IF EXISTS "06_notify"."v_notify_campaigns";
DROP VIEW  IF EXISTS "06_notify"."v_notify_deliveries";

-- Restore v_notify_deliveries without campaign_id
CREATE VIEW "06_notify"."v_notify_deliveries" AS
SELECT
    d.id, d.org_id, d.subscription_id, d.template_id,
    d.recipient_user_id,
    d.channel_id, ch.code AS channel_code, ch.label AS channel_label,
    d.priority_id, pr.code AS priority_code, pr.label AS priority_label,
    d.status_id, st.code AS status_code, st.label AS status_label,
    d.resolved_variables, d.audit_outbox_id,
    d.failure_reason, d.scheduled_at, d.attempted_at, d.delivered_at,
    d.created_at, d.updated_at
FROM "06_notify"."15_fct_notify_deliveries" d
JOIN "06_notify"."01_dim_notify_channels" ch ON ch.id = d.channel_id
JOIN "06_notify"."04_dim_notify_priorities" pr ON pr.id = d.priority_id
JOIN "06_notify"."03_dim_notify_statuses" st ON st.id = d.status_id;

DROP INDEX IF EXISTS "06_notify"."uq_notify_deliveries_campaign_user_channel";
DROP INDEX IF EXISTS "06_notify"."idx_notify_deliveries_campaign";
ALTER TABLE "06_notify"."15_fct_notify_deliveries" DROP COLUMN IF EXISTS campaign_id;
DROP TABLE IF EXISTS "06_notify"."18_fct_notify_campaigns";
DROP TABLE IF EXISTS "06_notify"."05_dim_notify_campaign_statuses";
