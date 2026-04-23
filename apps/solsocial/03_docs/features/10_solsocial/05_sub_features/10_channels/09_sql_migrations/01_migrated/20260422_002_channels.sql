-- UP ====

-- Channels sub-feature: connected social accounts.
-- OAuth tokens are NEVER stored here. vault_key points into tennetctl vault
-- under "solsocial.channels.{channel_id}.tokens".

CREATE TABLE "10_solsocial"."10_fct_channels" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,   -- tennetctl org UUID (foreign id)
    workspace_id    VARCHAR(36) NOT NULL,   -- tennetctl workspace UUID (foreign id)
    provider_id     SMALLINT    NOT NULL,
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,
    is_test         BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_solsocial_fct_channels PRIMARY KEY (id),
    CONSTRAINT fk_solsocial_fct_channels_provider
        FOREIGN KEY (provider_id) REFERENCES "10_solsocial"."01_dim_channel_providers" (id)
);
COMMENT ON TABLE  "10_solsocial"."10_fct_channels" IS 'Connected social accounts. Token material lives in tennetctl vault.';
COMMENT ON COLUMN "10_solsocial"."10_fct_channels".id IS 'UUID v7 generated app-side.';
COMMENT ON COLUMN "10_solsocial"."10_fct_channels".org_id IS 'Foreign ref to tennetctl org.';
COMMENT ON COLUMN "10_solsocial"."10_fct_channels".workspace_id IS 'Foreign ref to tennetctl workspace.';

CREATE INDEX idx_solsocial_fct_channels_workspace
    ON "10_solsocial"."10_fct_channels" (workspace_id)
    WHERE deleted_at IS NULL;

CREATE TABLE "10_solsocial"."20_dtl_channel_meta" (
    channel_id     VARCHAR(36) NOT NULL,
    handle         TEXT        NOT NULL,
    display_name   TEXT,
    avatar_url     TEXT,
    external_id    TEXT,
    vault_key      TEXT        NOT NULL,
    connected_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_synced_at TIMESTAMP,
    CONSTRAINT pk_solsocial_dtl_channel_meta PRIMARY KEY (channel_id),
    CONSTRAINT fk_solsocial_dtl_channel_meta_channel
        FOREIGN KEY (channel_id) REFERENCES "10_solsocial"."10_fct_channels" (id)
);
COMMENT ON TABLE  "10_solsocial"."20_dtl_channel_meta" IS 'Public per-channel metadata + pointer to vault token record.';
COMMENT ON COLUMN "10_solsocial"."20_dtl_channel_meta".vault_key IS 'Vault key in tennetctl storing {access_token, refresh_token, expires_in}.';

CREATE VIEW "10_solsocial".v_channels AS
SELECT
    c.id, c.org_id, c.workspace_id, c.provider_id, p.code AS provider_code,
    m.handle, m.display_name, m.avatar_url, m.external_id, m.vault_key,
    m.connected_at, m.last_synced_at,
    c.is_active, c.is_test,
    c.created_by, c.updated_by, c.created_at, c.updated_at
FROM "10_solsocial"."10_fct_channels" c
JOIN "10_solsocial"."01_dim_channel_providers" p ON p.id = c.provider_id
LEFT JOIN "10_solsocial"."20_dtl_channel_meta" m ON m.channel_id = c.id
WHERE c.deleted_at IS NULL;

-- DOWN ====

DROP VIEW  IF EXISTS "10_solsocial".v_channels;
DROP TABLE IF EXISTS "10_solsocial"."20_dtl_channel_meta";
DROP TABLE IF EXISTS "10_solsocial"."10_fct_channels";
