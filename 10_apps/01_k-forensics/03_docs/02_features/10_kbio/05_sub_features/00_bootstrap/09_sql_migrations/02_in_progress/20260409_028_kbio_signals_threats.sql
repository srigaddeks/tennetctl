-- =============================================================================
-- Migration:   20260409_028_kbio_signals_threats.sql
-- Module:      10_kbio
-- Sub-feature: 00_bootstrap
-- Sequence:    028
-- Depends on:  020 (10_kbio/00_bootstrap), 021 (10_kbio/00_bootstrap tables)
-- Description: Add signal and threat type infrastructure to the 10_kbio schema.
--              Creates dimension tables for signal categories, signal types, and
--              threat categories. Creates fact tables for signal and threat type
--              definitions (catalog synced from Python). Creates append-only
--              event tables for signal and threat evaluation results.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 10_dim_signal_categories
-- Thematic categories for behavioral signals evaluated by the scoring engine.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."10_dim_signal_categories" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_signal_categories       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_signal_categories_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."10_dim_signal_categories" IS
    'Thematic categories for behavioral signals. Groups signal definitions '
    'by domain (behavioral, device, network, etc.) for filtering and reporting.';
COMMENT ON COLUMN "10_kbio"."10_dim_signal_categories".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."10_dim_signal_categories".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."10_dim_signal_categories".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."10_dim_signal_categories".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."10_dim_signal_categories".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."10_dim_signal_categories" (code, label, description) VALUES
    ('behavioral',          'Behavioral',          'Signals from kbio scoring pipeline.'),
    ('device',              'Device',              'Signals from device fingerprint and trust.'),
    ('network',             'Network',             'Signals from IP/geo/VPN/Tor analysis.'),
    ('temporal',            'Temporal',            'Signals based on time and activity patterns.'),
    ('credential',          'Credential',          'Signals about credential usage patterns.'),
    ('session',             'Session',             'Signals about session behavior.'),
    ('historical',          'Historical',          'Signals from historical user/device data.'),
    ('bot',                 'Bot & Automation',    'Signals detecting automated interactions.'),
    ('social_engineering',  'Social Engineering',  'Signals detecting coercion and coaching.'),
    ('transaction',         'Transaction Risk',    'Signals for high-risk actions.'),
    ('fraud_ring',          'Fraud Ring',          'Signals detecting coordinated fraud.'),
    ('compliance',          'Compliance',          'Signals for regulatory compliance.');

GRANT SELECT ON "10_kbio"."10_dim_signal_categories" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."10_dim_signal_categories" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 11_dim_signal_types
-- Value types that a signal function can produce: boolean or score.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."11_dim_signal_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_signal_types       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_signal_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."11_dim_signal_types" IS
    'Value types for signal functions. Determines whether a signal produces '
    'a boolean result or a 0.0–1.0 score float.';
COMMENT ON COLUMN "10_kbio"."11_dim_signal_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."11_dim_signal_types".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."11_dim_signal_types".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."11_dim_signal_types".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."11_dim_signal_types".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."11_dim_signal_types" (code, label, description) VALUES
    ('boolean',  'Boolean',  'Signal produces true/false.'),
    ('score',    'Score',    'Signal produces 0.0-1.0 float.');

GRANT SELECT ON "10_kbio"."11_dim_signal_types" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."11_dim_signal_types" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 12_dim_threat_categories
-- Thematic categories for threat type definitions.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."12_dim_threat_categories" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_threat_categories       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_threat_categories_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."12_dim_threat_categories" IS
    'Thematic categories for threat type definitions. Groups threat types '
    'by attack vector (account takeover, bot attack, identity fraud, etc.).';
COMMENT ON COLUMN "10_kbio"."12_dim_threat_categories".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."12_dim_threat_categories".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."12_dim_threat_categories".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."12_dim_threat_categories".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."12_dim_threat_categories".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."12_dim_threat_categories" (code, label, description) VALUES
    ('account_takeover',   'Account Takeover',   'Unauthorized account access patterns.'),
    ('bot_attack',         'Bot Attack',         'Automated/scripted interaction patterns.'),
    ('identity_fraud',     'Identity Fraud',     'Identity impersonation and synthetic identity.'),
    ('social_engineering', 'Social Engineering', 'Coercion, coaching, and manipulation.'),
    ('network_threat',     'Network Threat',     'Anonymizer and geo anomaly patterns.'),
    ('transaction_fraud',  'Transaction Fraud',  'Fraudulent financial operations.'),
    ('fraud_ring',         'Fraud Ring',         'Coordinated multi-account fraud.'),
    ('compliance',         'Compliance',         'Regulatory policy breach patterns.');

