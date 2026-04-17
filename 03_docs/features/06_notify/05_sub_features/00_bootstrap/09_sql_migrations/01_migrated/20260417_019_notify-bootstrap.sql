-- UP ====
-- Notify feature bootstrap: schema + 4 dim tables.

CREATE SCHEMA IF NOT EXISTS "06_notify";

-- Channels: email, web push, in-app, SMS
CREATE TABLE IF NOT EXISTS "06_notify"."01_dim_notify_channels" (
    id           SMALLINT     NOT NULL,
    code         TEXT         NOT NULL,
    label        TEXT         NOT NULL,
    description  TEXT         NOT NULL,
    deprecated_at TIMESTAMP   NULL,
    CONSTRAINT pk_dim_notify_channels PRIMARY KEY (id),
    CONSTRAINT uq_dim_notify_channels_code UNIQUE (code)
);
COMMENT ON TABLE  "06_notify"."01_dim_notify_channels" IS 'Delivery channel enum: email, webpush, in_app, sms.';
COMMENT ON COLUMN "06_notify"."01_dim_notify_channels".id IS 'Permanent SMALLINT PK — never renumber.';
COMMENT ON COLUMN "06_notify"."01_dim_notify_channels".code IS 'Stable code referenced by fct/evt tables.';

-- Categories: transactional, critical, marketing, digest
CREATE TABLE IF NOT EXISTS "06_notify"."02_dim_notify_categories" (
    id           SMALLINT     NOT NULL,
    code         TEXT         NOT NULL,
    label        TEXT         NOT NULL,
    description  TEXT         NOT NULL,
    deprecated_at TIMESTAMP   NULL,
    CONSTRAINT pk_dim_notify_categories PRIMARY KEY (id),
    CONSTRAINT uq_dim_notify_categories_code UNIQUE (code)
);
COMMENT ON TABLE  "06_notify"."02_dim_notify_categories" IS 'Notification category enum. critical = multi-channel fan-out + priority queue.';
COMMENT ON COLUMN "06_notify"."02_dim_notify_categories".id IS 'Permanent SMALLINT PK — never renumber.';
COMMENT ON COLUMN "06_notify"."02_dim_notify_categories".code IS 'Stable code: transactional | critical | marketing | digest.';

-- Statuses: delivery lifecycle
CREATE TABLE IF NOT EXISTS "06_notify"."03_dim_notify_statuses" (
    id           SMALLINT     NOT NULL,
    code         TEXT         NOT NULL,
    label        TEXT         NOT NULL,
    description  TEXT         NOT NULL,
    deprecated_at TIMESTAMP   NULL,
    CONSTRAINT pk_dim_notify_statuses PRIMARY KEY (id),
    CONSTRAINT uq_dim_notify_statuses_code UNIQUE (code)
);
COMMENT ON TABLE  "06_notify"."03_dim_notify_statuses" IS 'Delivery status lifecycle: pending → queued → sent → delivered → opened/clicked/bounced/failed/unsubscribed.';

-- Priorities
CREATE TABLE IF NOT EXISTS "06_notify"."04_dim_notify_priorities" (
    id           SMALLINT     NOT NULL,
    code         TEXT         NOT NULL,
    label        TEXT         NOT NULL,
    description  TEXT         NOT NULL,
    deprecated_at TIMESTAMP   NULL,
    CONSTRAINT pk_dim_notify_priorities PRIMARY KEY (id),
    CONSTRAINT uq_dim_notify_priorities_code UNIQUE (code)
);
COMMENT ON TABLE  "06_notify"."04_dim_notify_priorities" IS 'Delivery priority enum. critical priority bypasses throttling and fans out to all enabled channels.';

-- DOWN ====
DROP TABLE IF EXISTS "06_notify"."04_dim_notify_priorities";
DROP TABLE IF EXISTS "06_notify"."03_dim_notify_statuses";
DROP TABLE IF EXISTS "06_notify"."02_dim_notify_categories";
DROP TABLE IF EXISTS "06_notify"."01_dim_notify_channels";
DROP SCHEMA IF EXISTS "06_notify";
