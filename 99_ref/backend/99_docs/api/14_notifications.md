# Notification System API

Enterprise-grade notification service with email and web push channels, versioned templates, hierarchical user preferences, and audit event-driven dispatch.

## Schema: `03_notifications`

## Base Path: `/api/v1/notifications`

---

## Endpoints Summary

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | GET | /config | None | All dimension data (channels, categories, types, variable keys) |
| 2 | GET | /preferences | Bearer | Get current user's notification preferences |
| 3 | PUT | /preferences | Bearer | Set a notification preference |
| 4 | DELETE | /preferences/{id} | Bearer | Delete a preference override |
| 5 | GET | /history | Bearer | Get current user's notification history |
| 6 | POST | /web-push/subscribe | Bearer | Subscribe to web push notifications |
| 7 | DELETE | /web-push/{subscription_id} | Bearer | Unsubscribe from web push |
| 8 | GET | /queue | Bearer | List queue items (admin) |
| 9 | GET | /queue/{notification_id} | Bearer | Get queue item detail with delivery logs |
| 10 | POST | /queue/{notification_id}/retry | Bearer | Retry a failed queue item |
| 11 | POST | /queue/{notification_id}/dead-letter | Bearer | Force dead-letter a queue item |
| 12 | GET | /smtp/config | Bearer | Get SMTP configuration |
| 13 | PUT | /smtp/config | Bearer | Save SMTP configuration |
| 14 | POST | /smtp/test | Bearer | Test SMTP connection |
| 15 | POST | /send-test | Bearer | Send a test notification |
| 16 | GET | /reports/delivery | Bearer | Get delivery report for a time period |
| 17 | GET | /templates | Bearer | List notification templates |
| 18 | POST | /templates | Bearer | Create a notification template |
| 19 | POST | /templates/render-raw | Bearer | Render raw template string with variables |
| 20 | GET | /templates/{template_id} | Bearer | Get template with embedded versions |
| 21 | PATCH | /templates/{template_id} | Bearer | Update template (including version activation) |
| 22 | POST | /templates/{template_id}/versions | Bearer | Create a new template version |
| 23 | POST | /templates/{template_id}/preview | Bearer | Preview rendered template |
| 24 | GET | /broadcasts | Bearer | List broadcasts (limit/offset paginated) |
| 25 | POST | /broadcasts | Bearer | Create a broadcast |
| 26 | POST | /broadcasts/{broadcast_id}/send | Bearer | Send a broadcast |
| 27 | GET | /releases | Bearer | List platform releases |
| 28 | GET | /releases/{release_id} | Bearer | Get a single release |
| 29 | POST | /releases | Bearer | Create a draft release |
| 30 | PATCH | /releases/{release_id} | Bearer | Update release details |
| 31 | POST | /releases/{release_id}/publish | Bearer | Publish release (optional broadcast) |
| 32 | POST | /releases/{release_id}/archive | Bearer | Archive a release |
| 33 | GET | /incidents | Bearer | List platform incidents |
| 34 | GET | /incidents/{incident_id} | Bearer | Get incident with status updates |
| 35 | POST | /incidents | Bearer | Create an incident (auto-broadcasts critical) |
| 36 | PATCH | /incidents/{incident_id} | Bearer | Update incident details |
| 37 | POST | /incidents/{incident_id}/updates | Bearer | Post incident status update |
| 38 | GET | /releases/public | Bearer | List published releases (no permission required) |
| 39 | GET | /incidents/active | Bearer | List active incidents (no permission required) |
| 40 | GET | /variable-queries | Bearer | List custom variable queries |
| 41 | POST | /variable-queries | Bearer | Create a custom variable query |
| 42 | GET | /variable-queries/{query_id} | Bearer | Get variable query detail |
| 43 | PATCH | /variable-queries/{query_id} | Bearer | Update a variable query |
| 44 | DELETE | /variable-queries/{query_id} | Bearer | Delete a variable query |
| 45 | POST | /variable-queries/{query_id}/preview | Bearer | Preview query with real data |
| 46 | POST | /variable-queries/test | Bearer | Test ad-hoc SQL before saving |

