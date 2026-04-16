# Tasks API

Base path: `/api/v1/tk`
Auth: Bearer JWT required on all endpoints (`get_current_access_claims`)

---

## Dimensions

### GET /api/v1/tk/task-types
Returns all task type dimension records.

**Response** `200 OK`
```json
[
  { "code": "remediation", "name": "Remediation", "description": "..." },
  { "code": "review",      "name": "Review",      "description": "..." }
]
```

### GET /api/v1/tk/task-priorities
Returns all priority dimension records ordered by sort_order.

**Response** `200 OK`
```json
[
  { "code": "critical", "name": "Critical", "sort_order": 1 },
  { "code": "high",     "name": "High",     "sort_order": 2 },
  { "code": "medium",   "name": "Medium",   "sort_order": 3 },
  { "code": "low",      "name": "Low",      "sort_order": 4 }
]
```

### GET /api/v1/tk/task-statuses
Returns all status dimension records with terminal flag and sort_order.

**Response** `200 OK`
```json
[
  { "code": "open",                 "name": "Open",                 "is_terminal": false, "sort_order": 1 },
  { "code": "in_progress",         "name": "In Progress",          "is_terminal": false, "sort_order": 2 },
  { "code": "pending_verification","name": "Pending Verification", "is_terminal": false, "sort_order": 3 },
  { "code": "resolved",            "name": "Resolved",             "is_terminal": true,  "sort_order": 4 },
  { "code": "cancelled",           "name": "Cancelled",            "is_terminal": true,  "sort_order": 5 }
]
```

---

## Tasks

### GET /api/v1/tk/tasks
List tasks with optional filters. Returns paginated results.

**Query Parameters**

| Parameter          | Type    | Description                                      |
|--------------------|---------|--------------------------------------------------|
| `org_id`           | UUID    | Filter by organization                           |
| `workspace_id`     | UUID    | Filter by workspace                              |
| `status_code`      | string  | Filter by status (e.g. `open`, `in_progress`)    |
| `assignee_user_id` | UUID    | Filter by assigned user                          |
| `reporter_user_id` | UUID    | Filter by reporter user                          |
| `entity_type`      | string  | Linked entity type (`control`, `risk`, `framework`, `test`) |
| `entity_id`        | UUID    | Linked entity ID                                 |
| `priority_code`    | string  | Filter by priority (`critical`, `high`, `medium`, `low`) |
| `task_type_code`   | string  | Filter by task type code                         |
| `due_date_from`    | date    | ISO date string (YYYY-MM-DD) inclusive lower bound on due_date |
| `due_date_to`      | date    | ISO date string (YYYY-MM-DD) inclusive upper bound on due_date |
| `is_overdue`       | boolean | When `true`, returns only overdue tasks          |
| `sort_by`          | string  | Column to sort by: `created_at`, `due_date`, `priority_code`, `updated_at` (default: `created_at`) |
| `sort_dir`         | string  | `asc` or `desc` (default: `desc`)               |
| `limit`            | int     | Max results (1–500, default: 100)               |
| `offset`           | int     | Pagination offset (default: 0)                  |

**Response** `200 OK`
```json
{
  "items": [ /* TaskDetailResponse[] */ ],
  "total": 42
}
```

### GET /api/v1/tk/tasks/summary
Returns aggregate counts for the dashboard summary bar. Scoped by org/workspace if provided.

**Query Parameters**: `org_id` (UUID, optional), `workspace_id` (UUID, optional)

**Response** `200 OK`
```json
{
  "open_count": 12,
  "in_progress_count": 5,
  "pending_verification_count": 3,
  "resolved_count": 20,
  "cancelled_count": 2,
  "overdue_count": 4,
  "resolved_this_week_count": 7,
  "by_type": [
    { "task_type_code": "remediation", "task_type_name": "Remediation", "count": 10 }
  ]
}
```

### GET /api/v1/tk/tasks/export
Export tasks as a CSV file. Accepts same filters as list (except sort/pagination).
Returns `Content-Type: text/csv` with `Content-Disposition: attachment; filename=tasks_export.csv`.
Maximum 5 000 rows per export.

**Query Parameters**: `org_id`, `workspace_id`, `status_code`, `priority_code`, `task_type_code`, `assignee_user_id`, `is_overdue`

### POST /api/v1/tk/tasks/bulk-update
Update up to 100 tasks in one call (status, priority, or assignee).

**Request Body**
```json
{
  "task_ids": ["<uuid>", "<uuid>"],
  "status_code":       "resolved",
  "priority_code":     "high",
  "assignee_user_id":  "<uuid>"
}
```
All fields except `task_ids` are optional. Only provided fields are applied.

**Response** `200 OK`
```json
{ "updated_count": 2, "failed_ids": [] }
```

### GET /api/v1/tk/tasks/{task_id}
Get a single task with full detail including EAV properties.

**Response** `200 OK` — `TaskDetailResponse` (see schema below)

### POST /api/v1/tk/tasks
Create a new task.

