-- UP ====

-- Register the `vault` module in the catalog so feature 02 manifests validate.
-- Must run BEFORE the vault schema migration so the catalog accepts module='vault'
-- when feature.manifest.yaml is upserted on first boot with vault enabled.

INSERT INTO "01_catalog"."01_dim_modules" (id, code, label, description, always_on)
VALUES (
    COALESCE((SELECT MAX(id) + 1 FROM "01_catalog"."01_dim_modules"), 1),
    'vault',
    'Vault',
    'Secret storage with AES-256-GCM envelope encryption. Backs auth secrets, signing keys, Argon2 pepper, OAuth client creds, third-party API tokens. See ADR-028.',
    false
)
ON CONFLICT (code) DO NOTHING;

-- DOWN ====

DELETE FROM "01_catalog"."01_dim_modules" WHERE code = 'vault';
