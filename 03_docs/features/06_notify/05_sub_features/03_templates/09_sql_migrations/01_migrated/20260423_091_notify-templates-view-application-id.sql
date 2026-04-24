-- UP ====
-- Rebuild v_notify_templates to expose application_id added in migration 090.
-- Required for the repository application_id filter to work correctly.

DROP VIEW IF EXISTS "06_notify"."v_notify_templates";

CREATE VIEW "06_notify"."v_notify_templates" AS
SELECT
    t.id,
    t.org_id,
    t.key,
    t.group_id,
    g.key AS group_key,
    g.category_id,
    g.category_code,
    g.category_label,
    t.subject,
    t.reply_to,
    t.priority_id,
    p.code AS priority_code,
    p.label AS priority_label,
    t.fallback_chain,
    t.is_active,
    t.created_by,
    t.updated_by,
    t.created_at,
    t.updated_at,
    t.application_id,
    COALESCE(
        json_agg(
            json_build_object(
                'id', b.id,
                'channel_id', b.channel_id,
                'body_html', b.body_html,
                'body_text', b.body_text,
                'preheader', b.preheader
            ) ORDER BY b.channel_id
        ) FILTER (WHERE b.id IS NOT NULL),
        '[]'::json
    ) AS bodies
FROM "06_notify"."12_fct_notify_templates" t
JOIN "06_notify".v_notify_template_groups g ON g.id::text = t.group_id::text
JOIN "06_notify"."04_dim_notify_priorities" p ON p.id = t.priority_id
LEFT JOIN "06_notify"."20_dtl_notify_template_bodies" b ON b.template_id::text = t.id::text
WHERE t.deleted_at IS NULL
GROUP BY
    t.id, t.org_id, t.key, t.group_id,
    g.key, g.category_id, g.category_code, g.category_label,
    t.subject, t.reply_to, t.priority_id, p.code, p.label,
    t.fallback_chain, t.is_active, t.created_by, t.updated_by,
    t.created_at, t.updated_at, t.application_id;

COMMENT ON VIEW "06_notify"."v_notify_templates" IS
    'Resolved notify templates with group/priority metadata, bodies, and application scoping.';

-- DOWN ====
DROP VIEW IF EXISTS "06_notify"."v_notify_templates";

CREATE VIEW "06_notify"."v_notify_templates" AS
SELECT
    t.id,
    t.org_id,
    t.key,
    t.group_id,
    g.key AS group_key,
    g.category_id,
    g.category_code,
    g.category_label,
    t.subject,
    t.reply_to,
    t.priority_id,
    p.code AS priority_code,
    p.label AS priority_label,
    t.fallback_chain,
    t.is_active,
    t.created_by,
    t.updated_by,
    t.created_at,
    t.updated_at,
    COALESCE(
        json_agg(
            json_build_object(
                'id', b.id,
                'channel_id', b.channel_id,
                'body_html', b.body_html,
                'body_text', b.body_text,
                'preheader', b.preheader
            ) ORDER BY b.channel_id
        ) FILTER (WHERE b.id IS NOT NULL),
        '[]'::json
    ) AS bodies
FROM "06_notify"."12_fct_notify_templates" t
JOIN "06_notify".v_notify_template_groups g ON g.id::text = t.group_id::text
JOIN "06_notify"."04_dim_notify_priorities" p ON p.id = t.priority_id
LEFT JOIN "06_notify"."20_dtl_notify_template_bodies" b ON b.template_id::text = t.id::text
WHERE t.deleted_at IS NULL
GROUP BY
    t.id, t.org_id, t.key, t.group_id,
    g.key, g.category_id, g.category_code, g.category_label,
    t.subject, t.reply_to, t.priority_id, p.code, p.label,
    t.fallback_chain, t.is_active, t.created_by, t.updated_by,
    t.created_at, t.updated_at;
