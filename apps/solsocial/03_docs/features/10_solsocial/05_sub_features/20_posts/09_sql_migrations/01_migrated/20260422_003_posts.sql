-- UP ====

-- Posts sub-feature. Body + media in dtl; provider publish audit in evt.

CREATE TABLE "10_solsocial"."11_fct_posts" (
    id            VARCHAR(36) NOT NULL,
    org_id        VARCHAR(36) NOT NULL,
    workspace_id  VARCHAR(36) NOT NULL,
    channel_id    VARCHAR(36) NOT NULL,
    status_id     SMALLINT    NOT NULL,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    is_test       BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by    VARCHAR(36) NOT NULL,
    updated_by    VARCHAR(36) NOT NULL,
    scheduled_at  TIMESTAMP,
    published_at  TIMESTAMP,
    created_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at    TIMESTAMP,
    CONSTRAINT pk_solsocial_fct_posts PRIMARY KEY (id),
    CONSTRAINT fk_solsocial_fct_posts_channel
        FOREIGN KEY (channel_id) REFERENCES "10_solsocial"."10_fct_channels" (id),
    CONSTRAINT fk_solsocial_fct_posts_status
        FOREIGN KEY (status_id) REFERENCES "10_solsocial"."02_dim_post_statuses" (id)
);
COMMENT ON TABLE "10_solsocial"."11_fct_posts" IS 'Post identity + lifecycle pointers. Body lives in dtl_post_content.';

CREATE INDEX idx_solsocial_fct_posts_ws_status
    ON "10_solsocial"."11_fct_posts" (workspace_id, status_id)
    WHERE deleted_at IS NULL;

CREATE INDEX idx_solsocial_fct_posts_scheduled
    ON "10_solsocial"."11_fct_posts" (scheduled_at)
    WHERE deleted_at IS NULL AND scheduled_at IS NOT NULL;

CREATE TABLE "10_solsocial"."21_dtl_post_content" (
    post_id VARCHAR(36) NOT NULL,
    body    TEXT        NOT NULL,
    media   JSONB       NOT NULL DEFAULT '[]'::jsonb,
    link    TEXT,
    CONSTRAINT pk_solsocial_dtl_post_content PRIMARY KEY (post_id),
    CONSTRAINT fk_solsocial_dtl_post_content_post
        FOREIGN KEY (post_id) REFERENCES "10_solsocial"."11_fct_posts" (id)
);
COMMENT ON TABLE "10_solsocial"."21_dtl_post_content" IS 'Post body, media refs, link. One row per post.';

CREATE TABLE "10_solsocial"."22_dtl_post_external" (
    post_id          VARCHAR(36) NOT NULL,
    external_post_id TEXT        NOT NULL,
    external_url     TEXT,
    published_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_solsocial_dtl_post_external PRIMARY KEY (post_id),
    CONSTRAINT fk_solsocial_dtl_post_external_post
        FOREIGN KEY (post_id) REFERENCES "10_solsocial"."11_fct_posts" (id)
);
COMMENT ON TABLE "10_solsocial"."22_dtl_post_external" IS 'Provider-side IDs after a successful publish.';

-- evt_* : append-only. id, org_id, actor_id, metadata JSONB, created_at. No updated_at, no deleted_at.
CREATE TABLE "10_solsocial"."60_evt_post_publishes" (
    id         VARCHAR(36) NOT NULL,
    org_id     VARCHAR(36) NOT NULL,
    actor_id   VARCHAR(36) NOT NULL,
    post_id    VARCHAR(36) NOT NULL,
    outcome    TEXT        NOT NULL,
    metadata   JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_solsocial_evt_post_publishes PRIMARY KEY (id),
    CONSTRAINT fk_solsocial_evt_post_publishes_post
        FOREIGN KEY (post_id) REFERENCES "10_solsocial"."11_fct_posts" (id),
    CONSTRAINT chk_solsocial_evt_post_publishes_outcome CHECK (outcome IN ('success', 'failure'))
);
COMMENT ON TABLE "10_solsocial"."60_evt_post_publishes" IS 'Append-only publish attempts. metadata carries {external_post_id, external_url, error_code, error_msg}.';
CREATE INDEX idx_solsocial_evt_post_publishes_post
    ON "10_solsocial"."60_evt_post_publishes" (post_id, created_at DESC);

CREATE VIEW "10_solsocial".v_posts AS
SELECT
    p.id, p.org_id, p.workspace_id, p.channel_id,
    p.status_id, s.code AS status,
    p.is_active, p.is_test,
    c.body, c.media, c.link,
    p.scheduled_at, p.published_at,
    p.created_by, p.updated_by, p.created_at, p.updated_at,
    e.external_post_id, e.external_url
FROM "10_solsocial"."11_fct_posts" p
JOIN "10_solsocial"."02_dim_post_statuses" s ON s.id = p.status_id
LEFT JOIN "10_solsocial"."21_dtl_post_content" c  ON c.post_id = p.id
LEFT JOIN "10_solsocial"."22_dtl_post_external" e ON e.post_id = p.id
WHERE p.deleted_at IS NULL;

-- DOWN ====

DROP VIEW  IF EXISTS "10_solsocial".v_posts;
DROP TABLE IF EXISTS "10_solsocial"."60_evt_post_publishes";
DROP TABLE IF EXISTS "10_solsocial"."22_dtl_post_external";
DROP TABLE IF EXISTS "10_solsocial"."21_dtl_post_content";
DROP TABLE IF EXISTS "10_solsocial"."11_fct_posts";
