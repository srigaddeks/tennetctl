-- UP ====

-- IAM mobile-OTP sub-feature.
-- Adds:
--   * dim_account_types rows for mobile_otp + soma_delights_customer
--   * dim_attr_defs row for `phone` (entity_type=user) so phones can be
--     stored EAV-style in dtl_attrs (canonical user store).
--   * 24_fct_iam_mobile_otp_codes table — short-lived 6-digit codes
--     keyed by phone_e164, with optional FK to fct_users (NULL for
--     pre-signup requests).
--
-- Twilio integration is plug-in via vault config (sms.twilio.account_sid,
-- sms.twilio.auth_token, sms.twilio.from_number) — backend logs the OTP
-- when no creds are present, sends real SMS when configured.

INSERT INTO "03_iam"."02_dim_account_types" (id, code, label, description, deprecated_at)
VALUES
    (6, 'mobile_otp',              'Mobile OTP',              'SMS-delivered one-time passcode (Twilio).',                NULL),
    (7, 'soma_delights_customer',  'Soma Delights Customer',  'End-customer of the Soma Delights consumer app.',          NULL)
ON CONFLICT (id) DO NOTHING;

INSERT INTO "03_iam"."20_dtl_attr_defs" (entity_type_id, code, label, value_type, description, deprecated_at)
VALUES (3, 'phone', 'Phone (E.164)', 'text', 'Mobile phone in E.164 format. Used by mobile_otp account type.', NULL)
ON CONFLICT (entity_type_id, code) DO NOTHING;

CREATE TABLE "03_iam"."24_fct_iam_mobile_otp_codes" (
    id            VARCHAR(36)  NOT NULL,
    user_id       VARCHAR(36)  NULL,
    phone_e164    TEXT         NOT NULL,
    code_hash     TEXT         NOT NULL,
    attempts      SMALLINT     NOT NULL DEFAULT 0,
    expires_at    TIMESTAMP    NOT NULL,
    consumed_at   TIMESTAMP    NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_iam_mobile_otp_codes        PRIMARY KEY (id),
    CONSTRAINT fk_iam_mobile_otp_codes_user   FOREIGN KEY (user_id) REFERENCES "03_iam"."12_fct_users"(id),
    CONSTRAINT chk_iam_mobile_otp_phone_fmt   CHECK (phone_e164 LIKE '+%' AND length(phone_e164) BETWEEN 8 AND 16),
    CONSTRAINT chk_iam_mobile_otp_attempts    CHECK (attempts >= 0 AND attempts <= 10)
);

CREATE INDEX idx_iam_mobile_otp_phone_created ON "03_iam"."24_fct_iam_mobile_otp_codes" (phone_e164, created_at DESC);
CREATE INDEX idx_iam_mobile_otp_user          ON "03_iam"."24_fct_iam_mobile_otp_codes" (user_id) WHERE user_id IS NOT NULL;
CREATE INDEX idx_iam_mobile_otp_expires       ON "03_iam"."24_fct_iam_mobile_otp_codes" (expires_at) WHERE consumed_at IS NULL;

COMMENT ON TABLE  "03_iam"."24_fct_iam_mobile_otp_codes" IS 'Append-only-ish mobile OTP codes. Hash stored, not raw. user_id is NULL for pre-signup requests; populated on first verify after user lookup/creation. consumed_at is set once on success.';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".id IS 'UUID v7.';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".user_id IS 'User UUID once resolved. NULL for unresolved pre-signup requests.';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".phone_e164 IS 'E.164 international format (must start with +).';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".code_hash IS 'argon2 hash of the 6-digit code. Raw code never persisted.';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".attempts IS 'Verification attempts. Capped at 10 to throttle brute force.';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".expires_at IS 'Code expiry. Default 5 minutes from issue; service-side enforced.';
COMMENT ON COLUMN "03_iam"."24_fct_iam_mobile_otp_codes".consumed_at IS 'Set once when code is verified. Codes are single-use.';

-- DOWN ====

DROP TABLE IF EXISTS "03_iam"."24_fct_iam_mobile_otp_codes";
DELETE FROM "03_iam"."20_dtl_attr_defs" WHERE entity_type_id = 3 AND code = 'phone';
DELETE FROM "03_iam"."02_dim_account_types" WHERE id IN (6, 7);
