-- ============================================================================
-- Notification Variable Query Views + System Queries
-- ============================================================================
-- 1. Creates lightweight notification-specific views for variable resolution
-- 2. Adds is_system column to variable queries
-- 3. Seeds system queries using those views
-- ============================================================================

-- ── Add is_system column ────────────────────────────────────────────────────

ALTER TABLE "03_notifications"."31_fct_variable_queries"
    ADD COLUMN IF NOT EXISTS is_system BOOLEAN NOT NULL DEFAULT FALSE;

-- ============================================================================
-- NOTIFICATION VARIABLE RESOLUTION VIEWS
-- ============================================================================
-- These views are purpose-built for notification template variable queries.
-- They flatten EAV patterns into simple columns so system queries are clean SELECTs.

-- ── 50_vw_user_profile ──────────────────────────────────────────────────────
-- Full user profile: flattens 05_dtl_user_properties into named columns

CREATE OR REPLACE VIEW "03_auth_manage"."50_vw_user_profile" AS
SELECT
    u.id                        AS user_id,
    u.tenant_key,
    u.is_active,
    p_email.property_value      AS email,
    p_username.property_value   AS username,
    p_first.property_value      AS first_name,
    p_last.property_value       AS last_name,
    p_display.property_value    AS display_name,
    p_tz.property_value         AS timezone,
    u.created_at
FROM "03_auth_manage"."03_fct_users" u
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" p_email
    ON p_email.user_id = u.id AND p_email.property_key = 'email'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" p_username
    ON p_username.user_id = u.id AND p_username.property_key = 'username'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" p_first
    ON p_first.user_id = u.id AND p_first.property_key = 'first_name'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" p_last
    ON p_last.user_id = u.id AND p_last.property_key = 'last_name'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" p_display
    ON p_display.user_id = u.id AND p_display.property_key = 'display_name'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" p_tz
    ON p_tz.user_id = u.id AND p_tz.property_key = 'timezone'
WHERE u.is_deleted = FALSE;

-- ── 51_vw_org_detail ────────────────────────────────────────────────────────
-- Org with type name for notification context

CREATE OR REPLACE VIEW "03_auth_manage"."51_vw_org_detail" AS
SELECT
    o.id                AS org_id,
    o.tenant_key,
    o.name              AS org_name,
    o.code              AS org_code,
    ot.name             AS org_type_name,
    o.is_active,
    o.created_at
FROM "03_auth_manage"."29_fct_orgs" o
LEFT JOIN "03_auth_manage"."28_dim_org_types" ot
    ON ot.code = o.org_type_code
WHERE o.is_deleted = FALSE;

-- ── 52_vw_workspace_detail ──────────────────────────────────────────────────
-- Workspace with org name for notification context

CREATE OR REPLACE VIEW "03_auth_manage"."52_vw_workspace_detail" AS
SELECT
    w.id                AS workspace_id,
    w.org_id,
    o.tenant_key,
    w.name              AS workspace_name,
    w.code              AS workspace_code,
    wt.name             AS workspace_type_name,
    o.name              AS org_name,
    w.is_active,
    w.created_at
FROM "03_auth_manage"."34_fct_workspaces" w
LEFT JOIN "03_auth_manage"."33_dim_workspace_types" wt
    ON wt.code = w.workspace_type_code
LEFT JOIN "03_auth_manage"."29_fct_orgs" o
    ON o.id = w.org_id
WHERE w.is_deleted = FALSE;

-- ── 50_vw_task_notification ─────────────────────────────────────────────────
-- Task flattened for notification variables: title, status, priority, assignee, reporter, due date

CREATE OR REPLACE VIEW "08_tasks"."50_vw_task_notification" AS
SELECT
    t.id                    AS task_id,
    t.tenant_key,
    t.org_id,
    t.workspace_id,
    t.task_type_code,
    t.priority_code,
    t.status_code,
    t.due_date,
    t.completed_at,
    t.assignee_user_id,
    t.reporter_user_id,
    p_title.property_value  AS title,
    p_desc.property_value   AS description,
    -- Assignee profile
    a_profile.display_name  AS assignee_name,
    a_profile.email         AS assignee_email,
    -- Reporter profile
    r_profile.display_name  AS reporter_name,
    r_profile.email         AS reporter_email,
    -- Org + workspace context
    o.name                  AS org_name,
    w.name                  AS workspace_name,
    t.entity_type,
    t.entity_id
