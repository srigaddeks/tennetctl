-- Framework hierarchy view: per-control breakdown within a framework
-- Used for "show tasks across all controls in SOC 2" type queries
-- Bounded: one row per control, not one row per task

CREATE OR REPLACE VIEW "05_grc_library"."85_vw_framework_hierarchy" AS
SELECT
    f.id::text                          AS framework_id,
    f.tenant_key,
    f_name.property_value               AS framework_name,
    f_code.property_value               AS framework_code,
    c.id::text                          AS control_id,
    c.control_code,
    c.criticality_code,
    req.requirement_code,
    req_name.property_value             AS requirement_name,
    -- tasks directly on this control
    COALESCE(ct.task_count, 0)::int     AS control_task_count,
    COALESCE(ct.open_count, 0)::int     AS control_open_tasks,
    COALESCE(ct.overdue_count, 0)::int  AS control_overdue_tasks,
    COALESCE(ct.evidence_count, 0)::int AS evidence_task_count,
    -- risks on this control
    COALESCE(ra.risk_count, 0)::int     AS linked_risk_count,
    COALESCE(ra.high_crit, 0)::int      AS high_critical_risk_count,
    ra.risk_codes                       AS risk_codes,
    ra.risk_levels                      AS risk_levels,
    -- tasks on risks linked to this control
    COALESCE(rt.task_count, 0)::int     AS risk_task_count,
    COALESCE(rt.open_count, 0)::int     AS risk_open_tasks
FROM "05_grc_library"."10_fct_frameworks" f
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" f_name
    ON f_name.framework_id = f.id AND f_name.property_key = 'name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" f_code
    ON f_code.framework_id = f.id AND f_code.property_key = 'code'
JOIN "05_grc_library"."13_fct_controls" c
    ON c.framework_id = f.id AND NOT c.is_deleted
LEFT JOIN "05_grc_library"."12_fct_requirements" req ON req.id = c.requirement_id
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" req_name
    ON req_name.requirement_id = c.requirement_id AND req_name.property_key = 'name'
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                        AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                       AS open_count,
        COUNT(*) FILTER (WHERE t.due_date < NOW() AND NOT t.is_terminal)                AS overdue_count,
        COUNT(*) FILTER (WHERE t.task_type_code = 'evidence_collection')                AS evidence_count
    FROM "08_tasks"."40_vw_task_detail" t
    WHERE t.entity_id = c.id AND t.entity_type = 'control' AND NOT t.is_deleted
) ct ON TRUE
LEFT JOIN LATERAL (
    SELECT
        COUNT(DISTINCT r.id)                                                             AS risk_count,
        COUNT(DISTINCT r.id) FILTER (WHERE r.risk_level_code IN ('critical','high'))     AS high_crit,
        ARRAY_AGG(DISTINCT r.risk_code)                                                  AS risk_codes,
        ARRAY_AGG(DISTINCT r.risk_level_code)                                            AS risk_levels
    FROM "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    JOIN "14_risk_registry"."10_fct_risks" r ON r.id = rcm.risk_id AND NOT r.is_deleted
    WHERE rcm.control_id = c.id
) ra ON TRUE
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_count
    FROM "08_tasks"."40_vw_task_detail" t
    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm ON rcm.risk_id = t.entity_id
    WHERE rcm.control_id = c.id AND t.entity_type = 'risk' AND NOT t.is_deleted
) rt ON TRUE
WHERE NOT f.is_deleted;

DO $$ BEGIN
  GRANT SELECT ON "05_grc_library"."85_vw_framework_hierarchy" TO kcontrol_dev_read;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
DO $$ BEGIN
  GRANT SELECT ON "05_grc_library"."85_vw_framework_hierarchy" TO kcontrol_dev_write;
EXCEPTION WHEN undefined_object THEN NULL; END $$;
