-- =============================================================================
-- Migration: 20260401_seed-grc-notification-templates.sql
-- Description: Seeds GRC-specific notification types and email templates for
--              task workflows: task assignment, task status change, comment
--              added, and feedback received. All templates follow the standard
--              design (white card, 4px blue bar, centered logo, amber info
--              box, blue CTA, disclaimer footer).
-- =============================================================================

-- UP ==========================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- 1. NEW NOTIFICATION TYPES
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."04_dim_notification_types"
    (id, code, name, description, category_code, is_mandatory, is_user_triggered,
     default_enabled, cooldown_seconds, sort_order, created_at, updated_at)
VALUES
    (
        'c0000000-0000-0000-0000-000000000040'::uuid,
        'task_assigned',
        'Task Assigned',
        'Notification sent when a task is assigned to a user',
        'engagement', FALSE, FALSE, TRUE, NULL, 40,
        NOW(), NOW()
    ),
    (
        'c0000000-0000-0000-0000-000000000041'::uuid,
        'task_status_changed',
        'Task Status Changed',
        'Notification sent when the status of a task the user owns or follows changes',
        'engagement', FALSE, FALSE, TRUE, 300, 41,
        NOW(), NOW()
    ),
    (
        'c0000000-0000-0000-0000-000000000042'::uuid,
        'task_comment_added',
        'Comment Added to Task',
        'Notification sent when a new comment is added to a task the user is involved with',
        'engagement', FALSE, FALSE, TRUE, 60, 42,
        NOW(), NOW()
    ),
    (
        'c0000000-0000-0000-0000-000000000043'::uuid,
        'task_feedback_received',
        'Task Feedback Received',
        'Notification sent when feedback is submitted on a task or control evidence',
        'engagement', FALSE, FALSE, TRUE, NULL, 43,
        NOW(), NOW()
    )
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 2. CHANNEL SUPPORT
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."07_dim_notification_channel_types"
    (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at)
VALUES
    ('f0000000-0000-0000-0000-000000000040'::uuid, 'task_assigned',        'email',    'high',   TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000041'::uuid, 'task_assigned',        'web_push', 'high',   TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000042'::uuid, 'task_status_changed',  'email',    'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000043'::uuid, 'task_status_changed',  'web_push', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000044'::uuid, 'task_comment_added',   'email',    'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000045'::uuid, 'task_comment_added',   'web_push', 'normal', TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000046'::uuid, 'task_feedback_received','email',   'high',   TRUE, NOW(), NOW()),
    ('f0000000-0000-0000-0000-000000000047'::uuid, 'task_feedback_received','web_push','high',   TRUE, NOW(), NOW())