FROM "08_tasks"."10_fct_tasks" t
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_title
    ON p_title.task_id = t.id AND p_title.property_key = 'title'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_desc
    ON p_desc.task_id = t.id AND p_desc.property_key = 'description'
LEFT JOIN "03_auth_manage"."50_vw_user_profile" a_profile
    ON a_profile.user_id = t.assignee_user_id
LEFT JOIN "03_auth_manage"."50_vw_user_profile" r_profile
    ON r_profile.user_id = t.reporter_user_id
LEFT JOIN "03_auth_manage"."29_fct_orgs" o
    ON o.id = t.org_id
LEFT JOIN "03_auth_manage"."34_fct_workspaces" w
    ON w.id = t.workspace_id
WHERE t.is_deleted = FALSE;

-- ── 50_vw_risk_notification ─────────────────────────────────────────────────
-- Risk flattened for notification: title, level, category, owner, treatment status

CREATE OR REPLACE VIEW "14_risk_registry"."50_vw_risk_notification" AS
SELECT
    r.id                        AS risk_id,
    r.tenant_key,
    r.org_id,
    r.workspace_id,
    r.risk_code,
    r.risk_category_code,
    r.risk_level_code,
    r.treatment_type_code,
    r.risk_status,
    p_title.property_value      AS title,
    p_desc.property_value       AS description,
    p_owner.property_value      AS owner_user_id,
    -- Owner profile
    owner_profile.display_name  AS owner_name,
    owner_profile.email         AS owner_email,
    -- Category label
    cat.name                    AS risk_category_name,
    lvl.name                    AS risk_level_name,
    -- Org + workspace
    o.name                      AS org_name,
    w.name                      AS workspace_name,
    -- Latest assessment
    latest_assess.risk_score    AS latest_risk_score
FROM "14_risk_registry"."10_fct_risks" r
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_title
    ON p_title.risk_id = r.id AND p_title.property_key = 'title'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_desc
    ON p_desc.risk_id = r.id AND p_desc.property_key = 'description'
LEFT JOIN "14_risk_registry"."20_dtl_risk_properties" p_owner
    ON p_owner.risk_id = r.id AND p_owner.property_key = 'owner_user_id'
LEFT JOIN "03_auth_manage"."50_vw_user_profile" owner_profile
    ON owner_profile.user_id::text = p_owner.property_value
LEFT JOIN "14_risk_registry"."02_dim_risk_categories" cat
    ON cat.code = r.risk_category_code
LEFT JOIN "14_risk_registry"."04_dim_risk_levels" lvl
    ON lvl.code = r.risk_level_code
LEFT JOIN "03_auth_manage"."29_fct_orgs" o
    ON o.id = r.org_id
LEFT JOIN "03_auth_manage"."34_fct_workspaces" w
    ON w.id = r.workspace_id
LEFT JOIN LATERAL (
    SELECT a.risk_score
    FROM "14_risk_registry"."32_trx_risk_assessments" a
    WHERE a.risk_id = r.id
    ORDER BY a.assessed_at DESC
    LIMIT 1
) latest_assess ON TRUE
WHERE r.is_deleted = FALSE;

-- ── 50_vw_control_notification ──────────────────────────────────────────────
-- Control flattened for notification: code, name, category, criticality, framework

CREATE OR REPLACE VIEW "05_grc_library"."50_vw_control_notification" AS
SELECT
    c.id                        AS control_id,
    c.tenant_key,
    c.framework_id,
    c.control_code,
    c.control_category_code,
    c.criticality_code,
    c.control_type,
    p_name.property_value       AS control_name,
    p_desc.property_value       AS description,
    p_guide.property_value      AS guidance,
    -- Category + criticality labels
    cat.name                    AS category_name,
    crit.name                   AS criticality_name,
    -- Framework info
    fw_name.property_value      AS framework_name,
    fw.framework_code
FROM "05_grc_library"."13_fct_controls" c
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_name
    ON p_name.control_id = c.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_desc
    ON p_desc.control_id = c.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."23_dtl_control_properties" p_guide
    ON p_guide.control_id = c.id AND p_guide.property_key = 'guidance'
LEFT JOIN "05_grc_library"."04_dim_control_categories" cat
    ON cat.code = c.control_category_code