### Org-Scoped Broadcasts (Base: `/api/v1/am/orgs`)

| # | Method | Path | Auth | Description |
|---|--------|------|------|-------------|
| 1 | GET | /orgs/{org_id}/broadcasts | Bearer | List org broadcasts (org membership auth) |
| 2 | POST | /orgs/{org_id}/broadcasts | Bearer | Create org broadcast (org membership auth) |
| 3 | POST | /orgs/{org_id}/broadcasts/{broadcast_id}/send | Bearer | Send org broadcast (org membership auth) |

**Total: 49 endpoints** (46 under `/api/v1/notifications` + 3 org-scoped under `/api/v1/am/orgs`)

---

## Permission Prefixes

| Module | Permission Prefix | Actions |
|--------|-------------------|---------|
| Templates | `notification_templates` | view, create, update |
| Preferences | `notification_preferences` | view, update |
| Broadcasts | `notification_broadcasts` | view, create |

---

## Config

### GET /config

Returns all notification dimension data in a single call. No auth required — this is static reference data.

**Response:**
```json
{
  "channels": [
    { "id": "...", "code": "email", "name": "Email", "is_available": true, "sort_order": 1 }
  ],
  "categories": [
    { "id": "...", "code": "security", "name": "Security", "is_mandatory": true, "sort_order": 1 }
  ],
  "types": [
    {
      "id": "...", "code": "password_reset", "name": "Password Reset",
      "category_code": "security", "is_mandatory": true,
      "default_enabled": true, "cooldown_seconds": null
    }
  ],
  "variable_keys": [
    {
      "id": "...", "code": "user.display_name", "name": "User Display Name",
      "data_type": "string", "example_value": "John Doe",
      "resolution_source": "user_property", "resolution_key": "display_name"
    }
  ]
}
```

---

## Preferences

### GET /preferences

Returns the current user's effective notification preferences.

### PUT /preferences

Set a notification preference at a specific hierarchy level.

**Request:**
```json
{
  "scope_level": "type",
  "channel_code": "email",
  "notification_type_code": "org_member_added",
  "is_enabled": false
}
```

Scope levels: `global`, `channel`, `category`, `type`

**Preference hierarchy** (most specific wins):
```
mandatory flag → type-level → category-level → channel-level → global → default
```

### DELETE /preferences/{id}

Remove a preference override (reverts to parent level default).

---

## Templates

### GET /templates

List all notification templates.

### GET /templates/{template_id}

Returns a single template with all its versions embedded.

**Response:**
```json
{
  "id": "...",
  "code": "password_reset_email",
  "name": "Password Reset Email",
  "notification_type_code": "password_reset",
  "channel_code": "email",
  "active_version_id": "...",
  "is_active": true,
  "versions": [
    {
      "id": "...", "version_number": 2, "subject_line": "Reset your password",
      "body_html": "...", "is_active": true, "created_at": "..."
    },
    {
      "id": "...", "version_number": 1, "subject_line": "Password reset",
      "body_html": "...", "is_active": true, "created_at": "..."
    }
  ]
}
```

### POST /templates

Create a notification template.

**Request:**
```json
{
  "code": "password_reset_email",
  "name": "Password Reset Email",
  "description": "Email template for password reset OTP",
  "notification_type_code": "password_reset",
  "channel_code": "email",
  "base_template_id": null
}
```

### POST /templates/render-raw

Render an arbitrary template string with provided variables — no stored template required. Useful for previewing inline broadcast content before saving.

**Request:**
```json
{
  "subject": "Hello {{user.display_name}}",
  "body_html": "<p>Hi {{user.first_name}}, welcome to {{platform.name}}!</p>",
  "body_text": "Hi {{user.first_name}}, welcome to {{platform.name}}!",
  "variables": {
    "user.display_name": "John Doe",
    "user.first_name": "John",
    "platform.name": "kcontrol"
  }
}
```

**Response:** `PreviewTemplateResponse` — rendered subject, HTML, and text.

### PATCH /templates/{template_id}

Update a template. To activate a specific version (rollback), include `active_version_id`.

**Request:**
```json
{
  "name": "Updated Name",
  "active_version_id": "version-uuid-to-activate"
}
```

