-- UP ====

-- IAM feature-level bootstrap: schema + all dim tables + EAV foundation.
-- Shared infrastructure used by every iam.* sub-feature (orgs, workspaces, users, roles, groups, applications).
-- Sub-feature migrations (002+) add their own fct_* and lnk_* tables.

CREATE SCHEMA IF NOT EXISTS "03_iam";
COMMENT ON SCHEMA "03_iam" IS 'Identity & Access Management — orgs, workspaces, users, roles, groups, scopes, applications.';

-- ── Entity types (EAV key for IAM) ──────────────────────────────────

CREATE TABLE "03_iam"."01_dim_entity_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_entity_types PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_entity_types_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."01_dim_entity_types" IS 'IAM entity categories (org, workspace, user, role, group, application, session). Keys EAV attrs in 21_dtl_attrs.';
COMMENT ON COLUMN "03_iam"."01_dim_entity_types".id IS 'Permanent manual ID. Never renumber. Referenced by dtl_attrs.entity_type_id.';
COMMENT ON COLUMN "03_iam"."01_dim_entity_types".code IS 'Entity category code (e.g. org, workspace, user).';
COMMENT ON COLUMN "03_iam"."01_dim_entity_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."01_dim_entity_types".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."01_dim_entity_types".deprecated_at IS 'Non-null when no longer in use.';

-- ── Account types ───────────────────────────────────────────────────

CREATE TABLE "03_iam"."02_dim_account_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_account_types PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_account_types_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."02_dim_account_types" IS 'Authentication account types (email_password, magic_link, google_oauth, github_oauth).';
COMMENT ON COLUMN "03_iam"."02_dim_account_types".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "03_iam"."02_dim_account_types".code IS 'Account type code.';
COMMENT ON COLUMN "03_iam"."02_dim_account_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."02_dim_account_types".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."02_dim_account_types".deprecated_at IS 'Non-null when deprecated.';

-- ── Scopes ──────────────────────────────────────────────────────────

CREATE TABLE "03_iam"."03_dim_scopes" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    scope_level     TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_scopes PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_scopes_code UNIQUE (code),
    CONSTRAINT chk_iam_dim_scopes_level CHECK (scope_level IN ('global','org'))
);
COMMENT ON TABLE  "03_iam"."03_dim_scopes" IS 'Permission scopes (global: read/write/admin:all; org: read/write/admin:org).';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".code IS 'Scope code (e.g. read:org).';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".scope_level IS 'Where this scope applies: global (cross-org) or org (tenant-scoped).';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."03_dim_scopes".deprecated_at IS 'Non-null when deprecated.';

-- ── Role types ──────────────────────────────────────────────────────

CREATE TABLE "03_iam"."04_dim_role_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_role_types PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_role_types_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."04_dim_role_types" IS 'Role classification: system (built-in) vs custom (org admin-created).';
COMMENT ON COLUMN "03_iam"."04_dim_role_types".id IS 'Permanent manual ID.';
COMMENT ON COLUMN "03_iam"."04_dim_role_types".code IS 'Role type code (system | custom).';
COMMENT ON COLUMN "03_iam"."04_dim_role_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."04_dim_role_types".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."04_dim_role_types".deprecated_at IS 'Non-null when deprecated.';

-- ── EAV attribute definitions ───────────────────────────────────────

CREATE TABLE "03_iam"."20_dtl_attr_defs" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    entity_type_id  SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    value_type      TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dtl_attr_defs PRIMARY KEY (id),
    CONSTRAINT fk_iam_dtl_attr_defs_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "03_iam"."01_dim_entity_types"(id),
    CONSTRAINT chk_iam_dtl_attr_defs_value_type CHECK (value_type IN ('text','jsonb','smallint')),
    CONSTRAINT uq_iam_dtl_attr_defs_entity_code UNIQUE (entity_type_id, code)
);
COMMENT ON TABLE  "03_iam"."20_dtl_attr_defs" IS 'Registered EAV attribute definitions per IAM entity type.';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".id IS 'Auto-generated identity.';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".entity_type_id IS 'Which entity type this attr applies to.';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".code IS 'Attr code (e.g. email, display_name).';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".value_type IS 'Which key_* column carries the value: text | jsonb | smallint.';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."20_dtl_attr_defs".deprecated_at IS 'Non-null when deprecated.';

-- ── EAV attribute values ────────────────────────────────────────────

CREATE TABLE "03_iam"."21_dtl_attrs" (
    id              VARCHAR(36) NOT NULL,
    entity_type_id  SMALLINT NOT NULL,
    entity_id       VARCHAR(36) NOT NULL,
    attr_def_id     SMALLINT NOT NULL,
    key_text        TEXT,
    key_jsonb       JSONB,
    key_smallint    SMALLINT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_dtl_attrs PRIMARY KEY (id),
    CONSTRAINT fk_iam_dtl_attrs_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "03_iam"."01_dim_entity_types"(id),
    CONSTRAINT fk_iam_dtl_attrs_attr_def FOREIGN KEY (attr_def_id)
        REFERENCES "03_iam"."20_dtl_attr_defs"(id),
    CONSTRAINT chk_iam_dtl_attrs_one_value CHECK (
        (CASE WHEN key_text     IS NOT NULL THEN 1 ELSE 0 END)
      + (CASE WHEN key_jsonb    IS NOT NULL THEN 1 ELSE 0 END)
      + (CASE WHEN key_smallint IS NOT NULL THEN 1 ELSE 0 END) = 1
    ),
    CONSTRAINT uq_iam_dtl_attrs_entity_attr UNIQUE (entity_type_id, entity_id, attr_def_id)
);
CREATE INDEX idx_iam_dtl_attrs_entity ON "03_iam"."21_dtl_attrs" (entity_type_id, entity_id);
COMMENT ON TABLE  "03_iam"."21_dtl_attrs" IS 'EAV attribute values for IAM entities. Append-only — no updated_at.';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".entity_type_id IS 'Which dim_entity_types row this attr belongs to.';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".entity_id IS 'UUID v7 of the entity (org / user / etc.).';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".attr_def_id IS 'Which attribute definition.';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".key_text IS 'String value (exactly one key_* non-null).';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".key_jsonb IS 'JSON value.';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".key_smallint IS 'Smallint / dim FK value.';
COMMENT ON COLUMN "03_iam"."21_dtl_attrs".created_at IS 'Insert timestamp (append-only).';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."21_dtl_attrs";
DROP TABLE IF EXISTS "03_iam"."20_dtl_attr_defs";
DROP TABLE IF EXISTS "03_iam"."04_dim_role_types";
DROP TABLE IF EXISTS "03_iam"."03_dim_scopes";
DROP TABLE IF EXISTS "03_iam"."02_dim_account_types";
DROP TABLE IF EXISTS "03_iam"."01_dim_entity_types";
DROP SCHEMA IF EXISTS "03_iam";
