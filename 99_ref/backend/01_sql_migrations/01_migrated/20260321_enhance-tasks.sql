-- ─────────────────────────────────────────────────────────────────────────────
-- TASKS SCHEMA ENHANCEMENTS
-- Adds start_date, estimated_hours, actual_hours columns
-- Recreates 40_vw_task_detail view with new fields + remediation_plan EAV
-- Adds composite indexes for new filter patterns
-- Extends event type CHECK constraint with start_date_changed
-- ─────────────────────────────────────────────────────────────────────────────

-- 1. Add columns to fact table
ALTER TABLE "08_tasks"."10_fct_tasks"
    ADD COLUMN IF NOT EXISTS start_date       TIMESTAMP    NULL,
    ADD COLUMN IF NOT EXISTS estimated_hours  NUMERIC(8,2) NULL,
    ADD COLUMN IF NOT EXISTS actual_hours     NUMERIC(8,2) NULL;

-- 2. Extend task events CHECK constraint with start_date_changed
ALTER TABLE "08_tasks"."30_trx_task_events"
    DROP CONSTRAINT IF EXISTS ck_30_trx_task_events_type;

ALTER TABLE "08_tasks"."30_trx_task_events"
    ADD CONSTRAINT ck_30_trx_task_events_type CHECK (event_type IN (
        'created','status_changed','reassigned','priority_changed',
        'due_date_changed','start_date_changed','comment_added',
        'dependency_added','dependency_removed',
        'co_assignee_added','co_assignee_removed'
    ));

-- 3. New indexes
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_priority_status
    ON "08_tasks"."10_fct_tasks" (priority_code, status_code) WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_reporter
    ON "08_tasks"."10_fct_tasks" (reporter_user_id) WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_type
    ON "08_tasks"."10_fct_tasks" (task_type_code) WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_due
    ON "08_tasks"."10_fct_tasks" (due_date) WHERE is_deleted = FALSE AND due_date IS NOT NULL;

-- 4. Recreate view with new fields + remediation_plan EAV
DROP VIEW IF EXISTS "08_tasks"."40_vw_task_detail" CASCADE;
CREATE VIEW "08_tasks"."40_vw_task_detail" AS
SELECT
    t.id, t.tenant_key, t.org_id, t.workspace_id,
    t.task_type_code,   tt.name  AS task_type_name,
    t.priority_code,    tp.name  AS priority_name,
    t.status_code,      ts.name  AS status_name, ts.is_terminal,
    t.entity_type, t.entity_id,
    t.assignee_user_id, t.reporter_user_id,
    t.due_date, t.start_date, t.completed_at,
    t.estimated_hours, t.actual_hours,
    t.is_active, t.is_deleted, t.created_at, t.updated_at,
    -- EAV flattened
    p_title.property_value   AS title,
    p_desc.property_value    AS description,
    p_accept.property_value  AS acceptance_criteria,
    p_resolve.property_value AS resolution_notes,
    p_remedy.property_value  AS remediation_plan,
    -- Counts
    (SELECT COUNT(*) FROM "08_tasks"."31_lnk_task_assignments" a
     WHERE a.task_id = t.id) AS co_assignee_count,
    (SELECT COUNT(*) FROM "08_tasks"."32_lnk_task_dependencies" d
     WHERE d.blocked_task_id = t.id) AS blocker_count,
    (SELECT COUNT(*) FROM "08_tasks"."30_trx_task_events" e
     WHERE e.task_id = t.id AND e.event_type = 'comment_added') AS comment_count
FROM "08_tasks"."10_fct_tasks" t
LEFT JOIN "08_tasks"."02_dim_task_types"     tt ON tt.code = t.task_type_code
LEFT JOIN "08_tasks"."03_dim_task_priorities" tp ON tp.code = t.priority_code
LEFT JOIN "08_tasks"."04_dim_task_statuses"  ts ON ts.code = t.status_code
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_title   ON p_title.task_id   = t.id AND p_title.property_key   = 'title'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_desc    ON p_desc.task_id    = t.id AND p_desc.property_key    = 'description'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_accept  ON p_accept.task_id  = t.id AND p_accept.property_key  = 'acceptance_criteria'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_resolve ON p_resolve.task_id = t.id AND p_resolve.property_key = 'resolution_notes'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_remedy  ON p_remedy.task_id  = t.id AND p_remedy.property_key  = 'remediation_plan'
WHERE t.is_deleted = FALSE;

