-- =============================================================================
-- Migration:   20260409_026_kprotect_tables.sql
-- Module:      11_kprotect
-- Sub-feature: 00_bootstrap
-- Sequence:    026
-- Depends on:  025 (11_kprotect/00_bootstrap dim tables)
-- Description: Create fact, detail, link, and event tables for kprotect.
--              Policy selections, policy sets, API keys, EAV detail rows,
--              policy-set-to-selection links, and decision event logs.
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 10_fct_policy_selections
-- An org's activation of a predefined kbio policy for inclusion in a set.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."10_fct_policy_selections" (
    id                       VARCHAR(36)   NOT NULL,
    org_id                   VARCHAR(36)   NOT NULL,
    predefined_policy_code   VARCHAR(100)  NOT NULL,
    priority                 INTEGER       NOT NULL DEFAULT 100,
    is_active                BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test                  BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at               TIMESTAMP,
    created_by               VARCHAR(36)   NOT NULL,
    updated_by               VARCHAR(36)   NOT NULL,
    created_at               TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at               TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_fct_policy_selections                PRIMARY KEY (id),
    CONSTRAINT uq_kp_fct_policy_selections_org_policy     UNIQUE (org_id, predefined_policy_code)
);

CREATE INDEX idx_kp_fct_policy_selections_org_id
    ON "11_kprotect"."10_fct_policy_selections" (org_id);
CREATE INDEX idx_kp_fct_policy_selections_policy_code
    ON "11_kprotect"."10_fct_policy_selections" (predefined_policy_code);
CREATE INDEX idx_kp_fct_policy_selections_created_at
    ON "11_kprotect"."10_fct_policy_selections" (created_at DESC);

COMMENT ON TABLE  "11_kprotect"."10_fct_policy_selections" IS
    'An org''s activation of a predefined kbio policy. Each row represents one '
    'org selecting a specific predefined policy code for use in their policy sets. '
    'predefined_policy_code is a text reference (no FK) to the kbio predefined '
    'policy library to avoid cross-schema hard coupling.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".org_id IS
    'Org that owns this policy selection. Scopes the row to the tennetctl IAM org.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".predefined_policy_code IS
    'Code of the predefined policy from the kbio policy library (e.g. geo_velocity_check). '
    'Text reference — no FK to allow decoupled library updates.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".priority IS
    'Evaluation priority within a policy set. Lower numbers run first. Default 100.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".is_active IS
    'FALSE when the policy selection is disabled but not deleted.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".is_test IS
    'TRUE for test/sandbox policy selections excluded from production analytics.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".deleted_at IS
    'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".created_by IS
    'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".updated_by IS
    'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".created_at IS
    'Row creation timestamp (UTC).';
COMMENT ON COLUMN "11_kprotect"."10_fct_policy_selections".updated_at IS
    'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "11_kprotect"."10_fct_policy_selections" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "11_kprotect"."10_fct_policy_selections" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 11_fct_policy_sets
-- An org's named collection of policy selections evaluated as a unit.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."11_fct_policy_sets" (
    id          VARCHAR(36)   NOT NULL,
    org_id      VARCHAR(36)   NOT NULL,
    is_default  BOOLEAN       NOT NULL DEFAULT FALSE,
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test     BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at  TIMESTAMP,
    created_by  VARCHAR(36)   NOT NULL,
    updated_by  VARCHAR(36)   NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_fct_policy_sets      PRIMARY KEY (id)
);

CREATE INDEX idx_kp_fct_policy_sets_org_id
    ON "11_kprotect"."11_fct_policy_sets" (org_id);
CREATE INDEX idx_kp_fct_policy_sets_created_at
    ON "11_kprotect"."11_fct_policy_sets" (created_at DESC);

-- Partial unique index: at most one default set per org (excluding deleted rows).
CREATE UNIQUE INDEX idx_kp_fct_policy_sets_org_default
    ON "11_kprotect"."11_fct_policy_sets" (org_id)
    WHERE is_default = TRUE AND deleted_at IS NULL;

