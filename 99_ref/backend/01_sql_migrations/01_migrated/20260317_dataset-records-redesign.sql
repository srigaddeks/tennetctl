-- ---------------------------------------------------------------------------
-- Dataset records redesign:
--   Replace 43_dtl_dataset_payloads (one JSONB blob per dataset) with
--   43_dtl_dataset_records (one row per JSON record, with sequence + asset link)
-- ---------------------------------------------------------------------------

-- 1. Drop old single-blob payload table (cascade removes FK refs)
DROP TABLE IF EXISTS "15_sandbox"."43_dtl_dataset_payloads" CASCADE;

-- 2. Create per-record table
CREATE TABLE IF NOT EXISTS "15_sandbox"."43_dtl_dataset_records" (
    id              UUID         NOT NULL DEFAULT gen_random_uuid(),
    dataset_id      UUID         NOT NULL,
    record_seq      INTEGER      NOT NULL,          -- ordering within dataset
    record_name     VARCHAR(200) NULL,              -- human-readable label
    description     TEXT         NULL,
    recorded_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    source_asset_id UUID         NULL,              -- optional link to 33_fct_assets
    connector_instance_id UUID   NULL,              -- which connector the record came from
    record_data     JSONB        NOT NULL DEFAULT '{}',

    CONSTRAINT pk_43_dtl_dataset_records        PRIMARY KEY (id),
    CONSTRAINT uq_43_dtl_dataset_records_seq    UNIQUE (dataset_id, record_seq),
    CONSTRAINT fk_43_dtl_dataset_records_ds     FOREIGN KEY (dataset_id)
        REFERENCES "15_sandbox"."21_fct_datasets" (id) ON DELETE CASCADE,
    CONSTRAINT fk_43_dtl_dataset_records_asset  FOREIGN KEY (source_asset_id)
        REFERENCES "15_sandbox"."33_fct_assets" (id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_43_dtl_dataset_records_dataset
    ON "15_sandbox"."43_dtl_dataset_records" (dataset_id, record_seq);

CREATE INDEX IF NOT EXISTS idx_43_dtl_dataset_records_asset
    ON "15_sandbox"."43_dtl_dataset_records" (source_asset_id)
    WHERE source_asset_id IS NOT NULL;

-- 3. Add asset_ids array column to 21_fct_datasets for quick asset association lookup
ALTER TABLE "15_sandbox"."21_fct_datasets"
    ADD COLUMN IF NOT EXISTS asset_ids UUID[] NULL;

-- 4. Create a view for dataset record counts (updates row_count on demand via trigger)
CREATE OR REPLACE FUNCTION "15_sandbox".fn_sync_dataset_row_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        UPDATE "15_sandbox"."21_fct_datasets"
        SET row_count = (
            SELECT COUNT(*) FROM "15_sandbox"."43_dtl_dataset_records"
            WHERE dataset_id = OLD.dataset_id
        ),
        updated_at = NOW()
        WHERE id = OLD.dataset_id;
        RETURN OLD;
    ELSE
        UPDATE "15_sandbox"."21_fct_datasets"
        SET row_count = (
            SELECT COUNT(*) FROM "15_sandbox"."43_dtl_dataset_records"
            WHERE dataset_id = NEW.dataset_id
        ),
        updated_at = NOW()
        WHERE id = NEW.dataset_id;
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_43_sync_dataset_row_count
    AFTER INSERT OR DELETE ON "15_sandbox"."43_dtl_dataset_records"
    FOR EACH ROW EXECUTE FUNCTION "15_sandbox".fn_sync_dataset_row_count();
