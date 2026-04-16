-- =============================================================================
-- Migration: 20260402_seed-workflow-notification-types.sql
-- Description: Seeds all workflow notification types for tasks, risks,
--              findings, assessments, reports, approvals, comments,
--              engagements, and feedback tickets.
-- =============================================================================

-- UP ==========================================================================

INSERT INTO "03_notifications"."04_dim_notification_types"
    (id, code, name, description, category_code, is_mandatory, is_user_triggered,
     default_enabled, cooldown_seconds, sort_order, created_at, updated_at)
VALUES
    -- ── Tasks ────────────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000001'::uuid, 'task_reassigned',         'Task Reassigned',               'Sent to the new assignee when a task is reassigned',                                         'engagement', FALSE, FALSE, TRUE,  NULL, 51, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000002'::uuid, 'task_overdue',            'Task Overdue',                  'Sent to the assignee when a task passes its due date without being completed',               'engagement', FALSE, FALSE, TRUE,  NULL, 52, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000003'::uuid, 'task_submitted',          'Task Submitted for Review',     'Sent to reviewers when a task is moved to pending_verification',                             'engagement', FALSE, FALSE, TRUE,  NULL, 53, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000004'::uuid, 'task_approved',           'Task Approved',                 'Sent to the assignee when their task is approved and published',                             'engagement', FALSE, FALSE, TRUE,  NULL, 54, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000005'::uuid, 'task_rejected',           'Task Sent Back',                'Sent to the assignee when their task is rejected and sent back to in_progress',              'engagement', FALSE, FALSE, TRUE,  NULL, 55, NOW(), NOW()),
    -- ── Comments ─────────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000010'::uuid, 'comment_mention',         'Mentioned in Comment',          'Sent when a user is @-mentioned in a comment',                                               'engagement', FALSE, FALSE, TRUE,  60,   60, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000011'::uuid, 'comment_reply',           'Reply to Your Comment',         'Sent when someone replies to your comment',                                                  'engagement', FALSE, FALSE, TRUE,  60,   61, NOW(), NOW()),
    -- ── Risks ─────────────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000020'::uuid, 'risk_assigned',           'Risk Assigned',                 'Sent when a risk is assigned to a user as owner',                                           'engagement', FALSE, FALSE, TRUE,  NULL, 70, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000021'::uuid, 'risk_review_due',         'Risk Review Due',               'Sent when a risk is approaching its scheduled review date',                                  'engagement', FALSE, FALSE, TRUE,  NULL, 71, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000022'::uuid, 'risk_status_changed',     'Risk Status Changed',           'Sent to the risk owner when a risk status changes',                                         'engagement', FALSE, FALSE, TRUE,  300,  72, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000023'::uuid, 'treatment_plan_assigned', 'Treatment Plan Assigned',       'Sent to the treatment owner when a treatment plan is created and assigned to them',          'engagement', FALSE, FALSE, TRUE,  NULL, 73, NOW(), NOW()),
    -- ── Findings ─────────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000030'::uuid, 'finding_assigned',        'Finding Assigned',              'Sent when an audit finding is assigned to a user for remediation',                          'engagement', FALSE, FALSE, TRUE,  NULL, 80, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000031'::uuid, 'finding_response_needed', 'Finding Response Needed',       'Sent to prompt the assignee to respond to a finding in auditor_review status',               'engagement', FALSE, FALSE, TRUE,  NULL, 81, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000032'::uuid, 'finding_reviewed',        'Finding Reviewed',              'Sent to the finding owner after auditor reviews and closes or escalates a finding',          'engagement', FALSE, FALSE, TRUE,  NULL, 82, NOW(), NOW()),
    -- ── Assessments ──────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000040'::uuid, 'assessment_completed',    'Assessment Completed',          'Sent when an assessment reaches completed status',                                           'engagement', FALSE, FALSE, TRUE,  NULL, 90, NOW(), NOW()),
    -- ── Engagements ──────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000050'::uuid, 'engagement_status_changed','Engagement Status Changed',    'Sent to engagement participants when the engagement moves to a new phase',                   'engagement', FALSE, FALSE, TRUE,  NULL, 100, NOW(), NOW()),
    -- ── Reports ──────────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000060'::uuid, 'report_ready',            'Report Ready',                  'Sent when an AI-generated report has completed and is ready to view',                       'transactional', FALSE, FALSE, TRUE, NULL, 110, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000061'::uuid, 'report_failed',           'Report Generation Failed',      'Sent when report generation fails so the user can retry',                                   'transactional', FALSE, FALSE, TRUE, NULL, 111, NOW(), NOW()),
    -- ── AI Approvals ─────────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000070'::uuid, 'approval_required',       'Approval Required',             'Sent to the designated approver when an AI agent action requires human approval',           'transactional', TRUE,  FALSE, TRUE, NULL, 120, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000071'::uuid, 'approval_expired',        'Approval Request Expired',      'Sent to the requester when an approval times out without a response',                      'transactional', FALSE, FALSE, TRUE, NULL, 121, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000072'::uuid, 'approval_rejected',       'Approval Rejected',             'Sent to the requester when their AI approval request is rejected by the approver',         'transactional', FALSE, FALSE, TRUE, NULL, 122, NOW(), NOW()),
    -- ── Feedback Tickets ─────────────────────────────────────────────────────
    ('c0000000-0000-0000-0001-000000000080'::uuid, 'ticket_assigned',         'Feedback Ticket Assigned',      'Sent when a feedback/support ticket is assigned to a user',                                 'transactional', FALSE, FALSE, TRUE, NULL, 130, NOW(), NOW()),
    ('c0000000-0000-0000-0001-000000000081'::uuid, 'ticket_status_changed',   'Ticket Status Changed',         'Sent to the ticket submitter when the status of their ticket changes',                     'transactional', FALSE, FALSE, TRUE, 300,  131, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- Channel support for all new types (email + web_push)
INSERT INTO "03_notifications"."07_dim_notification_channel_types"
    (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at)
VALUES
    ('f0000000-0000-0001-0001-000000000001'::uuid, 'task_reassigned',          'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000002'::uuid, 'task_reassigned',          'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000003'::uuid, 'task_overdue',             'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000004'::uuid, 'task_overdue',             'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000005'::uuid, 'task_submitted',           'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000006'::uuid, 'task_submitted',           'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000007'::uuid, 'task_approved',            'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000008'::uuid, 'task_approved',            'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000009'::uuid, 'task_rejected',            'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000000a'::uuid, 'task_rejected',            'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000000b'::uuid, 'comment_mention',          'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000000c'::uuid, 'comment_mention',          'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000000d'::uuid, 'comment_reply',            'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000000e'::uuid, 'comment_reply',            'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000000f'::uuid, 'risk_assigned',            'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000010'::uuid, 'risk_assigned',            'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000011'::uuid, 'risk_review_due',          'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000012'::uuid, 'risk_review_due',          'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000013'::uuid, 'risk_status_changed',      'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000014'::uuid, 'risk_status_changed',      'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000015'::uuid, 'treatment_plan_assigned',  'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000016'::uuid, 'treatment_plan_assigned',  'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000017'::uuid, 'finding_assigned',         'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000018'::uuid, 'finding_assigned',         'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000019'::uuid, 'finding_response_needed',  'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000001a'::uuid, 'finding_response_needed',  'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000001b'::uuid, 'finding_reviewed',         'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000001c'::uuid, 'finding_reviewed',         'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000001d'::uuid, 'assessment_completed',     'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000001e'::uuid, 'assessment_completed',     'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000001f'::uuid, 'engagement_status_changed','email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000020'::uuid, 'engagement_status_changed','web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000021'::uuid, 'report_ready',             'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000022'::uuid, 'report_ready',             'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000023'::uuid, 'report_failed',            'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000024'::uuid, 'report_failed',            'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000025'::uuid, 'approval_required',        'email',    'critical', TRUE, NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000026'::uuid, 'approval_required',        'web_push', 'critical', TRUE, NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000027'::uuid, 'approval_expired',         'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000028'::uuid, 'approval_expired',         'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-000000000029'::uuid, 'approval_rejected',        'email',    'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000002a'::uuid, 'approval_rejected',        'web_push', 'high',   TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000002b'::uuid, 'ticket_assigned',          'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000002c'::uuid, 'ticket_assigned',          'web_push', 'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000002d'::uuid, 'ticket_status_changed',    'email',    'normal', TRUE,  NOW(), NOW()),
    ('f0000000-0000-0001-0001-00000000002e'::uuid, 'ticket_status_changed',    'web_push', 'normal', TRUE,  NOW(), NOW())
ON CONFLICT (notification_type_code, channel_code) DO NOTHING;

-- Variable keys for new domains
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, resolution_source, preview_default, sort_order, created_at, updated_at)
VALUES
    ('a0000000-0000-0001-0001-000000000001'::uuid, 'risk.title',              'Risk Title',               'Title of the risk',                                          'audit_property', 'Unauthorised Data Access',           60, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000002'::uuid, 'risk.severity',           'Risk Severity',            'Current severity level (critical/high/medium/low)',           'audit_property', 'high',                               61, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000003'::uuid, 'risk.status.new',         'Risk New Status',          'The new status after the transition',                        'audit_property', 'treating',                           62, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000004'::uuid, 'risk.status.previous',    'Risk Previous Status',     'The previous status before the transition',                  'audit_property', 'assessed',                           63, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000005'::uuid, 'risk.url',                'Risk URL',                 'Direct link to the risk in K-Control',                       'audit_property', 'https://app.kcontrol.io/risks/x',    64, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000006'::uuid, 'risk.review_date',        'Risk Review Date',         'Scheduled review date for the risk',                         'audit_property', 'April 30, 2026',                     65, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000007'::uuid, 'treatment.title',         'Treatment Plan Title',     'Title of the risk treatment plan',                           'audit_property', 'Implement MFA across all services',  66, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000008'::uuid, 'treatment.due_date',      'Treatment Due Date',       'Due date for the treatment plan',                            'audit_property', 'May 15, 2026',                       67, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000009'::uuid, 'finding.title',           'Finding Title',            'Title of the audit finding',                                 'audit_property', 'Missing encryption at rest',         70, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000000a'::uuid, 'finding.severity',        'Finding Severity',         'Severity of the finding (critical/high/medium/low)',          'audit_property', 'high',                               71, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000000b'::uuid, 'finding.status.new',      'Finding New Status',       'The new status of the finding',                              'audit_property', 'auditor_review',                     72, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000000c'::uuid, 'finding.url',             'Finding URL',              'Direct link to the finding',                                 'audit_property', 'https://app.kcontrol.io/findings/x', 73, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000000d'::uuid, 'finding.due_date',        'Finding Due Date',         'Due date for remediating the finding',                       'audit_property', 'April 20, 2026',                     74, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000000e'::uuid, 'assessment.title',        'Assessment Title',         'Title of the assessment',                                    'audit_property', 'Q1 2026 SOC 2 Readiness Assessment', 80, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000000f'::uuid, 'assessment.url',          'Assessment URL',           'Direct link to the assessment',                              'audit_property', 'https://app.kcontrol.io/assessments/x', 81, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000010'::uuid, 'engagement.title',        'Engagement Title',         'Title of the engagement',                                    'audit_property', 'Q4 2025 SOC 2 Type II Audit',        90, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000011'::uuid, 'engagement.status.new',   'Engagement New Status',    'The new status of the engagement',                          'audit_property', 'active',                             91, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000012'::uuid, 'engagement.status.previous','Engagement Prev Status', 'The previous status of the engagement',                     'audit_property', 'setup',                              92, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000013'::uuid, 'engagement.url',          'Engagement URL',           'Direct link to the engagement',                              'audit_property', 'https://app.kcontrol.io/engagements/x', 93, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000014'::uuid, 'report.title',            'Report Title',             'Human-readable title of the generated report',               'audit_property', 'SOC 2 Framework Compliance Report',  100, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000015'::uuid, 'report.type_label',       'Report Type Label',        'Human label for the report type',                            'audit_property', 'Framework Compliance',               101, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000016'::uuid, 'report.url',              'Report URL',               'Direct link to view the report',                             'audit_property', 'https://app.kcontrol.io/reports/x',  102, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000017'::uuid, 'report.error',            'Report Error',             'Error message if report generation failed',                  'audit_property', 'LLM rate limit exceeded',            103, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000018'::uuid, 'approval.title',          'Approval Title',           'Human-readable description of the action requiring approval','audit_property', 'Deploy compliance report to Slack',  110, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000019'::uuid, 'approval.agent_name',     'Agent Name',               'Name of the AI agent that triggered the approval',           'audit_property', 'Audit Copilot',                      111, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000001a'::uuid, 'approval.action',         'Approval Action',          'Summary of the action to be approved or rejected',           'audit_property', 'Post report summary to #compliance channel', 112, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000001b'::uuid, 'approval.url',            'Approval URL',             'Direct link to the approval request',                        'audit_property', 'https://app.kcontrol.io/approvals/x',113, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000001c'::uuid, 'approval.expires_in',     'Approval Expires In',      'How long until the approval request expires',                'audit_property', '24 hours',                           114, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000001d'::uuid, 'ticket.title',            'Ticket Title',             'Title of the feedback/support ticket',                       'audit_property', 'Dashboard not loading in Firefox',   120, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000001e'::uuid, 'ticket.status.new',       'Ticket New Status',        'The new status of the ticket',                               'audit_property', 'in_progress',                        121, NOW(), NOW()),
    ('a0000000-0000-0001-0001-00000000001f'::uuid, 'ticket.url',              'Ticket URL',               'Direct link to the ticket',                                  'audit_property', 'https://app.kcontrol.io/feedback/x', 122, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000020'::uuid, 'mention.entity_type',     'Mention Entity Type',      'Type of entity the comment is on (task, risk, control, etc)','audit_property', 'task',                               130, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000021'::uuid, 'mention.entity_title',    'Mention Entity Title',     'Title of the entity the comment is on',                      'audit_property', 'Review CC6.1 Evidence',              131, NOW(), NOW()),
    ('a0000000-0000-0001-0001-000000000022'::uuid, 'mention.entity_url',      'Mention Entity URL',       'URL of the entity the comment is on',                        'audit_property', 'https://app.kcontrol.io/tasks/x',    132, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;

-- DOWN ========================================================================

DELETE FROM "03_notifications"."08_dim_template_variable_keys"
WHERE code IN (
    'risk.title','risk.severity','risk.status.new','risk.status.previous','risk.url','risk.review_date',
    'treatment.title','treatment.due_date',
    'finding.title','finding.severity','finding.status.new','finding.url','finding.due_date',
    'assessment.title','assessment.url',
    'engagement.title','engagement.status.new','engagement.status.previous','engagement.url',
    'report.title','report.type_label','report.url','report.error',
    'approval.title','approval.agent_name','approval.action','approval.url','approval.expires_in',
    'ticket.title','ticket.status.new','ticket.url',
    'mention.entity_type','mention.entity_title','mention.entity_url'
);

DELETE FROM "03_notifications"."07_dim_notification_channel_types"
WHERE notification_type_code IN (
    'task_reassigned','task_overdue','task_submitted','task_approved','task_rejected',
    'comment_mention','comment_reply',
    'risk_assigned','risk_review_due','risk_status_changed','treatment_plan_assigned',
    'finding_assigned','finding_response_needed','finding_reviewed',
    'assessment_completed','engagement_status_changed',
    'report_ready','report_failed',
    'approval_required','approval_expired','approval_rejected',
    'ticket_assigned','ticket_status_changed'
);

DELETE FROM "03_notifications"."04_dim_notification_types"
WHERE code IN (
    'task_reassigned','task_overdue','task_submitted','task_approved','task_rejected',
    'comment_mention','comment_reply',
    'risk_assigned','risk_review_due','risk_status_changed','treatment_plan_assigned',
    'finding_assigned','finding_response_needed','finding_reviewed',
    'assessment_completed','engagement_status_changed',
    'report_ready','report_failed',
    'approval_required','approval_expired','approval_rejected',
    'ticket_assigned','ticket_status_changed'
);
