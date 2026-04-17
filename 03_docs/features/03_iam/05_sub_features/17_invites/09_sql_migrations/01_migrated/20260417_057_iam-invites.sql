-- UP ====

-- Invite table: stores outgoing org invitations with HMAC-signed tokens
CREATE TABLE "03_iam"."30_fct_user_invites" (
    id          VARCHAR(36)  NOT NULL,
    org_id      VARCHAR(36)  NOT NULL,
    invited_by  VARCHAR(36)  NOT NULL,
    role_id     VARCHAR(36)  NULL,
    token_hash  TEXT         NOT NULL,
    status      SMALLINT     NOT NULL DEFAULT 1,  -- 1=pending 2=accepted 3=cancelled 4=expired
    expires_at  TIMESTAMP    NOT NULL,
    accepted_at TIMESTAMP    NULL,
    deleted_at  TIMESTAMP    NULL,
    created_by  VARCHAR(36)  NOT NULL,
    updated_by  VARCHAR(36)  NULL,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_user_invites PRIMARY KEY (id),
    CONSTRAINT fk_invites_org     FOREIGN KEY (org_id)     REFERENCES "03_iam"."10_fct_orgs"  (id),
    CONSTRAINT fk_invites_inviter FOREIGN KEY (invited_by) REFERENCES "03_iam"."12_fct_users" (id),
    CONSTRAINT fk_invites_role    FOREIGN KEY (role_id)    REFERENCES "03_iam"."13_fct_roles" (id),
    CONSTRAINT chk_invites_status CHECK (status IN (1, 2, 3, 4))
);

COMMENT ON TABLE  "03_iam"."30_fct_user_invites"             IS 'Org membership invitations with HMAC-signed one-time tokens';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".id          IS 'UUID v7 primary key';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".org_id      IS 'Org this invitation belongs to';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".invited_by  IS 'User (admin) who created the invitation';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".role_id     IS 'Optional role to assign on acceptance';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".token_hash  IS 'HMAC-SHA256 hex digest of the raw invite token';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".status      IS '1=pending 2=accepted 3=cancelled 4=expired';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".expires_at  IS 'Token expiry (UTC). 72 h from creation';
COMMENT ON COLUMN "03_iam"."30_fct_user_invites".accepted_at IS 'Timestamp when invitation was accepted';

-- EAV attr: invite email stored in dtl layer (entity_type_id = 3 = user context)
-- But for simplicity as specified we store the email inline in dtl_attrs
-- We store invite email as a separate dtl_attrs row keyed to the invite id.
-- For that we need an attr_def for invite emails:

-- Store invite target email inline in a separate dtl table dedicated to invites
-- (avoiding business columns on fct_* per convention — but per spec "for simplicity store inline")
-- Per spec exception: email stored inline as TEXT column on this table.
-- (This is the spec's explicit instruction; we follow it.)
ALTER TABLE "03_iam"."30_fct_user_invites"
    ADD COLUMN email TEXT NOT NULL DEFAULT '';

-- Remove the DEFAULT after adding the column
ALTER TABLE "03_iam"."30_fct_user_invites"
    ALTER COLUMN email DROP DEFAULT;

COMMENT ON COLUMN "03_iam"."30_fct_user_invites".email IS 'Invited email address (stored inline per spec; not used as PII once user created)';

-- Unique: one active invite per email per org
CREATE UNIQUE INDEX uq_invites_email_org_pending
    ON "03_iam"."30_fct_user_invites" (org_id, email)
    WHERE status = 1 AND deleted_at IS NULL;

-- Fast lookup by token hash
CREATE INDEX idx_invites_token_hash ON "03_iam"."30_fct_user_invites" (token_hash);

-- View: enriched invite rows with inviter info
CREATE VIEW "03_iam"."v_invites" AS
SELECT
    i.id,
    i.org_id,
    i.email,
    i.invited_by,
    u.email        AS inviter_email,
    u.display_name AS inviter_display_name,
    i.role_id,
    i.status,
    i.expires_at,
    i.accepted_at,
    i.deleted_at,
    i.created_by,
    i.updated_by,
    i.created_at,
    i.updated_at
FROM "03_iam"."30_fct_user_invites" i
LEFT JOIN "03_iam"."v_users" u ON u.id = i.invited_by;

COMMENT ON VIEW "03_iam"."v_invites" IS 'Invite rows enriched with inviter email + display_name';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam"."v_invites";
DROP TABLE IF EXISTS "03_iam"."30_fct_user_invites";
