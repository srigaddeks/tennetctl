-- ============================================================================
-- Seed portal view assignments for the platform admin role
-- ============================================================================
-- Assigns all 5 portal views to the platform admin role so that super admins
-- can see the view switcher bar and test all role perspectives.
-- ============================================================================

INSERT INTO "03_auth_manage"."51_lnk_role_views" (role_id, view_code)
VALUES
    ('00000000-0000-0000-0000-000000000601', 'grc'),
    ('00000000-0000-0000-0000-000000000601', 'auditor'),
    ('00000000-0000-0000-0000-000000000601', 'engineering'),
    ('00000000-0000-0000-0000-000000000601', 'executive'),
    ('00000000-0000-0000-0000-000000000601', 'vendor')
ON CONFLICT (role_id, view_code) DO NOTHING;
