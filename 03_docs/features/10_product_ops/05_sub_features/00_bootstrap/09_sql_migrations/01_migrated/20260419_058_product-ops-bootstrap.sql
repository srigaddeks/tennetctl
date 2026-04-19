-- UP ====

-- Product Ops bootstrap: schema + dim tables + dim_attr_defs.
--
-- Reference: ADR-030 (audit-vs-product-events split). evt_product_events lives
-- in its own schema with its own privacy contract because the audit triple-defense
-- (DB CHECK + Pydantic + handler) cannot accept anonymous browser events without
-- a permanent third bypass that would defeat the compliance guarantee.
--
-- This migration creates the schema container and the two dim tables that
-- everything else in the module depends on:
--   - dim_event_kinds: statically seeded (6 rows). SMALLINT plain (not IDENTITY)
--     because IDs are stable and referenced as FKs from evt_product_events.
--     Phase 10 Plan 01 precedent: dim_audit_categories static = SMALLINT plain.
--   - dim_attribution_sources: dynamically populated from incoming UTM events.
--     SMALLINT IDENTITY because the seeder uses OVERRIDING SYSTEM VALUE=no
--     and we always INSERT … ON CONFLICT (code) DO UPDATE … RETURNING id.
--     Phase 10 Plan 01 precedent: dim_audit_event_keys dynamic = IDENTITY.
--   - dim_attr_defs: registers EAV attributes (visitor display_name to start;
--     more added as needs arise). Mirrors 04_audit / 03_iam dim_attr_defs shape.

CREATE SCHEMA IF NOT EXISTS "10_product_ops";
COMMENT ON SCHEMA "10_product_ops" IS 'Product Ops: Mixpanel/PostHog-class anonymous-first product analytics + acquisition. Separate from 04_audit per ADR-030 (different privacy contract, scope contract, partition strategy, retention).';

-- ========================================================================
-- dim_event_kinds — statically seeded, SMALLINT plain PK
-- ========================================================================

CREATE TABLE "10_product_ops"."01_dim_event_kinds" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_event_kinds PRIMARY KEY (id),
    CONSTRAINT uq_dim_event_kinds_code UNIQUE (code)
);

COMMENT ON TABLE  "10_product_ops"."01_dim_event_kinds" IS 'Event kind taxonomy for evt_product_events. Statically seeded; IDs stable across deploys.';
COMMENT ON COLUMN "10_product_ops"."01_dim_event_kinds".code IS 'Stable code: page_view, custom, click, identify, alias, referral_attached.';
COMMENT ON COLUMN "10_product_ops"."01_dim_event_kinds".deprecated_at IS 'Soft-removal of an event kind. Never DELETE rows.';

INSERT INTO "10_product_ops"."01_dim_event_kinds" (id, code, label, description) VALUES
    (1, 'page_view',         'Page View',         'Browser page navigation; auto-emitted by the SDK on init and on history.pushState/popstate.'),
    (2, 'custom',             'Custom Event',     'Caller-supplied event_name (e.g. cta_click, signup_started). event_name is required for this kind.'),
    (3, 'click',              'Link Click',       'Tracked link click — used by the link shortener (Phase 46) and explicit tnt.trackLink().'),
    (4, 'identify',           'Identify',         'Anonymous visitor → IAM user merge. Emitted when SDK calls identify(userId).'),
    (5, 'alias',              'Alias',            'Cross-device alias attached to an existing visitor — many-to-one alias graph.'),
    (6, 'referral_attached',  'Referral Attached','Referral code resolved on the visitor (Phase 47). Auto-creates a utm_source=referral touch.')
ON CONFLICT (id) DO NOTHING;

-- ========================================================================
-- dim_attribution_sources — dynamically interned UTM source values
-- ========================================================================

CREATE TABLE "10_product_ops"."02_dim_attribution_sources" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    code            TEXT NOT NULL,
    label           TEXT,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    first_seen      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dim_attribution_sources PRIMARY KEY (id),
    CONSTRAINT uq_dim_attribution_sources_code UNIQUE (code)
);

COMMENT ON TABLE  "10_product_ops"."02_dim_attribution_sources" IS 'Interned UTM source values seen in incoming events. SMALLINT IDENTITY — populated via INSERT ... ON CONFLICT (code) DO UPDATE ... RETURNING id from product.touches.record.';
COMMENT ON COLUMN "10_product_ops"."02_dim_attribution_sources".code IS 'utm_source value (lowercased, max 256 chars enforced at SDK + service layer).';
COMMENT ON COLUMN "10_product_ops"."02_dim_attribution_sources".first_seen IS 'When this utm_source was first observed in any workspace.';

-- ========================================================================
-- dim_attr_defs — EAV attribute registry for this schema
-- ========================================================================
-- Mirrors 03_iam.dim_attr_defs / 04_audit.dim_attr_defs shape. Every attribute
-- written into dtl_attrs (Phase 45-02 / Phase 47 / future) must be registered
-- here first. Seeded with a single visitor.display_name attr to prove the
-- EAV pivot in v_visitors (Task 2 of plan 45-01).

CREATE TABLE "10_product_ops"."03_dim_attr_defs" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    entity_type     TEXT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    value_type      TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_attr_defs PRIMARY KEY (id),
    CONSTRAINT uq_dim_attr_defs_entity_code UNIQUE (entity_type, code),
    CONSTRAINT chk_dim_attr_defs_value_type CHECK (value_type IN ('text','jsonb','smallint'))
);

COMMENT ON TABLE  "10_product_ops"."03_dim_attr_defs" IS 'EAV attribute registry for product_ops. Every dtl_attrs row references one of these; unregistered attrs are rejected at the service layer.';
COMMENT ON COLUMN "10_product_ops"."03_dim_attr_defs".entity_type IS 'visitor | event | touch — what entity this attr describes.';
COMMENT ON COLUMN "10_product_ops"."03_dim_attr_defs".value_type IS 'Which key_* column in dtl_attrs holds the value.';

INSERT INTO "10_product_ops"."03_dim_attr_defs" (entity_type, code, label, value_type, description) VALUES
    ('visitor', 'display_name', 'Visitor Display Name', 'text', 'Optional human-readable name (set by SDK identify() if known). Stored in dtl_attrs.key_text.')
ON CONFLICT (entity_type, code) DO NOTHING;

-- DOWN ====

DROP TABLE IF EXISTS "10_product_ops"."03_dim_attr_defs";
DROP TABLE IF EXISTS "10_product_ops"."02_dim_attribution_sources";
DROP TABLE IF EXISTS "10_product_ops"."01_dim_event_kinds";
DROP SCHEMA IF EXISTS "10_product_ops";
