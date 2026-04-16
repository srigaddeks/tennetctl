-- GRC Insights Analytical Views
-- Pre-aggregated views for the AI copilot insight tools.
-- These are the ONLY data sources for insight tools — never raw table scans.
-- All views are bounded aggregates and cannot return unbounded rows.

-- ============================================================
-- View 1: Framework Summary
-- Schema: 05_grc_library
-- ============================================================
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


-- ============================================================
-- View 2: Requirement Summary
-- Schema: 05_grc_library
-- ============================================================
CREATE OR REPLACE VIEW "05_grc_library"."81_vw_requirement_summary" AS
SELECT
    r.id                                                        AS requirement_id,
    r.framework_id,
    f.tenant_key,
    r.requirement_code,
    rp.property_value                                           AS name,
    rp2.property_value                                          AS description,
    COUNT(DISTINCT c.id) FILTER (WHERE NOT c.is_deleted)        AS control_count,
    COUNT(DISTINCT c.id) FILTER (WHERE c.is_active AND NOT c.is_deleted) AS active_control_count,
    COUNT(DISTINCT t.id) FILTER (
        WHERE NOT t.is_deleted
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS open_task_count,
    COUNT(DISTINCT rcm.risk_id) FILTER (
        WHERE rk.risk_level_code IN ('critical', 'high') AND NOT rk.is_deleted
    )                                                           AS high_risk_count,
    -- coverage_gap: no controls at all, or all controls have no tests
    CASE
        WHEN COUNT(DISTINCT c.id) FILTER (WHERE NOT c.is_deleted) = 0 THEN TRUE
        WHEN COUNT(DISTINCT tcm.control_test_id) = 0 THEN TRUE
        ELSE FALSE
    END                                                         AS coverage_gap,
    COUNT(DISTINCT c.id) FILTER (WHERE NOT c.is_deleted) = 0   AS has_no_controls
FROM "05_grc_library"."12_fct_requirements" r
JOIN "05_grc_library"."10_fct_frameworks" f
    ON f.id = r.framework_id
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" rp
    ON rp.requirement_id = r.id AND rp.property_key = 'name'
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" rp2
    ON rp2.requirement_id = r.id AND rp2.property_key = 'description'
LEFT JOIN "05_grc_library"."13_fct_controls" c
    ON c.framework_id = r.framework_id AND c.requirement_id = r.id
LEFT JOIN "08_tasks"."10_fct_tasks" t
    ON t.entity_type = 'control_instance' AND t.entity_id = c.id
LEFT JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    ON rcm.control_id = c.id
LEFT JOIN "14_risk_registry"."10_fct_risks" rk
    ON rk.id = rcm.risk_id
LEFT JOIN "05_grc_library"."30_lnk_test_control_mappings" tcm
    ON tcm.control_id = c.id
LEFT JOIN "05_grc_library"."14_fct_control_tests" ct
    ON ct.id = tcm.control_test_id AND NOT ct.is_deleted
WHERE NOT r.is_deleted
GROUP BY r.id, r.framework_id, f.tenant_key, r.requirement_code,
         rp.property_value, rp2.property_value;


-- ============================================================
-- View 3: Control Health
-- Schema: 05_grc_library
-- ============================================================
CREATE OR REPLACE VIEW "05_grc_library"."82_vw_control_health" AS
SELECT
    c.id                                                        AS control_id,
    c.framework_id,
    c.requirement_id,
    c.tenant_key,
    c.control_code,
    c.criticality_code,
    c.control_type,
    cp_name.property_value                                      AS name,
    cp_owner.property_value                                     AS owner_user_id,
    cp_owner.property_value IS NOT NULL                         AS has_owner,
    COUNT(DISTINCT tcm.control_test_id) FILTER (WHERE NOT ct.is_deleted) AS test_count,
    COUNT(DISTINCT tcm.control_test_id) FILTER (WHERE NOT ct.is_deleted) > 0 AS has_tests,
    MAX(ct.created_at)                                          AS last_test_date,
    COUNT(DISTINCT t.id) FILTER (
        WHERE NOT t.is_deleted
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS open_task_count,
    COUNT(DISTINCT t.id) FILTER (
        WHERE NOT t.is_deleted
        AND t.due_date < NOW()
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS overdue_task_count,
    COUNT(DISTINCT rcm.risk_id)                                 AS linked_risk_count,
    CASE MAX(CASE rk.risk_level_code
        WHEN 'critical' THEN 4
        WHEN 'high' THEN 3
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 1
        ELSE 0
    END)
        WHEN 4 THEN 'critical'
        WHEN 3 THEN 'high'
        WHEN 2 THEN 'medium'
        WHEN 1 THEN 'low'
        ELSE NULL
    END                                                         AS max_risk_severity
FROM "05_grc_library"."13_fct_controls" c
LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp_name
    ON cp_name.control_id = c.id AND cp_name.property_key = 'name'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" cp_owner
    ON cp_owner.control_id = c.id AND cp_owner.property_key = 'owner_user_id'
LEFT JOIN "05_grc_library"."30_lnk_test_control_mappings" tcm
    ON tcm.control_id = c.id
LEFT JOIN "05_grc_library"."14_fct_control_tests" ct
    ON ct.id = tcm.control_test_id
LEFT JOIN "08_tasks"."10_fct_tasks" t
    ON t.entity_type = 'control_instance' AND t.entity_id = c.id
LEFT JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    ON rcm.control_id = c.id
LEFT JOIN "14_risk_registry"."10_fct_risks" rk
    ON rk.id = rcm.risk_id AND NOT rk.is_deleted
WHERE NOT c.is_deleted
GROUP BY c.id, c.framework_id, c.requirement_id, c.tenant_key,
         c.control_code, c.criticality_code, c.control_type,
         cp_name.property_value, cp_owner.property_value;


-- ============================================================
-- View 4: Risk Concentration (per control)
-- Schema: 14_risk_registry
-- ============================================================
CREATE OR REPLACE VIEW "14_risk_registry"."80_vw_risk_concentration" AS
SELECT
    c.id                                                        AS control_id,
    c.control_code,
    c.framework_id,
    c.tenant_key,
    rk.org_id,
    rk.workspace_id,
    COUNT(DISTINCT rk.id)                                       AS total_risk_count,
    COUNT(DISTINCT rk.id) FILTER (WHERE rk.risk_level_code = 'critical') AS critical_risk_count,
    COUNT(DISTINCT rk.id) FILTER (WHERE rk.risk_level_code = 'high')     AS high_risk_count,
    COUNT(DISTINCT rk.id) FILTER (WHERE rk.risk_level_code = 'medium')   AS medium_risk_count,
    COUNT(DISTINCT rk.id) FILTER (WHERE rk.risk_level_code = 'low')      AS low_risk_count,
    COUNT(DISTINCT rk.id) FILTER (WHERE rk.risk_status = 'identified')   AS unactioned_risk_count,
    COUNT(DISTINCT tp.id) FILTER (WHERE tp.plan_status = 'active')       AS active_treatment_count,
    rcm.link_type
FROM "05_grc_library"."13_fct_controls" c
JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm
    ON rcm.control_id = c.id
JOIN "14_risk_registry"."10_fct_risks" rk
    ON rk.id = rcm.risk_id AND NOT rk.is_deleted
LEFT JOIN "14_risk_registry"."11_fct_risk_treatment_plans" tp
    ON tp.risk_id = rk.id
WHERE NOT c.is_deleted
GROUP BY c.id, c.control_code, c.framework_id, c.tenant_key,
         rk.org_id, rk.workspace_id, rcm.link_type;


-- ============================================================
-- View 5: Task Health (per org/workspace)
-- Schema: 08_tasks
-- ============================================================
CREATE OR REPLACE VIEW "08_tasks"."80_vw_task_health" AS
SELECT
    t.org_id,
    t.workspace_id,
    t.tenant_key,
    COUNT(*) FILTER (
        WHERE t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS total_open_tasks,
    COUNT(*) FILTER (
        WHERE t.due_date < NOW()
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS overdue_count,
    COUNT(*) FILTER (
        WHERE t.assignee_user_id IS NULL
        AND t.priority_code IN ('critical', 'high')
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS unassigned_critical_count,
    COUNT(*) FILTER (
        WHERE t.due_date BETWEEN NOW() AND NOW() + INTERVAL '7 days'
        AND t.status_code NOT IN (
            SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
        )
    )                                                           AS due_this_week_count,
    ROUND(AVG(
        CASE
            WHEN t.due_date < NOW()
            AND t.status_code NOT IN (
                SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal = TRUE
            )
            THEN EXTRACT(EPOCH FROM (NOW() - t.due_date)) / 86400
            ELSE NULL
        END
    )::numeric, 1)                                             AS avg_days_overdue,
    jsonb_build_object(
        'critical', COUNT(*) FILTER (WHERE t.priority_code = 'critical' AND t.status_code NOT IN (SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal)),
        'high',     COUNT(*) FILTER (WHERE t.priority_code = 'high'     AND t.status_code NOT IN (SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal)),
        'medium',   COUNT(*) FILTER (WHERE t.priority_code = 'medium'   AND t.status_code NOT IN (SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal)),
        'low',      COUNT(*) FILTER (WHERE t.priority_code = 'low'      AND t.status_code NOT IN (SELECT code FROM "08_tasks"."04_dim_task_statuses" WHERE is_terminal))
    )                                                           AS open_by_priority
FROM "08_tasks"."10_fct_tasks" t
WHERE NOT t.is_deleted
GROUP BY t.org_id, t.workspace_id, t.tenant_key;
