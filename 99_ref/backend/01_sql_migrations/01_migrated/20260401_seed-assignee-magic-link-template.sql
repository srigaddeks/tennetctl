-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 20260401_seed-assignee-magic-link-template.sql
-- Description: Seeds the magic_link_assignee notification type and email
--              template for the assignee passwordless portal flow.
--              Also seeds magic_link_login_email template if missing (idempotent).
-- ─────────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. NOTIFICATION TYPE: magic_link_assignee
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO "03_notifications"."04_dim_notification_types"
    (id, code, name, description,
     category_code, is_mandatory, is_user_triggered,
     default_enabled, cooldown_seconds, sort_order,
     created_at, updated_at)
VALUES (
    'c0000000-0000-0000-0000-000000000021'::uuid,
    'magic_link_assignee',
    'Magic Link (Assignee Portal)',
    'Passwordless login link for assignee portal — sent to task assignees for one-click portal access',
    'security',
    TRUE, TRUE, TRUE, NULL, 21,
    NOW(), NOW()
)
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. CHANNEL SUPPORT
-- ─────────────────────────────────────────────────────────────────────────────
INSERT INTO "03_notifications"."07_dim_notification_channel_types"
    (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at)
VALUES
    ('f0000000-0000-0000-0000-000000000021'::uuid, 'magic_link_assignee', 'email', 'high', TRUE, NOW(), NOW())
ON CONFLICT (notification_type_code, channel_code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. EMAIL TEMPLATE: magic_link_assignee_email
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_tmpl_id UUID := 'e2000000-0000-0000-0000-000000000001'::uuid;
    v_ver_id  UUID := 'e2000000-0000-0000-0000-000000000002'::uuid;
BEGIN
    -- Step 1: insert template (active_version_id set after version is created)
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description,
         notification_type_code, channel_code,
         active_version_id, base_template_id,
         is_active, is_disabled, is_deleted, is_system,
         static_variables,
         created_at, updated_at)
    VALUES (
        v_tmpl_id, '__system__',
        'magic_link_assignee_email',
        'Magic Link — Assignee Portal',
        'Passwordless login link sent to task assignees for one-click portal access',
        'magic_link_assignee', 'email',
        NULL, NULL,
        TRUE, FALSE, FALSE, TRUE,
        '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb,
        NOW(), NOW()
    )
    ON CONFLICT (tenant_key, code) DO NOTHING;

    -- Step 2: insert version
    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (
        v_ver_id, v_tmpl_id, 1,
        'Your Task Portal Access Link — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Task Portal Access</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>You have been assigned a task on K-Control. Click the button below to access your task portal without a password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ magic_link.expires_in }}.</strong> If you did not expect this email, you can safely ignore it.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ magic_link.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Open Task Portal</a>
      </div>
      <div style="margin-top:24px;font-size:1em;">
        <span style="font-weight:600;">Best regards,</span><br>
        <span style="color:#295cf6;font-weight:700;">Kreesalis Team</span>
      </div>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:28px 0;">
      <div style="color:#888;font-size:0.9em;line-height:1.6;margin-bottom:4px;">
        <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.
      </div>
    </div>
  </div>
</body>
</html>$HTML$,
        $TEXT$Hi {{ user.first_name | default("there") }},

You have been assigned a task on K-Control.

Click here to access your task portal: {{ magic_link.url }}

This link expires in {{ magic_link.expires_in }}.

If you did not expect this email, you can safely ignore it.

Best regards,
Kreesalis Team$TEXT$,
        'Task portal: {{ magic_link.url }}',
        '{}', 'Initial version', NOW()
    )
    ON CONFLICT (id) DO NOTHING;

    -- Step 3: link active version
    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ver_id
    WHERE id = v_tmpl_id AND active_version_id IS NULL;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. ENSURE magic_link_login_email template exists (idempotent backfill)
--    These were seeded in staging but may be missing from dev if data was lost.
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_tmpl_id UUID := '1e421cc5-a30e-4d4e-ad1b-9ffb22f089de'::uuid;
    v_ver_id  UUID := '1073e024-0aa3-4251-a7fa-27e5e057cf93'::uuid;
BEGIN
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description,
         notification_type_code, channel_code,
         active_version_id, base_template_id,
         is_active, is_disabled, is_deleted, is_system,
         static_variables,
         created_at, updated_at)
    VALUES (
        v_tmpl_id, '__system__',
        'magic_link_login_email',
        'Magic Link Login',
        'Passwordless login link sent to user email',
        'magic_link_login', 'email',
        NULL, NULL,
        TRUE, FALSE, FALSE, TRUE,
        '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb,
        NOW(), NOW()
    )
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (
        v_ver_id, v_tmpl_id, 1,
        'Your Magic Link — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Magic Link Login</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We received a request to sign in to your K-Control account. Click the button below to log in securely without a password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ magic_link.expires_in }}.</strong> If you did not request this link, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ magic_link.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Sign In with Magic Link</a>
      </div>
      <div style="margin-top:24px;font-size:1em;">
        <span style="font-weight:600;">Best regards,</span><br>
        <span style="color:#295cf6;font-weight:700;">Kreesalis Team</span>
      </div>
      <hr style="border:none;border-top:1px solid #e8ecf1;margin:28px 0;">
      <div style="color:#888;font-size:0.9em;line-height:1.6;margin-bottom:4px;">
        <strong>Disclaimer:</strong> This email may contain confidential or proprietary information intended only for the recipient. If you are not the intended recipient, please delete this email immediately. Unauthorized copying, disclosure, or distribution is prohibited.
      </div>
    </div>
  </div>
</body>
</html>$HTML$,
        $TEXT$Hi {{ user.first_name }},

We received a request to sign in to your K-Control account.

Click here to sign in: {{ magic_link.url }}

This link expires in {{ magic_link.expires_in }}.

If you did not request this link, you can safely ignore this email.

Best regards,
Kreesalis Team$TEXT$,
        'Sign in: {{ magic_link.url }}',
        '{}', 'Initial version', NOW()
    )
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ver_id
    WHERE id = v_tmpl_id AND active_version_id IS NULL;
END $$;
