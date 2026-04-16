-- UP ====

-- Feature 09 (featureflags) — schema + 4 dim tables.
-- fct + lnk tables land in sub-feature migrations (09-02+).

CREATE SCHEMA IF NOT EXISTS "09_featureflags";
COMMENT ON SCHEMA "09_featureflags" IS 'Feature flags — definitions, per-env state, targeting rules, overrides, per-flag RBAC, evaluator.';

-- ── Environments ────────────────────────────────────────────────────

CREATE TABLE "09_featureflags"."01_dim_environments" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_environments PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_environments_code UNIQUE (code)
);
COMMENT ON TABLE  "09_featureflags"."01_dim_environments" IS 'Deployment environments for flag evaluation (dev/staging/prod/test). Extensible via additional rows.';
COMMENT ON COLUMN "09_featureflags"."01_dim_environments".id IS 'Permanent manual id. Never renumber.';
COMMENT ON COLUMN "09_featureflags"."01_dim_environments".code IS 'Environment code (dev, staging, prod, test).';
COMMENT ON COLUMN "09_featureflags"."01_dim_environments".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."01_dim_environments".description IS 'Free-text description.';
COMMENT ON COLUMN "09_featureflags"."01_dim_environments".deprecated_at IS 'Non-null when no longer in use.';

INSERT INTO "09_featureflags"."01_dim_environments" (id, code, label, description) VALUES
    (1, 'dev',     'Development', 'Developer-local and dev-cluster evaluation context'),
    (2, 'staging', 'Staging',     'Pre-production environment; mirrors prod data shape'),
    (3, 'prod',    'Production',  'Live customer-facing environment'),
    (4, 'test',    'Test',        'Automated test suites; always-deterministic flag values')
ON CONFLICT (id) DO NOTHING;

-- ── Value types ─────────────────────────────────────────────────────

CREATE TABLE "09_featureflags"."02_dim_value_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_value_types PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_value_types_code UNIQUE (code)
);
COMMENT ON TABLE  "09_featureflags"."02_dim_value_types" IS 'Flag value types. Evaluator casts flag values based on this dim code.';
COMMENT ON COLUMN "09_featureflags"."02_dim_value_types".id IS 'Permanent manual id.';
COMMENT ON COLUMN "09_featureflags"."02_dim_value_types".code IS 'Value type code (boolean, string, number, json).';
COMMENT ON COLUMN "09_featureflags"."02_dim_value_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."02_dim_value_types".description IS 'Free-text description.';
COMMENT ON COLUMN "09_featureflags"."02_dim_value_types".deprecated_at IS 'Non-null when deprecated.';

INSERT INTO "09_featureflags"."02_dim_value_types" (id, code, label, description) VALUES
    (1, 'boolean', 'Boolean', 'true / false — the simplest toggle'),
    (2, 'string',  'String',  'Free-text value (e.g. variant name)'),
    (3, 'number',  'Number',  'Integer or float (e.g. a percentage)'),
    (4, 'json',    'JSON',    'Arbitrary JSON payload (objects / arrays)')
ON CONFLICT (id) DO NOTHING;

-- ── Flag scopes ─────────────────────────────────────────────────────

CREATE TABLE "09_featureflags"."03_dim_flag_scopes" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_flag_scopes PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_flag_scopes_code UNIQUE (code)
);
COMMENT ON TABLE  "09_featureflags"."03_dim_flag_scopes" IS 'Where a flag applies: global (platform-wide), org (one org), application (one app within an org).';
COMMENT ON COLUMN "09_featureflags"."03_dim_flag_scopes".id IS 'Permanent manual id.';
COMMENT ON COLUMN "09_featureflags"."03_dim_flag_scopes".code IS 'Scope code (global, org, application).';
COMMENT ON COLUMN "09_featureflags"."03_dim_flag_scopes".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."03_dim_flag_scopes".description IS 'Free-text description.';
COMMENT ON COLUMN "09_featureflags"."03_dim_flag_scopes".deprecated_at IS 'Non-null when deprecated.';

INSERT INTO "09_featureflags"."03_dim_flag_scopes" (id, code, label, description) VALUES
    (1, 'global',      'Global',      'Platform-wide flag; visible and evaluable from any context'),
    (2, 'org',         'Org',         'Scoped to a single org; visible only within that org'),
    (3, 'application', 'Application', 'Scoped to a single application (inherits org from the app)')
ON CONFLICT (id) DO NOTHING;

-- ── Flag permissions ────────────────────────────────────────────────

CREATE TABLE "09_featureflags"."04_dim_flag_permissions" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    rank            SMALLINT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_ff_dim_flag_permissions PRIMARY KEY (id),
    CONSTRAINT uq_ff_dim_flag_permissions_code UNIQUE (code),
    CONSTRAINT chk_ff_dim_flag_permissions_rank CHECK (rank BETWEEN 1 AND 4)
);
COMMENT ON TABLE  "09_featureflags"."04_dim_flag_permissions" IS 'Per-flag permission bundle: view / toggle / write / admin. Rank encodes hierarchy (admin>write>toggle>view).';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".id IS 'Permanent manual id.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".code IS 'Permission code.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".label IS 'Human-readable label.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".rank IS 'Hierarchy rank (1=view, 2=toggle, 3=write, 4=admin). Higher rank includes lower-rank capabilities.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".description IS 'Free-text description of what this permission grants.';
COMMENT ON COLUMN "09_featureflags"."04_dim_flag_permissions".deprecated_at IS 'Non-null when deprecated.';

INSERT INTO "09_featureflags"."04_dim_flag_permissions" (id, code, label, rank, description) VALUES
    (1, 'view',   'View',   1, 'Read the flag definition and its current resolved value.'),
    (2, 'toggle', 'Toggle', 2, 'Enable or disable the flag per environment. No other edits.'),
    (3, 'write',  'Write',  3, 'Edit the flag definition, rules, and overrides.'),
    (4, 'admin',  'Admin',  4, 'All edits plus delete and manage per-flag permissions.')
ON CONFLICT (id) DO NOTHING;

-- DOWN ====

DROP TABLE IF EXISTS "09_featureflags"."04_dim_flag_permissions";
DROP TABLE IF EXISTS "09_featureflags"."03_dim_flag_scopes";
DROP TABLE IF EXISTS "09_featureflags"."02_dim_value_types";
DROP TABLE IF EXISTS "09_featureflags"."01_dim_environments";
DROP SCHEMA IF EXISTS "09_featureflags";