### POST /templates/{template_id}/versions

Create a new version (auto-activated).

**Request:**
```json
{
  "subject_line": "Reset your {{platform.name}} password",
  "body_html": "<h1>Hello {{user.display_name}}</h1><p>Your reset code: {{token}}</p>",
  "body_text": "Hello {{user.display_name}}, your reset code: {{token}}",
  "body_short": "Your password reset code: {{token}}",
  "change_notes": "Initial version"
}
```

### POST /templates/{template_id}/preview

Preview rendered template with sample data.

**Request:**
```json
{
  "variables": {
    "user.display_name": "John Doe",
    "platform.name": "kcontrol",
    "token": "ABC123"
  }
}
```

### Template Variables

Templates use `{{variable_key}}` Jinja2 syntax. Each variable has a **resolution source**
that tells the backend exactly where to fetch the value — no manual wiring needed.
All available variables are returned in `GET /config`.

| Variable | Resolution Source | Resolves From | Example |
|----------|------------------|---------------|---------|
| `user.display_name` | `user_property` | Recipient's `display_name` property | John Doe |
| `user.email` | `user_property` | Recipient's `email` property | john@example.com |
| `user.first_name` | `user_property` | Recipient's `first_name` property | John |
| `user.last_name` | `user_property` | Recipient's `last_name` property | Doe |
| `user.username` | `user_property` | Recipient's `username` property | johndoe |
| `org.name` | `org` | Org fact table `name` column | Acme Corp |
| `org.slug` | `org` | Org fact table `slug` column | acme-corp |
| `workspace.name` | `workspace` | Workspace fact table `name` column | Engineering |
| `workspace.slug` | `workspace` | Workspace fact table `slug` column | engineering |
| `action_url` | `audit_property` | Audit event properties | https://app.example.com/verify |
| `token` | `audit_property` | Audit event properties | abc123def456 |
| `platform.name` | `settings` | App settings `notification_from_name` | kcontrol |
| `expiry_hours` | `audit_property` | Audit event properties | 24 |
| `ip_address` | `audit_property` | Audit event properties | 192.168.1.1 |
| `device_info` | `audit_property` | Audit event properties | Chrome on macOS |
| `timestamp` | `computed` | Generated at render time | 2026-03-15 14:30:00 UTC |
| `actor.display_name` | `actor_property` | Actor's `display_name` property | Jane Admin |
| `actor.email` | `actor_property` | Actor's `email` property | jane@example.com |
| `role.name` | `audit_property` | Audit event properties | Workspace Admin |
| `api_key.name` | `audit_property` | Audit event properties | Production Key |
| `broadcast.title` | `audit_property` | Audit event properties | Important Update |
| `broadcast.body` | `audit_property` | Audit event properties | Please read... |
| `unsubscribe_url` | `computed` | Generated from tracking base URL | https://app.example.com/settings/notifications |
| `group.name` | `user_group` | User's primary group name | Engineering Team |
| `group.code` | `user_group` | User's primary group code | engineering |
| `group.description` | `user_group` | User's primary group description | Platform engineering team |
| `tenant.key` | `tenant` | Tenant identifier | acme |
| `tenant.user_count` | `tenant` | Active user count in tenant | 150 |
| `tenant.org_count` | `tenant` | Active org count in tenant | 5 |
| `release.version` | `audit_property` | Release version number | v2.1.0 |
| `release.title` | `audit_property` | Release title | Performance Improvements |
| `release.summary` | `audit_property` | Release summary | Bug fixes and improvements |
| `release.changelog_url` | `audit_property` | Changelog URL | `https://docs.example.com/changelog` |
| `incident.title` | `audit_property` | Incident title | API Latency Degradation |
| `incident.severity` | `audit_property` | Incident severity | major |
| `incident.status` | `audit_property` | Incident status | investigating |
| `incident.affected_components` | `audit_property` | Affected components | API, Dashboard |