COMMENT ON TABLE  "11_kprotect"."11_fct_policy_sets" IS
    'An org''s named policy set — an ordered collection of policy selections '
    'evaluated as a single unit by the kprotect engine. Name, code, description, '
    'and evaluation_mode are stored in 20_dtl_attrs (EAV). is_default flags the '
    'set used when no explicit policy_set_id is passed to the evaluate endpoint.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".org_id IS
    'Org that owns this policy set. Scopes evaluation to the tennetctl IAM org.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".is_default IS
    'TRUE for the policy set used when the evaluate endpoint omits policy_set_id. '
    'Enforced unique per org via partial index.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".is_active IS
    'FALSE when the policy set is disabled but not deleted.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".is_test IS
    'TRUE for sandbox policy sets excluded from production analytics.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".deleted_at IS
    'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".created_by IS
    'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".updated_by IS
    'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".created_at IS
    'Row creation timestamp (UTC).';
COMMENT ON COLUMN "11_kprotect"."11_fct_policy_sets".updated_at IS
    'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "11_kprotect"."11_fct_policy_sets" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "11_kprotect"."11_fct_policy_sets" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 12_fct_api_keys
-- API key credentials for external callers of the kprotect evaluate endpoint.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."12_fct_api_keys" (
    id          VARCHAR(36)   NOT NULL,
    org_id      VARCHAR(36)   NOT NULL,
    is_active   BOOLEAN       NOT NULL DEFAULT TRUE,
    is_test     BOOLEAN       NOT NULL DEFAULT FALSE,
    deleted_at  TIMESTAMP,
    created_by  VARCHAR(36)   NOT NULL,
    updated_by  VARCHAR(36)   NOT NULL,
    created_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_fct_api_keys      PRIMARY KEY (id)
);

CREATE INDEX idx_kp_fct_api_keys_org_id
    ON "11_kprotect"."12_fct_api_keys" (org_id);
CREATE INDEX idx_kp_fct_api_keys_created_at
    ON "11_kprotect"."12_fct_api_keys" (created_at DESC);

COMMENT ON TABLE  "11_kprotect"."12_fct_api_keys" IS
    'API key credentials that authorise external callers (e.g. SDK integrations) '
    'to invoke the kprotect evaluate endpoint. The raw key is never stored — '
    'key_hash and key_prefix are stored in 20_dtl_attrs via the kp_api_key entity type.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".org_id IS
    'Org that owns this API key. All evaluate calls made with this key are scoped to this org.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".is_active IS
    'FALSE when the key has been revoked. Revoked keys are rejected by the evaluate endpoint.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".is_test IS
    'TRUE for test keys that route to sandbox evaluation logic.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".deleted_at IS
    'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".created_by IS
    'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".updated_by IS
    'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".created_at IS
    'Row creation timestamp (UTC).';
COMMENT ON COLUMN "11_kprotect"."12_fct_api_keys".updated_at IS
    'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "11_kprotect"."12_fct_api_keys" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "11_kprotect"."12_fct_api_keys" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 20_dtl_attrs
-- EAV attribute detail rows. One row per (entity, attribute) pair.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."20_dtl_attrs" (
    id              VARCHAR(36)   NOT NULL,
    org_id          VARCHAR(36)   NOT NULL,
    entity_type_id  SMALLINT      NOT NULL,
    entity_id       VARCHAR(36)   NOT NULL,
    attr_def_id     SMALLINT      NOT NULL,
    key_text        TEXT,
    key_jsonb       JSONB,
    key_smallint    SMALLINT,
    created_by      VARCHAR(36)   NOT NULL,
    updated_by      VARCHAR(36)   NOT NULL,
    created_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_dtl_attrs                   PRIMARY KEY (id),
    CONSTRAINT uq_kp_dtl_attrs_entity_attr        UNIQUE (entity_id, attr_def_id),
    CONSTRAINT fk_kp_dtl_attrs_entity_type        FOREIGN KEY (entity_type_id)
        REFERENCES "11_kprotect"."04_dim_entity_types" (id),
    CONSTRAINT fk_kp_dtl_attrs_attr_def           FOREIGN KEY (attr_def_id)
        REFERENCES "11_kprotect"."05_dim_attr_defs" (id),
    CONSTRAINT chk_kp_dtl_attrs_single_value
        CHECK (
            (key_text IS NOT NULL)::int +
            (key_jsonb IS NOT NULL)::int +
            (key_smallint IS NOT NULL)::int = 1
        )
);

