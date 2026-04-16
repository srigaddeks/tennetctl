-- UP ====

-- featureflags.flags — flag definitions + per-environment state.

CREATE TABLE "09_featureflags"."10_fct_flags" (
    id                      VARCHAR(36) NOT NULL,
    scope_id                SMALLINT NOT NULL,
    org_id                  VARCHAR(36),
    application_id          VARCHAR(36),
    flag_key                TEXT NOT NULL,
    value_type_id           SMALLINT NOT NULL,
    default_value_jsonb     JSONB NOT NULL,
    description             TEXT,
    is_active               BOOLEAN NOT NULL DEFAULT true,
    is_test                 BOOLEAN NOT NULL DEFAULT false,
    deleted_at              TIMESTAMP,
    created_by              VARCHAR(36) NOT NULL,
    updated_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_fct_flags PRIMARY KEY (id),
    CONSTRAINT fk_ff_fct_flags_scope FOREIGN KEY (scope_id)
        REFERENCES "09_featureflags"."03_dim_flag_scopes"(id),
    CONSTRAINT fk_ff_fct_flags_value_type FOREIGN KEY (value_type_id)
        REFERENCES "09_featureflags"."02_dim_value_types"(id),
    CONSTRAINT fk_ff_fct_flags_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_ff_fct_flags_application FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications"(id),
    CONSTRAINT chk_ff_fct_flags_scope_targets CHECK (
        (scope_id = 1 AND org_id IS NULL     AND application_id IS NULL)
     OR (scope_id = 2 AND org_id IS NOT NULL AND application_id IS NULL)
     OR (scope_id = 3 AND org_id IS NOT NULL AND application_id IS NOT NULL)
    )
);
CREATE UNIQUE INDEX uq_ff_flags_global
    ON "09_featureflags"."10_fct_flags" (flag_key)
    WHERE scope_id = 1 AND deleted_at IS NULL;
CREATE UNIQUE INDEX uq_ff_flags_org
    ON "09_featureflags"."10_fct_flags" (org_id, flag_key)
    WHERE scope_id = 2 AND deleted_at IS NULL;
CREATE UNIQUE INDEX uq_ff_flags_app
    ON "09_featureflags"."10_fct_flags" (application_id, flag_key)
    WHERE scope_id = 3 AND deleted_at IS NULL;
CREATE INDEX idx_ff_fct_flags_org
    ON "09_featureflags"."10_fct_flags" (org_id)
    WHERE org_id IS NOT NULL;
CREATE INDEX idx_ff_fct_flags_app
    ON "09_featureflags"."10_fct_flags" (application_id)
    WHERE application_id IS NOT NULL;

COMMENT ON TABLE  "09_featureflags"."10_fct_flags" IS 'Feature flag definitions. Scope_id determines which target FKs are populated; CHECK enforces the combo. flag_key is unique within its scope partition (three partial unique indexes).';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".scope_id IS 'FK to dim_flag_scopes: 1=global, 2=org, 3=application.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".org_id IS 'Required when scope in (org, application). NULL otherwise.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".application_id IS 'Required when scope=application. NULL otherwise.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".flag_key IS 'Caller-facing key (e.g. beta_checkout). Unique per scope partition, not globally.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".value_type_id IS 'FK to dim_value_types: boolean / string / number / json.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".default_value_jsonb IS 'Fallback value when no env override + no override + no rule matches.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".description IS 'Human-readable description (optional).';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".is_active IS 'Soft-disable flag (all evaluations short-circuit to default).';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "09_featureflags"."10_fct_flags".updated_at IS 'Last-update timestamp.';

CREATE TABLE "09_featureflags"."11_fct_flag_states" (
    id                          VARCHAR(36) NOT NULL,
    flag_id                     VARCHAR(36) NOT NULL,
    environment_id              SMALLINT NOT NULL,
    is_enabled                  BOOLEAN NOT NULL DEFAULT false,
    env_default_value_jsonb     JSONB,
    is_test                     BOOLEAN NOT NULL DEFAULT false,
    deleted_at                  TIMESTAMP,
    created_by                  VARCHAR(36) NOT NULL,
    updated_by                  VARCHAR(36) NOT NULL,
    created_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_fct_flag_states PRIMARY KEY (id),
    CONSTRAINT fk_ff_fct_flag_states_flag FOREIGN KEY (flag_id)
        REFERENCES "09_featureflags"."10_fct_flags"(id),
    CONSTRAINT fk_ff_fct_flag_states_env FOREIGN KEY (environment_id)
        REFERENCES "09_featureflags"."01_dim_environments"(id),
    CONSTRAINT uq_ff_flag_states UNIQUE (flag_id, environment_id)
);
CREATE INDEX idx_ff_fct_flag_states_flag ON "09_featureflags"."11_fct_flag_states" (flag_id);

COMMENT ON TABLE  "09_featureflags"."11_fct_flag_states" IS 'Per-environment state for a flag. One row per (flag, environment); auto-provisioned on flag create, cascaded soft-delete on flag delete.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".flag_id IS 'FK to fct_flags.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".environment_id IS 'FK to dim_environments.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".is_enabled IS 'Flag on/off in this env. false = evaluator returns default without walking rules.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".env_default_value_jsonb IS 'Env-specific default. NULL = inherit flag.default_value.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".deleted_at IS 'Soft-delete timestamp (cascade from parent flag).';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "09_featureflags"."11_fct_flag_states".updated_at IS 'Last-update timestamp.';

-- DOWN ====

DROP TABLE IF EXISTS "09_featureflags"."11_fct_flag_states";
DROP TABLE IF EXISTS "09_featureflags"."10_fct_flags";
