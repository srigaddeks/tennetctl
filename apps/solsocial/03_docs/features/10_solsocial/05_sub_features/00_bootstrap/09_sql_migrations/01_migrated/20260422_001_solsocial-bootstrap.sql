-- UP ====

-- SolSocial schema + shared dim tables. Seeds live under
-- 00_bootstrap/09_sql_migrations/seeds/*.yaml and are applied by
-- `python -m backend.01_migrator.runner seed --root apps/solsocial`.

CREATE SCHEMA IF NOT EXISTS "10_solsocial";
COMMENT ON SCHEMA "10_solsocial" IS 'SolSocial business domain — channels, posts, queues, ideas, local RBAC.';

-- ========================================================================
-- DIM tables (01-09). Seeded via YAML seeds. Never mutated at runtime.
-- Mandatory cols: id, code, label, description, deprecated_at.
-- ========================================================================

CREATE TABLE "10_solsocial"."01_dim_channel_providers" (
    id            SMALLINT NOT NULL,
    code          TEXT NOT NULL,
    label         TEXT NOT NULL,
    description   TEXT,
    deprecated_at TIMESTAMP,
    CONSTRAINT pk_solsocial_dim_channel_providers PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_dim_channel_providers_code UNIQUE (code)
);
COMMENT ON TABLE  "10_solsocial"."01_dim_channel_providers" IS 'Supported social providers. v1: linkedin, twitter, instagram.';
COMMENT ON COLUMN "10_solsocial"."01_dim_channel_providers".id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "10_solsocial"."01_dim_channel_providers".code IS 'Provider code used by adapters (linkedin/twitter/instagram).';

CREATE TABLE "10_solsocial"."02_dim_post_statuses" (
    id            SMALLINT NOT NULL,
    code          TEXT NOT NULL,
    label         TEXT NOT NULL,
    description   TEXT,
    deprecated_at TIMESTAMP,
    CONSTRAINT pk_solsocial_dim_post_statuses PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_dim_post_statuses_code UNIQUE (code)
);
COMMENT ON TABLE  "10_solsocial"."02_dim_post_statuses" IS 'Post lifecycle statuses. Transitions are enforced in service.py.';
COMMENT ON COLUMN "10_solsocial"."02_dim_post_statuses".code IS 'Status code: draft|queued|scheduled|publishing|published|failed.';

CREATE TABLE "10_solsocial"."03_dim_permissions" (
    id            SMALLINT NOT NULL,
    code          TEXT NOT NULL,
    label         TEXT NOT NULL,
    description   TEXT,
    deprecated_at TIMESTAMP,
    CONSTRAINT pk_solsocial_dim_permissions PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_dim_permissions_code UNIQUE (code)
);
COMMENT ON TABLE  "10_solsocial"."03_dim_permissions" IS 'SolSocial-local action catalog. Does NOT overlap with tennetctl scopes.';
COMMENT ON COLUMN "10_solsocial"."03_dim_permissions".code IS 'Dotted permission code, e.g. posts.publish or channels.connect.';

CREATE TABLE "10_solsocial"."04_dim_roles" (
    id            SMALLINT NOT NULL,
    code          TEXT NOT NULL,
    label         TEXT NOT NULL,
    description   TEXT,
    deprecated_at TIMESTAMP,
    CONSTRAINT pk_solsocial_dim_roles PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_dim_roles_code UNIQUE (code)
);
COMMENT ON TABLE  "10_solsocial"."04_dim_roles" IS 'SolSocial role templates. Assigned per tennetctl-user per tennetctl-workspace.';

CREATE TABLE "10_solsocial"."05_dim_features" (
    id            SMALLINT NOT NULL,
    code          TEXT NOT NULL,
    label         TEXT NOT NULL,
    description   TEXT,
    deprecated_at TIMESTAMP,
    is_stable     BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_solsocial_dim_features PRIMARY KEY (id),
    CONSTRAINT uq_solsocial_dim_features_code UNIQUE (code)
);
COMMENT ON TABLE  "10_solsocial"."05_dim_features" IS 'SolSocial product feature catalog. Workspaces opt in/out via fct_workspace_features.';
COMMENT ON COLUMN "10_solsocial"."05_dim_features".is_stable IS 'If true, feature is on by default for new workspaces.';

-- DOWN ====

DROP SCHEMA IF EXISTS "10_solsocial" CASCADE;