GRANT SELECT ON "10_kbio"."12_dim_threat_categories" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."12_dim_threat_categories" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- Add entity types for signal and threat definitions to 06_dim_entity_types
-- id=9: kbio_signal_def, id=10: kbio_threat_type_def
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."06_dim_entity_types" (code, label, description) VALUES
    ('kbio_signal_def',      'Signal Definition',      'Registry entry for a signal function.'),
    ('kbio_threat_type_def', 'Threat Type Definition', 'Registry entry for a threat type composition.');

-- ---------------------------------------------------------------------------
-- Add attr defs for kbio_signal_def entity type to 07_dim_attr_defs
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kbio_signal_def', 'code',            'Signal Code',          'Stable machine-readable identifier for the signal.',           'key_text'),
    ('kbio_signal_def', 'name',            'Signal Name',          'Human-readable display name for the signal.',                  'key_text'),
    ('kbio_signal_def', 'description',     'Signal Description',   'Full description of what the signal detects and how.',         'key_text'),
    ('kbio_signal_def', 'function_name',   'Function Name',        'Python function name in the signal registry.',                 'key_text'),
    ('kbio_signal_def', 'default_config',  'Default Config',       'JSON object with default thresholds and parameters.',          'key_jsonb'),
    ('kbio_signal_def', 'tags',            'Tags',                 'Comma-separated tags for filtering and grouping.',             'key_text'),
    ('kbio_signal_def', 'version',         'Version',              'Semver string of the signal definition (e.g. 1.0.0).',        'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- Add attr defs for kbio_threat_type_def entity type to 07_dim_attr_defs
-- ---------------------------------------------------------------------------
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('kbio_threat_type_def', 'code',            'Threat Code',          'Stable machine-readable identifier for the threat type.',               'key_text'),
    ('kbio_threat_type_def', 'name',            'Threat Name',          'Human-readable display name for the threat type.',                      'key_text'),
    ('kbio_threat_type_def', 'description',     'Threat Description',   'Full description of the threat and its detection logic.',               'key_text'),
    ('kbio_threat_type_def', 'conditions',      'Conditions',           'JSON object defining signal conditions that compose this threat.',      'key_jsonb'),
    ('kbio_threat_type_def', 'default_config',  'Default Config',       'JSON object with default thresholds and parameters.',                   'key_jsonb'),
    ('kbio_threat_type_def', 'default_action',  'Default Action',       'Default enforcement action code (allow, monitor, challenge, block).',   'key_text'),
    ('kbio_threat_type_def', 'tags',            'Tags',                 'Comma-separated tags for filtering and grouping.',                      'key_text'),
    ('kbio_threat_type_def', 'version',         'Version',              'Semver string of the threat type definition (e.g. 1.0.0).',            'key_text'),
    ('kbio_threat_type_def', 'mitre_mapping',   'MITRE Mapping',        'MITRE ATT&CK technique ID mapping (e.g. T1078, T1110).',               'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- 16_fct_signal_defs — Signal definition catalog (synced from Python)
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."16_fct_signal_defs" (
    id              VARCHAR(36)   NOT NULL,
    category_id     SMALLINT      NOT NULL,
    signal_type_id  SMALLINT      NOT NULL,
    severity        SMALLINT      NOT NULL DEFAULT 50,
    is_active       BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test         BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at      TIMESTAMP,
    created_by      VARCHAR(36)   NOT NULL,
    updated_by      VARCHAR(36)   NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kbio_fct_signal_defs              PRIMARY KEY (id),
    CONSTRAINT fk_kbio_fct_signal_defs_category     FOREIGN KEY (category_id)
                                                     REFERENCES "10_kbio"."10_dim_signal_categories" (id),
    CONSTRAINT fk_kbio_fct_signal_defs_signal_type  FOREIGN KEY (signal_type_id)
                                                     REFERENCES "10_kbio"."11_dim_signal_types" (id),
    CONSTRAINT chk_kbio_fct_signal_defs_severity    CHECK (severity BETWEEN 0 AND 100)
);

CREATE INDEX idx_kbio_fct_signal_defs_category    ON "10_kbio"."16_fct_signal_defs" (category_id);
CREATE INDEX idx_kbio_fct_signal_defs_signal_type ON "10_kbio"."16_fct_signal_defs" (signal_type_id);
CREATE INDEX idx_kbio_fct_signal_defs_severity    ON "10_kbio"."16_fct_signal_defs" (severity);

COMMENT ON TABLE  "10_kbio"."16_fct_signal_defs" IS
    'Signal definition catalog. One row per registered signal function synced from '
    'the Python signal registry. Signal name, description, function reference, and '
    'default configuration are stored via EAV in 20_dtl_attrs.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".id              IS 'UUID v7 primary key.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".category_id     IS 'FK → 10_dim_signal_categories. Domain category of this signal.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".signal_type_id  IS 'FK → 11_dim_signal_types. Whether the signal produces boolean or score output.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".severity        IS 'Ordinal severity 0-100. Used for listing and priority resolution.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".is_active       IS 'FALSE when the signal is retired from the catalog.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".is_test         IS 'TRUE for sandbox-only signals used in integration tests.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".deleted_at      IS 'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".created_by      IS 'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".updated_by      IS 'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".created_at      IS 'Row creation timestamp (UTC).';
COMMENT ON COLUMN "10_kbio"."16_fct_signal_defs".updated_at      IS 'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "10_kbio"."16_fct_signal_defs" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "10_kbio"."16_fct_signal_defs" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 17_fct_threat_type_defs — Threat type definition catalog (synced from Python)
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."17_fct_threat_type_defs" (
    id          VARCHAR(36)   NOT NULL,
    category_id SMALLINT      NOT NULL,
    action_id   SMALLINT      NOT NULL,
    severity    SMALLINT      NOT NULL DEFAULT 50,
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test     BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at  TIMESTAMP,
    created_by  VARCHAR(36)   NOT NULL,
    updated_by  VARCHAR(36)   NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kbio_fct_threat_type_defs              PRIMARY KEY (id),
    CONSTRAINT fk_kbio_fct_threat_type_defs_category     FOREIGN KEY (category_id)
                                                          REFERENCES "10_kbio"."12_dim_threat_categories" (id),
    CONSTRAINT fk_kbio_fct_threat_type_defs_action       FOREIGN KEY (action_id)
                                                          REFERENCES "10_kbio"."04_dim_drift_actions" (id),
    CONSTRAINT chk_kbio_fct_threat_type_defs_severity    CHECK (severity BETWEEN 0 AND 100)
);

CREATE INDEX idx_kbio_fct_threat_type_defs_category ON "10_kbio"."17_fct_threat_type_defs" (category_id);
CREATE INDEX idx_kbio_fct_threat_type_defs_action   ON "10_kbio"."17_fct_threat_type_defs" (action_id);
CREATE INDEX idx_kbio_fct_threat_type_defs_severity ON "10_kbio"."17_fct_threat_type_defs" (severity);

COMMENT ON TABLE  "10_kbio"."17_fct_threat_type_defs" IS
    'Threat type definition catalog. One row per registered threat type synced from '
    'the Python threat type registry. Threat name, description, signal conditions, '
    'and default configuration are stored via EAV in 20_dtl_attrs.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".id          IS 'UUID v7 primary key.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".category_id IS 'FK → 12_dim_threat_categories. Attack vector category for this threat type.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".action_id   IS 'FK → 04_dim_drift_actions. Default enforcement action (allow, monitor, challenge, block, etc.).';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".severity    IS 'Ordinal severity 0-100. Used for listing and priority resolution.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".is_active   IS 'FALSE when the threat type is retired from the catalog.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".is_test     IS 'TRUE for sandbox-only threat types used in integration tests.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".deleted_at  IS 'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".created_by  IS 'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".updated_by  IS 'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".created_at  IS 'Row creation timestamp (UTC).';
COMMENT ON COLUMN "10_kbio"."17_fct_threat_type_defs".updated_at  IS 'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "10_kbio"."17_fct_threat_type_defs" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "10_kbio"."17_fct_threat_type_defs" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 64_evt_signal_events — Append-only signal evaluation results
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."64_evt_signal_events" (
    id          VARCHAR(36)   NOT NULL,
    session_id  VARCHAR(36)   NOT NULL,
    user_hash   VARCHAR(64)   NOT NULL,
    batch_id    VARCHAR(36)   NOT NULL,
    metadata    JSONB,
    created_by  VARCHAR(36)   NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kbio_evt_signal_events          PRIMARY KEY (id),
    CONSTRAINT uq_kbio_evt_signal_events_batch_id UNIQUE (batch_id)
);

CREATE INDEX idx_kbio_evt_signal_events_session_created ON "10_kbio"."64_evt_signal_events" (session_id, created_at DESC);
CREATE INDEX idx_kbio_evt_signal_events_user_created    ON "10_kbio"."64_evt_signal_events" (user_hash, created_at DESC);

COMMENT ON TABLE  "10_kbio"."64_evt_signal_events" IS
    'Append-only log of signal evaluation results. One row per batch of signals '
    'evaluated by the scoring engine. batch_id provides idempotency — re-delivery of '
    'the same batch must be deduplicated at insert time. No updated_at, no deleted_at.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".id          IS 'UUID v7 primary key.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".session_id  IS 'The session being evaluated. Not a FK — avoids join overhead on hot ingest path.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".user_hash   IS 'Pseudonymous user identifier. Denormalized for fast per-user timeline queries.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".batch_id    IS 'Idempotency key from the SDK batch submission. Must be unique across all signal events.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".metadata    IS 'Signal evaluation detail bag: signal results, scores, thresholds, model version, timing.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".created_by  IS 'UUID of the scoring service that wrote this row.';
COMMENT ON COLUMN "10_kbio"."64_evt_signal_events".created_at  IS 'Row creation timestamp (UTC).';

GRANT SELECT            ON "10_kbio"."64_evt_signal_events" TO tennetctl_read;
GRANT SELECT, INSERT    ON "10_kbio"."64_evt_signal_events" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 65_evt_threat_events — Append-only threat detection results
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."65_evt_threat_events" (
    id                VARCHAR(36)   NOT NULL,
    session_id        VARCHAR(36)   NOT NULL,
    user_hash         VARCHAR(64)   NOT NULL,
    threat_type_code  TEXT          NOT NULL,
    severity_id       SMALLINT      NOT NULL,
    metadata          JSONB,
    created_by        VARCHAR(36)   NOT NULL,
    created_at        TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kbio_evt_threat_events           PRIMARY KEY (id),
    CONSTRAINT fk_kbio_evt_threat_events_severity  FOREIGN KEY (severity_id)
                                                    REFERENCES "10_kbio"."08_dim_alert_severities" (id)
);

CREATE INDEX idx_kbio_evt_threat_events_session_created    ON "10_kbio"."65_evt_threat_events" (session_id, created_at DESC);
CREATE INDEX idx_kbio_evt_threat_events_user_created       ON "10_kbio"."65_evt_threat_events" (user_hash, created_at DESC);
CREATE INDEX idx_kbio_evt_threat_events_threat_type_code   ON "10_kbio"."65_evt_threat_events" (threat_type_code);

COMMENT ON TABLE  "10_kbio"."65_evt_threat_events" IS
    'Append-only log of threat detection results. One row per threat detected by '
    'the threat evaluation engine. threat_type_code is a text reference to the '
    'threat type definition — no FK to allow decoupled sync. No updated_at, no deleted_at.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".id                IS 'UUID v7 primary key.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".session_id        IS 'The session in which the threat was detected. Not a FK — hot ingest path.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".user_hash         IS 'Pseudonymous user identifier. Denormalized for fast per-user threat timeline.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".threat_type_code  IS 'Text reference to the threat type definition code. No FK — allows decoupled sync.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".severity_id       IS 'FK → 08_dim_alert_severities. Alert severity (low, medium, high, critical).';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".metadata          IS 'Threat detection detail bag: matched signals, confidence, recommended action, context.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".created_by        IS 'UUID of the threat evaluation service that wrote this row.';
COMMENT ON COLUMN "10_kbio"."65_evt_threat_events".created_at        IS 'Row creation timestamp (UTC).';

GRANT SELECT            ON "10_kbio"."65_evt_threat_events" TO tennetctl_read;
GRANT SELECT, INSERT    ON "10_kbio"."65_evt_threat_events" TO tennetctl_write;

-- DOWN =======================================================================

-- Drop event tables first (no dependencies)
DROP TABLE IF EXISTS "10_kbio"."65_evt_threat_events";
DROP TABLE IF EXISTS "10_kbio"."64_evt_signal_events";

-- Drop fact tables
DROP TABLE IF EXISTS "10_kbio"."17_fct_threat_type_defs";
DROP TABLE IF EXISTS "10_kbio"."16_fct_signal_defs";

-- Remove attr defs for signal and threat entity types
DELETE FROM "10_kbio"."07_dim_attr_defs"
WHERE entity_type_id IN (
    SELECT id FROM "10_kbio"."06_dim_entity_types"
    WHERE code IN ('kbio_signal_def', 'kbio_threat_type_def')
);

-- Remove entity types
DELETE FROM "10_kbio"."06_dim_entity_types"
WHERE code IN ('kbio_signal_def', 'kbio_threat_type_def');

-- Drop dim tables in reverse creation order
DROP TABLE IF EXISTS "10_kbio"."12_dim_threat_categories";
DROP TABLE IF EXISTS "10_kbio"."11_dim_signal_types";
DROP TABLE IF EXISTS "10_kbio"."10_dim_signal_categories";
