-- =============================================================================
-- Migration: 20260401_seed-missing-notification-templates.sql
-- Description: Seeds email templates for all notification types that currently
--              lack one. All templates follow the standard design:
--              white card, 4px blue top bar (#295cf6), centered logo,
--              amber warning/info box, blue CTA button, disclaimer footer.
--
--              Covers: password_reset, password_changed, login_from_new_device,
--              api_key_created, email_verified, org_invite_received,
--              org_member_added, org_member_removed, workspace_member_added,
--              workspace_member_removed, role_changed, inactivity_reminder,
--              platform_release, platform_incident, platform_maintenance.
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- Shared static variables shorthand — all system templates use this logo
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    -- ── Password Reset ───────────────────────────────────────────────────────
    v_pwd_reset_tmpl  UUID := 'e3000000-0000-0000-0000-000000000001'::uuid;
    v_pwd_reset_ver   UUID := 'e3000000-0000-0000-0000-000000000002'::uuid;

    -- ── Password Changed ─────────────────────────────────────────────────────
    v_pwd_chg_tmpl    UUID := 'e3000000-0000-0000-0000-000000000010'::uuid;
    v_pwd_chg_ver     UUID := 'e3000000-0000-0000-0000-000000000011'::uuid;

    -- ── Login From New Device ────────────────────────────────────────────────
    v_new_dev_tmpl    UUID := 'e3000000-0000-0000-0000-000000000020'::uuid;
    v_new_dev_ver     UUID := 'e3000000-0000-0000-0000-000000000021'::uuid;

    -- ── API Key Created ──────────────────────────────────────────────────────
    v_api_key_tmpl    UUID := 'e3000000-0000-0000-0000-000000000030'::uuid;
    v_api_key_ver     UUID := 'e3000000-0000-0000-0000-000000000031'::uuid;

    -- ── Email Verified ───────────────────────────────────────────────────────
    v_email_vfd_tmpl  UUID := 'e3000000-0000-0000-0000-000000000040'::uuid;
    v_email_vfd_ver   UUID := 'e3000000-0000-0000-0000-000000000041'::uuid;

    -- ── Org Invite Received ──────────────────────────────────────────────────
    v_org_inv_tmpl    UUID := 'e3000000-0000-0000-0000-000000000050'::uuid;
    v_org_inv_ver     UUID := 'e3000000-0000-0000-0000-000000000051'::uuid;

    -- ── Org Member Added ─────────────────────────────────────────────────────
    v_org_add_tmpl    UUID := 'e3000000-0000-0000-0000-000000000060'::uuid;
    v_org_add_ver     UUID := 'e3000000-0000-0000-0000-000000000061'::uuid;

    -- ── Org Member Removed ───────────────────────────────────────────────────
    v_org_rem_tmpl    UUID := 'e3000000-0000-0000-0000-000000000070'::uuid;
    v_org_rem_ver     UUID := 'e3000000-0000-0000-0000-000000000071'::uuid;

    -- ── Workspace Member Added ───────────────────────────────────────────────
    v_ws_add_tmpl     UUID := 'e3000000-0000-0000-0000-000000000080'::uuid;
    v_ws_add_ver      UUID := 'e3000000-0000-0000-0000-000000000081'::uuid;

    -- ── Workspace Member Removed ─────────────────────────────────────────────
    v_ws_rem_tmpl     UUID := 'e3000000-0000-0000-0000-000000000090'::uuid;
    v_ws_rem_ver      UUID := 'e3000000-0000-0000-0000-000000000091'::uuid;

    -- ── Role Changed ─────────────────────────────────────────────────────────
    v_role_chg_tmpl   UUID := 'e3000000-0000-0000-0000-0000000000a0'::uuid;
    v_role_chg_ver    UUID := 'e3000000-0000-0000-0000-0000000000a1'::uuid;

    -- ── Inactivity Reminder ──────────────────────────────────────────────────
    v_inact_tmpl      UUID := 'e3000000-0000-0000-0000-0000000000b0'::uuid;
    v_inact_ver       UUID := 'e3000000-0000-0000-0000-0000000000b1'::uuid;

    -- ── Platform Release ─────────────────────────────────────────────────────
    v_rel_tmpl        UUID := 'e3000000-0000-0000-0000-0000000000c0'::uuid;
    v_rel_ver         UUID := 'e3000000-0000-0000-0000-0000000000c1'::uuid;

    -- ── Platform Incident ────────────────────────────────────────────────────
    v_inc_tmpl        UUID := 'e3000000-0000-0000-0000-0000000000d0'::uuid;
    v_inc_ver         UUID := 'e3000000-0000-0000-0000-0000000000d1'::uuid;

    -- ── Platform Maintenance ─────────────────────────────────────────────────
    v_maint_tmpl      UUID := 'e3000000-0000-0000-0000-0000000000e0'::uuid;
    v_maint_ver       UUID := 'e3000000-0000-0000-0000-0000000000e1'::uuid;

    v_logo JSONB := '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb;
BEGIN

    -- =========================================================================
    -- 1. PASSWORD RESET
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_pwd_reset_tmpl, '__system__', 'password_reset_email', 'Password Reset Email',
        'Sent when a user requests a password reset link',
        'password_reset', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_pwd_reset_ver, v_pwd_reset_tmpl, 1,
        'Reset your K-Control password',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Password Reset</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We received a request to reset your K-Control password. Click the button below to choose a new password.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This link expires in {{ reset.expires_in | default("30 minutes") }}.</strong> If you did not request a password reset, you can safely ignore this email — your password will not change.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ reset.url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Reset Password</a>
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

We received a request to reset your K-Control password.

Click here to reset your password: {{ reset.url }}

This link expires in {{ reset.expires_in | default("30 minutes") }}. If you did not request this, ignore this email — your password will not change.

Best regards,
Kreesalis Team$TEXT$,
        'Reset your K-Control password: {{ reset.url }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_pwd_reset_ver WHERE id = v_pwd_reset_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 2. PASSWORD CHANGED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_pwd_chg_tmpl, '__system__', 'password_changed_email', 'Password Changed Email',
        'Sent to confirm a user''s password was successfully changed',
        'password_changed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_pwd_chg_ver, v_pwd_chg_tmpl, 1,
        'Your K-Control password was changed',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Password Changed</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Your K-Control account password was successfully changed on <strong>{{ event.occurred_at | default("just now") }}</strong>.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>If you did not make this change</strong>, please reset your password immediately and contact support. Your account security may be at risk.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ reset.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Reset Password</a>
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

Your K-Control password was successfully changed on {{ event.occurred_at | default("just now") }}.

If you did not make this change, please reset your password immediately: {{ reset.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Your K-Control password was changed',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_pwd_chg_ver WHERE id = v_pwd_chg_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 3. LOGIN FROM NEW DEVICE
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_new_dev_tmpl, '__system__', 'login_new_device_email', 'Login From New Device Email',
        'Security alert sent when a user logs in from an unrecognised device or location',
        'login_from_new_device', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_new_dev_ver, v_new_dev_tmpl, 1,
        'New sign-in to your K-Control account',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">New Device Sign-In</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We detected a sign-in to your K-Control account from a new device or location.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Sign-In Details</div>
        {% if event.occurred_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Time</span><span style="color:#0c4a6e;font-weight:500;">{{ event.occurred_at }}</span></div>{% endif %}
        {% if event.ip_address %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">IP Address</span><span style="color:#0c4a6e;font-weight:500;">{{ event.ip_address }}</span></div>{% endif %}
        {% if event.user_agent %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Device</span><span style="color:#0c4a6e;font-weight:500;">{{ event.user_agent }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>If this wasn't you</strong>, please reset your password immediately and contact our support team. Your account may be compromised.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ reset.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Secure My Account</a>
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

We detected a sign-in to your K-Control account from a new device or location.
{% if event.occurred_at %}Time:       {{ event.occurred_at }}
{% endif %}{% if event.ip_address %}IP Address: {{ event.ip_address }}
{% endif %}{% if event.user_agent %}Device:     {{ event.user_agent }}
{% endif %}
If this wasn't you, please reset your password immediately: {{ reset.url }}

Best regards,
Kreesalis Team$TEXT$,
        'New sign-in to your K-Control account',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_new_dev_ver WHERE id = v_new_dev_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 4. API KEY CREATED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_api_key_tmpl, '__system__', 'api_key_created_email', 'API Key Created Email',
        'Sent when a new API key is created for the user''s account',
        'api_key_created', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_api_key_ver, v_api_key_tmpl, 1,
        'New API key created — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">API Key Created</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>A new API key has been created for your K-Control account.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Key Details</div>
        {% if api_key.name %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Key Name</span><span style="color:#0c4a6e;font-weight:500;">{{ api_key.name }}</span></div>{% endif %}
        {% if api_key.prefix %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Prefix</span><span style="color:#0c4a6e;font-weight:500;font-family:monospace;">{{ api_key.prefix }}...</span></div>{% endif %}
        {% if event.occurred_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Created</span><span style="color:#0c4a6e;font-weight:500;">{{ event.occurred_at }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>If you did not create this key</strong>, please revoke it immediately in your account settings and contact our support team.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ settings.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Manage API Keys</a>
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

A new API key has been created for your K-Control account.
{% if api_key.name %}Key Name: {{ api_key.name }}
{% endif %}{% if api_key.prefix %}Prefix:   {{ api_key.prefix }}...
{% endif %}{% if event.occurred_at %}Created:  {{ event.occurred_at }}
{% endif %}
If you did not create this key, revoke it immediately in your account settings.

Best regards,
Kreesalis Team$TEXT$,
        'New API key created: {{ api_key.name | default("API Key") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_api_key_ver WHERE id = v_api_key_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 5. EMAIL VERIFIED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_email_vfd_tmpl, '__system__', 'email_verified_email', 'Email Verified Confirmation',
        'Sent to confirm that the user''s email address has been successfully verified',
        'email_verified', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_email_vfd_ver, v_email_vfd_tmpl, 1,
        'Your email address has been verified — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Email Verified</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Your email address has been successfully verified. Your K-Control account is fully active and ready to use.</p>
      </div>
      <div style="background:#f0fdf4;padding:14px 18px;border-radius:8px;border-left:4px solid #22c55e;margin:14px 0;">
        <strong>Verification complete.</strong> You can now access all features of the platform.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Dashboard</a>
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

Your K-Control email address has been successfully verified. Your account is fully active.

Go to your dashboard: {{ dashboard.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Email verified — your K-Control account is active',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_email_vfd_ver WHERE id = v_email_vfd_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 6. ORG INVITE RECEIVED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_org_inv_tmpl, '__system__', 'org_invite_email', 'Organisation Invitation Email',
        'Sent when a user is invited to join an organisation',
        'org_invite_received', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_org_inv_ver, v_org_inv_tmpl, 1,
        'You''ve been invited to join {{ invite.org_name | default("an organisation") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Organisation Invitation</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has invited you to join <strong>{{ invite.org_name | default("an organisation") }}</strong> on K-Control.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This invitation expires in {{ invite.expires_in | default("72 hours") }}.</strong> If you were not expecting this, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Accept Invitation</a>
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
        $TEXT$Hi {{ user.display_name | default("there") }},

{{ actor.display_name | default("A team member") }} has invited you to join {{ invite.org_name | default("an organisation") }} on K-Control.

Accept here: {{ invite.accept_url }}

This invitation expires in {{ invite.expires_in | default("72 hours") }}. If unexpected, ignore this email.

Best regards,
Kreesalis Team$TEXT$,
        'Invited to {{ invite.org_name | default("an organisation") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_org_inv_ver WHERE id = v_org_inv_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 7. ORG MEMBER ADDED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_org_add_tmpl, '__system__', 'org_member_added_email', 'Organisation Member Added Email',
        'Sent to confirm a user has joined an organisation',
        'org_member_added', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_org_add_ver, v_org_add_tmpl, 1,
        'Welcome to {{ org.name | default("your organisation") }} on K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Organisation Access Granted</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>You have been added to <strong>{{ org.name | default("your organisation") }}</strong> on K-Control with the role <strong>{{ member.role | default("member") }}</strong>.</p>
      </div>
      <div style="background:#f0fdf4;padding:14px 18px;border-radius:8px;border-left:4px solid #22c55e;margin:14px 0;">
        <strong>You now have access</strong> to the organisation's workspaces, resources, and team collaboration tools.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Dashboard</a>
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
        $TEXT$Hi {{ user.display_name | default("there") }},

You have been added to {{ org.name | default("your organisation") }} on K-Control with the role {{ member.role | default("member") }}.

Go to your dashboard: {{ dashboard.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Welcome to {{ org.name | default("your organisation") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_org_add_ver WHERE id = v_org_add_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 8. ORG MEMBER REMOVED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_org_rem_tmpl, '__system__', 'org_member_removed_email', 'Organisation Member Removed Email',
        'Sent to notify a user that they have been removed from an organisation',
        'org_member_removed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_org_rem_ver, v_org_rem_tmpl, 1,
        'Your access to {{ org.name | default("an organisation") }} has been removed — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Organisation Access Removed</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>Your membership in <strong>{{ org.name | default("your organisation") }}</strong> on K-Control has been removed.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>You no longer have access</strong> to this organisation's workspaces or resources. If you believe this is an error, please contact your organisation administrator.
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
        $TEXT$Hi {{ user.display_name | default("there") }},

Your membership in {{ org.name | default("your organisation") }} on K-Control has been removed.

You no longer have access to this organisation's workspaces or resources. If this is an error, contact your organisation administrator.

Best regards,
Kreesalis Team$TEXT$,
        'Access removed from {{ org.name | default("an organisation") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_org_rem_ver WHERE id = v_org_rem_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 9. WORKSPACE MEMBER ADDED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_ws_add_tmpl, '__system__', 'workspace_member_added_email', 'Workspace Member Added Email',
        'Sent to confirm a user has been added to a workspace',
        'workspace_member_added', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_ws_add_ver, v_ws_add_tmpl, 1,
        'You''ve been added to {{ workspace.name | default("a workspace") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Workspace Access Granted</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>You have been added to the workspace <strong>{{ workspace.name | default("a workspace") }}</strong>{% if org.name %} at <strong>{{ org.name }}</strong>{% endif %} with the role <strong>{{ member.role | default("member") }}</strong>.</p>
      </div>
      <div style="background:#f0fdf4;padding:14px 18px;border-radius:8px;border-left:4px solid #22c55e;margin:14px 0;">
        <strong>You now have access</strong> to this workspace and its resources.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ workspace.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Workspace</a>
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
        $TEXT$Hi {{ user.display_name | default("there") }},

You have been added to the workspace {{ workspace.name | default("a workspace") }}{% if org.name %} at {{ org.name }}{% endif %} with the role {{ member.role | default("member") }}.

Go to workspace: {{ workspace.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Added to {{ workspace.name | default("a workspace") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ws_add_ver WHERE id = v_ws_add_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 10. WORKSPACE MEMBER REMOVED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_ws_rem_tmpl, '__system__', 'workspace_member_removed_email', 'Workspace Member Removed Email',
        'Sent to notify a user that they have been removed from a workspace',
        'workspace_member_removed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_ws_rem_ver, v_ws_rem_tmpl, 1,
        'Your access to {{ workspace.name | default("a workspace") }} has been removed — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Workspace Access Removed</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>Your membership in the workspace <strong>{{ workspace.name | default("a workspace") }}</strong>{% if org.name %} at <strong>{{ org.name }}</strong>{% endif %} has been removed.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>You no longer have access</strong> to this workspace. If you believe this is an error, contact your workspace administrator.
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
        $TEXT$Hi {{ user.display_name | default("there") }},

Your membership in the workspace {{ workspace.name | default("a workspace") }}{% if org.name %} at {{ org.name }}{% endif %} has been removed.

If this is an error, contact your workspace administrator.

Best regards,
Kreesalis Team$TEXT$,
        'Access removed from {{ workspace.name | default("a workspace") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ws_rem_ver WHERE id = v_ws_rem_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 11. ROLE CHANGED
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_role_chg_tmpl, '__system__', 'role_changed_email', 'Role Changed Email',
        'Sent when a user''s role or permissions are changed',
        'role_changed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_role_chg_ver, v_role_chg_tmpl, 1,
        'Your role on K-Control has been updated',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Role Updated</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>Your role in <strong>{{ org.name | default("your organisation") }}</strong> has been updated by <strong>{{ actor.display_name | default("an administrator") }}</strong>.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Role Change</div>
        {% if role.previous %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Previous</span><span style="color:#64748b;font-weight:500;text-decoration:line-through;">{{ role.previous }}</span></div>{% endif %}
        {% if role.new %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">New Role</span><span style="color:#0c4a6e;font-weight:700;">{{ role.new }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        Your permissions have been updated accordingly. If you have questions about this change, contact your administrator.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to Dashboard</a>
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
        $TEXT$Hi {{ user.display_name | default("there") }},

Your role in {{ org.name | default("your organisation") }} has been updated by {{ actor.display_name | default("an administrator") }}.
{% if role.previous %}Previous role: {{ role.previous }}
{% endif %}{% if role.new %}New role:      {{ role.new }}
{% endif %}
If you have questions, contact your administrator.

Best regards,
Kreesalis Team$TEXT$,
        'Your role was updated to {{ role.new | default("a new role") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_role_chg_ver WHERE id = v_role_chg_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 12. INACTIVITY REMINDER
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_inact_tmpl, '__system__', 'inactivity_reminder_email', 'Inactivity Reminder Email',
        'Sent to re-engage users who have been inactive for a configurable period',
        'inactivity_reminder', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_inact_ver, v_inact_tmpl, 1,
        'We miss you — come back to K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">We Miss You</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>You haven't logged into K-Control in a while. Your team and workspaces are waiting for you.</p>
      </div>
      <div style="background:#f0f9ff;padding:14px 18px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        Log back in to stay up to date with your compliance controls, audit progress, and team activity.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ dashboard.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Return to K-Control</a>
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

You haven't logged into K-Control in a while. Your team and workspaces are waiting for you.

Return to K-Control: {{ dashboard.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Come back to K-Control',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_inact_ver WHERE id = v_inact_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 13. PLATFORM RELEASE
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_rel_tmpl, '__system__', 'platform_release_email', 'Platform Release Email',
        'Sent to announce a new platform release to users',
        'platform_release', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_rel_ver, v_rel_tmpl, 1,
        'K-Control {{ release.version | default("update") }} is now live',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">{{ release.title | default("New Release") }}</h2>
      {% if release.version %}<p style="color:#295cf6;font-size:0.9em;margin:4px 0 0 0;font-weight:600;">{{ release.version }}</p>{% endif %}
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>{{ release.summary | default("We have released a new version of K-Control with improvements and new features.") }}</p>
      </div>
      {% if release.changelog_url %}
      <div style="background:#f0f9ff;padding:14px 18px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        Read the full changelog for details on what's new in this release.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ release.changelog_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Read Changelog</a>
      </div>
      {% endif %}
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

{{ release.title | default("New Release") }}{% if release.version %} ({{ release.version }}){% endif %}

{{ release.summary | default("We have released a new version of K-Control.") }}
{% if release.changelog_url %}
Read the full changelog: {{ release.changelog_url }}
{% endif %}
Best regards,
Kreesalis Team$TEXT$,
        '{{ release.title | default("New release") }}{% if release.version %} ({{ release.version }}){% endif %}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_rel_ver WHERE id = v_rel_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 14. PLATFORM INCIDENT
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_inc_tmpl, '__system__', 'platform_incident_email', 'Platform Incident Email',
        'Sent to notify users of a platform incident or service disruption',
        'platform_incident', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_inc_ver, v_inc_tmpl, 1,
        '[{{ incident.severity | default("Incident") | upper }}] {{ incident.title | default("Platform Incident") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#dc2626;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Platform Incident</h2>
      {% if incident.severity %}<p style="color:#dc2626;font-size:0.9em;margin:4px 0 0 0;font-weight:700;text-transform:uppercase;">{{ incident.severity }}</p>{% endif %}
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>We are currently investigating an incident that may affect the K-Control platform.</p>
      </div>
      <div style="background:#fef2f2;padding:18px 20px;border-radius:8px;border:1px solid #fecaca;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#dc2626;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">{{ incident.title | default("Platform Incident") }}</div>
        <div style="font-size:0.95em;color:#7f1d1d;line-height:1.6;">{{ incident.description | default("We are investigating the issue and will provide updates.") }}</div>
        {% if incident.affected_components %}<div style="margin-top:10px;font-size:0.88em;color:#dc2626;"><strong>Affected:</strong> {{ incident.affected_components }}</div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        Our team is actively working to resolve this issue. We will send updates as the situation progresses.
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

[{{ incident.severity | default("INCIDENT") | upper }}] {{ incident.title | default("Platform Incident") }}

{{ incident.description | default("We are investigating an incident affecting the K-Control platform.") }}
{% if incident.affected_components %}Affected: {{ incident.affected_components }}
{% endif %}
Our team is actively working to resolve this. We will send updates as the situation progresses.

Best regards,
Kreesalis Team$TEXT$,
        '[{{ incident.severity | upper }}] {{ incident.title | default("Platform Incident") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_inc_ver WHERE id = v_inc_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- 15. PLATFORM MAINTENANCE
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_maint_tmpl, '__system__', 'platform_maintenance_email', 'Platform Maintenance Email',
        'Sent to notify users of planned platform maintenance windows',
        'platform_maintenance', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_maint_ver, v_maint_tmpl, 1,
        'Scheduled Maintenance — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#f59e0b;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Scheduled Maintenance</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>K-Control is scheduled for planned maintenance. During this window, the platform may be unavailable or experience degraded performance.</p>
      </div>
      <div style="background:#fffbeb;padding:18px 20px;border-radius:8px;border:1px solid #fde68a;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#b45309;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Maintenance Window</div>
        {% if maintenance.starts_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Starts</span><span style="color:#92400e;font-weight:500;">{{ maintenance.starts_at }}</span></div>{% endif %}
        {% if maintenance.ends_at %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Ends</span><span style="color:#92400e;font-weight:500;">{{ maintenance.ends_at }}</span></div>{% endif %}
        {% if maintenance.duration %}<div style="display:flex;padding:5px 0;font-size:0.9em;"><span style="color:#64748b;min-width:80px;">Duration</span><span style="color:#92400e;font-weight:500;">{{ maintenance.duration }}</span></div>{% endif %}
        {% if maintenance.description %}
        <div style="margin-top:10px;font-size:0.9em;color:#7f1d1d;line-height:1.5;">{{ maintenance.description }}</div>
        {% endif %}
      </div>
      <div style="background:#f5f7fa;padding:14px 18px;border-radius:8px;border-left:4px solid #94a3b8;margin:14px 0;">
        We apologise for any inconvenience. If you have questions, contact our support team.
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

K-Control is scheduled for planned maintenance. The platform may be unavailable during this window.
{% if maintenance.starts_at %}Starts:   {{ maintenance.starts_at }}
{% endif %}{% if maintenance.ends_at %}Ends:     {{ maintenance.ends_at }}
{% endif %}{% if maintenance.duration %}Duration: {{ maintenance.duration }}
{% endif %}{% if maintenance.description %}
{{ maintenance.description }}
{% endif %}
We apologise for any inconvenience.

Best regards,
Kreesalis Team$TEXT$,
        'Scheduled maintenance: {% if maintenance.starts_at %}{{ maintenance.starts_at }}{% else %}upcoming{% endif %}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_maint_ver WHERE id = v_maint_tmpl AND active_version_id IS NULL;

END $$;

-- DOWN ========================================================================
-- Delete template versions and templates inserted by this migration.
-- Templates with no versions will be left inactive (idempotent cleanup).

DELETE FROM "03_notifications"."14_dtl_template_versions"
WHERE id IN (
    'e3000000-0000-0000-0000-000000000002'::uuid,
    'e3000000-0000-0000-0000-000000000011'::uuid,
    'e3000000-0000-0000-0000-000000000021'::uuid,
    'e3000000-0000-0000-0000-000000000031'::uuid,
    'e3000000-0000-0000-0000-000000000041'::uuid,
    'e3000000-0000-0000-0000-000000000051'::uuid,
    'e3000000-0000-0000-0000-000000000061'::uuid,
    'e3000000-0000-0000-0000-000000000071'::uuid,
    'e3000000-0000-0000-0000-000000000081'::uuid,
    'e3000000-0000-0000-0000-000000000091'::uuid,
    'e3000000-0000-0000-0000-0000000000a1'::uuid,
    'e3000000-0000-0000-0000-0000000000b1'::uuid,
    'e3000000-0000-0000-0000-0000000000c1'::uuid,
    'e3000000-0000-0000-0000-0000000000d1'::uuid,
    'e3000000-0000-0000-0000-0000000000e1'::uuid
);

DELETE FROM "03_notifications"."10_fct_templates"
WHERE id IN (
    'e3000000-0000-0000-0000-000000000001'::uuid,
    'e3000000-0000-0000-0000-000000000010'::uuid,
    'e3000000-0000-0000-0000-000000000020'::uuid,
    'e3000000-0000-0000-0000-000000000030'::uuid,
    'e3000000-0000-0000-0000-000000000040'::uuid,
    'e3000000-0000-0000-0000-000000000050'::uuid,
    'e3000000-0000-0000-0000-000000000060'::uuid,
    'e3000000-0000-0000-0000-000000000070'::uuid,
    'e3000000-0000-0000-0000-000000000080'::uuid,
    'e3000000-0000-0000-0000-000000000090'::uuid,
    'e3000000-0000-0000-0000-0000000000a0'::uuid,
    'e3000000-0000-0000-0000-0000000000b0'::uuid,
    'e3000000-0000-0000-0000-0000000000c0'::uuid,
    'e3000000-0000-0000-0000-0000000000d0'::uuid,
    'e3000000-0000-0000-0000-0000000000e0'::uuid
);
