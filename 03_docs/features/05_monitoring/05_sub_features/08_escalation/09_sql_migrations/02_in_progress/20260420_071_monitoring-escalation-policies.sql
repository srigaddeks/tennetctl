-- UP ====
-- Escalation policies + step definitions + escalation state tracking.

-- ── Escalation step kind dimension ──────────────────────────────────────
-- Seeded values: notify_user(1), notify_group(2), notify_oncall(3), wait(4), repeat(5)

CREATE TABLE IF NOT EXISTS "05_monitoring"."02_dim_escalation_step_kind" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_escalation_step_kind PRIMARY KEY (id),
    CONSTRAINT uq_dim_escalation_step_kind_code UNIQUE (code)
);
COMMENT ON TABLE  "05_monitoring"."02_dim_escalation_step_kind" IS 'Escalation step types: notify_user, notify_group, notify_oncall, wait, repeat.';
COMMENT ON COLUMN "05_monitoring"."02_dim_escalation_step_kind".id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "05_monitoring"."02_dim_escalation_step_kind".code IS 'Step kind code (notify_user | notify_group | notify_oncall | wait | repeat).';
COMMENT ON COLUMN "05_monitoring"."02_dim_escalation_step_kind".label IS 'Human-readable label.';
COMMENT ON COLUMN "05_monitoring"."02_dim_escalation_step_kind".description IS 'Behavior description.';
COMMENT ON COLUMN "05_monitoring"."02_dim_escalation_step_kind".deprecated_at IS 'Non-null when kind is deprecated.';

-- ── Escalation policies ─────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS "05_monitoring"."10_fct_monitoring_escalation_policies" (
    id              VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_by      VARCHAR(36) NOT NULL,
    updated_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at      TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_escalation_policies PRIMARY KEY (id),
    CONSTRAINT uq_fct_monitoring_escalation_policies_org_name UNIQUE (org_id, name) DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT fk_fct_monitoring_escalation_policies_created_by FOREIGN KEY (created_by) REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_fct_monitoring_escalation_policies_updated_by FOREIGN KEY (updated_by) REFERENCES "03_iam"."12_fct_users"(id)
);
COMMENT ON TABLE  "05_monitoring"."10_fct_monitoring_escalation_policies" IS 'Escalation policy: named ordered list of steps. Referenced by alert rules to define progressive paging.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_escalation_policies".id IS 'UUID v7.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_escalation_policies".org_id IS 'Organization owner.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_escalation_policies".name IS 'User-friendly policy name (e.g. "On-Call → Lead → Manager").';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_escalation_policies".description IS 'Optional free-text description.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_escalation_policies".is_active IS 'Soft toggle. Only active policies are used by evaluator.';
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_escalation_policies".deleted_at IS 'Soft delete timestamp. Rows with deleted_at IS NOT NULL are excluded from reads.';

CREATE INDEX idx_fct_monitoring_escalation_policies_org_id ON "05_monitoring"."10_fct_monitoring_escalation_policies" (org_id);
CREATE INDEX idx_fct_monitoring_escalation_policies_deleted_at ON "05_monitoring"."10_fct_monitoring_escalation_policies" (deleted_at);

-- ── Escalation policy steps (immutable link) ────────────────────────────

CREATE TABLE IF NOT EXISTS "05_monitoring"."40_lnk_monitoring_escalation_steps" (
    policy_id       VARCHAR(36) NOT NULL,
    step_order      SMALLINT NOT NULL,
    kind_id         SMALLINT NOT NULL,
    target_ref      JSONB NOT NULL DEFAULT '{}'::jsonb,
    wait_seconds    INT,
    priority        SMALLINT NOT NULL DEFAULT 2,
    created_by      VARCHAR(36) NOT NULL,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_lnk_monitoring_escalation_steps PRIMARY KEY (policy_id, step_order),
    CONSTRAINT fk_lnk_monitoring_escalation_steps_policy FOREIGN KEY (policy_id) REFERENCES "05_monitoring"."10_fct_monitoring_escalation_policies"(id) ON DELETE CASCADE,
    CONSTRAINT fk_lnk_monitoring_escalation_steps_kind FOREIGN KEY (kind_id) REFERENCES "05_monitoring"."02_dim_escalation_step_kind"(id),
    CONSTRAINT fk_lnk_monitoring_escalation_steps_created_by FOREIGN KEY (created_by) REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT chk_lnk_monitoring_escalation_steps_priority CHECK (priority >= 1 AND priority <= 4)
);
COMMENT ON TABLE  "05_monitoring"."40_lnk_monitoring_escalation_steps" IS 'Immutable link: policy steps in order. Each row is PK(policy_id, step_order). When updating a policy, old rows are replaced with new ones — never partial mutation.';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_escalation_steps".kind_id IS 'FK to dim_escalation_step_kind (1=notify_user, 2=notify_group, 3=notify_oncall, 4=wait, 5=repeat).';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_escalation_steps".target_ref IS 'JSONB: {user_id?, group_id?, schedule_id?} depending on kind. Null/empty for wait/repeat.';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_escalation_steps".wait_seconds IS 'Seconds to wait before advancing to next step. Non-null only for kind=wait.';
COMMENT ON COLUMN "05_monitoring"."40_lnk_monitoring_escalation_steps".priority IS 'Notification priority (1=low, 2=normal, 3=high, 4=critical) for notify_* kinds. Controls channel routing in Notify.';

