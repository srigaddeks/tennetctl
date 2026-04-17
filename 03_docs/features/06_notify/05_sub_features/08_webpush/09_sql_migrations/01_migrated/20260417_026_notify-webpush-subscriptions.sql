-- Migration 026: notify webpush subscriptions
--
-- fct_notify_webpush_subscriptions: browser Push API subscription records per user.
-- Each row holds the endpoint + ECDH keys returned by PushSubscription.toJSON().
-- A user may have multiple active subscriptions (multiple devices/browsers).
-- The sender polls this table to get all targets for a given recipient_user_id.
--
-- Depends on: 06_notify schema (migration 019)

-- UP ====

CREATE TABLE "06_notify"."16_fct_notify_webpush_subscriptions" (
    id              VARCHAR(36)  NOT NULL,
    org_id          VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL,
    endpoint        TEXT         NOT NULL,
    p256dh          TEXT         NOT NULL,
    auth            TEXT         NOT NULL,
    device_label    TEXT,
    is_active       BOOLEAN      NOT NULL DEFAULT TRUE,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36)  NOT NULL,
    updated_by      VARCHAR(36)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_webpush_subscriptions PRIMARY KEY (id),
    CONSTRAINT uq_notify_webpush_endpoint UNIQUE (endpoint)
);

COMMENT ON TABLE  "06_notify"."16_fct_notify_webpush_subscriptions" IS
    'Browser push subscription records. endpoint is unique per browser/device pair. p256dh + auth are the ECDH keys from PushSubscription.toJSON().';
COMMENT ON COLUMN "06_notify"."16_fct_notify_webpush_subscriptions".endpoint IS
    'Push service URL from browser PushSubscription.endpoint. Globally unique per device+browser combination.';
COMMENT ON COLUMN "06_notify"."16_fct_notify_webpush_subscriptions".p256dh IS
    'Base64url ECDH P-256 public key from PushSubscription.keys.p256dh.';
COMMENT ON COLUMN "06_notify"."16_fct_notify_webpush_subscriptions".auth IS
    'Base64url authentication secret from PushSubscription.keys.auth.';
COMMENT ON COLUMN "06_notify"."16_fct_notify_webpush_subscriptions".device_label IS
    'Optional human-readable label: "Phone Safari", "Laptop Chrome". User-supplied; nullable.';

CREATE INDEX idx_notify_webpush_sub_user
    ON "06_notify"."16_fct_notify_webpush_subscriptions" (user_id)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_notify_webpush_sub_org
    ON "06_notify"."16_fct_notify_webpush_subscriptions" (org_id)
    WHERE deleted_at IS NULL;

CREATE OR REPLACE VIEW "06_notify"."v_notify_webpush_subscriptions" AS
SELECT
    id, org_id, user_id, endpoint, p256dh, auth, device_label,
    is_active, created_by, updated_by, created_at, updated_at
FROM "06_notify"."16_fct_notify_webpush_subscriptions"
WHERE deleted_at IS NULL;

COMMENT ON VIEW "06_notify"."v_notify_webpush_subscriptions" IS
    'Active webpush subscriptions (excludes soft-deleted rows).';

-- DOWN ====

DROP VIEW  IF EXISTS "06_notify"."v_notify_webpush_subscriptions";
DROP TABLE IF EXISTS "06_notify"."16_fct_notify_webpush_subscriptions";
