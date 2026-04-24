-- UP ====
CREATE SCHEMA IF NOT EXISTS "11_somaerp";
COMMENT ON SCHEMA "11_somaerp" IS 'somaerp app — Phase 56 v0.9.0';

-- DOWN ====
DROP SCHEMA IF EXISTS "11_somaerp" CASCADE;