CREATE INDEX idx_kp_dtl_attrs_entity_id
    ON "11_kprotect"."20_dtl_attrs" (entity_id);
CREATE INDEX idx_kp_dtl_attrs_entity_type_id
    ON "11_kprotect"."20_dtl_attrs" (entity_type_id);
CREATE INDEX idx_kp_dtl_attrs_attr_def_id
    ON "11_kprotect"."20_dtl_attrs" (attr_def_id);

COMMENT ON TABLE  "11_kprotect"."20_dtl_attrs" IS
    'EAV attribute rows for kprotect entities. Exactly one of key_text, key_jsonb, '
    'key_smallint must be non-NULL per row (enforced by chk_kp_dtl_attrs_single_value). '
    'Looked up via JOIN on 05_dim_attr_defs to resolve the attribute code.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".org_id IS
    'Org that owns the parent entity. Denormalised for partition pruning.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".entity_type_id IS
    'FK to 04_dim_entity_types. Identifies what kind of entity this attribute belongs to.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".entity_id IS
    'UUID of the parent entity (fct_* table pk).';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".attr_def_id IS
    'FK to 05_dim_attr_defs. Identifies which attribute this row holds.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".key_text IS
    'Text value. Non-NULL when attr_def.value_column = key_text.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".key_jsonb IS
    'JSONB value. Non-NULL when attr_def.value_column = key_jsonb.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".key_smallint IS
    'Smallint value (FK to dim table). Non-NULL when attr_def.value_column = key_smallint.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".created_by IS
    'UUID of the actor or service that created this row.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".updated_by IS
    'UUID of the actor or service that last updated this row.';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".created_at IS
    'Row creation timestamp (UTC).';
COMMENT ON COLUMN "11_kprotect"."20_dtl_attrs".updated_at IS
    'Row last-update timestamp (UTC). Managed by trigger.';

GRANT SELECT                            ON "11_kprotect"."20_dtl_attrs" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "11_kprotect"."20_dtl_attrs" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 40_lnk_policy_set_selections
-- Many-to-many: links policy sets to their member policy selections.
-- Immutable rows (no updated_at per lnk_* convention).
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."40_lnk_policy_set_selections" (
    id                   VARCHAR(36)   NOT NULL,
    org_id               VARCHAR(36)   NOT NULL,
    policy_set_id        VARCHAR(36)   NOT NULL,
    policy_selection_id  VARCHAR(36)   NOT NULL,
    sort_order           INTEGER       NOT NULL DEFAULT 0,
    created_by           VARCHAR(36)   NOT NULL,
    created_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_lnk_policy_set_selections              PRIMARY KEY (id),
    CONSTRAINT uq_kp_lnk_policy_set_selections_pair         UNIQUE (policy_set_id, policy_selection_id),
    CONSTRAINT fk_kp_lnk_policy_set_selections_set          FOREIGN KEY (policy_set_id)
        REFERENCES "11_kprotect"."11_fct_policy_sets" (id),
    CONSTRAINT fk_kp_lnk_policy_set_selections_selection    FOREIGN KEY (policy_selection_id)
        REFERENCES "11_kprotect"."10_fct_policy_selections" (id)
);

CREATE INDEX idx_kp_lnk_policy_set_selections_set_id
    ON "11_kprotect"."40_lnk_policy_set_selections" (policy_set_id);
CREATE INDEX idx_kp_lnk_policy_set_selections_selection_id
    ON "11_kprotect"."40_lnk_policy_set_selections" (policy_selection_id);

