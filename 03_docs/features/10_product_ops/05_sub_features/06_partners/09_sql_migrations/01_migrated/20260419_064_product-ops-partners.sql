-- UP ====

-- product_ops.partners — B2B affiliate / partner management.
--
-- Compared to Phase 47 referrals (which credit a referrer = a single end-user),
-- partners are first-class business entities (companies, agencies, influencers
-- with multiple codes) with tiers, lifetime stats, payout tracking, and
-- partner-facing dashboard data.
--
-- A Partner OWNS multiple referral codes (Phase 47) and/or promo codes (Phase 50).
-- This sub-feature models the partner side; conversion attribution + payout
-- math joins back through the existing referral/promo evt_* tables.

-- ── Partners ─────────────────────────────────────────────────────

CREATE TABLE "10_product_ops"."10_fct_partners" (
    id                  VARCHAR(36) NOT NULL,
    -- Stable handle (URL-safe slug, e.g. "agency-foo"). UNIQUE per workspace.
    slug                TEXT NOT NULL,
    display_name        TEXT NOT NULL,
    contact_email       TEXT NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    workspace_id        VARCHAR(36) NOT NULL,
    -- Optional link to an IAM user (for partner login)
    user_id             VARCHAR(36),
    -- Tier (small SMALLINT FK; tier rules are a dim_partner_tiers table)
    tier_id             SMALLINT NOT NULL,
    -- Operational
    is_active           BOOLEAN NOT NULL DEFAULT TRUE,
    created_by          VARCHAR(36) NOT NULL,
    deleted_at          TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_partners PRIMARY KEY (id),
    CONSTRAINT uq_fct_partners_workspace_slug UNIQUE (workspace_id, slug)
);

CREATE INDEX idx_fct_partners_workspace_active
    ON "10_product_ops"."10_fct_partners" (workspace_id, is_active)
    WHERE deleted_at IS NULL;
CREATE INDEX idx_fct_partners_user_id
    ON "10_product_ops"."10_fct_partners" (user_id)
    WHERE user_id IS NOT NULL;

COMMENT ON TABLE "10_product_ops"."10_fct_partners" IS 'B2B affiliate / partner accounts. Owns referral codes (Phase 47) and/or promo codes (Phase 50). Optional user_id binding lets partners log in via IAM.';

-- ── Tiers (dim — statically seeded; operators can extend via migration) ──

CREATE TABLE "10_product_ops"."01_dim_partner_tiers" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    -- Default payout rate as basis points (1 bp = 0.01%); tier-level default,
    -- partner can override on link table. 1000 = 10%.
    default_payout_bp INTEGER NOT NULL DEFAULT 1000,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_partner_tiers PRIMARY KEY (id),
    CONSTRAINT uq_dim_partner_tiers_code UNIQUE (code)
);

INSERT INTO "10_product_ops"."01_dim_partner_tiers" (id, code, label, description, default_payout_bp) VALUES
    (1, 'standard',  'Standard',  'Default tier — 10% payout',                    1000),
    (2, 'silver',    'Silver',    'Mid-tier — 15% payout',                        1500),
    (3, 'gold',      'Gold',      'High-tier — 20% payout',                       2000),
    (4, 'platinum',  'Platinum',  'Top-tier — 25% payout, custom contract',       2500)
ON CONFLICT (id) DO NOTHING;

ALTER TABLE "10_product_ops"."10_fct_partners"
    ADD CONSTRAINT fk_fct_partners_tier
        FOREIGN KEY (tier_id) REFERENCES "10_product_ops"."01_dim_partner_tiers"(id);

-- ── Link partners to their referral codes + promo codes ────────────

CREATE TABLE "10_product_ops"."40_lnk_partner_codes" (
    id                  VARCHAR(36) NOT NULL,
    partner_id          VARCHAR(36) NOT NULL,
    code_kind           TEXT NOT NULL,          -- 'referral' | 'promo'
    -- Discriminated union: one of these is set, matching code_kind
    referral_code_id    VARCHAR(36),
    promo_code_id       VARCHAR(36),
    -- Per-link payout override (NULL = inherit tier default)
    payout_bp_override  INTEGER,
    org_id              VARCHAR(36) NOT NULL,
    created_by          VARCHAR(36) NOT NULL,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_lnk_partner_codes PRIMARY KEY (id),
    CONSTRAINT fk_lnk_partner_codes_partner
        FOREIGN KEY (partner_id) REFERENCES "10_product_ops"."10_fct_partners"(id)
        ON DELETE CASCADE,
    CONSTRAINT fk_lnk_partner_codes_referral
        FOREIGN KEY (referral_code_id) REFERENCES "10_product_ops"."10_fct_referral_codes"(id),
    CONSTRAINT fk_lnk_partner_codes_promo
        FOREIGN KEY (promo_code_id) REFERENCES "10_product_ops"."10_fct_promo_codes"(id),
    CONSTRAINT chk_lnk_partner_codes_one_kind
        CHECK ((code_kind = 'referral' AND referral_code_id IS NOT NULL AND promo_code_id IS NULL)
            OR (code_kind = 'promo'    AND promo_code_id    IS NOT NULL AND referral_code_id IS NULL))
);

