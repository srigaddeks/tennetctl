-- UP ====

CREATE TABLE IF NOT EXISTS "03_iam"."48_fct_tos_versions" (
    id              VARCHAR(36)  NOT NULL,
    version         VARCHAR(50)  NOT NULL,
    title           TEXT         NOT NULL,
    body_markdown   TEXT         NOT NULL DEFAULT '',
    published_at    TIMESTAMP    NULL,
    effective_at    TIMESTAMP    NULL,
    created_by      VARCHAR(36)  NOT NULL,
    updated_by      VARCHAR(36)  NOT NULL,
    created_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_fct_tos_versions PRIMARY KEY (id),
    CONSTRAINT uq_iam_tos_version UNIQUE (version)
);

CREATE TABLE IF NOT EXISTS "03_iam"."49_lnk_user_tos_acceptance" (
    id              VARCHAR(36)  NOT NULL,
    user_id         VARCHAR(36)  NOT NULL,
    version_id      VARCHAR(36)  NOT NULL,
    accepted_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ip_hash         TEXT         NULL,
    CONSTRAINT pk_iam_lnk_user_tos PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_tos_user FOREIGN KEY (user_id)
        REFERENCES "03_iam"."12_fct_users"(id) ON DELETE CASCADE,
    CONSTRAINT fk_iam_lnk_tos_version FOREIGN KEY (version_id)
        REFERENCES "03_iam"."48_fct_tos_versions"(id) ON DELETE CASCADE,
    CONSTRAINT uq_iam_lnk_user_tos_version UNIQUE (user_id, version_id)
);

CREATE INDEX IF NOT EXISTS idx_iam_lnk_user_tos_user ON "03_iam"."49_lnk_user_tos_acceptance" (user_id);

COMMENT ON TABLE  "03_iam"."48_fct_tos_versions" IS 'Terms-of-Service versions.';
COMMENT ON TABLE  "03_iam"."49_lnk_user_tos_acceptance" IS 'Per-user TOS acceptance records.';
COMMENT ON COLUMN "03_iam"."49_lnk_user_tos_acceptance".ip_hash IS 'SHA-256 of IP for compliance audit; never stores plaintext IP.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."49_lnk_user_tos_acceptance";
DROP TABLE IF EXISTS "03_iam"."48_fct_tos_versions";
