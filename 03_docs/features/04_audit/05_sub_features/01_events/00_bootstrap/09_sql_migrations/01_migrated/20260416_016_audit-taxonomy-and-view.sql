-- UP ====

-- Audit analytics foundation (Phase 10 Plan 01):
--   * dim_audit_categories — typed taxonomy of audit categories (system/user/integration/setup)
--   * dim_audit_event_keys — registered event keys with labels/descriptions (auto-synced + explicit)
--   * v_audit_events       — read-path view joining evt_audit to both dim tables
--
-- Design note (deviation from plan): we DO NOT add a category_id FK to evt_audit
-- in this migration. The existing audit_category TEXT column + chk_evt_audit_category
-- + chk_evt_audit_scope are preserved unchanged. The dim_audit_categories table is
-- joined to evt_audit via the TEXT code in v_audit_events. This preserves full
-- backward compatibility with audit.events.emit (which writes audit_category TEXT).
-- A future plan can migrate emitters to category_id + drop the text column; that
-- cutover is out of scope here.

CREATE TABLE "04_audit"."01_dim_audit_categories" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_dim_audit_categories PRIMARY KEY (id),
    CONSTRAINT uq_dim_audit_categories_code UNIQUE (code)
);

COMMENT ON TABLE  "04_audit"."01_dim_audit_categories" IS 'Typed taxonomy of audit categories (system/user/integration/setup). Joined to evt_audit via TEXT code — evt_audit.audit_category itself keeps its CHECK constraint as the enforcement layer. Plain SMALLINT PK seeded with fixed ids (matches project dim_* convention).';
COMMENT ON COLUMN "04_audit"."01_dim_audit_categories".id IS 'SMALLINT PK seeded with fixed id. Stable; never renumber.';
COMMENT ON COLUMN "04_audit"."01_dim_audit_categories".code IS 'Stable TEXT code matching evt_audit.audit_category values: system | user | integration | setup.';
COMMENT ON COLUMN "04_audit"."01_dim_audit_categories".label IS 'Human-readable label for UIs.';
COMMENT ON COLUMN "04_audit"."01_dim_audit_categories".description IS 'Long-form explanation of when this category applies.';
COMMENT ON COLUMN "04_audit"."01_dim_audit_categories".deprecated_at IS 'Soft-deprecation timestamp; code stays valid but UI hides / warns.';

-- Seeding lives in seeds/04audit_categories.yaml (idempotent via ON CONFLICT DO NOTHING).
-- Migration does NOT insert rows — seeder is the authoritative path.

CREATE TABLE "04_audit"."02_dim_audit_event_keys" (
    id              SMALLINT GENERATED ALWAYS AS IDENTITY,
    key             TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    category_id     SMALLINT NOT NULL,
    deprecated_at   TIMESTAMP,
    created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_dim_audit_event_keys PRIMARY KEY (id),
    CONSTRAINT uq_dim_audit_event_keys_key UNIQUE (key),
    CONSTRAINT fk_dim_audit_event_keys_category FOREIGN KEY (category_id)
        REFERENCES "04_audit"."01_dim_audit_categories" (id)
);

CREATE INDEX idx_dim_audit_event_keys_category ON "04_audit"."02_dim_audit_event_keys" (category_id);

COMMENT ON TABLE  "04_audit"."02_dim_audit_event_keys" IS 'Registered audit event keys with labels + descriptions + default category. Populated via (a) auto-sync on observed evt_audit writes and (b) explicit registration via feature manifests (future plan).';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".id IS 'SMALLINT identity PK.';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".key IS 'Dotted-snake event key, e.g. "iam.orgs.created". Matches evt_audit.event_key.';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".label IS 'Short human-readable label for UIs.';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".description IS 'Long-form description of what this event signals.';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".category_id IS 'FK to dim_audit_categories — the expected category for rows carrying this key.';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".deprecated_at IS 'Soft-deprecation timestamp.';
COMMENT ON COLUMN "04_audit"."02_dim_audit_event_keys".created_at IS 'Registration timestamp (first observation or manifest registration).';

-- Read-path view. Joins via TEXT columns, not FKs — keeps backward compat with
-- emit_audit while exposing resolved labels for the Audit Explorer UI.
CREATE VIEW "04_audit"."v_audit_events" AS
SELECT
    e.id,
    e.event_key,
    k.label                         AS event_label,
    k.description                   AS event_description,
    e.audit_category                AS category_code,
    c.label                         AS category_label,
    e.actor_user_id,
    e.actor_session_id,
    e.org_id,
    e.workspace_id,
    e.trace_id,
    e.span_id,
    e.parent_span_id,
    e.outcome,
    e.metadata,
    e.created_at
FROM "04_audit"."60_evt_audit" e
LEFT JOIN "04_audit"."01_dim_audit_categories" c
    ON c.code = e.audit_category
LEFT JOIN "04_audit"."02_dim_audit_event_keys" k
    ON k.key = e.event_key;

COMMENT ON VIEW "04_audit"."v_audit_events" IS 'Read-path view over evt_audit with resolved category_label (via dim_audit_categories.code) and event_label/description (via dim_audit_event_keys.key). LEFT JOINs so unregistered event keys still return the row with NULL labels.';

-- DOWN ====

DROP VIEW IF EXISTS "04_audit"."v_audit_events";
DROP TABLE IF EXISTS "04_audit"."02_dim_audit_event_keys";
DROP TABLE IF EXISTS "04_audit"."01_dim_audit_categories";
