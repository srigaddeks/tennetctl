-- ─────────────────────────────────────────────────────────────────────────────
-- 08_TASKS SCHEMA
-- Polymorphic Task Management with Dependencies and Event Log
--
-- Scoping: Workspace-level (org_id + workspace_id both required)
--   - All tasks live inside a workspace
--   - Users access tasks through workspace membership
--
-- Pattern: lean fact + EAV (no property_keys dimension — unconstrained keys)
--   - 02-04 dim_*: task types, priorities, statuses
--   - 10    fct_*: LEAN structural only + polymorphic entity linking
--   - 20    dtl_*: ALL descriptive data (title, description, resolution notes)
--   - 30    trx_*: immutable event log (status changes, comments, reassignments)
--   - 31-32 lnk_*: co-assignees and task dependencies
--   - 40    vw_*:  reassembled task with EAV for API
--
-- Polymorphic linking: (entity_type, entity_id) — no cross-schema FK
--   - Intentional loose coupling allows tasks to link to any entity
--   - entity_type values: 'control_instance', 'risk', 'evidence_item', etc.
--
-- Audit: ALL lifecycle events go to 03_auth_manage.40_aud_events
-- Domain trx tables: task events (status changes, comments, reassignments)
-- ─────────────────────────────────────────────────────────────────────────────

-- Schema created in 20260313_a_create-all-schemas.sql

-- ─────────────────────────────────────────────────────────────────────────────
-- DIMENSION TABLES (02-04)
-- ─────────────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "08_tasks"."02_dim_task_types" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_02_dim_task_types      PRIMARY KEY (id),
    CONSTRAINT uq_02_dim_task_types_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "08_tasks"."03_dim_task_priorities" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_03_dim_task_priorities      PRIMARY KEY (id),
    CONSTRAINT uq_03_dim_task_priorities_code UNIQUE (code)
);

