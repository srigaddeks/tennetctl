-- UP ====

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

COMMENT ON VIEW "03_iam"."v_groups" IS 'Flat read shape for groups — pivots code/label/description EAV attrs. Always org-scoped.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_groups";
