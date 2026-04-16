-- UP ====

CREATE VIEW "03_iam"."v_workspaces" AS
SELECT
    w.id,
    w.org_id,
    w.slug,
    w.is_active,
    w.is_test,
    w.deleted_at,
    w.created_by,
    w.updated_by,
    w.created_at,
    w.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'display_name') AS display_name
FROM "03_iam"."11_fct_workspaces" w
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 2 AND da.entity_id = w.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    w.id, w.org_id, w.slug, w.is_active, w.is_test, w.deleted_at,
    w.created_by, w.updated_by, w.created_at, w.updated_at;

COMMENT ON VIEW "03_iam"."v_workspaces" IS 'Flat read shape for workspaces — joins fct_workspaces with dtl_attrs, pivots display_name. org_id stays as UUID (parent identity).';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_workspaces";
