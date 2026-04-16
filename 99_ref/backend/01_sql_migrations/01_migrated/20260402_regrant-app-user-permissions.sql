-- ─────────────────────────────────────────────────────────────────────────────
-- RE-GRANT APPLICATION USER PERMISSIONS
-- Re-runs the full grant sweep to cover all schemas added after the original
-- 20260327_grant-app-user-permissions.sql ran (notably 12_engagements and any
-- schemas added in later migration phases).
-- Idempotent: PostgreSQL silently ignores duplicate grants.
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    schema_name TEXT;
    role_name   TEXT;
BEGIN
    -- Grant to all write roles
    FOR role_name IN
        SELECT rolname FROM pg_roles WHERE rolname LIKE 'kcontrol_%_write'
    LOOP
        FOR schema_name IN
            SELECT s.schema_name FROM information_schema.schemata s
            WHERE s.schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'public')
              AND s.schema_name NOT LIKE 'pg_%'
        LOOP
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I', schema_name, role_name);
            EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA %I TO %I', schema_name, role_name);
            EXECUTE format('GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA %I TO %I', schema_name, role_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO %I', schema_name, role_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT USAGE, SELECT ON SEQUENCES TO %I', schema_name, role_name);
        END LOOP;
        RAISE NOTICE 'Granted write permissions to %', role_name;
    END LOOP;

    -- Grant to all read roles
    FOR role_name IN
        SELECT rolname FROM pg_roles WHERE rolname LIKE 'kcontrol_%_read'
    LOOP
        FOR schema_name IN
            SELECT s.schema_name FROM information_schema.schemata s
            WHERE s.schema_name NOT IN ('pg_catalog', 'information_schema', 'pg_toast', 'public')
              AND s.schema_name NOT LIKE 'pg_%'
        LOOP
            EXECUTE format('GRANT USAGE ON SCHEMA %I TO %I', schema_name, role_name);
            EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO %I', schema_name, role_name);
            EXECUTE format('ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT ON TABLES TO %I', schema_name, role_name);
        END LOOP;
        RAISE NOTICE 'Granted read permissions to %', role_name;
    END LOOP;
END
$$;
