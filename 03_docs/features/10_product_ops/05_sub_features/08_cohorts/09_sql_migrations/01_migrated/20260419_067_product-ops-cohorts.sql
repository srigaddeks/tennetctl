-- UP ====

-- product_ops.cohorts — saved filter sets with materialized rolling membership.
--
-- A cohort is a saved query that resolves to a set of visitor_ids. Two flavors:
--   - dynamic: definition is the eligibility AST (Phase 52 evaluator); membership
--     re-computed on demand or on a schedule. Examples: "US visitors who signed up
--     in last 7 days", "free plan with mrr_cents > 0".
--   - static: a fixed list of visitor_ids (CSV import, manual paste). Useful for
--     one-time sends, paid-list imports, etc.
--
-- Materialization: lnk_cohort_members holds the resolved set. Operators trigger
-- a recompute via POST /v1/cohorts/{id}/refresh; service runs the rule against
-- v_visitor_profiles + recent events and replaces the lnk rows.
--
-- Cohort membership becomes a primitive in the eligibility evaluator via the
-- cohort_member op: {"op":"cohort_member","value":"power_users"}. This wires
-- cohorts into promo eligibility, campaign audiences, and (Phase 55) destination
-- filters with one shared mechanism.

CREATE TABLE "10_product_ops"."10_fct_cohorts" (
    id              VARCHAR(36) NOT NULL,
    slug            TEXT NOT NULL,
    name            TEXT NOT NULL,
    description     TEXT,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    -- 'dynamic' = re-computable from definition; 'static' = fixed member list
    kind            TEXT NOT NULL,
    -- For dynamic: the eligibility AST evaluated against visitor profiles + events.
    -- For static: ignored / empty object.
    definition      JSONB NOT NULL DEFAULT '{}'::jsonb,
    -- Pre-aggregated rendering hints
    last_computed_at TIMESTAMP,
    member_count    INTEGER NOT NULL DEFAULT 0,
    -- Operational
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_by      VARCHAR(36) NOT NULL,
    deleted_at      TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_fct_cohorts PRIMARY KEY (id),
    CONSTRAINT uq_fct_cohorts_workspace_slug UNIQUE (workspace_id, slug),
    CONSTRAINT chk_fct_cohorts_kind CHECK (kind IN ('dynamic','static'))
);

CREATE INDEX idx_fct_cohorts_workspace_active
    ON "10_product_ops"."10_fct_cohorts" (workspace_id, is_active)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE "10_product_ops"."10_fct_cohorts" IS 'Saved visitor filter sets. dynamic = rule-based, static = fixed list. Membership materialized in lnk_cohort_members; refreshed on demand.';

-- ── Membership (materialized) ─────────────────────────────────────

CREATE TABLE "10_product_ops"."40_lnk_cohort_members" (
    id              BIGSERIAL,
    cohort_id       VARCHAR(36) NOT NULL,
    visitor_id      VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    joined_at       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_lnk_cohort_members PRIMARY KEY (id),
    CONSTRAINT uq_lnk_cohort_members_cohort_visitor UNIQUE (cohort_id, visitor_id),
    CONSTRAINT fk_lnk_cohort_members_cohort
        FOREIGN KEY (cohort_id) REFERENCES "10_product_ops"."10_fct_cohorts"(id) ON DELETE CASCADE,
    CONSTRAINT fk_lnk_cohort_members_visitor
        FOREIGN KEY (visitor_id) REFERENCES "10_product_ops"."10_fct_visitors"(id) ON DELETE CASCADE
);

CREATE INDEX idx_lnk_cohort_members_cohort ON "10_product_ops"."40_lnk_cohort_members" (cohort_id);
CREATE INDEX idx_lnk_cohort_members_visitor ON "10_product_ops"."40_lnk_cohort_members" (visitor_id);

COMMENT ON TABLE "10_product_ops"."40_lnk_cohort_members" IS 'Materialized cohort membership. Refreshed by service.refresh_cohort. UNIQUE prevents duplicate rows; ON DELETE CASCADE keeps consistency on cohort/visitor delete.';

-- ── Computation log (audit trail of refreshes) ────────────────────

CREATE TABLE "10_product_ops"."60_evt_cohort_computations" (
    id              VARCHAR(36) NOT NULL,
    cohort_id       VARCHAR(36) NOT NULL,
    org_id          VARCHAR(36) NOT NULL,
    workspace_id    VARCHAR(36) NOT NULL,
    triggered_by    VARCHAR(36),       -- nullable for scheduled refreshes
    duration_ms     INTEGER NOT NULL,
    members_added   INTEGER NOT NULL,
    members_removed INTEGER NOT NULL,
    final_count     INTEGER NOT NULL,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_evt_cohort_computations PRIMARY KEY (id),
    CONSTRAINT fk_evt_cohort_computations_cohort
        FOREIGN KEY (cohort_id) REFERENCES "10_product_ops"."10_fct_cohorts"(id)
);

CREATE INDEX idx_evt_cohort_computations_cohort_occurred
    ON "10_product_ops"."60_evt_cohort_computations" (cohort_id, occurred_at DESC);

COMMENT ON TABLE "10_product_ops"."60_evt_cohort_computations" IS 'Append-only refresh history. Diagnostic surface for cohort drift + perf monitoring.';

-- ── Read view ─────────────────────────────────────────────────────

CREATE OR REPLACE VIEW "10_product_ops".v_cohorts AS
SELECT
    c.id,
    c.slug,
    c.name,
    c.description,
    c.org_id,
    c.workspace_id,
    c.kind,
    c.definition,
    c.last_computed_at,
    c.member_count,
    c.is_active,
    (c.deleted_at IS NOT NULL) AS is_deleted,
    c.deleted_at,
    c.created_by,
    c.created_at,
    c.updated_at,
    -- Most recent refresh stats for at-a-glance health
    (SELECT duration_ms FROM "10_product_ops"."60_evt_cohort_computations" cc
       WHERE cc.cohort_id = c.id ORDER BY occurred_at DESC LIMIT 1) AS last_refresh_duration_ms,
    (SELECT COUNT(*) FROM "10_product_ops"."60_evt_cohort_computations" cc
       WHERE cc.cohort_id = c.id) AS refresh_count
FROM "10_product_ops"."10_fct_cohorts" c;

COMMENT ON VIEW "10_product_ops".v_cohorts IS 'Cohort read view with last-refresh duration + refresh count.';

-- DOWN ====

DROP VIEW  IF EXISTS "10_product_ops".v_cohorts;
DROP TABLE IF EXISTS "10_product_ops"."60_evt_cohort_computations";
DROP TABLE IF EXISTS "10_product_ops"."40_lnk_cohort_members";
DROP TABLE IF EXISTS "10_product_ops"."10_fct_cohorts";
