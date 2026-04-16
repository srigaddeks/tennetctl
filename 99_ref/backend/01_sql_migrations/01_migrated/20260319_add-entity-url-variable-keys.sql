-- ============================================================================
-- Add entity ID passthrough + deep-link URL computed variable keys
-- ============================================================================
-- These give template authors access to the raw IDs from the audit event
-- (task_id, risk_id, control_id, etc.) and pre-composed deep-link URLs
-- (task_url, risk_url, control_url, framework_url) that work out of the box.
--
-- Resolution source: "computed" — handled by VariableResolver._resolve_computed
-- resolution_key maps to the branch in that method.
-- ============================================================================

-- ── Entity ID pass-throughs ──────────────────────────────────────────────────

INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value,
     resolution_source, resolution_key, sort_order, created_at, updated_at)
VALUES
    -- task
    ('c0000001-0000-0000-0000-000000000001',
     'task_id', 'Task ID', 'UUID of the task from the audit event',
     'string', '3e7a1b2c-...', 'computed', 'task_id', 1010, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- risk
    ('c0000001-0000-0000-0000-000000000002',
     'risk_id', 'Risk ID', 'UUID of the risk from the audit event',
     'string', '5f2b8d1e-...', 'computed', 'risk_id', 1011, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- control
    ('c0000001-0000-0000-0000-000000000003',
     'control_id', 'Control ID', 'UUID of the control from the audit event',
     'string', '9a4c3f7d-...', 'computed', 'control_id', 1012, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- framework
    ('c0000001-0000-0000-0000-000000000004',
     'framework_id', 'Framework ID', 'UUID of the framework from the audit event',
     'string', 'b2e1d5a8-...', 'computed', 'framework_id', 1013, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- org
    ('c0000001-0000-0000-0000-000000000005',
     'org_id', 'Org ID', 'UUID of the organization from the audit event',
     'string', 'd4f6c2b1-...', 'computed', 'org_id', 1014, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- workspace
    ('c0000001-0000-0000-0000-000000000006',
     'workspace_id', 'Workspace ID', 'UUID of the workspace from the audit event',
     'string', 'e7a3b9c5-...', 'computed', 'workspace_id', 1015, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)

ON CONFLICT (code) DO NOTHING;


-- ── Deep-link URL computed variables ─────────────────────────────────────────

INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value,
     resolution_source, resolution_key, sort_order, created_at, updated_at)
VALUES
    -- task URL
    ('c0000002-0000-0000-0000-000000000001',
     'task_url', 'Task URL',
     'Direct link to the task page (base_url/tasks/{task_id})',
     'string', 'https://app.example.com/tasks/3e7a1b2c-...',
     'computed', 'task_url', 1020, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- risk URL
    ('c0000002-0000-0000-0000-000000000002',
     'risk_url', 'Risk URL',
     'Direct link to the risk page (base_url/risks/{risk_id})',
     'string', 'https://app.example.com/risks/5f2b8d1e-...',
     'computed', 'risk_url', 1021, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- control URL
    ('c0000002-0000-0000-0000-000000000003',
     'control_url', 'Control URL',
     'Direct link to the control page (base_url/controls/{control_id})',
     'string', 'https://app.example.com/controls/9a4c3f7d-...',
     'computed', 'control_url', 1022, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),

    -- framework URL
    ('c0000002-0000-0000-0000-000000000004',
     'framework_url', 'Framework URL',
     'Direct link to the framework page (base_url/frameworks/{framework_id})',
     'string', 'https://app.example.com/frameworks/b2e1d5a8-...',
     'computed', 'framework_url', 1023, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)

ON CONFLICT (code) DO NOTHING;
