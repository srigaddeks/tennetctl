-- =============================================================================
-- Migration:   20260409_013_iam_applications.sql
-- Module:      03_iam
-- Sub-feature: 06_applications
-- Sequence:    013
-- Depends on:  010 (foundation_primitives), 011 (rbac), 012 (feature_flags)
-- Description: Applications entity — a named grouping of products that external
--              apps present themselves as. Introduces:
--                1. Application categories in dim_categories
--                2. 10_fct_applications + EAV attr_defs
--                3. 40_lnk_application_products (M2M apps ↔ products)
--                4. 10_fct_application_tokens (opaque hashed API tokens)
--                5. v_applications + v_application_tokens views
-- =============================================================================

-- UP =========================================================================

-- ---------------------------------------------------------------------------
-- 1. Extend dim_categories CHECK to include 'application'
--    Cannot modify CHECK in place — must DROP then re-ADD.
-- ---------------------------------------------------------------------------
ALTER TABLE "03_iam"."06_dim_categories"
    DROP CONSTRAINT chk_iam_dim_categories_type;
ALTER TABLE "03_iam"."06_dim_categories"
    ADD CONSTRAINT chk_iam_dim_categories_type
    CHECK (category_type IN ('role', 'feature', 'flag', 'product', 'application'));

-- ---------------------------------------------------------------------------
-- 2. Seed application categories
-- ---------------------------------------------------------------------------
INSERT INTO "03_iam"."06_dim_categories" (category_type, code, label, description) VALUES
    ('application', 'saas_web',   'SaaS Web App',    'Browser-based SaaS application.'),
    ('application', 'mobile_app', 'Mobile App',      'iOS/Android native mobile app.'),
    ('application', 'cli',        'CLI Tool',        'Command-line tool consuming the platform.'),
    ('application', 'service',    'Backend Service', 'Headless backend service or daemon.');

-- ---------------------------------------------------------------------------
-- 3. Register entity types for EAV
-- ---------------------------------------------------------------------------
INSERT INTO "03_iam"."06_dim_entity_types" (code, label, description) VALUES
    ('platform_application',       'Platform Application', 'A platform application grouping of products.'),
    ('platform_application_token', 'Platform App Token',   'An API token issued for a platform application.')
ON CONFLICT (code) DO NOTHING;

-- ---------------------------------------------------------------------------
-- 4. Register attr_defs for platform_application
-- ---------------------------------------------------------------------------
INSERT INTO "03_iam"."07_dim_attr_defs"
    (entity_type_id, code, label, description, value_column)
SELECT et.id, x.code, x.label, x.description, x.value_column
FROM (VALUES
    ('platform_application', 'description',   'Description',   'Long-form application description.',                 'key_text'),
    ('platform_application', 'slug',          'Slug',          'URL-safe unique identifier for the application.',    'key_text'),
    ('platform_application', 'icon_url',      'Icon URL',      'URL of the application icon.',                       'key_text'),
    ('platform_application', 'redirect_uris', 'Redirect URIs', 'JSON array of allowed OAuth2 redirect URIs.',        'key_jsonb'),
    ('platform_application', 'owner_user_id', 'Owner User ID', 'UUID of the user who owns this application.',        'key_text')
) AS x(entity_code, code, label, description, value_column)
JOIN "03_iam"."06_dim_entity_types" et ON et.code = x.entity_code;

