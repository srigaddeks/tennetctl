-- UP ====

-- Register the `featureflags` module in the catalog so feature 09 manifests validate.
-- id is not hard-coded; dim_modules uses its own identity sequence.

INSERT INTO "01_catalog"."01_dim_modules" (id, code, label, description, always_on)
VALUES (
    COALESCE((SELECT MAX(id) + 1 FROM "01_catalog"."01_dim_modules"), 1),
    'featureflags',
    'Feature Flags',
    'Flag definitions, per-environment state, targeting rules, overrides, per-flag RBAC, and evaluator.',
    true
)
ON CONFLICT (code) DO NOTHING;

-- DOWN ====

DELETE FROM "01_catalog"."01_dim_modules" WHERE code = 'featureflags';
