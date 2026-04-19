-- UP ====

-- Make promo redemption_kind operator-extensible by replacing the inline CHECK
-- with a FK to a dim table. Phase 10 dim_audit_event_keys precedent: when the
-- value space might grow, store it in dim_*; when it's frozen, use CHECK.
--
-- Each kind carries a JSON Schema for its redemption_config so the admin UI
-- can render kind-specific form fields without hardcoded knowledge.
--
-- The fct_promo_codes.redemption_kind column stays as TEXT (legibility for
-- direct SQL queries + back-compat with existing rows). We add a FK validator
-- via a CHECK using EXISTS … but that's slow on hot paths; we do the safer
-- thing — service-layer validation against the dim. CHECK is dropped.

CREATE TABLE "10_product_ops"."01_dim_promotion_kinds" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    -- JSON Schema for redemption_config. Used by admin UI to render the right
    -- form + by service to validate. Stored as JSONB for portability.
    config_schema   JSONB NOT NULL DEFAULT '{}'::jsonb,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_promotion_kinds PRIMARY KEY (id),
    CONSTRAINT uq_dim_promotion_kinds_code UNIQUE (code)
);

INSERT INTO "10_product_ops"."01_dim_promotion_kinds" (id, code, label, description, config_schema) VALUES
    (1, 'discount_pct',     'Percentage Discount',
        'Reduce price by a percentage. config: {"value": 20} = 20% off.',
        '{"type":"object","required":["value"],"properties":{"value":{"type":"number","minimum":0,"maximum":100,"description":"Percent off (0–100)"}}}'::jsonb),
    (2, 'discount_cents',   'Fixed-Amount Discount',
        'Reduce price by a fixed amount in cents. config: {"amount_cents": 1000} = $10 off.',
        '{"type":"object","required":["amount_cents"],"properties":{"amount_cents":{"type":"integer","minimum":0,"description":"Cents to subtract from price"}}}'::jsonb),
    (3, 'free_trial_days',  'Free Trial Extension',
        'Extend the customer''s free trial. config: {"days": 30} = 30-day extension.',
        '{"type":"object","required":["days"],"properties":{"days":{"type":"integer","minimum":1,"maximum":365}}}'::jsonb),
    (4, 'custom',           'Custom (caller-defined)',
        'Caller-defined reward — service does not interpret config. Use when none of the standard kinds fit; redemption metadata flows back to the caller for client-side handling.',
        '{"type":"object","description":"Free-form caller payload","additionalProperties":true}'::jsonb),
    (5, 'bogo',             'Buy One Get One',
        'BOGO — buy quantity X, get quantity Y free or discounted. config: {"buy_qty": 1, "get_qty": 1, "get_discount_pct": 100, "applies_to_skus": ["..."]}.',
        '{"type":"object","required":["buy_qty","get_qty"],"properties":{"buy_qty":{"type":"integer","minimum":1},"get_qty":{"type":"integer","minimum":1},"get_discount_pct":{"type":"number","minimum":0,"maximum":100,"default":100},"applies_to_skus":{"type":"array","items":{"type":"string"}}}}'::jsonb),
    (6, 'tiered_discount',  'Tiered Discount',
        'Spend-threshold tiers. config: {"tiers": [{"min_cents": 5000, "discount_pct": 10}, {"min_cents": 10000, "discount_pct": 20}]}. Highest matching tier wins.',
        '{"type":"object","required":["tiers"],"properties":{"tiers":{"type":"array","items":{"type":"object","required":["min_cents"],"properties":{"min_cents":{"type":"integer","minimum":0},"discount_pct":{"type":"number","minimum":0,"maximum":100},"discount_cents":{"type":"integer","minimum":0}}}}}}'::jsonb),
    (7, 'bundle_discount',  'Bundle Discount',
        'Discount applied when a specified set of SKUs are purchased together. config: {"required_skus": ["A","B"], "bundle_price_cents": 4900}.',
        '{"type":"object","required":["required_skus","bundle_price_cents"],"properties":{"required_skus":{"type":"array","items":{"type":"string"},"minItems":2},"bundle_price_cents":{"type":"integer","minimum":0}}}'::jsonb),
    (8, 'free_shipping',    'Free Shipping',
        'Waive shipping cost. config: {"countries": ["US","CA"], "min_order_cents": 0}.',
        '{"type":"object","properties":{"countries":{"type":"array","items":{"type":"string","minLength":2,"maxLength":2}},"min_order_cents":{"type":"integer","minimum":0,"default":0}}}'::jsonb),
    (9, 'gift_credit',      'Gift Credit / Account Credit',
        'Add credit to the redeemer''s account. config: {"amount_cents": 2500, "currency": "USD", "expires_days": 365}.',
        '{"type":"object","required":["amount_cents"],"properties":{"amount_cents":{"type":"integer","minimum":0},"currency":{"type":"string","default":"USD"},"expires_days":{"type":"integer","minimum":1}}}'::jsonb)