LEFT JOIN "05_grc_library"."05_dim_control_criticalities" crit
    ON crit.code = c.criticality_code
LEFT JOIN "05_grc_library"."10_fct_frameworks" fw
    ON fw.id = c.framework_id
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" fw_name
    ON fw_name.framework_id = fw.id AND fw_name.property_key = 'name'
WHERE c.is_deleted = FALSE;

-- ── 50_vw_framework_notification ────────────────────────────────────────────
-- Framework flattened for notification: name, type, category, publisher

CREATE OR REPLACE VIEW "05_grc_library"."50_vw_framework_notification" AS
SELECT
    f.id                        AS framework_id,
    f.tenant_key,
    f.framework_code,
    f.framework_type_code,
    f.framework_category_code,
    p_name.property_value       AS framework_name,
    p_desc.property_value       AS description,
    p_pub.property_value        AS publisher_name,
    ft.name                     AS framework_type_name,
    fc.name                     AS framework_category_name
FROM "05_grc_library"."10_fct_frameworks" f
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_name
    ON p_name.framework_id = f.id AND p_name.property_key = 'name'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_desc
    ON p_desc.framework_id = f.id AND p_desc.property_key = 'description'
LEFT JOIN "05_grc_library"."20_dtl_framework_properties" p_pub
    ON p_pub.framework_id = f.id AND p_pub.property_key = 'publisher_name'
LEFT JOIN "05_grc_library"."02_dim_framework_types" ft
    ON ft.code = f.framework_type_code
LEFT JOIN "05_grc_library"."03_dim_framework_categories" fc
    ON fc.code = f.framework_category_code
WHERE f.is_deleted = FALSE;


-- ============================================================================
-- SYSTEM VARIABLE QUERIES (using views above)
-- ============================================================================

