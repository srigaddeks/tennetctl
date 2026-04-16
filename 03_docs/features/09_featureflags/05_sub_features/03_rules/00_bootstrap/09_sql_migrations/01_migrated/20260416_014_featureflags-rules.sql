-- UP ====

-- featureflags.rules — ordered targeting rules per (flag, environment).

CREATE TABLE "09_featureflags"."20_fct_rules" (
    id                      VARCHAR(36) NOT NULL,
    flag_id                 VARCHAR(36) NOT NULL,
    environment_id          SMALLINT NOT NULL,
    priority                SMALLINT NOT NULL,
    conditions_jsonb        JSONB NOT NULL,
    value_jsonb             JSONB NOT NULL,
    rollout_percentage      SMALLINT NOT NULL DEFAULT 100,
    is_active               BOOLEAN NOT NULL DEFAULT true,
    is_test                 BOOLEAN NOT NULL DEFAULT false,
    deleted_at              TIMESTAMP,
    created_by              VARCHAR(36) NOT NULL,
    updated_by              VARCHAR(36) NOT NULL,
    created_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_fct_rules PRIMARY KEY (id),
    CONSTRAINT fk_ff_fct_rules_flag FOREIGN KEY (flag_id)
        REFERENCES "09_featureflags"."10_fct_flags"(id),
    CONSTRAINT fk_ff_fct_rules_env FOREIGN KEY (environment_id)
        REFERENCES "09_featureflags"."01_dim_environments"(id),
    CONSTRAINT chk_ff_fct_rules_rollout CHECK (rollout_percentage BETWEEN 0 AND 100)
);
CREATE INDEX idx_ff_fct_rules_flag_env_prio
    ON "09_featureflags"."20_fct_rules" (flag_id, environment_id, priority)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE  "09_featureflags"."20_fct_rules" IS 'Targeting rules per (flag, environment). Evaluator walks in priority ASC; first match wins. rollout_percentage=100 means "always match when conditions apply".';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".flag_id IS 'FK to fct_flags.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".environment_id IS 'FK to dim_environments. Rules scope to a specific env; cross-env rules not supported in v0.1.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".priority IS 'Lower = checked first. Consecutive integers not required.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".conditions_jsonb IS 'Condition tree: {op:"and"|"or"|"not"|"eq"|"neq"|"in"|"startswith"|"endswith"|"contains", attr?, value?, children?}. Evaluator walks this against request context.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".value_jsonb IS 'Value to return when rule matches.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".rollout_percentage IS 'Deterministic rollout via hash(flag_key + entity_id) % 100 < rollout_percentage.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".is_active IS 'Soft-disable (evaluator skips inactive rules).';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "09_featureflags"."20_fct_rules".updated_at IS 'Last-update timestamp.';

CREATE VIEW "09_featureflags"."v_rules" AS
SELECT
    r.id,
    r.flag_id,
    e.code AS environment,
    r.priority,
    r.conditions_jsonb AS conditions,
    r.value_jsonb AS value,
    r.rollout_percentage,
    r.is_active,
    r.is_test,
    r.deleted_at,
    r.created_by,
    r.updated_by,
    r.created_at,
    r.updated_at
FROM "09_featureflags"."20_fct_rules" r
JOIN "09_featureflags"."01_dim_environments" e ON e.id = r.environment_id;

COMMENT ON VIEW "09_featureflags"."v_rules" IS 'Flat read shape for rules. Environment is the text code.';

-- DOWN ====

DROP VIEW IF EXISTS "09_featureflags"."v_rules";
DROP TABLE IF EXISTS "09_featureflags"."20_fct_rules";