**Resolution sources** — the backend knows how to fetch each variable automatically:
- `user_property` — queries `05_dtl_user_properties` by recipient user_id
- `actor_property` — queries `05_dtl_user_properties` by actor_id (who triggered the event)
- `user_group` — queries `17_fct_user_groups` via group memberships (primary group)
- `tenant` — resolves tenant-level aggregates (user count, org count) and metadata
- `org` — queries `29_fct_orgs` by org_id from audit event properties
- `workspace` — queries `34_fct_workspaces` by workspace_id from audit event properties
- `settings` — reads from application settings (frozen dataclass)
- `audit_property` — reads directly from the audit event's properties dict
- `computed` — calculated at render time (timestamps, URLs)

New resolution sources can be added by extending `VariableResolutionSource` in constants.py and adding a resolver method to `VariableResolver`.

### Base Templates (Layout Inheritance)

Set `base_template_id` on a template to inherit a layout. The base template must contain `{{content}}` where the child template's rendered HTML will be inserted. This enables shared email headers/footers.

---

## Broadcasts

Admin-initiated notifications to scoped audiences. Broadcasts support **personalization** (per-recipient template variables like `{{user.display_name}}`), **multi-channel delivery** (email + web push based on channel-type matrix), and **critical alert bypass** (skips user preferences for urgent notifications).

### GET /broadcasts

**Query params:** `limit` (default 25, max 200), `offset` (default 0)

### POST /broadcasts

**Request:**
```json
{
  "title": "Hello {{user.display_name}}, Platform Maintenance Scheduled",
  "body_text": "Scheduled maintenance on March 20th.",
  "body_html": "<p>Hi {{user.first_name}}, scheduled maintenance on <strong>March 20th</strong>.</p>",
  "scope": "global",
  "priority_code": "high",
  "severity": "medium",
  "is_critical": false,
  "notification_type_code": "platform_maintenance",
  "template_code": null
}
```

| Field | Description |
|-------|-------------|
| `scope` | `global` (all users), `org` (requires `scope_org_id`), `workspace` (requires `scope_workspace_id`) |
| `severity` | Optional: `critical`, `high`, `medium`, `low`, `info` |
| `is_critical` | When `true`, bypasses user preference checks and auto-escalates priority |
| `template_code` | Optional: use a specific template instead of inline body |
| `notification_type_code` | Default: `global_broadcast`. Use `platform_incident`, `platform_release`, `platform_maintenance` for typed broadcasts |

### POST /broadcasts/{broadcast_id}/send

Triggers recipient resolution and bulk queue insertion. For each recipient:
1. Resolves per-recipient template variables (user properties from DB)
2. Renders `title` and `body` through Jinja2 with `{{user.display_name}}`, `{{platform.name}}`, etc.
3. Resolves all available channels from the channel-type matrix (not just email)
4. Resolves delivery address (email or push endpoint) per channel
5. Inserts personalized queue entries

Returns the broadcast with total recipients count.

### Broadcast Personalization

Broadcast titles and bodies support Jinja2 template syntax. Variables resolved per-recipient:

| Variable | Source | Example |
|----------|--------|---------|
| `{{user.display_name}}` | Recipient's user properties | John Doe |
| `{{user.email}}` | Recipient's email | john@example.com |
| `{{user.first_name}}` | Recipient's first name | John |
| `{{user.username}}` | Recipient's username | johndoe |
| `{{platform.name}}` | App settings | kcontrol |
| `{{broadcast.title}}` | Broadcast title | Important Update |
| `{{broadcast.body}}` | Broadcast body text | Details... |

---

## Custom Variable Queries

Admin-defined SQL queries that resolve to template variables at dispatch time. Each query accepts bind parameters (e.g., `$user_id`, `$org_id`) and returns columns that become `{{ custom.<query_code>.<column> }}` variables.

### POST /variable-queries

Create a custom variable query.

**Request:**
```json
{
  "code": "user_task_stats",
  "name": "User Task Statistics",
  "description": "Count tasks by status for a user in an org",
  "sql_template": "SELECT COUNT(*) as total_tasks, COUNT(*) FILTER (WHERE status = 'overdue') as overdue_tasks FROM \"07_tasks\".\"02_fct_tasks\" WHERE assignee_user_id = $1 AND org_id = $2",
  "bind_params": [
    { "key": "$user_id", "position": 1, "source": "context", "required": true },
    { "key": "$org_id", "position": 2, "source": "audit_property", "required": false }
  ],
  "result_columns": [
    { "name": "total_tasks", "data_type": "integer", "default_value": "0" },
    { "name": "overdue_tasks", "data_type": "integer", "default_value": "0" }
  ],
  "timeout_ms": 3000
}
```

