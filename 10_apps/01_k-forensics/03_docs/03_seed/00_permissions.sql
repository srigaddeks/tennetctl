-- K-Forensics permissions seed (fallback — use 04_seed.py API path first)
-- Run: psql $DATABASE_URL -f 03_seed/00_permissions.sql
-- Idempotent: ON CONFLICT (resource, action) DO NOTHING

INSERT INTO "03_iam"."10_fct_permissions" (id, resource, action, description, is_active)
SELECT
    gen_random_uuid()::text,
    x.resource,
    x.action,
    x.description,
    TRUE
FROM (VALUES
    ('cases',    'read',    'Read cases and investigations'),
    ('cases',    'create',  'Create new cases'),
    ('cases',    'update',  'Update case details'),
    ('cases',    'delete',  'Delete or archive cases'),
    ('evidence', 'read',    'Read evidence items'),
    ('evidence', 'upload',  'Upload evidence files'),
    ('evidence', 'delete',  'Delete evidence items'),
    ('reports',  'read',    'Read investigation reports'),
    ('reports',  'create',  'Generate investigation reports')
) AS x(resource, action, description)
ON CONFLICT (resource, action) DO NOTHING;
