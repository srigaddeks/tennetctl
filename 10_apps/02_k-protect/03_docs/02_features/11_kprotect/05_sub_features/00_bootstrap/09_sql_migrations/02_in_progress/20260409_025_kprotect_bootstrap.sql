-- =============================================================================
-- Migration:   20260409_025_kprotect_bootstrap.sql
-- Module:      11_kprotect
-- Sub-feature: 00_bootstrap
-- Sequence:    025
-- Depends on:  020 (10_kbio/00_bootstrap)
-- Description: Create the 11_kprotect schema with all dimension tables and EAV
--              attribute definitions. This is the schema foundation for the
--              k-protect policy engine. All runtime kprotect tables depend on
--              this migration being applied first.
-- =============================================================================

-- UP =========================================================================

CREATE SCHEMA IF NOT EXISTS "11_kprotect";

GRANT USAGE ON SCHEMA "11_kprotect" TO tennetctl_read;
GRANT USAGE ON SCHEMA "11_kprotect" TO tennetctl_write;

COMMENT ON SCHEMA "11_kprotect" IS
    'Policy engine (kprotect). Owns policy selections, policy sets, API keys, '
    'and decision events for real-time behavioral fraud prevention. Depends on '
    '10_kbio being in place for score inputs. All runtime kprotect HTTP routes '
    'depend on this schema.';

-- ---------------------------------------------------------------------------
-- 01_dim_action_types
-- Enforcement actions the policy engine can take when a policy fires.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."01_dim_action_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kp_dim_action_types       PRIMARY KEY (id),
    CONSTRAINT uq_kp_dim_action_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "11_kprotect"."01_dim_action_types" IS
    'Enforcement actions the kprotect policy engine can issue when a policy '
    'condition is met. Ordered roughly by escalating severity. Extend by INSERT — '
    'never by ALTER.';
COMMENT ON COLUMN "11_kprotect"."01_dim_action_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "11_kprotect"."01_dim_action_types".code IS
    'Stable machine-readable identifier used by the policy runner.';
COMMENT ON COLUMN "11_kprotect"."01_dim_action_types".label IS
    'Human-readable name displayed in the dashboard.';
COMMENT ON COLUMN "11_kprotect"."01_dim_action_types".description IS
    'Optional description of the action semantics.';
COMMENT ON COLUMN "11_kprotect"."01_dim_action_types".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "11_kprotect"."01_dim_action_types" (code, label, description) VALUES
    ('allow',      'Allow',      'Permit the request. No friction applied.'),
    ('challenge',  'Challenge',  'Require the user to complete a behavioral challenge before proceeding.'),
    ('block',      'Block',      'Deny the request entirely. Session may be suspended.'),
    ('monitor',    'Monitor',    'Permit but emit a low-severity signal for analyst review.'),
    ('flag',       'Flag',       'Mark the event for manual investigation without blocking.'),
    ('throttle',   'Throttle',   'Rate-limit the session to reduce attack surface while maintaining access.');

GRANT SELECT ON "11_kprotect"."01_dim_action_types" TO tennetctl_read;
GRANT SELECT ON "11_kprotect"."01_dim_action_types" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 02_dim_decision_outcomes
-- Final outcome recorded for each policy set evaluation.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."02_dim_decision_outcomes" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kp_dim_decision_outcomes       PRIMARY KEY (id),
    CONSTRAINT uq_kp_dim_decision_outcomes_code  UNIQUE (code)
);

COMMENT ON TABLE  "11_kprotect"."02_dim_decision_outcomes" IS
    'Final outcome for a kprotect policy set evaluation event. Combines the '
    'aggregate result of all matched policy rules into a single code. Used for '
    'analytics, reporting, and SLA tracking.';
COMMENT ON COLUMN "11_kprotect"."02_dim_decision_outcomes".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "11_kprotect"."02_dim_decision_outcomes".code IS
    'Stable machine-readable identifier.';
COMMENT ON COLUMN "11_kprotect"."02_dim_decision_outcomes".label IS
    'Human-readable name.';
COMMENT ON COLUMN "11_kprotect"."02_dim_decision_outcomes".description IS
    'Optional description.';
COMMENT ON COLUMN "11_kprotect"."02_dim_decision_outcomes".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "11_kprotect"."02_dim_decision_outcomes" (code, label, description) VALUES
    ('allowed',    'Allowed',    'All evaluated policies passed. Request permitted.'),
    ('challenged', 'Challenged', 'At least one policy issued a challenge action.'),
    ('blocked',    'Blocked',    'At least one policy issued a block action.'),
    ('monitored',  'Monitored',  'Request permitted but flagged for analyst monitoring.'),
    ('error',      'Error',      'Policy evaluation failed due to a runtime error.'),
    ('degraded',   'Degraded',   'Evaluation completed but with partial data (e.g. kbio timeout). Result is advisory only.');