-- ── user_profile: full user profile for recipient ───────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000001',
    '__system__',
    'user_profile',
    'User Profile',
    'Full profile of the notification recipient: name, email, username, timezone.',
    'SELECT first_name, last_name, display_name, email, username, timezone FROM "03_auth_manage"."50_vw_user_profile" WHERE user_id = $1',
    '[{"key": "$user_id", "position": 1, "source": "context", "required": true}]'::jsonb,
    '[{"name": "first_name", "data_type": "string"}, {"name": "last_name", "data_type": "string"}, {"name": "display_name", "data_type": "string"}, {"name": "email", "data_type": "string"}, {"name": "username", "data_type": "string"}, {"name": "timezone", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── actor_profile: full profile of who triggered the event ──────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000002',
    '__system__',
    'actor_profile',
    'Actor Profile',
    'Full profile of the actor who triggered the audit event: name, email.',
    'SELECT first_name, last_name, display_name, email, username FROM "03_auth_manage"."50_vw_user_profile" WHERE user_id = $1',
    '[{"key": "$actor_id", "position": 1, "source": "context", "required": true}]'::jsonb,
    '[{"name": "first_name", "data_type": "string"}, {"name": "last_name", "data_type": "string"}, {"name": "display_name", "data_type": "string"}, {"name": "email", "data_type": "string"}, {"name": "username", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── org_detail: org name, slug, type ────────────────────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000003',
    '__system__',
    'org_detail',
    'Organization Detail',
    'Organization name, slug, and type from the org_id in event context.',
    'SELECT org_name, org_code, org_type_name FROM "03_auth_manage"."51_vw_org_detail" WHERE org_id = $1',
    '[{"key": "$org_id", "position": 1, "source": "context", "required": true}]'::jsonb,
    '[{"name": "org_name", "data_type": "string"}, {"name": "org_code", "data_type": "string"}, {"name": "org_type_name", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── workspace_detail: workspace name, slug, org ─────────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000004',
    '__system__',
    'workspace_detail',
    'Workspace Detail',
    'Workspace name, slug, type, and parent org name.',
    'SELECT workspace_name, workspace_code, workspace_type_name, org_name FROM "03_auth_manage"."52_vw_workspace_detail" WHERE workspace_id = $1',
    '[{"key": "$workspace_id", "position": 1, "source": "context", "required": true}]'::jsonb,
    '[{"name": "workspace_name", "data_type": "string"}, {"name": "workspace_code", "data_type": "string"}, {"name": "workspace_type_name", "data_type": "string"}, {"name": "org_name", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── task_detail: full task for notifications ─────────────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000005',
    '__system__',
    'task_detail',
    'Task Detail',
    'Full task context: title, status, priority, assignee, reporter, due date, org, workspace.',
    'SELECT title, description, status_code, priority_code, task_type_code, assignee_name, assignee_email, reporter_name, reporter_email, org_name, workspace_name, due_date::text AS due_date FROM "08_tasks"."50_vw_task_notification" WHERE task_id = $1',
    '[{"key": "$task_id", "position": 1, "source": "audit_property", "required": true}]'::jsonb,
    '[{"name": "title", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "status_code", "data_type": "string"}, {"name": "priority_code", "data_type": "string"}, {"name": "task_type_code", "data_type": "string"}, {"name": "assignee_name", "data_type": "string"}, {"name": "assignee_email", "data_type": "string"}, {"name": "reporter_name", "data_type": "string"}, {"name": "reporter_email", "data_type": "string"}, {"name": "org_name", "data_type": "string"}, {"name": "workspace_name", "data_type": "string"}, {"name": "due_date", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── risk_detail: full risk for notifications ─────────────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000006',
    '__system__',
    'risk_detail',
    'Risk Detail',
    'Full risk context: title, level, category, owner, treatment type, latest score, org, workspace.',
    'SELECT risk_code, title, description, risk_level_code, risk_level_name, risk_category_code, risk_category_name, risk_status, treatment_type_code, owner_name, owner_email, org_name, workspace_name, latest_risk_score::text AS latest_risk_score FROM "14_risk_registry"."50_vw_risk_notification" WHERE risk_id = $1',
    '[{"key": "$risk_id", "position": 1, "source": "audit_property", "required": true}]'::jsonb,
    '[{"name": "risk_code", "data_type": "string"}, {"name": "title", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "risk_level_code", "data_type": "string"}, {"name": "risk_level_name", "data_type": "string"}, {"name": "risk_category_code", "data_type": "string"}, {"name": "risk_category_name", "data_type": "string"}, {"name": "risk_status", "data_type": "string"}, {"name": "treatment_type_code", "data_type": "string"}, {"name": "owner_name", "data_type": "string"}, {"name": "owner_email", "data_type": "string"}, {"name": "org_name", "data_type": "string"}, {"name": "workspace_name", "data_type": "string"}, {"name": "latest_risk_score", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── control_detail: full control for notifications ───────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000007',
    '__system__',
    'control_detail',
    'Control Detail',
    'Full control context: code, name, category, criticality, guidance, framework name.',
    'SELECT control_code, control_name, description, guidance, category_name, criticality_name, control_type, framework_name, framework_code FROM "05_grc_library"."50_vw_control_notification" WHERE control_id = $1',
    '[{"key": "$control_id", "position": 1, "source": "audit_property", "required": true}]'::jsonb,
    '[{"name": "control_code", "data_type": "string"}, {"name": "control_name", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "guidance", "data_type": "string"}, {"name": "category_name", "data_type": "string"}, {"name": "criticality_name", "data_type": "string"}, {"name": "control_type", "data_type": "string"}, {"name": "framework_name", "data_type": "string"}, {"name": "framework_code", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;

-- ── framework_detail: framework for notifications ────────────────────────────
INSERT INTO "03_notifications"."31_fct_variable_queries"
    (id, tenant_key, code, name, description, sql_template, bind_params, result_columns, timeout_ms, is_system, created_at, updated_at)
VALUES (
    'a0000001-0000-0000-0000-000000000008',
    '__system__',
    'framework_detail',
    'Framework Detail',
    'Framework name, type, category, publisher for notification context.',
    'SELECT framework_code, framework_name, description, publisher_name, framework_type_name, framework_category_name FROM "05_grc_library"."50_vw_framework_notification" WHERE framework_id = $1',
    '[{"key": "$framework_id", "position": 1, "source": "audit_property", "required": true}]'::jsonb,
    '[{"name": "framework_code", "data_type": "string"}, {"name": "framework_name", "data_type": "string"}, {"name": "description", "data_type": "string"}, {"name": "publisher_name", "data_type": "string"}, {"name": "framework_type_name", "data_type": "string"}, {"name": "framework_category_name", "data_type": "string"}]'::jsonb,
    3000, TRUE, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
) ON CONFLICT (tenant_key, code) DO NOTHING;