CREATE INDEX idx_lnk_monitoring_escalation_steps_policy ON "05_monitoring"."40_lnk_monitoring_escalation_steps" (policy_id);
CREATE INDEX idx_lnk_monitoring_escalation_steps_kind ON "05_monitoring"."40_lnk_monitoring_escalation_steps" (kind_id);

-- ── Escalation state tracking per alert event ───────────────────────────

CREATE TABLE IF NOT EXISTS "05_monitoring"."20_dtl_monitoring_alert_escalation_state" (
    alert_event_id   VARCHAR(36) NOT NULL,
    policy_id        VARCHAR(36) NOT NULL,
    current_step     SMALLINT NOT NULL DEFAULT 0,
    next_action_at   TIMESTAMP NOT NULL,
    ack_user_id      VARCHAR(36),
    ack_at           TIMESTAMP,
    exhausted_at     TIMESTAMP,
    CONSTRAINT pk_dtl_monitoring_alert_escalation_state PRIMARY KEY (alert_event_id),
    CONSTRAINT fk_dtl_monitoring_alert_escalation_state_alert_event FOREIGN KEY (alert_event_id) REFERENCES "05_monitoring"."60_evt_monitoring_alert_events"(id),
    CONSTRAINT fk_dtl_monitoring_alert_escalation_state_policy FOREIGN KEY (policy_id) REFERENCES "05_monitoring"."10_fct_monitoring_escalation_policies"(id),
    CONSTRAINT fk_dtl_monitoring_alert_escalation_state_ack_user FOREIGN KEY (ack_user_id) REFERENCES "03_iam"."12_fct_users"(id)
);
COMMENT ON TABLE  "05_monitoring"."20_dtl_monitoring_alert_escalation_state" IS 'Escalation state per firing alert. Tracks current step, when next action is due, and ack/exhaustion status.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".alert_event_id IS 'FK to alert event. PK since one escalation per alert.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".policy_id IS 'FK to escalation policy used.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".current_step IS 'Zero-based index of next step to execute.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".next_action_at IS 'When the worker should next process this alert. Used for efficient polling.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".ack_user_id IS 'User who acknowledged the alert. Non-null acks short-circuit escalation.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".ack_at IS 'Timestamp when alert was acknowledged. Worker skips processing once set.';
COMMENT ON COLUMN "05_monitoring"."20_dtl_monitoring_alert_escalation_state".exhausted_at IS 'Timestamp when escalation completed (no more steps). Worker skips processing once set.';

CREATE INDEX idx_dtl_monitoring_alert_escalation_state_next_action ON "05_monitoring"."20_dtl_monitoring_alert_escalation_state" (next_action_at) WHERE ack_at IS NULL AND exhausted_at IS NULL;
CREATE INDEX idx_dtl_monitoring_alert_escalation_state_policy ON "05_monitoring"."20_dtl_monitoring_alert_escalation_state" (policy_id);

-- ── Add escalation_policy_id FK to alert rules ──────────────────────────

ALTER TABLE "05_monitoring"."10_fct_monitoring_alert_rules"
    ADD COLUMN escalation_policy_id VARCHAR(36) REFERENCES "05_monitoring"."10_fct_monitoring_escalation_policies"(id);
COMMENT ON COLUMN "05_monitoring"."10_fct_monitoring_alert_rules".escalation_policy_id IS 'Optional FK to escalation policy. If set, overrides notify_template_key single-recipient behavior. If NULL, uses legacy notify_template_key for backward compatibility.';

-- ── Read-model view for escalation policies ─────────────────────────────

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_escalation_policies" AS
SELECT
    p.id,
    p.org_id,
    p.name,
    p.description,
    p.is_active,
    p.created_by,
    p.updated_by,
    p.created_at,
    p.updated_at,
    p.deleted_at,
    (
        SELECT json_agg(
            json_build_object(
                'step_order', s.step_order,
                'kind_id', s.kind_id,
                'kind_code', k.code,
                'kind_label', k.label,
                'target_ref', s.target_ref,
                'wait_seconds', s.wait_seconds,
                'priority', s.priority
            ) ORDER BY s.step_order ASC
        )
        FROM "05_monitoring"."40_lnk_monitoring_escalation_steps" s
        JOIN "05_monitoring"."02_dim_escalation_step_kind" k ON k.id = s.kind_id
        WHERE s.policy_id = p.id
    ) AS steps
FROM "05_monitoring"."10_fct_monitoring_escalation_policies" p
WHERE p.deleted_at IS NULL;
COMMENT ON VIEW "05_monitoring"."v_monitoring_escalation_policies" IS 'Read-model for escalation policies: aggregates steps with kind resolution.';

-- DOWN ====
DROP VIEW IF EXISTS "05_monitoring"."v_monitoring_escalation_policies";
ALTER TABLE "05_monitoring"."10_fct_monitoring_alert_rules"
    DROP COLUMN IF EXISTS escalation_policy_id;
DROP TABLE IF EXISTS "05_monitoring"."20_dtl_monitoring_alert_escalation_state";
DROP TABLE IF EXISTS "05_monitoring"."40_lnk_monitoring_escalation_steps";
DROP TABLE IF EXISTS "05_monitoring"."10_fct_monitoring_escalation_policies";
DROP TABLE IF EXISTS "05_monitoring"."02_dim_escalation_step_kind";