ON CONFLICT (id) DO NOTHING;

COMMENT ON TABLE "10_product_ops"."01_dim_promotion_kinds" IS 'Operator-extensible promotion kind taxonomy. Each kind carries a JSON Schema for its redemption_config so the admin UI can render the right form. Add new kinds via INSERT (preserve IDs to keep evt_promo_redemptions joinable).';

-- Drop the old CHECK; service layer + dim FK now own validation.
ALTER TABLE "10_product_ops"."10_fct_promo_codes"
    DROP CONSTRAINT chk_fct_promo_codes_redemption_kind;

-- Add a FK by code (denormalized — keep TEXT for SQL legibility).
-- No CASCADE on update because dim codes are immutable by convention.
ALTER TABLE "10_product_ops"."10_fct_promo_codes"
    ADD CONSTRAINT fk_fct_promo_codes_redemption_kind
        FOREIGN KEY (redemption_kind)
        REFERENCES "10_product_ops"."01_dim_promotion_kinds"(code)
        DEFERRABLE INITIALLY IMMEDIATE;

-- Refresh v_promo_codes to expose the kind label + config schema for the UI.
DROP VIEW IF EXISTS "10_product_ops".v_promo_codes;
CREATE OR REPLACE VIEW "10_product_ops".v_promo_codes AS
SELECT
    p.id,
    p.code,
    p.org_id,
    p.workspace_id,
    p.redemption_kind,
    pk.label AS redemption_kind_label,
    pk.config_schema AS redemption_kind_schema,
    p.redemption_config,
    p.description,
    p.max_total_uses,
    p.max_uses_per_visitor,
    p.starts_at,
    p.ends_at,
    p.eligibility,
    p.is_active,
    (p.deleted_at IS NOT NULL) AS is_deleted,
    p.deleted_at,
    p.created_by,
    p.created_at,
    p.updated_at,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
       WHERE r.promo_code_id = p.id AND r.outcome = 'redeemed') AS redemption_count,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
       WHERE r.promo_code_id = p.id AND r.outcome <> 'redeemed') AS rejection_count,
    CASE
        WHEN p.deleted_at IS NOT NULL OR NOT p.is_active THEN 'inactive'
        WHEN p.starts_at IS NOT NULL AND p.starts_at > CURRENT_TIMESTAMP THEN 'scheduled'
        WHEN p.ends_at IS NOT NULL AND p.ends_at < CURRENT_TIMESTAMP THEN 'expired'
        WHEN p.max_total_uses IS NOT NULL
             AND (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
                    WHERE r.promo_code_id = p.id AND r.outcome = 'redeemed') >= p.max_total_uses THEN 'exhausted'
        ELSE 'active'
    END AS status
FROM "10_product_ops"."10_fct_promo_codes" p
LEFT JOIN "10_product_ops"."01_dim_promotion_kinds" pk ON pk.code = p.redemption_kind;

-- DOWN ====

-- Restore old view shape
DROP VIEW IF EXISTS "10_product_ops".v_promo_codes;
CREATE OR REPLACE VIEW "10_product_ops".v_promo_codes AS
SELECT
    p.id, p.code, p.org_id, p.workspace_id,
    p.redemption_kind, p.redemption_config, p.description,
    p.max_total_uses, p.max_uses_per_visitor,
    p.starts_at, p.ends_at, p.eligibility,
    p.is_active, (p.deleted_at IS NOT NULL) AS is_deleted, p.deleted_at,
    p.created_by, p.created_at, p.updated_at,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
       WHERE r.promo_code_id = p.id AND r.outcome = 'redeemed') AS redemption_count,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
       WHERE r.promo_code_id = p.id AND r.outcome <> 'redeemed') AS rejection_count,
    CASE
        WHEN p.deleted_at IS NOT NULL OR NOT p.is_active THEN 'inactive'
        WHEN p.starts_at IS NOT NULL AND p.starts_at > CURRENT_TIMESTAMP THEN 'scheduled'
        WHEN p.ends_at IS NOT NULL AND p.ends_at < CURRENT_TIMESTAMP THEN 'expired'
        WHEN p.max_total_uses IS NOT NULL
             AND (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
                    WHERE r.promo_code_id = p.id AND r.outcome = 'redeemed') >= p.max_total_uses THEN 'exhausted'
        ELSE 'active'
    END AS status
FROM "10_product_ops"."10_fct_promo_codes" p;

ALTER TABLE "10_product_ops"."10_fct_promo_codes"
    DROP CONSTRAINT IF EXISTS fk_fct_promo_codes_redemption_kind;
ALTER TABLE "10_product_ops"."10_fct_promo_codes"
    ADD CONSTRAINT chk_fct_promo_codes_redemption_kind
        CHECK (redemption_kind IN ('discount_pct','discount_cents','free_trial_days','custom'));
DROP TABLE IF EXISTS "10_product_ops"."01_dim_promotion_kinds";
