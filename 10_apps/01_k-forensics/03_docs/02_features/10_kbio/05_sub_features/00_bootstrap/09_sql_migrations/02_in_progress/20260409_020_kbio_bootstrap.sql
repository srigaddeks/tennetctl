-- =============================================================================
-- Migration:   20260409_020_kbio_bootstrap.sql
-- Module:      10_kbio
-- Sub-feature: 00_bootstrap
-- Sequence:    020
-- Depends on:  003 (03_iam/00_bootstrap)
-- Description: Create the 10_kbio schema with all dimension tables, EAV
--              attribute definitions, and seed rows for behavioral biometrics.
--              This migration is the schema foundation for k-forensics behavioral
--              intelligence. All runtime kbio tables depend on this being in place.
-- =============================================================================

-- UP =========================================================================

CREATE SCHEMA IF NOT EXISTS "10_kbio";

GRANT USAGE ON SCHEMA "10_kbio" TO tennetctl_read;
GRANT USAGE ON SCHEMA "10_kbio" TO tennetctl_write;

COMMENT ON SCHEMA "10_kbio" IS
    'Behavioral intelligence (kbio). Owns sessions, devices, user profiles, '
    'trusted entities, challenges, and predefined policy definitions. Depends on '
    '03_iam being in place. All runtime kbio HTTP routes depend on this schema.';

-- ---------------------------------------------------------------------------
-- 01_dim_session_statuses
-- Lifecycle states for a kbio behavioral session.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."01_dim_session_statuses" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_session_statuses       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_session_statuses_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."01_dim_session_statuses" IS
    'Lifecycle status for a kbio behavioral session. active = biometric '
    'collection in progress; suspended = temporarily paused; terminated = '
    'session ended and archived.';
COMMENT ON COLUMN "10_kbio"."01_dim_session_statuses".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."01_dim_session_statuses".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."01_dim_session_statuses".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."01_dim_session_statuses".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."01_dim_session_statuses".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."01_dim_session_statuses" (code, label, description) VALUES
    ('active',      'Active',      'Behavioral session is open and receiving pulse batches.'),
    ('suspended',   'Suspended',   'Session is temporarily paused. Pulses are held pending resumption.'),
    ('terminated',  'Terminated',  'Session has ended. No further pulses accepted. Final scores recorded.');

GRANT SELECT ON "10_kbio"."01_dim_session_statuses" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."01_dim_session_statuses" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 02_dim_batch_types
-- Classifies the purpose of each pulse batch submitted to a kbio session.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."02_dim_batch_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_batch_types       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_batch_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."02_dim_batch_types" IS
    'Classifies the purpose of each pulse batch submitted to a kbio session. '
    'Determines scoring path and retention policy for the batch.';
COMMENT ON COLUMN "10_kbio"."02_dim_batch_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."02_dim_batch_types".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."02_dim_batch_types".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."02_dim_batch_types".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."02_dim_batch_types".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."02_dim_batch_types" (code, label, description) VALUES
    ('behavioral',          'Behavioral',          'Standard ongoing behavioral biometric sample batch.'),
    ('critical_action',     'Critical Action',     'Batch captured during a high-risk user action (e.g. fund transfer, password change).'),
    ('keepalive',           'Keepalive',           'Lightweight heartbeat batch that extends session liveness without full scoring.'),
    ('session_start',       'Session Start',       'First batch upon session creation. Initialises scoring context.'),
    ('session_end',         'Session End',         'Final batch sent when the SDK closes the session gracefully.'),
    ('device_fingerprint',  'Device Fingerprint',  'Batch carrying device fingerprint signals for device-identity resolution.');

GRANT SELECT ON "10_kbio"."02_dim_batch_types" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."02_dim_batch_types" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 03_dim_trust_levels
-- Categorical trust assessment assigned to a session or user profile after
-- drift scoring.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."03_dim_trust_levels" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_trust_levels       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_trust_levels_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."03_dim_trust_levels" IS
    'Categorical trust assessment derived from behavioral drift scoring. '
    'Drives downstream policy evaluation and action selection.';
