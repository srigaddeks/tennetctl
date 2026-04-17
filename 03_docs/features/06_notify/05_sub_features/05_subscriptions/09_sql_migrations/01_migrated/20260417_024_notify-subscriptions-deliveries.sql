-- Migration 024: notify subscriptions + deliveries + delivery events
--
-- fct_notify_subscriptions: maps event_key_pattern → template + channel per org
-- fct_notify_deliveries: delivery queue (queued/processing/delivered/failed)
-- evt_notify_delivery_events: append-only tracking (open/click/bounce/unsubscribe)
-- Views expose joined dim codes for read path.
--
-- Depends on: 06_notify schema + dims + 12_fct_notify_templates (migration 021)
--             03_dim_notify_statuses (pending=1, queued=2, sent=3, delivered=4, ...)

-- UP ====

-- ── Subscriptions ───────────────────────────────────────────────────────────

CREATE TABLE "06_notify"."14_fct_notify_subscriptions" (
    id                  VARCHAR(36)     NOT NULL,
    org_id              VARCHAR(36)     NOT NULL,
    name                TEXT            NOT NULL,
    event_key_pattern   TEXT            NOT NULL,
    template_id         VARCHAR(36)     NOT NULL,
    channel_id          SMALLINT        NOT NULL,
    is_active           BOOLEAN         NOT NULL DEFAULT true,
    deleted_at          TIMESTAMP,
    created_by          TEXT            NOT NULL,
    updated_by          TEXT            NOT NULL,
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_subscriptions PRIMARY KEY (id),
    CONSTRAINT fk_notify_subscriptions_template FOREIGN KEY (template_id)
        REFERENCES "06_notify"."12_fct_notify_templates"(id),
    CONSTRAINT fk_notify_subscriptions_channel FOREIGN KEY (channel_id)
        REFERENCES "06_notify"."01_dim_notify_channels"(id)
);

CREATE INDEX idx_notify_subscriptions_org ON "06_notify"."14_fct_notify_subscriptions" (org_id);
CREATE INDEX idx_notify_subscriptions_pattern ON "06_notify"."14_fct_notify_subscriptions" (event_key_pattern);

COMMENT ON TABLE "06_notify"."14_fct_notify_subscriptions" IS
    'Maps event_key_pattern to a template + channel per org. Worker matches incoming audit events against these.';
COMMENT ON COLUMN "06_notify"."14_fct_notify_subscriptions".event_key_pattern IS
    'Exact ("iam.users.created"), suffix wildcard ("iam.users.*"), deep wildcard ("iam.*"), or global ("*").';

-- ── Deliveries ──────────────────────────────────────────────────────────────

CREATE TABLE "06_notify"."15_fct_notify_deliveries" (
    id                  VARCHAR(36)     NOT NULL,
    org_id              VARCHAR(36)     NOT NULL,
    subscription_id     VARCHAR(36),
    template_id         VARCHAR(36)     NOT NULL,
    recipient_user_id   TEXT            NOT NULL,
    channel_id          SMALLINT        NOT NULL,
    priority_id         SMALLINT        NOT NULL,
    status_id           SMALLINT        NOT NULL DEFAULT 2,
    resolved_variables  JSONB           NOT NULL DEFAULT '{}',
    audit_outbox_id     BIGINT,
    failure_reason      TEXT,
    scheduled_at        TIMESTAMP,
    attempted_at        TIMESTAMP,
    delivered_at        TIMESTAMP,
    created_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_deliveries PRIMARY KEY (id),
    CONSTRAINT fk_notify_deliveries_subscription FOREIGN KEY (subscription_id)
        REFERENCES "06_notify"."14_fct_notify_subscriptions"(id),
    CONSTRAINT fk_notify_deliveries_template FOREIGN KEY (template_id)
        REFERENCES "06_notify"."12_fct_notify_templates"(id),
    CONSTRAINT fk_notify_deliveries_channel FOREIGN KEY (channel_id)
        REFERENCES "06_notify"."01_dim_notify_channels"(id),
    CONSTRAINT fk_notify_deliveries_priority FOREIGN KEY (priority_id)
        REFERENCES "06_notify"."04_dim_notify_priorities"(id),
    CONSTRAINT fk_notify_deliveries_status FOREIGN KEY (status_id)
        REFERENCES "06_notify"."03_dim_notify_statuses"(id)
);

