-- UP ====

-- Saved views: persist filter + bucket presets per org/user.
-- fct: identity-only (id, org_id, user_id, created_at)
-- dtl: detail fields (name, filter_json, bucket)
-- v_: joins fct + dtl for read path

CREATE TABLE "04_audit"."10_fct_audit_saved_views" (
    id           VARCHAR(36)  NOT NULL,
    org_id       VARCHAR(36)  NOT NULL,
    user_id      VARCHAR(36),
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_audit_saved_views PRIMARY KEY (id)
);

COMMENT ON TABLE  "04_audit"."10_fct_audit_saved_views"     IS 'Identity rows for saved audit-explorer filter presets. One row per saved view.';
COMMENT ON COLUMN "04_audit"."10_fct_audit_saved_views".id          IS 'UUID v7 — globally unique.';
COMMENT ON COLUMN "04_audit"."10_fct_audit_saved_views".org_id      IS 'Owning org. Views are org-scoped.';
COMMENT ON COLUMN "04_audit"."10_fct_audit_saved_views".user_id     IS 'Creating user. NULL = org-shared (future use).';
COMMENT ON COLUMN "04_audit"."10_fct_audit_saved_views".created_at  IS 'UTC creation timestamp.';

CREATE INDEX idx_audit_saved_views_org ON "04_audit"."10_fct_audit_saved_views" (org_id);


CREATE TABLE "04_audit"."20_dtl_audit_saved_view_details" (
    id             VARCHAR(36)  NOT NULL,
    saved_view_id  VARCHAR(36)  NOT NULL,
    name           VARCHAR(255) NOT NULL,
    filter_json    JSONB        NOT NULL DEFAULT '{}',
    bucket         VARCHAR(10)  NOT NULL DEFAULT 'hour',
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_audit_saved_view_details  PRIMARY KEY (id),
    CONSTRAINT fk_saved_view_details_fct    FOREIGN KEY (saved_view_id)
        REFERENCES "04_audit"."10_fct_audit_saved_views" (id) ON DELETE CASCADE,
    CONSTRAINT chk_saved_view_bucket        CHECK (bucket IN ('hour', 'day'))
);

COMMENT ON TABLE  "04_audit"."20_dtl_audit_saved_view_details"              IS 'Detail payload for saved audit views: name, filter preset, time bucket.';
COMMENT ON COLUMN "04_audit"."20_dtl_audit_saved_view_details".saved_view_id IS 'FK to fct_audit_saved_views. 1:1 relationship.';
COMMENT ON COLUMN "04_audit"."20_dtl_audit_saved_view_details".name          IS 'User-supplied display name for the saved view.';
COMMENT ON COLUMN "04_audit"."20_dtl_audit_saved_view_details".filter_json   IS 'Serialized AuditEventFilter dict. Stored as JSONB.';
COMMENT ON COLUMN "04_audit"."20_dtl_audit_saved_view_details".bucket        IS 'Stats bucket granularity: hour or day.';

CREATE INDEX idx_audit_saved_view_details_fk ON "04_audit"."20_dtl_audit_saved_view_details" (saved_view_id);


CREATE VIEW "04_audit"."v_audit_saved_views" AS
SELECT
    f.id,
    f.org_id,
    f.user_id,
    f.created_at,
    d.name,
    d.filter_json,
    d.bucket
FROM "04_audit"."10_fct_audit_saved_views" f
JOIN "04_audit"."20_dtl_audit_saved_view_details" d ON d.saved_view_id = f.id;

COMMENT ON VIEW "04_audit"."v_audit_saved_views" IS 'Read-path view joining fct_audit_saved_views + dtl_audit_saved_view_details.';


-- DOWN ====

DROP VIEW  IF EXISTS "04_audit"."v_audit_saved_views";
DROP TABLE IF EXISTS "04_audit"."20_dtl_audit_saved_view_details";
DROP TABLE IF EXISTS "04_audit"."10_fct_audit_saved_views";
