-- ===========================================================================
-- Migration: Create feedback & support schema
-- Date: 2026-03-17
-- Description: User feedback/support ticket system. Reuses comments and
--   attachments systems via entity_type="feedback_ticket".
-- ===========================================================================

-- Schema created in 20260313_a_create-all-schemas.sql

-- ── Dimension: ticket types ─────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."01_dim_ticket_types" (
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    icon_name   VARCHAR(50),
    sort_order  INT          NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    CONSTRAINT pk_01_dim_ticket_types PRIMARY KEY (code)
);

INSERT INTO "10_feedback"."01_dim_ticket_types" (code, name, description, icon_name, sort_order)
VALUES
    ('bug_report',       'Bug Report',        'Something is broken or not working as expected',          'Bug',           10),
    ('feature_request',  'Feature Request',   'Suggest a new feature or improvement',                    'Lightbulb',     20),
    ('general_feedback', 'General Feedback',  'General comments, praise, or suggestions',                'MessageSquare', 30),
    ('service_issue',    'Service Issue',     'Degraded performance, outage, or reliability concern',    'AlertTriangle', 40),
    ('security_concern', 'Security Concern',  'Potential vulnerability or security-related observation', 'ShieldAlert',   50)
ON CONFLICT (code) DO NOTHING;

-- ── Dimension: ticket statuses ──────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."02_dim_ticket_statuses" (
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INT          NOT NULL DEFAULT 0,
    CONSTRAINT pk_02_dim_ticket_statuses PRIMARY KEY (code)
);

INSERT INTO "10_feedback"."02_dim_ticket_statuses" (code, name, description, is_terminal, sort_order)
VALUES
    ('open',        'Open',        'Newly submitted, awaiting triage',              FALSE, 10),
    ('in_review',   'In Review',   'Being triaged by support team',                 FALSE, 20),
    ('in_progress', 'In Progress', 'Actively being worked on',                      FALSE, 30),
    ('resolved',    'Resolved',    'Issue fixed or request fulfilled',               TRUE,  40),
    ('closed',      'Closed',      'Closed without further action',                 TRUE,  50),
    ('wont_fix',    'Won''t Fix',  'Acknowledged but will not be addressed',         TRUE,  60),
    ('duplicate',   'Duplicate',   'Same issue already tracked elsewhere',           TRUE,  70)
ON CONFLICT (code) DO NOTHING;

-- ── Dimension: ticket priorities ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."03_dim_ticket_priorities" (
    code          VARCHAR(50)  NOT NULL,
    name          VARCHAR(100) NOT NULL,
    description   TEXT,
    numeric_level INT          NOT NULL DEFAULT 0,
    sort_order    INT          NOT NULL DEFAULT 0,
    CONSTRAINT pk_03_dim_ticket_priorities PRIMARY KEY (code)
);

INSERT INTO "10_feedback"."03_dim_ticket_priorities" (code, name, description, numeric_level, sort_order)
VALUES
    ('low',      'Low',      'Minor inconvenience, no business impact',        0, 10),
    ('medium',   'Medium',   'Moderate impact, workaround exists',             1, 20),
    ('high',     'High',     'Significant impact, no easy workaround',         2, 30),
    ('critical', 'Critical', 'Platform unusable or security emergency',        3, 40)
ON CONFLICT (code) DO NOTHING;

