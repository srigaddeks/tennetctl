-- ===========================================================================
-- Migration: Enhance sandbox schema
-- Date: 2026-03-16
-- Description: Post-audit hardening for 15_sandbox — adds missing FK indexes,
--              GIN indexes on JSONB columns, BRIN indexes on append-only
--              timestamp columns, immutability triggers on transaction tables,
--              CHECK constraints for resource limits and temporal fields,
--              seed dataset templates, composite covering indexes for
--              high-volume queries, and corrected ON DELETE behavior.
-- ===========================================================================


-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. MISSING FK INDEXES
--    PostgreSQL does not auto-create indexes on FK columns. These are required
--    for efficient JOINs, WHERE filters, and CASCADE delete operations.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_21_fct_datasets_source
    ON "15_sandbox"."21_fct_datasets" (dataset_source_code);

CREATE INDEX IF NOT EXISTS idx_22_fct_signals_status
    ON "15_sandbox"."22_fct_signals" (signal_status_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_23_fct_threat_types_severity
    ON "15_sandbox"."23_fct_threat_types" (severity_code)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_exec_status
    ON "15_sandbox"."25_trx_sandbox_runs" (execution_status_code);

CREATE INDEX IF NOT EXISTS idx_25_trx_sandbox_runs_dataset
    ON "15_sandbox"."25_trx_sandbox_runs" (dataset_id)
    WHERE dataset_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_28_fct_live_sessions_connector
    ON "15_sandbox"."28_fct_live_sessions" (connector_instance_id);

CREATE INDEX IF NOT EXISTS idx_49_dtl_expectations_signal
    ON "15_sandbox"."49_dtl_signal_test_expectations" (signal_id);

CREATE INDEX IF NOT EXISTS idx_49_dtl_expectations_dataset
    ON "15_sandbox"."49_dtl_signal_test_expectations" (dataset_id);


-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. GIN INDEXES ON JSONB COLUMNS
--    Enables efficient containment (@>), existence (?), and path queries on
--    expression trees, policy actions, signal results, and SSF subject data.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_23_fct_threat_types_expression_gin
    ON "15_sandbox"."23_fct_threat_types" USING GIN (expression_tree)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_24_fct_policies_actions_gin
    ON "15_sandbox"."24_fct_policies" USING GIN (actions)
    WHERE is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_26_trx_threat_evals_signal_results_gin
    ON "15_sandbox"."26_trx_threat_evaluations" USING GIN (signal_results);

CREATE INDEX IF NOT EXISTS idx_71_dtl_ssf_subjects_data_gin
    ON "15_sandbox"."71_dtl_ssf_stream_subjects" USING GIN (subject_id_data);


-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. BRIN INDEXES ON APPEND-ONLY TIMESTAMP COLUMNS
--    BRIN indexes are extremely compact and efficient for naturally ordered
--    (append-only) data. Ideal for time-range scans on large tables.
-- ═══════════════════════════════════════════════════════════════════════════════

CREATE INDEX IF NOT EXISTS idx_20_fct_connectors_created_brin
    ON "15_sandbox"."20_fct_connector_instances" USING BRIN (created_at);

CREATE INDEX IF NOT EXISTS idx_21_fct_datasets_collected_brin
    ON "15_sandbox"."21_fct_datasets" USING BRIN (collected_at);

CREATE INDEX IF NOT EXISTS idx_28_fct_sessions_created_brin
    ON "15_sandbox"."28_fct_live_sessions" USING BRIN (created_at);

CREATE INDEX IF NOT EXISTS idx_30_trx_promotions_created_brin
    ON "15_sandbox"."30_trx_promotions" USING BRIN (created_at);


-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. IMMUTABILITY TRIGGERS ON TRANSACTION TABLES
--    Transaction rows are append-only facts. Prevent accidental UPDATEs that
--    would corrupt the audit trail.
-- ═══════════════════════════════════════════════════════════════════════════════

-- 4a. Generic immutability function — blocks all UPDATEs
CREATE OR REPLACE FUNCTION "15_sandbox".fn_prevent_update()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'UPDATE not allowed on immutable transaction table %', TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

-- Apply to fully immutable trx_ tables
CREATE TRIGGER trg_25_immutable
    BEFORE UPDATE ON "15_sandbox"."25_trx_sandbox_runs"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();

CREATE TRIGGER trg_26_immutable
    BEFORE UPDATE ON "15_sandbox"."26_trx_threat_evaluations"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();

CREATE TRIGGER trg_27_immutable
    BEFORE UPDATE ON "15_sandbox"."27_trx_policy_executions"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();

CREATE TRIGGER trg_30_immutable
    BEFORE UPDATE ON "15_sandbox"."30_trx_promotions"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();

CREATE TRIGGER trg_31_immutable
    BEFORE UPDATE ON "15_sandbox"."31_trx_entity_lifecycle_events"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();

CREATE TRIGGER trg_73_immutable
    BEFORE UPDATE ON "15_sandbox"."73_trx_ssf_delivery_log"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_prevent_update();

-- 4b. SSF outbox — allow UPDATE only on acknowledged/acknowledged_at columns
CREATE OR REPLACE FUNCTION "15_sandbox".fn_outbox_ack_only()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.set_jwt != OLD.set_jwt OR NEW.jti != OLD.jti OR NEW.stream_id != OLD.stream_id THEN
        RAISE EXCEPTION 'Only acknowledged/acknowledged_at can be updated on SSF outbox';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_72_ack_only
    BEFORE UPDATE ON "15_sandbox"."72_trx_ssf_outbox"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_outbox_ack_only();


-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. CHECK CONSTRAINTS FOR RESOURCE LIMITS AND TEMPORAL FIELDS
--    Enforces domain invariants at the database level — prevents nonsensical
--    values like negative timeouts, negative counters, or zero versions.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Resource limits on signals
ALTER TABLE "15_sandbox"."22_fct_signals"
    ADD CONSTRAINT ck_22_fct_signals_timeout CHECK (timeout_ms > 0);

ALTER TABLE "15_sandbox"."22_fct_signals"
    ADD CONSTRAINT ck_22_fct_signals_memory CHECK (max_memory_mb > 0);

-- Execution time must be non-negative (NULL = not yet completed)
ALTER TABLE "15_sandbox"."25_trx_sandbox_runs"
    ADD CONSTRAINT ck_25_trx_runs_exec_time CHECK (execution_time_ms IS NULL OR execution_time_ms >= 0);

-- Live session counters must be non-negative
ALTER TABLE "15_sandbox"."28_fct_live_sessions"
    ADD CONSTRAINT ck_28_sessions_counters CHECK (
        data_points_received >= 0
        AND bytes_received >= 0
        AND signals_executed >= 0
        AND threats_evaluated >= 0
    );

-- Duration must be positive and capped at 60 minutes
ALTER TABLE "15_sandbox"."28_fct_live_sessions"
    ADD CONSTRAINT ck_28_sessions_duration CHECK (duration_minutes > 0 AND duration_minutes <= 60);

-- Version numbers must be positive across all versioned entities
ALTER TABLE "15_sandbox"."21_fct_datasets"
    ADD CONSTRAINT ck_21_version_positive CHECK (version_number > 0);

ALTER TABLE "15_sandbox"."22_fct_signals"
    ADD CONSTRAINT ck_22_version_positive CHECK (version_number > 0);

ALTER TABLE "15_sandbox"."23_fct_threat_types"
    ADD CONSTRAINT ck_23_version_positive CHECK (version_number > 0);

ALTER TABLE "15_sandbox"."24_fct_policies"
    ADD CONSTRAINT ck_24_version_positive CHECK (version_number > 0);

ALTER TABLE "15_sandbox"."29_fct_libraries"
    ADD CONSTRAINT ck_29_version_positive CHECK (version_number > 0);


-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. SEED DATASET TEMPLATES
--    Pre-built schemas and sample payloads for common connector types.
--    Critical for feature usability — users need working examples to start.
-- ═══════════════════════════════════════════════════════════════════════════════

INSERT INTO "15_sandbox"."07_dim_dataset_templates"
    (code, connector_type_code, name, description, json_schema, sample_payload)
VALUES
(
    'aws_iam_users', 'aws_iam', 'AWS IAM Users',
    'IAM user listing with MFA, access keys, last login',
    '{"users": [{"username": "string", "user_id": "string", "arn": "string", "mfa_enabled": "boolean", "access_keys": [{"key_id": "string", "status": "string", "created_at": "string"}], "last_login": "string", "password_last_used": "string", "groups": ["string"]}]}',
    '{"users": [{"username": "admin", "user_id": "AIDA123", "arn": "arn:aws:iam::123456:user/admin", "mfa_enabled": true, "access_keys": [{"key_id": "AKIA123", "status": "Active", "created_at": "2025-01-15T00:00:00Z"}], "last_login": "2026-03-15T10:30:00Z", "password_last_used": "2026-03-15T10:30:00Z", "groups": ["Admins"]}, {"username": "dev-user", "user_id": "AIDA456", "arn": "arn:aws:iam::123456:user/dev-user", "mfa_enabled": false, "access_keys": [{"key_id": "AKIA456", "status": "Active", "created_at": "2024-06-01T00:00:00Z"}], "last_login": "2026-03-10T08:00:00Z", "password_last_used": "2026-03-10T08:00:00Z", "groups": ["Developers"]}]}'
),
(
    'github_branch_protection', 'github', 'GitHub Branch Protection',
    'Repository branch protection rules for main/master',
    '{"repositories": [{"name": "string", "full_name": "string", "default_branch": "string", "branch_protection": {"enabled": "boolean", "required_reviews": "integer", "dismiss_stale_reviews": "boolean", "require_code_owner_reviews": "boolean", "required_status_checks": ["string"], "enforce_admins": "boolean"}}]}',
    '{"repositories": [{"name": "api-service", "full_name": "acme/api-service", "default_branch": "main", "branch_protection": {"enabled": true, "required_reviews": 2, "dismiss_stale_reviews": true, "require_code_owner_reviews": true, "required_status_checks": ["ci/build", "ci/test"], "enforce_admins": false}}, {"name": "frontend", "full_name": "acme/frontend", "default_branch": "main", "branch_protection": {"enabled": false, "required_reviews": 0, "dismiss_stale_reviews": false, "require_code_owner_reviews": false, "required_status_checks": [], "enforce_admins": false}}]}'
),
(
    'k8s_pod_security', 'kubernetes', 'Kubernetes Pod Security',
    'Pod security policies and privilege levels',
    '{"pods": [{"name": "string", "namespace": "string", "containers": [{"name": "string", "image": "string", "privileged": "boolean", "run_as_root": "boolean", "read_only_root_fs": "boolean", "capabilities": ["string"]}], "service_account": "string", "host_network": "boolean", "host_pid": "boolean"}]}',
    '{"pods": [{"name": "web-server", "namespace": "production", "containers": [{"name": "nginx", "image": "nginx:1.25", "privileged": false, "run_as_root": false, "read_only_root_fs": true, "capabilities": []}], "service_account": "web-sa", "host_network": false, "host_pid": false}, {"name": "debug-pod", "namespace": "default", "containers": [{"name": "debug", "image": "ubuntu:latest", "privileged": true, "run_as_root": true, "read_only_root_fs": false, "capabilities": ["NET_ADMIN", "SYS_PTRACE"]}], "service_account": "default", "host_network": true, "host_pid": true}]}'
),
(
    'postgresql_audit_log', 'postgresql', 'PostgreSQL Audit Log',
    'pg_audit log entries for access monitoring',
    '{"audit_entries": [{"timestamp": "string", "user": "string", "database": "string", "command_tag": "string", "object_type": "string", "object_name": "string", "statement": "string", "client_addr": "string"}]}',
    '{"audit_entries": [{"timestamp": "2026-03-15T14:30:00Z", "user": "app_user", "database": "production", "command_tag": "SELECT", "object_type": "TABLE", "object_name": "users", "statement": "SELECT * FROM users WHERE role = ''admin''", "client_addr": "10.0.1.50"}, {"timestamp": "2026-03-15T14:31:00Z", "user": "root", "database": "production", "command_tag": "DROP", "object_type": "TABLE", "object_name": "audit_logs", "statement": "DROP TABLE audit_logs", "client_addr": "192.168.1.1"}]}'
),
(
    'okta_users', 'okta', 'Okta Users',
    'Okta user directory with MFA and status',
    '{"users": [{"id": "string", "login": "string", "email": "string", "status": "string", "mfa_factors": [{"factor_type": "string", "provider": "string", "status": "string"}], "last_login": "string", "created": "string", "groups": ["string"]}]}',
    '{"users": [{"id": "00u1a2b3c4", "login": "alice@acme.com", "email": "alice@acme.com", "status": "ACTIVE", "mfa_factors": [{"factor_type": "push", "provider": "OKTA", "status": "ACTIVE"}], "last_login": "2026-03-15T09:00:00Z", "created": "2024-01-10T00:00:00Z", "groups": ["Everyone", "Engineering"]}, {"id": "00u5e6f7g8", "login": "bob@acme.com", "email": "bob@acme.com", "status": "ACTIVE", "mfa_factors": [], "last_login": "2026-02-01T00:00:00Z", "created": "2025-06-15T00:00:00Z", "groups": ["Everyone"]}]}'
),
(
    'azure_ad_users', 'azure_ad', 'Azure AD Users',
    'Azure Active Directory user directory',
    '{"users": [{"id": "string", "displayName": "string", "userPrincipalName": "string", "accountEnabled": "boolean", "mfaRegistered": "boolean", "lastSignInDateTime": "string", "createdDateTime": "string", "assignedLicenses": ["string"]}]}',
    '{"users": [{"id": "abc-123", "displayName": "Alice Smith", "userPrincipalName": "alice@acme.onmicrosoft.com", "accountEnabled": true, "mfaRegistered": true, "lastSignInDateTime": "2026-03-15T10:00:00Z", "createdDateTime": "2024-03-01T00:00:00Z", "assignedLicenses": ["E5"]}, {"id": "def-456", "displayName": "Bob Jones", "userPrincipalName": "bob@acme.onmicrosoft.com", "accountEnabled": true, "mfaRegistered": false, "lastSignInDateTime": "2026-01-15T00:00:00Z", "createdDateTime": "2025-09-01T00:00:00Z", "assignedLicenses": ["E3"]}]}'
),
(
    'jira_workflows', 'jira', 'Jira Workflow Compliance',
    'Jira project workflow and issue tracking compliance',
    '{"projects": [{"key": "string", "name": "string", "issues": [{"key": "string", "type": "string", "status": "string", "priority": "string", "assignee": "string", "reporter": "string", "created": "string", "updated": "string", "resolution_time_days": "integer"}]}]}',
    '{"projects": [{"key": "SEC", "name": "Security", "issues": [{"key": "SEC-101", "type": "Bug", "status": "Open", "priority": "Critical", "assignee": "alice@acme.com", "reporter": "bob@acme.com", "created": "2026-03-01T00:00:00Z", "updated": "2026-03-15T00:00:00Z", "resolution_time_days": null}, {"key": "SEC-100", "type": "Task", "status": "Done", "priority": "High", "assignee": "alice@acme.com", "reporter": "alice@acme.com", "created": "2026-02-15T00:00:00Z", "updated": "2026-03-05T00:00:00Z", "resolution_time_days": 18}]}]}'
)
ON CONFLICT (code) DO NOTHING;


-- ═══════════════════════════════════════════════════════════════════════════════
-- 7. COMPOSITE COVERING INDEXES FOR HIGH-VOLUME QUERIES
--    Tuned for the most common access patterns: listing runs, finding the
--    latest version of datasets/signals.
-- ═══════════════════════════════════════════════════════════════════════════════

-- Common query: list runs by org + signal + result
CREATE INDEX IF NOT EXISTS idx_25_trx_runs_org_signal_result
    ON "15_sandbox"."25_trx_sandbox_runs" (org_id, signal_id, result_code, created_at DESC);

-- Common query: find latest version of a dataset
CREATE INDEX IF NOT EXISTS idx_21_datasets_latest_version
    ON "15_sandbox"."21_fct_datasets" (org_id, dataset_code, version_number DESC)
    WHERE is_deleted = FALSE;

-- Common query: find latest version of a signal
CREATE INDEX IF NOT EXISTS idx_22_signals_latest_version
    ON "15_sandbox"."22_fct_signals" (org_id, signal_code, version_number DESC)
    WHERE is_deleted = FALSE;


-- ═══════════════════════════════════════════════════════════════════════════════
-- 8. FIX ON DELETE BEHAVIOR ON TRANSACTION TABLE FKs
--    49_dtl_signal_test_expectations.dataset_id FK was missing ON DELETE CASCADE.
--    PostgreSQL does not support ALTER CONSTRAINT, so we drop and re-add.
-- ═══════════════════════════════════════════════════════════════════════════════

ALTER TABLE "15_sandbox"."49_dtl_signal_test_expectations"
    DROP CONSTRAINT IF EXISTS fk_49_dtl_expectations_ds;

ALTER TABLE "15_sandbox"."49_dtl_signal_test_expectations"
    ADD CONSTRAINT fk_49_dtl_expectations_ds
    FOREIGN KEY (dataset_id) REFERENCES "15_sandbox"."21_fct_datasets" (id) ON DELETE CASCADE;