-- ============================================================================
-- TEMPLATE VARIABLE KEYS (one per result column)
-- ============================================================================

-- ── user_profile keys ───────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000001', 'custom.user_profile.first_name',    'User First Name',    'Recipient first name',    'string', 'Sri',             'custom_query', 'first_name',    'a0000001-0000-0000-0000-000000000001', 900, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000002', 'custom.user_profile.last_name',     'User Last Name',     'Recipient last name',     'string', 'Kumar',           'custom_query', 'last_name',     'a0000001-0000-0000-0000-000000000001', 901, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000003', 'custom.user_profile.display_name',  'User Display Name',  'Recipient display name',  'string', 'Sri K',           'custom_query', 'display_name',  'a0000001-0000-0000-0000-000000000001', 902, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000004', 'custom.user_profile.email',         'User Email',         'Recipient email',         'string', 'sri@example.com', 'custom_query', 'email',         'a0000001-0000-0000-0000-000000000001', 903, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000005', 'custom.user_profile.username',      'User Username',      'Recipient username',      'string', 'sri',             'custom_query', 'username',      'a0000001-0000-0000-0000-000000000001', 904, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000006', 'custom.user_profile.timezone',      'User Timezone',      'Recipient timezone',      'string', 'America/Chicago', 'custom_query', 'timezone',      'a0000001-0000-0000-0000-000000000001', 905, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── actor_profile keys ──────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000010', 'custom.actor_profile.first_name',   'Actor First Name',   'Actor first name',   'string', 'John',              'custom_query', 'first_name',   'a0000001-0000-0000-0000-000000000002', 910, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000011', 'custom.actor_profile.last_name',    'Actor Last Name',    'Actor last name',    'string', 'Admin',             'custom_query', 'last_name',    'a0000001-0000-0000-0000-000000000002', 911, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000012', 'custom.actor_profile.display_name', 'Actor Display Name', 'Actor display name', 'string', 'John Admin',        'custom_query', 'display_name', 'a0000001-0000-0000-0000-000000000002', 912, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000013', 'custom.actor_profile.email',        'Actor Email',        'Actor email',        'string', 'admin@example.com', 'custom_query', 'email',        'a0000001-0000-0000-0000-000000000002', 913, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000014', 'custom.actor_profile.username',     'Actor Username',     'Actor username',     'string', 'admin',             'custom_query', 'username',     'a0000001-0000-0000-0000-000000000002', 914, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── org_detail keys ─────────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000020', 'custom.org_detail.org_name',       'Org Name',       'Organization name',  'string', 'Acme Corp',   'custom_query', 'org_name',       'a0000001-0000-0000-0000-000000000003', 920, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000021', 'custom.org_detail.org_code',       'Org Code',       'Organization slug',  'string', 'acme-corp',   'custom_query', 'org_code',       'a0000001-0000-0000-0000-000000000003', 921, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000022', 'custom.org_detail.org_type_name',  'Org Type',       'Organization type',  'string', 'Enterprise',  'custom_query', 'org_type_name',  'a0000001-0000-0000-0000-000000000003', 922, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── workspace_detail keys ───────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000030', 'custom.workspace_detail.workspace_name',      'Workspace Name',      'Workspace name',                    'string', 'Production',    'custom_query', 'workspace_name',      'a0000001-0000-0000-0000-000000000004', 930, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000031', 'custom.workspace_detail.workspace_code',      'Workspace Code',      'Workspace slug',                    'string', 'production',    'custom_query', 'workspace_code',      'a0000001-0000-0000-0000-000000000004', 931, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000032', 'custom.workspace_detail.workspace_type_name', 'Workspace Type',      'Workspace type',                    'string', 'Compliance',    'custom_query', 'workspace_type_name', 'a0000001-0000-0000-0000-000000000004', 932, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000033', 'custom.workspace_detail.org_name',            'Workspace Org Name',  'Parent org of workspace',           'string', 'Acme Corp',     'custom_query', 'org_name',            'a0000001-0000-0000-0000-000000000004', 933, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── task_detail keys ────────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000040', 'custom.task_detail.title',           'Task Title',          'Task title',                  'string', 'Review access policies',     'custom_query', 'title',           'a0000001-0000-0000-0000-000000000005', 940, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000041', 'custom.task_detail.description',     'Task Description',    'Task description',            'string', 'Quarterly access review',    'custom_query', 'description',     'a0000001-0000-0000-0000-000000000005', 941, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000042', 'custom.task_detail.status_code',     'Task Status',         'Task status code',            'string', 'in_progress',                'custom_query', 'status_code',     'a0000001-0000-0000-0000-000000000005', 942, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000043', 'custom.task_detail.priority_code',   'Task Priority',       'Task priority',               'string', 'high',                       'custom_query', 'priority_code',   'a0000001-0000-0000-0000-000000000005', 943, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000044', 'custom.task_detail.task_type_code',  'Task Type',           'Task type',                   'string', 'control_remediation',        'custom_query', 'task_type_code',  'a0000001-0000-0000-0000-000000000005', 944, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000045', 'custom.task_detail.assignee_name',   'Task Assignee Name',  'Assignee display name',       'string', 'Jane Engineer',              'custom_query', 'assignee_name',   'a0000001-0000-0000-0000-000000000005', 945, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000046', 'custom.task_detail.assignee_email',  'Task Assignee Email', 'Assignee email',              'string', 'jane@example.com',           'custom_query', 'assignee_email',  'a0000001-0000-0000-0000-000000000005', 946, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000047', 'custom.task_detail.reporter_name',   'Task Reporter Name',  'Reporter display name',       'string', 'John Admin',                 'custom_query', 'reporter_name',   'a0000001-0000-0000-0000-000000000005', 947, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000048', 'custom.task_detail.reporter_email',  'Task Reporter Email', 'Reporter email',              'string', 'admin@example.com',          'custom_query', 'reporter_email',  'a0000001-0000-0000-0000-000000000005', 948, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000049', 'custom.task_detail.org_name',        'Task Org',            'Task org name',               'string', 'Acme Corp',                  'custom_query', 'org_name',        'a0000001-0000-0000-0000-000000000005', 949, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-00000000004a', 'custom.task_detail.workspace_name',  'Task Workspace',      'Task workspace name',         'string', 'Production',                 'custom_query', 'workspace_name',  'a0000001-0000-0000-0000-000000000005', 950, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-00000000004b', 'custom.task_detail.due_date',        'Task Due Date',       'Task due date',               'string', '2026-04-01',                 'custom_query', 'due_date',        'a0000001-0000-0000-0000-000000000005', 951, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── risk_detail keys ────────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000050', 'custom.risk_detail.risk_code',            'Risk Code',           'Risk code',                   'string', 'RSK-042',               'custom_query', 'risk_code',            'a0000001-0000-0000-0000-000000000006', 960, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000051', 'custom.risk_detail.title',                'Risk Title',          'Risk title',                  'string', 'Unauthorized access',   'custom_query', 'title',                'a0000001-0000-0000-0000-000000000006', 961, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000052', 'custom.risk_detail.description',          'Risk Description',    'Risk description',            'string', 'Data breach risk',      'custom_query', 'description',          'a0000001-0000-0000-0000-000000000006', 962, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000053', 'custom.risk_detail.risk_level_code',      'Risk Level Code',     'Risk level code',             'string', 'high',                  'custom_query', 'risk_level_code',      'a0000001-0000-0000-0000-000000000006', 963, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000054', 'custom.risk_detail.risk_level_name',      'Risk Level Name',     'Risk level human name',       'string', 'High',                  'custom_query', 'risk_level_name',      'a0000001-0000-0000-0000-000000000006', 964, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000055', 'custom.risk_detail.risk_category_name',   'Risk Category',       'Risk category name',          'string', 'Technology',            'custom_query', 'risk_category_name',   'a0000001-0000-0000-0000-000000000006', 965, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000056', 'custom.risk_detail.risk_status',          'Risk Status',         'Risk status',                 'string', 'identified',            'custom_query', 'risk_status',          'a0000001-0000-0000-0000-000000000006', 966, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000057', 'custom.risk_detail.treatment_type_code',  'Risk Treatment',      'Treatment type',              'string', 'mitigate',              'custom_query', 'treatment_type_code',  'a0000001-0000-0000-0000-000000000006', 967, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000058', 'custom.risk_detail.owner_name',           'Risk Owner Name',     'Risk owner display name',     'string', 'Jane Engineer',         'custom_query', 'owner_name',           'a0000001-0000-0000-0000-000000000006', 968, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000059', 'custom.risk_detail.owner_email',          'Risk Owner Email',    'Risk owner email',            'string', 'jane@example.com',      'custom_query', 'owner_email',          'a0000001-0000-0000-0000-000000000006', 969, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-00000000005a', 'custom.risk_detail.org_name',             'Risk Org',            'Risk org name',               'string', 'Acme Corp',             'custom_query', 'org_name',             'a0000001-0000-0000-0000-000000000006', 970, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-00000000005b', 'custom.risk_detail.workspace_name',       'Risk Workspace',      'Risk workspace name',         'string', 'Production',            'custom_query', 'workspace_name',       'a0000001-0000-0000-0000-000000000006', 971, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-00000000005c', 'custom.risk_detail.latest_risk_score',    'Risk Score',          'Latest risk assessment score', 'string', '12',                   'custom_query', 'latest_risk_score',    'a0000001-0000-0000-0000-000000000006', 972, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── control_detail keys ─────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000060', 'custom.control_detail.control_code',      'Control Code',        'Control code',                'string', 'AC-001',                'custom_query', 'control_code',      'a0000001-0000-0000-0000-000000000007', 980, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000061', 'custom.control_detail.control_name',      'Control Name',        'Control name',                'string', 'Access Control Review', 'custom_query', 'control_name',      'a0000001-0000-0000-0000-000000000007', 981, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000062', 'custom.control_detail.description',       'Control Description', 'Control description',         'string', 'Periodic access audit', 'custom_query', 'description',       'a0000001-0000-0000-0000-000000000007', 982, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000063', 'custom.control_detail.guidance',          'Control Guidance',    'Implementation guidance',     'string', 'Review quarterly',      'custom_query', 'guidance',          'a0000001-0000-0000-0000-000000000007', 983, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000064', 'custom.control_detail.category_name',     'Control Category',    'Control category name',       'string', 'Access Control',        'custom_query', 'category_name',     'a0000001-0000-0000-0000-000000000007', 984, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000065', 'custom.control_detail.criticality_name',  'Control Criticality', 'Control criticality level',   'string', 'High',                  'custom_query', 'criticality_name',  'a0000001-0000-0000-0000-000000000007', 985, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000066', 'custom.control_detail.framework_name',    'Control Framework',   'Parent framework name',       'string', 'SOC 2',                 'custom_query', 'framework_name',    'a0000001-0000-0000-0000-000000000007', 986, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000067', 'custom.control_detail.framework_code',    'Framework Code',      'Parent framework code',       'string', 'soc2-2024',             'custom_query', 'framework_code',    'a0000001-0000-0000-0000-000000000007', 987, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;

