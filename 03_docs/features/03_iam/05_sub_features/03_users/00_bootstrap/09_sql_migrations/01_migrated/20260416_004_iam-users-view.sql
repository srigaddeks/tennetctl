-- UP ====

CREATE VIEW "03_iam"."v_users" AS
SELECT
    u.id,
    at.code AS account_type,
    u.is_active,
    u.is_test,
    u.deleted_at,
    u.created_by,
    u.updated_by,
    u.created_at,
    u.updated_at,
    MAX(da.key_text) FILTER (WHERE ad.code = 'email')        AS email,
    MAX(da.key_text) FILTER (WHERE ad.code = 'display_name') AS display_name,
    MAX(da.key_text) FILTER (WHERE ad.code = 'avatar_url')   AS avatar_url
FROM "03_iam"."12_fct_users" u
JOIN "03_iam"."02_dim_account_types" at
    ON at.id = u.account_type_id
LEFT JOIN "03_iam"."21_dtl_attrs" da
    ON da.entity_type_id = 3 AND da.entity_id = u.id
LEFT JOIN "03_iam"."20_dtl_attr_defs" ad
    ON ad.id = da.attr_def_id
GROUP BY
    u.id, at.code, u.is_active, u.is_test, u.deleted_at,
    u.created_by, u.updated_by, u.created_at, u.updated_at;

COMMENT ON VIEW "03_iam"."v_users" IS 'Flat read shape for users — resolves account_type from dim + pivots email/display_name/avatar_url from dtl_attrs. Hides account_type_id (internal FK).';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_users";
