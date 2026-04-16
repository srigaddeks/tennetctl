-- UP ====

CREATE VIEW "03_iam"."v_applications" AS
SELECT
    a.id,
    a.org_id,
    a.is_active,
    a.is_test,
    a.deleted_at,
    a.created_by,
    a.updated_by,
    a.created_at,
    a.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'code')        AS code,
    MAX(da.key_text) FILTER (WHERE ad.code = 'label')       AS label,
    MAX(da.key_text) FILTER (WHERE ad.code = 'description') AS description
FROM "03_iam"."15_fct_applications" a
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 6 AND da.entity_id = a.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    a.id, a.org_id, a.is_active, a.is_test, a.deleted_at,
    a.created_by, a.updated_by, a.created_at, a.updated_at;

COMMENT ON VIEW "03_iam"."v_applications" IS 'Flat read shape for applications — pivots code/label/description EAV attrs. Always org-scoped.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_applications";
