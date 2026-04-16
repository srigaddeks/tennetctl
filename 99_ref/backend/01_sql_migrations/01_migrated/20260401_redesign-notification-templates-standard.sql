-- =============================================================================
-- Migration: 20260401_redesign-notification-templates-standard.sql
-- Description: Redesigns the 3 existing invitation templates and the OTP
--              template to match the standard email design (white card,
--              4px blue top bar, centered logo, amber warning box, blue CTA).
--              All templates now follow the magic_link_assignee_email standard.
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- Template 1: workspace_invite_email — new version matching standard design
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_tmpl_id UUID := 'e1000000-0000-0000-0000-000000000001'::uuid;
    v_ver_id  UUID := 'e1000000-0000-0000-0000-000000000003'::uuid;
BEGIN
    -- Add static_variables for logo if not present
    UPDATE "03_notifications"."10_fct_templates"
    SET static_variables = '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb
    WHERE id = v_tmpl_id AND (static_variables IS NULL OR static_variables = '{}'::jsonb);

    -- Insert new version v2 with standard design
    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (
        v_ver_id, v_tmpl_id, 2,
        'You''ve been invited to join {{ invite.workspace_name | default("a workspace") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Workspace Invitation</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has invited you to join the workspace <strong>{{ invite.workspace_name | default("a workspace") }}</strong>{% if invite.org_name %} at <strong>{{ invite.org_name }}</strong>{% endif %}. Click the button below to accept your invitation and get started.</p>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This invitation expires in {{ invite.expires_in | default("72 hours") }}.</strong> If you were not expecting this invitation, you can safely ignore this email.
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

{{ actor.display_name | default("A team member") }} has invited you to join {{ invite.workspace_name | default("a workspace") }}{% if invite.org_name %} at {{ invite.org_name }}{% endif %}.

Accept here: {{ invite.accept_url }}

This invitation expires in {{ invite.expires_in | default("72 hours") }}. If unexpected, ignore this email.

Best regards,
Kreesalis Team$TEXT$,
        'Invited to {{ invite.workspace_name | default("a workspace") }}',
        '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', NOW()
    ) ON CONFLICT (id) DO NOTHING;

    -- Activate v2
    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ver_id, updated_at = NOW()
    WHERE id = v_tmpl_id;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- Template 2: workspace_invite_grc_email — new version matching standard design
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_tmpl_id UUID := 'e1000000-0000-0000-0000-000000000010'::uuid;
    v_ver_id  UUID := 'e1000000-0000-0000-0000-000000000012'::uuid;
