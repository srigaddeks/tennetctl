-- UP ====

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

COMMENT ON VIEW "03_iam"."v_roles" IS 'Flat read shape for roles — resolves role_type from dim; pivots code/label/description EAV attrs. org_id NULL means global role.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_roles";