**Request Body**
```json
{
  "org_id":            "<uuid>",
  "workspace_id":      "<uuid>",
  "task_type_code":    "remediation",
  "priority_code":     "medium",
  "title":             "Fix control gap in access review",
  "description":       "Optional longer text",
  "entity_type":       "control",
  "entity_id":         "<uuid>",
  "assignee_user_id":  "<uuid>",
  "due_date":          "2026-04-30",
  "start_date":        "2026-03-20",
  "estimated_hours":   8.0,
  "acceptance_criteria": "Evidence uploaded and approved",
  "remediation_plan":  "Update access policy document"
}
```

**Response** `201 Created` — `TaskDetailResponse`

### PATCH /api/v1/tk/tasks/{task_id}
Update a task. All fields optional; only provided fields are applied.

**Request Body**
```json
{
  "priority_code":     "high",
  "status_code":       "in_progress",
  "assignee_user_id":  "<uuid>",
  "due_date":          "2026-05-01",
  "actual_hours":      4.0,
  "title":             "Updated title",
  "resolution_notes":  "Completed review"
}
```

**Response** `200 OK` — `TaskDetailResponse`

### POST /api/v1/tk/tasks/{task_id}/clone
Clone a task (resets status to `open`, clears completed_at/actual_hours).

**Response** `201 Created` — `TaskDetailResponse`

### DELETE /api/v1/tk/tasks/{task_id}
Soft-delete a task (sets `is_active = false`).

**Response** `204 No Content`

---

## TaskDetailResponse Schema

```json
{
  "id":                    "<uuid>",
  "tenant_key":            "acme",
  "org_id":                "<uuid>",
  "workspace_id":          "<uuid>",
  "task_type_code":        "remediation",
  "task_type_name":        "Remediation",
  "priority_code":         "high",
  "priority_name":         "High",
  "status_code":           "in_progress",
  "status_name":           "In Progress",
  "is_terminal":           false,
  "entity_type":           "control",
  "entity_id":             "<uuid>",
  "assignee_user_id":      "<uuid>",
  "reporter_user_id":      "<uuid>",
  "due_date":              "2026-04-30",
  "start_date":            "2026-03-20",
  "completed_at":          null,
  "estimated_hours":       8.0,
  "actual_hours":          null,
  "is_active":             true,
  "created_at":            "2026-03-16T10:00:00",
  "updated_at":            "2026-03-16T10:00:00",
  "title":                 "Fix control gap in access review",
  "description":           "...",
  "acceptance_criteria":   "...",
  "resolution_notes":      null,
  "remediation_plan":      "...",
  "co_assignee_count":     1,
  "blocker_count":         0,
  "comment_count":         3
}
```

---

## Co-Assignments

### GET /api/v1/tk/tasks/{task_id}/assignments
List co-assignees for a task.

**Response** `200 OK`
```json
[
  { "id": "<uuid>", "task_id": "<uuid>", "user_id": "<uuid>", "created_at": "..." }
]
```

### POST /api/v1/tk/tasks/{task_id}/assignments
Add a co-assignee.

**Request Body**
```json
{ "user_id": "<uuid>" }
```

**Response** `201 Created` — `TaskAssignmentResponse`

### DELETE /api/v1/tk/tasks/{task_id}/assignments/{assignment_id}
Remove a co-assignee.

**Response** `204 No Content`

---

## Dependencies (Blockers)

### GET /api/v1/tk/tasks/{task_id}/dependencies
List all blocker relationships for a task. Returns both blockers of this task and tasks this task blocks.

**Response** `200 OK`
```json
{
  "blocked_by": [ { "id": "<uuid>", "task_id": "<uuid>", "blocks_task_id": "<uuid>", "created_at": "..." } ],
  "blocks":     [ { "id": "<uuid>", "task_id": "<uuid>", "blocks_task_id": "<uuid>", "created_at": "..." } ]
}
```

### POST /api/v1/tk/tasks/{task_id}/dependencies
Declare that `task_id` is blocked by another task.

**Request Body**
```json
{ "blocked_by_task_id": "<uuid>" }
```

**Response** `201 Created` — `TaskDependencyResponse`

### DELETE /api/v1/tk/tasks/{task_id}/dependencies/{dependency_id}
Remove a blocker dependency.

**Response** `204 No Content`

---

## Events (Comments & Activity Log)

### GET /api/v1/tk/tasks/{task_id}/events
Chronological list of events (status changes, comments, assignments, etc.).

**Response** `200 OK`
```json
{
  "items": [
    {
      "id":          "<uuid>",
      "task_id":     "<uuid>",
      "event_type":  "comment",
      "actor_id":    "<uuid>",
      "body":        "Added more context here.",
      "created_at":  "2026-03-16T11:00:00"
    }
  ],
  "total": 1
}
```

### POST /api/v1/tk/tasks/{task_id}/events
Add a comment to a task.

**Request Body**
```json
{ "body": "This is ready for review." }
```

**Response** `201 Created` — `TaskEventResponse`

---

## Notes

- `title`, `description`, `acceptance_criteria`, `resolution_notes`, `remediation_plan` are stored as EAV properties in the task detail table; absent properties return `null`.
- A task is **overdue** when `due_date < today` and `is_terminal = false`.
- `co_assignee_count`, `blocker_count`, `comment_count` are pre-aggregated on the task view for efficient list queries.
- Soft-delete via `is_active = false` — deleted tasks do not appear in list results.
- `sort_by` accepted values: `created_at`, `due_date`, `priority_code`, `updated_at`. Invalid values fall back to `created_at`.
