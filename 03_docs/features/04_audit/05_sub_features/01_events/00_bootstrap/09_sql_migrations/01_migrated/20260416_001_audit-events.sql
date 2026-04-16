-- UP ====

-- Audit schema + evt_audit table.
-- Owned by the iam.events sub-feature — schema creation lives here because
-- audit has only one sub-feature, no need for a separate feature-level bootstrap.
--
-- Audit scope rule (from project memory): every audit event must carry
-- user_id + session_id + org_id + workspace_id, with two bypasses:
--   - audit_category='setup' (pre-user-exists events)
--   - outcome='failure' (scope often unavailable at failure time)
-- Enforced by DB CHECK chk_evt_audit_scope so no code path can bypass.

CREATE SCHEMA IF NOT EXISTS "04_audit";
COMMENT ON SCHEMA "04_audit" IS 'Audit event pipeline. Append-only evt_* table; every effect node emits here via run_node("audit.emit", ...).';

CREATE TABLE "04_audit"."60_evt_audit" (
    id                  VARCHAR(36) NOT NULL,
    event_key           TEXT NOT NULL,
    actor_user_id       VARCHAR(36),
    actor_session_id    VARCHAR(36),
    org_id              VARCHAR(36),
    workspace_id        VARCHAR(36),
    trace_id            VARCHAR(36) NOT NULL,
    span_id             VARCHAR(36) NOT NULL,
    parent_span_id      VARCHAR(36),
    audit_category      TEXT NOT NULL,
    outcome             TEXT NOT NULL,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_evt_audit PRIMARY KEY (id),
    CONSTRAINT chk_evt_audit_category CHECK (audit_category IN ('system','user','integration','setup')),
    CONSTRAINT chk_evt_audit_outcome  CHECK (outcome IN ('success','failure')),
    CONSTRAINT chk_evt_audit_scope    CHECK (
        audit_category = 'setup'
     OR outcome = 'failure'
     OR (actor_user_id IS NOT NULL
         AND actor_session_id IS NOT NULL
         AND org_id IS NOT NULL
         AND workspace_id IS NOT NULL)
    )
);

CREATE INDEX idx_evt_audit_org_created        ON "04_audit"."60_evt_audit" (org_id, created_at DESC);
CREATE INDEX idx_evt_audit_actor_user_created ON "04_audit"."60_evt_audit" (actor_user_id, created_at DESC);
CREATE INDEX idx_evt_audit_event_key          ON "04_audit"."60_evt_audit" (event_key);
CREATE INDEX idx_evt_audit_trace_id           ON "04_audit"."60_evt_audit" (trace_id);
CREATE INDEX idx_evt_audit_created_at         ON "04_audit"."60_evt_audit" (created_at DESC);

COMMENT ON TABLE  "04_audit"."60_evt_audit" IS 'Audit events. Append-only. Every effect node emits here; chk_evt_audit_scope enforces that non-setup / non-failure events carry full audit scope (user/session/org/workspace).';
COMMENT ON COLUMN "04_audit"."60_evt_audit".id IS 'UUID v7 of this audit event.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".event_key IS 'Stable event key, e.g. "iam.orgs.created", "iam.users.logged_in".';
COMMENT ON COLUMN "04_audit"."60_evt_audit".actor_user_id IS 'User UUID from NodeContext. Nullable ONLY for setup or failure events.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".actor_session_id IS 'Session UUID from NodeContext. Nullable ONLY for setup or failure events.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".org_id IS 'Org UUID from NodeContext. Nullable ONLY for setup or failure events.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".workspace_id IS 'Workspace UUID from NodeContext. Nullable ONLY for setup or failure events.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".trace_id IS 'Distributed trace ID from NodeContext. Always required.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".span_id IS 'This emit''s own span_id (from child_ctx inside run_node).';
COMMENT ON COLUMN "04_audit"."60_evt_audit".parent_span_id IS 'Caller''s span_id (child_ctx.parent_span_id).';
COMMENT ON COLUMN "04_audit"."60_evt_audit".audit_category IS 'system | user | integration | setup. setup bypasses scope CHECK.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".outcome IS 'success | failure. failure bypasses scope CHECK.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".metadata IS 'Free-form event payload (caller-supplied). JSONB.';
COMMENT ON COLUMN "04_audit"."60_evt_audit".created_at IS 'Insert timestamp. Table is append-only — no updated_at, no deleted_at.';

-- DOWN ====

DROP TABLE IF EXISTS "04_audit"."60_evt_audit";
DROP SCHEMA IF EXISTS "04_audit";