Creates variable keys: `custom.user_task_stats.total_tasks` and `custom.user_task_stats.overdue_tasks` in `08_dim_template_variable_keys`.

### POST /variable-queries/test

Test ad-hoc SQL before saving. Executes in a read-only transaction with timeout.

**Request:**
```json
{
  "sql_template": "SELECT COUNT(*) as cnt FROM \"07_tasks\".\"02_fct_tasks\" WHERE assignee_user_id = $1",
  "bind_params": [{ "key": "$user_id", "position": 1, "source": "context", "required": true }],
  "use_my_profile": true
}
```

### POST /variable-queries/{query_id}/preview

Run a saved query with real data — your profile auto-fills `$user_id`, optional `audit_event_id` pulls context from a real audit event.

### Bind Parameters

| Key | Source | Always Available |
|-----|--------|------------------|
| `$user_id` | Recipient user ID | Yes |
| `$tenant_key` | Tenant key | Yes |
| `$actor_id` | Audit event actor | At dispatch time |
| `$org_id` | Audit event properties | At dispatch time |
| `$workspace_id` | Audit event properties | At dispatch time |
| `$framework_id` | Audit event properties | At dispatch time |
| `$control_id` | Audit event properties | At dispatch time |
| `$task_id` | Audit event properties | At dispatch time |
| `$risk_id` | Audit event properties | At dispatch time |

### Security

- SQL must be a `SELECT` statement — DDL/DML keywords are rejected
- Executed with `SET LOCAL default_transaction_read_only = ON` and `SET LOCAL statement_timeout`
- Configurable per-query timeout (100ms–10000ms)
- On failure at dispatch time, falls back to `default_value` per column — never blocks notification delivery

---

## Releases

Platform release notes with draft/publish/archive workflow. Publishing a release can auto-broadcast to all users.

### GET /releases

List releases with optional status filter.

**Query params:** `limit` (default 50, max 200), `offset` (default 0), `status` (draft, published, archived)

### POST /releases

Create a draft release.

**Request:**
```json
{
  "version": "v2.1.0",
  "title": "Performance Improvements",
  "summary": "Bug fixes and 3x faster API response times",
  "body_markdown": "## What's New\n- Feature A\n- Bug fix B",
  "body_html": null,
  "changelog_url": "https://docs.example.com/changelog/v2.1.0",
  "release_date": "2026-03-20T00:00:00"
}
```

### PATCH /releases/{release_id}

Update a release (title, summary, body, changelog URL).

### POST /releases/{release_id}/publish?notify=true

Publish a draft release. When `notify=true` (default), creates a global broadcast with notification type `platform_release` that can be sent to all users.

**Response includes** `broadcast_id` when notify is enabled.

### POST /releases/{release_id}/archive

Archive a published or draft release. Cannot be undone.

### Release Lifecycle

```
draft → published (with optional broadcast) → archived
```

---

## Incidents

Platform incident tracking with severity classification, status updates, and auto-broadcast for critical/major incidents.

### GET /incidents

List incidents with optional status filter.

**Query params:** `limit` (default 50, max 200), `offset` (default 0), `status` (investigating, identified, monitoring, resolved)

### POST /incidents

Create an incident. Critical/major incidents auto-create a global broadcast when `notify_users=true`.

**Request:**
```json
{
  "title": "API Latency Degradation",
  "description": "Users experiencing increased response times on API endpoints",
  "severity": "major",
  "affected_components": "API, Dashboard",
  "started_at": "2026-03-14T10:30:00",
  "notify_users": true
}
```

| Severity | Auto-broadcast | Priority |
|----------|----------------|----------|
| `critical` | Yes (is_critical=true) | critical |
| `major` | Yes (is_critical=true) | high |
| `minor` | Yes (is_critical=false) | high |
| `informational` | Yes (is_critical=false) | high |