ON CONFLICT (notification_type_code, channel_code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 3. GRC TASK VARIABLE KEYS
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, resolution_source, preview_default, sort_order, created_at, updated_at)
VALUES
    ('a0000000-0000-0000-0040-000000000001'::uuid, 'task.title',         'Task Title',          'Title of the task',                                     'audit_property', 'Review Q4 Controls Evidence',    40, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000002'::uuid, 'task.description',   'Task Description',    'Brief description of the task',                         'audit_property', 'Please review and upload the required evidence for SOC 2 controls.', 41, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000003'::uuid, 'task.due_date',      'Task Due Date',       'Due date of the task (human-readable)',                  'audit_property', 'April 15, 2026',                 42, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000004'::uuid, 'task.url',           'Task URL',            'Direct URL to the task in K-Control',                   'audit_property', 'https://app.kcontrol.io/tasks/x', 43, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000005'::uuid, 'task.status.new',    'Task New Status',     'The new status of the task after the change',           'audit_property', 'In Review',                      44, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000006'::uuid, 'task.status.previous','Task Previous Status','The previous status before the change',                'audit_property', 'In Progress',                    45, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000007'::uuid, 'task.priority',      'Task Priority',       'Priority level of the task (high, medium, low)',        'audit_property', 'high',                           46, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000008'::uuid, 'comment.body',       'Comment Body',        'The text content of the new comment',                   'audit_property', 'Please ensure the evidence covers the full audit period.', 47, NOW(), NOW()),
    ('a0000000-0000-0000-0040-000000000009'::uuid, 'comment.author',     'Comment Author',      'Display name of the person who added the comment',      'audit_property', 'Sarah Chen',                     48, NOW(), NOW()),
    ('a0000000-0000-0000-0040-00000000000a'::uuid, 'feedback.body',      'Feedback Body',       'The text content of the feedback',                      'audit_property', 'The evidence provided is incomplete. Please include the full policy document.', 49, NOW(), NOW()),
    ('a0000000-0000-0000-0040-00000000000b'::uuid, 'feedback.author',    'Feedback Author',     'Display name of the person who submitted the feedback', 'audit_property', 'Alex Torres',                    50, NOW(), NOW()),
    ('a0000000-0000-0000-0040-00000000000c'::uuid, 'feedback.type',      'Feedback Type',       'Type of feedback (approved, rejected, needs_revision)', 'audit_property', 'needs_revision',                 51, NOW(), NOW()),
    ('a0000000-0000-0000-0040-00000000000d'::uuid, 'task.control_name',  'Control Name',        'Name of the compliance control associated with the task','audit_property','CC6.1 – Logical Access Controls', 52, NOW(), NOW()),
    ('a0000000-0000-0000-0040-00000000000e'::uuid, 'task.framework',     'Framework',           'Compliance framework associated with this task',        'audit_property', 'SOC 2 Type II',                  53, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 4. EMAIL TEMPLATES
-- ─────────────────────────────────────────────────────────────────────────────

DO $$
DECLARE
    v_assigned_tmpl   UUID := 'e4000000-0000-0000-0000-000000000001'::uuid;
    v_assigned_ver    UUID := 'e4000000-0000-0000-0000-000000000002'::uuid;

    v_status_tmpl     UUID := 'e4000000-0000-0000-0000-000000000010'::uuid;
    v_status_ver      UUID := 'e4000000-0000-0000-0000-000000000011'::uuid;

    v_comment_tmpl    UUID := 'e4000000-0000-0000-0000-000000000020'::uuid;
    v_comment_ver     UUID := 'e4000000-0000-0000-0000-000000000021'::uuid;

    v_feedback_tmpl   UUID := 'e4000000-0000-0000-0000-000000000030'::uuid;
    v_feedback_ver    UUID := 'e4000000-0000-0000-0000-000000000031'::uuid;

    v_logo JSONB := '{"platform.logo_url": "https://kreesalis.ai/wp-content/uploads/2025/12/logo-black.png"}'::jsonb;
BEGIN

    -- =========================================================================
    -- Template 1: task_assigned_email
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_assigned_tmpl, '__system__', 'task_assigned_email', 'Task Assigned Email',
        'Sent when a compliance task is assigned to a user',
        'task_assigned', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_assigned_ver, v_assigned_tmpl, 1,
        'Task assigned: {{ task.title | default("New Task") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Task Assigned</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ actor.display_name | default("A team member") }}</strong> has assigned a task to you on K-Control.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Task Details</div>
        <div style="font-size:1.1em;font-weight:700;color:#0c4a6e;margin-bottom:10px;">{{ task.title | default("New Task") }}</div>
        {% if task.description %}<div style="font-size:0.9em;color:#475569;line-height:1.5;margin-bottom:10px;">{{ task.description }}</div>{% endif %}
        {% if task.control_name %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Control</span><span style="color:#0369a1;font-weight:500;">{{ task.control_name }}</span></div>{% endif %}
        {% if task.framework %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Framework</span><span style="color:#0369a1;font-weight:500;">{{ task.framework }}</span></div>{% endif %}
        {% if task.priority %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Priority</span><span style="color:#0369a1;font-weight:500;text-transform:capitalize;">{{ task.priority }}</span></div>{% endif %}
      </div>
      {% if task.due_date %}
      <div style="background:#fffbeb;padding:14px 18px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;">
        <strong>Due date: {{ task.due_date }}.</strong> Please complete this task before the due date.
      </div>
      {% endif %}
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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

{{ actor.display_name | default("A team member") }} has assigned a task to you on K-Control.

Task: {{ task.title | default("New Task") }}
{% if task.description %}{{ task.description }}
{% endif %}{% if task.control_name %}Control:   {{ task.control_name }}
{% endif %}{% if task.framework %}Framework: {{ task.framework }}
{% endif %}{% if task.priority %}Priority:  {{ task.priority }}
{% endif %}{% if task.due_date %}Due Date:  {{ task.due_date }}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Task assigned: {{ task.title | default("New Task") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_assigned_ver WHERE id = v_assigned_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- Template 2: task_status_changed_email
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_status_tmpl, '__system__', 'task_status_changed_email', 'Task Status Changed Email',
        'Sent when the status of a task changes',
        'task_status_changed', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_status_ver, v_status_tmpl, 1,
        'Task status updated: {{ task.title | default("Task") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Task Status Updated</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p>The status of a task you are involved with has been updated by <strong>{{ actor.display_name | default("a team member") }}</strong>.</p>
      </div>
      <div style="background:#f0f9ff;padding:18px 20px;border-radius:8px;border:1px solid #bae6fd;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:700;color:#0369a1;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:6px;">Status Change</div>
        <div style="font-size:1.05em;font-weight:600;color:#0c4a6e;margin-bottom:10px;">{{ task.title | default("Task") }}</div>
        <div style="display:flex;align-items:center;gap:12px;padding:8px 0;">
          {% if task.status.previous %}<span style="background:#e2e8f0;color:#475569;padding:4px 12px;border-radius:20px;font-size:0.85em;font-weight:500;">{{ task.status.previous }}</span>
          <span style="color:#64748b;font-size:1.2em;">→</span>{% endif %}
          <span style="background:#dbeafe;color:#1d4ed8;padding:4px 12px;border-radius:20px;font-size:0.85em;font-weight:600;">{{ task.status.new | default("Updated") }}</span>
        </div>
        {% if task.control_name %}<div style="display:flex;padding:5px 0;border-top:1px solid #e0f2fe;margin-top:8px;font-size:0.88em;"><span style="color:#64748b;min-width:90px;">Control</span><span style="color:#0369a1;font-weight:500;">{{ task.control_name }}</span></div>{% endif %}
      </div>
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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

{{ actor.display_name | default("A team member") }} updated the status of a task you are involved with.

Task: {{ task.title | default("Task") }}
{% if task.status.previous %}Previous: {{ task.status.previous }}
{% endif %}New Status: {{ task.status.new | default("Updated") }}
{% if task.control_name %}Control:  {{ task.control_name }}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team$TEXT$,
        '{{ task.title | default("Task") }}: status changed to {{ task.status.new | default("updated") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_status_ver WHERE id = v_status_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- Template 3: task_comment_added_email
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_comment_tmpl, '__system__', 'task_comment_added_email', 'Task Comment Added Email',
        'Sent when a new comment is added to a task the user is involved with',
        'task_comment_added', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_comment_ver, v_comment_tmpl, 1,
        'New comment on: {{ task.title | default("Task") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">New Comment</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ comment.author | default("A team member") }}</strong> added a comment to <strong>{{ task.title | default("a task") }}</strong> you are involved with.</p>
      </div>
      <div style="background:#f8fafc;padding:18px 20px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">{{ comment.author | default("Comment") }}</div>
        <div style="font-size:0.95em;color:#1e293b;line-height:1.6;font-style:italic;">"{{ comment.body | default("See the task for the full comment.") }}"</div>
      </div>
      {% if task.control_name %}
      <div style="background:#fffbeb;padding:12px 16px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;font-size:0.9em;">
        <strong>Control:</strong> {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
      </div>
      {% endif %}
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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

{{ comment.author | default("A team member") }} added a comment to {{ task.title | default("a task") }}:

"{{ comment.body | default("See the task for the full comment.") }}"

{% if task.control_name %}Control: {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team$TEXT$,
        '{{ comment.author | default("New comment") }} on {{ task.title | default("task") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_comment_ver WHERE id = v_comment_tmpl AND active_version_id IS NULL;

    -- =========================================================================
    -- Template 4: task_feedback_received_email
    -- =========================================================================
    INSERT INTO "03_notifications"."10_fct_templates"
        (id, tenant_key, code, name, description, notification_type_code, channel_code,
         active_version_id, base_template_id, is_active, is_disabled, is_deleted, is_system,
         static_variables, created_at, updated_at)
    VALUES (v_feedback_tmpl, '__system__', 'task_feedback_received_email', 'Task Feedback Received Email',
        'Sent when feedback is submitted on a task or control evidence',
        'task_feedback_received', 'email', NULL, NULL, TRUE, FALSE, FALSE, TRUE, v_logo, NOW(), NOW())
    ON CONFLICT (tenant_key, code) DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions"
        (id, template_id, version_number, subject_line, body_html, body_text, body_short,
         metadata_json, change_notes, created_at)
    VALUES (v_feedback_ver, v_feedback_tmpl, 1,
        'Feedback received on: {{ task.title | default("Task") }} — K-Control',
        $HTML$<html>
<body style="background:#f5f7fa;padding:0;margin:0;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:720px;margin:24px auto;background:#ffffff;border-radius:10px;box-shadow:0 2px 12px rgba(0,0,0,0.07);overflow:hidden;">
    <div style="height:4px;background:#295cf6;"></div>
    <div style="padding:32px 32px 0 32px;text-align:center;">
      <img src="{{ platform.logo_url }}" alt="Kreesalis" style="max-width:140px;margin-bottom:16px;" /><br>
      <h2 style="color:#222;font-size:1.5em;margin:8px 0 0 0;font-weight:700;">Feedback Received</h2>
    </div>
    <div style="padding:12px 32px 0 32px;">
      <div style="font-size:1.05em;color:#222;line-height:1.7;">
        <p>Hi <strong>{{ user.display_name | default("there") }}</strong>,</p>
        <p><strong>{{ feedback.author | default("A reviewer") }}</strong> has submitted feedback on <strong>{{ task.title | default("a task") }}</strong>.</p>
      </div>
      {% if feedback.type %}
      <div style="text-align:center;margin:10px 0;">
        {% if feedback.type == 'approved' %}
        <span style="display:inline-block;background:#dcfce7;color:#166534;padding:6px 18px;border-radius:20px;font-size:0.88em;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Approved</span>
        {% elif feedback.type == 'rejected' %}
        <span style="display:inline-block;background:#fee2e2;color:#991b1b;padding:6px 18px;border-radius:20px;font-size:0.88em;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Rejected</span>
        {% else %}
        <span style="display:inline-block;background:#fffbeb;color:#92400e;padding:6px 18px;border-radius:20px;font-size:0.88em;font-weight:700;text-transform:uppercase;letter-spacing:0.05em;">Needs Revision</span>
        {% endif %}
      </div>
      {% endif %}
      <div style="background:#f8fafc;padding:18px 20px;border-radius:8px;border-left:4px solid #295cf6;margin:14px 0;">
        <div style="font-size:0.78em;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:0.05em;margin-bottom:8px;">Feedback from {{ feedback.author | default("Reviewer") }}</div>
        <div style="font-size:0.95em;color:#1e293b;line-height:1.6;font-style:italic;">"{{ feedback.body | default("See the task for the full feedback.") }}"</div>
      </div>
      {% if task.control_name %}
      <div style="background:#fffbeb;padding:12px 16px;border-radius:8px;border-left:4px solid #f59e0b;margin:14px 0;font-size:0.9em;">
        <strong>Control:</strong> {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
      </div>
      {% endif %}
      <div style="text-align:center;margin:28px 0 8px 0;">
        <a href="{{ task.url | default("#") }}" style="background:#295cf6;color:#ffffff;padding:14px 36px;border-radius:6px;text-decoration:none;display:inline-block;font-size:1em;font-weight:600;box-shadow:0 2px 8px rgba(41,92,246,0.18);">View Task</a>
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

{{ feedback.author | default("A reviewer") }} submitted feedback on {{ task.title | default("a task") }}:
{% if feedback.type %}Outcome: {{ feedback.type | upper }}
{% endif %}
"{{ feedback.body | default("See the task for the full feedback.") }}"

{% if task.control_name %}Control: {{ task.control_name }}{% if task.framework %} · {{ task.framework }}{% endif %}
{% endif %}
View task: {{ task.url }}

Best regards,
Kreesalis Team$TEXT$,
        'Feedback on {{ task.title | default("task") }}: {{ feedback.type | default("review") }}',
        '{}', 'Initial version', NOW())
    ON CONFLICT (id) DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = v_feedback_ver WHERE id = v_feedback_tmpl AND active_version_id IS NULL;

END $$;

-- ─────────────────────────────────────────────────────────────────────────────
-- 5. NOTIFICATION RULES
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."11_fct_notification_rules"
    (id, tenant_key, code, name, description,
     source_event_type, source_event_category,
     notification_type_code, recipient_strategy,
     priority_code, is_active, created_at, updated_at)
VALUES
    (
        '30000000-0000-0000-0000-000000000030'::uuid,
        'default', 'rule_task_assigned',
        'Task Assigned',
        'Notify the assignee when a task is assigned to them',
        'task_assigned', 'grc',
        'task_assigned', 'specific_users',
        'high', TRUE, NOW(), NOW()
    ),
    (
        '30000000-0000-0000-0000-000000000031'::uuid,
        'default', 'rule_task_status_changed',
        'Task Status Changed',
        'Notify task participants when task status changes',
        'task_status_changed', 'grc',
        'task_status_changed', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        '30000000-0000-0000-0000-000000000032'::uuid,
        'default', 'rule_task_comment_added',
        'Comment Added to Task',
        'Notify task participants when a comment is added',
        'task_comment_added', 'grc',
        'task_comment_added', 'specific_users',
        'normal', TRUE, NOW(), NOW()
    ),
    (
        '30000000-0000-0000-0000-000000000033'::uuid,
        'default', 'rule_task_feedback_received',
        'Task Feedback Received',
        'Notify task owner when feedback is submitted on their task',
        'task_feedback_received', 'grc',
        'task_feedback_received', 'specific_users',
        'high', TRUE, NOW(), NOW()
    )
ON CONFLICT (tenant_key, code) DO NOTHING;

-- ─────────────────────────────────────────────────────────────────────────────
-- 6. RULE CHANNEL BINDINGS
-- ─────────────────────────────────────────────────────────────────────────────

INSERT INTO "03_notifications"."18_lnk_notification_rule_channels"
    (id, rule_id, channel_code, template_code, is_active, created_at, updated_at)
VALUES
    (
        'b0000000-0000-0000-0030-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000030'::uuid,
        'email', 'task_assigned_email', TRUE, NOW(), NOW()
    ),
    (
        'b0000000-0000-0000-0031-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000031'::uuid,
        'email', 'task_status_changed_email', TRUE, NOW(), NOW()
    ),
    (
        'b0000000-0000-0000-0032-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000032'::uuid,
        'email', 'task_comment_added_email', TRUE, NOW(), NOW()
    ),
    (
        'b0000000-0000-0000-0033-000000000001'::uuid,
        '30000000-0000-0000-0000-000000000033'::uuid,
        'email', 'task_feedback_received_email', TRUE, NOW(), NOW()
    )
ON CONFLICT (rule_id, channel_code) DO NOTHING;

-- DOWN ========================================================================

DELETE FROM "03_notifications"."18_lnk_notification_rule_channels"
WHERE id IN (
    'b0000000-0000-0000-0030-000000000001'::uuid,
    'b0000000-0000-0000-0031-000000000001'::uuid,
    'b0000000-0000-0000-0032-000000000001'::uuid,
    'b0000000-0000-0000-0033-000000000001'::uuid
);

DELETE FROM "03_notifications"."11_fct_notification_rules"
WHERE id IN (
    '30000000-0000-0000-0000-000000000030'::uuid,
    '30000000-0000-0000-0000-000000000031'::uuid,
    '30000000-0000-0000-0000-000000000032'::uuid,
    '30000000-0000-0000-0000-000000000033'::uuid
);

DELETE FROM "03_notifications"."14_dtl_template_versions"
WHERE id IN (
    'e4000000-0000-0000-0000-000000000002'::uuid,
    'e4000000-0000-0000-0000-000000000011'::uuid,
    'e4000000-0000-0000-0000-000000000021'::uuid,
    'e4000000-0000-0000-0000-000000000031'::uuid
);

DELETE FROM "03_notifications"."10_fct_templates"
WHERE id IN (
    'e4000000-0000-0000-0000-000000000001'::uuid,
    'e4000000-0000-0000-0000-000000000010'::uuid,
    'e4000000-0000-0000-0000-000000000020'::uuid,
    'e4000000-0000-0000-0000-000000000030'::uuid
);

DELETE FROM "03_notifications"."07_dim_notification_channel_types"
WHERE id IN (
    'f0000000-0000-0000-0000-000000000040'::uuid,
    'f0000000-0000-0000-0000-000000000041'::uuid,
    'f0000000-0000-0000-0000-000000000042'::uuid,
    'f0000000-0000-0000-0000-000000000043'::uuid,
    'f0000000-0000-0000-0000-000000000044'::uuid,
    'f0000000-0000-0000-0000-000000000045'::uuid,
    'f0000000-0000-0000-0000-000000000046'::uuid,
    'f0000000-0000-0000-0000-000000000047'::uuid
);

DELETE FROM "03_notifications"."04_dim_notification_types"
WHERE code IN ('task_assigned', 'task_status_changed', 'task_comment_added', 'task_feedback_received');

DELETE FROM "03_notifications"."08_dim_template_variable_keys"
WHERE code IN (
    'task.title', 'task.description', 'task.due_date', 'task.url',
    'task.status.new', 'task.status.previous', 'task.priority',
    'comment.body', 'comment.author',
    'feedback.body', 'feedback.author', 'feedback.type',
    'task.control_name', 'task.framework'
);
