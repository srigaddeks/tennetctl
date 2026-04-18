-- UP ====

-- Admin impersonation link table
-- Links an impersonation session to the admin who started it and the target user.
CREATE TABLE IF NOT EXISTS "03_iam"."45_lnk_impersonations" (
    id                   VARCHAR(36)  NOT NULL,
    session_id           VARCHAR(36)  NOT NULL,
    impersonator_user_id VARCHAR(36)  NOT NULL,
    impersonated_user_id VARCHAR(36)  NOT NULL,
    org_id               VARCHAR(36)  NOT NULL,
    ended_at             TIMESTAMP,
    created_by           VARCHAR(36)  NOT NULL,
    created_at           TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_iam_lnk_impersonations PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_impersonations_session
        FOREIGN KEY (session_id) REFERENCES "03_iam"."16_fct_sessions" (id) ON DELETE CASCADE,
    CONSTRAINT fk_iam_lnk_impersonations_impersonator
        FOREIGN KEY (impersonator_user_id) REFERENCES "03_iam"."12_fct_users" (id),
    CONSTRAINT fk_iam_lnk_impersonations_impersonated
        FOREIGN KEY (impersonated_user_id) REFERENCES "03_iam"."12_fct_users" (id),
    CONSTRAINT uq_iam_lnk_impersonations_session UNIQUE (session_id)
);

COMMENT ON TABLE "03_iam"."45_lnk_impersonations" IS 'Tracks admin impersonation sessions — links the minted session to the acting admin';
COMMENT ON COLUMN "03_iam"."45_lnk_impersonations".session_id IS 'The impersonation session row (expires_at enforces 30-min TTL)';
COMMENT ON COLUMN "03_iam"."45_lnk_impersonations".ended_at IS 'Set when admin ends impersonation early; NULL = still active (subject to session expiry)';

CREATE INDEX IF NOT EXISTS idx_iam_lnk_impersonations_admin
    ON "03_iam"."45_lnk_impersonations" (impersonator_user_id)
    WHERE ended_at IS NULL;

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."45_lnk_impersonations";