BEGIN
    UPDATE "03_notifications"."10_fct_templates"
    SET static_variables = '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb
    WHERE id = v_tmpl_id AND (static_variables IS NULL OR static_variables = '{}'::jsonb);

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (
        v_ver_id, v_tmpl_id, 2,
        'GRC Access: {{ invite.grc_role_label | default("GRC Role") }} on {{ invite.workspace_name | default("K-Control") }}',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">GRC Role Assignment</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has invited you to <strong>{{ invite.workspace_name | default("a GRC workspace") }}</strong>{% if invite.org_name %} ({{ invite.org_name }}){% endif %} with the following access:</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Assigned Role</div>
        <div style="font-size:1.2em;font-weight:700;color:#0c4a6e;margin-bottom:12px;">{{ invite.grc_role_label | default("GRC Member") }}</div>
        {% if invite.workspace_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #e0f2fe;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Workspace</span><span style="color:#0369a1;font-weight:500;">{{ invite.workspace_name }}</span></div>{% endif %}
        {% if invite.framework_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #e0f2fe;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Framework</span><span style="color:#0369a1;font-weight:500;">{{ invite.framework_name }}</span></div>{% endif %}
        {% if invite.engagement_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #e0f2fe;font-size:0.9em;"><span style="color:#64748b;min-width:100px;">Engagement</span><span style="color:#0369a1;font-weight:500;">{{ invite.engagement_name }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This invitation expires in {{ invite.expires_in | default("72 hours") }}.</strong> If you were not expecting this, you can safely ignore this email.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Accept &amp; Access Platform</a>
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

{{ actor.display_name | default("A team member") }} has assigned you a GRC role on {{ invite.workspace_name | default("a workspace") }}{% if invite.org_name %} ({{ invite.org_name }}){% endif %}.

Role: {{ invite.grc_role_label | default("GRC Member") }}
{% if invite.framework_name %}Framework:  {{ invite.framework_name }}
{% endif %}{% if invite.engagement_name %}Engagement: {{ invite.engagement_name }}
{% endif %}
Accept here: {{ invite.accept_url }}

This invitation expires in {{ invite.expires_in | default("72 hours") }}.

Best regards,
Kreesalis Team$TEXT$,
        'GRC role: {{ invite.grc_role_label | default("GRC Member") }} on {{ invite.workspace_name | default("K-Control") }}',
        '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', NOW()
    ) ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ver_id, updated_at = NOW()
    WHERE id = v_tmpl_id;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- Template 3: engagement_access_granted_email — new version matching standard design
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_tmpl_id UUID := 'e1000000-0000-0000-0000-000000000020'::uuid;
    v_ver_id  UUID := 'e1000000-0000-0000-0000-000000000022'::uuid;
BEGIN
    UPDATE "03_notifications"."10_fct_templates"
    SET static_variables = '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb
    WHERE id = v_tmpl_id AND (static_variables IS NULL OR static_variables = '{}'::jsonb);

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (
        v_ver_id, v_tmpl_id, 2,
        'Engagement Access: {{ invite.engagement_name | default("Audit Engagement") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Audit Engagement Access</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>You have been granted access to an audit engagement on K-Control.{% if invite.org_name %} This engagement is managed by <strong>{{ invite.org_name }}</strong>.{% endif %}</p>
      </div>
      <div style="background:#f0fdf4;padding:18px 20px;border-radius:8px;border:1px solid #bbf7d0;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#15803d;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:4px;">Audit Engagement</div>
        <div style="font-size:1.2em;font-weight:700;color:#14532d;margin-bottom:12px;">{{ invite.engagement_name | default("Audit Engagement") }}</div>
        {% if invite.framework_name %}<div style="display:flex;padding:6px 0;border-top:1px solid #dcfce7;font-size:0.9em;"><span style="color:#64748b;min-width:110px;">Framework</span><span style="color:#166534;font-weight:500;">{{ invite.framework_name }}</span></div>{% endif %}
        {% if invite.grc_role_label %}<div style="display:flex;padding:6px 0;border-top:1px solid #dcfce7;font-size:0.9em;"><span style="color:#64748b;min-width:110px;">Your Role</span><span style="color:#166534;font-weight:500;">{{ invite.grc_role_label }}</span></div>{% endif %}
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>Your access remains active</strong> until the engagement is closed or your access is revoked. Contact the engagement lead with any questions.
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ invite.accept_url }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">Go to K-Control</a>
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

You have been granted access to an audit engagement on K-Control.
{% if invite.org_name %}Organisation: {{ invite.org_name }}
{% endif %}
Engagement: {{ invite.engagement_name | default("Audit Engagement") }}
{% if invite.framework_name %}Framework:   {{ invite.framework_name }}
{% endif %}{% if invite.grc_role_label %}Your Role:   {{ invite.grc_role_label }}
{% endif %}
Log in here: {{ invite.accept_url }}

Access remains active until the engagement is closed or revoked.

Best regards,
Kreesalis Team$TEXT$,
        'Access: {{ invite.engagement_name | default("Audit Engagement") }}',
        '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', NOW()
    ) ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ver_id, updated_at = NOW()
    WHERE id = v_tmpl_id;
END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- Template 4: email_verification_otp — new version with clean dollar-quoting
--             and standard design (keeps OTP box but matches overall structure)
-- ─────────────────────────────────────────────────────────────────────────────
DO $$
DECLARE
    v_ver_id  UUID := gen_random_uuid();
    v_tmpl_id UUID;
BEGIN
    SELECT id INTO v_tmpl_id
    FROM "03_notifications"."10_fct_templates"
    WHERE code = 'email_verification_otp' AND tenant_key = '__system__';

    IF v_tmpl_id IS NULL THEN
        RETURN;
    END IF;

    UPDATE "03_notifications"."10_fct_templates"
    SET static_variables = '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb
    WHERE id = v_tmpl_id AND (static_variables IS NULL OR static_variables = '{}'::jsonb);

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    SELECT
        v_ver_id, v_tmpl_id,
        COALESCE((SELECT MAX(version_number) FROM "03_notifications"."14_dtl_template_versions" WHERE template_id = v_tmpl_id), 0) + 1,
        'Your Verification Code — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Email Verification</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.first_name | default("there") }}</strong>,</p>
        <p>Use the verification code below to complete your email verification. This code expires in <strong>5 minutes</strong>.</p>
      </div>
      <div style="text-align:center;margin:28px 0;">
        <div style="display:inline-block;background:#eaf3fb;color:#295cf6;border-radius:10px;padding:18px 48px;font-size:2em;font-weight:700;letter-spacing:0.15em;">{{ otp_code }}</div>
      </div>
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>This code expires in 5 minutes.</strong> If you did not request this code, you can safely ignore this email.
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

Your K-Control verification code is:

{{ otp_code }}

This code expires in 5 minutes. If you did not request this, ignore this email.

Best regards,
Kreesalis Team$TEXT$,
        'Your verification code: {{ otp_code }}',
        '{}', 'Redesigned to match standard email template (white card, blue bar, centered logo)', NOW()
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ver_id, updated_at = NOW()
    WHERE id = v_tmpl_id;
END $$;

-- DOWN ========================================================================
-- Revert active_version_id to the previous (v1) version for each redesigned template
-- NOTE: This restores v1 as active but does not delete the new v2 version rows.

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = 'e1000000-0000-0000-0000-000000000002'::uuid, updated_at = NOW()
WHERE id = 'e1000000-0000-0000-0000-000000000001'::uuid;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = 'e1000000-0000-0000-0000-000000000011'::uuid, updated_at = NOW()
WHERE id = 'e1000000-0000-0000-0000-000000000010'::uuid;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = 'e1000000-0000-0000-0000-000000000021'::uuid, updated_at = NOW()
WHERE id = 'e1000000-0000-0000-0000-000000000020'::uuid;
