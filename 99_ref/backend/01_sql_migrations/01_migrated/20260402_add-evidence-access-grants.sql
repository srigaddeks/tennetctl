-- Explicit evidence access grants for auditor workflow
-- Stores attachment-level grants separately from request workflow state.

CREATE TABLE IF NOT EXISTS "12_engagements"."13_lnk_evidence_access_grants" (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_key       TEXT NOT NULL,
    engagement_id    UUID NOT NULL
                         REFERENCES "12_engagements"."10_fct_audit_engagements"(id),
    request_id       UUID NULL
                         REFERENCES "12_engagements"."20_trx_auditor_requests"(id),
    membership_id    UUID NOT NULL
                         REFERENCES "12_engagements"."12_lnk_engagement_memberships"(id),
    attachment_id    UUID NOT NULL
                         REFERENCES "09_attachments"."01_fct_attachments"(id),
    granted_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at       TIMESTAMPTZ NULL,
    revoked_at       TIMESTAMPTZ NULL,
    revoked_by       UUID NULL,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted       BOOLEAN NOT NULL DEFAULT FALSE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by       UUID NULL,
    updated_by       UUID NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_13_lnk_evidence_access_grants_active_membership_attachment
    ON "12_engagements"."13_lnk_evidence_access_grants" (engagement_id, membership_id, attachment_id)
    WHERE revoked_at IS NULL
      AND is_active = TRUE
      AND is_deleted = FALSE;

CREATE INDEX IF NOT EXISTS idx_13_lnk_evidence_access_grants_membership
    ON "12_engagements"."13_lnk_evidence_access_grants" (membership_id, engagement_id, attachment_id)
    WHERE revoked_at IS NULL
      AND is_active = TRUE
      AND is_deleted = FALSE;
