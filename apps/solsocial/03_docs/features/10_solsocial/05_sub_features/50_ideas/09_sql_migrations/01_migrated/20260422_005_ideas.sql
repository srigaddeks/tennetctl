-- UP ====

-- Ideas sub-feature — lightweight idea bucket promotable to posts.

CREATE TABLE "10_solsocial"."13_fct_ideas" (
    id           VARCHAR(36) NOT NULL,
    org_id       VARCHAR(36) NOT NULL,
    workspace_id VARCHAR(36) NOT NULL,
    is_active    BOOLEAN     NOT NULL DEFAULT TRUE,
    is_test      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_by   VARCHAR(36) NOT NULL,
    updated_by   VARCHAR(36) NOT NULL,
    created_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at   TIMESTAMP,
    CONSTRAINT pk_solsocial_fct_ideas PRIMARY KEY (id)
);
COMMENT ON TABLE "10_solsocial"."13_fct_ideas" IS 'Idea bucket — seeds that can later be promoted to posts.';
CREATE INDEX idx_solsocial_fct_ideas_workspace
    ON "10_solsocial"."13_fct_ideas" (workspace_id) WHERE deleted_at IS NULL;

CREATE TABLE "10_solsocial"."24_dtl_idea_content" (
    idea_id VARCHAR(36) NOT NULL,
    title   TEXT        NOT NULL,
    notes   TEXT,
    tags    JSONB       NOT NULL DEFAULT '[]'::jsonb,
    CONSTRAINT pk_solsocial_dtl_idea_content PRIMARY KEY (idea_id),
    CONSTRAINT fk_solsocial_dtl_idea_content_idea
        FOREIGN KEY (idea_id) REFERENCES "10_solsocial"."13_fct_ideas" (id)
);
COMMENT ON TABLE "10_solsocial"."24_dtl_idea_content" IS 'Idea title, notes, tags.';

CREATE VIEW "10_solsocial".v_ideas AS
SELECT
    i.id, i.org_id, i.workspace_id,
    i.is_active, i.is_test,
    i.created_by, i.updated_by, i.created_at, i.updated_at,
    c.title, c.notes, c.tags
FROM "10_solsocial"."13_fct_ideas" i
LEFT JOIN "10_solsocial"."24_dtl_idea_content" c ON c.idea_id = i.id
WHERE i.deleted_at IS NULL;

-- DOWN ====

DROP VIEW  IF EXISTS "10_solsocial".v_ideas;
DROP TABLE IF EXISTS "10_solsocial"."24_dtl_idea_content";
DROP TABLE IF EXISTS "10_solsocial"."13_fct_ideas";
