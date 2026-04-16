-- Add static_variables JSONB to templates table
-- Static variables act as template-level defaults for variable placeholders.
-- They are filled in when dynamic resolution (audit event, custom query) returns nothing.
-- Priority: per-recipient dynamic resolution > template static defaults

ALTER TABLE "03_notifications"."10_fct_templates"
    ADD COLUMN IF NOT EXISTS static_variables JSONB NOT NULL DEFAULT '{}';

COMMENT ON COLUMN "03_notifications"."10_fct_templates".static_variables
    IS 'Template-level default variable values. Filled when dynamic resolution returns nothing. Format: {"variable.key": "value"}';
