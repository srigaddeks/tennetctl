-- UP ====

CREATE VIEW "09_featureflags"."v_flags" AS
SELECT
    f.id,
    fs.code AS scope,
    f.org_id,
    f.application_id,
    f.flag_key,
    vt.code AS value_type,
    f.default_value_jsonb AS default_value,
    f.description,
    f.is_active,
    f.is_test,
    f.deleted_at,
    f.created_by,
    f.updated_by,
    f.created_at,
    f.updated_at
FROM "09_featureflags"."10_fct_flags" f
JOIN "09_featureflags"."03_dim_flag_scopes" fs ON fs.id = f.scope_id
JOIN "09_featureflags"."02_dim_value_types" vt ON vt.id = f.value_type_id;

COMMENT ON VIEW "09_featureflags"."v_flags" IS 'Flat read shape for flags — resolves scope + value_type from dim tables. Callers never see SMALLINT fk ids.';

CREATE VIEW "09_featureflags"."v_flag_states" AS
SELECT
    s.id,
    s.flag_id,
    e.code AS environment,
    s.is_enabled,
    s.env_default_value_jsonb AS env_default_value,
    s.is_test,
    s.deleted_at,
    s.created_by,
    s.updated_by,
    s.created_at,
    s.updated_at
FROM "09_featureflags"."11_fct_flag_states" s
JOIN "09_featureflags"."01_dim_environments" e ON e.id = s.environment_id;

COMMENT ON VIEW "09_featureflags"."v_flag_states" IS 'Flat read shape for per-env flag state; environment is the text code, not SMALLINT id.';

-- DOWN ====

DROP VIEW IF EXISTS "09_featureflags"."v_flag_states";
DROP VIEW IF EXISTS "09_featureflags"."v_flags";
