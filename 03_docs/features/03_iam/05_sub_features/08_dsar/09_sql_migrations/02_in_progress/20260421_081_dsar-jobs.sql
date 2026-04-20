-- UP ====

-- DSAR (Data Subject Access Request) — Operator-triggered data subject requests.
-- Separate from self-service GDPR (19_gdpr). Append-only event table.

-- ── DSAR job statuses ──────────────────────────────────────────────────────

CREATE TABLE "03_iam"."07_dim_dsar_statuses" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_dsar_statuses PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_dsar_statuses_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."07_dim_dsar_statuses" IS 'DSAR job statuses: requested → in_progress → completed or failed.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".code IS 'Status code (requested, in_progress, completed, failed).';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."07_dim_dsar_statuses".deprecated_at IS 'Non-null when deprecated.';

-- ── DSAR job types ───────────────────────────────────────────────────────

CREATE TABLE "03_iam"."08_dim_dsar_types" (
    id              SMALLINT NOT NULL,
    code            TEXT NOT NULL,
    label           TEXT NOT NULL,
    description     TEXT,
    deprecated_at   TIMESTAMP,
    CONSTRAINT pk_iam_dim_dsar_types PRIMARY KEY (id),
    CONSTRAINT uq_iam_dim_dsar_types_code UNIQUE (code)
);
COMMENT ON TABLE  "03_iam"."08_dim_dsar_types" IS 'DSAR job types: export (SAR) or delete (right to be forgotten).';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".id IS 'Permanent manual ID. Never renumber.';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".code IS 'Job type code (export, delete).';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".label IS 'Human-readable label.';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".description IS 'Free-text description.';
COMMENT ON COLUMN "03_iam"."08_dim_dsar_types".deprecated_at IS 'Non-null when deprecated.';

-- ── DSAR jobs table (append-only, no updated_at) ──────────────────────────

CREATE TABLE "03_iam"."65_evt_dsar_jobs" (
    id                  VARCHAR(36) NOT NULL,
    org_id              VARCHAR(36) NOT NULL,
    subject_user_id     VARCHAR(36) NOT NULL,
    actor_user_id       VARCHAR(36) NOT NULL,
    actor_session_id    VARCHAR(36),
    job_type_id         SMALLINT NOT NULL,
    status_id           SMALLINT NOT NULL DEFAULT 1,
    row_counts          JSONB,
    result_location     TEXT,
    error_detail        TEXT,
    completed_at        TIMESTAMP,
    created_at          TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_evt_dsar_jobs PRIMARY KEY (id),
    CONSTRAINT fk_iam_evt_dsar_jobs_job_type FOREIGN KEY (job_type_id)
        REFERENCES "03_iam"."08_dim_dsar_types"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_status FOREIGN KEY (status_id)
        REFERENCES "03_iam"."07_dim_dsar_statuses"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_subject_user FOREIGN KEY (subject_user_id)
        REFERENCES "03_iam"."10_fct_users"(id),
    CONSTRAINT fk_iam_evt_dsar_jobs_actor_user FOREIGN KEY (actor_user_id)
        REFERENCES "03_iam"."10_fct_users"(id),
    CONSTRAINT chk_iam_evt_dsar_jobs_status_id CHECK (status_id >= 1)
);
CREATE INDEX idx_iam_evt_dsar_jobs_org_created
    ON "03_iam"."65_evt_dsar_jobs" (org_id, created_at DESC);
CREATE INDEX idx_iam_evt_dsar_jobs_subject_user
    ON "03_iam"."65_evt_dsar_jobs" (subject_user_id);
CREATE INDEX idx_iam_evt_dsar_jobs_actor_user
    ON "03_iam"."65_evt_dsar_jobs" (actor_user_id);
CREATE INDEX idx_iam_evt_dsar_jobs_status
    ON "03_iam"."65_evt_dsar_jobs" (status_id) WHERE status_id IN (1, 2);
COMMENT ON TABLE  "03_iam"."65_evt_dsar_jobs" IS 'Immutable append-only DSAR job log. No updated_at — events only. Operator-triggered requests.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".id IS 'UUID v7 job ID.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".org_id IS 'Org scope of the request.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".subject_user_id IS 'Target user whose data is requested/deleted.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".actor_user_id IS 'Operator user who triggered the request (audit scope).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".actor_session_id IS 'Session of the operator (audit scope).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".job_type_id IS 'Job type: export (1) or delete (2).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".status_id IS 'Current status: requested (1), in_progress (2), completed (3), failed (4).';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".row_counts IS 'Counts by table after export/delete: {users: 1, sessions: 5, audit: 100, ...}.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".result_location IS 'Vault path or signed download URL for export.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".error_detail IS 'Error message if job failed.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".completed_at IS 'Timestamp when job entered terminal state.';
COMMENT ON COLUMN "03_iam"."65_evt_dsar_jobs".created_at IS 'Job creation timestamp (append-only).';

-- ── View: DSAR jobs scoped by org ──────────────────────────────────────────

CREATE VIEW "03_iam".v_dsar_jobs AS
    SELECT
        j.id,
        j.org_id,
        j.subject_user_id,
        j.actor_user_id,
        j.actor_session_id,
        t.code AS job_type,
        s.code AS status,
        j.row_counts,
        j.result_location,
        j.error_detail,
        j.completed_at,
        j.created_at
    FROM "03_iam"."65_evt_dsar_jobs" j
    JOIN "03_iam"."08_dim_dsar_types" t ON t.id = j.job_type_id
    JOIN "03_iam"."07_dim_dsar_statuses" s ON s.id = j.status_id
    WHERE j.completed_at IS NOT NULL OR j.status_id IN (1, 2);
COMMENT ON VIEW "03_iam".v_dsar_jobs IS 'DSAR jobs view — org-scoped, excludes fully purged rows.';

-- DOWN ====

DROP VIEW IF EXISTS "03_iam".v_dsar_jobs;
DROP TABLE IF EXISTS "03_iam"."65_evt_dsar_jobs";
DROP TABLE IF EXISTS "03_iam"."08_dim_dsar_types";
DROP TABLE IF EXISTS "03_iam"."07_dim_dsar_statuses";
