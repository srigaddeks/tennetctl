-- Migration 035: Subscription recipient model + SMTP from fields
--
-- Closes two gaps:
--
-- 1. Subscriptions route notifications based on `recipient_mode`:
--      'actor'  — audit_event.actor_user_id (self-service events, default)
--      'users'  — recipient_filter.user_ids = [...] (explicit recipients)
--      'roles'  — recipient_filter.role_codes = [...] (all users with those
--                 role codes in the event's org)
--    Without this the worker always notifies the person who triggered the
--    event, which is wrong for admin broadcasts.
--
-- 2. SMTP configs get from_email + from_name so real providers (SendGrid,
--    Postmark, Mailgun) can authenticate with an API key username while the
--    envelope From address is a proper mailbox.
--
-- View chain: v_notify_smtp_configs → v_notify_template_groups →
-- v_notify_templates. Drop top-down, recreate bottom-up.

-- UP ====

-- Drop dependent views first.
DROP VIEW IF EXISTS "06_notify"."v_notify_templates";
DROP VIEW IF EXISTS "06_notify"."v_notify_template_groups";
DROP VIEW IF EXISTS "06_notify"."v_notify_smtp_configs";
DROP VIEW IF EXISTS "06_notify"."v_notify_subscriptions";

-- ── Subscriptions: recipient model ────────────────────────────────────────
ALTER TABLE "06_notify"."14_fct_notify_subscriptions"
    ADD COLUMN recipient_mode TEXT NOT NULL DEFAULT 'actor',
    ADD COLUMN recipient_filter JSONB NOT NULL DEFAULT '{}'::jsonb;

ALTER TABLE "06_notify"."14_fct_notify_subscriptions"
    ADD CONSTRAINT chk_notify_subscriptions_recipient_mode
    CHECK (recipient_mode IN ('actor', 'users', 'roles'));

COMMENT ON COLUMN "06_notify"."14_fct_notify_subscriptions".recipient_mode IS
    'Who receives the notification. actor = audit event actor (default, self-service); users = recipient_filter.user_ids; roles = recipient_filter.role_codes.';
COMMENT ON COLUMN "06_notify"."14_fct_notify_subscriptions".recipient_filter IS
    'Filter payload for recipient_mode. {} for actor; {user_ids:[...]} for users; {role_codes:[...]} for roles.';

-- ── SMTP configs: From email + name ───────────────────────────────────────
ALTER TABLE "06_notify"."10_fct_notify_smtp_configs"
    ADD COLUMN from_email TEXT NULL,
    ADD COLUMN from_name  TEXT NULL;

COMMENT ON COLUMN "06_notify"."10_fct_notify_smtp_configs".from_email IS
    'Envelope From address. Falls back to username if null. Required when SMTP auth username is an API key (SendGrid, Postmark, etc.).';
COMMENT ON COLUMN "06_notify"."10_fct_notify_smtp_configs".from_name IS
    'Optional display name used in From header (e.g. "Acme Support").';

-- ── Recreate views bottom-up ──────────────────────────────────────────────
CREATE VIEW "06_notify"."v_notify_smtp_configs" AS
SELECT
    s.id, s.org_id, s.key, s.label, s.host, s.port, s.tls, s.username,
    s.auth_vault_key, s.from_email, s.from_name,
    s.is_active, s.created_by, s.updated_by, s.created_at, s.updated_at
FROM "06_notify"."10_fct_notify_smtp_configs" s
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW "06_notify"."v_notify_smtp_configs" IS
    'Read path for SMTP configs. Includes from_email/from_name.';

CREATE VIEW "06_notify"."v_notify_template_groups" AS
SELECT
    g.id, g.org_id, g.key, g.label,
    g.category_id, c.code AS category_code, c.label AS category_label,
    g.smtp_config_id, s.key AS smtp_config_key,
    g.is_active, g.created_by, g.updated_by, g.created_at, g.updated_at
FROM "06_notify"."11_fct_notify_template_groups" g
JOIN "06_notify"."02_dim_notify_categories" c ON c.id = g.category_id
LEFT JOIN "06_notify"."v_notify_smtp_configs" s ON s.id::text = g.smtp_config_id::text
WHERE g.deleted_at IS NULL;

CREATE VIEW "06_notify"."v_notify_templates" AS
SELECT
    t.id, t.org_id, t.key, t.group_id,
    g.key AS group_key, g.category_id, g.category_code, g.category_label,
    t.subject, t.reply_to, t.priority_id,
    p.code AS priority_code, p.label AS priority_label,
    t.is_active, t.created_by, t.updated_by, t.created_at, t.updated_at,
    COALESCE(
        json_agg(
            json_build_object(
                'id', b.id,
                'channel_id', b.channel_id,
                'body_html', b.body_html,
                'body_text', b.body_text,
                'preheader', b.preheader
            ) ORDER BY b.channel_id
        ) FILTER (WHERE b.id IS NOT NULL),
        '[]'::json
    ) AS bodies
FROM "06_notify"."12_fct_notify_templates" t
JOIN "06_notify"."v_notify_template_groups" g ON g.id::text = t.group_id::text
JOIN "06_notify"."04_dim_notify_priorities" p ON p.id = t.priority_id
LEFT JOIN "06_notify"."20_dtl_notify_template_bodies" b ON b.template_id::text = t.id::text
WHERE t.deleted_at IS NULL
GROUP BY t.id, t.org_id, t.key, t.group_id, g.key, g.category_id, g.category_code,
         g.category_label, t.subject, t.reply_to, t.priority_id, p.code, p.label,
         t.is_active, t.created_by, t.updated_by, t.created_at, t.updated_at;

CREATE VIEW "06_notify"."v_notify_subscriptions" AS
SELECT
    s.id, s.org_id, s.name, s.event_key_pattern, s.template_id,
    s.channel_id, c.code AS channel_code, c.label AS channel_label,
    s.recipient_mode, s.recipient_filter,
    s.is_active, s.deleted_at,
    s.created_by, s.updated_by, s.created_at, s.updated_at
FROM "06_notify"."14_fct_notify_subscriptions" s
JOIN "06_notify"."01_dim_notify_channels" c ON c.id = s.channel_id
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW "06_notify"."v_notify_subscriptions" IS
    'Read path for subscriptions: joins channel dim + exposes recipient model.';

-- DOWN ====
DROP VIEW IF EXISTS "06_notify"."v_notify_subscriptions";
DROP VIEW IF EXISTS "06_notify"."v_notify_templates";
DROP VIEW IF EXISTS "06_notify"."v_notify_template_groups";
DROP VIEW IF EXISTS "06_notify"."v_notify_smtp_configs";

ALTER TABLE "06_notify"."10_fct_notify_smtp_configs"
    DROP COLUMN IF EXISTS from_email,
    DROP COLUMN IF EXISTS from_name;

ALTER TABLE "06_notify"."14_fct_notify_subscriptions"
    DROP CONSTRAINT IF EXISTS chk_notify_subscriptions_recipient_mode;

ALTER TABLE "06_notify"."14_fct_notify_subscriptions"
    DROP COLUMN IF EXISTS recipient_mode,
    DROP COLUMN IF EXISTS recipient_filter;

-- Restore old views (without new columns)
CREATE VIEW "06_notify"."v_notify_smtp_configs" AS
SELECT id, org_id, key, label, host, port, tls, username, auth_vault_key,
       is_active, created_by, updated_by, created_at, updated_at
FROM "06_notify"."10_fct_notify_smtp_configs"
WHERE deleted_at IS NULL;

CREATE VIEW "06_notify"."v_notify_template_groups" AS
SELECT g.id, g.org_id, g.key, g.label,
       g.category_id, c.code AS category_code, c.label AS category_label,
       g.smtp_config_id, s.key AS smtp_config_key,
       g.is_active, g.created_by, g.updated_by, g.created_at, g.updated_at
FROM "06_notify"."11_fct_notify_template_groups" g
JOIN "06_notify"."02_dim_notify_categories" c ON c.id = g.category_id
LEFT JOIN "06_notify"."v_notify_smtp_configs" s ON s.id::text = g.smtp_config_id::text
WHERE g.deleted_at IS NULL;

CREATE VIEW "06_notify"."v_notify_templates" AS
SELECT t.id, t.org_id, t.key, t.group_id,
       g.key AS group_key, g.category_id, g.category_code, g.category_label,
       t.subject, t.reply_to, t.priority_id,
       p.code AS priority_code, p.label AS priority_label,
       t.is_active, t.created_by, t.updated_by, t.created_at, t.updated_at,
       COALESCE(
           json_agg(
               json_build_object(
                   'id', b.id, 'channel_id', b.channel_id,
                   'body_html', b.body_html, 'body_text', b.body_text,
                   'preheader', b.preheader
               ) ORDER BY b.channel_id
           ) FILTER (WHERE b.id IS NOT NULL),
           '[]'::json
       ) AS bodies
FROM "06_notify"."12_fct_notify_templates" t
JOIN "06_notify"."v_notify_template_groups" g ON g.id::text = t.group_id::text
JOIN "06_notify"."04_dim_notify_priorities" p ON p.id = t.priority_id
LEFT JOIN "06_notify"."20_dtl_notify_template_bodies" b ON b.template_id::text = t.id::text
WHERE t.deleted_at IS NULL
GROUP BY t.id, t.org_id, t.key, t.group_id, g.key, g.category_id, g.category_code,
         g.category_label, t.subject, t.reply_to, t.priority_id, p.code, p.label,
         t.is_active, t.created_by, t.updated_by, t.created_at, t.updated_at;

CREATE VIEW "06_notify"."v_notify_subscriptions" AS
SELECT s.id, s.org_id, s.name, s.event_key_pattern, s.template_id,
       s.channel_id, c.code AS channel_code, c.label AS channel_label,
       s.is_active, s.deleted_at,
       s.created_by, s.updated_by, s.created_at, s.updated_at
FROM "06_notify"."14_fct_notify_subscriptions" s
JOIN "06_notify"."01_dim_notify_channels" c ON c.id = s.channel_id
WHERE s.deleted_at IS NULL;