-- ---------------------------------------------------------------------------
-- 5. 10_fct_applications — platform application catalog
--    Pure-EAV: code and name are identity columns (exception for lookups).
--    All extended attrs (description, slug, icon_url, redirect_uris,
--    owner_user_id) live in 20_dtl_attrs.
--    category_id FK enforced at app level (must be category_type='application').
-- ---------------------------------------------------------------------------
CREATE TABLE "03_iam"."10_fct_applications" (
    id           VARCHAR(36)  NOT NULL,
    code         VARCHAR(96)  NOT NULL,
    name         VARCHAR(255) NOT NULL,
    category_id  SMALLINT     NOT NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    is_test      BOOLEAN      NOT NULL DEFAULT FALSE,
    deleted_at   TIMESTAMP,
    created_by   VARCHAR(36)  NOT NULL,
    updated_by   VARCHAR(36)  NOT NULL,
    created_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_iam_fct_applications              PRIMARY KEY (id),
    CONSTRAINT uq_iam_fct_applications_code         UNIQUE (code),
    CONSTRAINT fk_iam_fct_applications_category     FOREIGN KEY (category_id)
        REFERENCES "03_iam"."06_dim_categories" (id),
    CONSTRAINT fk_iam_fct_applications_created_by   FOREIGN KEY (created_by)
        REFERENCES "03_iam"."10_fct_users" (id) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_iam_fct_applications_updated_by   FOREIGN KEY (updated_by)
        REFERENCES "03_iam"."10_fct_users" (id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_iam_fct_applications_category_id ON "03_iam"."10_fct_applications" (category_id);
CREATE INDEX idx_iam_fct_applications_is_active   ON "03_iam"."10_fct_applications" (is_active)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_iam_fct_applications_created_at  ON "03_iam"."10_fct_applications" (created_at DESC);

COMMENT ON TABLE  "03_iam"."10_fct_applications" IS
    'Platform application catalog. code and name are identity columns here '
    '(exception to pure-EAV for catalog lookups). All extended attributes '
    '(description, slug, icon_url, redirect_uris, owner_user_id) live in '
    '20_dtl_attrs. Applications group one or more products and represent how '
    'external clients present themselves to the platform.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".id          IS 'UUID v7 primary key.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".code        IS 'Unique machine-readable application code.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".name        IS 'Human-readable application name.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".category_id IS 'FK to 06_dim_categories (category_type=application).';
COMMENT ON COLUMN "03_iam"."10_fct_applications".is_active   IS 'FALSE to disable without deleting.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".is_test     IS 'TRUE for test/fixture rows.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".deleted_at  IS 'Soft-delete timestamp. NULL means active.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".created_by  IS 'Actor that created the application.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".updated_by  IS 'Actor that last updated the application.';
COMMENT ON COLUMN "03_iam"."10_fct_applications".created_at  IS 'Row creation timestamp (UTC).';
COMMENT ON COLUMN "03_iam"."10_fct_applications".updated_at  IS 'Last update timestamp (UTC).';

GRANT SELECT ON "03_iam"."10_fct_applications" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE ON "03_iam"."10_fct_applications" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 6. 40_lnk_application_products — application ↔ product M2M
--    Soft-deactivated via is_active; no DELETE grant.
-- ---------------------------------------------------------------------------
CREATE TABLE "03_iam"."40_lnk_application_products" (
    id             VARCHAR(36)  NOT NULL,
    application_id VARCHAR(36)  NOT NULL,
    product_id     VARCHAR(36)  NOT NULL,
    linked_at      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    linked_by      VARCHAR(36)  NOT NULL,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,

    CONSTRAINT pk_iam_lnk_application_products                    PRIMARY KEY (id),
    CONSTRAINT uq_iam_lnk_application_products_app_prod           UNIQUE (application_id, product_id),
    CONSTRAINT fk_iam_lnk_application_products_application        FOREIGN KEY (application_id)
        REFERENCES "03_iam"."10_fct_applications" (id),
    CONSTRAINT fk_iam_lnk_application_products_product            FOREIGN KEY (product_id)
        REFERENCES "03_iam"."10_fct_products" (id),
    CONSTRAINT fk_iam_lnk_application_products_linked_by          FOREIGN KEY (linked_by)
        REFERENCES "03_iam"."10_fct_users" (id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_iam_lnk_application_products_app  ON "03_iam"."40_lnk_application_products" (application_id);
CREATE INDEX idx_iam_lnk_application_products_prod ON "03_iam"."40_lnk_application_products" (product_id);

COMMENT ON TABLE  "03_iam"."40_lnk_application_products" IS
    'M2M link between platform applications and platform products. Tracks which '
    'products an application is associated with. Rows are never hard-deleted; '
    'set is_active = FALSE to remove the association.';
COMMENT ON COLUMN "03_iam"."40_lnk_application_products".id             IS 'UUID v7 primary key.';
COMMENT ON COLUMN "03_iam"."40_lnk_application_products".application_id IS 'FK to 10_fct_applications.';
COMMENT ON COLUMN "03_iam"."40_lnk_application_products".product_id     IS 'FK to 10_fct_products.';
COMMENT ON COLUMN "03_iam"."40_lnk_application_products".linked_at      IS 'When the product was linked to the application.';
COMMENT ON COLUMN "03_iam"."40_lnk_application_products".linked_by      IS 'Actor that created the link.';
COMMENT ON COLUMN "03_iam"."40_lnk_application_products".is_active      IS 'FALSE when the product link has been deactivated.';

GRANT SELECT ON "03_iam"."40_lnk_application_products" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE ON "03_iam"."40_lnk_application_products" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 7. 10_fct_application_tokens — opaque hashed API tokens
--    Intentionally immutable: no updated_by, no updated_at.
--    The wire token is NEVER stored. Only a BLAKE2b-256 hex digest is kept.
--    token_prefix is the first 16 chars of the random portion (after the
--    'tnctl_app_' wire prefix) for indexed prefix-based lookup.
-- ---------------------------------------------------------------------------
CREATE TABLE "03_iam"."10_fct_application_tokens" (
    id             VARCHAR(36)  NOT NULL,
    application_id VARCHAR(36)  NOT NULL,
    name           VARCHAR(128) NOT NULL,
    token_prefix   VARCHAR(16)  NOT NULL,
    token_hash     TEXT         NOT NULL,
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    expires_at     TIMESTAMP,
    last_used_at   TIMESTAMP,
    deleted_at     TIMESTAMP,
    created_by     VARCHAR(36)  NOT NULL,
    created_at     TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_iam_fct_application_tokens              PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_application_tokens_application  FOREIGN KEY (application_id)
        REFERENCES "03_iam"."10_fct_applications" (id),
    CONSTRAINT fk_iam_fct_application_tokens_created_by   FOREIGN KEY (created_by)
        REFERENCES "03_iam"."10_fct_users" (id) DEFERRABLE INITIALLY DEFERRED
);

CREATE INDEX idx_iam_fct_application_tokens_prefix ON "03_iam"."10_fct_application_tokens" (application_id, token_prefix)
    WHERE is_active = TRUE AND deleted_at IS NULL;
CREATE INDEX idx_iam_fct_application_tokens_app    ON "03_iam"."10_fct_application_tokens" (application_id);

COMMENT ON TABLE  "03_iam"."10_fct_application_tokens" IS
    'Opaque API tokens issued for platform applications. Intentionally immutable: '
    'there is no updated_by or updated_at column. The full wire token is NEVER '
    'stored — only a BLAKE2b-256 hex digest (token_hash) is persisted. '
    'token_prefix holds the first 16 chars of the random portion (after the '
    '''tnctl_app_'' wire prefix) to enable indexed lookup before hash verification.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".id             IS 'UUID v7 primary key.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".application_id IS 'FK to 10_fct_applications. The owning application.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".name           IS 'Human-readable label for the token (e.g. "CI Deploy Key").';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".token_prefix   IS 'First 16 chars of the random portion of the wire token. Used for indexed lookup before full hash comparison.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".token_hash     IS 'BLAKE2b-256 hex digest of the full wire token. The wire token itself is never stored.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".is_active      IS 'FALSE to revoke without deleting.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".expires_at     IS 'Expiry timestamp. NULL means the token never expires.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".last_used_at   IS 'Timestamp of the most recent successful token verification.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".deleted_at     IS 'Soft-delete timestamp. NULL means not deleted.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".created_by     IS 'Actor that created (issued) the token.';
COMMENT ON COLUMN "03_iam"."10_fct_application_tokens".created_at     IS 'Row creation timestamp (UTC).';

GRANT SELECT ON "03_iam"."10_fct_application_tokens" TO tennetctl_read;
GRANT SELECT, INSERT, UPDATE, DELETE ON "03_iam"."10_fct_application_tokens" TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 8. v_applications — pivoted EAV view for application reads
-- ---------------------------------------------------------------------------
CREATE VIEW "03_iam".v_applications AS
SELECT
    a.id,
    a.code,
    a.name,
    a.category_id,
    c.code                                                                AS category_code,
    c.label                                                               AS category_label,
    a.is_active,
    a.is_test,
    (a.deleted_at IS NOT NULL)                                            AS is_deleted,
    MAX(CASE WHEN ad.code = 'description'   THEN at2.key_text  END)      AS description,
    MAX(CASE WHEN ad.code = 'slug'          THEN at2.key_text  END)      AS slug,
    MAX(CASE WHEN ad.code = 'icon_url'      THEN at2.key_text  END)      AS icon_url,
    MAX(CASE WHEN ad.code = 'redirect_uris' THEN at2.key_jsonb END)      AS redirect_uris,
    MAX(CASE WHEN ad.code = 'owner_user_id' THEN at2.key_text  END)      AS owner_user_id,
    (SELECT COUNT(*)::INT
       FROM "03_iam"."40_lnk_application_products" lp
      WHERE lp.application_id = a.id
        AND lp.is_active = TRUE)                                          AS linked_product_count,
    (SELECT COUNT(*)::INT
       FROM "03_iam"."10_fct_application_tokens" tk
      WHERE tk.application_id = a.id
        AND tk.is_active = TRUE
        AND tk.deleted_at IS NULL)                                        AS active_token_count,
    a.created_by,
    a.updated_by,
    a.created_at,
    a.updated_at
FROM "03_iam"."10_fct_applications" a
LEFT JOIN "03_iam"."06_dim_categories" c ON c.id = a.category_id
LEFT JOIN "03_iam"."20_dtl_attrs" at2
       ON at2.entity_type_id = (SELECT id FROM "03_iam"."06_dim_entity_types" WHERE code = 'platform_application')
      AND at2.entity_id = a.id
LEFT JOIN "03_iam"."07_dim_attr_defs" ad ON ad.id = at2.attr_def_id
GROUP BY a.id, a.code, a.name, a.category_id, c.code, c.label,
         a.is_active, a.is_test, a.deleted_at,
         a.created_by, a.updated_by, a.created_at, a.updated_at;

COMMENT ON VIEW "03_iam".v_applications IS
    'Applications with EAV attrs pivoted, category code/label resolved, and '
    'derived counts for linked products and active tokens.';

GRANT SELECT ON "03_iam".v_applications TO tennetctl_read;
GRANT SELECT ON "03_iam".v_applications TO tennetctl_write;

-- ---------------------------------------------------------------------------
-- 9. v_application_tokens — safe read view for tokens
--    IMPORTANT: token_hash is intentionally excluded. This view NEVER exposes
--    the hash digest. Callers verify tokens via the service layer only.
-- ---------------------------------------------------------------------------
CREATE VIEW "03_iam".v_application_tokens AS
SELECT
    t.id,
    t.application_id,
    a.code          AS application_code,
    a.name          AS application_name,
    t.name,
    t.token_prefix,
    t.is_active,
    t.expires_at,
    t.last_used_at,
    (t.deleted_at IS NOT NULL)  AS is_deleted,
    t.created_by,
    t.created_at
FROM "03_iam"."10_fct_application_tokens" t
JOIN "03_iam"."10_fct_applications" a ON a.id = t.application_id;

COMMENT ON VIEW "03_iam".v_application_tokens IS
    'Safe read view for application tokens. token_hash is intentionally omitted '
    '— it is never exposed through this view. Token verification must go through '
    'the service layer which reads the raw fct table directly.';

GRANT SELECT ON "03_iam".v_application_tokens TO tennetctl_read;
GRANT SELECT ON "03_iam".v_application_tokens TO tennetctl_write;

-- DOWN =======================================================================

DROP VIEW  IF EXISTS "03_iam".v_application_tokens;
DROP VIEW  IF EXISTS "03_iam".v_applications;
DROP TABLE IF EXISTS "03_iam"."10_fct_application_tokens";
DROP TABLE IF EXISTS "03_iam"."40_lnk_application_products";
DROP TABLE IF EXISTS "03_iam"."10_fct_applications";

-- Remove EAV registrations for platform_application and platform_application_token
DELETE FROM "03_iam"."07_dim_attr_defs"
 WHERE entity_type_id IN (
     SELECT id FROM "03_iam"."06_dim_entity_types"
      WHERE code IN ('platform_application', 'platform_application_token')
 );

DELETE FROM "03_iam"."06_dim_entity_types"
 WHERE code IN ('platform_application', 'platform_application_token');

-- Remove application categories
DELETE FROM "03_iam"."06_dim_categories"
 WHERE category_type = 'application';

-- Restore original CHECK (without 'application')
ALTER TABLE "03_iam"."06_dim_categories"
    DROP CONSTRAINT chk_iam_dim_categories_type;
ALTER TABLE "03_iam"."06_dim_categories"
    ADD CONSTRAINT chk_iam_dim_categories_type
    CHECK (category_type IN ('role', 'feature', 'flag', 'product'));
