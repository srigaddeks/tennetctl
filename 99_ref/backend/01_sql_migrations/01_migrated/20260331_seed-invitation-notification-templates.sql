-- ─────────────────────────────────────────────────────────────────────────────
-- Migration: 20260331_seed-invitation-notification-templates.sql
-- Description: Email templates for workspace invitations (standard + GRC) and
--              engagement access grants. Seeds notification types, variable
--              keys, templates, versions, rules, and rule-channel bindings.
-- ─────────────────────────────────────────────────────────────────────────────

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. NEW NOTIFICATION TYPES
-- ─────────────────────────────────────────────────────────────────────────────

-- GRC workspace invitation (auditor / GRC role assigned)
INSERT INTO "03_notifications"."04_dim_notification_types"
    (id, code, name, description, category_code, is_mandatory, is_user_triggered, default_enabled, cooldown_seconds, sort_order, created_at, updated_at)
VALUES
    (
        'c0000000-0000-0000-0000-000000000030'::uuid,
        'workspace_invite_grc',
        'GRC Workspace Invitation',
        'Notification sent when a user is invited to a workspace with a GRC role (auditor, lead, engineer, etc.)',
        'engagement',
        FALSE, FALSE, TRUE, NULL, 30,
        NOW(), NOW()
    )
ON CONFLICT (code) DO NOTHING;

-- Engagement access granted (auditor provisioned to a specific engagement)
INSERT INTO "03_notifications"."04_dim_notification_types"
    (id, code, name, description, category_code, is_mandatory, is_user_triggered, default_enabled, cooldown_seconds, sort_order, created_at, updated_at)
VALUES
    (
        'c0000000-0000-0000-0000-000000000031'::uuid,
        'engagement_access_granted',
        'Engagement Access Granted',
        'Notification sent when a user is granted access to a specific audit engagement',
        'engagement',
        FALSE, FALSE, TRUE, NULL, 31,
        NOW(), NOW()
    )
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. CHANNEL SUPPORT FOR NEW TYPES
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."07_dim_notification_channel_types"
    (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at)
