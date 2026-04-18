-- UP ====

CREATE TABLE IF NOT EXISTS "03_iam"."47_fct_siem_destinations" (
    id                  VARCHAR(36)  NOT NULL,
    org_id              VARCHAR(36)  NOT NULL,
    kind                VARCHAR(20)  NOT NULL,  -- webhook | splunk_hec | datadog | s3
    label               TEXT         NOT NULL DEFAULT '',
    config_jsonb        JSONB        NOT NULL DEFAULT '{}',
    credentials_vault_key TEXT       NULL,       -- vault key storing sensitive creds
    is_active           BOOLEAN      NOT NULL DEFAULT TRUE,
    last_cursor         BIGINT       NOT NULL DEFAULT 0,
    last_exported_at    TIMESTAMP    NULL,
    failure_count       INTEGER      NOT NULL DEFAULT 0,
    created_by          VARCHAR(36)  NOT NULL,
    updated_by          VARCHAR(36)  NOT NULL,
    created_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at          TIMESTAMP    NULL,
    CONSTRAINT pk_iam_fct_siem_destinations PRIMARY KEY (id),
    CONSTRAINT fk_iam_fct_siem_dests_org FOREIGN KEY (org_id)
        REFERENCES "03_iam"."10_fct_orgs"(id) ON DELETE CASCADE,
    CONSTRAINT chk_iam_siem_kind CHECK (kind IN ('webhook', 'splunk_hec', 'datadog', 's3'))
);

CREATE INDEX IF NOT EXISTS idx_iam_siem_dests_org ON "03_iam"."47_fct_siem_destinations" (org_id)
    WHERE deleted_at IS NULL;

COMMENT ON TABLE  "03_iam"."47_fct_siem_destinations" IS 'SIEM export destinations per org.';
COMMENT ON COLUMN "03_iam"."47_fct_siem_destinations".kind IS 'Destination type: webhook, splunk_hec, datadog, s3.';
COMMENT ON COLUMN "03_iam"."47_fct_siem_destinations".last_cursor IS 'Last outbox id successfully exported — used to advance the read cursor.';
COMMENT ON COLUMN "03_iam"."47_fct_siem_destinations".failure_count IS 'Consecutive delivery failures; reset on success.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."47_fct_siem_destinations";