GRANT SELECT ON "11_kprotect"."02_dim_decision_outcomes" TO tennetctl_read;
GRANT SELECT ON "11_kprotect"."02_dim_decision_outcomes" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 03_dim_evaluation_modes
-- Controls how a policy set evaluates its member policies.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."03_dim_evaluation_modes" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kp_dim_evaluation_modes       PRIMARY KEY (id),
    CONSTRAINT uq_kp_dim_evaluation_modes_code  UNIQUE (code)
);

COMMENT ON TABLE  "11_kprotect"."03_dim_evaluation_modes" IS
    'Evaluation strategy for a kprotect policy set. Determines whether the engine '
    'stops at the first matching policy or evaluates all policies before resolving '
    'the final outcome.';
COMMENT ON COLUMN "11_kprotect"."03_dim_evaluation_modes".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "11_kprotect"."03_dim_evaluation_modes".code IS
    'Stable machine-readable identifier used by the policy runner.';
COMMENT ON COLUMN "11_kprotect"."03_dim_evaluation_modes".label IS
    'Human-readable name.';
COMMENT ON COLUMN "11_kprotect"."03_dim_evaluation_modes".description IS
    'Optional description.';
COMMENT ON COLUMN "11_kprotect"."03_dim_evaluation_modes".deprecated_at IS
    'Set when phasing out a row. Rows are never deleted.';

INSERT INTO "11_kprotect"."03_dim_evaluation_modes" (code, label, description) VALUES
    ('short_circuit', 'Short-Circuit', 'Stop evaluating on the first policy that fires. Lowest latency path.'),
    ('all',           'Evaluate All',  'Evaluate every policy in the set regardless of earlier matches. Highest coverage.');

GRANT SELECT ON "11_kprotect"."03_dim_evaluation_modes" TO tennetctl_read;
GRANT SELECT ON "11_kprotect"."03_dim_evaluation_modes" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 04_dim_entity_types
-- Entity-type registry for the kprotect EAV attribute system.
-- Insert order is significant — IDENTITY values are assigned sequentially
-- and are referenced as hard-coded entity_type_id values in 05_dim_attr_defs.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."04_dim_entity_types" (
    id             SMALLINT    GENERATED ALWAYS AS IDENTITY,
    code           TEXT        NOT NULL,
    label          TEXT        NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP,

    CONSTRAINT pk_kp_dim_entity_types       PRIMARY KEY (id),
    CONSTRAINT uq_kp_dim_entity_types_code  UNIQUE (code)
);

COMMENT ON TABLE  "11_kprotect"."04_dim_entity_types" IS
    'Entity-type registry for kprotect EAV attributes. One row per kind of entity '
    'that can own attributes in dtl_attrs. Insert order determines IDENTITY id '
    'values — do not reorder rows.';
COMMENT ON COLUMN "11_kprotect"."04_dim_entity_types".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "11_kprotect"."04_dim_entity_types".code IS
    'Stable machine-readable identifier used by app code.';
COMMENT ON COLUMN "11_kprotect"."04_dim_entity_types".label IS
    'Human-readable name for display in admin UIs.';
COMMENT ON COLUMN "11_kprotect"."04_dim_entity_types".description IS
    'Optional long-form description.';
COMMENT ON COLUMN "11_kprotect"."04_dim_entity_types".deprecated_at IS
    'Set when a row is being phased out. Rows are never deleted.';

-- id=1: kp_policy_selection, id=2: kp_policy_set, id=3: kp_api_key
INSERT INTO "11_kprotect"."04_dim_entity_types" (code, label, description) VALUES
    ('kp_policy_selection', 'KProtect Policy Selection', 'An org''s selection of a predefined policy for inclusion in a policy set.'),
    ('kp_policy_set',       'KProtect Policy Set',       'An ordered collection of policy selections evaluated as a unit by the engine.'),
    ('kp_api_key',          'KProtect API Key',          'An API key credential that authorises external callers to use the kprotect evaluate endpoint.');

GRANT SELECT ON "11_kprotect"."04_dim_entity_types" TO tennetctl_read;
GRANT SELECT ON "11_kprotect"."04_dim_entity_types" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 05_dim_attr_defs
-- EAV attribute registry. Every attribute any dtl_attrs row can reference
-- must be registered here first. entity_type_id is resolved via JOIN on
-- 04_dim_entity_types so the seed does not depend on raw IDENTITY values.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."05_dim_attr_defs" (
    id              SMALLINT    GENERATED ALWAYS AS IDENTITY,
    entity_type_id  SMALLINT    NOT NULL,
    code            TEXT        NOT NULL,
    label           TEXT        NOT NULL,
    description     TEXT,
    value_column    TEXT        NOT NULL,
    deprecated_at   TIMESTAMP,

    CONSTRAINT pk_kp_dim_attr_defs                PRIMARY KEY (id),
    CONSTRAINT uq_kp_dim_attr_defs_entity_code    UNIQUE (entity_type_id, code),
    CONSTRAINT fk_kp_dim_attr_defs_entity_type    FOREIGN KEY (entity_type_id)
        REFERENCES "11_kprotect"."04_dim_entity_types" (id),
    CONSTRAINT chk_kp_dim_attr_defs_value_column
        CHECK (value_column IN ('key_text', 'key_jsonb', 'key_smallint'))
);

