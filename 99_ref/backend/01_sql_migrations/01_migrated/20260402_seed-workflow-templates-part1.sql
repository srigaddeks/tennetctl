-- =============================================================================
-- Migration: 20260402_seed-workflow-templates-part1.sql
-- Description: Email templates for workflow notifications: tasks (reassigned,
--              overdue, submitted, approved, rejected), comments (mention,
--              reply), risks (assigned, review due, status changed, treatment
--              plan), and findings (assigned, response needed, reviewed).
--              All templates follow the standard design (white card, 4px blue
--              bar, centered logo, amber info box, blue CTA, disclaimer).
-- =============================================================================

-- UP ==========================================================================

DO $$
DECLARE
    -- Template UUIDs (e5000000-* namespace for workflow templates)
    v_task_reassigned       UUID := 'e5000000-0000-0000-0001-000000000001'::uuid;
    v_task_overdue          UUID := 'e5000000-0000-0000-0001-000000000002'::uuid;
    v_task_submitted        UUID := 'e5000000-0000-0000-0001-000000000003'::uuid;
    v_task_approved         UUID := 'e5000000-0000-0000-0001-000000000004'::uuid;
    v_task_rejected         UUID := 'e5000000-0000-0000-0001-000000000005'::uuid;
    v_comment_mention       UUID := 'e5000000-0000-0000-0001-000000000010'::uuid;
    v_comment_reply         UUID := 'e5000000-0000-0000-0001-000000000011'::uuid;
    v_risk_assigned         UUID := 'e5000000-0000-0000-0001-000000000020'::uuid;
    v_risk_review_due       UUID := 'e5000000-0000-0000-0001-000000000021'::uuid;
    v_risk_status_changed   UUID := 'e5000000-0000-0000-0001-000000000022'::uuid;
    v_treatment_assigned    UUID := 'e5000000-0000-0000-0001-000000000023'::uuid;
    v_finding_assigned      UUID := 'e5000000-0000-0000-0001-000000000030'::uuid;
    v_finding_response      UUID := 'e5000000-0000-0000-0001-000000000031'::uuid;
    v_finding_reviewed      UUID := 'e5000000-0000-0000-0001-000000000032'::uuid;

    v_logo JSONB := '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb;
    v_ver_id UUID;
BEGIN

-- =============================================================================
-- TASK REASSIGNED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_task_reassigned, 'default', 'task_reassigned_email', 'Task Reassigned Email',
    'Sent to the new assignee when a task is reassigned to them.',
    'task_reassigned', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_task_reassigned, 1,
    'Task Reassigned: {{ task.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Reassigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Reassigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A task has been reassigned to you. Please review the details below and take action before the due date.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Task Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default('Untitled Task') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Due: <strong>{{ task.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if task.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ task.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because a task was assigned to your account. If you believe this is an error, please contact <a href="mailto:{{ platform.support_email | default('support@kcontrol.io') }}" style="color:#295cf6;text-decoration:none;">{{ platform.support_email | default('support@kcontrol.io') }}</a>.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Task Reassigned to You

Hi {{ user.first_name | default('there') }},

A task has been reassigned to you. Please review the details and take action before the due date.

