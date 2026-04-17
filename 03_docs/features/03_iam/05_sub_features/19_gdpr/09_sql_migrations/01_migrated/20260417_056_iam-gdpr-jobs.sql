-- Migration 056: GDPR jobs (Art 15 export + Art 17 erasure)
-- Schema: "03_iam"

-- UP ====

-- ── dim: GDPR request kinds ────────────────────────────────────────────────────
CREATE TABLE "03_iam"."01_dim_gdpr_kinds" (
    id             SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code           TEXT NOT NULL UNIQUE,
    label          TEXT NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP
);

INSERT INTO "03_iam"."01_dim_gdpr_kinds" (code, label, description) VALUES
    ('export', 'Export',  'Art 15 — subject access / data portability'),
    ('erase',  'Erasure', 'Art 17 — right to be forgotten');

-- ── dim: GDPR job statuses ─────────────────────────────────────────────────────
CREATE TABLE "03_iam"."02_dim_gdpr_statuses" (
    id             SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    code           TEXT NOT NULL UNIQUE,
    label          TEXT NOT NULL,
    description    TEXT,
    deprecated_at  TIMESTAMP
);

INSERT INTO "03_iam"."02_dim_gdpr_statuses" (code, label, description) VALUES
    ('queued',     'Queued',     'Waiting for worker to pick up'),
    ('processing', 'Processing', 'Worker currently assembling bundle'),
    ('completed',  'Completed',  'Bundle ready / erasure complete'),
    ('failed',     'Failed',     'Worker encountered an unrecoverable error'),
    ('cancelled',  'Cancelled',  'User recovered before hard_erase_at');

-- ── fct: GDPR jobs ─────────────────────────────────────────────────────────────
CREATE TABLE "03_iam"."10_fct_gdpr_jobs" (
    id                UUID        PRIMARY KEY,
    user_id           UUID        NOT NULL,
    kind_id           SMALLINT    NOT NULL REFERENCES "03_iam"."01_dim_gdpr_kinds" (id),
    status_id         SMALLINT    NOT NULL REFERENCES "03_iam"."02_dim_gdpr_statuses" (id),
    requested_at      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at      TIMESTAMP,
    download_url_hash TEXT,       -- HMAC-SHA256 of the signed download path (never store plaintext)
    hard_erase_at     TIMESTAMP,  -- non-null for erase jobs; null for export jobs
    error_detail      TEXT,       -- last error message from worker, if any
    created_by        UUID,
    updated_by        UUID,
    created_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ON "03_iam"."10_fct_gdpr_jobs" (user_id);
CREATE INDEX ON "03_iam"."10_fct_gdpr_jobs" (status_id);
CREATE INDEX ON "03_iam"."10_fct_gdpr_jobs" (hard_erase_at) WHERE hard_erase_at IS NOT NULL;

-- DOWN ====
DROP TABLE IF EXISTS "03_iam"."10_fct_gdpr_jobs";
DROP TABLE IF EXISTS "03_iam"."02_dim_gdpr_statuses";
DROP TABLE IF EXISTS "03_iam"."01_dim_gdpr_kinds";
