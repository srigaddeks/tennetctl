-- UP ====
-- Plan 20-03: Account lockout — failed auth attempts tracking + lockout storage.

CREATE TABLE IF NOT EXISTS "03_iam"."23_fct_failed_auth_attempts" (
    id              VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NULL,
    email           TEXT         NOT NULL,
    source_ip       INET         NULL,
    attempted_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_23_fct_failed_auth_attempts PRIMARY KEY (id)
);

COMMENT ON TABLE "03_iam"."23_fct_failed_auth_attempts" IS
    'Sliding-window log of failed authentication attempts. Used by account lockout enforcement.';
COMMENT ON COLUMN "03_iam"."23_fct_failed_auth_attempts".user_id IS
    'NULL when the email has no matching user (enumeration-safe).';
COMMENT ON COLUMN "03_iam"."23_fct_failed_auth_attempts".email IS
    'Email address that was attempted.';
COMMENT ON COLUMN "03_iam"."23_fct_failed_auth_attempts".source_ip IS
    'Source IP of the signin attempt for forensics (INET type).';
COMMENT ON COLUMN "03_iam"."23_fct_failed_auth_attempts".attempted_at IS
    'Wall-clock time of the attempt. Used for sliding window queries.';

CREATE INDEX IF NOT EXISTS idx_23_fct_failed_auth_email_time
    ON "03_iam"."23_fct_failed_auth_attempts" (email, attempted_at DESC);

-- DOWN ====
DROP INDEX IF EXISTS "03_iam".idx_23_fct_failed_auth_email_time;
DROP TABLE IF EXISTS "03_iam"."23_fct_failed_auth_attempts";
