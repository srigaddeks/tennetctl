-- =============================================================================
-- Migration: 20260402_seed-workflow-templates-part2.sql
-- Description: Email templates for workflow notifications: assessment completed,
--              engagement status changed, report ready/failed, approval
--              required/expired/rejected, and ticket assigned/status changed.
--              All templates follow the standard design (white card, 4px blue
--              bar, centered logo, amber info box, blue CTA, disclaimer).
-- =============================================================================

-- UP ==========================================================================

DO $$
DECLARE
    -- Template UUIDs (e5000000-* namespace for workflow templates, 0002 block)
    v_assessment_completed       UUID := 'e5000000-0000-0000-0002-000000000001'::uuid;
    v_engagement_status_changed  UUID := 'e5000000-0000-0000-0002-000000000002'::uuid;
    v_report_ready               UUID := 'e5000000-0000-0000-0002-000000000003'::uuid;
    v_report_failed              UUID := 'e5000000-0000-0000-0002-000000000004'::uuid;
    v_approval_required          UUID := 'e5000000-0000-0000-0002-000000000005'::uuid;
    v_approval_expired           UUID := 'e5000000-0000-0000-0002-000000000006'::uuid;
    v_approval_rejected          UUID := 'e5000000-0000-0000-0002-000000000007'::uuid;
    v_ticket_assigned            UUID := 'e5000000-0000-0000-0002-000000000008'::uuid;
    v_ticket_status_changed      UUID := 'e5000000-0000-0000-0002-000000000009'::uuid;

    v_logo JSONB := '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb;
    v_ver_id UUID;
BEGIN

