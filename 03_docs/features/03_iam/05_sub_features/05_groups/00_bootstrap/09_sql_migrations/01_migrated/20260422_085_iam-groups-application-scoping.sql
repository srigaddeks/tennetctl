-- UP ====

-- Scope user-groups to a SaaS application. See companion migration
-- 20260422_084 for the rationale applied to roles.

ALTER TABLE "03_iam"."14_fct_groups"
    ADD COLUMN application_id VARCHAR(36);

COMMENT ON COLUMN "03_iam"."14_fct_groups".application_id IS
    'When set, this group is scoped to a specific SaaS application. NULL = org-wide group.';

ALTER TABLE "03_iam"."14_fct_groups"
    ADD CONSTRAINT fk_iam_fct_groups_application
        FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications" (id);

CREATE INDEX idx_iam_fct_groups_application
    ON "03_iam"."14_fct_groups" (application_id)
    WHERE application_id IS NOT NULL AND deleted_at IS NULL;

DROP VIEW IF EXISTS "03_iam"."v_groups";

CREATE VIEW "03_iam"."v_groups" AS
SELECT
    g.id,
    g.org_id,
    g.application_id,
    g.is_active,
    g.is_test,
    g.deleted_at,
    g.created_by,
    g.updated_by,
    g.created_at,
    g.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'code')        AS code,
    MAX(da.key_text) FILTER (WHERE ad.code = 'label')       AS label,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description
FROM "03_iam"."14_fct_groups" g
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 5 AND da.entity_id = g.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    g.id, g.org_id, g.application_id, g.is_active, g.is_test,
    g.deleted_at, g.created_by, g.updated_by, g.created_at, g.updated_at;

COMMENT ON VIEW "03_iam"."v_groups" IS
    'Flat read shape for groups. application_id NULL = org-wide group; non-null = app-scoped group.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_groups";

CREATE VIEW "03_iam"."v_groups" AS
SELECT
    g.id,
    g.org_id,
    g.is_active,
    g.is_test,
    g.deleted_at,
    g.created_by,
    g.updated_by,
    g.created_at,
    g.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'code')        AS code,
    MAX(da.key_text) FILTER (WHERE ad.code = 'label')       AS label,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description
FROM "03_iam"."14_fct_groups" g
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 5 AND da.entity_id = g.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    g.id, g.org_id, g.is_active, g.is_test, g.deleted_at,
    g.created_by, g.updated_by, g.created_at, g.updated_at;

DROP INDEX  IF EXISTS "03_iam".idx_iam_fct_groups_application;
ALTER TABLE "03_iam"."14_fct_groups" DROP CONSTRAINT IF EXISTS fk_iam_fct_groups_application;
ALTER TABLE "03_iam"."14_fct_groups" DROP COLUMN IF EXISTS application_id;
