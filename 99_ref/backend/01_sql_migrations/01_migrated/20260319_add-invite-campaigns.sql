-- Migration: Invite Campaigns (bulk invite tagging / event sourcing)
--
-- An invite_campaign groups a set of invitations under a named event or source
-- (e.g. "AWS Summit 2026", "Website Signup Form", "Partner Referral Q1").
-- Each invitation can optionally be tagged to a campaign via campaign_id.
-- This provides first-class analytics: how many users came from which source.
--
-- Table numbering follows existing schema:
--   45_fct_invite_campaigns   — fact table for campaigns
--   column on 44_trx_invitations: campaign_id (nullable FK)

-- ── Campaign status dimension ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."45_fct_invite_campaigns" (
    id                  UUID            NOT NULL DEFAULT gen_random_uuid(),
    tenant_key          VARCHAR(100)    NOT NULL,
    code                VARCHAR(80)     NOT NULL,        -- slug e.g. "aws-summit-2026"
    name                VARCHAR(200)    NOT NULL,        -- display name
    description         TEXT            NOT NULL DEFAULT '',
    campaign_type       VARCHAR(50)     NOT NULL DEFAULT 'event',
                                                        -- event | referral | form | import | other
    status              VARCHAR(20)     NOT NULL DEFAULT 'active',
                                                        -- active | paused | closed | archived
    default_scope       VARCHAR(20)     NOT NULL DEFAULT 'platform',
                                                        -- platform | organization | workspace
    default_role        VARCHAR(50),                    -- pre-fill role on invite form
    default_org_id      UUID,
    default_workspace_id UUID,
    default_expires_hours INTEGER       NOT NULL DEFAULT 168, -- 7 days
    starts_at           TIMESTAMP,
    ends_at             TIMESTAMP,
    invite_count        INTEGER         NOT NULL DEFAULT 0,  -- denormalised, updated on batch insert
    accepted_count      INTEGER         NOT NULL DEFAULT 0,  -- updated on accept
    notes               TEXT,
    created_at          TIMESTAMP       NOT NULL,
    updated_at          TIMESTAMP       NOT NULL,
    created_by          UUID,
    updated_by          UUID,
    CONSTRAINT pk_45_fct_invite_campaigns PRIMARY KEY (id),
    CONSTRAINT uq_45_fct_invite_campaigns_tenant_code UNIQUE (tenant_key, code)
);

CREATE INDEX IF NOT EXISTS idx_45_fct_invite_campaigns_tenant_status
    ON "03_auth_manage"."45_fct_invite_campaigns" (tenant_key, status, created_at DESC);

-- ── Add campaign_id + source_tag to invitations ───────────────────────────────

ALTER TABLE "03_auth_manage"."44_trx_invitations"
    ADD COLUMN IF NOT EXISTS campaign_id UUID NULL
        REFERENCES "03_auth_manage"."45_fct_invite_campaigns"(id)
        ON DELETE SET NULL;

ALTER TABLE "03_auth_manage"."44_trx_invitations"
    ADD COLUMN IF NOT EXISTS source_tag VARCHAR(100) NULL;
        -- free-text tag for attribution even without a formal campaign
        -- e.g. "linkedin_post_march", "partner:acme"

CREATE INDEX IF NOT EXISTS idx_44_trx_invitations_campaign_id
    ON "03_auth_manage"."44_trx_invitations" (campaign_id)
    WHERE campaign_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_44_trx_invitations_source_tag
    ON "03_auth_manage"."44_trx_invitations" (source_tag)
    WHERE source_tag IS NOT NULL;