COMMENT ON COLUMN "10_kbio"."03_dim_trust_levels".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."03_dim_trust_levels".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."03_dim_trust_levels".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."03_dim_trust_levels".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."03_dim_trust_levels".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."03_dim_trust_levels" (code, label, description) VALUES
    ('trusted',     'Trusted',     'Drift score is within normal bounds. Behaviour matches the enrolled profile.'),
    ('suspicious',  'Suspicious',  'Drift score is elevated. Behaviour deviates measurably from the profile.'),
    ('anomalous',   'Anomalous',   'Drift score exceeds anomaly threshold. Strong signal of impostor or automation.');

GRANT SELECT ON "10_kbio"."03_dim_trust_levels" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."03_dim_trust_levels" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 04_dim_drift_actions
-- Enforcement actions that can be taken when a drift score or policy
-- evaluation produces a decision. Shared by both real-time drift and the
-- predefined policy library.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."04_dim_drift_actions" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_drift_actions       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_drift_actions_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."04_dim_drift_actions" IS
    'Enforcement actions available to drift scoring and predefined policies. '
    'Ordered roughly by escalating severity. Extend by INSERT — never by ALTER.';
COMMENT ON COLUMN "10_kbio"."04_dim_drift_actions".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."04_dim_drift_actions".code IS
    'Stable machine-readable identifier used by the scoring engine and policy runner.';
COMMENT ON COLUMN "10_kbio"."04_dim_drift_actions".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."04_dim_drift_actions".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."04_dim_drift_actions".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."04_dim_drift_actions" (code, label, description) VALUES
    ('allow',      'Allow',      'Permit the action with no friction. Trust is confirmed.'),
    ('monitor',    'Monitor',    'Permit but emit a low-severity alert for analyst review.'),
    ('challenge',  'Challenge',  'Require the user to complete a behavioral challenge before proceeding.'),
    ('block',      'Block',      'Deny the action entirely. Session may be suspended or terminated.'),
    ('flag',       'Flag',       'Mark the session or event for manual investigation without blocking.'),
    ('throttle',   'Throttle',   'Rate-limit the session to reduce attack surface while maintaining access.');

GRANT SELECT ON "10_kbio"."04_dim_drift_actions" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."04_dim_drift_actions" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 05_dim_baseline_qualities
-- Maturity level of the enrolled behavioral baseline for a user profile.
-- Determines whether drift scoring is reliable enough to make decisions.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."05_dim_baseline_qualities" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_baseline_qualities       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_baseline_qualities_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."05_dim_baseline_qualities" IS
    'Maturity level of the behavioral baseline for a user profile. '
    'insufficient and forming indicate the encoder needs more data before '
    'drift scoring can be trusted. established and strong allow full policy enforcement.';
COMMENT ON COLUMN "10_kbio"."05_dim_baseline_qualities".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."05_dim_baseline_qualities".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."05_dim_baseline_qualities".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."05_dim_baseline_qualities".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."05_dim_baseline_qualities".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."05_dim_baseline_qualities" (code, label, description) VALUES
    ('insufficient',  'Insufficient',  'Fewer sessions than the minimum enrollment threshold. Scoring disabled.'),
    ('forming',       'Forming',       'Minimum threshold met but variance is still high. Scores are advisory only.'),
    ('established',   'Established',   'Sufficient sessions with stable variance. Scores are reliable for policy enforcement.'),
    ('strong',        'Strong',        'Large session corpus with very low variance. High-confidence scores. Strict policies enabled.');

GRANT SELECT ON "10_kbio"."05_dim_baseline_qualities" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."05_dim_baseline_qualities" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 06_dim_entity_types
-- Entity-type registry for the kbio EAV attribute system.
-- Insert order is significant — IDENTITY values are assigned sequentially
-- and are referenced as hard-coded entity_type_id values in 07_dim_attr_defs.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."06_dim_entity_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_entity_types       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_entity_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."06_dim_entity_types" IS
    'Entity-type registry for kbio EAV attributes. One row per kind of entity '
    'that can own attributes in dtl_attrs. Insert order determines IDENTITY id '
    'values — do not reorder rows.';
COMMENT ON COLUMN "10_kbio"."06_dim_entity_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."06_dim_entity_types".code IS
    'Stable machine-readable identifier used by app code.';