VALUES
    ('f0000000-0000-0000-0000-000000000030'::uuid, 'workspace_invite_grc',       'email',    'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000031'::uuid, 'workspace_invite_grc',       'web_push', 'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000032'::uuid, 'engagement_access_granted',  'email',    'high', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000033'::uuid, 'engagement_access_granted',  'web_push', 'high', TRUE, NOW(), NOW())
ON CONFLICT (notification_type_code, channel_code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. GRC-SPECIFIC VARIABLE KEYS (for use in templates)
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, resolution_source, preview_default, sort_order, created_at, updated_at)
VALUES
    ('a0000000-0000-0000-0030-000000000001'::uuid, 'invite.grc_role_code',    'GRC Role Code',          'Machine code for the GRC role (e.g. grc_lead_auditor)',          'audit_property', 'grc_lead_auditor',                            30, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000002'::uuid, 'invite.grc_role_label',   'GRC Role Label',         'Human-readable GRC role label (e.g. Lead Auditor)',               'audit_property', 'Lead Auditor',                                31, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000003'::uuid, 'invite.engagement_name',  'Engagement Name',        'Name of the audit engagement this invitation grants access to',   'audit_property', 'Q4 2025 SOC 2 Audit',                         32, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000004'::uuid, 'invite.framework_name',   'Framework Name',         'Framework name scoped to this invitation (e.g. SOC 2 Type II)',   'audit_property', 'SOC 2 Type II',                               33, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000005'::uuid, 'invite.accept_url',       'Invitation Accept URL',  'Full URL for the invitee to click and accept the invitation',      'audit_property', 'https://app.kcontrol.io/accept-invite?token=x', 34, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000006'::uuid, 'invite.expires_in',       'Invitation Expiry',      'Human-readable expiry string (e.g. 72 hours)',                    'audit_property', '72 hours',                                    35, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000007'::uuid, 'invite.workspace_name',   'Invite Workspace Name',  'Name of the workspace the user is being invited to',              'audit_property', 'Audit Workspace',                             36, NOW(), NOW()),
    ('a0000000-0000-0000-0030-000000000008'::uuid, 'invite.org_name',         'Invite Org Name',        'Name of the organisation associated with this invitation',         'audit_property', 'Acme Corp',                                   37, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. EMAIL TEMPLATES
--    Strategy: insert template with active_version_id = NULL, then insert
--    version, then update template to point at the version.
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    -- ── Workspace invite (standard) ──────────────────────────────────────────
    v_ws_invite_tmpl_id UUID := 'e1000000-0000-0000-0000-000000000001'::uuid;
    v_ws_invite_ver_id  UUID := 'e1000000-0000-0000-0000-000000000002'::uuid;

    -- ── Workspace invite (GRC) ───────────────────────────────────────────────
    v_grc_invite_tmpl_id UUID := 'e1000000-0000-0000-0000-000000000010'::uuid;
    v_grc_invite_ver_id  UUID := 'e1000000-0000-0000-0000-000000000011'::uuid;

    -- ── Engagement access granted ────────────────────────────────────────────
    v_eng_access_tmpl_id UUID := 'e1000000-0000-0000-0000-000000000020'::uuid;
    v_eng_access_ver_id  UUID := 'e1000000-0000-0000-0000-000000000021'::uuid;
BEGIN

    -- ────────────────────────────────────────────────────────────────────────
    -- Template 1: workspace_invite_email  (standard workspace invitation)
    -- Step 1: insert template with active_version_id = NULL
    -- ────────────────────────────────────────────────────────────────────────
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id,
         is_active, is_disabled, is_deleted, is_system,
         created_at, updated_at)
    VALUES
        (
            v_ws_invite_tmpl_id, '__system__',
            'workspace_invite_email', 'Workspace Invitation Email',
            'Sent when a user is invited to join a workspace',
            'workspace_invite_received', 'email',
            NULL, NULL,
            TRUE, FALSE, FALSE, TRUE,
            NOW(), NOW()
        )
    ON CONFLICT (tenant_key, code) DO NOTHING;

    -- Step 2: insert version
    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short, metadata_json, change_notes, created_at)
    VALUES (
        v_ws_invite_ver_id, v_ws_invite_tmpl_id, 1,
        'You have been invited to join {{ workspace.name | default("a workspace") }}',
        $HTML$<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Workspace Invitation</title>
  <style>
    body { margin:0; padding:0; background:#f4f4f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
    .wrapper { max-width:600px; margin:40px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    .header { background:#0f172a; padding:32px 40px; text-align:center; }
    .header h1 { margin:0; color:#fff; font-size:22px; font-weight:600; }
    .header p  { margin:6px 0 0; color:#94a3b8; font-size:13px; }
    .body  { padding:40px; }
    .body h2   { margin:0 0 12px; font-size:18px; font-weight:600; color:#0f172a; }
    .body p    { margin:0 0 16px; font-size:15px; color:#475569; line-height:1.6; }
    .cta  { display:block; margin:28px auto 0; padding:14px 32px; background:#0f172a; color:#fff; text-decoration:none; border-radius:6px; font-size:15px; font-weight:600; text-align:center; width:fit-content; }
    .meta { margin:28px 0 0; padding:20px; background:#f8fafc; border-radius:6px; border-left:3px solid #e2e8f0; }
    .meta p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
    .footer { padding:24px 40px; border-top:1px solid #e2e8f0; text-align:center; }
    .footer p { margin:0; font-size:12px; color:#94a3b8; }
    .footer a { color:#64748b; text-decoration:none; }
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>K-Control</h1>
    <p>Governance, Risk &amp; Compliance Platform</p>
  </div>
  <div class="body">
    <h2>You've been invited</h2>
    <p>Hi {{ user.display_name | default('there') }},</p>
    <p>
      <strong>{{ actor.display_name | default('A team member') }}</strong> has invited you to join
      the workspace <strong>{{ invite.workspace_name | default('a workspace') }}</strong>
      {% if invite.org_name %} at <strong>{{ invite.org_name }}</strong>{% endif %}.
    </p>
    <p>Click the button below to accept your invitation and get started.</p>
    <a href="{{ invite.accept_url }}" class="cta">Accept Invitation</a>
    <div class="meta">
      <p>This invitation expires in <strong>{{ invite.expires_in | default('72 hours') }}</strong>.
      If you were not expecting this invitation, you can safely ignore this email.</p>
    </div>
  </div>
  <div class="footer"><p>K-Control &mdash; <a href="{{ unsubscribe_url }}">Unsubscribe</a></p></div>
</div>
</body>
</html>$HTML$,
        $TEXT$You've been invited to join {{ invite.workspace_name | default('a workspace') }}{% if invite.org_name %} at {{ invite.org_name }}{% endif %}.

{{ actor.display_name | default('A team member') }} has invited you.

Accept here: {{ invite.accept_url }}

Expires in {{ invite.expires_in | default('72 hours') }}. If unexpected, ignore this email.$TEXT$,
        'Invited to {{ invite.workspace_name | default("a workspace") }}',
        '{}', 'Initial version', NOW()
    ) ON CONFLICT (id) DO NOTHING;

    -- Step 3: link active version
    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_ws_invite_ver_id
    WHERE id = v_ws_invite_tmpl_id AND active_version_id IS NULL;

    -- ────────────────────────────────────────────────────────────────────────
    -- Template 2: workspace_invite_grc_email  (GRC role invitation)
    -- ────────────────────────────────────────────────────────────────────────
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id,
         is_active, is_disabled, is_deleted, is_system,
         created_at, updated_at)
    VALUES
        (
            v_grc_invite_tmpl_id, '__system__',
            'workspace_invite_grc_email', 'GRC Workspace Invitation Email',
            'Sent when a user is invited to a workspace with a GRC role (auditor, lead, etc.)',
            'workspace_invite_grc', 'email',
            NULL, NULL,
            TRUE, FALSE, FALSE, TRUE,
            NOW(), NOW()
        )
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short, metadata_json, change_notes, created_at)
    VALUES (
        v_grc_invite_ver_id, v_grc_invite_tmpl_id, 1,
        'GRC Access: {{ invite.grc_role_label | default("GRC Role") }} on {{ invite.workspace_name | default("K-Control") }}',
        $HTML$<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>GRC Access Invitation</title>
  <style>
    body { margin:0; padding:0; background:#f4f4f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
    .wrapper { max-width:600px; margin:40px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    .header { background:#0f172a; padding:32px 40px; text-align:center; }
    .header h1 { margin:0; color:#fff; font-size:22px; font-weight:600; }
    .header .badge { display:inline-block; margin:10px 0 0; padding:4px 14px; background:#1e3a5f; color:#93c5fd; border-radius:20px; font-size:12px; font-weight:600; letter-spacing:.5px; text-transform:uppercase; }
    .body { padding:40px; }
    .body h2 { margin:0 0 12px; font-size:18px; font-weight:600; color:#0f172a; }
    .body p  { margin:0 0 16px; font-size:15px; color:#475569; line-height:1.6; }
    .role-card { margin:24px 0; padding:20px 24px; background:#f0f9ff; border-radius:8px; border:1px solid #bae6fd; }
    .role-card .role-title { font-size:13px; font-weight:600; color:#0369a1; text-transform:uppercase; letter-spacing:.5px; margin:0 0 4px; }
    .role-card .role-name  { font-size:18px; font-weight:700; color:#0c4a6e; margin:0 0 12px; }
    .scope-list { margin:0; padding:0; list-style:none; }
    .scope-list li { padding:7px 0; border-bottom:1px solid #e0f2fe; font-size:14px; color:#0369a1; display:flex; gap:8px; }
    .scope-list li:last-child { border-bottom:none; }
    .scope-list .lbl { color:#64748b; font-size:13px; min-width:100px; }
    .cta { display:block; margin:28px auto 0; padding:14px 32px; background:#0f172a; color:#fff; text-decoration:none; border-radius:6px; font-size:15px; font-weight:600; text-align:center; width:fit-content; }
    .meta { margin:28px 0 0; padding:20px; background:#f8fafc; border-radius:6px; border-left:3px solid #e2e8f0; }
    .meta p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
    .footer { padding:24px 40px; border-top:1px solid #e2e8f0; text-align:center; }
    .footer p { margin:0; font-size:12px; color:#94a3b8; }
    .footer a { color:#64748b; text-decoration:none; }
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>K-Control</h1>
    <div class="badge">GRC Access</div>
  </div>
  <div class="body">
    <h2>You've been assigned a GRC role</h2>
    <p>Hi {{ user.display_name | default('there') }},</p>
    <p>
      <strong>{{ actor.display_name | default('A team member') }}</strong> has invited you to
      <strong>{{ invite.workspace_name | default('a GRC workspace') }}</strong>
      {% if invite.org_name %}({{ invite.org_name }}){% endif %}
      with the following access:
    </p>
    <div class="role-card">
      <div class="role-title">Assigned Role</div>
      <div class="role-name">{{ invite.grc_role_label | default('GRC Member') }}</div>
      <ul class="scope-list">
        {% if invite.workspace_name %}<li><span class="lbl">Workspace</span>{{ invite.workspace_name }}</li>{% endif %}
        {% if invite.framework_name %}<li><span class="lbl">Framework</span>{{ invite.framework_name }}</li>{% endif %}
        {% if invite.engagement_name %}<li><span class="lbl">Engagement</span>{{ invite.engagement_name }}</li>{% endif %}
      </ul>
    </div>
    <p>Click below to accept and access the platform.</p>
    <a href="{{ invite.accept_url }}" class="cta">Accept &amp; Access Platform</a>
    <div class="meta">
      <p>This invitation expires in <strong>{{ invite.expires_in | default('72 hours') }}</strong>.
      If unexpected, you can safely ignore this email.</p>
    </div>
  </div>
  <div class="footer"><p>K-Control &mdash; <a href="{{ unsubscribe_url }}">Unsubscribe</a></p></div>
</div>
</body>
</html>$HTML$,
        $TEXT$You've been assigned a GRC role on {{ invite.workspace_name | default('a workspace') }}{% if invite.org_name %} ({{ invite.org_name }}){% endif %}.

Role: {{ invite.grc_role_label | default('GRC Member') }}
{% if invite.framework_name %}Framework:  {{ invite.framework_name }}
{% endif %}{% if invite.engagement_name %}Engagement: {{ invite.engagement_name }}
{% endif %}
Accept here: {{ invite.accept_url }}

Expires in {{ invite.expires_in | default('72 hours') }}.$TEXT$,
        'GRC role: {{ invite.grc_role_label | default("GRC Member") }} on {{ invite.workspace_name | default("K-Control") }}',
        '{}', 'Initial version', NOW()
    ) ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_grc_invite_ver_id
    WHERE id = v_grc_invite_tmpl_id AND active_version_id IS NULL;

    -- ────────────────────────────────────────────────────────────────────────
    -- Template 3: engagement_access_granted_email
    -- ────────────────────────────────────────────────────────────────────────
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id,
         is_active, is_disabled, is_deleted, is_system,
         created_at, updated_at)
    VALUES
        (
            v_eng_access_tmpl_id, '__system__',
            'engagement_access_granted_email', 'Engagement Access Granted Email',
            'Sent when an auditor is granted access to a specific audit engagement',
            'engagement_access_granted', 'email',
            NULL, NULL,
            TRUE, FALSE, FALSE, TRUE,
            NOW(), NOW()
        )
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short, metadata_json, change_notes, created_at)
    VALUES (
        v_eng_access_ver_id, v_eng_access_tmpl_id, 1,
        'Engagement Access: {{ invite.engagement_name | default("Audit Engagement") }} — {{ invite.org_name | default("K-Control") }}',
        $HTML$<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Engagement Access Granted</title>
  <style>
    body { margin:0; padding:0; background:#f4f4f5; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; }
    .wrapper { max-width:600px; margin:40px auto; background:#fff; border-radius:8px; overflow:hidden; box-shadow:0 1px 4px rgba(0,0,0,.08); }
    .header { background:#14532d; padding:32px 40px; text-align:center; }
    .header h1 { margin:0; color:#fff; font-size:22px; font-weight:600; }
    .header .badge { display:inline-block; margin:10px 0 0; padding:4px 14px; background:#166534; color:#86efac; border-radius:20px; font-size:12px; font-weight:600; letter-spacing:.5px; text-transform:uppercase; }
    .body { padding:40px; }
    .body h2 { margin:0 0 12px; font-size:18px; font-weight:600; color:#0f172a; }
    .body p  { margin:0 0 16px; font-size:15px; color:#475569; line-height:1.6; }
    .eng-card { margin:24px 0; padding:20px 24px; background:#f0fdf4; border-radius:8px; border:1px solid #bbf7d0; }
    .eng-card .eng-title { font-size:13px; font-weight:600; color:#15803d; text-transform:uppercase; letter-spacing:.5px; margin:0 0 4px; }
    .eng-card .eng-name  { font-size:18px; font-weight:700; color:#14532d; margin:0 0 12px; }
    .detail-row { display:flex; gap:8px; padding:6px 0; border-bottom:1px solid #dcfce7; font-size:14px; }
    .detail-row:last-child { border-bottom:none; }
    .detail-row .lbl { color:#64748b; font-size:13px; min-width:110px; }
    .detail-row .val { color:#166534; font-weight:500; }
    .cta { display:block; margin:28px auto 0; padding:14px 32px; background:#14532d; color:#fff; text-decoration:none; border-radius:6px; font-size:15px; font-weight:600; text-align:center; width:fit-content; }
    .meta { margin:28px 0 0; padding:20px; background:#f8fafc; border-radius:6px; border-left:3px solid #e2e8f0; }
    .meta p { margin:0; font-size:13px; color:#64748b; line-height:1.5; }
    .footer { padding:24px 40px; border-top:1px solid #e2e8f0; text-align:center; }
    .footer p { margin:0; font-size:12px; color:#94a3b8; }
    .footer a { color:#64748b; text-decoration:none; }
  </style>
</head>
<body>
<div class="wrapper">
  <div class="header">
    <h1>K-Control</h1>
    <div class="badge">Audit Access</div>
  </div>
  <div class="body">
    <h2>Engagement access granted</h2>
    <p>Hi {{ user.display_name | default('there') }},</p>
    <p>You have been granted access to an audit engagement on K-Control.
    {% if invite.org_name %}This engagement is managed by <strong>{{ invite.org_name }}</strong>.{% endif %}</p>
    <div class="eng-card">
      <div class="eng-title">Audit Engagement</div>
      <div class="eng-name">{{ invite.engagement_name | default('Audit Engagement') }}</div>
      {% if invite.framework_name %}
      <div class="detail-row"><span class="lbl">Framework</span><span class="val">{{ invite.framework_name }}</span></div>
      {% endif %}
      {% if invite.grc_role_label %}
      <div class="detail-row"><span class="lbl">Your Role</span><span class="val">{{ invite.grc_role_label }}</span></div>
      {% endif %}
    </div>
    <p>Log in to K-Control to view the engagement and begin your audit work.</p>
    <a href="{{ invite.accept_url }}" class="cta">Go to K-Control</a>
    <div class="meta">
      <p>Your access remains active until the engagement is closed or your access is revoked.
      Contact the engagement lead with any questions.</p>
    </div>
  </div>
  <div class="footer"><p>K-Control &mdash; <a href="{{ unsubscribe_url }}">Unsubscribe</a></p></div>
</div>
</body>
</html>$HTML$,
        $TEXT$Engagement access granted on K-Control.
{% if invite.org_name %}Organisation: {{ invite.org_name }}
{% endif %}
Engagement: {{ invite.engagement_name | default('Audit Engagement') }}
{% if invite.framework_name %}Framework:  {{ invite.framework_name }}
{% endif %}{% if invite.grc_role_label %}Your Role:  {{ invite.grc_role_label }}
{% endif %}
Log in here: {{ invite.accept_url }}

Access remains active until the engagement is closed or revoked.$TEXT$,
        'Access: {{ invite.engagement_name | default("Audit Engagement") }}',
        '{}', 'Initial version', NOW()
    ) ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_eng_access_ver_id
    WHERE id = v_eng_access_tmpl_id AND active_version_id IS NULL;

END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. NOTIFICATION RULES
-- ─────────────────────────────────────────────────────────────────────────────

-- Rule: workspace invite (standard) — invite_created, auth category
INSERT INTO "03_notifications"."11_fct_notification_rules"
    (id, tenant_key, code, name, description,
     source_event_type, source_event_category,
     notification_type_code, recipient_strategy,
     priority_code, is_active,
     created_at, updated_at)
VALUES
    (
        '30000000-0000-0000-0000-000000000020'::uuid,
        'default', 'rule_workspace_invite',
        'Workspace Invitation',
        'Notify invitee when a workspace invitation is created',
        'invite_created', 'auth',
        'workspace_invite_received', 'specific_users',
        'high', TRUE,
        NOW(), NOW()
    )
ON CONFLICT (tenant_key, code) DO NOTHING;

-- Rule: GRC workspace invite
INSERT INTO "03_notifications"."11_fct_notification_rules"
    (id, tenant_key, code, name, description,
     source_event_type, source_event_category,
     notification_type_code, recipient_strategy,
     priority_code, is_active,
     created_at, updated_at)
VALUES
    (
        '30000000-0000-0000-0000-000000000021'::uuid,
        'default', 'rule_workspace_invite_grc',
        'GRC Workspace Invitation',
        'Notify invitee when a workspace invitation with a GRC role is created',
        'invite_created', 'auth',
        'workspace_invite_grc', 'specific_users',
        'high', TRUE,
        NOW(), NOW()
    )
ON CONFLICT (tenant_key, code) DO NOTHING;

-- Rule: engagement access granted
INSERT INTO "03_notifications"."11_fct_notification_rules"
    (id, tenant_key, code, name, description,
     source_event_type, source_event_category,
     notification_type_code, recipient_strategy,
     priority_code, is_active,
     created_at, updated_at)
VALUES
    (
        '30000000-0000-0000-0000-000000000022'::uuid,
        'default', 'rule_engagement_access_granted',
        'Engagement Access Granted',
        'Notify user when audit engagement access is provisioned',
        'engagement_access_provisioned', 'auth',
        'engagement_access_granted', 'specific_users',
        'high', TRUE,
        NOW(), NOW()
    )
ON CONFLICT (tenant_key, code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. RULE CHANNEL BINDINGS
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."18_lnk_notification_rule_channels"
    (id, rule_id, channel_code, template_code, is_active, created_at, updated_at)
VALUES
    (
        'b0000000-0000-0000-0020-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000020'::uuid,
        'email', 'workspace_invite_email', TRUE, NOW(), NOW()
    ),
    (
        'b0000000-0000-0000-0021-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000021'::uuid,
        'email', 'workspace_invite_grc_email', TRUE, NOW(), NOW()
    ),
    (
        'b0000000-0000-0000-0022-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000022'::uuid,
        'email', 'engagement_access_granted_email', TRUE, NOW(), NOW()
    )
ON CONFLICT (rule_id, channel_code) DO NOTHING;
