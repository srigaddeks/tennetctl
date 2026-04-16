-- UP ====

-- Extend "03_iam"."03_dim_scopes" with feature-flag scopes.
-- IDs 1-6 are the generic read/write/admin × all/org scopes from Phase 3 bootstrap.
-- IDs 7-11 are flag-specific, added here as a one-shot migration (seed YAMLs are
-- already tracked by the migrator; writing a new seed would double-register).

INSERT INTO "03_iam"."03_dim_scopes" (id, code, label, scope_level, description)
VALUES
    (7,  'flags:view:org',   'Flags: View (Org)',   'org',    'Read flag definitions within an org'),
    (8,  'flags:toggle:org', 'Flags: Toggle (Org)', 'org',    'Enable or disable flag states within an org (no other edits)'),
    (9,  'flags:write:org',  'Flags: Write (Org)',  'org',    'Create / update flags, rules, and overrides within an org'),
    (10, 'flags:admin:org',  'Flags: Admin (Org)',  'org',    'Full flag management within an org including per-flag permissions'),
    (11, 'flags:admin:all',  'Flags: Admin (All)',  'global', 'Full flag management across all orgs including global flags')
ON CONFLICT (id) DO NOTHING;

-- DOWN ====

DELETE FROM "03_iam"."03_dim_scopes" WHERE id IN (7, 8, 9, 10, 11);