COMMENT ON TABLE  "11_kprotect"."40_lnk_policy_set_selections" IS
    'Many-to-many link between policy sets and their member policy selections. '
    'Immutable rows per lnk_* convention — no updated_at column. To reorder, '
    'delete and re-insert with a new sort_order. Ordered by sort_order ASC '
    'during policy set evaluation.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".org_id IS
    'Org that owns this link. Denormalised for partition pruning.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".policy_set_id IS
    'FK to 11_fct_policy_sets. The owning policy set.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".policy_selection_id IS
    'FK to 10_fct_policy_selections. The member policy selection.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".sort_order IS
    'Evaluation order within the policy set. Lower values evaluated first.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".created_by IS
    'UUID of the actor or service that created this link.';
COMMENT ON COLUMN "11_kprotect"."40_lnk_policy_set_selections".created_at IS
    'Row creation timestamp (UTC).';

GRANT SELECT                            ON "11_kprotect"."40_lnk_policy_set_selections" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE    ON "11_kprotect"."40_lnk_policy_set_selections" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 60_evt_decisions
-- Append-only event log of every policy set evaluation outcome.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."60_evt_decisions" (
    id                  VARCHAR(36)   NOT NULL,
    org_id              VARCHAR(36)   NOT NULL,
    session_id          TEXT          NOT NULL,
    user_hash           TEXT,
    device_uuid         TEXT,
    policy_set_id       VARCHAR(36)   NOT NULL,
    outcome_id          SMALLINT      NOT NULL,
    action_id           SMALLINT      NOT NULL,
    total_latency_ms    INTEGER,
    kbio_latency_ms     INTEGER,
    policy_latency_ms   INTEGER,
    metadata            JSONB,
    actor_id            VARCHAR(36)   NOT NULL,
    created_at          TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_evt_decisions              PRIMARY KEY (id),
    CONSTRAINT fk_kp_evt_decisions_outcome      FOREIGN KEY (outcome_id)
        REFERENCES "11_kprotect"."02_dim_decision_outcomes" (id),
    CONSTRAINT fk_kp_evt_decisions_action       FOREIGN KEY (action_id)
        REFERENCES "11_kprotect"."01_dim_action_types" (id)
);

CREATE INDEX idx_kp_evt_decisions_org_id
    ON "11_kprotect"."60_evt_decisions" (org_id);
CREATE INDEX idx_kp_evt_decisions_session_id
    ON "11_kprotect"."60_evt_decisions" (session_id);
CREATE INDEX idx_kp_evt_decisions_policy_set_id
    ON "11_kprotect"."60_evt_decisions" (policy_set_id);
CREATE INDEX idx_kp_evt_decisions_created_at
    ON "11_kprotect"."60_evt_decisions" (created_at DESC);
CREATE INDEX idx_kp_evt_decisions_outcome_id
    ON "11_kprotect"."60_evt_decisions" (outcome_id);

COMMENT ON TABLE  "11_kprotect"."60_evt_decisions" IS
    'Append-only log of every kprotect policy set evaluation. One row per evaluate '
    'call. No updated_at or deleted_at per evt_* convention. Contains latency '
    'breakdowns (total, kbio fetch, policy evaluation) and a metadata JSONB field '
    'for arbitrary engine-emitted signals.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".org_id IS
    'Org context. Scopes the decision to the tennetctl IAM org.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".session_id IS
    'kbio SDK session ID that was being evaluated. Not a FK (cross-schema text reference).';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".user_hash IS
    'Pseudonymous user identifier from the kbio session. May be NULL for anonymous sessions.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".device_uuid IS
    'SDK device identifier from the kbio session. May be NULL.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".policy_set_id IS
    'UUID of the policy set that was evaluated. Text reference retained even if set is deleted.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".outcome_id IS
    'FK to 02_dim_decision_outcomes. Aggregate result of the evaluation.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".action_id IS
    'FK to 01_dim_action_types. The enforcement action taken.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".total_latency_ms IS
    'Total wall-clock latency in milliseconds for the evaluate call.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".kbio_latency_ms IS
    'Latency in milliseconds to fetch behavioral scores from kbio.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".policy_latency_ms IS
    'Latency in milliseconds to run all policy evaluations.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".metadata IS
    'Arbitrary JSON metadata emitted by the engine (e.g. signal snapshot, score at time of eval).';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".actor_id IS
    'UUID of the API key or service account that triggered this evaluation.';
