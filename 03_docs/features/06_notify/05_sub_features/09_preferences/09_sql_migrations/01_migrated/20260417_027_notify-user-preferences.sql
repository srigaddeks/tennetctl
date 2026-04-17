-- Migration 027: notify user preferences
--
-- fct_notify_user_preferences: per-user opt-in/out per (channel, category) pair.
-- Default is opted-in (row absent = opted-in). Upsert sets the explicit preference.
--
-- Business rules enforced in service.py:
--   - category=critical (id=2) cannot be opted out — row allowed but is_opted_in
--     forced to TRUE by service layer.
--   - Non-critical channels can be freely toggled per user.
--
-- Depends on: 06_notify schema (migration 019)
--             01_dim_notify_channels, 02_dim_notify_categories (seeded in 019)

-- UP ====

CREATE TABLE "06_notify"."17_fct_notify_user_preferences" (
    id              VARCHAR(36)  NOT NULL,
    org_id          VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL,
    channel_id      SMALLINT     NOT NULL,
    category_id     SMALLINT     NOT NULL,
    is_opted_in     BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(36)  NOT NULL,
    updated_by      VARCHAR(36)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_user_prefs PRIMARY KEY (id),
    CONSTRAINT uq_notify_user_prefs UNIQUE (org_id, user_id, channel_id, category_id),
    CONSTRAINT fk_notify_user_prefs_channel
        FOREIGN KEY (channel_id) REFERENCES "06_notify"."01_dim_notify_channels" (id),
    CONSTRAINT fk_notify_user_prefs_category
        FOREIGN KEY (category_id) REFERENCES "06_notify"."02_dim_notify_categories" (id)
);

COMMENT ON TABLE  "06_notify"."17_fct_notify_user_preferences" IS
    'Per-user notification preferences. Absence of a row means opted-in (default). '
    'is_opted_in=FALSE means the user has opted out of that channel+category combination. '
    'critical category (id=2) is always forced to TRUE by the service layer.';
COMMENT ON COLUMN "06_notify"."17_fct_notify_user_preferences".org_id IS
    'Organisation scope — preferences are per-org.';
COMMENT ON COLUMN "06_notify"."17_fct_notify_user_preferences".user_id IS
    'User who holds the preference.';
COMMENT ON COLUMN "06_notify"."17_fct_notify_user_preferences".channel_id IS
    'FK to 01_dim_notify_channels. email=1, webpush=2, in_app=3, sms=4.';
COMMENT ON COLUMN "06_notify"."17_fct_notify_user_preferences".category_id IS
    'FK to 02_dim_notify_categories. transactional=1, critical=2, marketing=3, digest=4.';
COMMENT ON COLUMN "06_notify"."17_fct_notify_user_preferences".is_opted_in IS
    'TRUE = user wants this notification; FALSE = user has opted out.';

CREATE INDEX idx_notify_user_prefs_user
    ON "06_notify"."17_fct_notify_user_preferences" (org_id, user_id);

CREATE OR REPLACE VIEW "06_notify"."v_notify_user_preferences" AS
SELECT
    p.id,
    p.org_id,
    p.user_id,
    p.channel_id,
    c.code  AS channel_code,
    c.label AS channel_label,
    p.category_id,
    cat.code  AS category_code,
    cat.label AS category_label,
    p.is_opted_in,
    p.created_by,
    p.updated_by,
    p.created_at,
    p.updated_at
FROM "06_notify"."17_fct_notify_user_preferences" p
JOIN "06_notify"."01_dim_notify_channels"   c   ON c.id = p.channel_id
JOIN "06_notify"."02_dim_notify_categories" cat ON cat.id = p.category_id;

COMMENT ON VIEW "06_notify"."v_notify_user_preferences" IS
    'User notification preferences with resolved channel + category codes.';

-- DOWN ====

DROP VIEW  IF EXISTS "06_notify"."v_notify_user_preferences";
DROP TABLE IF EXISTS "06_notify"."17_fct_notify_user_preferences";
