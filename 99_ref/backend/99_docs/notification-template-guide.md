# Notification Template Creation Guide

This document describes the exact process for creating a new notification template in K-Control's notification system. Follow these steps whenever you need to add a new email, web push, or webhook template.

---

## Architecture Overview

```
Template Variable Keys (08_dim)  ──┐
                                   ├─→  Template (10_fct)  ──→  Template Version (14_dtl)
Template Placeholders (15_dtl)  ───┘         │
                                             │
Notification Rule (11_fct)  ─────────────────┘
    └─ source_event_type → notification_type_code
```

**Key tables** (schema: `03_notifications`):

| Table | Purpose |
|-------|---------|
| `04_dim_notification_types` | Notification type catalog (e.g., `email_verification`, `password_reset`) |
| `08_dim_template_variable_keys` | Valid placeholder variables with resolution source |
| `10_fct_templates` | Template registry (code, channel, notification type) |
| `14_dtl_template_versions` | Versioned content (subject, HTML body, text body, short body) |
| `15_dtl_template_placeholders` | Which variables a template uses (required/optional + defaults) |
| `11_fct_notification_rules` | Maps audit events to notification dispatch |

---

## Step-by-Step Process

### Step 1: Define the Notification Type (if new)

Check if your notification type already exists in `04_dim_notification_types`. Existing types:

| Code | Category | Description |
|------|----------|-------------|
| `password_reset` | security | Password reset OTP or link |
| `email_verification` | security | Email verification code or link |
| `login_from_new_device` | security | New device login alert |
| `password_changed` | transactional | Password change confirmation |
| `email_verified` | transactional | Email verified confirmation |
| `org_invite_received` | org | Org invitation |
| `workspace_invite_received` | workspace | Workspace invitation |
| `global_broadcast` | system | Platform announcements |

If your type doesn't exist, add it:

```sql
INSERT INTO "03_notifications"."04_dim_notification_types"
    (id, code, name, description, category_code, is_mandatory, is_user_triggered,
     default_enabled, cooldown_seconds, sort_order, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'my_new_type', 'My New Type', 'Description here',
     'transactional', TRUE, TRUE, TRUE, NULL, 20, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

**Also add the channel-type matrix entry** (which channels this type supports):

```sql
INSERT INTO "03_notifications"."07_dim_notification_channel_types"
    (id, notification_type_code, channel_code, priority_code, is_default, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'my_new_type', 'email', 'high', TRUE, NOW(), NOW())
ON CONFLICT DO NOTHING;
```

### Step 2: Define Template Variable Keys (if new)

Check existing variable keys in `08_dim_template_variable_keys`. Common ones:

| Code | Resolution Source | Resolution Key | Example |
|------|-------------------|----------------|---------|
| `user.display_name` | `user_property` | `display_name` | "John Doe" |
| `user.email` | `user_property` | `email` | "john@example.com" |
| `user.first_name` | `user_property` | `first_name` | "John" |
| `user.last_name` | `user_property` | `last_name` | "Doe" |
| `otp_code` | `audit_property` | `otp_code` | "482901" |
| `token` | `audit_property` | `token` | "abc123def456" |
| `action_url` | `audit_property` | `action_url` | "https://..." |
| `expiry_hours` | `audit_property` | `expiry_hours` | "24" |
| `org.name` | `org` | `name` | "Acme Corp" |
| `workspace.name` | `workspace` | `name` | "Production" |

**Resolution sources** determine where the value comes from at render time:

| Source | Description |
|--------|-------------|
| `user_property` | From `05_dtl_user_properties` for the **recipient** user |
| `actor_property` | From `05_dtl_user_properties` for the **actor** (who triggered the event) |
| `audit_property` | From the audit event's `properties` dict (passed by the service that emits the event) |
| `org` | From `29_fct_orgs` (resolved by `org_id` in audit properties) |
| `workspace` | From `34_fct_workspaces` (resolved by `workspace_id`) |
| `settings` | From application settings (e.g., `platform.name` maps to `notification_from_name`) |
| `computed` | Runtime-computed values (timestamp, unsubscribe_url) |
| `static` | Literal value stored in the dimension table |
| `custom_query` | Custom SQL query result |

To add a new variable key:

```sql
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value,
     resolution_source, resolution_key, sort_order, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'my_variable', 'My Variable', 'Description',
     'string', 'example_value', 'audit_property', 'my_variable', 99, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

