-- UP ====

-- Per-org IP allowlist — CIDR entries
CREATE TABLE IF NOT EXISTS "03_iam"."46_lnk_org_ip_allowlist" (
    id         VARCHAR(36)  NOT NULL,
    org_id     VARCHAR(36)  NOT NULL,
    cidr       VARCHAR(50)  NOT NULL,
    label      TEXT         NOT NULL DEFAULT '',
    created_by VARCHAR(36)  NOT NULL,
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_iam_lnk_org_ip_allowlist PRIMARY KEY (id),
    CONSTRAINT fk_iam_lnk_org_ip_allowlist_org
        FOREIGN KEY (org_id) REFERENCES "03_iam"."10_fct_orgs" (id) ON DELETE CASCADE,
    CONSTRAINT uq_iam_lnk_org_ip_allowlist_cidr UNIQUE (org_id, cidr)
);

COMMENT ON TABLE "03_iam"."46_lnk_org_ip_allowlist" IS 'Per-org IP CIDR allowlist — if any entries exist, all requests must originate from a matching IP';
COMMENT ON COLUMN "03_iam"."46_lnk_org_ip_allowlist".cidr IS 'IPv4/IPv6 CIDR block, e.g. 10.0.0.0/8 or 203.0.113.42/32';

CREATE INDEX IF NOT EXISTS idx_iam_lnk_org_ip_allowlist_org
    ON "03_iam"."46_lnk_org_ip_allowlist" (org_id);

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."46_lnk_org_ip_allowlist";
