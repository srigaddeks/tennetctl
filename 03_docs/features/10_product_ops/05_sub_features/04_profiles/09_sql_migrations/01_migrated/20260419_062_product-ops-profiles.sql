-- UP ====

-- product_ops.profiles — accumulated per-visitor traits.
--
-- Mixpanel "people" / PostHog "persons". Profiles are 1:1 with fct_visitors
-- (the visitor IS the profile holder); traits are stored in dtl_attrs (EAV
-- per the project rule). Existing dim_attr_defs from Phase 45 already supports
-- visitor.display_name; new traits register as `entity_type='visitor'` rows.
--
-- This migration adds:
--   1. dtl_visitor_attrs — the EAV table backing profile traits.
--   2. v_visitor_profiles — read view that joins fct_visitors + the EAV pivot.
--   3. A few seeded dim_attr_defs for canonical Mixpanel-style traits
--      (email, phone, name, plan, mrr_cents, country).

-- ========================================================================
-- dtl_visitor_attrs — EAV trait storage
-- ========================================================================

CREATE TABLE "10_product_ops"."20_dtl_visitor_attrs" (
    id              VARCHAR(36) NOT NULL,
    visitor_id      VARCHAR(36) NOT NULL,
    attr_def_id     SMALLINT NOT NULL,
    -- One of these is set per row, depending on attr_def's value_type
    key_text        TEXT,
    key_jsonb       JSONB,
    key_smallint    SMALLINT,
    -- Provenance
    source          TEXT NOT NULL DEFAULT 'identify',  -- identify | trait_set | inferred | imported
    set_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_dtl_visitor_attrs PRIMARY KEY (id),
    CONSTRAINT uq_dtl_visitor_attrs_visitor_attr UNIQUE (visitor_id, attr_def_id),
    CONSTRAINT fk_dtl_visitor_attrs_visitor
        FOREIGN KEY (visitor_id)
        REFERENCES "10_product_ops"."10_fct_visitors"(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_dtl_visitor_attrs_attr_def
        FOREIGN KEY (attr_def_id)
        REFERENCES "10_product_ops"."03_dim_attr_defs"(id),
    -- Exactly one value column non-NULL (matches IAM/audit dtl_attrs pattern)
    CONSTRAINT chk_dtl_visitor_attrs_one_value CHECK (
        (CASE WHEN key_text     IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN key_jsonb    IS NOT NULL THEN 1 ELSE 0 END +
         CASE WHEN key_smallint IS NOT NULL THEN 1 ELSE 0 END) = 1
    )
);

CREATE INDEX idx_dtl_visitor_attrs_visitor
    ON "10_product_ops"."20_dtl_visitor_attrs" (visitor_id);

COMMENT ON TABLE  "10_product_ops"."20_dtl_visitor_attrs" IS 'EAV trait storage. One row per (visitor_id, attr_def_id). UNIQUE — last write wins via INSERT … ON CONFLICT DO UPDATE.';
COMMENT ON COLUMN "10_product_ops"."20_dtl_visitor_attrs".source IS 'Provenance: identify (SDK identify call), trait_set (SDK setTrait), inferred (server-derived), imported (bulk import).';

-- ========================================================================
-- Seed core trait definitions
-- ========================================================================

INSERT INTO "10_product_ops"."03_dim_attr_defs" (entity_type, code, label, value_type, description) VALUES
    ('visitor', 'email',        'Email',           'text',  'Primary email. Hashed at SDK boundary by default.'),
    ('visitor', 'phone',        'Phone',           'text',  'E.164-format phone. Hashed at SDK boundary by default.'),
    ('visitor', 'name',         'Display Name',    'text',  'Human-readable name (overrides display_name from Phase 45 if both set).'),
    ('visitor', 'plan',         'Subscription Plan', 'text', 'Caller-defined plan code (free/starter/pro/enterprise).'),
    ('visitor', 'mrr_cents',    'MRR (cents)',     'jsonb', 'Monthly recurring revenue in cents. Stored as JSONB number for flexibility.'),
    ('visitor', 'country',      'Country (ISO-2)', 'text',  'ISO-3166 alpha-2 country code (US, GB, etc.). Server-side from IP unless explicitly set.'),
    ('visitor', 'company',      'Company',         'text',  'Caller-supplied org/company name. Useful for B2B segmentation.'),
    ('visitor', 'role',         'Role',            'text',  'Job title or role string.'),
    ('visitor', 'signup_at',    'Signup Timestamp','text',  'ISO-8601 timestamp of signup. Stored as text to preserve sub-millisecond precision.'),
    ('visitor', 'last_login_at','Last Login',      'text',  'ISO-8601 timestamp of most recent login.')
ON CONFLICT (entity_type, code) DO NOTHING;

-- ========================================================================
-- Read view: v_visitor_profiles
-- ========================================================================
-- Pivots dtl_visitor_attrs into one row per visitor. MAX(...) FILTER pattern
-- (Phase 3 Plan 04 + Phase 45 precedent) — single GROUP BY, no LATERAL.
-- Add columns here as new traits are seeded; the migration touching dim_attr_defs
-- is the right place to grow this view too.

CREATE OR REPLACE VIEW "10_product_ops".v_visitor_profiles AS
SELECT
    v.id,
    v.anonymous_id,
    v.user_id,
    v.org_id,
    v.workspace_id,
    v.first_seen,
    v.last_seen,
    -- Identity traits
    MAX(t.key_text) FILTER (WHERE ad.code = 'email')         AS email,
    MAX(t.key_text) FILTER (WHERE ad.code = 'phone')         AS phone,
    MAX(t.key_text) FILTER (WHERE ad.code = 'name')          AS name,
    -- Commercial traits
    MAX(t.key_text) FILTER (WHERE ad.code = 'plan')          AS plan,
    -- jsonb has no MAX(); UNIQUE (visitor_id, attr_def_id) guarantees ≤1 row per
    -- (visitor, attr) so we use array_agg[1] which is degenerate (= the value).
    (array_agg(t.key_jsonb) FILTER (WHERE ad.code = 'mrr_cents'))[1] AS mrr_cents,
    -- Demographic / firmographic
    MAX(t.key_text) FILTER (WHERE ad.code = 'country')       AS country,
    MAX(t.key_text) FILTER (WHERE ad.code = 'company')       AS company,
    MAX(t.key_text) FILTER (WHERE ad.code = 'role')          AS role,
    -- Lifecycle
    MAX(t.key_text) FILTER (WHERE ad.code = 'signup_at')     AS signup_at,
    MAX(t.key_text) FILTER (WHERE ad.code = 'last_login_at') AS last_login_at,
    -- Inherited from fct_visitors (first-touch attribution per ADR-030)
    v.first_utm_source_id,
    v.first_utm_campaign,
    v.first_referrer,
    v.is_active,
    (v.deleted_at IS NOT NULL) AS is_deleted,
    v.created_at,
    v.updated_at
FROM "10_product_ops"."10_fct_visitors" v
LEFT JOIN "10_product_ops"."20_dtl_visitor_attrs" t
       ON t.visitor_id = v.id
LEFT JOIN "10_product_ops"."03_dim_attr_defs" ad
       ON ad.id = t.attr_def_id
GROUP BY v.id;

COMMENT ON VIEW "10_product_ops".v_visitor_profiles IS 'Profile read view. EAV pivot via MAX(...) FILTER. Add new trait columns here when seeding new dim_attr_defs entries.';

-- DOWN ====

DROP VIEW IF EXISTS "10_product_ops".v_visitor_profiles;
DROP TABLE IF EXISTS "10_product_ops"."20_dtl_visitor_attrs";
DELETE FROM "10_product_ops"."03_dim_attr_defs"
 WHERE entity_type = 'visitor'
   AND code IN ('email','phone','name','plan','mrr_cents','country','company','role','signup_at','last_login_at');