### Step 3: Create the Template and Version

Use a `DO $$ ... END $$` block to create the template + version atomically and link them:

```sql
DO $$
DECLARE
    _tpl_id  UUID := gen_random_uuid();
    _ver_id  UUID := gen_random_uuid();
BEGIN
    -- 3a. Create the template record
    INSERT INTO "03_notifications"."10_fct_templates" (
        id, tenant_key, code, name, description,
        notification_type_code, channel_code,
        is_active, is_system,
        created_at, updated_at
    ) VALUES (
        _tpl_id, '__system__',
        'my_template_email',                    -- unique code
        'My Template (Email)',                   -- display name
        'Description of what this template does.',
        'my_new_type',                          -- FK to 04_dim_notification_types.code
        'email',                                -- channel: email, web_push, webhook
        TRUE, TRUE,
        NOW(), NOW()
    )
    ON CONFLICT DO NOTHING;

    -- 3b. Create version 1 with the actual content
    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_html, body_text, body_short,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'Subject Line Here — K-Control',
        E'<html>
<body style="font-family: Arial, sans-serif;">
  <h2>Hello {{ user.first_name }},</h2>
  <p>Your content here. Variable: {{ my_variable }}</p>
</body>
</html>',
        E'Hello {{ user.first_name }},\n\nYour content here. Variable: {{ my_variable }}',
        'Short version for push: {{ my_variable }}',
        TRUE, NOW()
    )
    ON CONFLICT DO NOTHING;

    -- 3c. Link template to its active version
    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;

    -- 3d. Declare template placeholders
    INSERT INTO "03_notifications"."15_dtl_template_placeholders"
        (id, template_id, variable_key_code, is_required, default_value, created_at, updated_at)
    VALUES
        (gen_random_uuid(), _tpl_id, 'user.first_name', FALSE, 'there', NOW(), NOW()),
        (gen_random_uuid(), _tpl_id, 'my_variable', TRUE, NULL, NOW(), NOW())
    ON CONFLICT DO NOTHING;
END $$;
```

### Step 4: Create the Notification Rule (if new event type)

Rules map audit events to notification types. When a service emits an audit event, the dispatcher finds matching rules and sends notifications.

```sql
INSERT INTO "03_notifications"."11_fct_notification_rules"
    (id, tenant_key, code, name, description,
     source_event_type, source_event_category,
     notification_type_code, recipient_strategy,
     priority_code, is_active, is_system, created_at, updated_at)
VALUES
    (gen_random_uuid(), 'default',
     'rule_my_event',                   -- unique rule code
     'My Event Notification',           -- display name
     'Send notification when my event occurs',
     'my_audit_event_type',             -- matches AuditEventType enum
     'auth',                            -- event category
     'my_new_type',                     -- notification type to send
     'actor',                           -- recipient strategy: actor, entity_owner, org_members, etc.
     'high',                            -- priority: critical, high, normal, low
     TRUE, TRUE, NOW(), NOW())
ON CONFLICT (tenant_key, code) DO NOTHING;
```

**Recipient strategies:**

| Strategy | Recipients |
|----------|-----------|
| `actor` | The user who triggered the event |
| `entity_owner` | The owner of the affected entity |
| `org_members` | All members of the related org |
| `workspace_members` | All members of the related workspace |
| `all_users` | All active users |
| `specific_users` | Users specified in audit properties |

### Step 5: Emit the Audit Event from Backend Service

In your backend service code, emit an audit event with the variable values as properties:

```python
await self._audit_writer.write_entry(
    connection,
    AuditEntry(
        id=str(uuid4()),
        tenant_key=tenant_key,
        entity_type="challenge",       # or "user", "org", etc.
        entity_id=entity_id,
        event_type="my_audit_event_type",   # matches the rule's source_event_type
        event_category="auth",
        occurred_at=now,
        actor_id=user_id,
        actor_type="user",
        ip_address=client_ip,
        properties={
            # These become audit_property variables
            "my_variable": "actual_value",
            "target": email,
        },
    ),
)
```

The notification dispatcher will:
1. Match the `source_event_type` to notification rules
2. Resolve recipients based on the rule's `recipient_strategy`
3. Look up the template by `notification_type_code` + `channel_code`
4. Resolve template variables using the resolution sources
5. Render the Jinja2 template with the resolved variables
6. Queue the notification for delivery

### Step 6: Verify via Admin UI

