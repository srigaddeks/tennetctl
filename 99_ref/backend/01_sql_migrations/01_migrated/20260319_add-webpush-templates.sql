-- Web Push notification templates for all transactional notification types.
-- Each email template gets a matching web_push template with short body and deep-link support.
-- The service worker uses notification.data.url for deep-link navigation on click.

-- ──────────────────────────────────────────────────────────────────────────────
-- Password Reset — web_push template
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
        'password_reset_push',
        'Password Reset (Push)',
        'Web push notification sent when a password reset is requested.',
        'password_reset', 'web_push',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_short, body_text,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'Password Reset Requested',
        'A password reset link has been sent. Tap to open.',
        'Click to reset your password. This link expires in {{ action.expires_in }}.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;
END $$;

-- ──────────────────────────────────────────────────────────────────────────────
-- Email Verification — web_push template
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
        'email_verification_push',
        'Email Verification (Push)',
        'Web push notification sent to verify email address.',
        'email_verification', 'web_push',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_short, body_text,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'Verify Your Email',
        'Please verify your email address. Tap to open.',
        'Click the link to verify your email address.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;
END $$;

-- ──────────────────────────────────────────────────────────────────────────────
-- Login From New Device — web_push template
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
        'login_new_device_push',
        'New Device Login (Push)',
        'Security alert when login is detected from a new device.',
        'login_from_new_device', 'web_push',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_short, body_text,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'New Device Login Detected',
        'A new login was detected on your account. Tap to review.',
        'A login was detected from a new device. If this was not you, secure your account immediately.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;
END $$;

-- ──────────────────────────────────────────────────────────────────────────────
-- Org Invite — web_push template
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
        'org_invite_push',
        'Organisation Invite (Push)',
        'Web push notification when user is invited to an organisation.',
        'org_invite_received', 'web_push',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_short, body_text,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'You have been invited to an organisation',
        'You have a new organisation invitation. Tap to view.',
        'You have been invited to join an organisation on K-Control.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;
END $$;

-- ──────────────────────────────────────────────────────────────────────────────
-- Workspace Invite — web_push template
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
        'workspace_invite_push',
        'Workspace Invite (Push)',
        'Web push notification when user is added to a workspace.',
        'workspace_invite_received', 'web_push',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_short, body_text,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'You have been added to a workspace',
        'You have been added to a new workspace. Tap to open.',
        'You have been added to a workspace on K-Control.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;
END $$;

-- ──────────────────────────────────────────────────────────────────────────────
-- Global Broadcast — web_push template
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
        'global_broadcast_push',
        'Global Broadcast (Push)',
        'Web push notification for platform-wide announcements.',
        'global_broadcast', 'web_push',
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_short, body_text,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'K-Control Platform Announcement',
        'A new platform announcement is available.',
        'There is a new platform announcement from K-Control.',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;
END $$;
