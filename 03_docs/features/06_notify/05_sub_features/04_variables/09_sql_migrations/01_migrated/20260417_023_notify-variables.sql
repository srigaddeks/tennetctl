-- Migration: 20260417_023_notify-variables
-- Feature: 06_notify / sub-feature: 04_variables
-- Purpose: Template variable registry — static literals and safelisted dynamic SQL queries

-- UP ====

CREATE TABLE "06_notify"."13_fct_notify_template_variables" (
    id VARCHAR(36) NOT NULL,
    template_id VARCHAR(36) NOT NULL,
    name TEXT NOT NULL,
    var_type TEXT NOT NULL,
    static_value TEXT,
    sql_template TEXT,
    param_bindings JSONB,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_notify_template_variables PRIMARY KEY (id),
    CONSTRAINT fk_notify_template_variables_template
        FOREIGN KEY (template_id)
        REFERENCES "06_notify"."12_fct_notify_templates" (id) ON DELETE CASCADE,
    CONSTRAINT uq_notify_template_variables_name UNIQUE (template_id, name),
    CONSTRAINT chk_notify_template_variables_type
        CHECK (var_type IN ('static', 'dynamic_sql')),
    CONSTRAINT chk_notify_template_variables_static
        CHECK (var_type != 'static' OR static_value IS NOT NULL),
    CONSTRAINT chk_notify_template_variables_dynamic
        CHECK (var_type != 'dynamic_sql' OR sql_template IS NOT NULL)
);

COMMENT ON TABLE "06_notify"."13_fct_notify_template_variables" IS
    'Registered Jinja2 variables per template: static literals or safelisted SELECT queries parameterized by audit event context';
COMMENT ON COLUMN "06_notify"."13_fct_notify_template_variables".name IS
    'Jinja2 variable name — must be a valid Python identifier (lowercase, underscores only)';
COMMENT ON COLUMN "06_notify"."13_fct_notify_template_variables".var_type IS
    'static = literal value set at template creation time; dynamic_sql = SELECT against v_* views with context params';
COMMENT ON COLUMN "06_notify"."13_fct_notify_template_variables".static_value IS
    'Required when var_type=static. The literal value injected into Jinja2 rendering.';
COMMENT ON COLUMN "06_notify"."13_fct_notify_template_variables".sql_template IS
    'Required when var_type=dynamic_sql. Must start with SELECT. Safelisted at save time; executed in read-only tx with statement_timeout=2s.';
COMMENT ON COLUMN "06_notify"."13_fct_notify_template_variables".param_bindings IS
    'Maps SQL positional params ($1, $2...) to allowed context keys: actor_user_id, org_id, workspace_id, event_metadata';

CREATE VIEW "06_notify"."v_notify_template_variables" AS
SELECT
    id,
    template_id,
    name,
    var_type,
    static_value,
    sql_template,
    param_bindings,
    description,
    created_at,
    updated_at
FROM "06_notify"."13_fct_notify_template_variables";

COMMENT ON VIEW "06_notify"."v_notify_template_variables" IS
    'Read path for template variables — no deleted_at (variables deleted by cascading from template or explicit DELETE)';

-- DOWN ====

DROP VIEW IF EXISTS "06_notify"."v_notify_template_variables";
DROP TABLE IF EXISTS "06_notify"."13_fct_notify_template_variables";
