-- UP ====

CREATE VIEW "03_iam"."v_orgs" AS
SELECT
    o.id,
    o.slug,
    o.is_active,
    o.is_test,
    o.deleted_at,
    o.created_by,
    o.updated_by,
    o.created_at,
    o.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'display_name') AS display_name
FROM "03_iam"."10_fct_orgs" o
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 1 AND da.entity_id = o.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    o.id, o.slug, o.is_active, o.is_test, o.deleted_at,
    o.created_by, o.updated_by, o.created_at, o.updated_at;

COMMENT ON VIEW "03_iam"."v_orgs" IS 'Flat read shape for orgs — joins fct_orgs with dtl_attrs, pivots display_name. Phase 4+ repositories SELECT from here.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_orgs";
