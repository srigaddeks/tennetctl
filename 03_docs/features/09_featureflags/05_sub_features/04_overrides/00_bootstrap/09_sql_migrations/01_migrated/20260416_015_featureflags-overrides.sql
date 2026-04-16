-- UP ====

-- featureflags.overrides — explicit per-entity force values per (flag, environment).

CREATE TABLE "09_featureflags"."21_fct_overrides" (
    id                  VARCHAR(36) NOT NULL,
    flag_id             VARCHAR(36) NOT NULL,
    environment_id      SMALLINT NOT NULL,
    entity_type_id      SMALLINT NOT NULL,
    entity_id           VARCHAR(36) NOT NULL,
    value_jsonb         JSONB NOT NULL,
    reason              TEXT,
    is_active           BOOLEAN NOT NULL DEFAULT true,
    is_test             BOOLEAN NOT NULL DEFAULT false,
    deleted_at          TIMESTAMP,
    created_by          VARCHAR(36) NOT NULL,
    updated_by          VARCHAR(36) NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_ff_fct_overrides PRIMARY KEY (id),
    CONSTRAINT fk_ff_fct_overrides_flag FOREIGN KEY (flag_id)
        REFERENCES "09_featureflags"."10_fct_flags"(id),
    CONSTRAINT fk_ff_fct_overrides_env FOREIGN KEY (environment_id)
        REFERENCES "09_featureflags"."01_dim_environments"(id),
    CONSTRAINT fk_ff_fct_overrides_entity_type FOREIGN KEY (entity_type_id)
        REFERENCES "03_iam"."01_dim_entity_types"(id)
);
CREATE UNIQUE INDEX uq_ff_overrides_flag_env_entity
    ON "09_featureflags"."21_fct_overrides" (flag_id, environment_id, entity_type_id, entity_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_ff_fct_overrides_lookup
    ON "09_featureflags"."21_fct_overrides" (flag_id, environment_id, entity_type_id, entity_id)
    WHERE deleted_at IS NULL AND is_active = true;

COMMENT ON TABLE  "09_featureflags"."21_fct_overrides" IS 'Explicit per-entity force values. Highest precedence in evaluation — beats rules. entity_type_id+entity_id form a polymorphic pointer.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".id IS 'UUID v7.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".flag_id IS 'FK to fct_flags.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".environment_id IS 'FK to dim_environments. Override is env-specific.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".entity_type_id IS 'FK to iam.dim_entity_types. 1=org, 3=user in practice.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".entity_id IS 'UUID of the entity being force-valued.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".value_jsonb IS 'Forced value.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".reason IS 'Why this override exists (for audit / UX).';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".is_active IS 'Soft-disable without revoke.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".is_test IS 'Marks test/staging data.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".deleted_at IS 'Soft-delete timestamp.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".created_by IS 'UUID of creator.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".updated_by IS 'UUID of last modifier.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "09_featureflags"."21_fct_overrides".updated_at IS 'Last-update timestamp.';

CREATE VIEW "09_featureflags"."v_overrides" AS
SELECT
    o.id,
    o.flag_id,
    e.code AS environment,
    et.code AS entity_type,
    o.entity_id,
    o.value_jsonb AS value,
    o.reason,
    o.is_active,
    o.is_test,
    o.deleted_at,
    o.created_by,
    o.updated_by,
    o.created_at,
    o.updated_at
FROM "09_featureflags"."21_fct_overrides" o
JOIN "09_featureflags"."01_dim_environments" e ON e.id = o.environment_id
JOIN "03_iam"."01_dim_entity_types" et ON et.id = o.entity_type_id;

COMMENT ON VIEW "09_featureflags"."v_overrides" IS 'Flat read shape for overrides — env + entity_type codes exposed, not SMALLINT ids.';

-- DOWN ====

DROP VIEW IF EXISTS "09_featureflags"."v_overrides";
DROP TABLE IF EXISTS "09_featureflags"."21_fct_overrides";
