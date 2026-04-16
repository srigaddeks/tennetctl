-- ─────────────────────────────────────────────────────────────────────────
-- UNIFIED AUDIT EVENT SYSTEM  (40, 41)
-- Single audit infrastructure for all domains: auth, access, product,
-- org, workspace. Designed for event-driven notifications.
-- ─────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "03_auth_manage"."40_aud_events" (
    id UUID NOT NULL,
    tenant_key VARCHAR(100) NOT NULL,
    entity_type VARCHAR(100) NOT NULL,
    entity_id UUID NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    event_category VARCHAR(50) NOT NULL,
    actor_id UUID NULL,
    actor_type VARCHAR(30) NULL,
    ip_address VARCHAR(64) NULL,
    session_id UUID NULL,
    occurred_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP NOT NULL,
    CONSTRAINT pk_40_aud_events PRIMARY KEY (id)
);

CREATE TABLE IF NOT EXISTS "03_auth_manage"."41_dtl_audit_event_properties" (
    id UUID NOT NULL,
    event_id UUID NOT NULL,
    meta_key VARCHAR(100) NOT NULL,
    meta_value TEXT NULL,
    CONSTRAINT pk_41_dtl_audit_event_properties PRIMARY KEY (id),
    CONSTRAINT fk_41_dtl_audit_event_properties_event FOREIGN KEY (event_id)
        REFERENCES "03_auth_manage"."40_aud_events" (id)
        ON DELETE CASCADE,
    CONSTRAINT uq_41_dtl_audit_event_properties_event_key UNIQUE (event_id, meta_key)
);

-- ─────────────────────────────────────────────────────────────────────────
-- VIEW: User profile from EAV properties
-- ─────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "03_auth_manage"."42_vw_auth_users" AS
SELECT
    u.id AS user_id,
    u.tenant_key AS tenant_key,
    email_prop.property_value AS email,
    username_prop.property_value AS username,
    COALESCE(email_verified_prop.property_value, 'false') AS email_verified,
    u.account_status AS account_status
FROM "03_auth_manage"."03_fct_users" AS u
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS email_prop
    ON email_prop.user_id = u.id AND email_prop.property_key = 'email'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS username_prop
    ON username_prop.user_id = u.id AND username_prop.property_key = 'username'
LEFT JOIN "03_auth_manage"."05_dtl_user_properties" AS email_verified_prop
    ON email_verified_prop.user_id = u.id AND email_verified_prop.property_key = 'email_verified'
WHERE u.is_deleted = FALSE
  AND u.is_test = FALSE;

-- ─────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_40_aud_events_entity_timeline
    ON "03_auth_manage"."40_aud_events" (entity_type, entity_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_40_aud_events_category_timeline
    ON "03_auth_manage"."40_aud_events" (tenant_key, event_category, occurred_at);

CREATE INDEX IF NOT EXISTS idx_40_aud_events_actor_timeline
    ON "03_auth_manage"."40_aud_events" (actor_id, occurred_at);

CREATE INDEX IF NOT EXISTS idx_41_dtl_audit_event_properties_event_id
    ON "03_auth_manage"."41_dtl_audit_event_properties" (event_id);

-- ─────────────────────────────────────────────────────────────────────────
-- COMMENTS
-- ─────────────────────────────────────────────────────────────────────────

COMMENT ON TABLE "03_auth_manage"."40_aud_events" IS 'Unified append-only audit event log for all domains. Designed for timeline queries and future notification triggers.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".id IS 'Application-assigned audit event identifier.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".tenant_key IS 'Tenant scope key.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".entity_type IS 'Logical entity type such as user, org, workspace, role, session.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".entity_id IS 'Primary key of the entity that changed.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".event_type IS 'Event type such as created, updated, deleted, login, password_reset.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".event_category IS 'Domain category: auth, access, product, org, workspace, system.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".actor_id IS 'User or system actor that caused the event.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".actor_type IS 'Actor type: user, system, api_key.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".ip_address IS 'Client IP associated with the event.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".session_id IS 'Auth session identifier when present.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".occurred_at IS 'Business event timestamp.';
COMMENT ON COLUMN "03_auth_manage"."40_aud_events".created_at IS 'Record creation timestamp.';

COMMENT ON TABLE "03_auth_manage"."41_dtl_audit_event_properties" IS 'EAV properties for audit events: flexible key-value metadata per event.';
COMMENT ON COLUMN "03_auth_manage"."41_dtl_audit_event_properties".id IS 'Application-assigned property identifier.';
COMMENT ON COLUMN "03_auth_manage"."41_dtl_audit_event_properties".event_id IS 'Parent audit event identifier.';
COMMENT ON COLUMN "03_auth_manage"."41_dtl_audit_event_properties".meta_key IS 'Property key such as previous_value, new_value, event_key, field_name.';
COMMENT ON COLUMN "03_auth_manage"."41_dtl_audit_event_properties".meta_value IS 'Property value as text.';

COMMENT ON VIEW "03_auth_manage"."42_vw_auth_users" IS 'Read view for the current user profile built from EAV user properties.';