### PATCH /incidents/{incident_id}

Update incident details (title, description, severity, affected_components).

### POST /incidents/{incident_id}/updates

Post a status update. Automatically transitions the incident status. When `is_public=true` and `notify_users=true`, creates a broadcast for the update.

**Request:**
```json
{
  "status": "identified",
  "message": "Root cause identified: database connection pool exhaustion",
  "is_public": true,
  "notify_users": true
}
```

**Response** includes the incident with all updates embedded.

### Incident Lifecycle

```
investigating → identified → monitoring → resolved
```

Each transition is recorded as an incident update with timestamp and message. Resolving an incident sets `resolved_at`.

---

## Web Push

### POST /web-push/subscribe

**Request:**
```json
{
  "endpoint": "https://fcm.googleapis.com/fcm/send/...",
  "p256dh_key": "BNcRd...",
  "auth_key": "tBHI...",
  "user_agent": "Chrome/120"
}
```

---

## Tracking (Public)

### GET /track/open/{notification_id}

Returns a 1x1 transparent GIF pixel. Records an `opened` tracking event.

### GET /track/click/{notification_id}?url={target_url}

Records a `clicked` tracking event, then 302 redirects to `target_url`.

---

## Queue & Delivery

Notifications flow through a queue with priority-based processing:

1. **Audit event** triggers notification dispatch
2. **Dispatcher** resolves recipients, checks preferences, renders templates, inserts into queue
3. **Queue processor** (background task) polls with `SELECT ... FOR UPDATE SKIP LOCKED`
4. **Channel provider** sends via SMTP or Web Push API
5. **Delivery log** records each attempt with provider response
6. **Retry** on failure with exponential backoff (base delay from priority config)
7. **Dead letter** after max attempts exhausted

### GET /queue

List queue items for admin monitoring.

**Query params:** `status_code`, `channel_code`, `limit` (default 50, max 200), `offset` (default 0)

### GET /queue/{notification_id}

Get queue item detail including delivery logs and tracking events.

### POST /queue/{notification_id}/retry

Reset a failed item back to `queued` status for reprocessing.

### POST /queue/{notification_id}/dead-letter

Force a queue item to `dead_letter` status.

**Request:**
```json
{ "reason": "Manual override — unresolvable delivery failure" }
```

### GET /smtp/config

Get the current SMTP configuration.

### PUT /smtp/config

Save SMTP configuration (host, port, credentials, from address).

### POST /smtp/test

Send a test email to verify SMTP connectivity.

### POST /send-test

Send a test notification to the authenticated user on a specified channel.

### GET /reports/delivery

Get a delivery report summarising send/fail/bounce rates.

**Query params:** `period_hours` (default 24, range 1–720)

### Priority Levels

| Priority | Weight | Max Retries | Base Delay |
|----------|--------|-------------|------------|
| critical | 100 | 5 | 30s |
| high | 75 | 4 | 60s |
| normal | 50 | 3 | 120s |
| low | 25 | 2 | 300s |

### Notification Statuses

`queued` → `processing` → `sent` → `delivered` → `opened` → `clicked`

Error path: `failed` (retryable) → `dead_letter` (exhausted)

Other terminal: `bounced`, `suppressed` (user opted out)

---

## Configuration (Environment Variables)

