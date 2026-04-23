-- UP ====

-- Scope roles to a SaaS application.
--
-- Why: tennetctl is multi-app — solsocial, and future apps on the same
-- backend. A role like "solsocial_publisher" is meaningful only inside the
-- solsocial application. Adding application_id lets list/filter endpoints
-- return only the roles a given app owns.
--
-- application_id is NULLABLE to keep backwards compatibility:
--   * application_id IS NULL AND org_id IS NULL  → global platform role
--   * application_id IS NULL AND org_id IS NOT NULL → org-wide role
--   * application_id IS NOT NULL                 → role scoped to a specific app
--
-- Existing rows are left as (application_id IS NULL) — they remain
-- platform/org roles exactly as before.

ALTER TABLE "03_iam"."13_fct_roles"
    ADD COLUMN application_id VARCHAR(36);

COMMENT ON COLUMN "03_iam"."13_fct_roles".application_id IS
    'When set, this role is scoped to a specific SaaS application '
    '(03_iam.15_fct_applications). NULL = platform-wide or org-wide role.';

ALTER TABLE "03_iam"."13_fct_roles"
    ADD CONSTRAINT fk_iam_fct_roles_application
        FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications" (id);

CREATE INDEX idx_iam_fct_roles_application
    ON "03_iam"."13_fct_roles" (application_id)
    WHERE application_id IS NOT NULL AND deleted_at IS NULL;

-- Rebuild v_roles to expose application_id.
DROP VIEW IF EXISTS "03_iam"."v_roles";

CREATE VIEW "03_iam"."v_roles" AS
SELECT
    r.id,
    r.org_id,
    r.application_id,
    rt.code AS role_type,
    r.is_active,
    r.is_test,
    r.deleted_at,
    r.created_by,
    r.updated_by,
    r.created_at,
    r.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'code')        AS code,
    MAX(da.key_text) FILTER (WHERE ad.code = 'label')       AS label,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description
FROM "03_iam"."13_fct_roles" r
JOIN "03_iam"."04_dim_role_types" rt
    ON rt.id = r.role_type_id
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 4 AND da.entity_id = r.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    r.id, r.org_id, r.application_id, rt.code, r.is_active, r.is_test,
    r.deleted_at, r.created_by, r.updated_by, r.created_at, r.updated_at;

COMMENT ON VIEW "03_iam"."v_roles" IS
    'Flat read shape for roles. application_id NULL = platform/org role; non-null = app-scoped role.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_roles";

CREATE VIEW "03_iam"."v_roles" AS
SELECT
    r.id,
    r.org_id,
    rt.code AS role_type,
    r.is_active,
    r.is_test,
    r.deleted_at,
    r.created_by,
    r.updated_by,
    r.created_at,
    r.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'code')        AS code,
    MAX(da.key_text) FILTER (WHERE ad.code = 'label')       AS label,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description
FROM "03_iam"."13_fct_roles" r
JOIN "03_iam"."04_dim_role_types" rt
    ON rt.id = r.role_type_id
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 4 AND da.entity_id = r.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    r.id, r.org_id, rt.code, r.is_active, r.is_test, r.deleted_at,
    r.created_by, r.updated_by, r.created_at, r.updated_at;

DROP INDEX  IF EXISTS "03_iam".idx_iam_fct_roles_application;
ALTER TABLE "03_iam"."13_fct_roles" DROP CONSTRAINT IF EXISTS fk_iam_fct_roles_application;
ALTER TABLE "03_iam"."13_fct_roles" DROP COLUMN IF EXISTS application_id;