1. Navigate to **Admin > Notifications > Templates tab**
2. Find your template by notification type
3. Click on it to view versions
4. Use the **Preview** button to test rendering with sample variables
5. Use **Send Test** to send a test notification to yourself

---

## Using the Admin UI (Alternative to SQL)

You can also create templates through the admin UI without writing SQL:

### Creating a Template via UI

1. Go to **Admin > Notifications**
2. Click the **Templates** tab
3. Click **Create Template**
4. Fill in:
   - **Code**: Unique identifier (e.g., `my_template_email`)
   - **Name**: Display name
   - **Description**: What this template does
   - **Notification Type**: Select from dropdown
   - **Channel**: email, web_push, or webhook
   - **Base Template**: (optional) wraps content in a layout
5. Click **Create**

### Creating a Template Version via UI

1. Open the template you just created
2. Click **New Version**
3. Fill in:
   - **Subject Line**: Email subject (supports `{{ variable }}` syntax)
   - **Body HTML**: Full HTML with Jinja2 variables
   - **Body Text**: Plain text fallback
   - **Body Short**: Short text for push notifications
   - **Change Notes**: What changed in this version
4. Click **Create Version** — it auto-activates

### Creating Variable Keys via UI

1. Go to **Admin > Notifications > Variable Queries** tab
2. Scroll to the **Variable Keys** section
3. Click **Create Variable Key**
4. Fill in:
   - **Code**: The placeholder name (e.g., `my_variable`)
   - **Name**: Display name
   - **Description**: What this variable represents
   - **Resolution Source**: Where the value comes from
5. Click **Create**

---

## Template Syntax Reference

Templates use **Jinja2 sandboxed** syntax:

```html
<!-- Simple variable -->
<p>Hello {{ user.first_name }},</p>

<!-- Variable with default -->
<p>Hello {{ user.first_name | default('there') }},</p>

<!-- Conditional -->
{% if otp_code %}
  <p>Your OTP: {{ otp_code }}</p>
{% endif %}

<!-- Loop (if variable is a list) -->
{% for item in items %}
  <li>{{ item }}</li>
{% endfor %}
```

**Variables are dot-notation nested**: `user.first_name` becomes `{{ user.first_name }}` in templates. The renderer converts flat `{"user.first_name": "John"}` to nested `{"user": {"first_name": "John"}}`.

---

## Complete Example: OTP Email Verification Template

This is the actual template created for the OTP email verification feature:

### 1. Variable Key (SQL)

```sql
INSERT INTO "03_notifications"."08_dim_template_variable_keys"
    (id, code, name, description, data_type, example_value,
     resolution_source, resolution_key, sort_order, created_at, updated_at)
VALUES
    ('10000000-0000-0000-0000-000000000050', 'otp_code', 'OTP Code',
     'One-time verification code', 'string', '482901',
     'audit_property', 'otp_code', 50, NOW(), NOW())
ON CONFLICT (code) DO NOTHING;
```

### 2. Template + Version + Placeholders (SQL)

```sql
DO $$
DECLARE
    _tpl_id  UUID := gen_random_uuid();
    _ver_id  UUID := gen_random_uuid();
BEGIN
    INSERT INTO "03_notifications"."10_fct_templates" (
        id, tenant_key, code, name, description,
        notification_type_code, channel_code,
        is_active, is_system, created_at, updated_at
    ) VALUES (
        _tpl_id, '__system__',
        'email_verification_otp',
        'Email Verification OTP',
        'Sends a 6-digit OTP code for email verification during onboarding.',
        'email_verification', 'email',
        TRUE, TRUE, NOW(), NOW()
    ) ON CONFLICT DO NOTHING;

    INSERT INTO "03_notifications"."14_dtl_template_versions" (
        id, template_id, version_number,
        subject_line, body_html, body_text, body_short,
        is_active, created_at
    ) VALUES (
        _ver_id, _tpl_id, 1,
        'Your Verification OTP — K-Control',
        -- HTML body with {{ user.first_name }} and {{ otp_code }}
        E'<html>...</html>',
        E'Hi {{ user.first_name }},\n\nYour verification OTP is: {{ otp_code }}\n\nExpires in 5 minutes.',
        'Your OTP is {{ otp_code }}. Expires in 5 minutes.',
        TRUE, NOW()
    ) ON CONFLICT DO NOTHING;

    UPDATE "03_notifications"."10_fct_templates"
    SET active_version_id = _ver_id, updated_at = NOW()
    WHERE id = _tpl_id AND active_version_id IS NULL;

    INSERT INTO "03_notifications"."15_dtl_template_placeholders"
        (id, template_id, variable_key_code, is_required, default_value, created_at, updated_at)
    VALUES
        (gen_random_uuid(), _tpl_id, 'user.first_name', FALSE, 'there', NOW(), NOW()),
        (gen_random_uuid(), _tpl_id, 'otp_code', TRUE, NULL, NOW(), NOW())
    ON CONFLICT DO NOTHING;
END $$;
```

