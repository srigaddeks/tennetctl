# Comments API

Base path: `/api/v1/cm`
Auth: Bearer JWT required on all endpoints
Permission: `comments.view` to read, `comments.create` to write

---

## Overview

The comments system supports:
- **Threaded replies** — top-level comments with nested replies (one level deep)
- **Reactions** — emoji reactions with per-user toggle, rate-limited to 30/min
- **Markdown rendering** — server-side markdown → HTML with XSS sanitization
- **Visibility** — `internal` (authenticated users only) vs `external` (customer-facing)
- **Pinning / Resolving** — requires `comments.manage` / `comments.resolve` permission
- **@Mentions** — extracted from `@[username]` syntax, triggers notifications
- **Cursor pagination** — stable ordering across concurrent inserts
- **GDPR** — anonymize all user data via admin endpoint

---

## List Comments

### GET /api/v1/cm/comments

List threaded comments for an entity. Returns top-level comments with up to 10 inline replies.

**Query params**

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| entity_type | string | yes | e.g. `task`, `risk`, `control`, `framework` |
| entity_id | UUID | yes | UUID of the entity |
| visibility | string | no | `internal` or `external` (default: both) |
| pinned_only | bool | no | Only return pinned comments |
| resolved | bool | no | Filter by resolved status |
| cursor_created_at | ISO8601 | no* | Cursor for next page (must pair with cursor_id) |
| cursor_id | UUID | no* | Cursor for next page (must pair with cursor_created_at) |
| per_page | int | no | 1–100 (default: 25) |

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...",
      "entity_type": "risk",
      "entity_id": "...",
      "parent_comment_id": null,
      "author_user_id": "...",
      "author_display_name": "Alice Chen",
      "author_email": "alice@example.com",
      "content": "This risk needs reassessment after the audit.",
      "content_format": "markdown",
      "rendered_html": "<p>This risk needs reassessment after the audit.</p>",
      "visibility": "internal",
      "is_edited": false,
      "is_deleted": false,
      "is_locked": false,
      "pinned": false,
      "resolved": false,
      "mention_user_ids": [],
      "reply_count": 2,
      "replies": [
        {
          "id": "...",
          "parent_comment_id": "...",
          "author_display_name": "Bob Smith",
          "content": "Agreed — scheduling for next sprint.",
          "reactions": [],
          "created_at": "2026-03-20T10:05:00Z"
        }
      ],
      "reactions": [
        {
          "reaction_code": "👍",
          "count": 3,
          "user_ids": ["...", "...", "..."],
          "reacted_by_me": true
        }
      ],
      "created_at": "2026-03-20T10:00:00Z",
      "updated_at": "2026-03-20T10:00:00Z"
    }
  ],
  "total": 14,
  "next_cursor": "2026-03-19T09:55:00Z,<uuid>",
  "unread_count": 2
}
```

**Cursor pagination:** Pass `next_cursor` value split by `,` as `cursor_created_at` and `cursor_id`.

---

## Create Comment

### POST /api/v1/cm/comments

Create a top-level comment or a reply.

**Request body**
```json
{
  "entity_type": "risk",
  "entity_id": "...",
  "content": "This risk **requires immediate action**. cc @[alice.chen]",
  "content_format": "markdown",
  "parent_comment_id": null,
  "visibility": "internal",
  "mention_user_ids": ["..."],
  "attachment_ids": ["..."]
}
```

| Field | Required | Description |
|-------|----------|-------------|
| entity_type | yes | Target entity type |
| entity_id | yes | Target entity UUID |
| content | yes | Comment body (max 50,000 chars) |
| content_format | no | `markdown` (default) or `plain_text` |
| parent_comment_id | no | UUID — set to create a reply |
| visibility | no | `internal` (default) or `external` |
| mention_user_ids | no | UUIDs of mentioned users (triggers notifications) |
| attachment_ids | no | UUIDs of pre-uploaded attachments to link |

**Response** `201 Created` — `CommentResponse`

---

## Get Comment

### GET /api/v1/cm/comments/{comment_id}

Get a single comment with full detail including edit history summary.

---

## Edit Comment

### PATCH /api/v1/cm/comments/{comment_id}

Edit comment content. Author only.

**Request body**
```json
{ "content": "Updated content here" }
```

**Response** `200 OK` — previous version is saved to `04_trx_comment_edits`.

---

## Delete Comment

### DELETE /api/v1/cm/comments/{comment_id}

Soft-delete. Content is replaced with `[deleted]`, author info retained.

Returns `204 No Content`.

---

## Batch Comment Counts

### GET /api/v1/cm/comments/counts

Get comment counts for multiple entities in one call — used for badge indicators on list pages.

**Query params**

| Param | Type | Description |
|-------|------|-------------|
| entity_type | string | e.g. `task`, `risk` |
| entity_ids | string | Comma-separated UUIDs (max 100) |

**Response** `200 OK`
```json
{
  "counts": {
    "<entity_id_1>": 5,
    "<entity_id_2>": 12,
    "<entity_id_3>": 0
  }
}
```

---

## Mention Inbox

### GET /api/v1/cm/comments/mentions

List comments where the current user has been @mentioned.

**Query params:** `per_page` (default 25, max 100), `unread_only` (bool)

**Response** `200 OK` — `MentionsListResponse` with `items` and `total`.

---

## Mark Read

### POST /api/v1/cm/comments/mark-read

Mark all comments on an entity as read for the current user.

**Request body**
```json
{
  "entity_type": "risk",
  "entity_id": "..."
}
```

**Response** `200 OK` — `{ "marked": 7 }`

---

## Edit History

### GET /api/v1/cm/comments/{comment_id}/history

Get the edit history for a comment (immutable audit trail).

**Response** `200 OK`
```json
{
  "items": [
    {
      "id": "...",
      "comment_id": "...",
      "previous_content": "Original text before edit",
      "edited_by": "...",
      "edited_at": "2026-03-20T10:15:00Z"
    }
  ],
  "total": 2
}
```

---

## Pin / Unpin

### POST /api/v1/cm/comments/{comment_id}/pin

Pin a comment. Requires `comments.manage` permission.

### DELETE /api/v1/cm/comments/{comment_id}/pin

Unpin a comment. Returns `204 No Content`.

---

## Resolve / Unresolve

### POST /api/v1/cm/comments/{comment_id}/resolve

Resolve a comment thread. Requires `comments.resolve` permission.

### DELETE /api/v1/cm/comments/{comment_id}/resolve

Unresolve a comment thread. Returns `204 No Content`.

---

## Reactions

### GET /api/v1/cm/comments/{comment_id}/reactions

Get reaction summaries for a comment.

**Response** `200 OK`
```json
{
  "reactions": [
    { "reaction_code": "👍", "count": 5, "user_ids": ["..."], "reacted_by_me": true },
    { "reaction_code": "🎉", "count": 2, "user_ids": ["..."], "reacted_by_me": false }
  ]
}
```

### POST /api/v1/cm/comments/{comment_id}/reactions

Toggle a reaction (add if not present, remove if already reacted).

**Rate limit:** 30 reactions per minute per user.

**Request body**
```json
{ "reaction_code": "👍" }
```

**Response** `200 OK` — updated `ReactionListResponse`

### DELETE /api/v1/cm/comments/{comment_id}/reactions/{reaction_code}

Explicitly remove a reaction. Returns `204 No Content`.

---

## Admin Endpoints

All admin endpoints require platform-level permission.

### DELETE /api/v1/cm/comments/{comment_id}/admin

Hard-delete a comment (platform admin only). Irreversible.

### POST /api/v1/cm/comments/gdpr-delete

Anonymize all comment data for a user (GDPR right to be forgotten).

**Request body**
```json
{ "user_id": "..." }
```

**Response** `200 OK` — `{ "anonymized_count": 47 }`

---

## Permissions

| Permission | Required for |
|-----------|-------------|
| `comments.view` | GET /comments, GET /comments/{id} |
| `comments.create` | POST /comments |
| `comments.update` | PATCH /comments/{id} |
| `comments.delete` | DELETE /comments/{id} |
| `comments.manage` | POST/DELETE /comments/{id}/pin |
| `comments.resolve` | POST/DELETE /comments/{id}/resolve |

---

## Notes

- Comments use **cursor-based pagination** for stable ordering. Offset pagination is not supported.
- `content_format: "markdown"` — server renders markdown to `rendered_html`. Clients should render `rendered_html` when present.
- @Mention syntax: `@[username]` — server extracts mentions and fires notifications asynchronously.
- Reactions are **toggled** — calling POST with a reaction you already have will remove it.
- `visibility: "external"` requires `comments.manage` permission to set.