-- ── 5. Recreate hierarchy views dropped by CASCADE above ───────────────────
-- These were originally created in 20260318 but depend on 40_vw_task_detail

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
    COALESCE(ct.task_count, 0)::int             AS direct_task_count,
    COALESCE(ct.open_task_count, 0)::int        AS direct_open_task_count,
    COALESCE(ct.overdue_task_count, 0)::int     AS direct_overdue_task_count,
    COALESCE(ct.evidence_task_count, 0)::int    AS evidence_task_count,
    COALESCE(ct.remediation_task_count, 0)::int AS remediation_task_count,
    COALESCE(ra.risk_count, 0)::int             AS linked_risk_count,
    COALESCE(ra.critical_risk_count, 0)::int    AS critical_risk_count,
    COALESCE(ra.high_risk_count, 0)::int        AS high_risk_count,
    ra.risk_ids                                 AS linked_risk_ids,
    ra.risk_codes                               AS linked_risk_codes,
    ra.risk_titles                              AS linked_risk_titles,
    ra.risk_levels                              AS linked_risk_levels,
    COALESCE(rt.task_count, 0)::int             AS risk_task_count,
    COALESCE(rt.open_task_count, 0)::int        AS risk_open_task_count
FROM "05_grc_library"."13_fct_controls" c
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" f_name
    ON f_name.framework_id = c.framework_id AND f_name.property_key = 'name'
LEFT JOIN "05_grc_library"."12_fct_requirements" req
    ON req.id = c.requirement_id
LEFT JOIN "05_grc_library"."22_dtl_requirement_properties" req_name
    ON req_name.requirement_id = c.requirement_id AND req_name.property_key = 'name'
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
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm ON rcm.risk_id = t.entity_id
    WHERE rcm.control_id = c.id AND t.entity_type = 'risk' AND NOT t.is_deleted
) rt ON TRUE
WHERE NOT c.is_deleted;

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
    COALESCE(rt.task_count, 0)::int             AS direct_task_count,
    COALESCE(rt.open_task_count, 0)::int        AS direct_open_task_count,
    COALESCE(rt.overdue_task_count, 0)::int     AS direct_overdue_task_count,
    COALESCE(ca.control_count, 0)::int          AS linked_control_count,
    ca.control_ids                              AS linked_control_ids,
    ca.control_codes                            AS linked_control_codes,
    ca.framework_ids                            AS linked_framework_ids,
    ca.framework_names                          AS linked_framework_names,
    COALESCE(ct.task_count, 0)::int             AS control_task_count,
    COALESCE(ct.open_task_count, 0)::int        AS control_open_task_count
FROM "14_risk_registry"."10_fct_risks" r
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" rp
    ON rp.risk_id = r.id AND rp.property_key = 'title'
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_task_count,
        COUNT(*) FILTER (WHERE t.due_date < NOW() AND NOT t.is_terminal)                  AS overdue_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    WHERE t.entity_id = r.id AND t.entity_type = 'risk' AND NOT t.is_deleted
) rt ON TRUE
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
LEFT JOIN LATERAL (
    SELECT
        COUNT(*)                                                                          AS task_count,
        COUNT(*) FILTER (WHERE NOT t.is_terminal)                                         AS open_task_count
    FROM "08_tasks"."40_vw_task_detail" t
    JOIN "14_risk_registry"."30_lnk_risk_control_mappings" rcm ON rcm.control_id = t.entity_id
    WHERE rcm.risk_id = r.id AND t.entity_type = 'control' AND NOT t.is_deleted
) ct ON TRUE
WHERE NOT r.is_deleted;

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
    COALESCE(ct.task_count, 0)::int     AS control_task_count,
    COALESCE(ct.open_count, 0)::int     AS control_open_tasks,
    COALESCE(ct.overdue_count, 0)::int  AS control_overdue_tasks,
    COALESCE(ct.evidence_count, 0)::int AS evidence_task_count,
    COALESCE(ra.risk_count, 0)::int     AS linked_risk_count,
    COALESCE(ra.high_crit, 0)::int      AS high_critical_risk_count,
    ra.risk_codes                       AS risk_codes,
    ra.risk_levels                      AS risk_levels,
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
