-- UP ====

-- product_ops.referrals — referral code → referrer + reward config + conversions.
--
-- Each code is owned by an IAM user (the "referrer"). When a visitor lands
-- with the code (e.g. ?ref=alice123), we attach the referrer to the visitor
-- AND fire a synthetic touch row carrying utm_source='referral' &
-- utm_campaign={code} so referral conversions show up in standard UTM funnels
-- without special-case UI.

CREATE TABLE "10_product_ops"."10_fct_referral_codes" (
    id              VARCHAR(36) NOT NULL,
    code            TEXT NOT NULL,
    referrer_user_id VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    -- Reward config is JSONB to avoid premature schema commitment;
    -- examples: {"kind": "credit", "amount_cents": 1000} or {"kind": "discount_pct", "value": 20}
    reward_config   JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_referral_codes PRIMARY KEY (id),
    CONSTRAINT uq_fct_referral_codes_workspace_code UNIQUE (workspace_id, code)
);

CREATE INDEX idx_fct_referral_codes_referrer
    ON "10_product_ops"."10_fct_referral_codes" (referrer_user_id);

COMMENT ON TABLE  "10_product_ops"."10_fct_referral_codes" IS 'Referral codes. UNIQUE per workspace. Reward shape is intentionally JSONB — actual payout/credit logic is operator-specific and lives in the consumer app.';
COMMENT ON COLUMN "10_product_ops"."10_fct_referral_codes".reward_config IS 'JSONB. Schema is intentionally open: caller-defined reward shape ({"kind","amount_cents"} or {"kind","value"}, etc.).';

-- Conversion event log: each row = one resolved referral (signup, purchase, etc.)
CREATE TABLE "10_product_ops"."60_evt_referral_conversions" (
    id              VARCHAR(36) NOT NULL,
    referral_code_id VARCHAR(36) NOT NULL,
    visitor_id      VARCHAR(36) NOT NULL,
    converted_user_id VARCHAR(36),
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    conversion_kind TEXT NOT NULL,           -- 'signup' | 'purchase' | caller-defined
    conversion_value_cents BIGINT,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMP NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_referral_conversions PRIMARY KEY (id),
    CONSTRAINT fk_evt_referral_conversions_code
        FOREIGN KEY (referral_code_id)
        REFERENCES "10_product_ops"."10_fct_referral_codes"(id)
);

CREATE INDEX idx_evt_referral_conversions_code_occurred
    ON "10_product_ops"."60_evt_referral_conversions" (referral_code_id, occurred_at DESC);
CREATE INDEX idx_evt_referral_conversions_visitor
    ON "10_product_ops"."60_evt_referral_conversions" (visitor_id);

COMMENT ON TABLE "10_product_ops"."60_evt_referral_conversions" IS 'Append-only referral conversion log. NO updated_at, NO deleted_at (evt convention). One row per conversion event.';

-- Read view exposing referrer code as TEXT
CREATE OR REPLACE VIEW "10_product_ops".v_referral_codes AS
SELECT
    rc.id,
    rc.code,
    rc.referrer_user_id,
    rc.org_id,
    rc.workspace_id,
    rc.reward_config,
    rc.is_active,
    (rc.deleted_at IS NOT NULL) AS is_deleted,
    rc.deleted_at,
    rc.created_by,
    rc.created_at,
    rc.updated_at,
    -- Conversion stats
    (SELECT COUNT(*)::int FROM "10_product_ops"."60_evt_referral_conversions" c
       WHERE c.referral_code_id = rc.id) AS conversion_count,
    (SELECT COALESCE(SUM(conversion_value_cents), 0)::bigint
       FROM "10_product_ops"."60_evt_referral_conversions" c
      WHERE c.referral_code_id = rc.id) AS conversion_value_cents_total
FROM "10_product_ops"."10_fct_referral_codes" rc;

COMMENT ON VIEW "10_product_ops".v_referral_codes IS 'Read view. Includes pre-aggregated conversion_count + conversion_value_cents_total per code.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_referral_codes;
DROP TABLE IF EXISTS "10_product_ops"."60_evt_referral_conversions";
DROP TABLE IF EXISTS "10_product_ops"."10_fct_referral_codes";
