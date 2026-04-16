-- OTP Email Verification: add otp_code variable key, seed email template + version + placeholders
-- This template is used when a user requests OTP during onboarding/email verification.

-- ──────────────────────────────────────────────────────────────────────────────
-- 1. Add otp_code variable key (audit_property → otp_code)
-- ──────────────────────────────────────────────────────────────────────────────
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value, resolution_source, resolution_key, sort_order, created_at, updated_at)
VALUES
    ('10000000-0000-0000-0000-000000000050', 'otp_code', 'OTP Code', 'One-time verification code', 'string', '482901', 'audit_property', 'otp_code', 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ──────────────────────────────────────────────────────────────────────────────
-- 2. Seed OTP email verification template + version
-- ──────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    _tpl_id  UUID := gen_random_uuid();
    _ver_id  UUID := gen_random_uuid();
BEGIN
    INSERT INTO "03_notifications"."10_fct_templates" (
        id, tenant_key, code, name, description,
        notification_type_code, channel_code,
        is_active, is_system,
        created_at, updated_at
    ) VALUES (
        _tpl_id, '__system__',
        'email_verification_otp',
        'Email Verification OTP',
        'Sends a 6-digit OTP code for email verification during onboarding.',
        'email_verification', 'email',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_html, body_text, body_short,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'Your Verification OTP — K-Control',
        E'<html>\n<body style="font-family: Arial, sans-serif; background: #F9F9FB; margin:0; padding:0;">\n  <div style="background: #fff; margin: 24px auto; padding: 32px 20px 24px 20px; max-width: 480px; border-radius: 8px; box-shadow:0 2px 6px #eee;">\n    <div style="padding:32px 32px 0 32px;text-align:center;">\n      <img src="{{ platform.logo_url }}" alt="Kreesalis Logo" style="max-width:120px;margin-bottom:16px;" /><br>\n    </div>\n    <h2 style="text-align:center; margin-bottom:16px; color:#222;">Your Verification OTP</h2>\n    <div style="font-size:17px; margin-bottom:16px; color:#222;">Hi {{ user.first_name }},</div>\n    <div style="font-size:16px; margin-bottom:16px; color:#222;">Please use the OTP below to complete your verification:</div>\n    <div style="text-align:center; margin-bottom:20px;">\n      <div style="display:inline-block; background: #eaf3fb; color:#2184e2; border-radius:10px; padding:18px 48px; font-size:32px; font-weight:600; letter-spacing:3px;">\n        {{ otp_code }}\n      </div>\n    </div>\n    <div style="font-size:15px; margin-bottom:20px; color:#222;">This OTP expires in <b>5 minutes</b>.</div>\n    <div style="font-size:15px; margin-bottom:20px; color:#222;">Best regards,<br><b>Kreesalis Team</b></div>\n    <div style="font-size:12px; color:#666; margin-top:28px; border-top:1px solid #efefef; padding-top:16px;">\n      <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.\n    </div>\n  </div>\n</body>\n</html>',
        E'Hi {{ user.first_name }},\n\nYour verification OTP is: {{ otp_code }}\n\nThis OTP expires in 5 minutes.\n\nBest regards,\nKreesalis Team',
        'Your OTP is {{ otp_code }}. Expires in 5 minutes.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;

    -- 3. Declare template placeholders
    INSERT INTO "03_notifications"."15_dtl_template_placeholders"
        (id, template_id, variable_key_code, is_required, default_value, created_at, updated_at)
    VALUES
        (gen_random_uuid(), _tpl_id, 'user.first_name', FALSE, 'there', NOW(), NOW()),
        (gen_random_uuid(), _tpl_id, 'otp_code', TRUE, NULL, NOW(), NOW())
    ON CONFLICT DO NOTHING;
END $$;

-- ──────────────────────────────────────────────────────────────────────────────
-- 4. Add otp_verified user property key (tracks whether user completed OTP)
-- ──────────────────────────────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."04_dim_user_property_keys"
    (id, code, name, description, data_type, is_pii, is_required, sort_order, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'otp_verified', 'OTP Verified', 'Whether the user has completed OTP verification during onboarding', 'boolean', FALSE, FALSE, 15, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ──────────────────────────────────────────────────────────────────────────────
-- 5. Backfill otp_verified = 'true' for ALL existing users so they are not disrupted
-- ──────────────────────────────────────────────────────────────────────────────
INSERT INTO "03_auth_manage"."05_dtl_user_properties" (id, user_id, property_key, property_value, created_by, updated_by, created_at, updated_at)
SELECT gen_random_uuid(), u.id, 'otp_verified', 'true', u.id, u.id, NOW(), NOW()
FROM "03_auth_manage"."03_fct_users" u
WHERE NOT EXISTS (
    SELECT 1 FROM "03_auth_manage"."05_dtl_user_properties" p
    WHERE p.user_id = u.id AND p.property_key = 'otp_verified'
);
