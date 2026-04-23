-- UP ====

-- Add application_id to audit events. Every SaaS app running on tennetctl
-- (solsocial first, more later) stamps its application_id so operators can
-- filter audit by app. Nullable — legacy and platform-internal events leave
-- it unset. No change to chk_evt_audit_scope (already covers the mandatory
-- fields; application_id is an additional dimension, not a replacement).

ALTER TABLE "04_audit"."60_evt_audit"
    ADD COLUMN application_id VARCHAR(36);

COMMENT ON COLUMN "04_audit"."60_evt_audit".application_id IS
    'Foreign ref to 03_iam.15_fct_applications. Set when the event originates '
    'from a SaaS application (solsocial, etc.). NULL = platform-internal event.';

ALTER TABLE "04_audit"."60_evt_audit"
    ADD CONSTRAINT fk_evt_audit_application
        FOREIGN KEY (application_id)
        REFERENCES "03_iam"."15_fct_applications" (id);

CREATE INDEX idx_evt_audit_application_created
    ON "04_audit"."60_evt_audit" (application_id, created_at DESC)
    WHERE application_id IS NOT NULL;

-- Rebuild v_audit_events so callers see application_id in read results.
DROP VIEW IF EXISTS "04_audit"."v_audit_events";

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
    e.application_id,
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

COMMENT ON VIEW "04_audit"."v_audit_events" IS
    'Read-path view over evt_audit with resolved category_label and event_label, plus application_id for per-app filtering.';

-- DOWN ====

DROP VIEW IF EXISTS "04_audit"."v_audit_events";

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

DROP INDEX IF EXISTS "04_audit".idx_evt_audit_application_created;
ALTER TABLE "04_audit"."60_evt_audit" DROP CONSTRAINT IF EXISTS fk_evt_audit_application;
ALTER TABLE "04_audit"."60_evt_audit" DROP COLUMN IF EXISTS application_id;
