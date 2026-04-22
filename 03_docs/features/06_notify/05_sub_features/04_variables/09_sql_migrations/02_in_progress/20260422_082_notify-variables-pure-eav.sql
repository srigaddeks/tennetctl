-- UP ====

-- Pure-EAV refactor of 13_fct_notify_template_variables (FIX-8).
-- Removes strings and JSONB from the fct_* table, lifts them into a new
-- 23_dtl_notify_template_variables detail row per variable, and adds all
-- mandatory fct_* columns the original migration omitted:
--   is_active, is_test, deleted_at, created_by, updated_by, org_id.
-- var_type goes from TEXT to a FK to the new 06_dim_notify_variable_types
-- dim so the rule "no strings on fct_*" is satisfied cleanly.
--
-- Data migration is inline. Constraints that referenced the moved strings
-- are relocated to the dtl table.

-- -------------------------------------------------------------------
-- Dim: variable types
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "06_notify"."06_dim_notify_variable_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_notify_variable_types PRIMARY KEY (id),
    CONSTRAINT uq_dim_notify_variable_types_code UNIQUE (code)
);
COMMENT ON TABLE "06_notify"."06_dim_notify_variable_types" IS
    'Template variable kinds. Seeded: static=1, dynamic_sql=2.';

INSERT INTO "06_notify"."06_dim_notify_variable_types" (id, code, label, description)
VALUES
    (1, 'static',      'Static',      'Literal value injected into Jinja2 rendering'),
    (2, 'dynamic_sql', 'Dynamic SQL', 'Safelisted SELECT query executed at render time with context params')
ON CONFLICT (id) DO NOTHING;

-- -------------------------------------------------------------------
-- Dtl: variable strings + param bindings
-- -------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS "06_notify"."23_dtl_notify_template_variables" (
    variable_id     VARCHAR(36) NOT NULL,
    template_id     VARCHAR(36) NOT NULL,
    name            TEXT NOT NULL,
    static_value    TEXT,
    sql_template    TEXT,
    param_bindings  JSONB,
    description     TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dtl_notify_template_variables PRIMARY KEY (variable_id),
    CONSTRAINT uq_dtl_notify_template_variables_template_name UNIQUE (template_id, name),
    CONSTRAINT fk_dtl_notify_template_variables_variable
        FOREIGN KEY (variable_id)
        REFERENCES "06_notify"."13_fct_notify_template_variables" (id)
        ON DELETE CASCADE
);
COMMENT ON TABLE "06_notify"."23_dtl_notify_template_variables" IS
    'String + JSONB detail for template variables. template_id is denormalized from fct for the (template_id, name) uniqueness scope.';

-- -------------------------------------------------------------------
-- Fact: add mandatory + FK columns, then swap var_type -> var_type_id
-- -------------------------------------------------------------------

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ADD COLUMN IF NOT EXISTS org_id       VARCHAR(36),
    ADD COLUMN IF NOT EXISTS var_type_id  SMALLINT,
    ADD COLUMN IF NOT EXISTS is_active    BOOLEAN NOT NULL DEFAULT TRUE,
    ADD COLUMN IF NOT EXISTS is_test      BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS deleted_at   TIMESTAMP,
    ADD COLUMN IF NOT EXISTS created_by   VARCHAR(36),
    ADD COLUMN IF NOT EXISTS updated_by   VARCHAR(36);

-- Backfill org_id from the owning template.
UPDATE "06_notify"."13_fct_notify_template_variables" v
   SET org_id = t.org_id
  FROM "06_notify"."12_fct_notify_templates" t
 WHERE v.template_id = t.id
   AND v.org_id IS NULL;

-- Backfill var_type_id from legacy var_type string.
UPDATE "06_notify"."13_fct_notify_template_variables"
   SET var_type_id = 1
 WHERE var_type_id IS NULL AND var_type = 'static';
UPDATE "06_notify"."13_fct_notify_template_variables"
   SET var_type_id = 2
 WHERE var_type_id IS NULL AND var_type = 'dynamic_sql';

-- Backfill created_by / updated_by from the template's creator.
UPDATE "06_notify"."13_fct_notify_template_variables" v
   SET created_by = t.created_by,
       updated_by = t.updated_by
  FROM "06_notify"."12_fct_notify_templates" t
 WHERE v.template_id = t.id
   AND (v.created_by IS NULL OR v.updated_by IS NULL);

-- Move strings + JSONB into the new dtl table. Idempotent.
INSERT INTO "06_notify"."23_dtl_notify_template_variables"
    (variable_id, template_id, name, static_value, sql_template, param_bindings, description,
     created_at, updated_at)
SELECT id, template_id, name, static_value, sql_template, param_bindings, description,
       created_at, updated_at
  FROM "06_notify"."13_fct_notify_template_variables"
 WHERE NOT EXISTS (
           SELECT 1
             FROM "06_notify"."23_dtl_notify_template_variables" d
            WHERE d.variable_id = "06_notify"."13_fct_notify_template_variables".id
       );

-- Drop the constraints that reference columns we are about to drop.
ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    DROP CONSTRAINT IF EXISTS chk_notify_template_variables_type,
    DROP CONSTRAINT IF EXISTS chk_notify_template_variables_static,
    DROP CONSTRAINT IF EXISTS chk_notify_template_variables_dynamic,
    DROP CONSTRAINT IF EXISTS uq_notify_template_variables_name;