### 3. Backend Service (Python)

```python
# In the service method that sends the OTP:
await self._audit_writer.write_entry(
    connection,
    AuditEntry(
        id=str(uuid4()),
        tenant_key=tenant_key,
        entity_type="challenge",
        entity_id=challenge_id,
        event_type="email_verification_requested",  # matches existing rule
        event_category="auth",
        occurred_at=now,
        actor_id=user_id,
        actor_type="user",
        ip_address=client_ip,
        properties={
            "target": email,
            "otp_code": otp_code,      # passed as audit_property
            "method": "otp",
        },
    ),
)
```

### 4. Existing Rule (already seeded)

The `rule_email_verification` rule (`source_event_type = 'email_verification_requested'`) already maps to `notification_type_code = 'email_verification'`, so no new rule was needed.

---

## Platform Base URL Configuration

All email deep links (magic link verify, password reset, tracking pixels, click redirects) derive from a single `PLATFORM_BASE_URL` environment variable.

### How it works

Set **one** env var per environment — everything else auto-derives:

| Environment | `PLATFORM_BASE_URL` |
|-------------|---------------------|
| Local dev | `http://localhost:3000` |
| Dev server | `https://k-control-dev.kreesalis.com` |
| Staging | `https://k-control-staging.kreesalis.com` |
| Production | `https://k-control.kreesalis.com` |

### What auto-derives from `PLATFORM_BASE_URL`

| Setting | Derived Value | Override Env Var |
|---------|---------------|------------------|
| `notification_tracking_base_url` | `{PLATFORM_BASE_URL}` | `NOTIFICATION_TRACKING_BASE_URL` |
| `password_reset_frontend_url` | `{PLATFORM_BASE_URL}/reset-password` | `PASSWORD_RESET_FRONTEND_URL` |
| `magic_link_frontend_verify_url` | `{PLATFORM_BASE_URL}/magic-link/verify` | `MAGIC_LINK_FRONTEND_VERIFY_URL` |
| `magic_link_assignee_frontend_verify_url` | `{PLATFORM_BASE_URL}/assignee/login` | `MAGIC_LINK_ASSIGNEE_FRONTEND_VERIFY_URL` |

### Where to set it

- **Local**: `backend/.env` or `backend/.env.local` → `PLATFORM_BASE_URL=http://localhost:3000`
- **K8s**: `deploy/kcontrol-v1-dev/backend-configmap.yaml` → `PLATFORM_BASE_URL: "https://k-control-dev.kreesalis.com"`
- **Docker**: `docker-compose.yml` environment section

### Email tracking URLs

When a notification email is sent, the queue processor automatically:
1. Rewrites `<a href="...">` links through `{PLATFORM_BASE_URL}/api/v1/notifications/track/click/{id}?url=...`
2. Injects a 1x1 open-tracking pixel: `{PLATFORM_BASE_URL}/api/v1/notifications/track/open/{id}`

These URLs must be reachable by the email recipient's browser — so `PLATFORM_BASE_URL` must be a publicly accessible URL in non-local environments.

---

## Checklist for New Templates

- [ ] Notification type exists in `04_dim_notification_types` (or create one)
- [ ] Channel-type mapping exists in `07_dim_notification_channel_types`
- [ ] All variable keys exist in `08_dim_template_variable_keys` (or create them)
- [ ] Template created in `10_fct_templates` with correct `notification_type_code` + `channel_code`
- [ ] Version created in `14_dtl_template_versions` with HTML/text/short bodies
- [ ] Template `active_version_id` points to the version
- [ ] Placeholders declared in `15_dtl_template_placeholders`
- [ ] Notification rule exists in `11_fct_notification_rules` mapping audit event to notification type
- [ ] Backend service emits the correct audit event with variable values in `properties`
- [ ] Test via Admin UI preview and send-test functionality