-- ── Fact table: tickets (lean, structural fields only) ──────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."10_fct_tickets" (
    id               UUID        NOT NULL DEFAULT gen_random_uuid(),
    tenant_key       VARCHAR(100) NOT NULL,
    submitted_by     UUID        NOT NULL,
    ticket_type_code VARCHAR(50) NOT NULL
                         REFERENCES "10_feedback"."01_dim_ticket_types"(code),
    status_code      VARCHAR(50) NOT NULL DEFAULT 'open'
                         REFERENCES "10_feedback"."02_dim_ticket_statuses"(code),
    priority_code    VARCHAR(50) NOT NULL DEFAULT 'medium'
                         REFERENCES "10_feedback"."03_dim_ticket_priorities"(code),
    org_id           UUID        NULL,
    workspace_id     UUID        NULL,
    is_deleted       BOOLEAN     NOT NULL DEFAULT FALSE,
    deleted_at       TIMESTAMPTZ NULL,
    deleted_by       UUID        NULL,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by       UUID        NOT NULL,
    updated_by       UUID        NOT NULL,
    resolved_at      TIMESTAMPTZ NULL,
    resolved_by      UUID        NULL,
    CONSTRAINT pk_10_fct_tickets PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_10_fct_tickets_tenant
    ON "10_feedback"."10_fct_tickets" (tenant_key, created_at DESC)
    WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tickets_submitted_by
    ON "10_feedback"."10_fct_tickets" (submitted_by, created_at DESC)
    WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tickets_status
    ON "10_feedback"."10_fct_tickets" (status_code)
    WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tickets_priority
    ON "10_feedback"."10_fct_tickets" (priority_code)
    WHERE is_deleted = FALSE;

-- ── Detail / EAV table: ticket properties ───────────────────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."15_dtl_ticket_properties" (
    id             UUID        NOT NULL DEFAULT gen_random_uuid(),
    ticket_id      UUID        NOT NULL
                       REFERENCES "10_feedback"."10_fct_tickets"(id) ON DELETE CASCADE,
    property_key   VARCHAR(100) NOT NULL,
    property_value TEXT        NOT NULL,
    is_internal    BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by     UUID        NOT NULL,
    updated_by     UUID        NOT NULL,
    CONSTRAINT pk_15_dtl_ticket_properties PRIMARY KEY (id),
    CONSTRAINT uq_15_dtl_ticket_properties UNIQUE (ticket_id, property_key)
);

CREATE INDEX IF NOT EXISTS idx_15_dtl_ticket_properties_ticket
    ON "10_feedback"."15_dtl_ticket_properties" (ticket_id);

-- ── Link table: ticket assignments ──────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."20_lnk_ticket_assignments" (
    id            UUID        NOT NULL DEFAULT gen_random_uuid(),
    ticket_id     UUID        NOT NULL
                      REFERENCES "10_feedback"."10_fct_tickets"(id) ON DELETE CASCADE,
    assigned_to   UUID        NOT NULL,
    assigned_by   UUID        NOT NULL,
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    assigned_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unassigned_at TIMESTAMPTZ NULL,
    unassigned_by UUID        NULL,
    note          TEXT        NULL,
    CONSTRAINT pk_20_lnk_ticket_assignments PRIMARY KEY (id)
);

CREATE INDEX IF NOT EXISTS idx_20_lnk_ticket_assignments_ticket
    ON "10_feedback"."20_lnk_ticket_assignments" (ticket_id)
    WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_20_lnk_ticket_assignments_user
    ON "10_feedback"."20_lnk_ticket_assignments" (assigned_to)
    WHERE is_active = TRUE;

-- ── Audit table: ticket events ───────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS "10_feedback"."30_aud_ticket_events" (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    ticket_id   UUID        NOT NULL
                    REFERENCES "10_feedback"."10_fct_tickets"(id) ON DELETE CASCADE,
    tenant_key  VARCHAR(100) NOT NULL,
    event_type  VARCHAR(100) NOT NULL,
    actor_id    UUID        NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    old_value   TEXT        NULL,
    new_value   TEXT        NULL,
    note        TEXT        NULL,
    CONSTRAINT pk_30_aud_ticket_events PRIMARY KEY (id),
    CONSTRAINT ck_30_aud_ticket_events_event_type CHECK (event_type IN (
        'ticket_created', 'ticket_updated', 'ticket_deleted',
        'status_changed', 'priority_changed',
        'ticket_assigned', 'ticket_unassigned'
    ))
);

CREATE INDEX IF NOT EXISTS idx_30_aud_ticket_events_ticket
    ON "10_feedback"."30_aud_ticket_events" (ticket_id, occurred_at DESC);
CREATE INDEX IF NOT EXISTS idx_30_aud_ticket_events_tenant
    ON "10_feedback"."30_aud_ticket_events" (tenant_key, occurred_at DESC);
