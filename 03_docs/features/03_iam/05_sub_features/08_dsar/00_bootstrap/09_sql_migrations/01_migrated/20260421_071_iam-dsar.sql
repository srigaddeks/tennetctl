-- UP ====

-- iam.dsar sub-feature: operator-triggered Data Subject Access Requests.
-- Depends on: iam bootstrap (schema "03_iam"), iam.users (12_fct_users), iam.orgs (10_fct_orgs).
-- Shape aligns with repository.py (Plan 45-01 APPLY): numbered fct/dim/evt tables with dim FKs.

-- Dim: dsar status lifecycle (statically seeded via YAML -> plain SMALLINT PK).
CREATE TABLE "03_iam"."07_dim_dsar_statuses" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_dsar_statuses PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_dsar_statuses_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."07_dim_dsar_statuses" IS 'DSAR job lifecycle states (requested/in_progress/completed/failed).';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".id IS 'Stable SMALLINT PK (YAML-seeded).';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".code IS 'Stable machine code used by services.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".description IS 'Long-form description.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".deprecated_at IS 'Set when a status is retired; row is never deleted.';

-- Dim: dsar job kinds (export | delete).
CREATE TABLE "03_iam"."08_dim_dsar_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_dsar_types PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_dsar_types_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."08_dim_dsar_types" IS 'DSAR job kind — export (SAR) or delete (RTBF).';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".id IS 'Stable SMALLINT PK (YAML-seeded).';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".code IS 'Stable machine code used by services.';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".description IS 'Long-form description.';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".deprecated_at IS 'Set when a type is retired; row is never deleted.';

-- Event: append-only DSAR job log. No updated_at, no deleted_at (evt_* rule).
-- No created_by / updated_by — instrumentation-emitted (Phase 13 monitoring precedent
-- extended to admin-operator-initiated events where the actor is captured in a
-- first-class column: `actor_user_id`).
CREATE TABLE "03_iam"."65_evt_dsar_jobs" (
    id                 VARCHAR(36) NOT NULL,
    org_id             VARCHAR(36) NOT NULL,
    subject_user_id    VARCHAR(36) NOT NULL,
    actor_user_id      VARCHAR(36) NOT NULL,
    actor_session_id   VARCHAR(36),
    job_type_id        SMALLINT NOT NULL,
    status_id          SMALLINT NOT NULL,
    row_counts         JSONB,
    result_location    TEXT,
    error_detail       TEXT,
    completed_at       TIMESTAMP,
    created_at         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_test            BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT pk_iam_evt_dsar_jobs            PRIMARY KEY (id),
    CONSTRAINT fk_iam_evt_dsar_jobs_org        FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_subject    FOREIGN KEY (subject_user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_actor      FOREIGN KEY (actor_user_id)
        REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_type       FOREIGN KEY (job_type_id)
        REFERENCES "03_iam"."08_dim_dsar_types"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_status     FOREIGN KEY (status_id)
        REFERENCES "03_iam"."07_dim_dsar_statuses"(id)
);
CREATE INDEX idx_iam_evt_dsar_jobs_org_id          ON "03_iam"."65_evt_dsar_jobs" (org_id);
CREATE INDEX idx_iam_evt_dsar_jobs_subject_user_id ON "03_iam"."65_evt_dsar_jobs" (subject_user_id);
CREATE INDEX idx_iam_evt_dsar_jobs_status_id       ON "03_iam"."65_evt_dsar_jobs" (status_id);
CREATE INDEX idx_iam_evt_dsar_jobs_created_at      ON "03_iam"."65_evt_dsar_jobs" (created_at DESC);

COMMENT ON TABLE  "03_iam"."65_evt_dsar_jobs" IS 'Append-only log of DSAR export/delete jobs. Operator-triggered. Worker transitions status_id; row itself is never updated for lifecycle changes beyond the few mutable columns (status_id, row_counts, result_location, error_detail, completed_at).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".id IS 'UUID v7 — assigned by the app at INSERT time.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".org_id IS 'Tenant scope (10_fct_orgs).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".subject_user_id IS 'Data subject (whose data is being exported or deleted).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".actor_user_id IS 'Operator who triggered the job.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".actor_session_id IS 'Optional session id of the operator at request time (null when invoked outside a session).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".job_type_id IS 'FK → 08_dim_dsar_types (export | delete).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".status_id IS 'FK → 07_dim_dsar_statuses; worker transitions requested → in_progress → completed | failed.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".row_counts IS 'Per-table row counts produced by the job (JSONB keyed by table name).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".result_location IS 'Vault key (or stub path) where the export JSON is stored; null for delete jobs.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".error_detail IS 'Populated when status=failed; truncated to 500 chars in code.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".completed_at IS 'Set when status reaches completed or failed.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".is_test IS 'Marks test/staging data.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."65_evt_dsar_jobs";
DROP TABLE IF EXISTS "03_iam"."08_dim_dsar_types";
DROP TABLE IF EXISTS "03_iam"."07_dim_dsar_statuses";