| Variable | Default | Description |
|----------|---------|-------------|
| `NOTIFICATION_ENABLED` | `false` | Master toggle for notification system |
| `NOTIFICATION_EMAIL_PROVIDER` | — | Email provider type (`smtp`) |
| `NOTIFICATION_SMTP_HOST` | — | SMTP server hostname |
| `NOTIFICATION_SMTP_PORT` | `587` | SMTP server port |
| `NOTIFICATION_SMTP_USER` | — | SMTP username |
| `NOTIFICATION_SMTP_PASSWORD` | — | SMTP password |
| `NOTIFICATION_FROM_EMAIL` | — | Sender email address |
| `NOTIFICATION_FROM_NAME` | `kcontrol` | Sender display name |
| `NOTIFICATION_VAPID_PRIVATE_KEY` | — | VAPID private key for web push |
| `NOTIFICATION_VAPID_PUBLIC_KEY` | — | VAPID public key for web push |
| `NOTIFICATION_VAPID_CLAIMS_EMAIL` | — | VAPID claims email |
| `NOTIFICATION_QUEUE_POLL_INTERVAL_SECONDS` | `5` | Queue polling interval |
| `NOTIFICATION_QUEUE_BATCH_SIZE` | `50` | Notifications per batch |
| `NOTIFICATION_EMAIL_RATE_LIMIT_PER_MINUTE` | `100` | Email rate limit |
| `NOTIFICATION_PUSH_RATE_LIMIT_PER_MINUTE` | `200` | Push rate limit |
| `NOTIFICATION_TRACKING_BASE_URL` | — | Public URL for tracking pixel/clicks |

---

## Audit Events

All notification operations emit audit events to `03_auth_manage.40_aud_events`:

| Event Type | Category | When |
|------------|----------|------|
| `template_created` | notification | Template created |
| `template_version_created` | notification | New template version |
| `template_activated` | notification | Template version activated |
| `broadcast_created` | notification | Broadcast created |
| `broadcast_sent` | notification | Broadcast dispatched |
| `notification_preference_changed` | notification | User preference changed |
| `web_push_subscribed` | notification | Web push subscription |
| `web_push_unsubscribed` | notification | Web push unsubscription |
| `notification_queued` | notification | Notification entered queue |
| `notification_sent` | notification | Notification sent |
| `notification_failed` | notification | Delivery failed |
| `release_created` | notification | Release created |
| `release_published` | notification | Release published (with broadcast) |
| `incident_created` | notification | Incident created |
| `incident_updated` | notification | Incident status update posted |

---

## Feature Flags

| Code | Category | Access Mode |
|------|----------|-------------|
| `notification_system` | admin | permissioned |
| `notification_email` | admin | permissioned |
| `notification_web_push` | admin | permissioned |
| `notification_templates` | admin | permissioned |
| `notification_preferences` | admin | authenticated |
| `notification_broadcasts` | admin | permissioned |
| `org_broadcasts` | org | permissioned |

---

## Public Read-Only Endpoints

These endpoints require JWT authentication but **no platform permission**. Any authenticated user in the tenant can read published releases and active incidents.

### GET /releases/public

List published releases only.

**Query params:** `limit` (default 50, max 200), `offset` (default 0)

**Response:** `ReleaseListResponse` — same structure as `GET /releases` but filtered to `status = 'published'`.

### GET /incidents/active

List non-resolved incidents (status: investigating, identified, monitoring).

**Query params:** `limit` (default 50, max 200), `offset` (default 0)

**Response:** `IncidentListResponse` — same structure as `GET /incidents` but filtered to `status != 'resolved'`.

---

## Org-Scoped Broadcasts

Org admins can create and send broadcasts scoped to their organization without requiring platform-level `notification_broadcasts` permission. Authentication is via org membership — the caller must be an active member of the specified org.

**Base path:** `/api/v1/am/orgs/{org_id}/broadcasts`

### GET /orgs/{org_id}/broadcasts

List broadcasts scoped to the specified organization.

**Auth:** Bearer JWT + org membership
**Response:** Array of `BroadcastResponse` objects filtered to `scope_org_id = org_id`.

### POST /orgs/{org_id}/broadcasts

Create a broadcast scoped to the organization. The `scope` is automatically set to `org` and `scope_org_id` is pinned to the path parameter.

**Auth:** Bearer JWT + org membership

**Request:**

```json
{
  "title": "Team Update",
  "body_text": "Important announcement for the organization.",
  "body_html": "<p>Important announcement.</p>",
  "priority_code": "normal",
  "is_critical": false,
  "notification_type_code": "global_broadcast"
}
```

**Response:** Created `BroadcastResponse` object.

### POST /orgs/{org_id}/broadcasts/{broadcast_id}/send

Send an org broadcast. The broadcast must belong to the specified org.

**Auth:** Bearer JWT + org membership
**Response:** Updated `BroadcastResponse` with `total_recipients` count.
