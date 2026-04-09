-- kprotect permissions seed
-- Inserts all kprotect resource/action pairs into 03_iam.10_fct_permissions.
-- Idempotent: ON CONFLICT DO NOTHING.

INSERT INTO "03_iam"."10_fct_permissions" (id, resource, action, description, is_active)
SELECT gen_random_uuid()::text, x.resource, x.action, x.description, TRUE
FROM (VALUES
    ('policies',      'read',    'Read kprotect policies'),
    ('policies',      'create',  'Create kprotect policies'),
    ('policies',      'update',  'Update kprotect policies'),
    ('policies',      'delete',  'Delete kprotect policies'),
    ('policies',      'execute', 'Execute/test kprotect policies'),
    ('policy_sets',   'read',    'Read kprotect policy sets'),
    ('policy_sets',   'create',  'Create kprotect policy sets'),
    ('policy_sets',   'update',  'Update kprotect policy sets'),
    ('policy_sets',   'delete',  'Delete kprotect policy sets'),
    ('decisions',     'read',    'Read kprotect decision history'),
    ('library',       'read',    'Read kprotect policy library'),
    ('library',       'install', 'Install library policies into org'),
    ('evaluate',      'execute', 'Call the kprotect evaluate endpoint'),
    ('api_keys',      'read',    'Read kprotect API keys'),
    ('api_keys',      'create',  'Create kprotect API keys'),
    ('api_keys',      'revoke',  'Revoke kprotect API keys')
) AS x(resource, action, description)
ON CONFLICT (resource, action) DO NOTHING;
