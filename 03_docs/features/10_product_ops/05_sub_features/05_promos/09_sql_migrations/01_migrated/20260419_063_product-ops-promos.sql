-- UP ====

-- product_ops.promos — promotional codes (coupons), distinct from referrals.
--
-- Phase 47 referrals = "credit a referrer when a referred visitor converts".
-- Phase 50 promos    = "give a discount/perk to anyone who redeems this code".
--
-- Shared concept: a code string; differences:
--   - promos have global + per-user usage caps
--   - promos have expiry windows (starts_at/ends_at)
--   - promos have redemption_kind (discount_pct, discount_cents, free_trial_days, custom)
--   - promos track redemptions (one row per use), not conversions

CREATE TABLE "10_product_ops"."10_fct_promo_codes" (
    id                  VARCHAR(36) NOT NULL,
    code                TEXT NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    workspace_id        VARCHAR(36) NOT NULL,
    -- What the promo does. Reward shape stored as JSONB for flexibility, but a
    -- typed kind enables filtering + UI rendering without unpacking JSONB.
    redemption_kind     TEXT NOT NULL,
    redemption_config   JSONB NOT NULL DEFAULT '{}'::jsonb,
    description         TEXT,
    -- Usage caps
    max_total_uses      INTEGER,                -- NULL = unlimited
    max_uses_per_visitor INTEGER NOT NULL DEFAULT 1,
    -- Time window
    starts_at           TIMESTAMP,              -- NULL = available immediately
    ends_at             TIMESTAMP,              -- NULL = no expiry
    -- Eligibility (optional caller-defined predicate stored as JSONB for forward compat)
    eligibility         JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Operational
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_by          VARCHAR(36) NOT NULL,
    deleted_at          TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_promo_codes PRIMARY KEY (id),
    CONSTRAINT uq_fct_promo_codes_workspace_code UNIQUE (workspace_id, code),
    CONSTRAINT chk_fct_promo_codes_redemption_kind
        CHECK (redemption_kind IN ('discount_pct','discount_cents','free_trial_days','custom')),
    CONSTRAINT chk_fct_promo_codes_max_per_visitor
        CHECK (max_uses_per_visitor >= 1)
);

CREATE INDEX idx_fct_promo_codes_workspace_active
    ON "10_product_ops"."10_fct_promo_codes" (workspace_id, is_active)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE "10_product_ops"."10_fct_promo_codes" IS 'Promotional codes (coupons). Distinct from referrals (Phase 47): promos discount the redeemer; referrals credit the referrer. UNIQUE per workspace.';
COMMENT ON COLUMN "10_product_ops"."10_fct_promo_codes".redemption_kind IS 'discount_pct | discount_cents | free_trial_days | custom. CHECK enforced.';
COMMENT ON COLUMN "10_product_ops"."10_fct_promo_codes".redemption_config IS 'Shape depends on kind: {"value":20} for discount_pct, {"amount_cents":1000} for discount_cents, {"days":30} for free_trial_days, free-form for custom.';
COMMENT ON COLUMN "10_product_ops"."10_fct_promo_codes".eligibility IS 'Caller-defined predicate. v1: ignored by service (operator enforces externally). v2 may interpret {"plan":"free"} etc.';

-- ── Redemption log (append-only) ──────────────────────────────────

CREATE TABLE "10_product_ops"."60_evt_promo_redemptions" (
    id                  VARCHAR(36) NOT NULL,
    promo_code_id       VARCHAR(36) NOT NULL,
    visitor_id          VARCHAR(36),                -- nullable for non-tracked redemptions
    redeemer_user_id    VARCHAR(36),                -- nullable for anonymous redemptions
    org_id              VARCHAR(36) NOT NULL,
    workspace_id        VARCHAR(36) NOT NULL,
    -- Outcome of the redemption attempt
    outcome             TEXT NOT NULL,              -- redeemed | rejected_max_uses | rejected_per_visitor | rejected_expired | rejected_inactive
    rejection_reason    TEXT,
    -- Optional payload (e.g. order_id, amount_before_discount)
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at         TIMESTAMP NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_promo_redemptions PRIMARY KEY (id),
    CONSTRAINT fk_evt_promo_redemptions_code
        FOREIGN KEY (promo_code_id)
        REFERENCES "10_product_ops"."10_fct_promo_codes"(id),
    CONSTRAINT chk_evt_promo_redemptions_outcome
        CHECK (outcome IN ('redeemed','rejected_max_uses','rejected_per_visitor','rejected_expired','rejected_inactive','rejected_eligibility','rejected_unknown_code'))
);

CREATE INDEX idx_evt_promo_redemptions_code_occurred
    ON "10_product_ops"."60_evt_promo_redemptions" (promo_code_id, occurred_at DESC);
CREATE INDEX idx_evt_promo_redemptions_visitor
    ON "10_product_ops"."60_evt_promo_redemptions" (visitor_id)
    WHERE visitor_id IS NOT NULL;
CREATE INDEX idx_evt_promo_redemptions_user
    ON "10_product_ops"."60_evt_promo_redemptions" (redeemer_user_id)
    WHERE redeemer_user_id IS NOT NULL;

COMMENT ON TABLE "10_product_ops"."60_evt_promo_redemptions" IS 'Append-only redemption log. Records ALL attempts (successful redemption + rejections) so operators can audit cap hits + investigate fraud patterns.';

-- ── Read view ─────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "10_product_ops".v_promo_codes AS
SELECT
    p.id,
    p.code,
    p.org_id,
    p.workspace_id,
    p.redemption_kind,
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
    -- Pre-aggregated counts
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
       WHERE r.promo_code_id = p.id AND r.outcome = 'redeemed') AS redemption_count,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" r
       WHERE r.promo_code_id = p.id AND r.outcome <> 'redeemed') AS rejection_count,
    -- Computed status: scheduled | active | expired | inactive | exhausted
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

COMMENT ON VIEW "10_product_ops".v_promo_codes IS 'Promo read view with pre-aggregated redemption counts + computed status (scheduled/active/expired/inactive/exhausted).';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_promo_codes;
DROP TABLE IF EXISTS "10_product_ops"."60_evt_promo_redemptions";
DROP TABLE IF EXISTS "10_product_ops"."10_fct_promo_codes";
