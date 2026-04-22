-- UP ====

-- iam.dsar payload storage (Plan 45-01c).
-- AES-256-GCM-encrypted export payloads keyed by job_id. The DEK itself is
-- fetched at runtime from vault key "iam/dsar/export_dek_v1"; only ciphertext,
-- nonce, and dek_version land in this table. Plaintext never persists.

CREATE TABLE "03_iam"."20_dtl_dsar_payloads" (
    id             VARCHAR(36) NOT NULL,
    job_id         VARCHAR(36) NOT NULL,
    ciphertext     BYTEA       NOT NULL,
    nonce          BYTEA       NOT NULL,
    dek_version    SMALLINT    NOT NULL DEFAULT 1,
    byte_size      INTEGER     NOT NULL,
    created_at     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_dtl_dsar_payloads            PRIMARY KEY (id),
    CONSTRAINT uq_iam_dtl_dsar_payloads_job_id     UNIQUE (job_id),
    CONSTRAINT fk_iam_dtl_dsar_payloads_job        FOREIGN KEY (job_id)
        REFERENCES "03_iam"."65_evt_dsar_jobs"(id),
    CONSTRAINT chk_iam_dtl_dsar_payloads_nonce_len CHECK (octet_length(nonce) = 12),
    CONSTRAINT chk_iam_dtl_dsar_payloads_ciph_len  CHECK (octet_length(ciphertext) > 0),
    CONSTRAINT chk_iam_dtl_dsar_payloads_dek_ver   CHECK (dek_version >= 1),
    CONSTRAINT chk_iam_dtl_dsar_payloads_bytesize  CHECK (byte_size >= 0)
);
CREATE INDEX idx_iam_dtl_dsar_payloads_created_at
    ON "03_iam"."20_dtl_dsar_payloads" (created_at DESC);

COMMENT ON TABLE  "03_iam"."20_dtl_dsar_payloads" IS 'Encrypted DSAR export payloads. One row per completed export job. AES-256-GCM ciphertext produced with a DEK fetched from vault key "iam/dsar/export_dek_v1" at encrypt time; DEK itself is never stored here.';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".id IS 'UUID v7 row PK; result_location on the job row stores this id.';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".job_id IS 'FK → 65_evt_dsar_jobs.id (UNIQUE — at most one payload per job).';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".ciphertext IS 'AES-256-GCM ciphertext (includes 16-byte auth tag suffix).';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".nonce IS '12-byte GCM nonce; fresh per encrypt. Never reused with the same DEK.';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".dek_version IS 'Logical version of the DEK used; supports future key rotation. Current DEK is iam/dsar/export_dek_v1 → version 1.';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".byte_size IS 'Plaintext size in bytes (pre-encryption), for quick size reporting without decrypt.';
COMMENT ON COLUMN "03_iam"."20_dtl_dsar_payloads".created_at IS 'Encryption timestamp (insert time).';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."20_dtl_dsar_payloads";
