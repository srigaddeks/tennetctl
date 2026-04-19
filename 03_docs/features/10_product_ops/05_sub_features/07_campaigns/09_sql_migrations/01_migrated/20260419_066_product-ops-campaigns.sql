-- UP ====

-- product_ops.campaigns — bundle multiple promos under a named campaign with
-- shared schedule + audience eligibility + A/B-style weighting.
--
-- Design principle: campaigns are a thin orchestration layer. The real reward
-- shape stays on the promo (Phase 50). A campaign just groups + schedules +
-- targets. This keeps individual promos composable across many campaigns
-- ("Spring Launch" + "Email Reactivation" can both link the same SAVE10 promo
-- with different weights).

CREATE TABLE "10_product_ops"."10_fct_promo_campaigns" (
    id              VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    -- Schedule (BOTH this AND each promo's schedule must be active for the promo
    -- to be redeemable via the campaign).
    starts_at       TIMESTAMP,
    ends_at         TIMESTAMP,
    -- Audience eligibility (rule AST evaluated by service against visitor profile)
    audience_rule   JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Operator-defined goals/budget (opaque to v1 service).
    -- Examples: {"target_redemptions": 10000, "budget_cents": 50000}.
    goals           JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Operational
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_promo_campaigns PRIMARY KEY (id),
    CONSTRAINT uq_fct_promo_campaigns_workspace_slug UNIQUE (workspace_id, slug)
);

CREATE INDEX idx_fct_promo_campaigns_workspace_active
    ON "10_product_ops"."10_fct_promo_campaigns" (workspace_id, is_active)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE "10_product_ops"."10_fct_promo_campaigns" IS 'Promotion campaigns: bundle multiple promo codes under a named campaign with shared schedule + audience filter + A/B weighting. Campaigns add orchestration; individual reward shapes stay on the promo.';
COMMENT ON COLUMN "10_product_ops"."10_fct_promo_campaigns".audience_rule IS 'JSONB rule AST evaluated against visitor profile by service.eligibility_evaluator. Examples: {"op":"eq","field":"visitor.plan","value":"free"} or {"op":"all","rules":[...]}.';

-- ── Link campaigns to promos with weights (A/B testing primitive) ──

CREATE TABLE "10_product_ops"."40_lnk_campaign_promos" (
    id              VARCHAR(36) NOT NULL,
    campaign_id     VARCHAR(36) NOT NULL,
    promo_code_id   VARCHAR(36) NOT NULL,
    -- Weight for A/B selection. Higher = more often shown.
    -- Picker normalizes by sum across all active promos in the campaign.
    weight          INTEGER NOT NULL DEFAULT 1,
    -- Optional per-link override of the promo's audience (NULL = use campaign rule)
    audience_rule_override JSONB,
    org_id          VARCHAR(36) NOT NULL,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_lnk_campaign_promos PRIMARY KEY (id),
    CONSTRAINT uq_lnk_campaign_promos_campaign_promo UNIQUE (campaign_id, promo_code_id),
    CONSTRAINT fk_lnk_campaign_promos_campaign
        FOREIGN KEY (campaign_id) REFERENCES "10_product_ops"."10_fct_promo_campaigns"(id) ON DELETE CASCADE,
    CONSTRAINT fk_lnk_campaign_promos_promo
        FOREIGN KEY (promo_code_id) REFERENCES "10_product_ops"."10_fct_promo_codes"(id),
    CONSTRAINT chk_lnk_campaign_promos_weight CHECK (weight >= 1)
);

CREATE INDEX idx_lnk_campaign_promos_campaign ON "10_product_ops"."40_lnk_campaign_promos" (campaign_id);
CREATE INDEX idx_lnk_campaign_promos_promo ON "10_product_ops"."40_lnk_campaign_promos" (promo_code_id);

COMMENT ON TABLE "10_product_ops"."40_lnk_campaign_promos" IS 'Joins campaigns to their promo codes with A/B weights. Same promo can belong to multiple campaigns. UNIQUE (campaign_id, promo_code_id) prevents duplicate linkage.';

-- ── Campaign exposure log (append-only, optional but recommended) ──

CREATE TABLE "10_product_ops"."60_evt_campaign_exposures" (
    id              VARCHAR(36) NOT NULL,
    campaign_id     VARCHAR(36) NOT NULL,
    promo_code_id   VARCHAR(36),       -- nullable: visitor saw the campaign but no promo was assigned (eligibility miss)
    visitor_id      VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    -- Why this promo was assigned (or why none): "weighted_pick" | "eligibility_miss" | "no_active_promos"
    decision        TEXT NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_campaign_exposures PRIMARY KEY (id),
    CONSTRAINT fk_evt_campaign_exposures_campaign
        FOREIGN KEY (campaign_id) REFERENCES "10_product_ops"."10_fct_promo_campaigns"(id),
    CONSTRAINT fk_evt_campaign_exposures_promo
        FOREIGN KEY (promo_code_id) REFERENCES "10_product_ops"."10_fct_promo_codes"(id)
);

CREATE INDEX idx_evt_campaign_exposures_campaign_occurred
    ON "10_product_ops"."60_evt_campaign_exposures" (campaign_id, occurred_at DESC);
CREATE INDEX idx_evt_campaign_exposures_visitor
    ON "10_product_ops"."60_evt_campaign_exposures" (visitor_id);

COMMENT ON TABLE "10_product_ops"."60_evt_campaign_exposures" IS 'Append-only campaign exposure log. Records every (campaign, visitor) impression — what promo was selected (or why none). Enables impression→redemption funnel analysis.';

-- ── Read view ─────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "10_product_ops".v_promo_campaigns AS
SELECT
    c.id,
    c.slug,
    c.name,
    c.description,
    c.org_id,
    c.workspace_id,
    c.starts_at,
    c.ends_at,
    c.audience_rule,
    c.goals,
    c.is_active,
    (c.deleted_at IS NOT NULL) AS is_deleted,
    c.deleted_at,
    c.created_by,
    c.created_at,
    c.updated_at,
    -- Pre-aggregated stats
    (SELECT COUNT(*)::int FROM "10_product_ops"."40_lnk_campaign_promos" lcp
       WHERE lcp.campaign_id = c.id) AS promo_count,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_campaign_exposures" ce
       WHERE ce.campaign_id = c.id) AS exposure_count,
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_promo_redemptions" pr
       JOIN "10_product_ops"."40_lnk_campaign_promos" lcp ON lcp.promo_code_id = pr.promo_code_id
      WHERE lcp.campaign_id = c.id AND pr.outcome = 'redeemed') AS redemption_count,
    -- Computed status
    CASE
        WHEN c.deleted_at IS NOT NULL OR NOT c.is_active THEN 'inactive'
        WHEN c.starts_at IS NOT NULL AND c.starts_at > CURRENT_TIMESTAMP THEN 'scheduled'
        WHEN c.ends_at IS NOT NULL AND c.ends_at < CURRENT_TIMESTAMP THEN 'ended'
        ELSE 'active'
    END AS status
FROM "10_product_ops"."10_fct_promo_campaigns" c;

COMMENT ON VIEW "10_product_ops".v_promo_campaigns IS 'Campaign read view with pre-aggregated promo_count, exposure_count, redemption_count, and computed status.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_promo_campaigns;
DROP TABLE IF EXISTS "10_product_ops"."60_evt_campaign_exposures";
DROP TABLE IF EXISTS "10_product_ops"."40_lnk_campaign_promos";
DROP TABLE IF EXISTS "10_product_ops"."10_fct_promo_campaigns";