COMMENT ON COLUMN "10_kbio"."06_dim_entity_types".label IS
    'Human-readable name for display in admin UIs.';
COMMENT ON COLUMN "10_kbio"."06_dim_entity_types".description IS
    'Optional long-form description.';
COMMENT ON COLUMN "10_kbio"."06_dim_entity_types".deprecated_at IS
    'Set when a row is being phased out. Rows are never deleted.';

-- id=1: kbio_session, id=2: kbio_device, id=3: kbio_user_profile,
-- id=4: kbio_trusted_entity, id=5: kbio_challenge, id=6: kbio_predefined_policy
INSERT INTO "10_kbio"."06_dim_entity_types" (code, label, description) VALUES
    ('kbio_session',           'kBio Session',           'A behavioral biometric monitoring session bound to an IAM session.'),
    ('kbio_device',            'kBio Device',            'A device fingerprint record linked to one or more kbio sessions.'),
    ('kbio_user_profile',      'kBio User Profile',      'Per-user behavioral baseline: centroids, zone transition matrix, and credential profiles.'),
    ('kbio_trusted_entity',    'kBio Trusted Entity',    'An entity (device, IP, location, network) explicitly trusted for a user.'),
    ('kbio_challenge',         'kBio Challenge',         'A one-time behavioral challenge issued to verify user identity mid-session.'),
    ('kbio_predefined_policy', 'kBio Predefined Policy', 'A system-defined reusable policy template from the predefined policy library.');

GRANT SELECT ON "10_kbio"."06_dim_entity_types" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."06_dim_entity_types" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 06_dim_policy_categories
-- Thematic categories used to organise predefined policies in the library.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."06_dim_policy_categories" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_policy_categories       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_policy_categories_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."06_dim_policy_categories" IS
    'Thematic groupings for the predefined policy library. Policies are tagged '
    'with one or more categories to aid discovery and organisation in the UI.';
COMMENT ON COLUMN "10_kbio"."06_dim_policy_categories".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."06_dim_policy_categories".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."06_dim_policy_categories".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."06_dim_policy_categories".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."06_dim_policy_categories".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."06_dim_policy_categories" (code, label, description) VALUES
    ('fraud',       'Fraud',       'Policies that detect and respond to fraudulent transaction or account activity.'),
    ('auth',        'Auth',        'Policies governing step-up authentication and re-verification requirements.'),
    ('bot',         'Bot',         'Policies targeting automated script and bot behavior detection.'),
    ('compliance',  'Compliance',  'Policies enforcing regulatory or contractual obligations (e.g. SOC 2, PCI DSS).'),
    ('risk',        'Risk',        'General risk-scoring and risk-threshold enforcement policies.'),
    ('trust',       'Trust',       'Policies that manage trusted entity allowlists and trust decay schedules.'),
    ('session',     'Session',     'Policies governing session lifetime, idle timeout, and session-level anomalies.'),
    ('geo',         'Geo',         'Policies based on geographic location, country, or network topology signals.'),
    ('credential',  'Credential',  'Policies monitoring credential stuffing, password change velocity, and MFA bypass attempts.');

GRANT SELECT ON "10_kbio"."06_dim_policy_categories" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."06_dim_policy_categories" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 07_dim_attr_defs
-- EAV attribute registry. Every attribute any dtl_attrs row can reference
-- must be registered here first. entity_type_id is resolved via JOIN on
-- 06_dim_entity_types so the seed does not depend on raw IDENTITY values.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."07_dim_attr_defs" (
    id              SMALLINT    GENERATED ALWAYS AS IDENTITY,
    entity_type_id  SMALLINT    NOT NULL,
    code            TEXT        NOT NULL,
    label           TEXT        NOT NULL,
    description     TEXT,
    value_column    TEXT        NOT NULL,
    deprecated_at   TIMESTAMP,

    CONSTRAINT pk_kbio_dim_attr_defs                PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_attr_defs_entity_code    UNIQUE (entity_type_id, code),
    CONSTRAINT fk_kbio_dim_attr_defs_entity_type    FOREIGN KEY (entity_type_id)
        REFERENCES "10_kbio"."06_dim_entity_types" (id),
    CONSTRAINT chk_kbio_dim_attr_defs_value_column
        CHECK (value_column IN ('key_text', 'key_jsonb', 'key_smallint'))
);