CREATE TABLE IF NOT EXISTS "08_tasks"."04_dim_task_statuses" (
    id          UUID         NOT NULL,
    code        VARCHAR(50)  NOT NULL,
    name        VARCHAR(100) NOT NULL,
    description TEXT         NOT NULL,
    is_terminal BOOLEAN      NOT NULL DEFAULT FALSE,
    sort_order  INTEGER      NOT NULL DEFAULT 0,
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL,
    updated_at  TIMESTAMP    NOT NULL,
    CONSTRAINT pk_04_dim_task_statuses      PRIMARY KEY (id),
    CONSTRAINT uq_04_dim_task_statuses_code UNIQUE (code)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- FACT TABLE (10) — LEAN: structural + polymorphic entity linking
-- ─────────────────────────────────────────────────────────────────────────────

-- 10_fct_tasks — workspace-scoped polymorphic tasks
-- title, description, acceptance_criteria, resolution_notes → 20_dtl_task_properties
CREATE TABLE IF NOT EXISTS "08_tasks"."10_fct_tasks" (
    id                 UUID         NOT NULL,
    tenant_key         VARCHAR(100) NOT NULL,
    org_id             UUID         NOT NULL,
    workspace_id       UUID         NOT NULL,
    task_type_code     VARCHAR(50)  NOT NULL,
    priority_code      VARCHAR(50)  NOT NULL DEFAULT 'medium',
    status_code        VARCHAR(50)  NOT NULL DEFAULT 'open',
    -- Polymorphic entity linking (no cross-schema FK — intentional loose coupling)
    entity_type        VARCHAR(50)  NULL,
    entity_id          UUID         NULL,
    -- Assignment
    assignee_user_id   UUID         NULL,
    reporter_user_id   UUID         NOT NULL,
    -- Dates
    due_date           TIMESTAMP    NULL,
    completed_at       TIMESTAMP    NULL,
    -- Standard flags
    is_active          BOOLEAN      NOT NULL DEFAULT TRUE,
    is_disabled        BOOLEAN      NOT NULL DEFAULT FALSE,
    is_deleted         BOOLEAN      NOT NULL DEFAULT FALSE,
    is_test            BOOLEAN      NOT NULL DEFAULT FALSE,
    is_system          BOOLEAN      NOT NULL DEFAULT FALSE,
    is_locked          BOOLEAN      NOT NULL DEFAULT FALSE,
    created_at         TIMESTAMP    NOT NULL,
    updated_at         TIMESTAMP    NOT NULL,
    created_by         UUID         NULL,
    updated_by         UUID         NULL,
    deleted_at         TIMESTAMP    NULL,
    deleted_by         UUID         NULL,
    CONSTRAINT pk_10_fct_tasks                  PRIMARY KEY (id),
    CONSTRAINT fk_10_fct_tasks_type             FOREIGN KEY (task_type_code)
        REFERENCES "08_tasks"."02_dim_task_types" (code),
    CONSTRAINT fk_10_fct_tasks_priority         FOREIGN KEY (priority_code)
        REFERENCES "08_tasks"."03_dim_task_priorities" (code),
    CONSTRAINT fk_10_fct_tasks_status           FOREIGN KEY (status_code)
        REFERENCES "08_tasks"."04_dim_task_statuses" (code),
    CONSTRAINT fk_10_fct_tasks_org              FOREIGN KEY (org_id)
        REFERENCES "03_auth_manage"."29_fct_orgs" (id),
    CONSTRAINT fk_10_fct_tasks_workspace        FOREIGN KEY (workspace_id)
        REFERENCES "03_auth_manage"."34_fct_workspaces" (id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- DETAIL / EAV TABLE (20)
-- ─────────────────────────────────────────────────────────────────────────────

-- Task properties: title, description, acceptance_criteria, resolution_notes,
--   resolution_evidence_id
CREATE TABLE IF NOT EXISTS "08_tasks"."20_dtl_task_properties" (
    id             UUID         NOT NULL,
    task_id        UUID         NOT NULL,
    property_key   VARCHAR(80)  NOT NULL,
    property_value TEXT         NOT NULL,
    created_at     TIMESTAMP    NOT NULL,
    updated_at     TIMESTAMP    NOT NULL,
    created_by     UUID         NULL,
    updated_by     UUID         NULL,
    CONSTRAINT pk_20_dtl_task_props        PRIMARY KEY (id),
    CONSTRAINT uq_20_dtl_task_props_key    UNIQUE (task_id, property_key),
    CONSTRAINT fk_20_dtl_task_props_task   FOREIGN KEY (task_id)
        REFERENCES "08_tasks"."10_fct_tasks" (id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- TRANSACTION TABLE (30) — Immutable event log
-- ─────────────────────────────────────────────────────────────────────────────

-- Task events: status changes, comments, reassignments, priority changes, etc.
CREATE TABLE IF NOT EXISTS "08_tasks"."30_trx_task_events" (
    id          UUID         NOT NULL,
    task_id     UUID         NOT NULL,
    event_type  VARCHAR(50)  NOT NULL,
    old_value   TEXT         NULL,
    new_value   TEXT         NULL,
    comment     TEXT         NULL,
    actor_id    UUID         NOT NULL,
    occurred_at TIMESTAMP    NOT NULL,
    CONSTRAINT pk_30_trx_task_events            PRIMARY KEY (id),
    CONSTRAINT ck_30_trx_task_events_type       CHECK (event_type IN (
        'created','status_changed','reassigned','priority_changed',
        'due_date_changed','comment_added','dependency_added',
        'dependency_removed','co_assignee_added','co_assignee_removed'
    )),
    CONSTRAINT fk_30_trx_task_events_task       FOREIGN KEY (task_id)
        REFERENCES "08_tasks"."10_fct_tasks" (id)
);

-- ─────────────────────────────────────────────────────────────────────────────
-- LINK TABLES (31-32)
-- ─────────────────────────────────────────────────────────────────────────────

-- Co-assignees: additional users assigned to a task beyond the primary assignee
CREATE TABLE IF NOT EXISTS "08_tasks"."31_lnk_task_assignments" (
    id          UUID         NOT NULL,
    task_id     UUID         NOT NULL,
    user_id     UUID         NOT NULL,
    role        VARCHAR(50)  NOT NULL DEFAULT 'co_assignee',
    assigned_at TIMESTAMP    NOT NULL,
    assigned_by UUID         NULL,
    CONSTRAINT pk_31_lnk_task_assignments           PRIMARY KEY (id),
    CONSTRAINT uq_31_lnk_task_assignments           UNIQUE (task_id, user_id),
    CONSTRAINT ck_31_lnk_task_assignments_role      CHECK (role IN ('co_assignee','reviewer','observer')),
    CONSTRAINT fk_31_lnk_task_assignments_task      FOREIGN KEY (task_id)
        REFERENCES "08_tasks"."10_fct_tasks" (id) ON DELETE CASCADE
);

-- Task dependencies: blocking relationships between tasks
-- blocking_task_id must be resolved before blocked_task_id can be resolved
CREATE TABLE IF NOT EXISTS "08_tasks"."32_lnk_task_dependencies" (
    id               UUID         NOT NULL,
    blocking_task_id UUID         NOT NULL,
    blocked_task_id  UUID         NOT NULL,
    created_at       TIMESTAMP    NOT NULL,
    created_by       UUID         NULL,
    CONSTRAINT pk_32_lnk_task_dependencies              PRIMARY KEY (id),
    CONSTRAINT uq_32_lnk_task_dependencies              UNIQUE (blocking_task_id, blocked_task_id),
    CONSTRAINT ck_32_lnk_task_deps_no_self              CHECK (blocking_task_id != blocked_task_id),
    CONSTRAINT fk_32_lnk_task_deps_blocking             FOREIGN KEY (blocking_task_id)
        REFERENCES "08_tasks"."10_fct_tasks" (id) ON DELETE CASCADE,
    CONSTRAINT fk_32_lnk_task_deps_blocked              FOREIGN KEY (blocked_task_id)
        REFERENCES "08_tasks"."10_fct_tasks" (id) ON DELETE CASCADE
);

-- ─────────────────────────────────────────────────────────────────────────────
-- VIEW (40) — Reassemble task + EAV for API consumption
-- ─────────────────────────────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "08_tasks"."40_vw_task_detail" AS
SELECT
    t.id,
    t.tenant_key,
    t.org_id,
    t.workspace_id,
    t.task_type_code,
    tt.name                 AS task_type_name,
    t.priority_code,
    tp.name                 AS priority_name,
    t.status_code,
    ts.name                 AS status_name,
    ts.is_terminal,
    t.entity_type,
    t.entity_id,
    t.assignee_user_id,
    t.reporter_user_id,
    t.due_date,
    t.completed_at,
    t.is_active,
    t.is_deleted,
    t.created_at,
    t.updated_at,
    -- EAV flattened
    p_title.property_value   AS title,
    p_desc.property_value    AS description,
    p_accept.property_value  AS acceptance_criteria,
    p_resolve.property_value AS resolution_notes,
    -- Counts
    (SELECT COUNT(*)
     FROM "08_tasks"."31_lnk_task_assignments" a
     WHERE a.task_id = t.id)                                    AS co_assignee_count,
    (SELECT COUNT(*)
     FROM "08_tasks"."32_lnk_task_dependencies" d
     WHERE d.blocked_task_id = t.id)                            AS blocker_count,
    (SELECT COUNT(*)
     FROM "08_tasks"."30_trx_task_events" e
     WHERE e.task_id = t.id AND e.event_type = 'comment_added') AS comment_count
FROM "08_tasks"."10_fct_tasks" t
LEFT JOIN "08_tasks"."02_dim_task_types" tt
    ON tt.code = t.task_type_code
LEFT JOIN "08_tasks"."03_dim_task_priorities" tp
    ON tp.code = t.priority_code
LEFT JOIN "08_tasks"."04_dim_task_statuses" ts
    ON ts.code = t.status_code
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_title
    ON p_title.task_id = t.id AND p_title.property_key = 'title'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_desc
    ON p_desc.task_id = t.id AND p_desc.property_key = 'description'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_accept
    ON p_accept.task_id = t.id AND p_accept.property_key = 'acceptance_criteria'
LEFT JOIN "08_tasks"."20_dtl_task_properties" p_resolve
    ON p_resolve.task_id = t.id AND p_resolve.property_key = 'resolution_notes'
WHERE t.is_deleted = FALSE;

-- ─────────────────────────────────────────────────────────────────────────────
-- INDEXES
-- ─────────────────────────────────────────────────────────────────────────────

-- Fact: tasks
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_tenant
    ON "08_tasks"."10_fct_tasks" (tenant_key) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_org
    ON "08_tasks"."10_fct_tasks" (org_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_workspace
    ON "08_tasks"."10_fct_tasks" (workspace_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_assignee
    ON "08_tasks"."10_fct_tasks" (assignee_user_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_status
    ON "08_tasks"."10_fct_tasks" (status_code) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_entity
    ON "08_tasks"."10_fct_tasks" (entity_type, entity_id) WHERE is_deleted = FALSE;
CREATE INDEX IF NOT EXISTS idx_10_fct_tasks_due
    ON "08_tasks"."10_fct_tasks" (due_date) WHERE is_deleted = FALSE AND due_date IS NOT NULL;

-- Detail: EAV
CREATE INDEX IF NOT EXISTS idx_20_dtl_task_props_key
    ON "08_tasks"."20_dtl_task_properties" (task_id, property_key);

-- Transaction: events
CREATE INDEX IF NOT EXISTS idx_30_trx_task_events_task
    ON "08_tasks"."30_trx_task_events" (task_id, occurred_at DESC);

-- Link: assignments
CREATE INDEX IF NOT EXISTS idx_31_lnk_assignments_task
    ON "08_tasks"."31_lnk_task_assignments" (task_id);
CREATE INDEX IF NOT EXISTS idx_31_lnk_assignments_user
    ON "08_tasks"."31_lnk_task_assignments" (user_id);

-- Link: dependencies
CREATE INDEX IF NOT EXISTS idx_32_lnk_deps_blocking
    ON "08_tasks"."32_lnk_task_dependencies" (blocking_task_id);
CREATE INDEX IF NOT EXISTS idx_32_lnk_deps_blocked
    ON "08_tasks"."32_lnk_task_dependencies" (blocked_task_id);

-- ─────────────────────────────────────────────────────────────────────────────
-- SEED DATA — Dimension tables
-- ─────────────────────────────────────────────────────────────────────────────

-- Task types
INSERT INTO "08_tasks"."02_dim_task_types" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('b1c10001-0000-0000-0000-000000000000', 'evidence_collection',  'Evidence Collection',  'Collect evidence for a control test',    1, TRUE, NOW(), NOW()),
    ('b1c10002-0000-0000-0000-000000000000', 'control_remediation',  'Control Remediation',  'Fix a failing or non-compliant control', 2, TRUE, NOW(), NOW()),
    ('b1c10003-0000-0000-0000-000000000000', 'risk_mitigation',      'Risk Mitigation',      'Execute a risk treatment action',         3, TRUE, NOW(), NOW()),
    ('b1c10004-0000-0000-0000-000000000000', 'general',              'General',              'General compliance or operational task',  4, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Task priorities
INSERT INTO "08_tasks"."03_dim_task_priorities" (id, code, name, description, sort_order, is_active, created_at, updated_at)
VALUES
    ('b2c20001-0000-0000-0000-000000000000', 'critical', 'Critical', 'Must be completed immediately',   1, TRUE, NOW(), NOW()),
    ('b2c20002-0000-0000-0000-000000000000', 'high',     'High',     'Complete within 3 business days', 2, TRUE, NOW(), NOW()),
    ('b2c20003-0000-0000-0000-000000000000', 'medium',   'Medium',   'Complete within 2 weeks',          3, TRUE, NOW(), NOW()),
    ('b2c20004-0000-0000-0000-000000000000', 'low',      'Low',      'Complete at next opportunity',     4, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Task statuses
INSERT INTO "08_tasks"."04_dim_task_statuses" (id, code, name, description, is_terminal, sort_order, is_active, created_at, updated_at)
VALUES
    ('b3c30001-0000-0000-0000-000000000000', 'open',                  'Open',                  'Task created, not yet started',           FALSE, 1, TRUE, NOW(), NOW()),
    ('b3c30002-0000-0000-0000-000000000000', 'in_progress',           'In Progress',           'Actively being worked on',                 FALSE, 2, TRUE, NOW(), NOW()),
    ('b3c30003-0000-0000-0000-000000000000', 'pending_verification',  'Pending Verification',  'Work done, awaiting review/verification', FALSE, 3, TRUE, NOW(), NOW()),
    ('b3c30004-0000-0000-0000-000000000000', 'resolved',              'Resolved',              'Task completed and verified',              TRUE,  4, TRUE, NOW(), NOW()),
    ('b3c30005-0000-0000-0000-000000000000', 'cancelled',             'Cancelled',             'Task cancelled — no longer needed',        TRUE,  5, TRUE, NOW(), NOW()),
    ('b3c30006-0000-0000-0000-000000000000', 'overdue',               'Overdue',               'Past due date — system-managed',           FALSE, 6, TRUE, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