CREATE INDEX idx_kp_dim_attr_defs_entity_type
    ON "11_kprotect"."05_dim_attr_defs" (entity_type_id);

COMMENT ON TABLE  "11_kprotect"."05_dim_attr_defs" IS
    'Registered EAV attributes for kprotect entities. Every dtl_attrs row must '
    'reference an entry here. value_column indicates which column in dtl_attrs '
    'carries the value for this attribute.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".id IS
    'Auto-assigned primary key. Permanent — never renumbered.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".entity_type_id IS
    'Which entity type this attribute belongs to. FK to 04_dim_entity_types.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".code IS
    'Attribute identifier, unique within its entity type.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".label IS
    'Human-readable attribute name.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".description IS
    'Optional description of the attribute semantics.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".value_column IS
    'Which key_* column in dtl_attrs holds the value. One of '
    'key_text, key_jsonb, key_smallint.';
COMMENT ON COLUMN "11_kprotect"."05_dim_attr_defs".deprecated_at IS
    'Set when an attribute is being removed. Rows are never deleted.';

-- Seed all attribute definitions. entity_type_id resolved by code JOIN.
INSERT INTO "11_kprotect"."05_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    -- kp_policy_selection (entity_type_id=1)
    ('kp_policy_selection', 'policy_category', 'Policy Category',
     'Category of the predefined policy (e.g. fraud, auth, bot). Copied from kbio catalog at selection time.',
     'key_text'),
    ('kp_policy_selection', 'policy_name', 'Policy Name',
     'Human-readable name of the predefined policy. Copied from kbio catalog at selection time.',
     'key_text'),
    ('kp_policy_selection', 'config_overrides', 'Config Overrides',
     'JSON object of per-org threshold and parameter overrides applied on top of the predefined policy default config.',
     'key_jsonb'),
    ('kp_policy_selection', 'notes', 'Notes',
     'Free-text operator notes about why this policy was selected or how it was customised.',
     'key_text'),
    -- kp_policy_set (entity_type_id=2)
    ('kp_policy_set', 'code', 'Policy Set Code',
     'Stable slug identifier for the policy set (e.g. fraud_standard).',
     'key_text'),
    ('kp_policy_set', 'name', 'Policy Set Name',
     'Human-readable display name for the policy set.',
     'key_text'),
    ('kp_policy_set', 'description', 'Policy Set Description',
     'Full description of the policy set purpose and intended use case.',
     'key_text'),
    ('kp_policy_set', 'evaluation_mode', 'Evaluation Mode',
     'How the engine evaluates member policies: short_circuit or all.',
     'key_text'),
    -- kp_api_key (entity_type_id=3)
    ('kp_api_key', 'key_hash', 'Key Hash',
     'SHA-256 hash of the raw API key. The raw key is never stored.',
     'key_text'),
    ('kp_api_key', 'key_prefix', 'Key Prefix',
     'First 8 characters of the raw key, used for identification in the UI.',
     'key_text'),
    ('kp_api_key', 'label', 'Label',
     'Human-readable label assigned by the operator (e.g. production-sdk).',
     'key_text'),
    ('kp_api_key', 'expires_at', 'Expires At',
     'ISO-8601 timestamp after which this key is no longer valid. NULL means no expiry.',
     'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "11_kprotect"."04_dim_entity_types" et ON et.code = x.entity_code;

GRANT SELECT ON "11_kprotect"."05_dim_attr_defs" TO tennetctl_read;
GRANT SELECT ON "11_kprotect"."05_dim_attr_defs" TO tennetctl_write;

-- DOWN =======================================================================

-- Drop tables in reverse creation order to satisfy FK constraints.
DROP TABLE IF EXISTS "11_kprotect"."05_dim_attr_defs";
DROP TABLE IF EXISTS "11_kprotect"."04_dim_entity_types";
DROP TABLE IF EXISTS "11_kprotect"."03_dim_evaluation_modes";
DROP TABLE IF EXISTS "11_kprotect"."02_dim_decision_outcomes";
DROP TABLE IF EXISTS "11_kprotect"."01_dim_action_types";
DROP SCHEMA IF EXISTS "11_kprotect";
