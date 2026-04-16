-- GRC Hierarchy views for AI copilot traversal
-- control → tasks, control → risks → tasks, risk → controls → tasks

-- ─────────────────────────────────────────────────────────────────────────────
-- View 1: per-control full hierarchy summary
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW "05_grc_library"."83_vw_control_hierarchy" AS
SELECT
    c.id::text                          AS control_id,
    c.framework_id::text                AS framework_id,
    c.requirement_id::text              AS requirement_id,
    c.tenant_key,
    c.control_code,
    f_name.property_value               AS framework_name,
    req.requirement_code                AS requirement_code,
    req_name.property_value             AS requirement_name,
    -- direct tasks on this control
    COALESCE(ct.task_count, 0)::int             AS direct_task_count,
    COALESCE(ct.open_task_count, 0)::int        AS direct_open_task_count,
    COALESCE(ct.overdue_task_count, 0)::int     AS direct_overdue_task_count,
    COALESCE(ct.evidence_task_count, 0)::int    AS evidence_task_count,
    COALESCE(ct.remediation_task_count, 0)::int AS remediation_task_count,
    -- risks linked to this control
    COALESCE(ra.risk_count, 0)::int             AS linked_risk_count,
    COALESCE(ra.critical_risk_count, 0)::int    AS critical_risk_count,
    COALESCE(ra.high_risk_count, 0)::int        AS high_risk_count,
    ra.risk_ids                                 AS linked_risk_ids,
    ra.risk_codes                               AS linked_risk_codes,
    ra.risk_titles                              AS linked_risk_titles,
    ra.risk_levels                              AS linked_risk_levels,
    -- tasks on those risks
    COALESCE(rt.task_count, 0)::int             AS risk_task_count,
    COALESCE(rt.open_task_count, 0)::int        AS risk_open_task_count
FROM "05_grc_library"."13_fct_controls" c
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" f_name
    ON f_name.framework_id = c.framework_id AND f_name.property_key = 'name'
LEFT JOIN "05_grc_library"."12_fct_requirements" req
    ON req.id = c.requirement_id
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" req_name
    ON req_name.requirement_id = c.requirement_id AND req_name.property_key = 'name'
-- direct control tasks
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                         AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                        AS open_task_count,
        COUNT(*) FILTER (WHERE t.due_date < NOW() AND NOT t.is_terminal)                 AS overdue_task_count,
        COUNT(*) FILTER (WHERE t.task_type_code = 'evidence_collection')                 AS evidence_task_count,
        COUNT(*) FILTER (WHERE t.task_type_code = 'remediation')                         AS remediation_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    WHERE t.entity_id = c.id AND t.entity_type = 'control' AND NOT t.is_deleted
) ct ON TRUE
-- risks linked to control
LEFT JOIN LATERAL (
    SELECT
        COUNT(DISTINCT r.id)                                                              AS risk_count,
        COUNT(DISTINCT r.id) FILTER (WHERE r.risk_level_code = 'critical')                AS critical_risk_count,
        COUNT(DISTINCT r.id) FILTER (WHERE r.risk_level_code = 'high')                    AS high_risk_count,
        ARRAY_AGG(DISTINCT rcm.risk_id::text)                                             AS risk_ids,
        ARRAY_AGG(DISTINCT r.risk_code)                                                   AS risk_codes,
        ARRAY_AGG(DISTINCT rp.property_value)                                             AS risk_titles,
        ARRAY_AGG(DISTINCT r.risk_level_code)                                             AS risk_levels
    FROM "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    JOIN "14_risk_registry"."10_fct_risks" r ON r.id = rcm.risk_id AND NOT r.is_deleted
    LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" rp
        ON rp.risk_id = r.id AND rp.property_key = 'title'
    WHERE rcm.control_id = c.id
) ra ON TRUE
-- tasks on those linked risks
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm ON rcm.risk_id = t.entity_id
    WHERE rcm.control_id = c.id AND t.entity_type = 'risk' AND NOT t.is_deleted
) rt ON TRUE
WHERE NOT c.is_deleted;


-- ─────────────────────────────────────────────────────────────────────────────
-- View 2: per-risk full hierarchy summary  (put in 05_grc_library since write
--          user has CREATE there; risk schema requires admin)
-- ─────────────────────────────────────────────────────────────────────────────
CREATE OR REPLACE VIEW "05_grc_library"."84_vw_risk_hierarchy" AS
SELECT
    r.id::text                          AS risk_id,
    r.tenant_key,
    r.org_id::text                      AS org_id,
    r.workspace_id::text                AS workspace_id,
    r.risk_code,
    r.risk_level_code,
    r.risk_status,
    r.risk_category_code,
    rp.property_value                   AS title,
    -- direct tasks on this risk
    COALESCE(rt.task_count, 0)::int             AS direct_task_count,
    COALESCE(rt.open_task_count, 0)::int        AS direct_open_task_count,
    COALESCE(rt.overdue_task_count, 0)::int     AS direct_overdue_task_count,
    -- controls linked to this risk
    COALESCE(ca.control_count, 0)::int          AS linked_control_count,
    ca.control_ids                              AS linked_control_ids,
    ca.control_codes                            AS linked_control_codes,
    ca.framework_ids                            AS linked_framework_ids,
    ca.framework_names                          AS linked_framework_names,
    -- tasks from those linked controls
    COALESCE(ct.task_count, 0)::int             AS control_task_count,
    COALESCE(ct.open_task_count, 0)::int        AS control_open_task_count
FROM "14_risk_registry"."10_fct_risks" r
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" rp
    ON rp.risk_id = r.id AND rp.property_key = 'title'
-- direct risk tasks
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_task_count,
        COUNT(*) FILTER (WHERE t.due_date < NOW() AND NOT t.is_terminal)                  AS overdue_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    WHERE t.entity_id = r.id AND t.entity_type = 'risk' AND NOT t.is_deleted
) rt ON TRUE
-- controls linked to this risk
LEFT JOIN LATERAL (
    SELECT
        COUNT(DISTINCT c.id)                                   AS control_count,
        ARRAY_AGG(DISTINCT rcm.control_id::text)               AS control_ids,
        ARRAY_AGG(DISTINCT c.control_code)                     AS control_codes,
        ARRAY_AGG(DISTINCT c.framework_id::text)               AS framework_ids,
        ARRAY_AGG(DISTINCT fn.property_value)                  AS framework_names
    FROM "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    JOIN "05_grc_library"."13_fct_controls" c ON c.id = rcm.control_id AND NOT c.is_deleted
    LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fn
        ON fn.framework_id = c.framework_id AND fn.property_key = 'name'
    WHERE rcm.risk_id = r.id
) ca ON TRUE
-- tasks from linked controls
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm ON rcm.control_id = t.entity_id
    WHERE rcm.risk_id = r.id AND t.entity_type = 'control' AND NOT t.is_deleted
) ct ON TRUE
WHERE NOT r.is_deleted;

-- Grant read access to app roles (safe: skips if role does not exist)
DO $$ BEGIN
  GRANT SELECT ON "05_grc_library"."83_vw_control_hierarchy" TO kcontrol_dev_read;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN
  GRANT SELECT ON "05_grc_library"."84_vw_risk_hierarchy" TO kcontrol_dev_read;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN
  GRANT SELECT ON "05_grc_library"."83_vw_control_hierarchy" TO kcontrol_dev_write;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN
  GRANT SELECT ON "05_grc_library"."84_vw_risk_hierarchy" TO kcontrol_dev_write;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
