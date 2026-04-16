-- Migration: Add user property keys for onboarding flow
-- These keys support the post-registration onboarding wizard:
--   first_name / last_name  — collected during setup, used to compose display_name
--   default_org_id          — user's preferred/default organization UUID
--   default_workspace_id    — user's preferred/default workspace UUID (K-Control ws)
--   onboarding_complete     — gate flag; 'true' once wizard finishes

INSERT INTO "03_auth_manage"."04_dim_user_property_keys"
    (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
SELECT v.id::UUID, v.code, v.name, v.description, v.data_type, v.is_pii, v.is_required, v.sort_order,
       TIMESTAMP '2026-03-14 00:00:00', TIMESTAMP '2026-03-14 00:00:00'
FROM (VALUES
    ('00000000-0000-0000-0001-000000000010', 'first_name',           'First Name',            'User''s given / first name',                     'string',  TRUE,  FALSE, 100),
    ('00000000-0000-0000-0001-000000000011', 'last_name',            'Last Name',             'User''s family / last name',                     'string',  TRUE,  FALSE, 110),
    ('00000000-0000-0000-0001-000000000012', 'default_org_id',       'Default Org ID',        'UUID of the user''s default organization',       'string',  FALSE, FALSE, 120),
    ('00000000-0000-0000-0001-000000000013', 'default_workspace_id', 'Default Workspace ID',  'UUID of the user''s default workspace',          'string',  FALSE, FALSE, 130),
    ('00000000-0000-0000-0001-000000000014', 'onboarding_complete',  'Onboarding Complete',   'Set to true once the setup wizard is finished',  'boolean', FALSE, FALSE, 140)
) AS v(id, code, name, description, data_type, is_pii, is_required, sort_order)
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."04_dim_user_property_keys" WHERE code = v.code
);