CREATE INDEX idx_notify_deliveries_org ON "06_notify"."15_fct_notify_deliveries" (org_id);
CREATE INDEX idx_notify_deliveries_status ON "06_notify"."15_fct_notify_deliveries" (status_id);
CREATE INDEX idx_notify_deliveries_recipient ON "06_notify"."15_fct_notify_deliveries" (recipient_user_id);
CREATE INDEX idx_notify_deliveries_subscription ON "06_notify"."15_fct_notify_deliveries" (subscription_id);

COMMENT ON TABLE "06_notify"."15_fct_notify_deliveries" IS
    'Delivery queue. subscription_id=NULL for transactional sends (Plan 11-10). status_id=2 (queued) on creation.';
COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".recipient_user_id IS
    'actor_user_id from the matching audit event. TEXT (not FK) to avoid cross-schema FK coupling.';
COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".audit_outbox_id IS
    'Reference to 04_audit.61_evt_audit_outbox.id (not enforced FK). Used for idempotency and debugging.';
COMMENT ON COLUMN "06_notify"."15_fct_notify_deliveries".resolved_variables IS
    'Snapshot of resolved template variables at enqueue time. Stored so render does not re-resolve at send time.';

-- ── Delivery tracking events ─────────────────────────────────────────────────

CREATE TABLE "06_notify"."61_evt_notify_delivery_events" (
    id          VARCHAR(36)     NOT NULL,
    delivery_id VARCHAR(36)     NOT NULL,
    event_type  TEXT            NOT NULL,
    metadata    JSONB           NOT NULL DEFAULT '{}',
    occurred_at TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_delivery_events PRIMARY KEY (id),
    CONSTRAINT fk_notify_delivery_events_delivery FOREIGN KEY (delivery_id)
        REFERENCES "06_notify"."15_fct_notify_deliveries"(id) ON DELETE CASCADE,
    CONSTRAINT chk_notify_delivery_event_type CHECK (
        event_type IN ('open', 'click', 'bounce', 'unsubscribe', 'spam_report')
    )
);

CREATE INDEX idx_notify_delivery_events_delivery ON "06_notify"."61_evt_notify_delivery_events" (delivery_id);

COMMENT ON TABLE "06_notify"."61_evt_notify_delivery_events" IS
    'Append-only tracking events for each delivery: open, click, bounce, unsubscribe, spam_report.';

-- ── Views ────────────────────────────────────────────────────────────────────

CREATE VIEW "06_notify"."v_notify_subscriptions" AS
SELECT
    s.id, s.org_id, s.name, s.event_key_pattern, s.template_id,
    s.channel_id, c.code AS channel_code, c.label AS channel_label,
    s.is_active, s.deleted_at, s.created_by, s.updated_by,
    s.created_at, s.updated_at
FROM "06_notify"."14_fct_notify_subscriptions" s
JOIN "06_notify"."01_dim_notify_channels" c ON c.id = s.channel_id
WHERE s.deleted_at IS NULL;

COMMENT ON VIEW "06_notify"."v_notify_subscriptions" IS
    'Read path for subscriptions: joins channel dim, filters deleted.';

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

COMMENT ON VIEW "06_notify"."v_notify_deliveries" IS
    'Read path for deliveries: joins channel/priority/status dims.';

CREATE VIEW "06_notify"."v_notify_delivery_events" AS
SELECT id, delivery_id, event_type, metadata, occurred_at
FROM "06_notify"."61_evt_notify_delivery_events";

COMMENT ON VIEW "06_notify"."v_notify_delivery_events" IS
    'Read path for delivery tracking events (open/click/bounce).';

-- DOWN ====

DROP VIEW IF EXISTS "06_notify"."v_notify_delivery_events";
DROP VIEW IF EXISTS "06_notify"."v_notify_deliveries";
DROP VIEW IF EXISTS "06_notify"."v_notify_subscriptions";
DROP TABLE IF EXISTS "06_notify"."61_evt_notify_delivery_events";
DROP TABLE IF EXISTS "06_notify"."15_fct_notify_deliveries";
DROP TABLE IF EXISTS "06_notify"."14_fct_notify_subscriptions";
