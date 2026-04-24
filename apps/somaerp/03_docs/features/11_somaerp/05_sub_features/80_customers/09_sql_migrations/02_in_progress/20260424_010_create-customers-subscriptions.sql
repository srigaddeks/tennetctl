-- UP ====================================================================

-- Customers + Subscription Plans + Subscriptions for somaerp (Plan 56-11).
-- Creates:
--   dim_subscription_frequencies  (universal seeded lookup)
--   fct_customers                 (tenant-scoped customer identity)
--   fct_subscription_plans        (tenant-scoped plan templates)
--   dtl_subscription_plan_items   (soft-delete product mix per plan)
--   fct_subscriptions             (customer's active/historic subscription)
--   evt_subscription_events       (append-only state-transition event log)
-- Plus views:
--   v_customers               (JOIN fct_locations + active subscription count)
--   v_subscription_plans      (JOIN frequency + item_count)
--   v_subscription_plan_items (JOIN product + variant + computed line_price)
--   v_subscriptions           (JOIN customer + plan + frequency + zone)
--
-- Rules per 56-11-PLAN + table-type conventions:
-- * fct_customers.status CHECK transitions enforced in service, not DB.
-- * dtl_subscription_plan_items is soft-delete (dtl_* convention).
-- * evt_subscription_events has NO updated_at/deleted_at (evt_* append-only).

-- ── dim_subscription_frequencies ──────────────────────────────────────────

CREATE TABLE "11_somaerp".dim_subscription_frequencies (
    id                    SMALLINT NOT NULL,
    code                  TEXT NOT NULL,
    name                  TEXT NOT NULL,
    deliveries_per_week   NUMERIC(4,2) NOT NULL,
    deprecated_at         TIMESTAMP,
    CONSTRAINT pk_somaerp_dim_subscription_frequencies PRIMARY KEY (id),
    CONSTRAINT uq_somaerp_dim_subscription_frequencies_code UNIQUE (code)
);
COMMENT ON TABLE  "11_somaerp".dim_subscription_frequencies IS 'Universal lookup of delivery cadences: daily (7/wk), 3x_week, 5x_week, weekly (1/wk), biweekly (0.5/wk), monthly (0.25/wk), custom (0).';
COMMENT ON COLUMN "11_somaerp".dim_subscription_frequencies.id IS 'SMALLINT PK, hand-assigned.';
COMMENT ON COLUMN "11_somaerp".dim_subscription_frequencies.code IS 'Stable machine code (e.g. daily, weekly).';
COMMENT ON COLUMN "11_somaerp".dim_subscription_frequencies.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".dim_subscription_frequencies.deliveries_per_week IS 'Nominal cadence in deliveries/week — used to approximate revenue + logistics load.';
COMMENT ON COLUMN "11_somaerp".dim_subscription_frequencies.deprecated_at IS 'Soft-deprecation sentinel.';

-- ── fct_customers ─────────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_customers (
    id                   VARCHAR(36) NOT NULL,
    tenant_id            VARCHAR(36) NOT NULL,
    location_id          VARCHAR(36),
    name                 TEXT NOT NULL,
    slug                 TEXT NOT NULL,
    email                TEXT,
    phone                TEXT,
    address_jsonb        JSONB NOT NULL DEFAULT '{}'::jsonb,
    delivery_notes       TEXT,
    acquisition_source   TEXT,
    status               TEXT NOT NULL DEFAULT 'active',
    lifetime_value       NUMERIC(14,2) NOT NULL DEFAULT 0,
    properties           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           VARCHAR(36) NOT NULL,
    updated_by           VARCHAR(36) NOT NULL,
    deleted_at           TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_customers PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_customers_location FOREIGN KEY (location_id)
        REFERENCES "11_somaerp".fct_locations(id),
    CONSTRAINT chk_somaerp_fct_customers_status
        CHECK (status IN ('prospect','active','paused','churned','blocked'))
);
COMMENT ON TABLE  "11_somaerp".fct_customers IS 'Tenant-scoped customer identity. Location is optional at creation, fixed later as address becomes known.';
COMMENT ON COLUMN "11_somaerp".fct_customers.id IS 'UUID v7, app-generated.';
COMMENT ON COLUMN "11_somaerp".fct_customers.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_customers.location_id IS 'FK to fct_locations.id — city/region anchor (nullable).';
COMMENT ON COLUMN "11_somaerp".fct_customers.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".fct_customers.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_customers.email IS 'Contact email (nullable).';
COMMENT ON COLUMN "11_somaerp".fct_customers.phone IS 'Contact phone (nullable).';
COMMENT ON COLUMN "11_somaerp".fct_customers.address_jsonb IS 'Structured address (line1/pincode/landmark/...).';
COMMENT ON COLUMN "11_somaerp".fct_customers.delivery_notes IS 'Free text — gate code, time-window preferences, dog warning.';
COMMENT ON COLUMN "11_somaerp".fct_customers.acquisition_source IS 'Referral channel (e.g. ig_ad, whatsapp, word_of_mouth).';
COMMENT ON COLUMN "11_somaerp".fct_customers.status IS 'prospect | active | paused | churned | blocked.';
COMMENT ON COLUMN "11_somaerp".fct_customers.lifetime_value IS 'Denormalized LTV (money).';
COMMENT ON COLUMN "11_somaerp".fct_customers.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_customers.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_customers.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_customers.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_customers.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_customers.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_fct_customers_tenant_slug
    ON "11_somaerp".fct_customers(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_customers_tenant_status
    ON "11_somaerp".fct_customers(tenant_id, status)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_customers_tenant_location
    ON "11_somaerp".fct_customers(tenant_id, location_id)
    WHERE deleted_at IS NULL;

-- ── fct_subscription_plans ────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_subscription_plans (
    id                   VARCHAR(36) NOT NULL,
    tenant_id            VARCHAR(36) NOT NULL,
    name                 TEXT NOT NULL,
    slug                 TEXT NOT NULL,
    description          TEXT,
    frequency_id         SMALLINT NOT NULL,
    price_per_delivery   NUMERIC(14,4),
    currency_code        CHAR(3) NOT NULL,
    status               TEXT NOT NULL DEFAULT 'active',
    properties           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           VARCHAR(36) NOT NULL,
    updated_by           VARCHAR(36) NOT NULL,
    deleted_at           TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_subscription_plans PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_subscription_plans_frequency FOREIGN KEY (frequency_id)
        REFERENCES "11_somaerp".dim_subscription_frequencies(id),
    CONSTRAINT chk_somaerp_fct_subscription_plans_status
        CHECK (status IN ('draft','active','archived')),
    CONSTRAINT chk_somaerp_fct_subscription_plans_price_nonneg
        CHECK (price_per_delivery IS NULL OR price_per_delivery >= 0)
);
COMMENT ON TABLE  "11_somaerp".fct_subscription_plans IS 'Tenant-defined plan templates: "Morning Glow", "Hydration Habit", etc.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.name IS 'Display name.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.slug IS 'URL-safe slug, unique per tenant.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.description IS 'Marketing copy.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.frequency_id IS 'FK to dim_subscription_frequencies.id.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.price_per_delivery IS 'Per-delivery price, tenant currency. Nullable = custom-billed plan.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.currency_code IS 'ISO 4217.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.status IS 'draft | active | archived.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_subscription_plans.deleted_at IS 'Soft-delete sentinel.';

CREATE UNIQUE INDEX idx_somaerp_fct_subscription_plans_tenant_slug
    ON "11_somaerp".fct_subscription_plans(tenant_id, slug)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_subscription_plans_tenant_status
    ON "11_somaerp".fct_subscription_plans(tenant_id, status)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_subscription_plans_tenant_frequency
    ON "11_somaerp".fct_subscription_plans(tenant_id, frequency_id)
    WHERE deleted_at IS NULL;

-- ── dtl_subscription_plan_items ──────────────────────────────────────────

CREATE TABLE "11_somaerp".dtl_subscription_plan_items (
    id                    VARCHAR(36) NOT NULL,
    tenant_id             VARCHAR(36) NOT NULL,
    plan_id               VARCHAR(36) NOT NULL,
    product_id            VARCHAR(36) NOT NULL,
    variant_id            VARCHAR(36),
    qty_per_delivery      NUMERIC(8,2) NOT NULL,
    position              INTEGER NOT NULL DEFAULT 0,
    notes                 TEXT,
    created_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by            VARCHAR(36) NOT NULL,
    updated_by            VARCHAR(36) NOT NULL,
    deleted_at            TIMESTAMP,
    CONSTRAINT pk_somaerp_dtl_subscription_plan_items PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_dtl_subscription_plan_items_plan FOREIGN KEY (plan_id)
        REFERENCES "11_somaerp".fct_subscription_plans(id),
    CONSTRAINT fk_somaerp_dtl_subscription_plan_items_product FOREIGN KEY (product_id)
        REFERENCES "11_somaerp".fct_products(id),
    CONSTRAINT fk_somaerp_dtl_subscription_plan_items_variant FOREIGN KEY (variant_id)
        REFERENCES "11_somaerp".fct_product_variants(id),
    CONSTRAINT chk_somaerp_dtl_subscription_plan_items_qty_pos
        CHECK (qty_per_delivery > 0)
);
COMMENT ON TABLE  "11_somaerp".dtl_subscription_plan_items IS 'Product mix for a subscription plan — one row per (plan, product, optional variant).';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.plan_id IS 'FK to fct_subscription_plans.id.';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.product_id IS 'FK to fct_products.id.';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.variant_id IS 'Optional FK to fct_product_variants.id (NULL = product default).';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.qty_per_delivery IS 'Quantity per delivery (bottles/units).';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.position IS 'Display ordering.';
COMMENT ON COLUMN "11_somaerp".dtl_subscription_plan_items.notes IS 'Free-text notes.';

-- Partial unique index: distinct (plan, product, variant) where variant may be NULL.
-- NULLS NOT DISTINCT avoided per convention; use two indexes.
CREATE UNIQUE INDEX idx_somaerp_dtl_sub_plan_items_uniq_var
    ON "11_somaerp".dtl_subscription_plan_items(plan_id, product_id, variant_id)
    WHERE deleted_at IS NULL AND variant_id IS NOT NULL;
CREATE UNIQUE INDEX idx_somaerp_dtl_sub_plan_items_uniq_novar
    ON "11_somaerp".dtl_subscription_plan_items(plan_id, product_id)
    WHERE deleted_at IS NULL AND variant_id IS NULL;
CREATE INDEX idx_somaerp_dtl_sub_plan_items_tenant_plan
    ON "11_somaerp".dtl_subscription_plan_items(tenant_id, plan_id)
    WHERE deleted_at IS NULL;

-- ── fct_subscriptions ────────────────────────────────────────────────────

CREATE TABLE "11_somaerp".fct_subscriptions (
    id                   VARCHAR(36) NOT NULL,
    tenant_id            VARCHAR(36) NOT NULL,
    customer_id          VARCHAR(36) NOT NULL,
    plan_id              VARCHAR(36) NOT NULL,
    service_zone_id      VARCHAR(36),
    start_date           DATE NOT NULL,
    end_date             DATE,
    status               TEXT NOT NULL DEFAULT 'active',
    paused_from          DATE,
    paused_to            DATE,
    billing_cycle        TEXT,
    properties           JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at           TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by           VARCHAR(36) NOT NULL,
    updated_by           VARCHAR(36) NOT NULL,
    deleted_at           TIMESTAMP,
    CONSTRAINT pk_somaerp_fct_subscriptions PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_fct_subscriptions_customer FOREIGN KEY (customer_id)
        REFERENCES "11_somaerp".fct_customers(id),
    CONSTRAINT fk_somaerp_fct_subscriptions_plan FOREIGN KEY (plan_id)
        REFERENCES "11_somaerp".fct_subscription_plans(id),
    CONSTRAINT fk_somaerp_fct_subscriptions_service_zone FOREIGN KEY (service_zone_id)
        REFERENCES "11_somaerp".fct_service_zones(id),
    CONSTRAINT chk_somaerp_fct_subscriptions_status
        CHECK (status IN ('active','paused','cancelled','ended')),
    CONSTRAINT chk_somaerp_fct_subscriptions_end_after_start
        CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT chk_somaerp_fct_subscriptions_pause_range
        CHECK (paused_to IS NULL OR paused_from IS NULL OR paused_to >= paused_from)
);
COMMENT ON TABLE  "11_somaerp".fct_subscriptions IS 'A customer-plan assignment with current lifecycle state. Transitions emit evt_subscription_events.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.customer_id IS 'FK to fct_customers.id.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.plan_id IS 'FK to fct_subscription_plans.id.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.service_zone_id IS 'Optional FK to fct_service_zones.id — delivery polygon anchor.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.start_date IS 'Service start date.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.end_date IS 'Service end date (null = open-ended).';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.status IS 'active | paused | cancelled | ended.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.paused_from IS 'Start of the active pause window.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.paused_to IS 'Planned end of the active pause window (null = indefinite).';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.billing_cycle IS 'weekly | monthly | prepaid (free text; validated in service).';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.properties IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.created_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.updated_at IS 'App-managed UTC timestamp.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.created_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.updated_by IS 'Acting user_id.';
COMMENT ON COLUMN "11_somaerp".fct_subscriptions.deleted_at IS 'Soft-delete sentinel.';

CREATE INDEX idx_somaerp_fct_subscriptions_tenant_customer
    ON "11_somaerp".fct_subscriptions(tenant_id, customer_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_subscriptions_tenant_plan
    ON "11_somaerp".fct_subscriptions(tenant_id, plan_id)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_subscriptions_tenant_status
    ON "11_somaerp".fct_subscriptions(tenant_id, status)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_somaerp_fct_subscriptions_tenant_start
    ON "11_somaerp".fct_subscriptions(tenant_id, start_date DESC)
    WHERE deleted_at IS NULL;

-- ── evt_subscription_events ──────────────────────────────────────────────

CREATE TABLE "11_somaerp".evt_subscription_events (
    id                       VARCHAR(36) NOT NULL,
    tenant_id                VARCHAR(36) NOT NULL,
    subscription_id          VARCHAR(36) NOT NULL,
    event_type               TEXT NOT NULL,
    from_date                DATE,
    to_date                  DATE,
    reason                   TEXT,
    metadata                 JSONB NOT NULL DEFAULT '{}'::jsonb,
    ts                       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    performed_by_user_id     VARCHAR(36) NOT NULL,
    created_at               TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_somaerp_evt_subscription_events PRIMARY KEY (id),
    CONSTRAINT fk_somaerp_evt_subscription_events_subscription FOREIGN KEY (subscription_id)
        REFERENCES "11_somaerp".fct_subscriptions(id),
    CONSTRAINT chk_somaerp_evt_subscription_events_event_type
        CHECK (event_type IN (
            'started','paused','resumed','cancelled','ended',
            'plan_changed','frequency_changed'
        ))
);
COMMENT ON TABLE  "11_somaerp".evt_subscription_events IS 'Append-only log of subscription lifecycle events.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.id IS 'UUID v7.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.tenant_id IS 'tennetctl workspace_id.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.subscription_id IS 'FK to fct_subscriptions.id.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.event_type IS 'started | paused | resumed | cancelled | ended | plan_changed | frequency_changed.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.from_date IS 'Event-specific start date (e.g. pause from).';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.to_date IS 'Event-specific end date (e.g. pause to).';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.reason IS 'Optional free-text reason.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.metadata IS 'JSONB side-channel.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.ts IS 'Event timestamp (business meaning).';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.performed_by_user_id IS 'iam user_id who triggered the event.';
COMMENT ON COLUMN "11_somaerp".evt_subscription_events.created_at IS 'Row insert timestamp.';

CREATE INDEX idx_somaerp_evt_subscription_events_tenant_sub
    ON "11_somaerp".evt_subscription_events(tenant_id, subscription_id, ts DESC);
CREATE INDEX idx_somaerp_evt_subscription_events_tenant_type
    ON "11_somaerp".evt_subscription_events(tenant_id, event_type, ts DESC);

-- ── Views ────────────────────────────────────────────────────────────────

CREATE VIEW "11_somaerp".v_customers AS
SELECT
    c.id,
    c.tenant_id,
    c.location_id,
    l.name                          AS location_name,
    c.name,
    c.slug,
    c.email,
    c.phone,
    c.address_jsonb,
    c.delivery_notes,
    c.acquisition_source,
    c.status,
    c.lifetime_value,
    c.properties,
    c.created_at,
    c.updated_at,
    c.created_by,
    c.updated_by,
    c.deleted_at,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".fct_subscriptions s
        WHERE s.customer_id = c.id
          AND s.tenant_id   = c.tenant_id
          AND s.status      = 'active'
          AND s.deleted_at  IS NULL
    ), 0)                           AS active_subscription_count
FROM "11_somaerp".fct_customers c
LEFT JOIN "11_somaerp".fct_locations l ON l.id = c.location_id;
COMMENT ON VIEW "11_somaerp".v_customers IS 'fct_customers joined with fct_locations (for location_name) + computed active_subscription_count.';

CREATE VIEW "11_somaerp".v_subscription_plans AS
SELECT
    p.id,
    p.tenant_id,
    p.name,
    p.slug,
    p.description,
    p.frequency_id,
    f.code                           AS frequency_code,
    f.name                           AS frequency_name,
    f.deliveries_per_week,
    p.price_per_delivery,
    p.currency_code,
    p.status,
    p.properties,
    p.created_at,
    p.updated_at,
    p.created_by,
    p.updated_by,
    p.deleted_at,
    COALESCE((
        SELECT COUNT(*)::INT
        FROM "11_somaerp".dtl_subscription_plan_items i
        WHERE i.plan_id = p.id
          AND i.tenant_id = p.tenant_id
          AND i.deleted_at IS NULL
    ), 0)                            AS item_count
FROM "11_somaerp".fct_subscription_plans p
LEFT JOIN "11_somaerp".dim_subscription_frequencies f ON f.id = p.frequency_id;
COMMENT ON VIEW "11_somaerp".v_subscription_plans IS 'fct_subscription_plans joined with frequency + computed item_count.';

CREATE VIEW "11_somaerp".v_subscription_plan_items AS
SELECT
    i.id,
    i.tenant_id,
    i.plan_id,
    i.product_id,
    pr.name                          AS product_name,
    pr.slug                          AS product_slug,
    i.variant_id,
    v.name                           AS variant_name,
    i.qty_per_delivery,
    i.position,
    i.notes,
    i.created_at,
    i.updated_at,
    i.created_by,
    i.updated_by,
    i.deleted_at,
    -- line_price = qty_per_delivery * (variant_price COALESCE product_price)
    (i.qty_per_delivery *
        COALESCE(v.selling_price, pr.default_selling_price, 0))
                                     AS line_price,
    COALESCE(v.currency_code, pr.currency_code) AS currency_code
FROM "11_somaerp".dtl_subscription_plan_items i
LEFT JOIN "11_somaerp".fct_products        pr ON pr.id = i.product_id
LEFT JOIN "11_somaerp".fct_product_variants v  ON v.id  = i.variant_id;
COMMENT ON VIEW "11_somaerp".v_subscription_plan_items IS 'dtl_subscription_plan_items joined with product + variant + computed line_price.';

CREATE VIEW "11_somaerp".v_subscriptions AS
SELECT
    s.id,
    s.tenant_id,
    s.customer_id,
    c.name                           AS customer_name,
    c.slug                           AS customer_slug,
    s.plan_id,
    p.name                           AS plan_name,
    p.slug                           AS plan_slug,
    p.frequency_id,
    f.code                           AS frequency_code,
    f.name                           AS frequency_name,
    p.price_per_delivery,
    s.service_zone_id,
    z.name                           AS service_zone_name,
    s.start_date,
    s.end_date,
    s.status,
    s.paused_from,
    s.paused_to,
    s.billing_cycle,
    s.properties,
    s.created_at,
    s.updated_at,
    s.created_by,
    s.updated_by,
    s.deleted_at,
    p.currency_code
FROM "11_somaerp".fct_subscriptions s
LEFT JOIN "11_somaerp".fct_customers           c ON c.id = s.customer_id
LEFT JOIN "11_somaerp".fct_subscription_plans  p ON p.id = s.plan_id
LEFT JOIN "11_somaerp".dim_subscription_frequencies f ON f.id = p.frequency_id
LEFT JOIN "11_somaerp".fct_service_zones       z ON z.id = s.service_zone_id;
COMMENT ON VIEW "11_somaerp".v_subscriptions IS 'fct_subscriptions joined with customer + plan + frequency + service_zone.';


-- DOWN ==================================================================

DROP VIEW  IF EXISTS "11_somaerp".v_subscriptions;
DROP VIEW  IF EXISTS "11_somaerp".v_subscription_plan_items;
DROP VIEW  IF EXISTS "11_somaerp".v_subscription_plans;
DROP VIEW  IF EXISTS "11_somaerp".v_customers;

DROP TABLE IF EXISTS "11_somaerp".evt_subscription_events;
DROP TABLE IF EXISTS "11_somaerp".fct_subscriptions;
DROP TABLE IF EXISTS "11_somaerp".dtl_subscription_plan_items;
DROP TABLE IF EXISTS "11_somaerp".fct_subscription_plans;
DROP TABLE IF EXISTS "11_somaerp".fct_customers;
DROP TABLE IF EXISTS "11_somaerp".dim_subscription_frequencies;
