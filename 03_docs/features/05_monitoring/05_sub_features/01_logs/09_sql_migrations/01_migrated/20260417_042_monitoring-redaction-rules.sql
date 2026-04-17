-- UP ====
-- fct_monitoring_redaction_rules — registry table (catalog carve-out per 13-01).
-- Rules drive the log redaction pipeline executed in the JetStream consumer
-- (workers.redaction.RedactionEngine). NULL org_id = global default rule.

CREATE TABLE IF NOT EXISTS "05_monitoring"."12_fct_monitoring_redaction_rules" (
    id            SMALLINT GENERATED ALWAYS AS IDENTITY,
    org_id        VARCHAR(36) NULL,
    code          TEXT        NOT NULL,
    pattern       TEXT        NOT NULL,
    applies_to    TEXT        NOT NULL,
    kind          TEXT        NOT NULL,
    replacement   TEXT        NOT NULL DEFAULT '[REDACTED]',
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    priority      SMALLINT    NOT NULL DEFAULT 100,
    created_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_fct_monitoring_redaction_rules PRIMARY KEY (id),
    CONSTRAINT uq_fct_monitoring_redaction_rules_code UNIQUE (code),
    CONSTRAINT chk_fct_monitoring_redaction_rules_applies_to
        CHECK (applies_to IN ('body', 'attribute', 'both')),
    CONSTRAINT chk_fct_monitoring_redaction_rules_kind
        CHECK (kind IN ('regex', 'denylist'))
);

COMMENT ON TABLE  "05_monitoring"."12_fct_monitoring_redaction_rules" IS 'Redaction rules applied to logs before persistence. Registry — catalog carve-out (not EAV).';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".id IS 'SMALLINT identity PK. Registry-identity pattern.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".org_id IS 'Owning org. NULL = global default applied across all orgs.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".code IS 'Stable human-readable code (unique). e.g. "credit_card", "jwt_bearer".';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".pattern IS 'Regex (kind=regex) or attribute key (kind=denylist).';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".applies_to IS 'Which fields the rule targets: body | attribute | both.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".kind IS 'regex = substitute matches with replacement; denylist = drop whole attribute.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".replacement IS 'String substituted for regex matches. Unused for denylist kind.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".is_active IS 'Soft-toggle. Inactive rules are skipped at load time.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".priority IS 'Lower runs first. Tie-break by id ascending.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".created_at IS 'Insert timestamp.';
COMMENT ON COLUMN "05_monitoring"."12_fct_monitoring_redaction_rules".updated_at IS 'Set by app on every UPDATE.';

CREATE INDEX idx_fct_monitoring_redaction_rules_active
    ON "05_monitoring"."12_fct_monitoring_redaction_rules" (is_active, priority)
    WHERE is_active = TRUE;

CREATE OR REPLACE VIEW "05_monitoring"."v_monitoring_redaction_rules" AS
SELECT
    id,
    org_id,
    code,
    pattern,
    applies_to,
    kind,
    replacement,
    is_active,
    priority,
    created_at,
    updated_at
FROM "05_monitoring"."12_fct_monitoring_redaction_rules";
COMMENT ON VIEW "05_monitoring"."v_monitoring_redaction_rules" IS 'Read-model for redaction rules. 1:1 with base table (no joins needed yet).';

-- DOWN ====
DROP VIEW  IF EXISTS "05_monitoring"."v_monitoring_redaction_rules";
DROP TABLE IF EXISTS "05_monitoring"."12_fct_monitoring_redaction_rules";