CREATE INDEX idx_kbio_dim_attr_defs_entity_type
    ON "10_kbio"."07_dim_attr_defs" (entity_type_id);

COMMENT ON TABLE  "10_kbio"."07_dim_attr_defs" IS
    'Registered EAV attributes for kbio entities. Every dtl_attrs row must '
    'reference an entry here. value_column indicates which column in dtl_attrs '
    'carries the value for this attribute.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".entity_type_id IS
    'Which entity type this attribute belongs to. FK to 06_dim_entity_types.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".code IS
    'Attribute identifier, unique within its entity type.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".label IS
    'Human-readable attribute name.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".description IS
    'Optional description of the attribute semantics.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".value_column IS
    'Which key_* column in dtl_attrs holds the value. One of '
    'key_text, key_jsonb, key_smallint.';
COMMENT ON COLUMN "10_kbio"."07_dim_attr_defs".deprecated_at IS
    'Set when an attribute is being removed. Rows are never deleted.';

-- Seed all attribute definitions. entity_type_id is resolved by code via JOIN
-- so the seed does not depend on insertion-order IDENTITY values.
INSERT INTO "10_kbio"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    -- kbio_session (9 attrs)
    ('kbio_session', 'ip_address',            'IP Address',            'IP address of the client at session creation time.',                                         'key_text'),
    ('kbio_session', 'user_agent',            'User Agent',            'HTTP User-Agent header at session creation time.',                                           'key_text'),
    ('kbio_session', 'sdk_version',           'SDK Version',           'Version string of the kbio SDK used to create this session.',                               'key_text'),
    ('kbio_session', 'sdk_platform',          'SDK Platform',          'Platform identifier reported by the SDK (e.g. web, ios, android).',                        'key_text'),
    ('kbio_session', 'total_pulses',          'Total Pulses',          'Cumulative count of behavioral pulses received across all batches.',                        'key_text'),
    ('kbio_session', 'max_drift_score',       'Max Drift Score',       'Highest drift score observed across all scoring rounds in this session.',                   'key_text'),
    ('kbio_session', 'current_drift_score',   'Current Drift Score',   'Most recent drift score from the last completed scoring round.',                            'key_text'),
    ('kbio_session', 'critical_actions',      'Critical Actions',      'Array of critical-action records captured during the session.',                             'key_jsonb'),
    ('kbio_session', 'end_reason',            'End Reason',            'Human-readable reason the session was terminated (e.g. logout, timeout, block).',          'key_text'),
    -- kbio_device (7 attrs)
    ('kbio_device', 'fingerprint_hash',       'Fingerprint Hash',      'SHA-256 hash of the canonical device fingerprint payload.',                                 'key_text'),
    ('kbio_device', 'first_seen_at',          'First Seen At',         'ISO-8601 timestamp of the first session that identified this device.',                     'key_text'),
    ('kbio_device', 'last_seen_at',           'Last Seen At',          'ISO-8601 timestamp of the most recent session that identified this device.',               'key_text'),
    ('kbio_device', 'platform',               'Platform',              'OS/platform reported by the device fingerprint (e.g. Windows, macOS, iOS).',               'key_text'),
    ('kbio_device', 'screen_profile',         'Screen Profile',        'JSON object with screen resolution, color depth, and pixel ratio.',                        'key_jsonb'),
    ('kbio_device', 'gpu_profile',            'GPU Profile',           'JSON object with WebGL renderer and vendor strings.',                                       'key_jsonb'),
    ('kbio_device', 'automation_risk',        'Automation Risk Score', 'Floating-point score (0–1) indicating likelihood of automated/bot client.',                'key_text'),
    -- kbio_user_profile (7 attrs)
    ('kbio_user_profile', 'centroids',                    'Behavioral Centroids',      'JSON array of learned cluster centroids from the behavioral encoder.',      'key_jsonb'),
    ('kbio_user_profile', 'zone_transition_matrix',       'Zone Transition Matrix',    'JSON matrix of inter-zone transition probabilities.',                       'key_jsonb'),
    ('kbio_user_profile', 'credential_profiles',          'Credential Profiles',       'JSON array of per-credential typing and timing profiles.',                  'key_jsonb'),
    ('kbio_user_profile', 'profile_maturity',             'Profile Maturity',          'Current baseline quality code (see 05_dim_baseline_qualities).',            'key_text'),
    ('kbio_user_profile', 'total_sessions',               'Total Sessions',            'Cumulative count of sessions contributed to this profile.',                 'key_text'),
    ('kbio_user_profile', 'last_genuine_session_at',      'Last Genuine Session',      'ISO-8601 timestamp of the last session scored as trusted.',                 'key_text'),
    ('kbio_user_profile', 'encoder_version',              'Encoder Version',           'Version of the behavioral encoder model used to build this profile.',      'key_text'),
    -- kbio_trusted_entity (4 attrs)
    ('kbio_trusted_entity', 'entity_value',   'Entity Value',          'The raw value being trusted (e.g. IP string, device fingerprint hash).',                   'key_text'),
    ('kbio_trusted_entity', 'trust_reason',   'Trust Reason',          'Free-text explanation of why this entity was trusted.',                                    'key_text'),
    ('kbio_trusted_entity', 'trusted_by',     'Trusted By Actor',      'UUID of the IAM user who granted trust for this entity.',                                  'key_text'),
    ('kbio_trusted_entity', 'expires_at',     'Expiry',                'ISO-8601 timestamp after which this trust entry is no longer valid.',                      'key_text'),
    -- kbio_challenge (10 attrs)
    ('kbio_challenge', 'purpose',                     'Challenge Purpose',       'Reason the challenge was issued (e.g. elevated_drift, critical_action).',        'key_text'),
    ('kbio_challenge', 'phrase',                      'Challenge Phrase',        'Plaintext phrase the user is asked to type during the challenge.',                'key_text'),
    ('kbio_challenge', 'phrase_hash',                 'Phrase Hash',             'SHA-256 hash of the challenge phrase for integrity verification.',               'key_text'),
    ('kbio_challenge', 'expected_zone_sequence',      'Expected Zone Sequence',  'JSON array of expected behavioral zone transitions for this phrase.',             'key_jsonb'),
    ('kbio_challenge', 'discriminative_pairs',        'Discriminative Pairs',    'JSON array of key-pair sequences with highest discriminative power.',             'key_jsonb'),
    ('kbio_challenge', 'pair_weights',                'Pair Weights',            'JSON object mapping each discriminative pair to its scoring weight.',             'key_jsonb'),
    ('kbio_challenge', 'expires_at',                  'Challenge Expiry',        'ISO-8601 timestamp after which the challenge is no longer valid.',               'key_text'),
    ('kbio_challenge', 'used',                        'Challenge Used',          'Boolean string (true/false) — whether the challenge was consumed.',              'key_text'),
    ('kbio_challenge', 'result_passed',               'Result Passed',           'Boolean string (true/false) — outcome of the challenge evaluation.',             'key_text'),
    ('kbio_challenge', 'result_drift_score',          'Result Drift Score',      'Drift score computed from the challenge response submission.',                    'key_text'),
    -- kbio_predefined_policy (7 attrs)
    ('kbio_predefined_policy', 'code',            'Policy Code',           'Stable slug identifier for the policy (e.g. geo_velocity_check).',                    'key_text'),
    ('kbio_predefined_policy', 'name',            'Policy Name',           'Human-readable name shown in the policy library UI.',                                  'key_text'),
    ('kbio_predefined_policy', 'description',     'Policy Description',    'Full description of what the policy detects and how it responds.',                     'key_text'),
    ('kbio_predefined_policy', 'conditions',      'Policy Conditions',     'JSON object defining the signal conditions that trigger this policy.',                 'key_jsonb'),
    ('kbio_predefined_policy', 'default_config',  'Default Configuration', 'JSON object with default thresholds and parameter values for the policy.',             'key_jsonb'),
    ('kbio_predefined_policy', 'tags',            'Tags',                  'Comma-separated category codes from 06_dim_policy_categories.',                        'key_text'),
    ('kbio_predefined_policy', 'version',         'Policy Version',        'Semver string of the policy definition (e.g. 1.0.0).',                                'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "10_kbio"."06_dim_entity_types" et ON et.code = x.entity_code;

GRANT SELECT ON "10_kbio"."07_dim_attr_defs" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."07_dim_attr_defs" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 08_dim_alert_severities
-- Severity levels for alerts emitted by the kbio scoring engine and
-- policy runner.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."08_dim_alert_severities" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_alert_severities       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_alert_severities_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."08_dim_alert_severities" IS
    'Severity classification for alerts raised by the kbio scoring engine '
    'and predefined policy evaluations. Drives notification routing and '
    'analyst queue prioritisation.';
COMMENT ON COLUMN "10_kbio"."08_dim_alert_severities".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."08_dim_alert_severities".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."08_dim_alert_severities".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."08_dim_alert_severities".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."08_dim_alert_severities".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."08_dim_alert_severities" (code, label, description) VALUES
    ('low',       'Low',       'Informational signal. No immediate action required. Logged for trend analysis.'),
    ('medium',    'Medium',    'Notable deviation. Warrants analyst review within normal SLA.'),
    ('high',      'High',      'Significant anomaly or policy breach. Expedited analyst review required.'),
    ('critical',  'Critical',  'Severe threat signal. Immediate automated response and analyst escalation triggered.');

GRANT SELECT ON "10_kbio"."08_dim_alert_severities" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."08_dim_alert_severities" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 09_dim_trusted_entity_types
-- Classifies the kind of entity recorded in a kbio_trusted_entity row.
-- ---------------------------------------------------------------------------
CREATE TABLE "10_kbio"."09_dim_trusted_entity_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kbio_dim_trusted_entity_types       PRIMARY KEY (id),
    CONSTRAINT uq_kbio_dim_trusted_entity_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "10_kbio"."09_dim_trusted_entity_types" IS
    'Type of entity that can appear in the kbio trusted-entity allowlist. '
    'Determines how the entity_value attribute is interpreted and validated.';
COMMENT ON COLUMN "10_kbio"."09_dim_trusted_entity_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "10_kbio"."09_dim_trusted_entity_types".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "10_kbio"."09_dim_trusted_entity_types".label IS
    'Human-readable name.';
COMMENT ON COLUMN "10_kbio"."09_dim_trusted_entity_types".description IS
    'Optional description.';
COMMENT ON COLUMN "10_kbio"."09_dim_trusted_entity_types".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "10_kbio"."09_dim_trusted_entity_types" (code, label, description) VALUES
    ('device',      'Device',      'A specific device identified by its fingerprint hash.'),
    ('ip_address',  'IP Address',  'A specific IPv4 or IPv6 address.'),
    ('location',    'Location',    'A geographic location identified by country code or city.'),
    ('network',     'Network',     'A CIDR network block or ASN.');

GRANT SELECT ON "10_kbio"."09_dim_trusted_entity_types" TO tennetctl_read;
GRANT SELECT ON "10_kbio"."09_dim_trusted_entity_types" TO tennetctl_write;

-- DOWN =======================================================================

-- Drop tables in reverse creation order to satisfy FK constraints.
DROP TABLE IF EXISTS "10_kbio"."07_dim_attr_defs";
DROP TABLE IF EXISTS "10_kbio"."09_dim_trusted_entity_types";
DROP TABLE IF EXISTS "10_kbio"."08_dim_alert_severities";
DROP TABLE IF EXISTS "10_kbio"."06_dim_policy_categories";
DROP TABLE IF EXISTS "10_kbio"."06_dim_entity_types";
DROP TABLE IF EXISTS "10_kbio"."05_dim_baseline_qualities";
DROP TABLE IF EXISTS "10_kbio"."04_dim_drift_actions";
DROP TABLE IF EXISTS "10_kbio"."03_dim_trust_levels";
DROP TABLE IF EXISTS "10_kbio"."02_dim_batch_types";
DROP TABLE IF EXISTS "10_kbio"."01_dim_session_statuses";
DROP SCHEMA IF EXISTS "10_kbio";