CREATE INDEX idx_lnk_partner_codes_partner ON "10_product_ops"."40_lnk_partner_codes" (partner_id);
CREATE INDEX idx_lnk_partner_codes_referral ON "10_product_ops"."40_lnk_partner_codes" (referral_code_id) WHERE referral_code_id IS NOT NULL;
CREATE INDEX idx_lnk_partner_codes_promo ON "10_product_ops"."40_lnk_partner_codes" (promo_code_id) WHERE promo_code_id IS NOT NULL;

COMMENT ON TABLE "10_product_ops"."40_lnk_partner_codes" IS 'Joins partners to their referral codes + promo codes. Discriminated by code_kind. CHECK enforces exactly one FK is set per row.';

-- ── Payout log (append-only) ──────────────────────────────────────

CREATE TABLE "10_product_ops"."60_evt_partner_payouts" (
    id                  VARCHAR(36) NOT NULL,
    partner_id          VARCHAR(36) NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    workspace_id        VARCHAR(36) NOT NULL,
    period_start        TIMESTAMP NOT NULL,
    period_end          TIMESTAMP NOT NULL,
    amount_cents        BIGINT NOT NULL,
    currency            TEXT NOT NULL DEFAULT 'USD',
    status              TEXT NOT NULL,          -- pending | paid | failed | cancelled
    paid_at             TIMESTAMP,
    external_ref        TEXT,                   -- external system reference (Stripe payout id, etc.)
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by          VARCHAR(36) NOT NULL,
    occurred_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_partner_payouts PRIMARY KEY (id),
    CONSTRAINT fk_evt_partner_payouts_partner
        FOREIGN KEY (partner_id) REFERENCES "10_product_ops"."10_fct_partners"(id),
    CONSTRAINT chk_evt_partner_payouts_status
        CHECK (status IN ('pending','paid','failed','cancelled'))
);

CREATE INDEX idx_evt_partner_payouts_partner_occurred
    ON "10_product_ops"."60_evt_partner_payouts" (partner_id, occurred_at DESC);
CREATE INDEX idx_evt_partner_payouts_status
    ON "10_product_ops"."60_evt_partner_payouts" (status, occurred_at DESC);

COMMENT ON TABLE "10_product_ops"."60_evt_partner_payouts" IS 'Append-only payout log. Operator records outbound payments to partners; external_ref ties to upstream financial system (Stripe, Wise, Mercury, etc.).';

-- ── Read view: partner stats ──────────────────────────────────────

CREATE OR REPLACE VIEW "10_product_ops".v_partners AS
SELECT
    p.id,
    p.slug,
    p.display_name,
    p.contact_email,
    p.org_id,
    p.workspace_id,
    p.user_id,
    p.tier_id,
    t.code AS tier_code,
    t.label AS tier_label,
    t.default_payout_bp,
    p.is_active,
    (p.deleted_at IS NOT NULL) AS is_deleted,
    p.deleted_at,
    p.created_by,
    p.created_at,
    p.updated_at,
    -- Pre-aggregated lifetime stats
    (SELECT COUNT(*)::int
       FROM "10_product_ops"."40_lnk_partner_codes" lpc
      WHERE lpc.partner_id = p.id) AS code_count,
    -- Conversions across all linked referral codes
    (SELECT COALESCE(COUNT(c.*), 0)::int
       FROM "10_product_ops"."40_lnk_partner_codes" lpc
       JOIN "10_product_ops"."60_evt_referral_conversions" c
         ON c.referral_code_id = lpc.referral_code_id
      WHERE lpc.partner_id = p.id) AS conversion_count,
    -- Total conversion value across linked referrals
    (SELECT COALESCE(SUM(c.conversion_value_cents), 0)::bigint
       FROM "10_product_ops"."40_lnk_partner_codes" lpc
       JOIN "10_product_ops"."60_evt_referral_conversions" c
         ON c.referral_code_id = lpc.referral_code_id
      WHERE lpc.partner_id = p.id) AS conversion_value_cents_total,
    -- Lifetime payouts paid + pending
    (SELECT COALESCE(SUM(amount_cents), 0)::bigint
       FROM "10_product_ops"."60_evt_partner_payouts" pay
      WHERE pay.partner_id = p.id AND pay.status = 'paid') AS payout_paid_cents,
    (SELECT COALESCE(SUM(amount_cents), 0)::bigint
       FROM "10_product_ops"."60_evt_partner_payouts" pay
      WHERE pay.partner_id = p.id AND pay.status = 'pending') AS payout_pending_cents
FROM "10_product_ops"."10_fct_partners" p
JOIN "10_product_ops"."01_dim_partner_tiers" t ON t.id = p.tier_id;

COMMENT ON VIEW "10_product_ops".v_partners IS 'Partner read view with pre-aggregated lifetime stats: code count, conversion count + value, paid + pending payouts. Enables partner leaderboard + dashboard with no extra queries.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_partners;
DROP TABLE IF EXISTS "10_product_ops"."60_evt_partner_payouts";
DROP TABLE IF EXISTS "10_product_ops"."40_lnk_partner_codes";
ALTER TABLE "10_product_ops"."10_fct_partners" DROP CONSTRAINT IF EXISTS fk_fct_partners_tier;
DROP TABLE IF EXISTS "10_product_ops"."01_dim_partner_tiers";
DROP TABLE IF EXISTS "10_product_ops"."10_fct_partners";