-- Drop the now-migrated columns from fct.
ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    DROP COLUMN IF EXISTS name,
    DROP COLUMN IF EXISTS var_type,
    DROP COLUMN IF EXISTS static_value,
    DROP COLUMN IF EXISTS sql_template,
    DROP COLUMN IF EXISTS param_bindings,
    DROP COLUMN IF EXISTS description;

-- Tighten nullability and wire FKs now that data is migrated.
ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ALTER COLUMN org_id      SET NOT NULL,
    ALTER COLUMN var_type_id SET NOT NULL,
    ALTER COLUMN created_by  SET NOT NULL,
    ALTER COLUMN updated_by  SET NOT NULL;

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ADD CONSTRAINT fk_fct_notify_template_variables_org
        FOREIGN KEY (org_id) REFERENCES "03_iam"."10_fct_orgs"(id),
    ADD CONSTRAINT fk_fct_notify_template_variables_type
        FOREIGN KEY (var_type_id)
        REFERENCES "06_notify"."06_dim_notify_variable_types"(id);

-- Rebuild the read view over the new shape.
DROP VIEW IF EXISTS "06_notify"."v_notify_template_variables";
CREATE VIEW "06_notify"."v_notify_template_variables" AS
SELECT
    v.id,
    v.template_id,
    v.org_id,
    d.name,
    t.code AS var_type,
    d.static_value,
    d.sql_template,
    d.param_bindings,
    d.description,
    v.is_active,
    v.is_test,
    v.deleted_at,
    v.created_by,
    v.updated_by,
    v.created_at,
    v.updated_at
FROM "06_notify"."13_fct_notify_template_variables" v
JOIN "06_notify"."23_dtl_notify_template_variables"   d ON d.variable_id = v.id
JOIN "06_notify"."06_dim_notify_variable_types"       t ON t.id          = v.var_type_id;

COMMENT ON VIEW "06_notify"."v_notify_template_variables" IS
    'Read path for template variables — joins fct identity to dtl strings/JSONB and resolves var_type code.';

-- DOWN ====

DROP VIEW IF EXISTS "06_notify"."v_notify_template_variables";

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    DROP CONSTRAINT IF EXISTS fk_fct_notify_template_variables_org,
    DROP CONSTRAINT IF EXISTS fk_fct_notify_template_variables_type;

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ALTER COLUMN org_id      DROP NOT NULL,
    ALTER COLUMN var_type_id DROP NOT NULL,
    ALTER COLUMN created_by  DROP NOT NULL,
    ALTER COLUMN updated_by  DROP NOT NULL;

-- Restore the legacy columns (nullable) and replay data from dtl.
ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ADD COLUMN IF NOT EXISTS name            TEXT,
    ADD COLUMN IF NOT EXISTS var_type        TEXT,
    ADD COLUMN IF NOT EXISTS static_value    TEXT,
    ADD COLUMN IF NOT EXISTS sql_template    TEXT,
    ADD COLUMN IF NOT EXISTS param_bindings  JSONB,
    ADD COLUMN IF NOT EXISTS description     TEXT;

UPDATE "06_notify"."13_fct_notify_template_variables" v
   SET name           = d.name,
       static_value   = d.static_value,
       sql_template   = d.sql_template,
       param_bindings = d.param_bindings,
       description    = d.description
  FROM "06_notify"."23_dtl_notify_template_variables" d
 WHERE d.variable_id = v.id;

UPDATE "06_notify"."13_fct_notify_template_variables"
   SET var_type = 'static'
 WHERE var_type IS NULL AND var_type_id = 1;
UPDATE "06_notify"."13_fct_notify_template_variables"
   SET var_type = 'dynamic_sql'
 WHERE var_type IS NULL AND var_type_id = 2;

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ALTER COLUMN name     SET NOT NULL,
    ALTER COLUMN var_type SET NOT NULL;

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    ADD CONSTRAINT uq_notify_template_variables_name UNIQUE (template_id, name),
    ADD CONSTRAINT chk_notify_template_variables_type
        CHECK (var_type IN ('static', 'dynamic_sql')),
    ADD CONSTRAINT chk_notify_template_variables_static
        CHECK (var_type != 'static' OR static_value IS NOT NULL),
    ADD CONSTRAINT chk_notify_template_variables_dynamic
        CHECK (var_type != 'dynamic_sql' OR sql_template IS NOT NULL);

ALTER TABLE "06_notify"."13_fct_notify_template_variables"
    DROP COLUMN IF EXISTS var_type_id,
    DROP COLUMN IF EXISTS is_active,
    DROP COLUMN IF EXISTS is_test,
    DROP COLUMN IF EXISTS deleted_at,
    DROP COLUMN IF EXISTS created_by,
    DROP COLUMN IF EXISTS updated_by,
    DROP COLUMN IF EXISTS org_id;

DROP TABLE IF EXISTS "06_notify"."23_dtl_notify_template_variables";
DROP TABLE IF EXISTS "06_notify"."06_dim_notify_variable_types";

CREATE VIEW "06_notify"."v_notify_template_variables" AS
SELECT
    id,
    template_id,
    name,
    var_type,
    static_value,
    sql_template,
    param_bindings,
    description,
    created_at,
    updated_at
FROM "06_notify"."13_fct_notify_template_variables";
