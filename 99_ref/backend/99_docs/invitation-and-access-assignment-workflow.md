# Invitation & Access Assignment Workflow

This document explains how K-Control handles both **new users** (who don't yet have an account) and **existing users** (who already have an account) when they are invited or directly assigned to an org, workspace, or GRC role.

---

## Two Entry Paths

### Path A — Invite a New User (no account yet)

1. **Admin sends invite** via the Invitations tab (Team Member or External Auditor).
2. Backend creates a pending invitation row in `03_auth_manage.39_fct_invitations`.
3. **Email sent immediately** via the notification pipeline:
   - Standard invite → `workspace_invite_received` template ("You've been invited")
   - GRC/External Auditor invite → `workspace_invite_grc` template ("GRC Access: {role} on {org/workspace}")
4. Invitee clicks the accept link → lands on `/accept-invite?token=...`
5. If they **register** (new account): `process_registration_invites()` runs automatically on registration, finds all pending invites for that email, and auto-accepts them — adding org/workspace memberships and GRC role assignments in one shot.
6. If they **log in** with an existing account: they can explicitly accept the invite via the accept link, which calls `accept_invitation()`.

### Path B — Existing User Already in the System

If the invitee already has a K-Control account, two sub-cases apply:

#### Sub-case 1: Invited by email (existing account, pending invite)

The flow is identical to Path A steps 1–4. When the user logs in and visits `/accept-invite?token=...`, the system:
- Validates the token
- Calls `accept_invitation()` → `_auto_enroll()`:
  - **Org-scoped invite**: Upserts `31_lnk_org_memberships` with the specified role
  - **Workspace-scoped invite**: Upserts org membership first, then `36_lnk_workspace_memberships`, then assigns the GRC role group (if `grc_role_code` is set)
- Marks invite as `accepted`
- Emits an `invite_accepted` audit event

#### Sub-case 2: Admin directly adds an existing user (no invite needed)

Use the Members tab → "Add member" to add a user who already has an account. This bypasses the invite flow entirely:
- Directly inserts `31_lnk_org_memberships` or `36_lnk_workspace_memberships`
- For GRC role: use the GRC Role Assignment endpoint (`POST /api/v1/am/workspaces/{id}/members/{user_id}/grc-role`)
- No email is sent by default in this flow (direct assignment is considered synchronous/in-person)

---

## GRC Role Assignment: What Gets Set

When a GRC invite is accepted (workspace-scoped), the system calls `assign_workspace_member_grc_role()` which:
1. Looks up the scoped group for `(workspace_id, grc_role_code)` in `17_fct_user_groups`
2. Inserts `18_lnk_group_memberships` linking the user to that group
3. The group already has role assignments (`19_lnk_group_role_assignments`) giving the correct feature permissions

**Important**: GRC role assignment requires a `workspace_id`. Org-scoped GRC invites (no workspace selected) grant org membership only — the GRC role is assigned when the user is later added to a specific workspace.

---

## Notification Matrix

| Scenario | Email sent? | Template |
|---|---|---|
| New team member invite | Yes | `workspace_invite_email` |
| New external auditor invite | Yes | `workspace_invite_grc_email` |
| Existing user accepts invite | No additional email | (already received invite email) |
| Admin directly assigns existing user | No | — |
| Engagement access granted | Yes | `engagement_access_granted_email` |

---

## Email Template Variables

All invitation emails resolve these variables at send time:

| Variable | Source | Example |
|---|---|---|
| `invite.grc_role_label` | Looked up from `grc_role_code` | "Staff Auditor" |
| `invite.workspace_name` | `34_fct_workspaces.name` (or org name if no workspace) | "ISO 27001 Workspace" |
| `invite.org_name` | `29_fct_orgs.name` | "Kreesalis" |
| `invite.accept_url` | `{platform_base_url}/accept-invite?token={token}` | "https://app.kreesalis.com/accept-invite?token=..." |
| `invite.expires_in` | From `expires_in_hours` on invite | "72 hours" |

---

## Checking Notification Delivery

To verify an email was sent and delivered:

```sql
-- Check queue status
SELECT notification_type_code, recipient_email, rendered_subject, status_code, created_at
FROM "03_notifications"."20_trx_notification_queue"
WHERE recipient_email = 'user@example.com'
ORDER BY created_at DESC LIMIT 5;

-- Check SMTP delivery log
SELECT d.status, d.provider_response, d.attempted_at
FROM "03_notifications"."21_trx_delivery_log" d
JOIN "03_notifications"."20_trx_notification_queue" q ON q.id = d.notification_id
WHERE q.recipient_email = 'user@example.com'
ORDER BY d.attempted_at DESC LIMIT 5;
```

Status values: `queued` → `processing` → `sent` / `failed`

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| No email sent after invite | `notification_enabled=false` in `.env` | Set `NOTIFICATION_ENABLED=true` |
| Email queued but not sent | SMTP not configured in DB | Check `03_notifications.30_fct_smtp_config` |
| `status=failed` in queue | See `last_error` column | Check SMTP credentials / recipient domain |
| GRC role not assigned after accept | Invite was org-scoped (no workspace) | Assign to a specific workspace after org access granted |
| "Workspace scope requires..." error | Frontend sent `scope=workspace` with no `workspace_id` | Frontend now auto-falls-back to `scope=organization` |
