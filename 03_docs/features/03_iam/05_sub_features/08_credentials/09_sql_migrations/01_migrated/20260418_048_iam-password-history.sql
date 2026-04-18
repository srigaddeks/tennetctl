-- UP ====

CREATE TABLE IF NOT EXISTS "03_iam"."50_fct_password_history" (
    id          VARCHAR(36)  NOT NULL,
    user_id     VARCHAR(36)  NOT NULL,
    hash        TEXT         NOT NULL,   -- argon2id hash
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_password_history PRIMARY KEY (id),
    CONSTRAINT fk_iam_pw_history_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_iam_pw_history_user_time ON "03_iam"."50_fct_password_history" (user_id, created_at DESC);

COMMENT ON TABLE  "03_iam"."50_fct_password_history" IS 'Per-user password hash history for reuse prevention.';
COMMENT ON COLUMN "03_iam"."50_fct_password_history".hash IS 'argon2id hash of previous password.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."50_fct_password_history";
