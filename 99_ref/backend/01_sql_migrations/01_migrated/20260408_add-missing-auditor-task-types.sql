-- Add missing task types for auditor workspace
-- These codes are used by the frontend EvidenceTasksTab to track auditor follow-up tasks

INSERT INTO "08_tasks"."02_dim_task_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('b1c10005-0000-0000-0000-000000000000', 'evidence_request', 'Evidence Request', 'Auditor request for specific evidence items', 5, TRUE, NOW(), NOW()),
    ('b1c10006-0000-0000-0000-000000000000', 'remediation',      'Remediation',      'Task to remediate a finding or gap',       6, TRUE, NOW(), NOW()),
    ('b1c10007-0000-0000-0000-000000000000', 'review',           'Review',           'Auditor review of submitted evidence',      7, TRUE, NOW(), NOW()),
    ('b1c10008-0000-0000-0000-000000000000', 'documentation',    'Documentation',    'Update or provide missing documentation',   8, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