-- ── framework_detail keys ───────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, query_id, sort_order, created_at, updated_at)
VALUES
    ('b0000001-0000-0000-0000-000000000070', 'custom.framework_detail.framework_code',          'Framework Code',     'Framework code',              'string', 'soc2-2024',           'custom_query', 'framework_code',          'a0000001-0000-0000-0000-000000000008', 990, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000071', 'custom.framework_detail.framework_name',          'Framework Name',     'Framework name',              'string', 'SOC 2',               'custom_query', 'framework_name',          'a0000001-0000-0000-0000-000000000008', 991, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000072', 'custom.framework_detail.description',             'Framework Desc',     'Framework description',       'string', 'Service org controls', 'custom_query', 'description',             'a0000001-0000-0000-0000-000000000008', 992, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000073', 'custom.framework_detail.publisher_name',          'Framework Publisher', 'Publisher name',              'string', 'AICPA',               'custom_query', 'publisher_name',          'a0000001-0000-0000-0000-000000000008', 993, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000074', 'custom.framework_detail.framework_type_name',     'Framework Type',     'Framework type',              'string', 'Security Framework',  'custom_query', 'framework_type_name',     'a0000001-0000-0000-0000-000000000008', 994, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('b0000001-0000-0000-0000-000000000075', 'custom.framework_detail.framework_category_name', 'Framework Category', 'Framework category',          'string', 'Security',            'custom_query', 'framework_category_name', 'a0000001-0000-0000-0000-000000000008', 995, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
ON CONFLICT (code) DO NOTHING;
