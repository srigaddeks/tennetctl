-- UP ====
-- dim_monitoring_dashboard_share_event_kind — event taxonomy (granted, viewed, token_minted, token_rotated, revoked, expired, passphrase_failed).
-- evt_monitoring_dashboard_share_events — append-only event log, partitioned daily, 365-day retention.

-- Dimension table: event kinds
CREATE TABLE IF NOT EXISTS "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind" (
    id          SMALLINT NOT NULL,
    code        TEXT NOT NULL,
    label       TEXT NOT NULL,
    description TEXT,
    deprecated_at TIMESTAMP NULL,
    CONSTRAINT pk_dim_monitoring_dashboard_share_event_kind PRIMARY KEY (id),
    CONSTRAINT uq_dim_monitoring_dashboard_share_event_kind_code UNIQUE (code)
);

COMMENT ON TABLE  "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind" IS 'Event taxonomy: granted, viewed, token_minted, token_rotated, revoked, expired, passphrase_failed.';
COMMENT ON COLUMN "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind".id IS 'SMALLINT PK.';
COMMENT ON COLUMN "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind".code IS 'granted | viewed | token_minted | token_rotated | revoked | expired | passphrase_failed.';
COMMENT ON COLUMN "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind".label IS 'Human-readable label.';
COMMENT ON COLUMN "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind".description IS 'Usage description.';
COMMENT ON COLUMN "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind".deprecated_at IS 'Soft-deprecation marker.';

CREATE INDEX idx_dim_monitoring_dashboard_share_event_kind_code
    ON "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind" (code);

-- Append-only event table: partitioned by occurred_at (daily), 365-day retention
-- partition parent table (unpartitioned in design; migrations will add partitions as needed)
CREATE TABLE IF NOT EXISTS "05_monitoring"."63_evt_monitoring_dashboard_share_events" (
    id                  VARCHAR(36) NOT NULL,
    share_id            VARCHAR(36) NOT NULL,
    kind_id             SMALLINT NOT NULL,
    actor_user_id       VARCHAR(36) NULL,
    viewer_email        TEXT NULL,
    viewer_ip           INET NULL,
    viewer_ua           TEXT NULL,
    payload             JSONB DEFAULT '{}'::jsonb,
    occurred_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_evt_monitoring_dashboard_share_events PRIMARY KEY (id),
    CONSTRAINT fk_evt_monitoring_dashboard_share_events_share
        FOREIGN KEY (share_id)
        REFERENCES "05_monitoring"."12_fct_monitoring_dashboard_shares"(id),
    CONSTRAINT fk_evt_monitoring_dashboard_share_events_kind
        FOREIGN KEY (kind_id)
        REFERENCES "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind"(id),
    CONSTRAINT fk_evt_monitoring_dashboard_share_events_actor
        FOREIGN KEY (actor_user_id)
        REFERENCES "03_iam"."12_fct_users"(id)
) PARTITION BY RANGE (occurred_at);

COMMENT ON TABLE  "05_monitoring"."63_evt_monitoring_dashboard_share_events" IS 'Append-only event log: share grants, views, revocations, expirations. Partitioned daily. 365-day retention.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".id IS 'UUID v7 PK.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".share_id IS 'FK -> fct_monitoring_dashboard_shares.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".kind_id IS 'FK -> dim_monitoring_dashboard_share_event_kind.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".actor_user_id IS 'User performing the action (grant, revoke) or NULL for public viewer.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".viewer_email IS 'Email from public viewer, captured on view or passphrase attempt.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".viewer_ip IS 'Viewer IP (INET type) for brute-force tracking and audit.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".viewer_ua IS 'User-Agent string of viewer.';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".payload IS 'Additional event context (e.g., brute_force reason on revoke, recipient_email on mint).';
COMMENT ON COLUMN "05_monitoring"."63_evt_monitoring_dashboard_share_events".occurred_at IS 'Event timestamp (UTC). Partition key.';

-- Index for timeline queries (share_id + occurred_at DESC for efficient ordering)
CREATE INDEX idx_evt_monitoring_dashboard_share_events_share_time
    ON "05_monitoring"."63_evt_monitoring_dashboard_share_events" (share_id, occurred_at DESC);

-- Index for brute-force detector (viewer_ip, occurred_at for 10-minute window scans)
CREATE INDEX idx_evt_monitoring_dashboard_share_events_viewer_ip
    ON "05_monitoring"."63_evt_monitoring_dashboard_share_events" (viewer_ip, occurred_at DESC)
    WHERE kind_id = (SELECT id FROM "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind" WHERE code = 'passphrase_failed');

-- Seed initial dimension records for share scopes
INSERT INTO "05_monitoring"."01_dim_monitoring_dashboard_share_scope" (id, code, label, description, deprecated_at)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'internal_user', 'Internal User', 'Share with a known platform user in the same org.', NULL),
    (2, 'public_token', 'Public Token', 'Share via signed token URL (no login required).', NULL)
ON CONFLICT (id) DO NOTHING;

-- Seed initial dimension records for event kinds
INSERT INTO "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind" (id, code, label, description, deprecated_at)
OVERRIDING SYSTEM VALUE
VALUES
    (1, 'granted', 'Share Granted', 'Dashboard access granted to a user.', NULL),
    (2, 'viewed', 'Share Viewed', 'Dashboard viewed via share link.', NULL),
    (3, 'token_minted', 'Token Minted', 'Public share token created.', NULL),
    (4, 'token_rotated', 'Token Rotated', 'Public share token rotated (new token issued).', NULL),
    (5, 'revoked', 'Share Revoked', 'Dashboard share revoked/disabled.', NULL),
    (6, 'expired', 'Share Expired', 'Public share token expired.', NULL),
    (7, 'passphrase_failed', 'Passphrase Failed', 'Invalid passphrase attempt on protected share.', NULL)
ON CONFLICT (id) DO NOTHING;

-- DOWN ====
DELETE FROM "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind"
WHERE code IN ('granted', 'viewed', 'token_minted', 'token_rotated', 'revoked', 'expired', 'passphrase_failed');

DELETE FROM "05_monitoring"."01_dim_monitoring_dashboard_share_scope"
WHERE code IN ('internal_user', 'public_token');

DROP INDEX IF EXISTS "05_monitoring"."idx_evt_monitoring_dashboard_share_events_viewer_ip";
DROP INDEX IF EXISTS "05_monitoring"."idx_evt_monitoring_dashboard_share_events_share_time";
DROP TABLE IF EXISTS "05_monitoring"."63_evt_monitoring_dashboard_share_events";
DROP INDEX IF EXISTS "05_monitoring"."idx_dim_monitoring_dashboard_share_event_kind_code";
DROP TABLE IF EXISTS "05_monitoring"."02_dim_monitoring_dashboard_share_event_kind";