COMMENT ON COLUMN "11_kprotect"."60_evt_decisions".created_at IS
    'Decision timestamp (UTC). Append-only — never updated.';

GRANT SELECT                    ON "11_kprotect"."60_evt_decisions" TO tennetctl_read;
GRANT SELECT, INSERT            ON "11_kprotect"."60_evt_decisions" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 61_evt_decision_details
-- Per-policy breakdown rows for each decision event.
-- ---------------------------------------------------------------------------
CREATE TABLE "11_kprotect"."61_evt_decision_details" (
    id                   VARCHAR(36)   NOT NULL,
    org_id               VARCHAR(36)   NOT NULL,
    decision_id          VARCHAR(36)   NOT NULL,
    policy_selection_id  VARCHAR(36)   NOT NULL,
    action_id            SMALLINT      NOT NULL,
    reason               TEXT,
    execution_ms         INTEGER,
    error_message        TEXT,
    metadata             JSONB,
    actor_id             VARCHAR(36)   NOT NULL,
    created_at           TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_kp_evt_decision_details              PRIMARY KEY (id),
    CONSTRAINT fk_kp_evt_decision_details_decision     FOREIGN KEY (decision_id)
        REFERENCES "11_kprotect"."60_evt_decisions" (id),
    CONSTRAINT fk_kp_evt_decision_details_action       FOREIGN KEY (action_id)
        REFERENCES "11_kprotect"."01_dim_action_types" (id)
);

CREATE INDEX idx_kp_evt_decision_details_decision_id
    ON "11_kprotect"."61_evt_decision_details" (decision_id);
CREATE INDEX idx_kp_evt_decision_details_policy_selection_id
    ON "11_kprotect"."61_evt_decision_details" (policy_selection_id);
CREATE INDEX idx_kp_evt_decision_details_created_at
    ON "11_kprotect"."61_evt_decision_details" (created_at DESC);

COMMENT ON TABLE  "11_kprotect"."61_evt_decision_details" IS
    'Per-policy breakdown of a decision event. One row per policy selection '
    'that was evaluated within a 60_evt_decisions row. Captures the individual '
    'policy action, execution latency, reason text, and any error if the policy '
    'failed to evaluate.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".id IS
    'UUID v7 primary key.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".org_id IS
    'Org context. Denormalised from the parent decision event.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".decision_id IS
    'FK to 60_evt_decisions. The parent decision event this detail belongs to.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".policy_selection_id IS
    'UUID of the policy selection that was evaluated. Retained as text reference '
    'even if the selection is soft-deleted.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".action_id IS
    'FK to 01_dim_action_types. The action this individual policy issued.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".reason IS
    'Human-readable explanation of why this policy fired or passed.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".execution_ms IS
    'Time in milliseconds to evaluate this individual policy.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".error_message IS
    'Error message if the policy evaluation raised an exception. NULL on success.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".metadata IS
    'Arbitrary JSON metadata from the policy evaluator (e.g. matched condition snapshot).';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".actor_id IS
    'UUID of the API key or service account that triggered the parent decision.';
COMMENT ON COLUMN "11_kprotect"."61_evt_decision_details".created_at IS
    'Detail row creation timestamp (UTC). Append-only — never updated.';

GRANT SELECT                    ON "11_kprotect"."61_evt_decision_details" TO tennetctl_read;
GRANT SELECT, INSERT            ON "11_kprotect"."61_evt_decision_details" TO tennetctl_write;

-- DOWN =======================================================================

-- Drop tables in reverse creation order to satisfy FK constraints.
DROP TABLE IF EXISTS "11_kprotect"."61_evt_decision_details";
DROP TABLE IF EXISTS "11_kprotect"."60_evt_decisions";
DROP TABLE IF EXISTS "11_kprotect"."40_lnk_policy_set_selections";
DROP TABLE IF EXISTS "11_kprotect"."20_dtl_attrs";
DROP TABLE IF EXISTS "11_kprotect"."12_fct_api_keys";
DROP TABLE IF EXISTS "11_kprotect"."11_fct_policy_sets";
DROP TABLE IF EXISTS "11_kprotect"."10_fct_policy_selections";