-- =============================================================================
-- ASSESSMENT COMPLETED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_assessment_completed, 'default', 'assessment_completed_email', 'Assessment Completed Email',
    'Sent when an assessment reaches completed status.',
    'assessment_completed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_assessment_completed, 1,
    'Assessment Completed: {{ assessment.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Assessment Completed</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Assessment Completed</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An assessment has been completed. The results are now available for review.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">Completed</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ assessment.title | default('Untitled Assessment') }}</p>
            {% if assessment.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ assessment.type }}</p>{% endif %}
            {% if assessment.score %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Score: <strong>{{ assessment.score }}</strong></p>{% endif %}
            {% if assessment.completed_at %}<p style="margin:0;font-size:13px;color:#64748b;">Completed: {{ assessment.completed_at }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ assessment.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Results</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are a participant in this assessment in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Assessment Completed

Hi {{ user.first_name | default('there') }},

An assessment has been completed. The results are now available for review.

COMPLETED
Title: {{ assessment.title | default('Untitled Assessment') }}
{% if assessment.type %}Type: {{ assessment.type }}{% endif %}
{% if assessment.score %}Score: {{ assessment.score }}{% endif %}
{% if assessment.completed_at %}Completed: {{ assessment.completed_at }}{% endif %}

View the results: {{ assessment.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you are a participant in this assessment.$TEXT$,
    'Assessment Completed: {{ assessment.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_assessment_completed AND active_version_id IS NULL;

-- =============================================================================
-- ENGAGEMENT STATUS CHANGED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_engagement_status_changed, 'default', 'engagement_status_changed_email', 'Engagement Status Changed Email',
    'Sent to engagement participants when the engagement moves to a new phase.',
    'engagement_status_changed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_engagement_status_changed, 1,
    'Engagement Update: {{ engagement.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Engagement Update</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Engagement Phase Updated</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An engagement you are participating in has moved to a new phase.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Phase Update</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ engagement.title | default('Untitled Engagement') }}</p>
            {% if engagement.status.previous and engagement.status.new %}
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">
              <span style="color:#64748b;">{{ engagement.status.previous }}</span>
              <span style="color:#94a3b8;margin:0 6px;">→</span>
              <strong style="color:#1e293b;">{{ engagement.status.new }}</strong>
            </p>
            {% elif engagement.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">New phase: <strong>{{ engagement.status.new }}</strong></p>{% endif %}
            {% if engagement.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Target completion: <strong>{{ engagement.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ engagement.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Engagement</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are a participant in this engagement in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Engagement Phase Updated

Hi {{ user.first_name | default('there') }},

An engagement you are participating in has moved to a new phase.

PHASE UPDATE
Title: {{ engagement.title | default('Untitled Engagement') }}
{% if engagement.status.previous and engagement.status.new %}{{ engagement.status.previous }} → {{ engagement.status.new }}{% elif engagement.status.new %}New phase: {{ engagement.status.new }}{% endif %}
{% if engagement.due_date %}Target completion: {{ engagement.due_date }}{% endif %}

View the engagement: {{ engagement.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you are a participant in this engagement.$TEXT$,
    'Engagement Update: {{ engagement.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_engagement_status_changed AND active_version_id IS NULL;

-- =============================================================================
-- REPORT READY
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_report_ready, 'default', 'report_ready_email', 'Report Ready Email',
    'Sent when an AI-generated report has completed and is ready to view.',
    'report_ready', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_report_ready, 1,
    'Your Report Is Ready: {{ report.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Report Ready</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Report Is Ready</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Your AI-generated report has been completed and is ready for review.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">Report Completed</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ report.title | default('Untitled Report') }}</p>
            {% if report.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ report.type }}</p>{% endif %}
            {% if report.completed_at %}<p style="margin:0;font-size:13px;color:#64748b;">Generated: {{ report.completed_at }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ report.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Report</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because a report you requested is now ready in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Your Report Is Ready

Hi {{ user.first_name | default('there') }},

Your AI-generated report has been completed and is ready for review.

REPORT COMPLETED
Title: {{ report.title | default('Untitled Report') }}
{% if report.type %}Type: {{ report.type }}{% endif %}
{% if report.completed_at %}Generated: {{ report.completed_at }}{% endif %}

View the report: {{ report.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because a report you requested is now ready.$TEXT$,
    'Your Report Is Ready: {{ report.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_report_ready AND active_version_id IS NULL;

-- =============================================================================
-- REPORT FAILED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_report_failed, 'default', 'report_failed_email', 'Report Failed Email',
    'Sent when report generation fails so the user can retry.',
    'report_failed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_report_failed, 1,
    'Report Generation Failed: {{ report.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Report Failed</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#dc2626;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Report Generation Failed</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Unfortunately, your report could not be generated. You can retry from the reports page.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#991b1b;text-transform:uppercase;letter-spacing:0.05em;">Failed</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ report.title | default('Untitled Report') }}</p>
            {% if report.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ report.type }}</p>{% endif %}
            {% if report.error %}<p style="margin:0;font-size:13px;color:#dc2626;">Error: {{ report.error }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ report.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Retry Report</a>
          </td></tr>
        </table>
        <p style="margin:0 0 20px;font-size:14px;color:#64748b;line-height:1.6;">If this problem persists, please contact <a href="mailto:{{ platform.support_email | default('support@kcontrol.io') }}" style="color:#295cf6;text-decoration:none;">{{ platform.support_email | default('support@kcontrol.io') }}</a>.</p>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because a report you requested failed to generate in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Report Generation Failed

Hi {{ user.first_name | default('there') }},

Unfortunately, your report could not be generated. You can retry from the reports page.

FAILED
Title: {{ report.title | default('Untitled Report') }}
{% if report.type %}Type: {{ report.type }}{% endif %}
{% if report.error %}Error: {{ report.error }}{% endif %}

Retry the report: {{ report.url | default('#') }}

If this problem persists, please contact {{ platform.support_email | default('support@kcontrol.io') }}.

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because a report you requested failed to generate.$TEXT$,
    'Report Generation Failed: {{ report.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_report_failed AND active_version_id IS NULL;

-- =============================================================================
-- APPROVAL REQUIRED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_approval_required, 'default', 'approval_required_email', 'Approval Required Email',
    'Sent to the designated approver when an AI agent action requires human approval.',
    'approval_required', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_approval_required, 1,
    'Your Approval Is Required',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approval Required</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Approval Is Required</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An AI agent is requesting your approval before proceeding. Please review the proposed action and approve or reject it.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Pending Approval</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ approval.action | default('AI Agent Action') }}</p>
            {% if approval.agent %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Agent: {{ approval.agent }}</p>{% endif %}
            {% if approval.context %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Context: {{ approval.context }}</p>{% endif %}
            {% if approval.expires_at %}<p style="margin:0;font-size:13px;color:#92400e;font-weight:600;">Expires: {{ approval.expires_at }}</p>{% endif %}
          </td></tr>
        </table>
        {% if approval.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ approval.description }}</p>
        {% endif %}
        <p style="margin:0 0 16px;font-size:14px;color:#475569;">This request will expire if no action is taken before the deadline.</p>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ approval.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Review &amp; Approve</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are the designated approver for this AI agent action in {{ platform.name | default('K-Control') }}. This is a mandatory notification.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Your Approval Is Required

Hi {{ user.first_name | default('there') }},

An AI agent is requesting your approval before proceeding. Please review the proposed action and approve or reject it.

PENDING APPROVAL
Action: {{ approval.action | default('AI Agent Action') }}
{% if approval.agent %}Agent: {{ approval.agent }}{% endif %}
{% if approval.context %}Context: {{ approval.context }}{% endif %}
{% if approval.expires_at %}Expires: {{ approval.expires_at }}{% endif %}

{% if approval.description %}
{{ approval.description }}
{% endif %}

This request will expire if no action is taken before the deadline.

Review & Approve: {{ approval.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you are the designated approver for this AI agent action. This is a mandatory notification.$TEXT$,
    'Your Approval Is Required',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_approval_required AND active_version_id IS NULL;

-- =============================================================================
-- APPROVAL EXPIRED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_approval_expired, 'default', 'approval_expired_email', 'Approval Request Expired Email',
    'Sent to the requester when an approval times out without a response.',
    'approval_expired', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_approval_expired, 1,
    'Approval Request Expired',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approval Expired</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#f59e0b;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Approval Request Expired</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An approval request for your AI agent action expired before a response was received. The agent has been paused. You can submit a new approval request from the agents dashboard.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Expired Request</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ approval.action | default('AI Agent Action') }}</p>
            {% if approval.agent %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Agent: {{ approval.agent }}</p>{% endif %}
            {% if approval.expires_at %}<p style="margin:0;font-size:13px;color:#64748b;">Expired at: {{ approval.expires_at }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ approval.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Agent Dashboard</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because an approval request you initiated expired in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Approval Request Expired

Hi {{ user.first_name | default('there') }},

An approval request for your AI agent action expired before a response was received. The agent has been paused.

EXPIRED REQUEST
Action: {{ approval.action | default('AI Agent Action') }}
{% if approval.agent %}Agent: {{ approval.agent }}{% endif %}
{% if approval.expires_at %}Expired at: {{ approval.expires_at }}{% endif %}

View Agent Dashboard: {{ approval.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because an approval request you initiated expired.$TEXT$,
    'Approval Request Expired',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_approval_expired AND active_version_id IS NULL;

-- =============================================================================
-- APPROVAL REJECTED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_approval_rejected, 'default', 'approval_rejected_email', 'Approval Rejected Email',
    'Sent to the requester when their AI approval request is rejected by the approver.',
    'approval_rejected', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_approval_rejected, 1,
    'Approval Rejected',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Approval Rejected</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Approval Rejected</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Your AI agent approval request has been rejected. The agent has been paused. Review the reason below and adjust the configuration before resubmitting.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Rejected</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ approval.action | default('AI Agent Action') }}</p>
            {% if approval.agent %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Agent: {{ approval.agent }}</p>{% endif %}
            {% if approval.rejected_by %}<p style="margin:0;font-size:13px;color:#64748b;">Rejected by: {{ approval.rejected_by }}</p>{% endif %}
          </td></tr>
        </table>
        {% if approval.rejection_reason %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Reason</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ approval.rejection_reason }}</p>
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ approval.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Agent</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because your AI agent approval request was rejected in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Approval Rejected

Hi {{ user.first_name | default('there') }},

Your AI agent approval request has been rejected. The agent has been paused.

REJECTED
Action: {{ approval.action | default('AI Agent Action') }}
{% if approval.agent %}Agent: {{ approval.agent }}{% endif %}
{% if approval.rejected_by %}Rejected by: {{ approval.rejected_by }}{% endif %}

{% if approval.rejection_reason %}
REASON
{{ approval.rejection_reason }}
{% endif %}

View the agent: {{ approval.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because your AI agent approval request was rejected.$TEXT$,
    'Approval Rejected',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_approval_rejected AND active_version_id IS NULL;

-- =============================================================================
-- TICKET ASSIGNED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_ticket_assigned, 'default', 'ticket_assigned_email', 'Feedback Ticket Assigned Email',
    'Sent when a feedback/support ticket is assigned to a user.',
    'ticket_assigned', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_ticket_assigned, 1,
    'Support Ticket Assigned: {{ ticket.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ticket Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Support Ticket Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A support ticket has been assigned to you. Please review the details and respond to the submitter.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Ticket Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ ticket.title | default('Untitled Ticket') }}</p>
            {% if ticket.type %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Type: {{ ticket.type }}</p>{% endif %}
            {% if ticket.priority %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Priority: <strong>{{ ticket.priority }}</strong></p>{% endif %}
            {% if ticket.submitted_by %}<p style="margin:0;font-size:13px;color:#64748b;">Submitted by: {{ ticket.submitted_by }}</p>{% endif %}
          </td></tr>
        </table>
        {% if ticket.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ ticket.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ ticket.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Ticket</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because a support ticket was assigned to you in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Support Ticket Assigned to You

Hi {{ user.first_name | default('there') }},

A support ticket has been assigned to you. Please review the details and respond to the submitter.

TICKET DETAILS
Title: {{ ticket.title | default('Untitled Ticket') }}
{% if ticket.type %}Type: {{ ticket.type }}{% endif %}
{% if ticket.priority %}Priority: {{ ticket.priority }}{% endif %}
{% if ticket.submitted_by %}Submitted by: {{ ticket.submitted_by }}{% endif %}
{% if ticket.description %}
{{ ticket.description }}
{% endif %}

View the ticket: {{ ticket.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because a support ticket was assigned to you.$TEXT$,
    'Support Ticket Assigned: {{ ticket.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_ticket_assigned AND active_version_id IS NULL;

-- =============================================================================
-- TICKET STATUS CHANGED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_ticket_status_changed, 'default', 'ticket_status_changed_email', 'Ticket Status Changed Email',
    'Sent to the ticket submitter when the status of their ticket changes.',
    'ticket_status_changed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_ticket_status_changed, 1,
    'Update on Your Ticket: {{ ticket.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ticket Updated</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Ticket Has Been Updated</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">There has been an update to your support ticket. Please review the latest status below.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Status Update</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ ticket.title | default('Untitled Ticket') }}</p>
            {% if ticket.status.previous and ticket.status.new %}
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">
              <span style="color:#64748b;">{{ ticket.status.previous }}</span>
              <span style="color:#94a3b8;margin:0 6px;">→</span>
              <strong style="color:#1e293b;">{{ ticket.status.new }}</strong>
            </p>
            {% elif ticket.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Status: <strong>{{ ticket.status.new }}</strong></p>{% endif %}
            {% if ticket.assignee %}<p style="margin:0;font-size:13px;color:#64748b;">Assigned to: {{ ticket.assignee }}</p>{% endif %}
          </td></tr>
        </table>
        {% if comment.body %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Update Note</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ comment.body }}</p>
          {% if comment.author %}<p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">— {{ comment.author }}</p>{% endif %}
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ ticket.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Ticket</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you submitted this ticket in {{ platform.name | default('K-Control') }}. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Your Ticket Has Been Updated

Hi {{ user.first_name | default('there') }},

There has been an update to your support ticket.

STATUS UPDATE
Title: {{ ticket.title | default('Untitled Ticket') }}
{% if ticket.status.previous and ticket.status.new %}{{ ticket.status.previous }} → {{ ticket.status.new }}{% elif ticket.status.new %}Status: {{ ticket.status.new }}{% endif %}
{% if ticket.assignee %}Assigned to: {{ ticket.assignee }}{% endif %}

{% if comment.body %}
UPDATE NOTE
{{ comment.body }}
{% if comment.author %}— {{ comment.author }}{% endif %}
{% endif %}

View the ticket: {{ ticket.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you submitted this ticket.$TEXT$,
    'Update on Your Ticket: {{ ticket.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_ticket_status_changed AND active_version_id IS NULL;

END $$;

-- =============================================================================
-- NOTIFICATION RULES (outside DO block)
-- =============================================================================

INSERT INTO "03_notifications"."11_fct_notification_rules"
    (id, tenant_key, code, name, description,
     source_event_type, source_event_category,
     notification_type_code, recipient_strategy,
     priority_code, is_active, created_at, updated_at)
VALUES
    (
        'b5000000-0000-0000-0002-000000000001'::uuid,
        'default', 'rule_assessment_completed',
        'Assessment Completed',
        'Notify relevant parties when an assessment is completed',
        'assessment_completed', 'grc',
        'assessment_completed', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000002'::uuid,
        'default', 'rule_engagement_status_changed',
        'Engagement Status Changed',
        'Notify relevant parties when an engagement status changes',
        'engagement_status_changed', 'grc',
        'engagement_status_changed', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000003'::uuid,
        'default', 'rule_report_ready',
        'Report Ready',
        'Notify the requester when a report is ready to download',
        'report_ready', 'grc',
        'report_ready', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000004'::uuid,
        'default', 'rule_report_failed',
        'Report Generation Failed',
        'Notify the requester when report generation fails',
        'report_failed', 'grc',
        'report_failed', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000005'::uuid,
        'default', 'rule_approval_required',
        'Approval Required',
        'Notify the approver when an item requires their approval',
        'approval_required', 'grc',
        'approval_required', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000006'::uuid,
        'default', 'rule_approval_expired',
        'Approval Request Expired',
        'Notify the requester when an approval request expires',
        'approval_expired', 'grc',
        'approval_expired', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000007'::uuid,
        'default', 'rule_approval_rejected',
        'Approval Rejected',
        'Notify the requester when their approval request is rejected',
        'approval_rejected', 'grc',
        'approval_rejected', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000008'::uuid,
        'default', 'rule_ticket_assigned',
        'Feedback Ticket Assigned',
        'Notify the assignee when a feedback ticket is assigned to them',
        'ticket_assigned', 'grc',
        'ticket_assigned', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-000000000009'::uuid,
        'default', 'rule_ticket_status_changed',
        'Ticket Status Changed',
        'Notify the submitter when their ticket status changes',
        'ticket_status_changed', 'grc',
        'ticket_status_changed', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    )
ON CONFLICT (tenant_key, code) DO NOTHING;

-- =============================================================================
-- CHANNEL BINDINGS (outside DO block)
-- =============================================================================

INSERT INTO "03_notifications"."18_lnk_notification_rule_channels"
    (id, rule_id, channel_code, template_code, is_active, created_at, updated_at)
VALUES
    (
        'b5000000-0000-0000-0002-00000000b001'::uuid,
        'b5000000-0000-0000-0002-000000000001'::uuid,
        'email', 'assessment_completed_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b002'::uuid,
        'b5000000-0000-0000-0002-000000000002'::uuid,
        'email', 'engagement_status_changed_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b003'::uuid,
        'b5000000-0000-0000-0002-000000000003'::uuid,
        'email', 'report_ready_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b004'::uuid,
        'b5000000-0000-0000-0002-000000000004'::uuid,
        'email', 'report_failed_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b005'::uuid,
        'b5000000-0000-0000-0002-000000000005'::uuid,
        'email', 'approval_required_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b006'::uuid,
        'b5000000-0000-0000-0002-000000000006'::uuid,
        'email', 'approval_expired_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b007'::uuid,
        'b5000000-0000-0000-0002-000000000007'::uuid,
        'email', 'approval_rejected_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b008'::uuid,
        'b5000000-0000-0000-0002-000000000008'::uuid,
        'email', 'ticket_assigned_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0002-00000000b009'::uuid,
        'b5000000-0000-0000-0002-000000000009'::uuid,
        'email', 'ticket_status_changed_email', TRUE, NOW(), NOW()
    )
ON CONFLICT (rule_id, channel_code) DO NOTHING;

-- DOWN ========================================================================

DELETE FROM "03_notifications"."18_lnk_notification_rule_channels"
WHERE id IN (
    'b5000000-0000-0000-0002-00000000b001'::uuid,
    'b5000000-0000-0000-0002-00000000b002'::uuid,
    'b5000000-0000-0000-0002-00000000b003'::uuid,
    'b5000000-0000-0000-0002-00000000b004'::uuid,
    'b5000000-0000-0000-0002-00000000b005'::uuid,
    'b5000000-0000-0000-0002-00000000b006'::uuid,
    'b5000000-0000-0000-0002-00000000b007'::uuid,
    'b5000000-0000-0000-0002-00000000b008'::uuid,
    'b5000000-0000-0000-0002-00000000b009'::uuid
);

DELETE FROM "03_notifications"."11_fct_notification_rules"
WHERE id IN (
    'b5000000-0000-0000-0002-000000000001'::uuid,
    'b5000000-0000-0000-0002-000000000002'::uuid,
    'b5000000-0000-0000-0002-000000000003'::uuid,
    'b5000000-0000-0000-0002-000000000004'::uuid,
    'b5000000-0000-0000-0002-000000000005'::uuid,
    'b5000000-0000-0000-0002-000000000006'::uuid,
    'b5000000-0000-0000-0002-000000000007'::uuid,
    'b5000000-0000-0000-0002-000000000008'::uuid,
    'b5000000-0000-0000-0002-000000000009'::uuid
);

DELETE FROM "03_notifications"."14_dtl_template_versions"
WHERE template_id IN (
    'e5000000-0000-0000-0002-000000000001'::uuid,
    'e5000000-0000-0000-0002-000000000002'::uuid,
    'e5000000-0000-0000-0002-000000000003'::uuid,
    'e5000000-0000-0000-0002-000000000004'::uuid,
    'e5000000-0000-0000-0002-000000000005'::uuid,
    'e5000000-0000-0000-0002-000000000006'::uuid,
    'e5000000-0000-0000-0002-000000000007'::uuid,
    'e5000000-0000-0000-0002-000000000008'::uuid,
    'e5000000-0000-0000-0002-000000000009'::uuid
);

DELETE FROM "03_notifications"."10_fct_templates"
WHERE id IN (
    'e5000000-0000-0000-0002-000000000001'::uuid,
    'e5000000-0000-0000-0002-000000000002'::uuid,
    'e5000000-0000-0000-0002-000000000003'::uuid,
    'e5000000-0000-0000-0002-000000000004'::uuid,
    'e5000000-0000-0000-0002-000000000005'::uuid,
    'e5000000-0000-0000-0002-000000000006'::uuid,
    'e5000000-0000-0000-0002-000000000007'::uuid,
    'e5000000-0000-0000-0002-000000000008'::uuid,
    'e5000000-0000-0000-0002-000000000009'::uuid
);