TASK DETAILS
Title: {{ task.title | default('Untitled Task') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Due: {{ task.due_date }}{% endif %}
{% if task.description %}
{{ task.description }}
{% endif %}

View the task: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because a task was assigned to your account.$TEXT$,
    'Task Reassigned: {{ task.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_task_reassigned AND active_version_id IS NULL;

-- =============================================================================
-- TASK OVERDUE
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_task_overdue, 'default', 'task_overdue_email', 'Task Overdue Email',
    'Sent to the assignee when a task passes its due date without being completed.',
    'task_overdue', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_task_overdue, 1,
    'Overdue Task: {{ task.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Overdue</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#dc2626;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Is Overdue</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">The following task has passed its due date and still requires your attention. Please complete or update it as soon as possible.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-left:4px solid #dc2626;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#991b1b;text-transform:uppercase;letter-spacing:0.05em;">Overdue Task</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default('Untitled Task') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#dc2626;font-weight:600;">Was due: {{ task.due_date }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Complete Task Now</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This is an automated overdue reminder from {{ platform.name | default('K-Control') }}. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Task Is Overdue

Hi {{ user.first_name | default('there') }},

The following task has passed its due date and still requires your attention.

OVERDUE TASK
Title: {{ task.title | default('Untitled Task') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Was due: {{ task.due_date }}{% endif %}

Complete the task: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This is an automated overdue reminder from {{ platform.name | default('K-Control') }}.$TEXT$,
    'Overdue Task: {{ task.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_task_overdue AND active_version_id IS NULL;

-- =============================================================================
-- TASK SUBMITTED FOR REVIEW
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_task_submitted, 'default', 'task_submitted_email', 'Task Submitted for Review Email',
    'Sent to reviewers when a task is moved to pending_verification status.',
    'task_submitted', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_task_submitted, 1,
    'Task Ready for Review: {{ task.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Ready for Review</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Awaiting Your Review</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A task has been submitted for review and is pending your approval. Please review the evidence and either approve or send it back for revision.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Pending Review</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default('Untitled Task') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Due: <strong>{{ task.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Review Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You are receiving this because you are a reviewer for this task. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Task Awaiting Your Review

Hi {{ user.first_name | default('there') }},

A task has been submitted for review and is pending your approval.

PENDING REVIEW
Title: {{ task.title | default('Untitled Task') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Due: {{ task.due_date }}{% endif %}

Review the task: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You are receiving this because you are a reviewer for this task.$TEXT$,
    'Task Ready for Review: {{ task.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_task_submitted AND active_version_id IS NULL;

-- =============================================================================
-- TASK APPROVED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_task_approved, 'default', 'task_approved_email', 'Task Approved Email',
    'Sent to the assignee when their task is approved and published.',
    'task_approved', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_task_approved, 1,
    'Task Approved: {{ task.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Approved</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Approved</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Great news — your task has been reviewed and approved. The evidence has been accepted and the task is now published.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f0fdf4;border-left:4px solid #22c55e;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#166534;text-transform:uppercase;letter-spacing:0.05em;">Approved</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default('Untitled Task') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because your task was reviewed and approved in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Task Approved

Hi {{ user.first_name | default('there') }},

Great news — your task has been reviewed and approved. The evidence has been accepted and the task is now published.

APPROVED
Title: {{ task.title | default('Untitled Task') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}

View the task: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because your task was reviewed and approved.$TEXT$,
    'Task Approved: {{ task.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_task_approved AND active_version_id IS NULL;

-- =============================================================================
-- TASK REJECTED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_task_rejected, 'default', 'task_rejected_email', 'Task Sent Back Email',
    'Sent to the assignee when their task is rejected and sent back for revision.',
    'task_rejected', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_task_rejected, 1,
    'Task Sent Back for Revision: {{ task.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Task Sent Back</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Task Sent Back for Revision</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">Your task has been reviewed and sent back for revision. Please review the feedback below and update your submission.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Needs Revision</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ task.title | default('Untitled Task') }}</p>
            {% if task.control_name %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Control: {{ task.control_name }}</p>{% endif %}
            {% if task.framework %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Framework: {{ task.framework }}</p>{% endif %}
            {% if task.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Due: <strong>{{ task.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if feedback.body %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Reviewer Feedback</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ feedback.body }}</p>
          {% if feedback.author %}<p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">— {{ feedback.author }}</p>{% endif %}
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Update Task</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This notification was sent because your task submission was returned for revision in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Task Sent Back for Revision

Hi {{ user.first_name | default('there') }},

Your task has been reviewed and sent back for revision. Please review the feedback and update your submission.

NEEDS REVISION
Title: {{ task.title | default('Untitled Task') }}
{% if task.control_name %}Control: {{ task.control_name }}{% endif %}
{% if task.framework %}Framework: {{ task.framework }}{% endif %}
{% if task.due_date %}Due: {{ task.due_date }}{% endif %}

{% if feedback.body %}
REVIEWER FEEDBACK
{{ feedback.body }}
{% if feedback.author %}— {{ feedback.author }}{% endif %}
{% endif %}

Update the task: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This notification was sent because your task submission was returned for revision.$TEXT$,
    'Task Sent Back for Revision: {{ task.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_task_rejected AND active_version_id IS NULL;

-- =============================================================================
-- COMMENT MENTION
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_comment_mention, 'default', 'comment_mention_email', 'Mentioned in Comment Email',
    'Sent when a user is @-mentioned in a comment.',
    'comment_mention', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_comment_mention, 1,
    '{{ comment.author | default(''Someone'') }} mentioned you in a comment',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>You Were Mentioned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">You Were Mentioned</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;"><strong>{{ comment.author | default('A team member') }}</strong> mentioned you in a comment{% if task.title %} on <strong>{{ task.title }}</strong>{% endif %}.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Comment</p>
            <p style="margin:0;font-size:15px;color:#1e293b;line-height:1.6;font-style:italic;">"{{ comment.body | default('') }}"</p>
            {% if comment.author %}<p style="margin:8px 0 0;font-size:13px;color:#64748b;">— {{ comment.author }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Comment</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were @-mentioned. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$You Were Mentioned

Hi {{ user.first_name | default('there') }},

{{ comment.author | default('A team member') }} mentioned you in a comment{% if task.title %} on {{ task.title }}{% endif %}.

COMMENT
"{{ comment.body | default('') }}"
{% if comment.author %}— {{ comment.author }}{% endif %}

View the comment: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you were @-mentioned. To manage your notification preferences, visit your account settings.$TEXT$,
    '{{ comment.author | default(''Someone'') }} mentioned you in a comment',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_comment_mention AND active_version_id IS NULL;

-- =============================================================================
-- COMMENT REPLY
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_comment_reply, 'default', 'comment_reply_email', 'Reply to Your Comment Email',
    'Sent when someone replies to your comment.',
    'comment_reply', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_comment_reply, 1,
    '{{ comment.author | default(''Someone'') }} replied to your comment',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>New Reply</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">New Reply to Your Comment</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;"><strong>{{ comment.author | default('A team member') }}</strong> replied to your comment{% if task.title %} on <strong>{{ task.title }}</strong>{% endif %}.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Reply</p>
            <p style="margin:0;font-size:15px;color:#1e293b;line-height:1.6;font-style:italic;">"{{ comment.body | default('') }}"</p>
            {% if comment.author %}<p style="margin:8px 0 0;font-size:13px;color:#64748b;">— {{ comment.author }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ task.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Conversation</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because someone replied to your comment. To manage your notification preferences, visit your account settings.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$New Reply to Your Comment

Hi {{ user.first_name | default('there') }},

{{ comment.author | default('A team member') }} replied to your comment{% if task.title %} on {{ task.title }}{% endif %}.

REPLY
"{{ comment.body | default('') }}"
{% if comment.author %}— {{ comment.author }}{% endif %}

View the conversation: {{ task.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because someone replied to your comment.$TEXT$,
    '{{ comment.author | default(''Someone'') }} replied to your comment',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_comment_reply AND active_version_id IS NULL;

-- =============================================================================
-- RISK ASSIGNED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_risk_assigned, 'default', 'risk_assigned_email', 'Risk Assigned Email',
    'Sent when a risk is assigned to a user as owner.',
    'risk_assigned', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_risk_assigned, 1,
    'Risk Assigned to You: {{ risk.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Risk Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Risk Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">You have been assigned as the owner of a risk. Please review the risk details and ensure appropriate treatment plans are in place.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Risk Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ risk.title | default('Untitled Risk') }}</p>
            {% if risk.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ risk.severity }}</strong></p>{% endif %}
            {% if risk.status %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Status: {{ risk.status }}</p>{% endif %}
            {% if risk.review_date %}<p style="margin:0;font-size:13px;color:#64748b;">Next review: <strong>{{ risk.review_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if risk.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ risk.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Risk</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were assigned as the risk owner in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Risk Assigned to You

Hi {{ user.first_name | default('there') }},

You have been assigned as the owner of a risk. Please review the details and ensure appropriate treatment plans are in place.

RISK DETAILS
Title: {{ risk.title | default('Untitled Risk') }}
{% if risk.severity %}Severity: {{ risk.severity }}{% endif %}
{% if risk.status %}Status: {{ risk.status }}{% endif %}
{% if risk.review_date %}Next review: {{ risk.review_date }}{% endif %}
{% if risk.description %}
{{ risk.description }}
{% endif %}

View the risk: {{ risk.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you were assigned as the risk owner.$TEXT$,
    'Risk Assigned to You: {{ risk.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_risk_assigned AND active_version_id IS NULL;

-- =============================================================================
-- RISK REVIEW DUE
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_risk_review_due, 'default', 'risk_review_due_email', 'Risk Review Due Email',
    'Sent when a risk is approaching its scheduled review date.',
    'risk_review_due', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_risk_review_due, 1,
    'Risk Review Due: {{ risk.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Risk Review Due</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Risk Review Due Soon</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">A risk you own is scheduled for review soon. Please assess the current risk status and update the treatment plan if necessary.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Review Reminder</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ risk.title | default('Untitled Risk') }}</p>
            {% if risk.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ risk.severity }}</strong></p>{% endif %}
            {% if risk.status %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Current Status: {{ risk.status }}</p>{% endif %}
            {% if risk.review_date %}<p style="margin:0;font-size:13px;color:#92400e;font-weight:600;">Review due: {{ risk.review_date }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Review Risk</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this scheduled reminder because you are the risk owner in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Risk Review Due Soon

Hi {{ user.first_name | default('there') }},

A risk you own is scheduled for review soon. Please assess the current status and update the treatment plan if necessary.

REVIEW REMINDER
Title: {{ risk.title | default('Untitled Risk') }}
{% if risk.severity %}Severity: {{ risk.severity }}{% endif %}
{% if risk.status %}Current Status: {{ risk.status }}{% endif %}
{% if risk.review_date %}Review due: {{ risk.review_date }}{% endif %}

Review the risk: {{ risk.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this scheduled reminder because you are the risk owner.$TEXT$,
    'Risk Review Due: {{ risk.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_risk_review_due AND active_version_id IS NULL;

-- =============================================================================
-- RISK STATUS CHANGED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_risk_status_changed, 'default', 'risk_status_changed_email', 'Risk Status Changed Email',
    'Sent to the risk owner when a risk status changes.',
    'risk_status_changed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_risk_status_changed, 1,
    'Risk Status Updated: {{ risk.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Risk Status Updated</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Risk Status Updated</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">The status of a risk you own has been updated.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Status Change</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ risk.title | default('Untitled Risk') }}</p>
            {% if risk.status.previous and risk.status.new %}
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">
              <span style="color:#64748b;">{{ risk.status.previous }}</span>
              <span style="color:#94a3b8;margin:0 6px;">→</span>
              <strong style="color:#1e293b;">{{ risk.status.new }}</strong>
            </p>
            {% elif risk.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">New status: <strong>{{ risk.status.new }}</strong></p>{% endif %}
            {% if risk.severity %}<p style="margin:0;font-size:13px;color:#64748b;">Severity: {{ risk.severity }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Risk</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are the owner of this risk in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Risk Status Updated

Hi {{ user.first_name | default('there') }},

The status of a risk you own has been updated.

STATUS CHANGE
Title: {{ risk.title | default('Untitled Risk') }}
{% if risk.status.previous and risk.status.new %}{{ risk.status.previous }} → {{ risk.status.new }}{% elif risk.status.new %}New status: {{ risk.status.new }}{% endif %}
{% if risk.severity %}Severity: {{ risk.severity }}{% endif %}

View the risk: {{ risk.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you are the owner of this risk.$TEXT$,
    'Risk Status Updated: {{ risk.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_risk_status_changed AND active_version_id IS NULL;

-- =============================================================================
-- TREATMENT PLAN ASSIGNED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_treatment_assigned, 'default', 'treatment_plan_assigned_email', 'Treatment Plan Assigned Email',
    'Sent to the treatment owner when a treatment plan is created and assigned.',
    'treatment_plan_assigned', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_treatment_assigned, 1,
    'Treatment Plan Assigned: {{ risk.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Treatment Plan Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Treatment Plan Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">You have been assigned as the owner of a risk treatment plan. Please review the treatment details and begin implementing the required controls.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Treatment Plan</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ treatment.title | default('Treatment Plan') }}</p>
            <p style="margin:0 0 4px;font-size:13px;color:#64748b;">Risk: {{ risk.title | default('Untitled Risk') }}</p>
            {% if risk.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Risk Severity: <strong>{{ risk.severity }}</strong></p>{% endif %}
            {% if treatment.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Target date: <strong>{{ treatment.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if treatment.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ treatment.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ risk.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Treatment Plan</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were assigned as the treatment owner in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Treatment Plan Assigned to You

Hi {{ user.first_name | default('there') }},

You have been assigned as the owner of a risk treatment plan.

TREATMENT PLAN
Title: {{ treatment.title | default('Treatment Plan') }}
Risk: {{ risk.title | default('Untitled Risk') }}
{% if risk.severity %}Risk Severity: {{ risk.severity }}{% endif %}
{% if treatment.due_date %}Target date: {{ treatment.due_date }}{% endif %}
{% if treatment.description %}
{{ treatment.description }}
{% endif %}

View the treatment plan: {{ risk.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you were assigned as the treatment owner.$TEXT$,
    'Treatment Plan Assigned: {{ risk.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_treatment_assigned AND active_version_id IS NULL;

-- =============================================================================
-- FINDING ASSIGNED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_finding_assigned, 'default', 'finding_assigned_email', 'Finding Assigned Email',
    'Sent when an audit finding is assigned to a user for remediation.',
    'finding_assigned', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_finding_assigned, 1,
    'Audit Finding Assigned: {{ finding.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Finding Assigned</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Audit Finding Assigned to You</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An audit finding has been assigned to you for remediation. Please review the finding and provide a response within the required timeframe.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Finding Details</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ finding.title | default('Untitled Finding') }}</p>
            {% if finding.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ finding.severity }}</strong></p>{% endif %}
            {% if finding.status %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Status: {{ finding.status }}</p>{% endif %}
            {% if finding.due_date %}<p style="margin:0;font-size:13px;color:#64748b;">Response due: <strong>{{ finding.due_date }}</strong></p>{% endif %}
          </td></tr>
        </table>
        {% if finding.description %}
        <p style="margin:0 0 24px;font-size:14px;color:#64748b;line-height:1.6;background:#f8fafc;padding:16px;border-radius:6px;">{{ finding.description }}</p>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ finding.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Finding</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you were assigned to remediate this finding in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Audit Finding Assigned to You

Hi {{ user.first_name | default('there') }},

An audit finding has been assigned to you for remediation.

FINDING DETAILS
Title: {{ finding.title | default('Untitled Finding') }}
{% if finding.severity %}Severity: {{ finding.severity }}{% endif %}
{% if finding.status %}Status: {{ finding.status }}{% endif %}
{% if finding.due_date %}Response due: {{ finding.due_date }}{% endif %}
{% if finding.description %}
{{ finding.description }}
{% endif %}

View the finding: {{ finding.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you were assigned to remediate this finding.$TEXT$,
    'Audit Finding Assigned: {{ finding.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_finding_assigned AND active_version_id IS NULL;

-- =============================================================================
-- FINDING RESPONSE NEEDED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_finding_response, 'default', 'finding_response_needed_email', 'Finding Response Needed Email',
    'Sent to prompt the assignee to respond to a finding in auditor_review status.',
    'finding_response_needed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_finding_response, 1,
    'Response Required: {{ finding.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Response Required</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Your Response Is Required</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">An audit finding assigned to you is now under auditor review and requires your formal response. Please provide your response as soon as possible.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Response Required</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ finding.title | default('Untitled Finding') }}</p>
            {% if finding.severity %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">Severity: <strong>{{ finding.severity }}</strong></p>{% endif %}
            {% if finding.due_date %}<p style="margin:0;font-size:13px;color:#92400e;font-weight:600;">Response due: {{ finding.due_date }}</p>{% endif %}
          </td></tr>
        </table>
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ finding.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">Respond to Finding</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">This is a reminder that your formal response is required for an audit finding in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Your Response Is Required

Hi {{ user.first_name | default('there') }},

An audit finding assigned to you is now under auditor review and requires your formal response.

RESPONSE REQUIRED
Title: {{ finding.title | default('Untitled Finding') }}
{% if finding.severity %}Severity: {{ finding.severity }}{% endif %}
{% if finding.due_date %}Response due: {{ finding.due_date }}{% endif %}

Respond to the finding: {{ finding.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
This is a reminder that your formal response is required for an audit finding.$TEXT$,
    'Response Required: {{ finding.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_finding_response AND active_version_id IS NULL;

-- =============================================================================
-- FINDING REVIEWED
-- =============================================================================
INSERT INTO "03_notifications"."10_fct_templates"
    (id, tenant_key, code, name, description, notification_type_code, channel_code,
     active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
     static_variables, created_at, updated_at)
VALUES (
    v_finding_reviewed, 'default', 'finding_reviewed_email', 'Finding Reviewed Email',
    'Sent to the finding owner after an auditor reviews and closes or escalates a finding.',
    'finding_reviewed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE,
    v_logo, NOW(), NOW()
) ON CONFLICT (tenant_key, code) DO NOTHING;

v_ver_id := gen_random_uuid();
INSERT INTO "03_notifications"."14_dtl_template_versions"
    (id, template_id, version_number, subject_line, body_html, body_text, body_short,
     metadata_json, change_notes, created_at)
VALUES (
    v_ver_id, v_finding_reviewed, 1,
    'Finding Reviewed: {{ finding.title }}',
    $HTML$<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Finding Reviewed</title></head>
<body style="margin:0;padding:0;background:#f8fafc;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#f8fafc;padding:40px 20px;">
  <tr><td align="center">
    <table width="720" cellpadding="0" cellspacing="0" style="max-width:720px;width:100%;background:#ffffff;border-radius:8px;box-shadow:0 1px 3px rgba(0,0,0,0.1);overflow:hidden;">
      <tr><td style="height:4px;background:#295cf6;font-size:0;">&nbsp;</td></tr>
      <tr><td style="padding:32px 40px 24px;text-align:center;">
        <img src="{{ platform.logo_url | default('https://assets.kcontrol.io/logo.png') }}" alt="{{ platform.name | default('K-Control') }}" height="36" style="display:block;margin:0 auto;">
      </td></tr>
      <tr><td style="padding:0 40px 32px;">
        <h1 style="margin:0 0 8px;font-size:22px;font-weight:700;color:#0f172a;">Audit Finding Reviewed</h1>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;">Hi {{ user.first_name | default('there') }},</p>
        <p style="margin:0 0 20px;font-size:15px;color:#475569;line-height:1.6;">The auditor has reviewed your finding. Please check the updated status and any reviewer notes below.</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #f59e0b;border-radius:0 6px 6px 0;margin:0 0 24px;padding:0;">
          <tr><td style="padding:16px 20px;">
            <p style="margin:0 0 6px;font-size:13px;font-weight:600;color:#92400e;text-transform:uppercase;letter-spacing:0.05em;">Auditor Decision</p>
            <p style="margin:0 0 4px;font-size:15px;font-weight:600;color:#1e293b;">{{ finding.title | default('Untitled Finding') }}</p>
            {% if finding.status.new %}<p style="margin:0 0 4px;font-size:13px;color:#64748b;">New status: <strong>{{ finding.status.new }}</strong></p>{% endif %}
            {% if finding.severity %}<p style="margin:0;font-size:13px;color:#64748b;">Severity: {{ finding.severity }}</p>{% endif %}
          </td></tr>
        </table>
        {% if comment.body %}
        <div style="background:#f8fafc;border-radius:6px;padding:16px 20px;margin:0 0 24px;">
          <p style="margin:0 0 8px;font-size:13px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;">Auditor Notes</p>
          <p style="margin:0;font-size:14px;color:#1e293b;line-height:1.6;">{{ comment.body }}</p>
          {% if comment.author %}<p style="margin:8px 0 0;font-size:12px;color:#94a3b8;">— {{ comment.author }}</p>{% endif %}
        </div>
        {% endif %}
        <table cellpadding="0" cellspacing="0" style="margin:0 0 28px;">
          <tr><td style="background:#295cf6;border-radius:6px;">
            <a href="{{ finding.url | default('#') }}" style="display:inline-block;padding:12px 28px;font-size:15px;font-weight:600;color:#ffffff;text-decoration:none;">View Finding</a>
          </td></tr>
        </table>
        <p style="margin:0 0 4px;font-size:14px;color:#475569;">Best regards,<br><strong>{{ platform.name | default('Kreesalis') }} Team</strong></p>
      </td></tr>
      <tr><td style="padding:20px 40px;border-top:1px solid #e2e8f0;background:#f8fafc;">
        <p style="margin:0;font-size:12px;color:#94a3b8;line-height:1.6;text-align:center;">You received this because you are the owner of this finding in {{ platform.name | default('K-Control') }}.</p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>$HTML$,
    $TEXT$Audit Finding Reviewed

Hi {{ user.first_name | default('there') }},

The auditor has reviewed your finding. Please check the updated status and any reviewer notes.

AUDITOR DECISION
Title: {{ finding.title | default('Untitled Finding') }}
{% if finding.status.new %}New status: {{ finding.status.new }}{% endif %}
{% if finding.severity %}Severity: {{ finding.severity }}{% endif %}

{% if comment.body %}
AUDITOR NOTES
{{ comment.body }}
{% if comment.author %}— {{ comment.author }}{% endif %}
{% endif %}

View the finding: {{ finding.url | default('#') }}

Best regards,
{{ platform.name | default('Kreesalis') }} Team

---
You received this because you are the owner of this finding.$TEXT$,
    'Finding Reviewed: {{ finding.title }}',
    '{}', 'Initial version', NOW()
) ON CONFLICT (id) DO NOTHING;

UPDATE "03_notifications"."10_fct_templates"
SET active_version_id = v_ver_id WHERE id = v_finding_reviewed AND active_version_id IS NULL;

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
        'b5000000-0000-0000-0001-000000000001'::uuid,
        'default', 'rule_task_reassigned',
        'Task Reassigned',
        'Notify the new assignee when a task is reassigned to them',
        'task_reassigned', 'grc',
        'task_reassigned', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000002'::uuid,
        'default', 'rule_task_overdue',
        'Task Overdue',
        'Notify the assignee when a task passes its due date',
        'task_overdue', 'grc',
        'task_overdue', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000003'::uuid,
        'default', 'rule_task_submitted',
        'Task Submitted for Review',
        'Notify reviewers when a task is submitted for verification',
        'task_submitted', 'grc',
        'task_submitted', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000004'::uuid,
        'default', 'rule_task_approved',
        'Task Approved',
        'Notify the assignee when their task is approved',
        'task_approved', 'grc',
        'task_approved', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000005'::uuid,
        'default', 'rule_task_rejected',
        'Task Sent Back for Revision',
        'Notify the assignee when their task is sent back for revision',
        'task_rejected', 'grc',
        'task_rejected', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000010'::uuid,
        'default', 'rule_comment_mention',
        'Comment Mention',
        'Notify a user when they are @-mentioned in a comment',
        'comment_mention', 'grc',
        'comment_mention', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000011'::uuid,
        'default', 'rule_comment_reply',
        'Comment Reply',
        'Notify a user when someone replies to their comment',
        'comment_reply', 'grc',
        'comment_reply', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000020'::uuid,
        'default', 'rule_risk_assigned',
        'Risk Assigned',
        'Notify the user when a risk is assigned to them as owner',
        'risk_assigned', 'grc',
        'risk_assigned', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000021'::uuid,
        'default', 'rule_risk_review_due',
        'Risk Review Due',
        'Notify the risk owner when a review is approaching',
        'risk_review_due', 'grc',
        'risk_review_due', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000022'::uuid,
        'default', 'rule_risk_status_changed',
        'Risk Status Changed',
        'Notify the risk owner when risk status is updated',
        'risk_status_changed', 'grc',
        'risk_status_changed', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000023'::uuid,
        'default', 'rule_treatment_plan_assigned',
        'Treatment Plan Assigned',
        'Notify the user when a risk treatment plan is assigned to them',
        'treatment_plan_assigned', 'grc',
        'treatment_plan_assigned', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000030'::uuid,
        'default', 'rule_finding_assigned',
        'Finding Assigned',
        'Notify the user when an audit finding is assigned to them',
        'finding_assigned', 'grc',
        'finding_assigned', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000031'::uuid,
        'default', 'rule_finding_response_needed',
        'Finding Response Needed',
        'Notify the assignee that a formal response is required for their finding',
        'finding_response_needed', 'grc',
        'finding_response_needed', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-000000000032'::uuid,
        'default', 'rule_finding_reviewed',
        'Finding Reviewed',
        'Notify the finding owner when the auditor has reviewed their finding',
        'finding_reviewed', 'grc',
        'finding_reviewed', 'specific_users',
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
        'b5000000-0000-0000-0001-00000000b001'::uuid,
        'b5000000-0000-0000-0001-000000000001'::uuid,
        'email', 'task_reassigned_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b002'::uuid,
        'b5000000-0000-0000-0001-000000000002'::uuid,
        'email', 'task_overdue_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b003'::uuid,
        'b5000000-0000-0000-0001-000000000003'::uuid,
        'email', 'task_submitted_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b004'::uuid,
        'b5000000-0000-0000-0001-000000000004'::uuid,
        'email', 'task_approved_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b005'::uuid,
        'b5000000-0000-0000-0001-000000000005'::uuid,
        'email', 'task_rejected_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b010'::uuid,
        'b5000000-0000-0000-0001-000000000010'::uuid,
        'email', 'comment_mention_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b011'::uuid,
        'b5000000-0000-0000-0001-000000000011'::uuid,
        'email', 'comment_reply_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b020'::uuid,
        'b5000000-0000-0000-0001-000000000020'::uuid,
        'email', 'risk_assigned_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b021'::uuid,
        'b5000000-0000-0000-0001-000000000021'::uuid,
        'email', 'risk_review_due_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b022'::uuid,
        'b5000000-0000-0000-0001-000000000022'::uuid,
        'email', 'risk_status_changed_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b023'::uuid,
        'b5000000-0000-0000-0001-000000000023'::uuid,
        'email', 'treatment_plan_assigned_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b030'::uuid,
        'b5000000-0000-0000-0001-000000000030'::uuid,
        'email', 'finding_assigned_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b031'::uuid,
        'b5000000-0000-0000-0001-000000000031'::uuid,
        'email', 'finding_response_needed_email', TRUE, NOW(), NOW()
    ),
    (
        'b5000000-0000-0000-0001-00000000b032'::uuid,
        'b5000000-0000-0000-0001-000000000032'::uuid,
        'email', 'finding_reviewed_email', TRUE, NOW(), NOW()
    )
ON CONFLICT (rule_id, channel_code) DO NOTHING;

-- DOWN ========================================================================

DELETE FROM "03_notifications"."18_lnk_notification_rule_channels"
WHERE id IN (
    'b5000000-0000-0000-0001-00000000b001'::uuid,
    'b5000000-0000-0000-0001-00000000b002'::uuid,
    'b5000000-0000-0000-0001-00000000b003'::uuid,
    'b5000000-0000-0000-0001-00000000b004'::uuid,
    'b5000000-0000-0000-0001-00000000b005'::uuid,
    'b5000000-0000-0000-0001-00000000b010'::uuid,
    'b5000000-0000-0000-0001-00000000b011'::uuid,
    'b5000000-0000-0000-0001-00000000b020'::uuid,
    'b5000000-0000-0000-0001-00000000b021'::uuid,
    'b5000000-0000-0000-0001-00000000b022'::uuid,
    'b5000000-0000-0000-0001-00000000b023'::uuid,
    'b5000000-0000-0000-0001-00000000b030'::uuid,
    'b5000000-0000-0000-0001-00000000b031'::uuid,
    'b5000000-0000-0000-0001-00000000b032'::uuid
);

DELETE FROM "03_notifications"."11_fct_notification_rules"
WHERE id IN (
    'b5000000-0000-0000-0001-000000000001'::uuid,
    'b5000000-0000-0000-0001-000000000002'::uuid,
    'b5000000-0000-0000-0001-000000000003'::uuid,
    'b5000000-0000-0000-0001-000000000004'::uuid,
    'b5000000-0000-0000-0001-000000000005'::uuid,
    'b5000000-0000-0000-0001-000000000010'::uuid,
    'b5000000-0000-0000-0001-000000000011'::uuid,
    'b5000000-0000-0000-0001-000000000020'::uuid,
    'b5000000-0000-0000-0001-000000000021'::uuid,
    'b5000000-0000-0000-0001-000000000022'::uuid,
    'b5000000-0000-0000-0001-000000000023'::uuid,
    'b5000000-0000-0000-0001-000000000030'::uuid,
    'b5000000-0000-0000-0001-000000000031'::uuid,
    'b5000000-0000-0000-0001-000000000032'::uuid
);

DELETE FROM "03_notifications"."14_dtl_template_versions"
WHERE template_id IN (
    'e5000000-0000-0000-0001-000000000001'::uuid,
    'e5000000-0000-0000-0001-000000000002'::uuid,
    'e5000000-0000-0000-0001-000000000003'::uuid,
    'e5000000-0000-0000-0001-000000000004'::uuid,
    'e5000000-0000-0000-0001-000000000005'::uuid,
    'e5000000-0000-0000-0001-000000000010'::uuid,
    'e5000000-0000-0000-0001-000000000011'::uuid,
    'e5000000-0000-0000-0001-000000000020'::uuid,
    'e5000000-0000-0000-0001-000000000021'::uuid,
    'e5000000-0000-0000-0001-000000000022'::uuid,
    'e5000000-0000-0000-0001-000000000023'::uuid,
    'e5000000-0000-0000-0001-000000000030'::uuid,
    'e5000000-0000-0000-0001-000000000031'::uuid,
    'e5000000-0000-0000-0001-000000000032'::uuid
);

DELETE FROM "03_notifications"."10_fct_templates"
WHERE id IN (
    'e5000000-0000-0000-0001-000000000001'::uuid,
    'e5000000-0000-0000-0001-000000000002'::uuid,
    'e5000000-0000-0000-0001-000000000003'::uuid,
    'e5000000-0000-0000-0001-000000000004'::uuid,
    'e5000000-0000-0000-0001-000000000005'::uuid,
    'e5000000-0000-0000-0001-000000000010'::uuid,
    'e5000000-0000-0000-0001-000000000011'::uuid,
    'e5000000-0000-0000-0001-000000000020'::uuid,
    'e5000000-0000-0000-0001-000000000021'::uuid,
    'e5000000-0000-0000-0001-000000000022'::uuid,
    'e5000000-0000-0000-0001-000000000023'::uuid,
    'e5000000-0000-0000-0001-000000000030'::uuid,
    'e5000000-0000-0000-0001-000000000031'::uuid,
    'e5000000-0000-0000-0001-000000000032'::uuid
);
