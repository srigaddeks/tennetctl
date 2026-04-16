-- Add 'static' and 'custom_query' to the resolution_source constraint
-- and add static_value column for static variables

ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    DROP CONSTRAINT IF EXISTS ck_08_dim_template_variable_keys_source;

ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    ADD CONSTRAINT ck_08_dim_template_variable_keys_source
        CHECK (resolution_source IN (
            'audit_property', 'user_property', 'actor_property',
            'user_group', 'tenant', 'org', 'workspace',
            'settings', 'computed', 'custom_query', 'static'
        ));

ALTER TABLE "03_notifications"."08_dim_template_variable_keys"
    ADD COLUMN IF NOT EXISTS static_value TEXT NULL,
    ADD COLUMN IF NOT EXISTS is_user_defined BOOLEAN NOT NULL DEFAULT FALSE;

COMMENT ON COLUMN "03_notifications"."08_dim_template_variable_keys".static_value IS
    'For resolution_source=''static'': the literal value returned at render time.';
COMMENT ON COLUMN "03_notifications"."08_dim_template_variable_keys".is_user_defined IS
    'TRUE for variables created by admins; FALSE for system-seeded variables.';
