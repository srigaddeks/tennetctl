-- Add scope_workspace_id to 80_vw_framework_summary so AI report tools can filter by workspace.
CREATE OR REPLACE VIEW "05_grc_library"."80_vw_framework_summary" AS
SELECT
    f.id                                                        AS framework_id,
    f.tenant_key,
    f.framework_code,
    f.scope_org_id,
    f.scope_workspace_id,
    f.approval_status,
    f.is_active,
    pn.property_value                                           AS name,
    ps.property_value                                           AS short_description,
    COUNT(DISTINCT c.id) FILTER (WHERE NOT c.is_deleted)        AS total_controls,
    COUNT(DISTINCT c.id) FILTER (WHERE c.is_active AND NOT c.is_deleted) AS active_controls,
    COUNT(DISTINCT r.id) FILTER (WHERE NOT r.is_deleted)        AS total_requirements,
    COUNT(DISTINCT t.id) FILTER (
        WHERE NOT t.is_deleted
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS open_task_count,
    COUNT(DISTINCT rcm.risk_id)                                 AS linked_risk_count,
    COUNT(DISTINCT rcm.risk_id) FILTER (
        WHERE rk.risk_level_code IN ('critical', 'high')
        AND NOT rk.is_deleted
    )                                                           AS high_risk_count,
    CASE
        WHEN COUNT(DISTINCT c.id) FILTER (WHERE NOT c.is_deleted) = 0 THEN 0
        ELSE ROUND(
            100.0 * COUNT(DISTINCT c.id) FILTER (
                WHERE c.is_active AND NOT c.is_deleted
                AND EXISTS (
                    SELECT 1 FROM "08_tasks"."10_fct_tasks" t2
                    WHERE t2.entity_type = 'control_instance'
                    AND t2.entity_id = c.id
                    AND t2.status_code IN (
                        SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
                    )
                )
            ) / NULLIF(COUNT(DISTINCT c.id) FILTER (WHERE NOT c.is_deleted), 0)
        )
    END                                                         AS completion_pct
FROM "05_grc_library"."10_fct_frameworks" f
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" pn
    ON pn.framework_id = f.id AND pn.property_key = 'name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" ps
    ON ps.framework_id = f.id AND ps.property_key = 'short_description'
LEFT JOIN "05_grc_library"."12_fct_requirements" r
    ON r.framework_id = f.id AND NOT r.is_deleted
LEFT JOIN "05_grc_library"."13_fct_controls" c
    ON c.framework_id = f.id
LEFT JOIN "08_tasks"."10_fct_tasks" t
    ON t.entity_type = 'control_instance' AND t.entity_id = c.id
LEFT JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    ON rcm.control_id = c.id
LEFT JOIN "14_risk_registry"."10_fct_risks" rk
    ON rk.id = rcm.risk_id
WHERE NOT f.is_deleted
GROUP BY f.id, f.tenant_key, f.framework_code, f.scope_org_id, f.scope_workspace_id,
         f.approval_status, f.is_active, pn.property_value, ps.property_value;
